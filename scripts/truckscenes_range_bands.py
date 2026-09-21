"""Count matched RADAR and LiDAR returns by distance band, per sample and in total.

FA-S3-1. The sample subset comes from the committed manifest written by
``scripts/truckscenes_sample_manifest.py`` -- this script never decides for
itself which samples to measure, so the declared subset stays the single
source of truth.

WHAT THIS MEASURES: how many sensor returns fall within each distance band.
That is sensor *coverage*. It is not object-detection accuracy, and a
populated far band is not evidence that anything can be detected at that
distance. The stock TruckScenes v1.2.0 evaluator produces no detection score
beyond 150 m at all.

Band edges are a command-line option, not a constant, because the band
decision is still open -- see "TruckScenes - Fatima/RANGE-BANDS-OPEN-QUESTION.md".

Range is computed as sqrt(x^2 + y^2) in each sensor's own coordinate frame,
reusing ``range_counts`` from ``scripts/truckscenes_stats.py`` rather than
reimplementing it. Radar and LiDAR ranges are therefore measured from two
different physical positions on the truck.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import numpy as np

from truckscenes_stats import range_counts

try:
    from truckscenes import TruckScenes
    from truckscenes.utils.data_classes import LidarPointCloud, RadarPointCloud
except ModuleNotFoundError:  # Allows pure helper tests without the optional devkit.
    TruckScenes = None
    LidarPointCloud = None
    RadarPointCloud = None


CONFIGURED_DATA_ROOT = os.environ.get("TRUCKSCENES_ROOT")
DEFAULT_DATA_ROOT = Path(CONFIGURED_DATA_ROOT) if CONFIGURED_DATA_ROOT else None
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "TruckScenes - Fatima"
DEFAULT_MANIFEST = OUTPUT_DIR / "sample-manifest.json"
DEFAULT_CSV = OUTPUT_DIR / "range-bands.csv"

VERSION = "v1.2-mini"

# Proposed in docs/metrics-definitions.md, open question 3. NOT an agreed
# team decision -- override with --band-edges.
DEFAULT_BAND_EDGES = [0.0, 50.0, 100.0, 150.0, 400.0]

# Written into every row where a count could not be measured. A band that was
# measured and genuinely held no points is a real 0; a band that could not be
# measured at all is NOT 0, and conflating the two would misstate the
# denominator. docs/metrics-definitions.md requires this distinction.
NO_DATA = "no data"

COLUMNS = [
    "scope",
    "sample_count",
    "sample_index",
    "scene_name",
    "sample_token",
    "modality",
    "channel",
    "band_label",
    "band_lower_m",
    "band_upper_m",
    "point_count",
    "denominator_points",
    "denominator_scope",
    "proportion_of_denominator",
    "max_observed_range_m",
    "coordinate_frame",
]

MODALITIES = [
    ("radar", "radar_channel", "radar_sample_data_token"),
    ("lidar", "lidar_channel", "lidar_sample_data_token"),
]


class RangeBandError(Exception):
    """Raised when the requested bands or manifest cannot be used."""


def parse_band_edges(text):
    """Turn "0,50,100,150,400" into a list of ascending float edges.

    Rejects anything that would silently produce meaningless bands: fewer than
    two edges, a negative edge, or edges that do not strictly increase.
    """
    try:
        edges = [float(part) for part in text.split(",") if part.strip() != ""]
    except ValueError as error:
        raise RangeBandError(f"Band edges must be numbers: {text}") from error

    if len(edges) < 2:
        raise RangeBandError("Give at least two band edges, e.g. 0,50,100,150,400")
    if edges[0] < 0:
        raise RangeBandError("The first band edge cannot be negative")
    if any(high <= low for low, high in zip(edges, edges[1:])):
        raise RangeBandError(f"Band edges must strictly increase: {edges}")
    return edges


def band_bounds(edges):
    """Pair up the edges, then add one open band above the highest edge.

    The open top band matters: with edges ending at 400 m, a return at 450 m
    would otherwise belong to no band and vanish from the table while still
    sitting in the point cloud. Every point lands in exactly one band, so the
    proportions always add up to the whole.
    """
    bounds = list(zip(edges[:-1], edges[1:]))
    bounds.append((edges[-1], float("inf")))
    return bounds


def band_label(lower, upper):
    if upper == float("inf"):
        return f"> {lower:g} m"
    return f"{lower:g}-{upper:g} m"


def measure_points(points, edges):
    """Summarise one point cloud: per-band counts, total, and furthest return."""
    counts = range_counts(points, edges + [float("inf")])
    total = int(points.shape[1])
    if total:
        radial = np.linalg.norm(points[:2, :], axis=0)
        furthest = float(np.max(radial))
    else:
        furthest = None
    return {"counts": counts, "total": total, "max_range": furthest}


def format_proportion(count, denominator):
    """A proportion needs a denominator greater than zero to mean anything."""
    if denominator in (None, 0):
        return NO_DATA
    return f"{count / denominator:.6f}"


def format_max_range(value):
    return NO_DATA if value is None else f"{value:.2f}"


def per_sample_rows(manifest_row, modality, channel, measurement, edges, coordinate_frame):
    """One row per band for one sample and one modality.

    ``measurement`` is None when that channel was not available for the sample.
    Those rows are still written, with counts reading "no data", so a missing
    channel stays visible instead of quietly shrinking the table.
    """
    rows = []
    for index, (lower, upper) in enumerate(band_bounds(edges)):
        if measurement is None:
            count = NO_DATA
            denominator = NO_DATA
            proportion = NO_DATA
            furthest = NO_DATA
        else:
            count = measurement["counts"][index]
            denominator = measurement["total"]
            proportion = format_proportion(count, measurement["total"])
            furthest = format_max_range(measurement["max_range"])

        rows.append(
            {
                "scope": "per_sample",
                "sample_count": 1,
                "sample_index": manifest_row["index"],
                "scene_name": manifest_row["scene_name"],
                "sample_token": manifest_row["sample_token"],
                "modality": modality,
                "channel": channel,
                "band_label": band_label(lower, upper),
                "band_lower_m": f"{lower:g}",
                "band_upper_m": "inf" if upper == float("inf") else f"{upper:g}",
                "point_count": count,
                "denominator_points": denominator,
                "denominator_scope": "all returns in this sample and modality",
                "proportion_of_denominator": proportion,
                "max_observed_range_m": furthest,
                "coordinate_frame": coordinate_frame,
            }
        )
    return rows


def aggregate_rows(modality, channel, measurements, edges, coordinate_frame):
    """One row per band totalling every sample in which this modality was measured.

    ``sample_count`` is the number of samples actually behind these totals, not
    the number of samples in the manifest. If a channel were missing from one
    sample, the aggregate would say 9, not 10.
    """
    measured = [item for item in measurements if item is not None]
    band_count = len(band_bounds(edges))

    if not measured:
        totals = [NO_DATA] * band_count
        denominator = NO_DATA
        furthest = NO_DATA
    else:
        totals = [sum(item["counts"][i] for item in measured) for i in range(band_count)]
        denominator = sum(item["total"] for item in measured)
        ranges = [item["max_range"] for item in measured if item["max_range"] is not None]
        furthest = format_max_range(max(ranges) if ranges else None)

    rows = []
    for index, (lower, upper) in enumerate(band_bounds(edges)):
        count = totals[index]
        rows.append(
            {
                "scope": "aggregate",
                "sample_count": len(measured),
                "sample_index": "",
                "scene_name": "",
                "sample_token": "",
                "modality": modality,
                "channel": channel,
                "band_label": band_label(lower, upper),
                "band_lower_m": f"{lower:g}",
                "band_upper_m": "inf" if upper == float("inf") else f"{upper:g}",
                "point_count": count,
                "denominator_points": denominator,
                "denominator_scope": (
                    f"all returns across the {len(measured)} measured sample(s) "
                    "for this modality"
                ),
                "proportion_of_denominator": (
                    NO_DATA
                    if count == NO_DATA
                    else format_proportion(count, denominator)
                ),
                "max_observed_range_m": furthest,
                "coordinate_frame": coordinate_frame,
            }
        )
    return rows


def build_rows(manifest, measurements, edges):
    """Assemble the whole table: every per-sample row first, then the aggregates.

    ``measurements`` maps (sample_token, modality) to a measure_points result,
    or to None where the channel was unavailable.
    """
    coordinate_frame = manifest.get("coordinate_frame", "")
    samples = manifest["samples"]
    rows = []

    for manifest_row in samples:
        for modality, channel_field, _token_field in MODALITIES:
            rows.extend(
                per_sample_rows(
                    manifest_row,
                    modality,
                    manifest_row[channel_field],
                    measurements.get((manifest_row["sample_token"], modality)),
                    edges,
                    coordinate_frame,
                )
            )

    for modality, channel_field, _token_field in MODALITIES:
        channel = samples[0][channel_field] if samples else ""
        rows.extend(
            aggregate_rows(
                modality,
                channel,
                [measurements.get((row["sample_token"], modality)) for row in samples],
                edges,
                coordinate_frame,
            )
        )
    return rows


def write_csv(rows, path):
    """Write the table with LF line endings so regeneration is byte-identical."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_manifest(path):
    if not path.exists():
        raise RangeBandError(
            f"Manifest not found: {path}. Run scripts/truckscenes_sample_manifest.py first."
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not manifest.get("samples"):
        raise RangeBandError(f"Manifest {path} lists no samples.")
    return manifest


def measure_from_devkit(trucksc, data_root, manifest, edges):
    """Load each cloud named by the manifest and measure it.

    The manifest's sample-data tokens are used directly, so this reads exactly
    the clouds the manifest declares rather than looking the channels up again.
    """
    measurements = {}
    for row in manifest["samples"]:
        for modality, _channel_field, token_field in MODALITIES:
            token = row[token_field]
            if not token:
                measurements[(row["sample_token"], modality)] = None
                print(f"WARNING: {row['scene_name']} has no {modality} record; recording 'no data'")
                continue
            sample_data = trucksc.get("sample_data", token)
            path = data_root / sample_data["filename"]
            cloud_class = RadarPointCloud if modality == "radar" else LidarPointCloud
            cloud = cloud_class.from_file(str(path))
            measurements[(row["sample_token"], modality)] = measure_points(cloud.points, edges)
    return measurements


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--band-edges",
        default=",".join(f"{edge:g}" for edge in DEFAULT_BAND_EDGES),
        help="Comma-separated band edges in metres. An open band above the "
        "highest edge is always added.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.data_root is None:
        raise SystemExit("Provide --data-root or set TRUCKSCENES_ROOT.")
    if TruckScenes is None:
        raise SystemExit("Install truckscenes-devkit before reading the dataset.")

    try:
        edges = parse_band_edges(args.band_edges)
        manifest = load_manifest(args.manifest)
    except RangeBandError as error:
        raise SystemExit(str(error))

    trucksc = TruckScenes(version=VERSION, dataroot=str(args.data_root), verbose=False)
    measurements = measure_from_devkit(trucksc, args.data_root, manifest, edges)
    rows = build_rows(manifest, measurements, edges)
    write_csv(rows, args.csv_output)

    labels = [band_label(low, high) for low, high in band_bounds(edges)]
    print(f"{len(manifest['samples'])} sample(s) from {args.manifest.name}")
    print(f"bands: {', '.join(labels)}")
    print(f"{len(rows)} row(s) written")
    print(args.csv_output)


if __name__ == "__main__":
    main()
