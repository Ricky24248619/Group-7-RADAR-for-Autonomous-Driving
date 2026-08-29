#!/usr/bin/env python3
"""Build the single client-facing figure for Adrian and Fabian (task D4).

Two panels of the same frame: what each surface is made of, beside what the vehicle
can drive on. Captioned in plain language, no jargon, no metric names.

    python scripts/goose_client_figure.py --root <split> --scenario <name>
    python scripts/goose_client_figure.py --root <split> --survey   # rank candidates

Both panels use a ground slice rather than a raw bird's-eye view. D3 found that
34-40% of non-traversable points in the open scenarios sit above 1.5 m, so a plain
overhead view paints tree canopy over the drivable ground beneath it and overstates
how blocked the scene is. Keeping the lowest return in each ground cell answers the
question the client actually asked -- what is underneath the vehicle's wheels.
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
    apply_group_map, default_config, load_config, load_frame, load_group_map,
)
from goose_traversability import DEFAULT_MAP, scenario_frames   # noqa: E402
from goose_contact_sheet import CONDITIONS                      # noqa: E402


def ground_slice(points, cell=0.4):
    """Index of the lowest return in each ground cell.

    Slope makes an absolute height threshold unreliable, so this takes the minimum-z
    point per x-y cell instead. On flat ground that is the surface; under a canopy it
    is the ground beneath rather than the leaves above.
    """
    ix = np.floor(points[:, 0] / cell).astype(np.int64)
    iy = np.floor(points[:, 1] / cell).astype(np.int64)
    cell_id = (ix.astype(np.int64) << 32) + iy.astype(np.int64)

    order = np.lexsort((points[:, 2], cell_id))
    sorted_cells = cell_id[order]
    first = np.empty(len(order), dtype=bool)
    first[0] = True
    np.not_equal(sorted_cells[1:], sorted_cells[:-1], out=first[1:])
    return order[first]


def score_candidates(root, class_to_group, limit):
    """Rank scenarios for how clearly they show a route through blocked surroundings.

    Wants a scene that is genuinely mixed: enough drivable ground to read as a route,
    enough blocked ground to read as a hazard, and both present after the ground slice.
    """
    rows = []
    for name, pair in scenario_frames(root).items():
        points, sem = load_frame(*pair)
        keep = ground_slice(points)
        near = np.abs(points[keep, 0]) < limit
        near &= np.abs(points[keep, 1]) < limit
        grp = apply_group_map(sem[keep][near], class_to_group)
        if not len(grp):
            continue
        trav = (grp == 1).mean()
        nont = (grp == 3).mean()
        poten = (grp == 2).mean()
        # Balance beats extremes: a scene that is all road or all forest shows nothing.
        rows.append((min(trav, nont) * (1 - abs(trav - nont)), name,
                     trav, poten, nont, len(grp)))
    return sorted(rows, reverse=True)


CAPTION = (
    "A laser scanner on a vehicle measures the shape of the ground around it, out to "
    "about 100 metres. Every measurement has been labelled by hand.\n"
    "LEFT: what each surface is made of.   RIGHT: the same scene sorted into what a "
    "vehicle could actually drive on.\n"
    "Blue is firm ground — track, gravel, short grass.   Amber is passable but "
    "uncertain — long grass and crops hide whatever lies underneath.   "
    "Red is not drivable — trees, hedges, buildings.\n"
    "The vehicle sits at the white cross. Both views show only the lowest measurement "
    "in each patch of ground, so tree canopy does not hide the route beneath it."
)


def build(root, scenario, map_path, out_path, limit, cell):
    class_to_group, group_names, group_colors = load_group_map(map_path)
    names, colors = load_config(default_config(root))

    pair = scenario_frames(root)[scenario]
    points, sem = load_frame(*pair)

    keep = ground_slice(points, cell)
    pts, lab = points[keep], sem[keep]
    near = (np.abs(pts[:, 0]) < limit) & (np.abs(pts[:, 1]) < limit)
    pts, lab = pts[near], lab[near]
    grp = apply_group_map(lab, class_to_group)

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(16.5, 11.4), facecolor="white")

    ax_l.scatter(pts[:, 0], pts[:, 1],
                 c=[colors.get(int(c), np.zeros(3)) for c in lab], s=1.6, linewidths=0)
    ax_l.set_title("What the ground is made of", fontsize=15, pad=10)

    ax_r.scatter(pts[:, 0], pts[:, 1],
                 c=[group_colors.get(int(g), np.array([1.0, 0, 1.0])) for g in grp],
                 s=1.6, linewidths=0)
    ax_r.set_title("What the vehicle can drive on", fontsize=15, pad=10)

    for ax in (ax_l, ax_r):
        ax.set(xlim=(-limit, limit), ylim=(-limit, limit), aspect="equal")
        ax.set_facecolor("#0d0d0d")
        ax.set_xticks([]), ax.set_yticks([])
        ax.plot(0, 0, marker="+", color="white", markersize=13, markeredgewidth=1.8)

    # Left legend: the materials actually present, most common first.
    ids, counts = np.unique(lab, return_counts=True)
    top = [int(c) for c, _ in sorted(zip(ids, counts), key=lambda t: -t[1])[:9]]
    ax_l.legend(handles=[Patch(facecolor=colors.get(c, "k"),
                               label=names.get(c, "?").replace("_", " "))
                         for c in top],
                loc="upper center", bbox_to_anchor=(0.5, -0.035), ncol=5,
                frameon=False, fontsize=10.5)

    # Only groups with a visible share. A "Free 0%" entry pointing at nothing on the
    # canvas is exactly the kind of detail that makes a reader distrust the figure.
    present = [g for g in sorted(group_names) if (grp == g).mean() >= 0.005]
    ax_r.legend(handles=[Patch(facecolor=group_colors[g],
                               label=f"{group_names[g]}  {(grp == g).mean():.0%}")
                         for g in present],
                loc="upper center", bbox_to_anchor=(0.5, -0.035), ncol=len(present),
                frameon=False, fontsize=11.5)

    fig.suptitle(
        "Can a self-driving truck tell the ground from the obstacles, off-road?\n"
        f"One moment from the GOOSE dataset · {CONDITIONS.get(scenario, '')} · "
        f"{limit * 2:.0f} m across",
        fontsize=18, y=0.972)
    fig.text(0.5, 0.175, CAPTION, ha="center", va="top", fontsize=12,
             linespacing=1.85, color="#222222")
    fig.subplots_adjust(top=0.885, bottom=0.28, left=0.03, right=0.97, wspace=0.04)
    fig.savefig(out_path, dpi=135)
    plt.close(fig)
    print(f"Wrote {out_path}  ({len(pts):,} ground points)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--map", default=str(DEFAULT_MAP))
    ap.add_argument("--scenario", default=None)
    ap.add_argument("--out", default="docs/evidence/goose_client_figure.png")
    ap.add_argument("--limit", type=float, default=50.0,
                    help="Half-width in metres (default 50, so 100 m across)")
    ap.add_argument("--cell", type=float, default=0.4,
                    help="Ground cell size in metres (default 0.4)")
    ap.add_argument("--survey", action="store_true",
                    help="Rank scenarios instead of rendering")
    args = ap.parse_args()

    class_to_group, _, _ = load_group_map(args.map)

    if args.survey or not args.scenario:
        print(f"{'score':>6}  {'scenario':<38}{'Trav':>7}{'Poten':>7}{'Non':>7}"
              f"{'cells':>9}")
        for score, name, t, p, n, cells in score_candidates(
                args.root, class_to_group, args.limit):
            print(f"{score:>6.3f}  {name:<38}{t:>6.0%}{p:>7.0%}{n:>7.0%}{cells:>9,}")
        if args.survey:
            return
        return

    build(args.root, args.scenario, args.map, pathlib.Path(args.out),
          args.limit, args.cell)


if __name__ == "__main__":
    main()
