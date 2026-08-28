#!/usr/bin/env python3
"""Render GOOSE frames by traversability rather than by material (task D3).

Takes Ricky's traversability_map.csv (WORKPLAN §9) and produces the picture that
answers the client's kickoff question — what can I drive over, what can I crash into.

    # all eight scenarios, sheet + per-scenario renders
    python scripts/goose_traversability.py --root <split> --out-dir docs/evidence

    # test an alternative assignment without editing the CSV
    python scripts/goose_traversability.py --root <split> --override bush=2 \
        --out-dir /tmp --tag bush2

Overrides exist so a contested assignment can be compared from pictures rather than
argued about. They never write to the CSV — under the interface contract, assignments
change in Ricky's file, never as exceptions here.

Loading, grouping and the two-panel layout come from goose_render_frame; this module
adds scenario selection, batch rendering and the comparison sheet.
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
    apply_group_map, find_frames, load_frame, load_group_map, render,
)
from goose_contact_sheet import CONDITIONS, by_scenario   # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MAP = REPO / "GOOSE - Ricky+Damien" / "traversability_map.csv"


def apply_overrides(class_to_group, names_by_class, overrides):
    """Reassign named classes to a different traversability id, for comparison only."""
    if not overrides:
        return class_to_group, []
    lookup = {v: k for k, v in names_by_class.items()}
    changed = []
    out = dict(class_to_group)
    for item in overrides:
        cls, _, gid = item.partition("=")
        cls = cls.strip()
        if cls not in lookup:
            sys.exit(f"--override: no GOOSE class named '{cls}'")
        key = lookup[cls]
        changed.append(f"{cls}: {out.get(key)} -> {int(gid)}")
        out[key] = int(gid)
    return out, changed


def class_names_from_map(map_path):
    """label_key -> class_name, read from the traversability map itself."""
    import csv
    with pathlib.Path(map_path).open(newline="", encoding="utf-8-sig") as fh:
        return {int(r["label_key"]): r["class_name"] for r in csv.DictReader(fh)}


def scenario_frames(root):
    """One representative frame per scenario — the same selection D1 used."""
    groups = by_scenario(find_frames(root))
    return {name: pairs[len(pairs) // 2] for name, pairs in sorted(groups.items())}


def distribution(sem, names):
    ids, counts = np.unique(sem, return_counts=True)
    total = counts.sum()
    return {names.get(int(i), f"?{i}"): c / total for i, c in
            sorted(zip(ids, counts), key=lambda t: -t[1])}


def sheet(frames, class_to_group, names, colors, out_path, subtitle):
    """Tile one bird's-eye traversability view per scenario."""
    cols = 4
    rows = -(-len(frames) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4.6 * cols, 4.9 * rows),
                             facecolor="white")
    axes = np.atleast_1d(axes).ravel()

    for ax, (name, pair) in zip(axes, frames.items()):
        points, sem = load_frame(*pair)
        grp = apply_group_map(sem, class_to_group)
        rgb = np.array([colors.get(int(g), np.array([1.0, 0, 1.0])) for g in grp])
        ax.scatter(points[:, 0], points[:, 1], c=rgb, s=0.12, linewidths=0)
        ax.set(xlim=(-100, 100), ylim=(-100, 100), aspect="equal")
        ax.set_facecolor("#0d0d0d")
        ax.set_xticks([]), ax.set_yticks([])
        drivable = (grp == 1).mean()
        ax.set_title(f"{name}\n{CONDITIONS.get(name, '')} · {drivable:.0%} traversable",
                     fontsize=9.5, pad=6)
        ax.plot(0, 0, marker="+", color="white", markersize=8, markeredgewidth=1.1)

    for ax in axes[len(frames):]:
        ax.axis("off")

    fig.legend(handles=[Patch(facecolor=colors[g], label=f"{g} — {names[g]}")
                        for g in sorted(names)],
               loc="lower center", ncol=4, frameon=False, fontsize=10,
               bbox_to_anchor=(0.5, 0.015))
    fig.suptitle("GOOSE — traversability view, one frame per scenario\n" + subtitle,
                 fontsize=13, y=0.985)
    fig.subplots_adjust(top=0.90, bottom=0.10, left=0.02, right=0.98,
                        hspace=0.16, wspace=0.06)
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"  wrote {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--map", default=str(DEFAULT_MAP))
    ap.add_argument("--out-dir", default="docs/evidence")
    ap.add_argument("--tag", default="", help="Suffix for output filenames")
    ap.add_argument("--override", action="append", default=[],
                    metavar="CLASS=ID", help="Comparison only; never writes the CSV")
    ap.add_argument("--per-scenario", action="store_true",
                    help="Also write a full two-panel render per scenario")
    args = ap.parse_args()

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"_{args.tag}" if args.tag else ""

    class_to_group, names, colors = load_group_map(args.map)
    class_names = class_names_from_map(args.map)
    class_to_group, changed = apply_overrides(class_to_group, class_names, args.override)

    subtitle = "assignments as mapped in traversability_map.csv"
    if changed:
        subtitle = "OVERRIDE for comparison — " + "; ".join(changed)
        print("Overrides applied (comparison only):")
        for c in changed:
            print(f"  {c}")

    frames = scenario_frames(args.root)
    print(f"\n{len(frames)} scenarios\n")

    print(f"{'scenario':<38}{'Free':>8}{'Trav':>8}{'Poten':>8}{'Non':>8}")
    for name, pair in frames.items():
        _, sem = load_frame(*pair)
        grp = apply_group_map(sem, class_to_group)
        shares = [(grp == g).mean() for g in range(4)]
        unmapped = (grp == -1).mean()
        flag = f"   UNMAPPED {unmapped:.1%}" if unmapped else ""
        print(f"{name:<38}" + "".join(f"{s:>7.1%}" for s in shares) + flag)

    print()
    sheet(frames, class_to_group, names, colors,
          out_dir / f"goose_traversability_sheet{tag}.png", subtitle)

    if args.per_scenario:
        for name, pair in frames.items():
            points, sem = load_frame(*pair)
            grp = apply_group_map(sem, class_to_group)
            render(points, grp, names, colors,
                   out_dir / f"goose_traversability_{name}{tag}.png",
                   f"GOOSE — {name} · {CONDITIONS.get(name, '')} · traversability")


if __name__ == "__main__":
    main()
