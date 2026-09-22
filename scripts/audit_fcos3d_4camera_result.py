#!/usr/bin/env python3
"""Audit the EXP-0010 four-camera FCOS3D result (AD-S3-1, acceptance bullet 1).

Independently re-checks calibration/box-coordinate correctness and
camera/sample coverage for the four-camera zero-shot run, using the
devkit's own (trusted) geometry code -- Box, TruckScenes.boxes_to_sensor,
box_in_image -- rather than reusing truckscenes_fcos3d_infer.py's own
conversion math. A bug shared between "produce the result" and "check the
result" can't hide from an audit that uses different code for each.

Three checks, in order:

1. Camera/sample data coverage (full 80-sample mini_val split, no
   inference): confirms every sample actually has all 4 camera channels in
   its sample_data, so "4 cameras" wasn't silently short of data for some
   samples.

2. Geometric visibility audit of the EXISTING EXP-0010 predictions
   (results_mini_val_fcos3d_4cam.json, no rerun): for every saved
   global-frame predicted box and every one of that sample's 4 cameras,
   reproject with the devkit's own boxes_to_sensor()+box_in_image() and
   record whether it lands validly (in front, in image bounds) in that
   camera. This is a geometric visibility PROXY for camera provenance --
   the original run didn't tag which camera each prediction came from, so
   this cannot prove a box came from a specific camera, only whether it
   COULD have (neighbouring cameras can have overlapping frustums). Report
   it as that, not as literal per-call provenance.

3. A small fresh instrumented run (a handful of samples, camera-tagged,
   written to a separate audit-only file -- EXP-0010's own result file is
   untouched) to get genuine per-call, per-camera success/skip counts, and
   to independently verify: for a box tagged with its real source camera,
   does it round-trip validly into THAT SAME camera via the devkit's own
   geometry? This directly answers "is the box-coordinate conversion
   correct", using code the original run never called.

Visual overlays (devkit GT boxes + our predicted boxes, both rendered via
the devkit's own Box.render(), on the same real camera image) are saved for
each sample/camera pair processed in step 3.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from pyquaternion import Quaternion

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from truckscenes_fcos3d_infer import (  # noqa: E402
    CAMERA_CHANNELS,
    DEFAULT_ATTRIBUTE,
    NUSC_CLASSES,
    NUSC_TO_TRUCKSCENES,
    SCORE_THRESHOLD,
    boxes_cam_to_global,
    cam2img_matrix4,
    quat_to_matrix4,
)

from truckscenes import TruckScenes  # noqa: E402
from truckscenes.utils.splits import create_splits_scenes  # noqa: E402
from truckscenes.utils.data_classes import Box  # noqa: E402
from truckscenes.utils.geometry_utils import BoxVisibility, box_in_image, view_points  # noqa: E402

from mmdet3d.apis import inference_mono_3d_detector, init_model  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataroot", required=True)
    ap.add_argument("--version", default="v1.2-mini")
    ap.add_argument("--split", default="mini_val")
    ap.add_argument("--config", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument(
        "--existing-results", required=True,
        help="EXP-0010's results_mini_val_fcos3d_4cam.json, for checks 1-2.",
    )
    ap.add_argument("--out-dir", default="audit_fcos3d_4camera")
    ap.add_argument(
        "--rerun-indices", type=int, nargs="+", default=[0, 20, 40, 60],
        help="Split-list sample indices for the instrumented mini rerun (step 3).",
    )
    ap.add_argument(
        "--overlays-only", action="store_true",
        help="Skip steps 1-3 (already-saved outputs in --out-dir) and just "
             "(re-)render step 3's overlays -- for fixing rendering without "
             "repeating CPU inference.",
    )
    return ap.parse_args()


def split_samples(trucksc: TruckScenes, split: str) -> list:
    split_scenes = create_splits_scenes()[split]
    scene_name_to_token = {s["name"]: s["token"] for s in trucksc.scene}
    split_scene_tokens = {
        scene_name_to_token[n] for n in split_scenes if n in scene_name_to_token
    }
    return [s for s in trucksc.sample if s["scene_token"] in split_scene_tokens]


# --- Step 1: camera/sample data coverage -----------------------------------

def check_coverage(samples: list) -> dict:
    counts = {ch: 0 for ch in CAMERA_CHANNELS}
    missing = []
    for s in samples:
        for ch in CAMERA_CHANNELS:
            if ch in s["data"]:
                counts[ch] += 1
            else:
                missing.append({"sample_token": s["token"], "camera": ch})
    return {
        "total_samples": len(samples),
        "cameras_expected_per_sample": len(CAMERA_CHANNELS),
        "present_count_per_camera": counts,
        "missing": missing,
    }


# --- Step 2: geometric visibility audit of the existing EXP-0010 result ----

def geometric_visibility_audit(trucksc: TruckScenes, samples: list, results: dict) -> dict:
    per_camera_valid = {ch: 0 for ch in CAMERA_CHANNELS}
    per_camera_checked = {ch: 0 for ch in CAMERA_CHANNELS}
    boxes_with_zero_valid_cameras = 0
    boxes_with_multiple_valid_cameras = 0
    total_boxes_checked = 0

    for s in samples:
        preds = results.get(s["token"], [])
        if not preds:
            continue

        cam_geo = {}
        for ch in CAMERA_CHANNELS:
            if ch not in s["data"]:
                continue
            sd = trucksc.get("sample_data", s["data"][ch])
            cs = trucksc.get("calibrated_sensor", sd["calibrated_sensor_token"])
            ego_pose = trucksc.get("ego_pose", sd["ego_pose_token"])
            cam_geo[ch] = {
                "cs": cs, "ego_pose": ego_pose,
                "intrinsic": np.array(cs["camera_intrinsic"]),
                "imsize": (sd["width"], sd["height"]),
            }

        for p in preds:
            total_boxes_checked += 1
            valid_cameras = 0
            for ch, geo in cam_geo.items():
                per_camera_checked[ch] += 1
                box = Box(p["translation"], p["size"], Quaternion(p["rotation"]))
                sensor_box = trucksc.boxes_to_sensor([box], geo["ego_pose"], geo["cs"])[0]
                if box_in_image(sensor_box, geo["intrinsic"], geo["imsize"],
                                 vis_level=BoxVisibility.ANY):
                    per_camera_valid[ch] += 1
                    valid_cameras += 1
            if valid_cameras == 0:
                boxes_with_zero_valid_cameras += 1
            elif valid_cameras > 1:
                boxes_with_multiple_valid_cameras += 1

    return {
        "method": (
            "For every saved EXP-0010 predicted box, reprojected with the devkit's own "
            "boxes_to_sensor()+box_in_image() into each of the sample's 4 cameras. This "
            "is a geometric visibility PROXY, not per-call provenance -- EXP-0010's "
            "output does not record which camera produced each box, and overlapping "
            "camera frustums mean a box can legitimately reproject validly into more "
            "than one camera."
        ),
        "total_boxes_checked": total_boxes_checked,
        "per_camera_checked": per_camera_checked,
        "per_camera_geometrically_valid": per_camera_valid,
        "per_camera_valid_fraction": {
            ch: round(per_camera_valid[ch] / per_camera_checked[ch], 4)
            if per_camera_checked[ch] else None
            for ch in CAMERA_CHANNELS
        },
        "boxes_with_zero_valid_cameras": boxes_with_zero_valid_cameras,
        "boxes_with_zero_valid_cameras_fraction": (
            round(boxes_with_zero_valid_cameras / total_boxes_checked, 4)
            if total_boxes_checked else None
        ),
        "boxes_with_multiple_valid_cameras": boxes_with_multiple_valid_cameras,
    }


# --- Step 3: instrumented mini rerun + independent round-trip check --------

def run_instrumented_subset(trucksc, dataroot, samples, indices, config, checkpoint):
    model = init_model(config, checkpoint, device="cpu")
    audit_samples = [samples[i] for i in indices if i < len(samples)]

    tagged_results = []  # flat list; each entry carries its own source_camera
    success_skip = []    # one row per (sample, camera) call

    for sample in audit_samples:
        for cam in CAMERA_CHANNELS:
            if cam not in sample["data"]:
                success_skip.append({
                    "sample_token": sample["token"], "camera": cam,
                    "status": "no_data", "n_boxes": 0,
                })
                continue

            sample_data = trucksc.get("sample_data", sample["data"][cam])
            calib = trucksc.get("calibrated_sensor", sample_data["calibrated_sensor_token"])
            ego_pose = trucksc.get("ego_pose", sample_data["ego_pose_token"])
            img_path = pathlib.Path(dataroot) / sample_data["filename"]
            cam2img = cam2img_matrix4(calib["camera_intrinsic"])
            cam2ego = quat_to_matrix4(calib["translation"], calib["rotation"])
            ego2global = quat_to_matrix4(ego_pose["translation"], ego_pose["rotation"])

            info = {
                "metainfo": {},
                "data_list": [{
                    "images": {cam: {"img_path": img_path.name, "cam2img": cam2img.tolist()}}
                }],
            }
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(info, f)
                info_path = pathlib.Path(f.name)
            try:
                result = inference_mono_3d_detector(
                    model, str(img_path), str(info_path), cam_type=cam)
            finally:
                info_path.unlink()

            pred = result.pred_instances_3d
            keep = pred.scores_3d >= SCORE_THRESHOLD
            n_boxes = int(keep.sum())
            success_skip.append({
                "sample_token": sample["token"], "camera": cam,
                "status": "success" if n_boxes else "skip_no_detections",
                "n_boxes": n_boxes,
            })
            if n_boxes == 0:
                continue

            entries = boxes_cam_to_global(
                pred.bboxes_3d[keep], pred.scores_3d[keep].numpy(),
                pred.labels_3d[keep].numpy(), cam2ego, ego2global)
            for e in entries:
                e["sample_token"] = sample["token"]
                e["source_camera"] = cam  # audit-only field; not part of eval schema
                tagged_results.append(e)

            print(f"  {sample['token'][:8]} {cam}: {n_boxes} boxes", flush=True)

    return audit_samples, tagged_results, success_skip


def roundtrip_check(trucksc, tagged_results):
    """For each camera-tagged prediction, does it reproject validly back into
    the SAME camera it was reported as coming from, using the devkit's own
    geometry (not the inference script's)? This is the real correctness
    check on calibration/box-coordinate conversion, independent of check 2's
    cross-camera proxy.
    """
    per_camera_valid = {ch: 0 for ch in CAMERA_CHANNELS}
    per_camera_total = {ch: 0 for ch in CAMERA_CHANNELS}
    invalid_examples = []

    # Cache sample_data-derived calibration per (sample_token, camera).
    geo_cache = {}

    for entry in tagged_results:
        key = (entry["sample_token"], entry["source_camera"])
        if key not in geo_cache:
            sample = trucksc.get("sample", entry["sample_token"])
            sd = trucksc.get("sample_data", sample["data"][entry["source_camera"]])
            cs = trucksc.get("calibrated_sensor", sd["calibrated_sensor_token"])
            ego_pose = trucksc.get("ego_pose", sd["ego_pose_token"])
            geo_cache[key] = {
                "cs": cs, "ego_pose": ego_pose,
                "intrinsic": np.array(cs["camera_intrinsic"]),
                "imsize": (sd["width"], sd["height"]),
            }
        geo = geo_cache[key]

        box = Box(entry["translation"], entry["size"], Quaternion(entry["rotation"]))
        sensor_box = trucksc.boxes_to_sensor([box], geo["ego_pose"], geo["cs"])[0]
        valid = box_in_image(sensor_box, geo["intrinsic"], geo["imsize"],
                              vis_level=BoxVisibility.ANY)

        ch = entry["source_camera"]
        per_camera_total[ch] += 1
        if valid:
            per_camera_valid[ch] += 1
        elif len(invalid_examples) < 10:
            invalid_examples.append({
                "sample_token": entry["sample_token"], "camera": ch,
                "detection_name": entry["detection_name"],
                "translation": entry["translation"],
            })

    return {
        "method": (
            "For each box from the instrumented rerun (source camera known with "
            "certainty), reprojected with the devkit's own boxes_to_sensor()+"
            "box_in_image() into that SAME camera. A high valid fraction here "
            "means the calibration/box-coordinate conversion in "
            "truckscenes_fcos3d_infer.py is geometrically consistent with the "
            "devkit's own trusted geometry code -- independent confirmation, "
            "since this check never calls that script's own conversion math."
        ),
        "per_camera_total": per_camera_total,
        "per_camera_valid": per_camera_valid,
        "per_camera_valid_fraction": {
            ch: round(per_camera_valid[ch] / per_camera_total[ch], 4)
            if per_camera_total[ch] else None
            for ch in CAMERA_CHANNELS
        },
        "invalid_examples": invalid_examples,
    }


def draw_box_2d(ax, box: Box, view: np.ndarray, color: str, linewidth: float = 2) -> None:
    """Draw a Box's projected wireframe directly (avoids Box.render(), which
    needs the optional truckscenes-devkit[all] visualization extras that
    detection-env deliberately doesn't install -- installing them risks
    re-upgrading numpy past the <2 pin EXP-0006 fought to keep). Same corner
    convention and edge pattern as the devkit's own render_box.
    """
    corners = view_points(box.corners(), view, normalize=True)[:2, :].T  # (8, 2)

    def draw_rect(selected_corners):
        prev = selected_corners[-1]
        for corner in selected_corners:
            ax.plot([prev[0], corner[0]], [prev[1], corner[1]], color=color, linewidth=linewidth)
            prev = corner

    for i in range(4):
        ax.plot([corners[i][0], corners[i + 4][0]], [corners[i][1], corners[i + 4][1]],
                color=color, linewidth=linewidth)
    draw_rect(corners[:4])
    draw_rect(corners[4:])

    center_bottom_forward = np.mean(corners[0:2], axis=0)
    center_bottom = np.mean(corners[[0, 1, 2, 3]], axis=0)
    ax.plot([center_bottom[0], center_bottom_forward[0]],
            [center_bottom[1], center_bottom_forward[1]], color=color, linewidth=linewidth)


def render_overlays(trucksc, dataroot, audit_samples, tagged_results, out_dir: pathlib.Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    by_key = {}
    for entry in tagged_results:
        by_key.setdefault((entry["sample_token"], entry["source_camera"]), []).append(entry)

    saved = []
    for sample in audit_samples:
        for cam in CAMERA_CHANNELS:
            if cam not in sample["data"]:
                continue
            sd_token = sample["data"][cam]
            sd = trucksc.get("sample_data", sd_token)
            cs = trucksc.get("calibrated_sensor", sd["calibrated_sensor_token"])
            ego_pose = trucksc.get("ego_pose", sd["ego_pose_token"])
            intrinsic = np.array(cs["camera_intrinsic"])
            img_path = pathlib.Path(dataroot) / sd["filename"]

            # GT boxes: devkit's own trusted pipeline.
            _, gt_boxes, _ = trucksc.get_sample_data(sd_token, box_vis_level=BoxVisibility.ANY)

            # Predicted boxes from this camera's instrumented-rerun entries.
            pred_entries = by_key.get((sample["token"], cam), [])
            pred_boxes = []
            for e in pred_entries:
                b = Box(e["translation"], e["size"], Quaternion(e["rotation"]),
                        name=e["detection_name"])
                pred_boxes.append(trucksc.boxes_to_sensor([b], ego_pose, cs)[0])

            im = Image.open(img_path)
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            ax.imshow(im)
            for b in gt_boxes:
                draw_box_2d(ax, b, intrinsic, color="g", linewidth=2)
            for b in pred_boxes:
                draw_box_2d(ax, b, intrinsic, color="r", linewidth=1)
            ax.set_xlim(0, im.size[0])
            ax.set_ylim(im.size[1], 0)
            ax.axis("off")
            ax.set_title(
                f"{cam} | green=ground truth ({len(gt_boxes)}) | "
                f"red=FCOS3D prediction ({len(pred_boxes)})",
                fontsize=9,
            )
            out_path = out_dir / f"{sample['token'][:10]}_{cam}.png"
            fig.savefig(out_path, dpi=110, bbox_inches="tight")
            plt.close(fig)
            saved.append(str(out_path))
            print(f"  saved {out_path}", flush=True)
    return saved


def main():
    args = parse_args()
    dataroot = pathlib.Path(args.dataroot)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    trucksc = TruckScenes(version=args.version, dataroot=str(dataroot), verbose=True)
    samples = split_samples(trucksc, args.split)
    print(f'Split "{args.split}": {len(samples)} samples.')

    if args.overlays_only:
        audit_samples = [samples[i] for i in args.rerun_indices if i < len(samples)]
        tagged_results = json.loads(
            (out_dir / "instrumented_rerun_results.json").read_text())
        overlays = render_overlays(trucksc, dataroot, audit_samples, tagged_results,
                                    out_dir / "overlays")
        print(f"Done. {len(overlays)} overlay image(s) written to {out_dir / 'overlays'}.")
        return

    # Step 1.
    coverage = check_coverage(samples)
    (out_dir / "coverage_report.json").write_text(json.dumps(coverage, indent=2))
    print(f"[1/3] Coverage: {coverage['present_count_per_camera']}, "
          f"{len(coverage['missing'])} missing channel(s).")

    # Step 2.
    existing = json.loads(pathlib.Path(args.existing_results).read_text())["results"]
    visibility = geometric_visibility_audit(trucksc, samples, existing)
    (out_dir / "geometric_visibility_report.json").write_text(
        json.dumps(visibility, indent=2))
    print(f"[2/3] Geometric visibility: "
          f"{visibility['boxes_with_zero_valid_cameras']}/{visibility['total_boxes_checked']} "
          f"boxes reproject into zero cameras.")

    # Step 3.
    print(f"[3/3] Instrumented rerun on sample indices {args.rerun_indices} ...")
    audit_samples, tagged_results, success_skip = run_instrumented_subset(
        trucksc, dataroot, samples, args.rerun_indices, args.config, args.checkpoint)
    (out_dir / "instrumented_rerun_results.json").write_text(
        json.dumps(tagged_results, indent=2))
    (out_dir / "instrumented_rerun_success_skip.json").write_text(
        json.dumps(success_skip, indent=2))

    rt = roundtrip_check(trucksc, tagged_results)
    (out_dir / "roundtrip_check.json").write_text(json.dumps(rt, indent=2))
    print(f"      Round-trip valid fraction per camera: {rt['per_camera_valid_fraction']}")

    overlays = render_overlays(trucksc, dataroot, audit_samples, tagged_results,
                                out_dir / "overlays")
    print(f"Done. {len(overlays)} overlay image(s) written to {out_dir / 'overlays'}.")


if __name__ == "__main__":
    main()
