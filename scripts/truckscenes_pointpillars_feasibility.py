#!/usr/bin/env python3
"""Minimal execution-path check: nuScenes-pretrained PointPillars LiDAR
detector, zero-shot, on one real TruckScenes sample.

AD-S3-1 bullet 2 (LiDAR candidate feasibility) -- see
experiment-log/0019-truckscenes-lidar-detector-feasibility.md and
docs/truckscenes-lidar-detector-decision.md for the full go/no-go writeup,
including why CenterPoint (the originally planned candidate) is a no-go on
this hardware (spconv has no Windows wheel, CPU or CUDA).

This is deliberately NOT a scored run: one sample, no ground-truth
comparison, no class breakdown. It exists to prove the candidate loads and
produces plausible output on real TruckScenes data on this machine's CPU --
nothing more. A full 80-sample scored run (mirroring
truckscenes_fcos3d_infer.py's methodology) is the natural follow-on if the
team wants the actual benchmark.

    python scripts/truckscenes_pointpillars_feasibility.py \
        --dataroot <man-truckscenes> --config <pointpillars nus-3d config .py> \
        --checkpoint <pointpillars .pth>

Requires the same detection-env venv as truckscenes_fcos3d_infer.py
(mmdet3d, torch, truckscenes-devkit) -- no new dependencies, and
deliberately no spconv, which is the whole point of this candidate.
"""

from __future__ import annotations

import argparse

import numpy as np

from truckscenes import TruckScenes
from truckscenes.utils.data_classes import LidarPointCloud

from mmdet3d.apis import inference_detector, init_model


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataroot", required=True)
    ap.add_argument("--version", default="v1.2-mini")
    ap.add_argument("--config", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--sample-index", type=int, default=0,
                     help="Index into trucksc.sample for the one sample checked.")
    ap.add_argument("--channel", default="LIDAR_TOP_FRONT")
    ap.add_argument("--score-threshold", type=float, default=0.10)
    return ap.parse_args()


def load_padded_points(trucksc: TruckScenes, dataroot: str, sample: dict,
                        channel: str) -> np.ndarray:
    """TruckScenes' own devkit returns 4 features per point (x, y, z,
    intensity). The nuScenes loading pipeline this config uses expects a 5th
    column -- a per-point sweep time-lag, zeroed here to mark every point as
    the current (single) sweep, since we are not doing nuScenes' multi-sweep
    temporal aggregation. Confirmed necessary by a real IndexError on the
    unpadded array -- not a preemptive guess.
    """
    sd = trucksc.get("sample_data", sample["data"][channel])
    pcd_path = f"{dataroot}/{sd['filename']}"
    pc = LidarPointCloud.from_file(pcd_path)
    points_4d = pc.points.T.astype(np.float32)
    zeros = np.zeros((points_4d.shape[0], 1), dtype=np.float32)
    return np.concatenate([points_4d, zeros], axis=1), pcd_path


def main():
    args = parse_args()
    trucksc = TruckScenes(version=args.version, dataroot=args.dataroot, verbose=False)
    sample = trucksc.sample[args.sample_index]

    points, pcd_path = load_padded_points(trucksc, args.dataroot, sample, args.channel)
    print(f"Sample: {pcd_path}")
    print(f"Loaded and padded points: {points.shape}")

    model = init_model(args.config, args.checkpoint, device="cpu")
    print("Model loaded. Running inference on one real sample ...")

    result = inference_detector(model, points)
    # inference_detector returns a (result, data) tuple, unlike
    # inference_mono_3d_detector's bare result for a single non-batch image.
    if isinstance(result, tuple):
        result = result[0]

    pred = result.pred_instances_3d
    n_raw = len(pred.scores_3d)
    n_keep = int((pred.scores_3d >= args.score_threshold).sum()) if n_raw else 0
    print(f"Inference completed. Raw boxes: {n_raw}. "
          f"Boxes >= {args.score_threshold} score: {n_keep}.")
    print("MINIMAL EXECUTION PATH: SUCCESS")


if __name__ == "__main__":
    main()
