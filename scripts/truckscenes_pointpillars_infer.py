#!/usr/bin/env python3
"""Run a nuScenes-pretrained PointPillars LiDAR detector zero-shot against all
80 official TruckScenes `mini_val` samples, and score it with the devkit's own
detection evaluator.

Follow-on to EXP-0019 (`truckscenes_pointpillars_feasibility.py`), which
verified the candidate loads and runs on one real sample but was deliberately
not scored. This script mirrors `truckscenes_fcos3d_infer.py`'s methodology
(EXP-0010) exactly: same chunked --start/--end resume pattern, same
per-sample submission format, same evaluator invocation -- so the LiDAR
result is comparable to the camera result on the same split.

Single channel only (`LIDAR_TOP_FRONT`, same channel EXP-0019 verified) --
TruckScenes splits sensing across six separate LiDARs at different mount
points, unlike nuScenes' single roof LiDAR that this checkpoint was trained
against. Merging multiple TruckScenes LiDAR channels into one cloud is a
materially different, unverified experiment (new calibration-alignment
surface, no feasibility check done for it) and is explicitly out of scope
here -- this only extends the exact channel and preprocessing EXP-0019
already verified from one sample to the full split.

    python scripts/truckscenes_pointpillars_infer.py \
        --dataroot <man-truckscenes> --config <pointpillars nus-3d config .py> \
        --checkpoint <pointpillars .pth> --start 0 --end 15 --out results.json

Requires the same detection-env venv as truckscenes_fcos3d_infer.py and
truckscenes_pointpillars_feasibility.py (mmdet3d, torch, truckscenes-devkit,
no spconv).

A long CPU run is expected to be chunked across several calls: pass
--start/--end to process one slice of the split's sample list at a time.
Each call replaces predictions for its selected samples and preserves the
other samples, so retrying a chunk does not duplicate boxes. It checkpoints
every 5 samples.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from pyquaternion import Quaternion

from truckscenes import TruckScenes
from truckscenes.utils.splits import create_splits_scenes
from truckscenes.utils.data_classes import LidarPointCloud

from mmdet3d.apis import inference_detector, init_model


# nuScenes' 10 detection classes, in the exact index order PointPillars'
# label output uses (same mapping EXP-0019 confirmed reusable from the
# FCOS3D script -- both checkpoints share the nuScenes 10-class output).
NUSC_CLASSES = [
    "car", "truck", "trailer", "bus", "construction_vehicle", "bicycle",
    "motorcycle", "pedestrian", "traffic_cone", "barrier",
]

# nuScenes class -> TruckScenes detection class (eval/detection/README.md).
NUSC_TO_TRUCKSCENES = {
    "car": "car",
    "truck": "truck",
    "trailer": "trailer",
    "bus": "bus",
    "construction_vehicle": "other_vehicle",
    "bicycle": "bicycle",
    "motorcycle": "motorcycle",
    "pedestrian": "pedestrian",
    "traffic_cone": "traffic_cone",
    "barrier": "barrier",
}

# Standard nuScenes default attribute per class (mmdet3d's NuScenesMetric).
DEFAULT_ATTRIBUTE = {
    "car": "vehicle.parked",
    "pedestrian": "pedestrian.moving",
    "trailer": "vehicle.parked",
    "truck": "vehicle.parked",
    "bus": "vehicle.moving",
    "motorcycle": "cycle.without_rider",
    "construction_vehicle": "vehicle.parked",
    "bicycle": "cycle.without_rider",
    "barrier": "",
    "traffic_cone": "",
}

# The single channel EXP-0019 verified feasible. See module docstring for why
# this does not merge TruckScenes' other five LiDAR channels.
LIDAR_CHANNEL = "LIDAR_TOP_FRONT"

SCORE_THRESHOLD = 0.10
MAX_BOXES_PER_SAMPLE = 500


def quat_to_matrix4(translation, rotation_wxyz) -> np.ndarray:
    """Build a 4x4 homogeneous transform from TruckScenes' translation +
    wxyz-quaternion rotation (same convention as calibrated_sensor/ego_pose).
    Identical helper to the one in truckscenes_fcos3d_infer.py.
    """
    m = np.eye(4)
    m[:3, :3] = Quaternion(rotation_wxyz).rotation_matrix
    m[:3, 3] = translation
    return m


def load_padded_points(trucksc: TruckScenes, dataroot: pathlib.Path,
                        sample: dict, channel: str) -> np.ndarray:
    """Same padding EXP-0019 verified necessary: TruckScenes' devkit returns
    4 features per point (x, y, z, intensity); the nuScenes loading pipeline
    this config uses expects a 5th "sweep time-lag" column, zeroed here since
    this is single-sweep zero-shot inference, not multi-sweep aggregation.
    """
    sd = trucksc.get("sample_data", sample["data"][channel])
    pcd_path = dataroot / sd["filename"]
    pc = LidarPointCloud.from_file(str(pcd_path))
    points_4d = pc.points.T.astype(np.float32)
    zeros = np.zeros((points_4d.shape[0], 1), dtype=np.float32)
    return np.concatenate([points_4d, zeros], axis=1)


def boxes_lidar_to_global(bboxes_3d, scores, labels,
                          lidar2ego: np.ndarray, ego2global: np.ndarray):
    """Reimplements mmdet3d's output_to_nusc_box + lidar_nusc_box_to_global
    (mmdet3d/evaluation/metrics/nuscenes_metric.py) without depending on the
    nuscenes-devkit's Box class -- plain numpy/pyquaternion only, mirroring
    how truckscenes_fcos3d_infer.py's boxes_cam_to_global copies the camera
    path's geometry. The LiDAR path needs no extra axis rotation (unlike the
    camera path's cam-to-ego 90-degree correction): predicted boxes are
    already in the devkit's LiDAR sensor frame, same convention as
    LiDARInstance3DBoxes.
    """
    centers = bboxes_3d.gravity_center.numpy()             # (N, 3) LiDAR frame
    dims = bboxes_3d.dims.numpy()                           # (N, 3) raw (l, w, h)
    yaws = bboxes_3d.yaw.numpy()                            # (N,)
    tensor = bboxes_3d.tensor.numpy()                       # (N, 9): ..., vx, vy

    # mmdet3d's own LiDAR -> nuScenes box convention: (l, w, h) -> (w, l, h).
    nus_dims = dims[:, [1, 0, 2]]

    r_l2e, t_l2e = lidar2ego[:3, :3], lidar2ego[:3, 3]
    r_e2g, t_e2g = ego2global[:3, :3], ego2global[:3, 3]

    entries = []
    for i in range(len(bboxes_3d)):
        quat = Quaternion(axis=[0, 0, 1], radians=float(yaws[i]))
        center = centers[i].copy()
        velocity = np.array([tensor[i, 7], tensor[i, 8], 0.0])

        # lidar -> ego (rotate then translate; velocity rotates only)
        center = r_l2e @ center + t_l2e
        quat = Quaternion(matrix=r_l2e, rtol=1e-5, atol=1e-7) * quat
        velocity = r_l2e @ velocity

        # ego -> global
        center = r_e2g @ center + t_e2g
        quat = Quaternion(matrix=r_e2g, rtol=1e-5, atol=1e-7) * quat
        velocity = r_e2g @ velocity

        cls_name = NUSC_CLASSES[int(labels[i])]
        entries.append({
            "sample_token": None,  # filled in by the caller
            "translation": center.tolist(),
            "size": nus_dims[i].tolist(),
            "rotation": [quat.w, quat.x, quat.y, quat.z],
            "velocity": [float(velocity[0]), float(velocity[1])],
            "detection_name": NUSC_TO_TRUCKSCENES[cls_name],
            "detection_score": float(scores[i]),
            "attribute_name": DEFAULT_ATTRIBUTE.get(cls_name, ""),
        })
    return entries


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataroot", required=True)
    ap.add_argument("--version", default="v1.2-mini")
    ap.add_argument("--split", default="mini_val")
    ap.add_argument("--config", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--out", default="results.json")
    ap.add_argument("--channel", default=LIDAR_CHANNEL)
    ap.add_argument("--score-threshold", type=float, default=SCORE_THRESHOLD)
    ap.add_argument("--limit", type=int, default=None,
                     help="Cap number of samples processed (smoke testing).")
    ap.add_argument("--start", type=int, default=0,
                     help="Start index into the split's sample list "
                          "(for chunking a long CPU run across calls).")
    ap.add_argument("--end", type=int, default=None,
                     help="End index (exclusive) into the split's sample "
                          "list. Combined with --start to process one chunk "
                          "at a time; --out is merged with, not overwritten.")
    return ap.parse_args()


def main():
    args = parse_args()
    dataroot = pathlib.Path(args.dataroot)

    trucksc = TruckScenes(version=args.version, dataroot=str(dataroot),
                           verbose=True)

    split_scenes = create_splits_scenes()[args.split]
    scene_name_to_token = {s["name"]: s["token"] for s in trucksc.scene}
    split_scene_tokens = {scene_name_to_token[n] for n in split_scenes
                           if n in scene_name_to_token}

    all_samples = [s for s in trucksc.sample
                   if s["scene_token"] in split_scene_tokens]
    if args.limit:
        all_samples = all_samples[:args.limit]

    # Every sample_token in the split must be a key in the final results
    # file (even with an empty list) or the evaluator's assertion that
    # predictions and ground truth cover the same sample set will fail.
    out_path = pathlib.Path(args.out)
    if out_path.exists():
        results = json.loads(out_path.read_text())["results"]
        print(f"Resuming: loaded existing results for "
              f"{sum(1 for v in results.values() if v)} samples from "
              f"{out_path}.")
    else:
        results = {}
    for s in all_samples:
        results.setdefault(s["token"], [])

    end = args.end if args.end is not None else len(all_samples)
    samples = all_samples[args.start:end]
    print(f'Split "{args.split}" has {len(all_samples)} samples total; '
          f"this call processes indices [{args.start}:{end}] "
          f"({len(samples)} samples) on channel {args.channel}.")

    model = init_model(args.config, args.checkpoint, device="cpu")

    for idx, sample in enumerate(samples):
        if args.channel not in sample["data"]:
            results[sample["token"]] = []
            continue

        sample_data = trucksc.get("sample_data", sample["data"][args.channel])
        calib = trucksc.get("calibrated_sensor",
                             sample_data["calibrated_sensor_token"])
        ego_pose = trucksc.get("ego_pose", sample_data["ego_pose_token"])

        lidar2ego = quat_to_matrix4(calib["translation"], calib["rotation"])
        ego2global = quat_to_matrix4(ego_pose["translation"], ego_pose["rotation"])

        points = load_padded_points(trucksc, dataroot, sample, args.channel)

        result = inference_detector(model, points)
        # inference_detector returns a (result, data) tuple, same as EXP-0019
        # found -- unlike inference_mono_3d_detector's bare result.
        if isinstance(result, tuple):
            result = result[0]

        pred = result.pred_instances_3d
        keep = pred.scores_3d >= args.score_threshold
        if keep.sum() == 0:
            sample_results = []
        else:
            entries = boxes_lidar_to_global(
                pred.bboxes_3d[keep], pred.scores_3d[keep].numpy(),
                pred.labels_3d[keep].numpy(), lidar2ego, ego2global)
            for e in entries:
                e["sample_token"] = sample["token"]
            sample_results = entries

        if len(sample_results) > MAX_BOXES_PER_SAMPLE:
            sample_results = sorted(
                sample_results,
                key=lambda r: -r["detection_score"])[:MAX_BOXES_PER_SAMPLE]
        results[sample["token"]] = sample_results

        if (idx + 1) % 5 == 0 or (idx + 1) == len(samples):
            print(f"  processed {idx + 1}/{len(samples)} samples "
                  f"(chunk index {args.start}-{end})", flush=True)
            out_path.write_text(json.dumps({"meta": {}, "results": results}))

    submission = {
        "meta": {
            "use_camera": False, "use_lidar": True, "use_radar": False,
            "use_map": False, "use_external": False,
            "use_future_frames": False, "use_tta": False,
            "method_name": "PointPillars (nuScenes-pretrained, zero-shot)",
            "authors": "", "affiliation": "",
            "description": ("Zero-shot cross-dataset test: nuScenes-trained "
                             "PointPillars checkpoint run directly on "
                             f"TruckScenes {args.channel} point clouds, no "
                             "fine-tuning. Follow-on to EXP-0019's one-sample "
                             "feasibility check."),
            "code_url": "", "paper_url": "",
        },
        "results": results,
    }
    out_path.write_text(json.dumps(submission))
    n_boxes = sum(len(v) for v in results.values())
    print(f"Wrote {out_path}: {len(results)} samples, {n_boxes} boxes total.")


if __name__ == "__main__":
    main()
