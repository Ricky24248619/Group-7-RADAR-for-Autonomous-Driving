"""Regression tests for the MAN TruckScenes range-band analysis."""

import pathlib
import sys
import tempfile
import unittest

import numpy as np

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from truckscenes_range_bands import (  # noqa: E402
    COLUMNS,
    DEFAULT_BAND_EDGES,
    NO_DATA,
    RangeBandError,
    band_bounds,
    band_label,
    build_rows,
    measure_points,
    parse_band_edges,
    write_csv,
)


def cloud(distances):
    """A point cloud laid out along +x, so radial distance equals the x value."""
    points = np.zeros((3, len(distances)), dtype=float)
    points[0] = distances
    return points


def manifest(sample_tokens=("s1", "s2")):
    return {
        "coordinate_frame": "sensor (test)",
        "samples": [
            {
                "index": index,
                "scene_name": f"scene-{index}",
                "sample_token": token,
                "radar_channel": "RADAR_LEFT_FRONT",
                "lidar_channel": "LIDAR_TOP_FRONT",
            }
            for index, token in enumerate(sample_tokens, start=1)
        ],
    }


class BandEdgeParsingTests(unittest.TestCase):
    def test_parses_the_sprint_3_default_edges(self):
        self.assertEqual(parse_band_edges("0,50,100,150,400"), DEFAULT_BAND_EDGES)

    def test_rejects_non_increasing_edges(self):
        with self.assertRaises(RangeBandError):
            parse_band_edges("0,100,50")

    def test_rejects_a_single_edge(self):
        with self.assertRaises(RangeBandError):
            parse_band_edges("50")

    def test_rejects_negative_and_non_numeric_edges(self):
        with self.assertRaises(RangeBandError):
            parse_band_edges("-10,50")
        with self.assertRaises(RangeBandError):
            parse_band_edges("0,fifty")


class BandLayoutTests(unittest.TestCase):
    def test_an_open_band_is_added_above_the_highest_edge(self):
        bounds = band_bounds([0.0, 50.0, 100.0])

        self.assertEqual(bounds[-1], (100.0, float("inf")))
        self.assertEqual(band_label(*bounds[-1]), "> 100 m")

    def test_default_edges_give_the_four_proposed_bands_plus_an_open_one(self):
        labels = [band_label(low, high) for low, high in band_bounds(DEFAULT_BAND_EDGES)]

        self.assertEqual(
            labels, ["0-50 m", "50-100 m", "100-150 m", "150-400 m", "> 400 m"]
        )

    def test_changing_the_edges_changes_the_bands(self):
        labels = [band_label(low, high) for low, high in band_bounds([0.0, 25.0])]

        self.assertEqual(labels, ["0-25 m", "> 25 m"])


class MeasurementTests(unittest.TestCase):
    def test_points_are_assigned_to_the_band_containing_them(self):
        points = cloud([10, 49.999, 50, 120, 200, 399.999])
        result = measure_points(points, DEFAULT_BAND_EDGES)

        self.assertEqual(result["counts"], [2, 1, 1, 2, 0])
        self.assertEqual(result["total"], 6)

    def test_points_beyond_the_highest_edge_land_in_the_open_band(self):
        result = measure_points(cloud([10, 450, 900]), DEFAULT_BAND_EDGES)

        self.assertEqual(result["counts"][-1], 2)

    def test_band_counts_always_sum_to_the_total(self):
        points = cloud([0, 5, 60, 149, 151, 399, 401, 2000])
        result = measure_points(points, DEFAULT_BAND_EDGES)

        self.assertEqual(sum(result["counts"]), result["total"])

    def test_furthest_return_is_reported(self):
        result = measure_points(cloud([10, 250, 30]), DEFAULT_BAND_EDGES)

        self.assertAlmostEqual(result["max_range"], 250.0)

    def test_an_empty_cloud_has_no_furthest_return(self):
        result = measure_points(cloud([]), DEFAULT_BAND_EDGES)

        self.assertEqual(result["total"], 0)
        self.assertIsNone(result["max_range"])


class RowTests(unittest.TestCase):
    def measurements(self, radar=(10, 60, 200), lidar=(5, 20, 120), missing=()):
        result = {}
        for token in ("s1", "s2"):
            for modality, distances in (("radar", radar), ("lidar", lidar)):
                if (token, modality) in missing:
                    result[(token, modality)] = None
                else:
                    result[(token, modality)] = measure_points(
                        cloud(list(distances)), DEFAULT_BAND_EDGES
                    )
        return result

    def test_every_row_has_exactly_the_documented_columns(self):
        rows = build_rows(manifest(), self.measurements(), DEFAULT_BAND_EDGES)

        for row in rows:
            self.assertEqual(sorted(row), sorted(COLUMNS))

    def test_table_holds_per_sample_and_aggregate_rows_for_both_modalities(self):
        rows = build_rows(manifest(), self.measurements(), DEFAULT_BAND_EDGES)
        bands = len(band_bounds(DEFAULT_BAND_EDGES))

        per_sample = [row for row in rows if row["scope"] == "per_sample"]
        aggregate = [row for row in rows if row["scope"] == "aggregate"]

        self.assertEqual(len(per_sample), 2 * 2 * bands)
        self.assertEqual(len(aggregate), 2 * bands)

    def test_per_sample_proportions_use_that_sample_as_the_denominator(self):
        rows = build_rows(manifest(), self.measurements(), DEFAULT_BAND_EDGES)
        radar = [
            row
            for row in rows
            if row["scope"] == "per_sample"
            and row["modality"] == "radar"
            and row["sample_token"] == "s1"
        ]

        self.assertTrue(all(row["denominator_points"] == 3 for row in radar))
        # Proportions are written to six decimal places, so a repeating value
        # such as 1/3 sums to 0.999999 rather than exactly 1. Allow one
        # rounding step per band rather than pretending the format is exact.
        self.assertAlmostEqual(
            sum(float(row["proportion_of_denominator"]) for row in radar),
            1.0,
            delta=len(radar) * 5e-7,
        )

    def test_aggregate_counts_and_sample_count_cover_every_measured_sample(self):
        rows = build_rows(manifest(), self.measurements(), DEFAULT_BAND_EDGES)
        radar = [
            row for row in rows if row["scope"] == "aggregate" and row["modality"] == "radar"
        ]

        self.assertTrue(all(row["sample_count"] == 2 for row in radar))
        self.assertTrue(all(row["denominator_points"] == 6 for row in radar))
        self.assertEqual(sum(row["point_count"] for row in radar), 6)

    def test_a_missing_channel_reads_no_data_rather_than_zero(self):
        measurements = self.measurements(missing=[("s2", "radar")])
        rows = build_rows(manifest(), measurements, DEFAULT_BAND_EDGES)

        missing = [
            row
            for row in rows
            if row["scope"] == "per_sample"
            and row["modality"] == "radar"
            and row["sample_token"] == "s2"
        ]

        self.assertTrue(missing)
        for row in missing:
            self.assertEqual(row["point_count"], NO_DATA)
            self.assertEqual(row["denominator_points"], NO_DATA)
            self.assertEqual(row["proportion_of_denominator"], NO_DATA)

    def test_aggregate_sample_count_excludes_the_unmeasured_sample(self):
        measurements = self.measurements(missing=[("s2", "radar")])
        rows = build_rows(manifest(), measurements, DEFAULT_BAND_EDGES)
        radar = [
            row for row in rows if row["scope"] == "aggregate" and row["modality"] == "radar"
        ]
        lidar = [
            row for row in rows if row["scope"] == "aggregate" and row["modality"] == "lidar"
        ]

        self.assertTrue(all(row["sample_count"] == 1 for row in radar))
        self.assertTrue(all(row["sample_count"] == 2 for row in lidar))

    def test_an_empty_cloud_keeps_real_zero_counts_but_no_proportion(self):
        measurements = {
            key: measure_points(cloud([]), DEFAULT_BAND_EDGES)
            for key in [
                ("s1", "radar"),
                ("s1", "lidar"),
                ("s2", "radar"),
                ("s2", "lidar"),
            ]
        }
        rows = build_rows(manifest(), measurements, DEFAULT_BAND_EDGES)
        sample_rows = [row for row in rows if row["scope"] == "per_sample"]

        for row in sample_rows:
            self.assertEqual(row["point_count"], 0)
            self.assertEqual(row["proportion_of_denominator"], NO_DATA)
            self.assertEqual(row["max_observed_range_m"], NO_DATA)


class OutputTests(unittest.TestCase):
    def rows(self):
        measurements = {
            (token, modality): measure_points(cloud([10, 60, 200]), DEFAULT_BAND_EDGES)
            for token in ("s1", "s2")
            for modality in ("radar", "lidar")
        }
        return build_rows(manifest(), measurements, DEFAULT_BAND_EDGES)

    def test_written_file_is_byte_identical_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            outputs = []
            for run in ("first", "second"):
                path = directory / f"{run}.csv"
                write_csv(self.rows(), path)
                outputs.append(path.read_bytes())

            self.assertEqual(outputs[0], outputs[1])

    def test_written_file_uses_unix_line_endings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bands.csv"
            write_csv(self.rows(), path)

            self.assertNotIn(b"\r\n", path.read_bytes())

    def test_header_names_every_documented_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bands.csv"
            write_csv(self.rows(), path)
            header = path.read_text(encoding="utf-8").splitlines()[0]

        self.assertEqual(header.split(","), COLUMNS)


class ReuseTests(unittest.TestCase):
    def test_existing_six_band_behaviour_of_range_counts_is_unchanged(self):
        """The Sprint 2 default must still produce the numbers in record 0009."""
        from truckscenes_stats import RANGE_EDGES, range_counts

        points = cloud([0, 24.999, 25, 49.999, 50, 79.999, 80, 99.999, 100, 149.999, 150, 200])

        self.assertEqual(range_counts(points), [2, 2, 2, 2, 2, 2])
        self.assertEqual(range_counts(points, RANGE_EDGES), [2, 2, 2, 2, 2, 2])


if __name__ == "__main__":
    unittest.main()
