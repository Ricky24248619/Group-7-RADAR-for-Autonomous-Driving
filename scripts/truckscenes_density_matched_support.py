"""Density-matched control for the TruckScenes radar/LiDAR support comparison.

THE QUESTION THIS ANSWERS
-------------------------
Record 0017 reports that at 150-175 m, 93.40% of released boxes contain a
LiDAR return and 22.00% contain a radar return. Radar returns reach 189.5 m,
so at 150-175 m that gap is not a range limit.

One untested explanation is point count. LiDAR produces far more returns than
radar in the same scene, and a sensor that emits many more points will land at
least one inside more boxes almost by construction, whatever it can actually
resolve. That is a counting effect, not a sensing difference.

This module holds point count constant. For each frame it draws a random
subset of the LiDAR cloud the same size as that frame's radar cloud, then
recounts support using the *same* definition. Repeating the draw many times
gives a distribution rather than one lucky or unlucky sample.

  - If the LiDAR advantage survives, the finding is about sensing.
  - If it collapses, a large part of it was point density.

WHAT THIS IS NOT
----------------
Geometric support, not detection. A return inside a box means the sensor put a
point there; it says nothing about whether a detector would find the object.
No model is run here. The recorded radar boundary near 189.5 m bounds any
statement about bands beyond it.

The support test is imported from ``truckscenes_paired_support`` rather than
rewritten, so this control and the analysis it controls for cannot drift apart.
"""

from __future__ import annotations

import hashlib

import numpy as np

from truckscenes_paired_support import inside_box

# A box counts as supported when at least this many returns fall inside it.
# Matches record 0024: ">=1 in-box return defines support".
SUPPORT_THRESHOLD = 1

# Changing this changes every number produced. It is recorded in the output so
# a reader can tell which seed a result came from.
DEFAULT_SEED = 20260929
DEFAULT_DRAWS = 200


def stable_token_hash(sample_token):
    """Turn a sample token into a fixed integer, the same way on every machine.

    Python's built-in hash() is randomised per process, so it cannot be used:
    the same token would seed a different random stream on each run. blake2b is
    stable across runs, processes and platforms.
    """
    digest = hashlib.blake2b(str(sample_token).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def draw_generator(seed, draw_index, sample_token):
    """One independent random stream per (seed, draw, frame).

    Seeding from the sample token rather than the frame's position means the
    stream for a frame does not change if frames are added, removed or
    reordered. Two runs over the same frames give identical draws; a run over a
    subset gives the same draws for the frames it shares.
    """
    return np.random.default_rng([int(seed), int(draw_index), stable_token_hash(sample_token)])


def frame_budget(lidar_count, radar_count):
    """How many LiDAR points this frame is allowed, and whether that reduced it.

    ``reduced`` is False when the LiDAR cloud was already at or below the radar
    count, so nothing was thrown away. Those frames do not test the hypothesis
    and must stay visible in the output rather than being silently folded in
    with the rest.
    """
    lidar_count, radar_count = int(lidar_count), int(radar_count)
    if lidar_count < 0 or radar_count < 0:
        raise ValueError("Point counts cannot be negative")

    budget = min(lidar_count, radar_count)
    return budget, budget < lidar_count


def matched_indices(lidar_count, radar_count, rng):
    """Pick which LiDAR points to keep: a random subset the size of the radar cloud.

    Drawn without replacement, so no point is counted twice. When the LiDAR
    cloud is already small enough every point is kept, in its original order,
    and no randomness is consumed.
    """
    budget, reduced = frame_budget(lidar_count, radar_count)
    if not reduced:
        return np.arange(budget, dtype=int)
    return np.sort(rng.choice(int(lidar_count), size=budget, replace=False))


def count_supported_boxes(points, boxes, margin=0.0, threshold=SUPPORT_THRESHOLD):
    """How many of these boxes contain at least `threshold` of these points.

    The inside-the-box test is imported from the paired-support analysis, so
    "supported" means exactly what it means there.
    """
    points = np.asarray(points, dtype=float)
    supported = 0
    for box in boxes:
        if points.size == 0:
            continue
        hits = inside_box(points, box["center"], box["rotation"], box["size_wlh"], margin)
        if int(np.count_nonzero(hits)) >= threshold:
            supported += 1
    return supported


def frame_draw(frame, seed, draw_index, margin=0.0, threshold=SUPPORT_THRESHOLD):
    """Run one random draw over one frame.

    Returns the box total, how many boxes the density-matched LiDAR supported,
    how many the full LiDAR cloud supported, how many radar supported, and the
    point budget used. The full-LiDAR and radar figures do not depend on the
    draw; they are returned alongside so every draw carries its own baseline
    and no caller has to line up two tables by hand.
    """
    lidar = np.asarray(frame["lidar_points"], dtype=float)
    radar = np.asarray(frame["radar_points"], dtype=float)
    boxes = frame["boxes"]

    for name, cloud in (("lidar_points", lidar), ("radar_points", radar)):
        if cloud.ndim != 2 or cloud.shape[0] != 3:
            raise ValueError(f"{name} must be a 3xN array of points")

    lidar_count, radar_count = lidar.shape[1], radar.shape[1]
    rng = draw_generator(seed, draw_index, frame["sample_token"])
    keep = matched_indices(lidar_count, radar_count, rng)
    budget, reduced = frame_budget(lidar_count, radar_count)

    return {
        "sample_token": frame["sample_token"],
        "draw_index": int(draw_index),
        "boxes": len(boxes),
        "matched_supported": count_supported_boxes(lidar[:, keep], boxes, margin, threshold),
        "full_lidar_supported": count_supported_boxes(lidar, boxes, margin, threshold),
        "radar_supported": count_supported_boxes(radar, boxes, margin, threshold),
        "lidar_points": lidar_count,
        "radar_points": radar_count,
        "point_budget": budget,
        "reduced": bool(reduced),
        "radar_empty": radar_count == 0,
    }


def support_distribution(frames, draws=DEFAULT_DRAWS, seed=DEFAULT_SEED, margin=0.0,
                         threshold=SUPPORT_THRESHOLD):
    """Repeat the whole draw `draws` times and keep every result.

    Returns one row per draw, pooled across frames, plus the two baselines that
    do not vary. Keeping every draw rather than an average is the point: a
    single random subset could be lucky, and the spread across draws is what
    says whether a difference is real.
    """
    frames = list(frames)
    if draws < 1:
        raise ValueError("Need at least one draw")

    totals = {"boxes": 0, "full_lidar_supported": 0, "radar_supported": 0,
              "reduced_frames": 0, "radar_empty_frames": 0,
              "lidar_points": 0, "radar_points": 0, "point_budget": 0}
    per_draw = []

    for draw_index in range(draws):
        matched = 0
        for frame_number, frame in enumerate(frames):
            row = frame_draw(frame, seed, draw_index, margin, threshold)
            matched += row["matched_supported"]
            if draw_index == 0:  # baselines are identical in every draw
                totals["boxes"] += row["boxes"]
                totals["full_lidar_supported"] += row["full_lidar_supported"]
                totals["radar_supported"] += row["radar_supported"]
                totals["reduced_frames"] += int(row["reduced"])
                totals["radar_empty_frames"] += int(row["radar_empty"])
                totals["lidar_points"] += row["lidar_points"]
                totals["radar_points"] += row["radar_points"]
                totals["point_budget"] += row["point_budget"]
        per_draw.append({"draw_index": draw_index, "matched_supported": matched})

    return {
        "seed": int(seed),
        "draws": int(draws),
        "frames": len(frames),
        "support_threshold": int(threshold),
        "box_margin_m": float(margin),
        **totals,
        "per_draw": per_draw,
    }


def summarise_distribution(distribution):
    """Turn the per-draw counts into something reportable.

    Reports the median and the 5th-95th percentile spread of the
    density-matched result, against the two fixed baselines. Percentages are
    shares of the same box total, which is stated so no figure is readable
    without its denominator.
    """
    boxes = distribution["boxes"]
    counts = np.array([row["matched_supported"] for row in distribution["per_draw"]], dtype=float)

    def share(value):
        return None if boxes == 0 else float(value) / boxes

    return {
        "frames": distribution["frames"],
        "boxes": boxes,
        "denominator": "released boxes in the supplied frames",
        "draws": distribution["draws"],
        "seed": distribution["seed"],
        "reduced_frames": distribution["reduced_frames"],
        "radar_empty_frames": distribution["radar_empty_frames"],
        "lidar_points": distribution["lidar_points"],
        "radar_points": distribution["radar_points"],
        "point_budget": distribution["point_budget"],
        "full_lidar_supported": distribution["full_lidar_supported"],
        "full_lidar_share": share(distribution["full_lidar_supported"]),
        "radar_supported": distribution["radar_supported"],
        "radar_share": share(distribution["radar_supported"]),
        "matched_median": float(np.median(counts)),
        "matched_median_share": share(np.median(counts)),
        "matched_p5": float(np.percentile(counts, 5)),
        "matched_p95": float(np.percentile(counts, 95)),
        "matched_min": float(counts.min()),
        "matched_max": float(counts.max()),
    }
