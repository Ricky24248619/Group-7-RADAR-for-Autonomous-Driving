"""Summarise publisher-provided per-box sensor support across the full mini release.

Point support is conditional on released annotations, not detector recall.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
from compare_truckscenes_raw import EDGES, LABELS, transform_points, write_csv


def support_counts(annotation):
    values = [annotation.get(key) for key in ("num_lidar_pts", "num_radar_pts")]
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("Missing, negative or non-integer annotation point count")
    return values


def summarize(rows):
    lidar = np.asarray([r["lidar_points"] for r in rows])
    radar = np.asarray([r["radar_points"] for r in rows])
    if not len(rows):
        raise ValueError("Cannot summarise an empty annotation group")
    return {"box_observations": len(rows), "unique_instances": len({r["instance_token"] for r in rows}),
            "samples": len({r["sample_token"] for r in rows}),
            "lidar_supported": int((lidar > 0).sum()), "radar_supported": int((radar > 0).sum()),
            "both_supported": int(((lidar > 0) & (radar > 0)).sum()),
            "neither_supported": int(((lidar == 0) & (radar == 0)).sum()),
            "radar_support_percent": float(100 * (radar > 0).mean()),
            "median_lidar_points": float(np.median(lidar)), "median_radar_points": float(np.median(radar))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    from truckscenes import TruckScenes
    from truckscenes.utils.geometry_utils import transform_matrix
    from pyquaternion import Quaternion
    truck = TruckScenes(version="v1.2-mini", dataroot=str(args.data_root), verbose=False)
    rows, references = [], []
    for sample in sorted(truck.sample, key=lambda s: s["token"]):
        pose = truck.getclosest("ego_pose", sample["timestamp"])
        if abs(pose["timestamp"] - sample["timestamp"]) > 10_000:
            raise ValueError("Reference pose is more than 10 ms from sample")
        inverse = transform_matrix(np.array(pose["translation"]), Quaternion(pose["rotation"]), inverse=True)
        scene = truck.get("scene", sample["scene_token"])
        references.append({"sample_token": sample["token"], "ego_pose_token": pose["token"],
                           "offset_us": pose["timestamp"] - sample["timestamp"]})
        for token in sample["anns"]:
            annotation = truck.get("sample_annotation", token)
            lidar, radar = support_counts(annotation)
            xyz = transform_points(np.array(annotation["translation"]).reshape(3, 1), inverse)[:, 0]
            distance = float(np.hypot(xyz[0], xyz[1]))
            rows.append({"annotation_token": token, "instance_token": annotation["instance_token"],
                         "sample_token": sample["token"], "scene": scene["name"],
                         "class": annotation["category_name"], "range_m": distance,
                         "band_m": LABELS[int(np.searchsorted(EDGES, distance, side="right") - 1)],
                         "lidar_points": lidar, "radar_points": radar})
    if len(rows) != len(truck.sample_annotation) or len({r["annotation_token"] for r in rows}) != len(rows):
        raise ValueError("Annotation coverage is incomplete or duplicated")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "objects.csv", rows)
    for fields, filename in [(("band_m",), "range_support.csv"), (("class", "band_m"), "class_range_support.csv"),
                             (("scene", "band_m"), "scene_range_support.csv")]:
        groups = defaultdict(list)
        for row in rows:
            groups[tuple(row[key] for key in fields)].append(row)
        write_csv(args.output_dir / filename,
                  [{**dict(zip(fields, key)), **summarize(group)} for key, group in sorted(groups.items())])
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted((args.data_root / "v1.2-mini").glob("*.json"))}
    report = {"dataset": "MAN TruckScenes v1.2-mini", "scene_count": len(truck.scene),
              "sample_count": len(truck.sample), "summary": summarize(rows), "input_sha256": hashes,
              "reference": "Nearest sample-time ego pose; box-centre planar x-y range; all released classes",
              "count_source": "Publisher num_lidar_pts and num_radar_pts; not independently recounted. Radar count sums all radar sensors without invalid-point filtering per official schema",
              "schema_source": "https://github.com/TUMFTM/truckscenes-devkit/blob/main/docs/schema_truckscenes.md",
              "limitations": ["Repeated box observations are not independent objects",
                              "All released boxes have LiDAR support; no radar-only or unsupported annotation population",
                              "Nonzero radar returns inside a released box do not establish a correct model detection",
                              "Scene comparisons are descriptive, with confounded road, weather and class composition"],
              "scene_descriptions": {s["name"]: s["description"] for s in truck.scene}, "references": references}
    (args.output_dir / "manifest.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
