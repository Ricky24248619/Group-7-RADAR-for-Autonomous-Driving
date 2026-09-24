"""Stream the labelled GOOSE split into class/traversability-by-range evidence.

These are released semantic labels and a project remap, not model predictions.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from goose_render_frame import find_frames, frame_key, load_frame
from goose_stats import load_classes
from compare_truckscenes_raw import EDGES, LABELS, write_csv

ROOT = Path(__file__).resolve().parents[1]


def class_ranges(points, labels, class_ids):
    if len(points) != len(labels) or not np.isfinite(points[:, :3]).all():
        raise ValueError("Mismatched labels or nonfinite coordinates")
    if not np.isin(labels, class_ids).all():
        raise ValueError("Unknown semantic ID in labels")
    bins = np.searchsorted(EDGES, np.hypot(points[:, 0].astype(float), points[:, 1].astype(float)), side="right") - 1
    return np.bincount(labels.astype(np.int64) * len(LABELS) + bins,
                       minlength=(max(class_ids) + 1) * len(LABELS)).reshape(-1, len(LABELS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    classes = load_classes(args.root)
    frames = find_frames(args.root)
    if len({frame_key(scan) for scan, _ in frames}) != len(frames):
        raise ValueError("Duplicate scan join keys")
    mapping = ROOT / "GOOSE - Ricky+Damien/traversability_map.csv"
    with mapping.open(encoding="utf-8-sig", newline="") as stream:
        groups = {int(r["label_key"]): r["traversability_name"] for r in csv.DictReader(stream)}
    if set(groups) != set(classes):
        raise ValueError("Traversability map and semantic taxonomy differ")
    totals = defaultdict(lambda: np.zeros((max(classes) + 1, len(LABELS)), dtype=np.int64))
    manifest, frame_rows = [], []
    seen_pairs = {}
    for i, (scan, label) in enumerate(frames, 1):
        points, labels = load_frame(scan, label)
        counts = class_ranges(points, labels, list(classes))
        scenario = scan.parent.name
        totals[scenario] += counts
        digest = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (scan, label)]
        pair_hash = tuple(digest)
        duplicate_of = seen_pairs.get(pair_hash)
        seen_pairs.setdefault(pair_hash, str(scan.relative_to(args.root)))
        manifest.append({"scan": str(scan.relative_to(args.root)), "label": str(label.relative_to(args.root)),
                         "scan_sha256": digest[0], "label_sha256": digest[1], "duplicate_content_of": duplicate_of})
        for band, count in zip(LABELS, counts.sum(axis=0)):
            frame_rows.append({"frame": frame_key(scan), "scenario": scenario, "band_m": band,
                               "points": int(count), "frame_points": len(points)})
        if i % 100 == 0 or i == len(frames):
            print(f"Processed {i}/{len(frames)} GOOSE frames", flush=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    totals["ALL"] = sum(totals.values())
    class_rows, group_rows = [], []
    for scenario, counts in sorted(totals.items()):
        grouped = defaultdict(lambda: np.zeros(len(LABELS), dtype=np.int64))
        for key, name in classes.items():
            grouped[groups[key]] += counts[key]
            for band, count in zip(LABELS, counts[key]):
                class_rows.append({"scenario": scenario, "class_id": key, "class": name,
                                   "band_m": band, "points": int(count)})
        for group, values in sorted(grouped.items()):
            for band, count, denominator in zip(LABELS, values, counts.sum(axis=0)):
                group_rows.append({"scenario": scenario, "group": group, "band_m": band,
                                   "points": int(count), "all_points_in_band": int(denominator)})
    write_csv(args.output_dir / "class_ranges.csv", class_rows)
    write_csv(args.output_dir / "traversability_ranges.csv", group_rows)
    write_csv(args.output_dir / "frame_ranges.csv", frame_rows)
    report = {"dataset": "GOOSE labelled 3D validation download", "frames": len(frames),
              "points": int(totals["ALL"].sum()), "range_counts": totals["ALL"].sum(axis=0).tolist(),
              "range_labels": LABELS, "scenarios": len(totals) - 1,
              "duplicate_scan_and_label_pairs": sum(r["duplicate_content_of"] is not None for r in manifest),
              "reference": "Released LiDAR coordinates, planar x-y range, full azimuth; no cross-dataset extrinsic alignment",
              "traversability_map_sha256": hashlib.sha256(mapping.read_bytes()).hexdigest(),
              "taxonomy_sha256": hashlib.sha256((args.root / "goose_label_mapping.csv").read_bytes()).hexdigest(),
              "limitations": "No local radar bag or radar labels; project traversability mapping is not measured driveability or model accuracy",
              "inputs": manifest}
    (args.output_dir / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "inputs"}, indent=2))


if __name__ == "__main__":
    main()
