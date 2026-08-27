#!/usr/bin/env python3
"""Tile one bird's-eye view per GOOSE scenario into a single contact sheet (task D1).

The validation split spans eight recording days across four seasons, including the
same location two days apart in rain and sun. Seeing them side by side is the fastest
way to understand what the dataset actually covers.

Also prints a per-scenario summary — frame count, points, extent, dominant classes —
which is the raw material for the written observations in findings-damien.md.

    python scripts/goose_contact_sheet.py --root <split> --out sheet.png

Loading logic is imported from goose_render_frame rather than duplicated.
"""

import argparse
import pathlib
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from goose_render_frame import (          # noqa: E402
    default_config, find_frames, load_config, load_frame,
)

# Conditions are not recorded in the data — they are read off the scenario names,
# which encode date and location. Kept here so the sheet is self-describing.
CONDITIONS = {
    "2022-07-22_flight": "Summer",
    "2022-08-30_siegertsbrunn_feldwege": "Summer · field tracks",
    "2022-09-21_garching_uebungsplatz_2": "Autumn · training ground",
    "2022-12-07_aying_hills": "Winter · hills",
    "2023-01-20_aying_mangfall_2": "Winter",
    "2023-03-03_garching_2": "Early spring",
    "2023-05-15_neubiberg_rain": "Spring · RAIN",
    "2023-05-17_neubiberg_sunny": "Spring · SUNNY",
}


def by_scenario(frames):
    """Group (scan, label) pairs by their scenario directory, preserving order."""
    groups = {}
    for scan, label in frames:
        groups.setdefault(scan.parent.name, []).append((scan, label))
    return groups


def summarise(name, pairs, names, sample):
    """Print a summary over `sample` frames and return the middle frame's data."""
    step = max(1, len(pairs) // sample)
    chosen = pairs[::step][:sample]

    totals, points_per_frame, extents = {}, [], []
    for scan, label in chosen:
        points, sem = load_frame(scan, label)
        points_per_frame.append(len(points))
        extents.append((points[:, 0].min(), points[:, 0].max(),
                        points[:, 2].min(), points[:, 2].max()))
        ids, counts = np.unique(sem, return_counts=True)
        for i, c in zip(ids, counts):
            totals[int(i)] = totals.get(int(i), 0) + int(c)

    total = sum(totals.values())
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:5]

    print(f"\n{name}")
    print(f"  condition       {CONDITIONS.get(name, '?')}")
    print(f"  frames in split {len(pairs)}  (sampled {len(chosen)})")
    print(f"  points/frame    mean {np.mean(points_per_frame):,.0f}  "
          f"min {min(points_per_frame):,}  max {max(points_per_frame):,}")
    print(f"  x extent        {min(e[0] for e in extents):.0f} to "
          f"{max(e[1] for e in extents):.0f} m")
    print(f"  z extent        {min(e[2] for e in extents):.0f} to "
          f"{max(e[3] for e in extents):.0f} m")
    print(f"  classes present {len(totals)}")
    print("  dominant        " + ", ".join(
        f"{names.get(k, '?')} {v / total:.0%}" for k, v in top))

    mid = pairs[len(pairs) // 2]
    return mid, totals


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="goose_contact_sheet.png")
    ap.add_argument("--sample", type=int, default=3,
                    help="Frames per scenario to summarise (default 3)")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--limit", type=float, default=100.0,
                    help="Half-width in metres of the plotted window (default 100)")
    args = ap.parse_args()

    names, colors = load_config(default_config(args.root))
    groups = by_scenario(find_frames(args.root))
    print(f"{len(groups)} scenarios, {sum(len(v) for v in groups.values())} frames")

    chosen, grand = {}, {}
    for name in sorted(groups):
        mid, totals = summarise(name, groups[name], names, args.sample)
        chosen[name] = mid
        for k, v in totals.items():
            grand[k] = grand.get(k, 0) + v

    rows = -(-len(groups) // args.cols)
    fig, axes = plt.subplots(rows, args.cols,
                             figsize=(4.6 * args.cols, 4.9 * rows),
                             facecolor="white")
    axes = np.atleast_1d(axes).ravel()

    for ax, name in zip(axes, sorted(groups)):
        points, sem = load_frame(*chosen[name])
        rgb = np.array([colors.get(int(c), np.zeros(3)) for c in sem])
        ax.scatter(points[:, 0], points[:, 1], c=rgb, s=0.12, linewidths=0)
        ax.set(xlim=(-args.limit, args.limit), ylim=(-args.limit, args.limit),
               aspect="equal")
        ax.set_facecolor("#0d0d0d")
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_title(f"{name}\n{CONDITIONS.get(name, '')}", fontsize=9.5, pad=6)
        ax.plot(0, 0, marker="+", color="white", markersize=8, markeredgewidth=1.1)

    for ax in axes[len(groups):]:
        ax.axis("off")

    top = [k for k, _ in sorted(grand.items(), key=lambda kv: -kv[1])[:14]]
    fig.legend(
        handles=[Patch(facecolor=colors.get(k, "k"), label=names.get(k, "?"))
                 for k in top],
        loc="lower center", ncol=7, frameon=False, fontsize=9.5,
        bbox_to_anchor=(0.5, 0.012),
    )
    fig.suptitle(
        "GOOSE validation split — one frame per scenario\n"
        f"bird's-eye view, ±{args.limit:.0f} m, ego vehicle at +. "
        "Colours are the 64-class GOOSE taxonomy; 14 most common shown.",
        fontsize=13, y=0.985)
    fig.subplots_adjust(top=0.90, bottom=0.10, left=0.02, right=0.98,
                        hspace=0.16, wspace=0.06)
    fig.savefig(args.out, dpi=125)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
