#!/usr/bin/env python3
"""How many scored ground-truth boxes can one LiDAR channel see at all?

Context for the rectified PointPillars score (EXP-0024): the evaluator scores
every mini_val ground-truth box that survives its own class-range and
point-count filters, using points from all six TruckScenes LiDARs and the
radars. The detector only receives `LIDAR_TOP_FRONT`. This counts, with the
evaluator's own GT loading and filtering, how many of those scored boxes
contain at least one point from that channel in the same keyframe.

No inference. Measures input coverage only; it does not say how many visible
boxes a detector should find.

    python scripts/pointpillars_channel_coverage.py --dataroot <man-truckscenes>
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import Counter

import numpy as np

from truckscenes import TruckScenes
from truckscenes.eval.common.loaders import add_center_dist, filter_eval_boxes, load_gt
from truckscenes.eval.detection.config import config_factory
from truckscenes.eval.detection.data_classes import DetectionBox
from truckscenes.utils.data_classes import LidarPointCloud

from truckscenes_pointpillars_infer import LIDAR_CHANNEL, quat_to_matrix4, quat_to_rotation


def channel_points_global(trucksc: TruckScenes, dataroot: pathlib.Path,
                          sample_token: str, channel: str) -> np.ndarray:
    sd = trucksc.get("sample_data", trucksc.get("sample", sample_token)["data"][channel])
    calib = trucksc.get("calibrated_sensor", sd["calibrated_sensor_token"])
    pose = trucksc.get("ego_pose", sd["ego_pose_token"])
    sensor2global = (quat_to_matrix4(pose["translation"], pose["rotation"])
                     @ quat_to_matrix4(calib["translation"], calib["rotation"]))
    xyz = LidarPointCloud.from_file(str(dataroot / sd["filename"])).points[:3].T
    return xyz @ sensor2global[:3, :3].T + sensor2global[:3, 3]


def points_inside(box: DetectionBox, points: np.ndarray) -> int:
    """Count points inside a box; size is (w, l, h) with length along box x."""
    local = (points - np.asarray(box.translation)) @ quat_to_rotation(box.rotation)
    w, l, h = box.size
    return int(np.sum((np.abs(local[:, 0]) <= l / 2) & (np.abs(local[:, 1]) <= w / 2)
                      & (np.abs(local[:, 2]) <= h / 2)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataroot", required=True)
    ap.add_argument("--version", default="v1.2-mini")
    ap.add_argument("--eval-set", default="mini_val")
    ap.add_argument("--channel", default=LIDAR_CHANNEL)
    ap.add_argument("--config", default="detection_cvpr_2024")
    ap.add_argument("--output", type=pathlib.Path,
                    default=pathlib.Path("docs/evidence/pr63-channel-coverage.json"))
    args = ap.parse_args()
    dataroot = pathlib.Path(args.dataroot)

    trucksc = TruckScenes(version=args.version, dataroot=str(dataroot), verbose=False)
    cfg = config_factory(args.config)
    gt = load_gt(trucksc, args.eval_set, DetectionBox)
    gt = add_center_dist(trucksc, gt)
    gt = filter_eval_boxes(trucksc, gt, cfg.class_range)

    scored, visible = Counter(), Counter()
    visible_dist, hidden_dist = [], []
    for sample_token in gt.sample_tokens:
        points = channel_points_global(trucksc, dataroot, sample_token, args.channel)
        for box in gt[sample_token]:
            scored[box.detection_name] += 1
            if points_inside(box, points) > 0:
                visible[box.detection_name] += 1
                visible_dist.append(box.ego_dist)
            else:
                hidden_dist.append(box.ego_dist)

    total, seen = sum(scored.values()), sum(visible.values())
    result = {
        "channel": args.channel,
        "eval_set": args.eval_set,
        "config": args.config,
        "scored_gt_boxes": total,
        "gt_boxes_with_channel_points": seen,
        "fraction_with_channel_points": round(seen / total, 4) if total else None,
        "ego_dist_m_of_boxes_with_points": (
            {"min": round(min(visible_dist), 2), "median": round(float(np.median(visible_dist)), 2),
             "max": round(max(visible_dist), 2)} if visible_dist else None),
        "ego_dist_m_median_of_boxes_without_points": (
            round(float(np.median(hidden_dist)), 2) if hidden_dist else None),
        "per_class": {name: {"scored": scored[name], "with_channel_points": visible[name]}
                      for name in sorted(scored)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
