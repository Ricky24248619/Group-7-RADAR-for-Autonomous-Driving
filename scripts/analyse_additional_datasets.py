#!/usr/bin/env python3
"""Bounded Boreas scan and WildScenes split audit; no model or sensor ranking."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

REVISIONS = {
    "boreas": ("utiasASRL/pyboreas", "8e100ff82ecd4992511da61b016398dbd230f205"),
    "wildscenes": ("csiro-robotics/WildScenes", "9eb4e10b4483a634159e2b371be0437e465fe218"),
    "radial": ("valeoai/RADIal", "02f52fc13ee41feacec82fd8e05f5b1f0bf4ce26"),
    "dualradar": ("adept-thu/Dual-Radar", "9a972df36af319d3953b4a6e672e6a814ec05eb9"),
    "vod": ("tudelft-iv/view-of-delft-dataset", "d39b519018701b221787668b182c159bbc8a848f"),
}
SEQUENCE = "boreas-2021-09-02-11-42"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}

def metadata_paths(dataset):
    if dataset == "boreas":
        return ["README.md", "DATA_REFERENCE.md", "DATA_LICENSE.md", "DATA_RT_REFERENCE.md"]
    if dataset == "wildscenes":
        return ["README.md"] + [f"data/splits/{dim}/{split}.csv"
                               for dim in ("opt2d", "opt3d") for split in ("train", "val", "test")]
    return ["README.md"]

def fetch(url):
    with urllib.request.urlopen(url, timeout=40) as response:
        return response.read()

def acquire(root):
    """Public sources only; at most 20 MB of raw scans and six small split CSVs."""
    for dataset, (repository, revision) in REVISIONS.items():
        for relative in metadata_paths(dataset):
            path = root / dataset / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(fetch(f"https://raw.githubusercontent.com/{repository}/{revision}/{relative}"))
    def listing(sensor, count):
        query = urllib.parse.urlencode({"list-type": "2", "prefix": f"{SEQUENCE}/{sensor}/", "max-keys": count})
        data = fetch("https://boreas.s3.amazonaws.com/?" + query)
        (root / "boreas" / f"list-{sensor}.xml").write_bytes(data)
        return [(node.find("s:Key", NS).text, int(node.find("s:Size", NS).text))
                for node in ET.fromstring(data).findall("s:Contents", NS)]
    radar = listing("radar", 3)
    candidates = listing("lidar", 12)
    selected = dict(radar)
    for key, _ in radar:
        nearest = min(candidates, key=lambda item: abs(int(Path(item[0]).stem) - int(Path(key).stem)))
        selected[nearest[0]] = nearest[1]
    if len(radar) != 3 or sum(selected.values()) > 20_000_000:
        raise ValueError("Public sample does not meet the bounded selection protocol")
    for key, size in selected.items():
        if not key.startswith(SEQUENCE + "/") or ".." in Path(key).parts:
            raise ValueError("Unexpected public object path")
        path = root / "boreas" / key
        path.parent.mkdir(parents=True, exist_ok=True)
        data = fetch("https://boreas.s3.amazonaws.com/" + urllib.parse.quote(key))
        if len(data) != size:
            raise ValueError("Incomplete raw object: " + key)
        path.write_bytes(data)

def audit_splits(directory):
    populations = {}
    for dimension in ("opt2d", "opt3d"):
        populations[dimension] = {}
        for split in ("train", "val", "test"):
            path = directory / "data" / "splits" / dimension / f"{split}.csv"
            with path.open(newline="", encoding="utf-8-sig") as stream:
                rows = list(csv.DictReader(stream))
            identities = [row["id"] for row in rows]
            if not rows or len(set(identities)) != len(identities):
                raise ValueError(f"Empty split or duplicate frame IDs: {path}")
            populations[dimension][split] = {
                "frames": len(rows), "ids": set(identities),
                "recording_groups": dict(sorted(Counter(row["label_path"].split("/")[1] for row in rows).items())),
            }
    overlap = {}
    for dimension, splits in populations.items():
        overlap[dimension] = {f"{a}/{b}": len(splits[a]["ids"] & splits[b]["ids"])
                              for a, b in (("train", "val"), ("train", "test"), ("val", "test"))}
    cross = {f"{a}/{b}": len(populations["opt2d"][a]["ids"] & populations["opt3d"][b]["ids"])
             for a in ("train", "val", "test") for b in ("train", "val", "test")}
    return {"splits": {dim: {split: {key: value for key, value in data.items() if key != "ids"}
                                    for split, data in splits.items()} for dim, splits in populations.items()},
            "within_dimension_id_overlap": overlap, "cross_dimension_id_overlap": cross,
            "limits": "Recording-group overlap is not proof of leakage. No raw terrain labels, predictions or geographic separation audited."}

def scan_metrics(root):
    import numpy as np
    from PIL import Image
    directory = root / "boreas" / SEQUENCE
    radar_files = sorted((directory / "radar").glob("*.png"))
    lidar_files = sorted((directory / "lidar").glob("*.bin"))
    if len(radar_files) != 3 or len(lidar_files) != 3:
        raise ValueError("Expected exactly the three preselected scans of each modality")
    rows = []
    for radar_file in radar_files:
        radar = np.asarray(Image.open(radar_file))
        if radar.dtype != np.uint8 or radar.shape != (400, 3371):
            raise ValueError("Unexpected Boreas radar image layout")
        times = np.ascontiguousarray(radar[:, :8]).view("<i8").reshape(-1)
        if np.any(np.diff(times) <= 0) or int(times[199]) != int(radar_file.stem):
            raise ValueError("Radar timestamps do not follow the documented convention")
        lidar_file = min(lidar_files, key=lambda path: abs(int(path.stem)-int(radar_file.stem)))
        values = np.fromfile(lidar_file, dtype="<f4")
        if values.size % 6 or not np.isfinite(values).all():
            raise ValueError("Invalid LiDAR scan")
        lidar = values.reshape(-1, 6)
        ranges = np.linalg.norm(lidar[:, :3].astype(np.float64), axis=1)
        bins = radar.shape[1] - 11
        rows.append({"radar_file": radar_file.name, "lidar_file": lidar_file.name,
                     "file_offset_ms": (int(lidar_file.stem)-int(radar_file.stem))/1000,
                     "radar_azimuths": len(times), "radar_span_ms": (int(times[-1])-int(times[0]))/1000,
                     "radar_range_bins": bins, "last_bin_center_m": (bins-1)*0.0596-0.31,
                     "lidar_points": len(lidar), "lidar_span_ms": float(np.ptp(lidar[:, 5].astype(np.float64))*1000),
                     "lidar_max_spherical_range_m": float(ranges.max()),
                     "lidar_points_beyond_200_m": int(np.count_nonzero(ranges >= 200))})
    return rows

def analyse(root, output):
    output.mkdir(parents=True, exist_ok=True)
    rows = scan_metrics(root)
    splits = audit_splits(root / "wildscenes")
    sources = []
    for dataset, (repository, revision) in REVISIONS.items():
        for relative in metadata_paths(dataset):
            path = root / dataset / relative
            data = path.read_bytes()
            sources.append({"dataset": dataset, "path": relative, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(), "revision": revision,
                            "url": f"https://raw.githubusercontent.com/{repository}/{revision}/{relative}"})
    for path in sorted((root / "boreas" / SEQUENCE).rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            key = path.relative_to(root / "boreas").as_posix()
            sources.append({"dataset": "boreas", "path": key, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(),
                            "url": "https://boreas.s3.amazonaws.com/" + key})
    with (output / "boreas_scans.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "wildscenes_splits.json").write_text(json.dumps(splits, indent=2) + "\n", encoding="utf-8")
    manifest = {"date": "2026-10-01", "boreas_sequence": SEQUENCE, "radar_scans": 3, "lidar_scans": 3,
                "selection": "First three chronological radar scans, nearest LiDAR from first twelve; preselection before scoring",
                "source_revisions": REVISIONS, "inputs": sources,
                "limits": "CPU decoding and metadata audit. No boxes, detector, weather effect, sensor accuracy or full-dataset results."}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"boreas_scan_pairs": len(rows), "wildscenes_3d_splits": splits["splits"]["opt3d"]}))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results/evidence/findings-oct01/additional-datasets"))
    parser.add_argument("--acquire", action="store_true", help="Download the bounded public inputs to source-root")
    args = parser.parse_args()
    if args.source_root.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("Raw source-root must be outside the Git repository")
    if args.acquire:
        acquire(args.source_root)
    analyse(args.source_root, args.output_dir)

if __name__ == "__main__":
    main()
