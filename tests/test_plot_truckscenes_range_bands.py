"""Regression tests for the MAN TruckScenes range-band figures."""

import pathlib
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from plot_truckscenes_range_bands import (  # noqa: E402
    COUNT_FIGURE,
    SHARE_FIGURE,
    PlotError,
    aggregate_series,
    build_figures,
    check_bands_match,
    read_rows,
    subtitle_for,
)

BANDS = ["0-50 m", "50-100 m", "100-150 m", "150-400 m", "> 400 m"]


def row(scope, modality, band, count, denominator, proportion, samples="10", channel=None):
    return {
        "scope": scope,
        "sample_count": samples,
        "sample_index": "",
        "scene_name": "",
        "sample_token": "",
        "modality": modality,
        "channel": channel or ("RADAR_LEFT_FRONT" if modality == "radar" else "LIDAR_TOP_FRONT"),
        "band_label": band,
        "band_lower_m": "0",
        "band_upper_m": "50",
        "point_count": count,
        "denominator_points": denominator,
        "denominator_scope": "all returns across the measured sample(s) for this modality",
        "proportion_of_denominator": proportion,
        "max_observed_range_m": "189.46",
        "coordinate_frame": "sensor (test)",
    }


def aggregate_rows():
    radar = [1655, 1670, 941, 305, 0]
    lidar = [165520, 53, 15, 0, 0]
    rows = []
    for band, count in zip(BANDS, radar):
        rows.append(row("aggregate", "radar", band, str(count), "4571", f"{count / 4571:.6f}"))
    for band, count in zip(BANDS, lidar):
        rows.append(row("aggregate", "lidar", band, str(count), "165588", f"{count / 165588:.6f}"))
    return rows


def per_sample_noise():
    """Per-sample rows the figures must ignore when aggregating."""
    return [
        {**row("per_sample", "radar", BANDS[0], "999", "999", "1.000000", samples="1"),
         "sample_token": "s1"}
    ]


class AggregateSelectionTests(unittest.TestCase):
    def test_reads_only_the_aggregate_rows(self):
        series = aggregate_series(aggregate_rows() + per_sample_noise(), "radar")

        self.assertEqual(series["labels"], BANDS)
        self.assertEqual(series["counts"], [1655, 1670, 941, 305, 0])
        self.assertEqual(series["denominator"], 4571)
        self.assertEqual(series["sample_count"], 10)

    def test_band_order_follows_the_csv_not_sorting(self):
        series = aggregate_series(aggregate_rows(), "lidar")

        self.assertEqual(series["labels"], BANDS)

    def test_shares_are_converted_to_percentages(self):
        series = aggregate_series(aggregate_rows(), "lidar")

        self.assertAlmostEqual(series["shares"][0], 99.96, places=1)
        self.assertAlmostEqual(series["shares"][3], 0.0, places=6)

    def test_missing_modality_is_an_error_not_an_empty_chart(self):
        rows = [item for item in aggregate_rows() if item["modality"] != "lidar"]

        with self.assertRaises(PlotError):
            aggregate_series(rows, "lidar")

    def test_inconsistent_denominator_is_rejected(self):
        rows = aggregate_rows()
        rows[0]["denominator_points"] = "999"

        with self.assertRaises(PlotError):
            aggregate_series(rows, "radar")


class NoDataTests(unittest.TestCase):
    def rows_with_no_data(self):
        rows = aggregate_rows()
        for item in rows:
            if item["modality"] == "lidar":
                item["point_count"] = "no data"
                item["denominator_points"] = "no data"
                item["proportion_of_denominator"] = "no data"
                item["sample_count"] = "0"
        return rows

    def test_no_data_becomes_none_rather_than_zero(self):
        series = aggregate_series(self.rows_with_no_data(), "lidar")

        self.assertTrue(all(count is None for count in series["counts"]))
        self.assertTrue(all(share is None for share in series["shares"]))
        self.assertIsNone(series["denominator"])

    def test_figures_still_render_when_a_modality_has_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            build_figures(self.rows_with_no_data(), directory)

            self.assertTrue((directory / SHARE_FIGURE).exists())
            self.assertTrue((directory / COUNT_FIGURE).exists())


class SharedAxisTests(unittest.TestCase):
    def test_mismatched_bands_are_refused(self):
        rows = aggregate_rows()
        for item in rows:
            if item["modality"] == "lidar":
                item["band_label"] = item["band_label"] + " (other)"
        series = {
            "radar": aggregate_series(rows, "radar"),
            "lidar": aggregate_series(rows, "lidar"),
        }

        with self.assertRaises(PlotError):
            check_bands_match(series)

    def test_matching_bands_pass(self):
        rows = aggregate_rows()
        check_bands_match(
            {
                "radar": aggregate_series(rows, "radar"),
                "lidar": aggregate_series(rows, "lidar"),
            }
        )


class CaptionTests(unittest.TestCase):
    def test_subtitle_states_sample_count_channels_and_denominators(self):
        rows = aggregate_rows()
        subtitle = subtitle_for(
            {
                "radar": aggregate_series(rows, "radar"),
                "lidar": aggregate_series(rows, "lidar"),
            }
        )

        self.assertIn("10 matched samples", subtitle)
        self.assertIn("RADAR_LEFT_FRONT", subtitle)
        self.assertIn("LIDAR_TOP_FRONT", subtitle)
        self.assertIn("4,571", subtitle)
        self.assertIn("165,588", subtitle)


class OutputTests(unittest.TestCase):
    def test_both_figures_are_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            _, paths = build_figures(aggregate_rows(), directory)

            self.assertEqual([path.name for path in paths], [SHARE_FIGURE, COUNT_FIGURE])
            for path in paths:
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)

    def test_figures_are_byte_identical_across_runs(self):
        """No date or software stamp, so regeneration does not churn the repo."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            first = directory / "first"
            second = directory / "second"
            build_figures(aggregate_rows(), first)
            build_figures(aggregate_rows(), second)

            for name in (SHARE_FIGURE, COUNT_FIGURE):
                self.assertEqual(
                    (first / name).read_bytes(),
                    (second / name).read_bytes(),
                    f"{name} changed between runs",
                )


class InputTests(unittest.TestCase):
    def test_a_missing_csv_names_the_script_that_makes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "nope.csv"

            with self.assertRaises(PlotError) as raised:
                read_rows(missing)
        self.assertIn("truckscenes_range_bands.py", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
