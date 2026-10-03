"""Run the density-matched control over the committed paired-support evidence.

WHAT THIS ANSWERS
-----------------
Record 0016 reports that at 150-400 m, 2,118 of 2,309 released box observations
contain a LiDAR return and 350 contain a radar return. Radar returns reach
189.5 m, so at that distance the gap is not a range limit.

One untested explanation is point count. In these frames LiDAR produces a
median of roughly 78 returns for every radar return. A sensor emitting far more
points lands at least one inside more boxes almost by construction, whatever it
can actually resolve. That is a counting effect, not a sensing difference.

This holds point count constant: give LiDAR the same point budget as radar in
the same frame, and recount support.

WHY THIS READS CSVs RATHER THAN THE DATASET
-------------------------------------------
Subsampling a cloud uniformly at random and asking whether at least `threshold`
of a box's returns survive is the hypergeometric distribution. Every input it
needs is already committed:

  - ``object_counts.csv``        in-box return count per box observation
  - ``sample_channel_ranges.csv``  total returns per frame per modality

so the answer can be computed *exactly* rather than estimated, it agrees with
record 0016 by construction because it uses the same counts that produced it,
and anyone can reproduce it in seconds with no dataset on disk. Re-reading the
9.6 GB release would give a noisier answer to the same question.

The seeded random draws are still reported, because a spread is easier to argue
with than a single number, and because agreement between the draws and the
exact value is itself a check that neither is wrong.

WHAT THIS IS NOT
----------------
Geometric support, not detection. No model is run. Uniform random thinning is
one specific null model: a genuinely lower-resolution LiDAR would thin
structurally, not at random, so this bounds how much of the gap *arithmetic*
explains, not how a cheaper sensor would behave.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from truckscenes_density_matched_support import (
    DEFAULT_DRAWS,
    DEFAULT_SEED,
    SUPPORT_THRESHOLD,
    draw_generator,
    frame_budget,
)

REPO = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = REPO / "docs/evidence/truckscenes/paired-point-motion-support"
DEFAULT_OUTPUT = REPO / "docs/evidence/truckscenes/density-matched"

# Record 0016 reports exact boxes and a 0.5 m sensitivity check. Both are kept
# so the control cannot be accused of holding at one margin only.
MARGINS = ("0.0", "0.5")

# The full-azimuth region is the whole cloud. The forward sector is a subset and
# would understate the budget, so the budget must come from all_azimuth.
BUDGET_REGION = "all_azimuth"

SUMMARY_COLUMNS = [
    "band_m", "margin_m", "threshold", "boxes",
    "full_lidar_supported", "full_lidar_share",
    "radar_supported", "radar_share",
    "matched_expected", "matched_expected_share",
    "matched_p5", "matched_median", "matched_p95",
    "draws", "seed", "denominator",
]

BUDGET_COLUMNS = [
    "sample_token", "lidar_points", "radar_points", "point_budget",
    "reduced", "lidar_to_radar_ratio",
]


def load_frame_totals(path):
    """Total returns per frame per modality, summed over channels and bands.

    The band edges in the source are [0, 50, 100, 150, 400, inf), which covers
    every non-negative range, so summing them gives the whole cloud rather than
    a subset of it.
    """
    totals = collections.defaultdict(int)
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["region"] == BUDGET_REGION:
                totals[(row["sample_token"], row["modality"])] += int(row["count"])
    if not totals:
        raise ValueError(f"No {BUDGET_REGION} rows found in {path}")
    return dict(totals)


def load_box_rows(path):
    """One row per box observation per margin, with its in-box counts."""
    with open(path, encoding="utf-8", newline="") as handle:
        rows = [
            {
                "sample_token": row["sample_token"],
                "band_m": row["band_m"],
                "margin_m": row["margin_m"],
                "lidar_points": int(row["lidar_points"]),
                "radar_points": int(row["radar_points"]),
            }
            for row in csv.DictReader(handle)
        ]
    if not rows:
        raise ValueError(f"No box observations found in {path}")
    return rows


def log_choose(total, chosen):
    """log of total-choose-chosen, via lgamma so large clouds do not overflow."""
    if chosen < 0 or chosen > total:
        return -math.inf
    return (math.lgamma(total + 1) - math.lgamma(chosen + 1)
            - math.lgamma(total - chosen + 1))


def survival_probability(total, in_box, budget, threshold=SUPPORT_THRESHOLD):
    """Chance at least `threshold` of a box's returns survive the subsample.

    Keeping `budget` of `total` returns uniformly at random without replacement
    is the hypergeometric distribution, so this is exact rather than estimated.
    """
    total, in_box, budget = int(total), int(in_box), int(budget)
    if threshold < 1:
        raise ValueError("Threshold must be at least one return")
    if in_box < 0 or budget < 0 or total < in_box or total < budget:
        raise ValueError("Impossible frame: counts must satisfy 0 <= in_box, budget <= total")
    if in_box < threshold:
        return 0.0  # never supported, subsampling cannot create returns
    if budget == total:
        return 1.0  # nothing was discarded

    # P(X >= threshold) = 1 - P(X <= threshold - 1), summed exactly.
    denominator = log_choose(total, budget)
    below = 0.0
    for kept in range(threshold):
        term = log_choose(in_box, kept) + log_choose(total - in_box, budget - kept)
        if term > -math.inf:
            below += math.exp(term - denominator)
    return max(0.0, min(1.0, 1.0 - below))


def frame_table(totals, sample_tokens):
    """Point budget per frame, and whether matching actually discarded anything."""
    table = {}
    for token in sorted(sample_tokens):
        lidar = totals.get((token, "lidar"))
        radar = totals.get((token, "radar"))
        if lidar is None or radar is None:
            raise ValueError(f"Frame {token} is missing a modality total")
        budget, reduced = frame_budget(lidar, radar)
        table[token] = {
            "sample_token": token,
            "lidar_points": lidar,
            "radar_points": radar,
            "point_budget": budget,
            "reduced": reduced,
            "lidar_to_radar_ratio": (lidar / radar) if radar else None,
        }
    return table


def expected_supported(rows, frames, threshold=SUPPORT_THRESHOLD):
    """Exact expected number of supported boxes after density matching.

    Expectation is additive whether or not the per-box outcomes are independent,
    so this total is exact even though boxes in one frame share a subsample.
    """
    return sum(
        survival_probability(
            frames[row["sample_token"]]["lidar_points"],
            row["lidar_points"],
            frames[row["sample_token"]]["point_budget"],
            threshold,
        )
        for row in rows
    )


def group_by_frame(rows):
    """Rows bucketed by sample token, so one frame draws from one stream."""
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[row["sample_token"]].append(row)
    return grouped


def draw_supported(grouped, frames, seed, draw_index, threshold=SUPPORT_THRESHOLD):
    """One seeded random draw: how many boxes keep support this time.

    One generator per (frame, draw), advanced across that frame's boxes. Giving
    each box its own freshly seeded generator would hand every box in a frame
    the same first random value, so boxes with equal counts would rise and fall
    together and the reported spread would be far too narrow.

    Each box is still drawn from its own hypergeometric, which treats boxes in a
    frame as independent. They are not exactly independent under one shared
    subsample, but the clouds hold millions of returns against tens per box, so
    the correlation is negligible -- and this spread is a sanity check on the
    exact expectation above, not the headline number.
    """
    supported = 0
    for token in sorted(grouped):
        frame = frames[token]
        rng = draw_generator(seed, draw_index, token)
        for row in grouped[token]:
            in_box = row["lidar_points"]
            if in_box < threshold:
                continue
            kept = rng.hypergeometric(in_box, frame["lidar_points"] - in_box,
                                      frame["point_budget"])
            supported += int(kept >= threshold)
    return supported


def summarise_band(rows, frames, band, margin, threshold, draws, seed):
    """One summary row: the two baselines, the exact matched value, and the spread."""
    selected = [r for r in rows if r["band_m"] == band and r["margin_m"] == margin]
    boxes = len(selected)
    if boxes == 0:
        return None

    grouped = group_by_frame(selected)
    counts = np.array(
        [draw_supported(grouped, frames, seed, index, threshold) for index in range(draws)],
        dtype=float,
    )
    # Rounded once, then used for both the count and its share, so a reader
    # checking that the share equals count/denominator gets agreement rather
    # than a small residue from two differently rounded numbers.
    expected = round(expected_supported(selected, frames, threshold), 2)

    def share(value):
        return f"{value / boxes:.6f}"

    full_lidar = sum(1 for r in selected if r["lidar_points"] >= threshold)
    radar = sum(1 for r in selected if r["radar_points"] >= threshold)

    return {
        "band_m": band,
        "margin_m": margin,
        "threshold": threshold,
        "boxes": boxes,
        "full_lidar_supported": full_lidar,
        "full_lidar_share": share(full_lidar),
        "radar_supported": radar,
        "radar_share": share(radar),
        "matched_expected": f"{expected:.2f}",
        "matched_expected_share": share(expected),
        "matched_p5": f"{np.percentile(counts, 5):.1f}",
        "matched_median": f"{np.median(counts):.1f}",
        "matched_p95": f"{np.percentile(counts, 95):.1f}",
        "draws": draws,
        "seed": seed,
        "denominator": "released box observations in this band and margin",
    }


def band_order(rows):
    """Bands in distance order, not alphabetical, so a table reads correctly."""
    known = ["0-50", "50-100", "100-150", "150-400", ">=400"]
    present = {row["band_m"] for row in rows}
    ordered = [band for band in known if band in present]
    return ordered + sorted(present - set(ordered))


def write_csv(rows, path, columns):
    """LF endings and no timestamp, so regeneration is byte-identical."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_manifest(object_counts, channel_ranges, frames, draws, seed, threshold):
    """Records what was read and under what rules, so a number can be traced back."""
    reduced = sum(1 for f in frames.values() if f["reduced"])
    ratios = sorted(f["lidar_to_radar_ratio"] for f in frames.values()
                    if f["lidar_to_radar_ratio"] is not None)
    return {
        "analysis": "density-matched LiDAR subsampling control",
        "dataset": "MAN TruckScenes v1.2-mini",
        "source_records": ["0016-truckscenes-paired-point-support",
                           "0017-truckscenes-long-range-evidence-audit"],
        "inputs": {
            "object_counts.csv": sha256(object_counts),
            "sample_channel_ranges.csv": sha256(channel_ranges),
        },
        "frames": len(frames),
        "frames_reduced": reduced,
        "median_lidar_to_radar_ratio": round(ratios[len(ratios) // 2], 2) if ratios else None,
        "support_threshold": threshold,
        "seed": seed,
        "draws": draws,
        "method": (
            "Per frame, keep a uniformly random subset of the LiDAR returns the "
            "size of that frame's radar returns, then recount support. The "
            "expected number of supported boxes is computed exactly from the "
            "hypergeometric distribution; the percentiles come from seeded draws."
        ),
        "limitations": [
            "Geometric support, not detection recall or mAP; no model is run",
            "Uniform random thinning is one null model; a lower-resolution sensor "
            "would thin structurally, not at random",
            "Per-box draws treat boxes in a frame as independent, which affects "
            "the reported spread but not the exact expectation",
            "Inherits every limitation of record 0016, including LiDAR-based "
            "annotation selection and repeated observations across scenes",
            "Recorded radar returns stop near 189.5 m, bounding any statement "
            "about bands beyond it",
        ],
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--threshold", type=int, default=SUPPORT_THRESHOLD)
    return parser.parse_args()


def main():
    args = parse_args()
    object_counts = args.evidence_dir / "object_counts.csv"
    channel_ranges = args.evidence_dir / "sample_channel_ranges.csv"

    rows = load_box_rows(object_counts)
    totals = load_frame_totals(channel_ranges)
    frames = frame_table(totals, {row["sample_token"] for row in rows})

    summary = []
    for margin in MARGINS:
        for band in band_order(rows):
            entry = summarise_band(rows, frames, band, margin, args.threshold,
                                   args.draws, args.seed)
            if entry is not None:
                summary.append(entry)

    write_csv(summary, args.output_dir / "band_summary.csv", SUMMARY_COLUMNS)
    write_csv(
        [{k: ("" if f[k] is None else (f"{f[k]:.2f}" if k == "lidar_to_radar_ratio" else f[k]))
          for k in BUDGET_COLUMNS} for f in frames.values()],
        args.output_dir / "frame_budgets.csv",
        BUDGET_COLUMNS,
    )
    manifest = build_manifest(object_counts, channel_ranges, frames,
                              args.draws, args.seed, args.threshold)
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"{len(frames)} frames, {len(rows)} box rows, {args.draws} draws, seed {args.seed}")
    for entry in summary:
        if entry["margin_m"] == "0.0":
            print(
                f"  {entry['band_m']:>9}  n={entry['boxes']:>6}  "
                f"full LiDAR {entry['full_lidar_supported']:>6}  "
                f"matched {entry['matched_expected']:>8}  "
                f"radar {entry['radar_supported']:>6}"
            )
    print(args.output_dir)


if __name__ == "__main__":
    main()
