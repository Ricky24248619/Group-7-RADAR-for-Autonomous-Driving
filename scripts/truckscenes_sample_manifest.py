"""Write the declared list of MAN TruckScenes samples used by our analysis.

FA-S3-1 requires the sample tokens, channels, coordinate frame and inclusion
rule to be saved *before* the range analysis is extended, so that another team
member can rerun the same subset and obtain the same summary.

This script records which samples are analysed. It measures nothing: no point
counts, no range bands, no model output. Those belong to the range analysis
that reads this manifest.

The sampling policy is unchanged from the Sprint 2 work in
``scripts/truckscenes_stats.py`` and ``scripts/visualize_truckscenes_sample.py``
-- the first annotated sample of each scene, RADAR_LEFT_FRONT paired with
LIDAR_TOP_FRONT. This script only writes that existing policy down in a
machine-readable form; it does not introduce a new one.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

try:
    from truckscenes import TruckScenes
except ModuleNotFoundError:  # Allows pure helper tests without the optional devkit.
    TruckScenes = None


CONFIGURED_DATA_ROOT = os.environ.get("TRUCKSCENES_ROOT")
DEFAULT_DATA_ROOT = Path(CONFIGURED_DATA_ROOT) if CONFIGURED_DATA_ROOT else None
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "TruckScenes - Fatima"
DEFAULT_CSV = OUTPUT_DIR / "sample-manifest.csv"
DEFAULT_JSON = OUTPUT_DIR / "sample-manifest.json"

VERSION = "v1.2-mini"
MANIFEST_VERSION = 1

# The paired channels used by every TruckScenes figure and statistic this
# project has produced so far. One of six radar sensors and one of six lidar
# sensors -- a documented limitation, not full sensor coverage.
RADAR_CHANNEL = "RADAR_LEFT_FRONT"
LIDAR_CHANNEL = "LIDAR_TOP_FRONT"

# Point clouds are read straight from their .pcd files, so each cloud sits in
# its own sensor's coordinate frame. No transform to the ego or global frame is
# applied anywhere in this analysis. Radar and lidar ranges are therefore each
# measured from their own sensor origin, not from a shared origin.
COORDINATE_FRAME = "sensor (per-sensor frame as stored; no ego/global transform applied)"

INCLUSION_RULE = (
    "First annotated sample of every scene in MAN TruckScenes v1.2-mini "
    "(scene['first_sample_token']), in devkit scene-table order. "
    "All scenes are included; none are filtered on weather, location or content."
)

MANIFEST_FIELDS = [
    "index",
    "scene_name",
    "scene_token",
    "sample_token",
    "sample_timestamp",
    "radar_channel",
    "radar_sample_data_token",
    "lidar_channel",
    "lidar_sample_data_token",
    "annotation_count",
    "coordinate_frame",
    "inclusion_rule",
    "record_status",
]


class ManifestError(Exception):
    """Raised when the manifest cannot be trusted as a reproducible subset."""


def build_manifest_rows(scenes, get, radar_channel=RADAR_CHANNEL, lidar_channel=LIDAR_CHANNEL):
    """Turn the devkit's scene records into one manifest row per scene.

    ``scenes`` is the devkit scene table (a list of dicts). ``get`` is the
    devkit's ``get(table_name, token)`` lookup, passed in rather than imported
    so this function can be tested without installing the devkit or the data.

    Row order follows the order of ``scenes``, which is fixed by the released
    metadata file, so two runs over the same release produce the same rows in
    the same order. Nothing time-dependent or machine-dependent is recorded.
    """
    rows = []
    for index, scene in enumerate(scenes, start=1):
        sample = get("sample", scene["first_sample_token"])
        sample_data = sample.get("data", {})

        radar_token = sample_data.get(radar_channel, "")
        lidar_token = sample_data.get(lidar_channel, "")

        rows.append(
            {
                "index": index,
                "scene_name": scene["name"],
                "scene_token": scene["token"],
                "sample_token": sample["token"],
                "sample_timestamp": sample.get("timestamp", ""),
                "radar_channel": radar_channel,
                "radar_sample_data_token": radar_token,
                "lidar_channel": lidar_channel,
                "lidar_sample_data_token": lidar_token,
                "annotation_count": len(sample.get("anns", [])),
                "coordinate_frame": COORDINATE_FRAME,
                "inclusion_rule": INCLUSION_RULE,
                "record_status": record_status(radar_token, lidar_token),
            }
        )
    return rows


def record_status(radar_token, lidar_token):
    """Say plainly whether this sample has both paired channels.

    A sample missing a channel stays in the manifest with its gap named, rather
    than being dropped silently -- a dropped row would quietly change the
    denominator of every later statistic.
    """
    if radar_token and lidar_token:
        return "complete"
    if not radar_token and not lidar_token:
        return "missing_radar_and_lidar"
    if not radar_token:
        return "missing_radar"
    return "missing_lidar"


def assert_unique_sample_tokens(rows):
    """Refuse to write a manifest that lists the same sample twice.

    A duplicated sample would be counted twice by the range analysis and
    silently weight one scene more heavily than the others.
    """
    seen = set()
    duplicates = []
    for row in rows:
        token = row["sample_token"]
        if token in seen:
            duplicates.append(token)
        seen.add(token)
    if duplicates:
        raise ManifestError(
            "Duplicate sample_token(s) in manifest: " + ", ".join(sorted(set(duplicates)))
        )


def manifest_document(rows, version=VERSION):
    """Wrap the rows with the context needed to read them on their own."""
    return {
        "manifest_version": MANIFEST_VERSION,
        "dataset": "MAN TruckScenes",
        "dataset_version": version,
        "generated_by": "scripts/truckscenes_sample_manifest.py",
        "inclusion_rule": INCLUSION_RULE,
        "coordinate_frame": COORDINATE_FRAME,
        "radar_channel": RADAR_CHANNEL,
        "lidar_channel": LIDAR_CHANNEL,
        "sample_count": len(rows),
        "complete_pair_count": sum(1 for row in rows if row["record_status"] == "complete"),
        "samples": rows,
    }


def write_csv(rows, path):
    """Write the manifest as CSV with Unix line endings on every platform.

    Python's csv module defaults to CRLF. This repository normalises line
    endings (.gitattributes) and pins scripts to LF, so a CRLF file would be
    stored as LF in git while the script kept writing CRLF to disk -- the
    committed file and the regenerated file would not be byte-identical, which
    is the one property this manifest exists to provide.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows, path, version=VERSION):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest_document(rows, version), indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.data_root is None:
        raise SystemExit("Provide --data-root or set TRUCKSCENES_ROOT.")
    if TruckScenes is None:
        raise SystemExit("Install truckscenes-devkit before reading the dataset.")

    trucksc = TruckScenes(version=VERSION, dataroot=str(args.data_root), verbose=False)
    rows = build_manifest_rows(trucksc.scene, trucksc.get)
    assert_unique_sample_tokens(rows)

    incomplete = [row for row in rows if row["record_status"] != "complete"]
    for row in incomplete:
        print(f"WARNING: scene {row['scene_name']} is {row['record_status']}")

    write_csv(rows, args.csv_output)
    write_json(rows, args.json_output, VERSION)
    print(f"{len(rows)} sample(s), {len(rows) - len(incomplete)} with both channels present")
    print(args.csv_output)
    print(args.json_output)


if __name__ == "__main__":
    main()
