"""Regression tests for the TruckScenes sensor inventory."""

import pathlib
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from truckscenes_sensor_inventory import (  # noqa: E402
    COLUMNS,
    build_rows,
    inferred_model,
    long_range_lidar_channels,
    mount_group,
    write_csv,
)

# Positions taken from the v1.2-mini calibrated_sensor table, so these tests
# fail if the classification stops matching the real dataset.
REAL_POSITIONS = {
    "LIDAR_LEFT": [5.115, 1.279, 2.191],
    "LIDAR_RIGHT": [5.128, -1.299, 2.189],
    "LIDAR_TOP_FRONT": [5.008, -0.014, 3.234],
    "LIDAR_TOP_LEFT": [4.066, 1.407, 3.320],
    "LIDAR_TOP_RIGHT": [4.084, -1.452, 3.303],
    "LIDAR_REAR": [-0.862, 0.000, 0.569],
}


def dataset(channels):
    """Build devkit-shaped sensor and calibrated_sensor tables."""
    sensors, calibrated = [], []
    for index, (channel, modality, translation) in enumerate(channels, start=1):
        token = f"sensor-{index}"
        sensors.append({"token": token, "channel": channel, "modality": modality})
        calibrated.append({"sensor_token": token, "translation": translation})
    return sensors, calibrated


def lidar_dataset():
    return dataset(
        [(channel, "lidar", position) for channel, position in REAL_POSITIONS.items()]
    )


class MountGroupTests(unittest.TestCase):
    def test_corner_module_lidars_are_recognised(self):
        for channel in ("LIDAR_LEFT", "LIDAR_RIGHT"):
            with self.subTest(channel=channel):
                self.assertEqual(mount_group(REAL_POSITIONS[channel]), "corner module")

    def test_roof_lidars_are_recognised(self):
        for channel in ("LIDAR_TOP_FRONT", "LIDAR_TOP_LEFT", "LIDAR_TOP_RIGHT"):
            with self.subTest(channel=channel):
                self.assertEqual(mount_group(REAL_POSITIONS[channel]), "cabin roof")

    def test_trailer_sensor_is_recognised_by_being_behind_the_cab(self):
        self.assertEqual(mount_group(REAL_POSITIONS["LIDAR_REAR"]), "trailer rear")

    def test_a_position_the_paper_does_not_describe_is_not_guessed(self):
        self.assertEqual(mount_group([2.0, 0.0, 6.0]), "unclassified")


class ModelInferenceTests(unittest.TestCase):
    def test_corner_module_lidar_is_the_long_range_model(self):
        model, rated = inferred_model("lidar", "corner module")

        self.assertEqual(model, "Hesai Pandar64")
        self.assertEqual(rated, 200.0)

    def test_roof_and_trailer_lidars_are_the_short_range_model(self):
        for group in ("cabin roof", "trailer rear"):
            with self.subTest(group=group):
                model, rated = inferred_model("lidar", group)
                self.assertEqual(model, "Ouster OS0")
                self.assertEqual(rated, 35.0)

    def test_an_unclassified_lidar_reports_unknown_rather_than_guessing(self):
        model, rated = inferred_model("lidar", "unclassified")

        self.assertEqual(model, "unknown")
        self.assertIsNone(rated)

    def test_radar_model_is_named_without_a_rated_range(self):
        model, rated = inferred_model("radar", "corner module")

        self.assertIn("ARS 548", model)
        self.assertIsNone(rated)


class InventoryTests(unittest.TestCase):
    def test_every_row_has_exactly_the_documented_columns(self):
        rows = build_rows(*lidar_dataset())

        self.assertEqual(len(rows), len(REAL_POSITIONS))
        for row in rows:
            self.assertEqual(sorted(row), sorted(COLUMNS))

    def test_the_six_real_lidars_split_two_corner_and_four_elsewhere(self):
        """The paper states 2 Hesai in corner modules and 4 Ouster elsewhere."""
        rows = build_rows(*lidar_dataset())
        corner = [row for row in rows if row["mount_group"] == "corner module"]
        other = [row for row in rows if row["mount_group"] != "corner module"]

        self.assertEqual(len(corner), 2)
        self.assertEqual(len(other), 4)
        self.assertTrue(all(row["inferred_model"] == "Hesai Pandar64" for row in corner))
        self.assertTrue(all(row["inferred_model"] == "Ouster OS0" for row in other))

    def test_the_channel_used_by_the_range_analysis_is_the_short_range_one(self):
        """LIDAR_TOP_FRONT is a roof Ouster, which is why the comparison is channel-specific."""
        rows = build_rows(*lidar_dataset())
        top_front = next(row for row in rows if row["channel"] == "LIDAR_TOP_FRONT")

        self.assertEqual(top_front["mount_group"], "cabin roof")
        self.assertEqual(top_front["inferred_model"], "Ouster OS0")
        self.assertEqual(top_front["rated_range_m_at_10pct"], "35")

    def test_long_range_channels_are_the_two_corner_lidars(self):
        rows = build_rows(*lidar_dataset())

        self.assertEqual(sorted(long_range_lidar_channels(rows)), ["LIDAR_LEFT", "LIDAR_RIGHT"])

    def test_every_row_records_that_the_model_is_inferred_not_measured(self):
        rows = build_rows(*lidar_dataset())

        for row in rows:
            self.assertIn("inferred", row["evidence"])
            self.assertIn("calibrated_sensor.json", row["evidence"])

    def test_a_calibration_without_a_matching_sensor_is_skipped(self):
        sensors, calibrated = lidar_dataset()
        calibrated.append({"sensor_token": "missing", "translation": [1.0, 0.0, 2.0]})

        self.assertEqual(len(build_rows(sensors, calibrated)), len(REAL_POSITIONS))

    def test_rows_are_ordered_deterministically(self):
        sensors, calibrated = lidar_dataset()

        self.assertEqual(build_rows(sensors, calibrated), build_rows(sensors, calibrated))


class OutputTests(unittest.TestCase):
    def test_written_file_is_byte_identical_across_runs_and_uses_unix_endings(self):
        rows = build_rows(*lidar_dataset())

        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            outputs = []
            for run in ("first", "second"):
                path = directory / f"{run}.csv"
                write_csv(rows, path)
                outputs.append(path.read_bytes())

            self.assertEqual(outputs[0], outputs[1])
            self.assertNotIn(b"\r\n", outputs[0])


if __name__ == "__main__":
    unittest.main()
