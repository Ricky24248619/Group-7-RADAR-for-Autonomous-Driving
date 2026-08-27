#!/usr/bin/env python3
"""Render one annotated GOOSE LiDAR frame to a PNG.

The devkit ships a vispy visualiser (pointcloud_processing/tools/visualize_3d_data.py)
which opens an interactive window. This is the headless equivalent: it writes an image
file instead, so a frame can be attached as evidence to a survey or a PR without
screenshotting a GUI.

Usage:
    python3 goose_render_frame.py --root ~/datasets/goose/goose_3d_val
    python3 goose_render_frame.py --root ... --index 42 --out frame42.png

Point clouds are float32 [x, y, z, intensity]. Labels are uint32 in SemanticKITTI
packing: semantic id in the low 16 bits, instance id in the high 16 bits.
"""

import argparse
import csv
import pathlib
import sys

import numpy as np
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def load_config(path):
    """Load class names and colours from either taxonomy GOOSE ships.

    The splits carry the full 64-class labels under labels/, described by
    goose_label_mapping.csv (class_name, label_key, has_instance, hex). The devkit's
    vispy visualiser instead expects labels_challenge/ and an 8-class remap in
    common/goose_kitti-visualizer.yaml, whose colour map is BGR per the SemanticKITTI
    convention. Colouring 64-class labels with the 8-class map silently renders most
    of the scene as unknown, so pick the one matching the labels being read.
    """
    # utf-8-sig, not utf-8: Excel on Windows writes a byte-order mark, and Python's
    # default encoding there is the locale codepage rather than UTF-8. Reading with
    # utf-8-sig accepts both BOM and plain UTF-8 on either platform.
    path = pathlib.Path(path)
    if path.suffix == ".csv":
        names, colors = {}, {}
        with path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                key = int(row["label_key"])
                names[key] = row["class_name"]
                h = row["hex"].lstrip("#")
                colors[key] = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0
        return names, colors

    with path.open(encoding="utf-8-sig") as fh:
        cfg = yaml.safe_load(fh)
    names = {int(k): v for k, v in cfg["labels"].items()}
    colors = {int(k): np.array(v[::-1]) / 255.0 for k, v in cfg["color_map"].items()}
    return names, colors


def default_config(root):
    """Prefer the mapping shipped inside the split; fall back to the devkit yaml."""
    csv_path = pathlib.Path(root).expanduser() / "goose_label_mapping.csv"
    if csv_path.is_file():
        return csv_path
    return (pathlib.Path(__file__).resolve().parent.parent
            / "goose_dataset" / "common" / "goose_kitti-visualizer.yaml")


def frame_key(path):
    """Join key for a scan/label pair.

    Scans and labels describe the same frame but carry different trailing tokens --
    <scenario>__<idx>_<timestamp>_vls128.bin against ..._goose.label -- so the shared
    identifier is everything up to the final underscore.
    """
    return path.stem.rsplit("_", 1)[0]


def find_frames(root):
    """Pair each .bin scan with its .label file."""
    root = pathlib.Path(root).expanduser()
    scans = sorted((root / "lidar").rglob("*.bin"))
    if not scans:
        sys.exit(f"No .bin scans under {root / 'lidar'} — is --root the extracted split?")

    label_dirs = [d for d in (root / "labels_challenge", root / "labels") if d.is_dir()]
    if not label_dirs:
        sys.exit(f"No labels_challenge/ or labels/ directory under {root}")

    labels = {frame_key(p): p for d in label_dirs for p in d.rglob("*.label")}
    paired = [(s, labels[frame_key(s)]) for s in scans if frame_key(s) in labels]
    if not paired:
        sys.exit(f"Found {len(scans)} scans and {len(labels)} labels but none matched.")
    return paired


def load_frame(scan_path, label_path):
    points = np.fromfile(scan_path, dtype=np.float32).reshape(-1, 4)
    raw = np.fromfile(label_path, dtype=np.uint32)
    if len(raw) != len(points):
        sys.exit(f"Length mismatch: {len(points)} points vs {len(raw)} labels.")
    return points, raw & 0xFFFF  # low 16 bits are the semantic class


def render(points, sem, names, colors, out_path, title):
    rgb = np.array([colors.get(int(c), np.zeros(3)) for c in sem])
    x, y, z = points[:, 0], points[:, 1], points[:, 2]

    fig = plt.figure(figsize=(15, 13), facecolor="white")
    grid = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.18)
    ax_bev = fig.add_subplot(grid[0])
    ax_side = fig.add_subplot(grid[1])

    ax_bev.scatter(x, y, c=rgb, s=0.3, linewidths=0)
    ax_bev.set(xlabel="x — forward (m)", ylabel="y — left (m)",
               title="Bird's-eye view", aspect="equal")

    # Narrow corridor either side of the driving axis, so the terrain profile along
    # the direction of travel reads clearly instead of the whole scene overplotting.
    corridor = np.abs(y) < 20
    ax_side.scatter(x[corridor], z[corridor], c=rgb[corridor], s=0.3, linewidths=0)
    ax_side.set(xlabel="x — forward (m)", ylabel="z — up (m)",
                title="Side elevation — terrain profile within |y| < 20 m",
                aspect="equal")

    for ax in (ax_bev, ax_side):
        ax.set_facecolor("#0d0d0d")
        ax.grid(alpha=0.15, linewidth=0.4)
        ax.axhline(0, color="white", alpha=0.18, linewidth=0.6)
        ax.axvline(0, color="white", alpha=0.18, linewidth=0.6)

    # Legend ordered by prevalence, so the dominant classes read first.
    ids, counts = np.unique(sem, return_counts=True)
    order = [int(c) for c, _ in sorted(zip(ids, counts), key=lambda t: -t[1])]
    fig.legend(
        handles=[Patch(facecolor=colors.get(c, "k"),
                       label=f"{c} — {names.get(c, '?')}") for c in order],
        loc="lower center", ncol=min(len(order), 6), frameon=False, fontsize=9,
        bbox_to_anchor=(0.5, 0.02),
    )
    fig.suptitle(title, fontsize=14, y=0.985)
    fig.subplots_adjust(top=0.93, bottom=0.11, left=0.07, right=0.97)
    fig.savefig(out_path, dpi=130)
    print(f"Wrote {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="Extracted split, e.g. goose_3d_val/")
    ap.add_argument("--config", default=None,
                    help="Class mapping. Defaults to goose_label_mapping.csv in --root")
    ap.add_argument("--index", type=int, default=0, help="Which paired frame to render")
    ap.add_argument("--out", default="goose_frame.png")
    args = ap.parse_args()

    config = args.config or default_config(args.root)
    print(f"Class mapping: {config}")
    names, colors = load_config(config)
    frames = find_frames(args.root)
    print(f"Found {len(frames)} annotated frames.")

    scan_path, label_path = frames[args.index % len(frames)]
    points, sem = load_frame(scan_path, label_path)

    print(f"\nFrame  : {scan_path.name}")
    print(f"Points : {len(points):,}")
    print(f"Extent : x [{points[:,0].min():.1f}, {points[:,0].max():.1f}] m  "
          f"y [{points[:,1].min():.1f}, {points[:,1].max():.1f}] m  "
          f"z [{points[:,2].min():.1f}, {points[:,2].max():.1f}] m")
    print("\nClass distribution")
    ids, counts = np.unique(sem, return_counts=True)
    for c, n in sorted(zip(ids, counts), key=lambda t: -t[1]):
        print(f"  {int(c):>2}  {names.get(int(c), '?'):<24} {n:>8,}  {n/len(sem):6.2%}")

    render(points, sem, names, colors, args.out, f"GOOSE — {scan_path.name}")


if __name__ == "__main__":
    main()
