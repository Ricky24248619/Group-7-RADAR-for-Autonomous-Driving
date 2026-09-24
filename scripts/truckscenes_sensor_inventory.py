"""List every TruckScenes sensor channel with where it is mounted on the truck.

FA-S3-1. The range analysis compares one radar channel against one LiDAR
channel, and the result depends heavily on which physical sensors those are.
TruckScenes carries two different LiDAR models with very different ranges, so
picking the wrong channel would make a sensor-placement effect look like a
modality difference.

The dataset records *where* each sensor sits. It does not record *what* each
sensor is: `sensor.json` holds only a channel name and a modality, and the
official devkit contains no sensor-model information either. The models come
from the MAN TruckScenes paper (NeurIPS 2024), which gives each model's
mounting position:

  - 2x Hesai Pandar64, 200 m at 10% reflectivity, in the two corner
    modules at roughly 2.2 m, alongside two cameras and three radars each.
  - 4x Ouster OS0, 35 m at 10% reflectivity, three on the cabin roof
    "tilted downwards for blindspot coverage" at roughly 3.2 m, and one at
    the rear of the semi-trailer.

This script reports the measured mounting position from the dataset, groups
each sensor by where it sits, and names the model that the paper places
there. The position is measured; the model is an inference from the paper and
is labelled as such in the output. It is not a dataset field.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

try:
    from truckscenes import TruckScenes
except ModuleNotFoundError:  # Allows pure helper tests without the optional devkit.
    TruckScenes = None


CONFIGURED_DATA_ROOT = os.environ.get("TRUCKSCENES_ROOT")
DEFAULT_DATA_ROOT = Path(CONFIGURED_DATA_ROOT) if CONFIGURED_DATA_ROOT else None
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "TruckScenes - Fatima"
DEFAULT_CSV = OUTPUT_DIR / "sensor-inventory.csv"

VERSION = "v1.2-mini"

# Height bands taken from the paper's stated mounting heights, widened enough
# to absorb per-sensor calibration differences of a few centimetres.
CORNER_MODULE_HEIGHT = (1.8, 2.6)
CABIN_ROOF_HEIGHT = (3.0, 3.6)

# What the paper places in each position. Inference, not a dataset field.
LIDAR_MODEL_BY_GROUP = {
    "corner module": ("Hesai Pandar64", 200.0),
    "cabin roof": ("Ouster OS0", 35.0),
    "trailer rear": ("Ouster OS0", 35.0),
}
RADAR_MODEL = ("Continental ARS 548 RDI", None)

EVIDENCE = (
    "position measured from calibrated_sensor.json; model inferred from "
    "MAN TruckScenes paper (NeurIPS 2024) sensor placement"
)

COLUMNS = [
    "channel",
    "modality",
    "x_m",
    "y_m",
    "z_m",
    "mount_group",
    "inferred_model",
    "rated_range_m_at_10pct",
    "evidence",
]


def mount_group(translation):
    """Say where on the truck a sensor sits, from its measured position.

    Only three places exist on this vehicle: the two corner modules beside the
    cab, the cabin roof, and the rear of the trailer. Height separates the
    first two; a negative x puts a sensor behind the cab reference point and
    therefore on the trailer.
    """
    x, y, z = translation[0], translation[1], translation[2]

    if x < 0:
        return "trailer rear"
    if CABIN_ROOF_HEIGHT[0] <= z <= CABIN_ROOF_HEIGHT[1]:
        return "cabin roof"
    if CORNER_MODULE_HEIGHT[0] <= z <= CORNER_MODULE_HEIGHT[1] and abs(y) > 1.0:
        return "corner module"
    if CORNER_MODULE_HEIGHT[0] <= z <= CORNER_MODULE_HEIGHT[1]:
        return "cab front"
    return "unclassified"


def inferred_model(modality, group):
    """Name the model the paper places at this position, or say we cannot tell.

    Returning "unknown" rather than guessing matters: an unclassified mounting
    position means the paper's description does not cover it, and a made-up
    model name would be worse than an honest gap.
    """
    if modality == "lidar":
        return LIDAR_MODEL_BY_GROUP.get(group, ("unknown", None))
    if modality == "radar":
        return RADAR_MODEL
    return ("not applicable", None)


def build_rows(sensors, calibrated_sensors):
    """One row per calibrated sensor, sorted by modality then channel.

    ``sensors`` and ``calibrated_sensors`` are the devkit's own tables, passed
    in as plain lists so this can be tested without the devkit or the data.
    """
    by_token = {sensor["token"]: sensor for sensor in sensors}
    rows = []

    for calibrated in calibrated_sensors:
        sensor = by_token.get(calibrated["sensor_token"])
        if sensor is None:
            continue
        translation = calibrated.get("translation")
        if not translation or len(translation) < 3:
            continue

        group = mount_group(translation)
        model, rated_range = inferred_model(sensor["modality"], group)
        rows.append(
            {
                "channel": sensor["channel"],
                "modality": sensor["modality"],
                "x_m": f"{translation[0]:.3f}",
                "y_m": f"{translation[1]:.3f}",
                "z_m": f"{translation[2]:.3f}",
                "mount_group": group,
                "inferred_model": model,
                "rated_range_m_at_10pct": "" if rated_range is None else f"{rated_range:g}",
                "evidence": EVIDENCE,
            }
        )

    rows.sort(key=lambda row: (row["modality"], row["channel"]))
    return rows


def long_range_lidar_channels(rows):
    """The LiDAR channels the paper puts in the corner modules.

    These are the only LiDARs on this truck rated beyond 35 m, so they are the
    ones a range comparison should use.
    """
    return [
        row["channel"]
        for row in rows
        if row["modality"] == "lidar" and row["mount_group"] == "corner module"
    ]


def write_csv(rows, path):
    """LF line endings, no timestamp -- regeneration produces the same file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.data_root is None:
        raise SystemExit("Provide --data-root or set TRUCKSCENES_ROOT.")
    if TruckScenes is None:
        raise SystemExit("Install truckscenes-devkit before reading the dataset.")

    trucksc = TruckScenes(version=VERSION, dataroot=str(args.data_root), verbose=False)
    rows = build_rows(trucksc.sensor, trucksc.calibrated_sensor)
    write_csv(rows, args.csv_output)

    print(f"{len(rows)} calibrated sensor(s)")
    for row in rows:
        if row["modality"] == "lidar":
            print(
                f"  {row['channel']:18} z={row['z_m']:>7} m  "
                f"{row['mount_group']:14} -> {row['inferred_model']}"
            )
    long_range = long_range_lidar_channels(rows)
    print(f"long-range LiDAR channel(s): {', '.join(long_range) if long_range else 'none found'}")
    print(args.csv_output)


if __name__ == "__main__":
    main()
