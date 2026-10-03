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

Input frame (PR #63 review, docs/pr63-input-frame-review.md): the native
`LIDAR_TOP_FRONT` frame is pitched ~56 degrees down from vertical, but the
checkpoint was trained on nuScenes' upright roof LiDAR (z = gravity axis,
yaw-only boxes, x right / y forward, ~1.84 m above the ground). Feeding native
points straight in produced boxes tilted 54.6-58.2 degrees in world frame.
By default (`--input-frame upright`) points are therefore moved into an
upright *virtual* LiDAR before inference, and boxes are mapped back out of
that same frame -- see `upright_virtual_lidar`. `--input-frame native`
reproduces the historical unrectified run (EXP-0024's first run) exactly.

    python scripts/truckscenes_pointpillars_infer.py \
        --dataroot <man-truckscenes> --config <pointpillars nus-3d config .py> \
        --checkpoint <pointpillars .pth> --start 0 --end 15 --out results.json

Requires the same detection-env venv as truckscenes_fcos3d_infer.py and
truckscenes_pointpillars_feasibility.py (mmdet3d, torch, truckscenes-devkit,
no spconv). The frame geometry itself is plain numpy, so
tests/test_truckscenes_pointpillars_infer.py checks it without any of them.

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

# nuScenes' LIDAR_TOP, which the checkpoint was trained on: mounted ~1.84 m
# above the ego origin (ground level, rear axle) and yawed -90 degrees about
# ego z, so its x axis points right and y forward. The checkpoint's anchors sit
# at z = -1.8 in that frame, i.e. on the ground. TruckScenes' ego origin is
# also at ground level (annotated box bottoms have median z ~0.00 m in ego).
NUSC_LIDAR_HEIGHT = 1.84
NUSC_LIDAR_YAW_IN_EGO = -np.pi / 2

INPUT_FRAMES = ("upright", "native")


def quat_to_rotation(rotation_wxyz) -> np.ndarray:
    """3x3 rotation matrix from a wxyz quaternion (TruckScenes' convention)."""
    w, x, y, z = np.asarray(rotation_wxyz, dtype=float) / np.linalg.norm(rotation_wxyz)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


def rotation_to_quat(r: np.ndarray) -> list:
    """wxyz quaternion (w >= 0) from a 3x3 rotation matrix."""
    trace = np.trace(r)
    if trace > 0:
        s = 2 * np.sqrt(trace + 1)
        q = [s / 4, (r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s]
    else:
        i = int(np.argmax(np.diag(r)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = 2 * np.sqrt(1 + r[i, i] - r[j, j] - r[k, k])
        q = [0.0, 0.0, 0.0, 0.0]
        q[0] = (r[k, j] - r[j, k]) / s
        q[1 + i] = s / 4
        q[1 + j] = (r[j, i] + r[i, j]) / s
        q[1 + k] = (r[k, i] + r[i, k]) / s
    q = np.array(q)
    return (q if q[0] >= 0 else -q).tolist()


def rot_z(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def quat_to_matrix4(translation, rotation_wxyz) -> np.ndarray:
    """Build a 4x4 homogeneous transform from TruckScenes' translation +
    wxyz-quaternion rotation (same convention as calibrated_sensor/ego_pose).
    Same transform as the helper in truckscenes_fcos3d_infer.py.
    """
    m = np.eye(4)
    m[:3, :3] = quat_to_rotation(rotation_wxyz)
    m[:3, 3] = translation
    return m


def upright_virtual_lidar(lidar2ego: np.ndarray, ego2global: np.ndarray) -> np.ndarray:
    """4x4 virtual-LiDAR -> global transform matching the checkpoint's frame.

    - z is the world gravity axis (not ego z, so ego pitch/roll on a slope
      does not tilt it either);
    - x/y follow the ego heading rotated by nuScenes' -90 degree LIDAR_TOP
      yaw, so x points right and y forward as in training;
    - the origin is NUSC_LIDAR_HEIGHT above the ground point directly below
      the real sensor (ego z = 0 at the sensor's ego x/y).

    Only the frame changes; no points are added or dropped.
    """
    r_e2g = ego2global[:3, :3]
    ego_yaw = np.arctan2(r_e2g[1, 0], r_e2g[0, 0])
    ground_below_sensor = ego2global @ np.array([lidar2ego[0, 3], lidar2ego[1, 3], 0.0, 1.0])

    virtual2global = np.eye(4)
    virtual2global[:3, :3] = rot_z(ego_yaw + NUSC_LIDAR_YAW_IN_EGO)
    virtual2global[:3, 3] = ground_below_sensor[:3] + [0.0, 0.0, NUSC_LIDAR_HEIGHT]
    return virtual2global


def model_frame_to_global(lidar2ego: np.ndarray, ego2global: np.ndarray,
                          input_frame: str) -> np.ndarray:
    """The frame the model sees, as a 4x4 transform into global."""
    if input_frame == "upright":
        return upright_virtual_lidar(lidar2ego, ego2global)
    if input_frame == "native":
        # Historical unrectified run: native sensor frame, tilted ~56 degrees.
        return ego2global @ lidar2ego
    raise ValueError(f"unknown input frame {input_frame!r}")


def points_to_model_frame(points: np.ndarray, lidar2ego: np.ndarray,
                          ego2global: np.ndarray, model2global: np.ndarray) -> np.ndarray:
    """Move (N, >=3) native-sensor points into the model frame. Columns after
    xyz (intensity, sweep time) are passed through unchanged."""
    native2model = np.linalg.inv(model2global) @ ego2global @ lidar2ego
    out = points.copy()
    out[:, :3] = points[:, :3] @ native2model[:3, :3].T + native2model[:3, 3]
    return out


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


def boxes_model_to_global(centers, dims, yaws, velocities, scores, labels,
                          model2global: np.ndarray):
    """Reimplements mmdet3d's output_to_nusc_box + lidar_nusc_box_to_global
    (mmdet3d/evaluation/metrics/nuscenes_metric.py) without depending on the
    nuscenes-devkit's Box class -- plain numpy only, mirroring how
    truckscenes_fcos3d_infer.py's boxes_cam_to_global copies the camera
    path's geometry. Inputs are LiDARInstance3DBoxes fields in the model frame
    (gravity centres, raw (l, w, h) dims, yaw, (vx, vy)); the boxes leave
    through exactly the frame the points entered by.
    """
    # mmdet3d's own LiDAR -> nuScenes box convention: (l, w, h) -> (w, l, h).
    nus_dims = np.asarray(dims)[:, [1, 0, 2]]
    r_m2g, t_m2g = model2global[:3, :3], model2global[:3, 3]

    entries = []
    for i in range(len(centers)):
        center = r_m2g @ np.asarray(centers[i], dtype=float) + t_m2g
        rotation = r_m2g @ rot_z(float(yaws[i]))
        velocity = r_m2g @ np.array([velocities[i][0], velocities[i][1], 0.0])

        cls_name = NUSC_CLASSES[int(labels[i])]
        entries.append({
            "sample_token": None,  # filled in by the caller
            "translation": center.tolist(),
            "size": nus_dims[i].tolist(),
            "rotation": rotation_to_quat(rotation),
            "velocity": [float(velocity[0]), float(velocity[1])],
            "detection_name": NUSC_TO_TRUCKSCENES[cls_name],
            "detection_score": float(scores[i]),
            "attribute_name": DEFAULT_ATTRIBUTE.get(cls_name, ""),
        })
    return entries


def world_up_tilt_deg(rotation_wxyz) -> float:
    """Angle between a box's own up axis and world up -- 0 for an upright box.
    Same measure as scripts/audit_pointpillars_tilt.py."""
    up_z = quat_to_rotation(rotation_wxyz)[2, 2]
    return float(np.degrees(np.arccos(np.clip(up_z, -1.0, 1.0))))


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataroot", required=True)
    ap.add_argument("--version", default="v1.2-mini")
    ap.add_argument("--split", default="mini_val")
    ap.add_argument("--config", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--out", default="results.json")
    ap.add_argument("--channel", default=LIDAR_CHANNEL)
    ap.add_argument("--input-frame", choices=INPUT_FRAMES, default="upright",
                     help="upright: rectified virtual LiDAR (default). "
                          "native: the historical unrectified run.")
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
        model2global = model_frame_to_global(lidar2ego, ego2global, args.input_frame)

        points = points_to_model_frame(
            load_padded_points(trucksc, dataroot, sample, args.channel),
            lidar2ego, ego2global, model2global)

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
            boxes = pred.bboxes_3d[keep]
            entries = boxes_model_to_global(
                boxes.gravity_center.numpy(), boxes.dims.numpy(),
                boxes.yaw.numpy(), boxes.tensor.numpy()[:, 7:9],
                pred.scores_3d[keep].numpy(), pred.labels_3d[keep].numpy(),
                model2global)
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
                             f"TruckScenes {args.channel} point clouds "
                             f"({args.input_frame} input frame), no "
                             "fine-tuning. Follow-on to EXP-0019's one-sample "
                             "feasibility check."),
            "code_url": "", "paper_url": "",
        },
        "results": results,
    }
    out_path.write_text(json.dumps(submission))
    n_boxes = sum(len(v) for v in results.values())
    print(f"Wrote {out_path}: {len(results)} samples, {n_boxes} boxes total.")
    tilts = [world_up_tilt_deg(b["rotation"]) for v in results.values() for b in v]
    if tilts:
        # Upright input should give upright boxes, like the ground truth.
        print(f"Box world-up tilt: max {max(tilts):.4f} deg over {len(tilts)} boxes.")


if __name__ == "__main__":
    main()
