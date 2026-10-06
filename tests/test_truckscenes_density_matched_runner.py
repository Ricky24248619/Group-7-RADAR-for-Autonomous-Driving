"""Regression tests for the density-matched runner.

The runner's headline number is a probability, so the tests that matter are the
ones checking the probability is right: closed-form cases worked out by hand,
the edges where subsampling cannot change anything, and the agreement between
the exact value and the seeded draws.
"""

import csv
import json
import math
import pathlib
import sys
import tempfile
import unittest

import numpy as np

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from truckscenes_density_matched_runner import (  # noqa: E402
    BUDGET_COLUMNS,
    SUMMARY_COLUMNS,
    band_order,
    build_manifest,
    draw_supported,
    expected_supported,
    frame_table,
    group_by_frame,
    load_box_rows,
    load_frame_totals,
    log_choose,
    summarise_band,
    survival_probability,
    write_csv,
)

SEED = 20260929


def box(token, band="150-400", margin="0.0", lidar=1, radar=0):
    return {"sample_token": token, "band_m": band, "margin_m": margin,
            "lidar_points": lidar, "radar_points": radar}


def totals(**frames):
    """{'a': (lidar, radar)} -> the (token, modality) mapping the runner expects."""
    built = {}
    for token, (lidar, radar) in frames.items():
        built[(token, "lidar")] = lidar
        built[(token, "radar")] = radar
    return built


class LogChooseTests(unittest.TestCase):
    def test_matches_the_exact_binomial_coefficient(self):
        for total, chosen, expected in ((10, 5, 252), (6, 2, 15), (52, 5, 2598960)):
            with self.subTest(total=total, chosen=chosen):
                self.assertAlmostEqual(math.exp(log_choose(total, chosen)), expected, places=3)

    def test_impossible_choices_are_negative_infinity(self):
        self.assertEqual(log_choose(5, 6), -math.inf)
        self.assertEqual(log_choose(5, -1), -math.inf)

    def test_handles_a_cloud_too_large_for_plain_factorials(self):
        """A real frame holds millions of returns; this must not overflow."""
        self.assertTrue(math.isfinite(log_choose(3_000_000, 40_000)))


class SurvivalProbabilityTests(unittest.TestCase):
    def test_a_hand_worked_case(self):
        """10 returns, 1 in the box, keep 5: 1 - C(9,5)/C(10,5) = 1 - 126/252."""
        self.assertAlmostEqual(survival_probability(10, 1, 5), 0.5, places=12)

    def test_a_second_hand_worked_case_at_a_higher_threshold(self):
        """Both of the box's 2 returns must survive: C(2,2)C(8,3)/C(10,5) = 56/252."""
        self.assertAlmostEqual(survival_probability(10, 2, 5, threshold=2),
                               56 / 252, places=12)

    def test_a_box_with_no_returns_can_never_gain_support(self):
        self.assertEqual(survival_probability(1000, 0, 500), 0.0)

    def test_a_box_below_the_threshold_can_never_reach_it(self):
        self.assertEqual(survival_probability(1000, 2, 500, threshold=3), 0.0)

    def test_keeping_everything_keeps_every_box(self):
        self.assertEqual(survival_probability(500, 3, 500), 1.0)

    def test_keeping_nothing_loses_every_box(self):
        self.assertAlmostEqual(survival_probability(500, 3, 0), 0.0, places=12)

    def test_more_returns_in_the_box_never_hurts(self):
        previous = -1.0
        for in_box in range(0, 40):
            value = survival_probability(5000, in_box, 200)
            self.assertGreaterEqual(value, previous)
            previous = value

    def test_a_bigger_budget_never_hurts(self):
        previous = -1.0
        for budget in range(0, 5000, 250):
            value = survival_probability(5000, 6, budget)
            self.assertGreaterEqual(value, previous)
            previous = value

    def test_every_result_is_a_probability(self):
        for total, in_box, budget in ((5000, 1, 60), (5000, 300, 60), (12, 4, 11)):
            with self.subTest(total=total, in_box=in_box, budget=budget):
                self.assertTrue(0.0 <= survival_probability(total, in_box, budget) <= 1.0)

    def test_an_impossible_frame_is_refused(self):
        with self.assertRaises(ValueError):
            survival_probability(10, 20, 5)  # more in the box than in the cloud
        with self.assertRaises(ValueError):
            survival_probability(10, 2, 20)  # budget larger than the cloud

    def test_a_threshold_below_one_is_refused(self):
        with self.assertRaises(ValueError):
            survival_probability(10, 2, 5, threshold=0)

    def test_it_agrees_with_a_brute_force_simulation(self):
        """Independent check: draw the subsample and count, rather than trust the formula."""
        total, in_box, budget = 60, 4, 12
        rng = np.random.default_rng(1)
        hits = sum(int(rng.hypergeometric(in_box, total - in_box, budget) >= 1)
                   for _ in range(40_000))

        self.assertAlmostEqual(hits / 40_000, survival_probability(total, in_box, budget),
                               places=2)


class FrameTableTests(unittest.TestCase):
    def test_the_budget_is_the_radar_point_count(self):
        table = frame_table(totals(a=(10_000, 250)), {"a"})

        self.assertEqual(table["a"]["point_budget"], 250)
        self.assertTrue(table["a"]["reduced"])
        self.assertAlmostEqual(table["a"]["lidar_to_radar_ratio"], 40.0)

    def test_a_frame_already_below_the_radar_count_is_not_reduced(self):
        table = frame_table(totals(a=(80, 250)), {"a"})

        self.assertEqual(table["a"]["point_budget"], 80)
        self.assertFalse(table["a"]["reduced"])

    def test_a_frame_missing_a_modality_is_refused_rather_than_guessed(self):
        with self.assertRaises(ValueError):
            frame_table({("a", "lidar"): 100}, {"a"})


class ExpectedSupportedTests(unittest.TestCase):
    def test_the_total_is_the_sum_of_the_per_box_probabilities(self):
        frames = frame_table(totals(a=(10, 5)), {"a"})
        rows = [box("a", lidar=1), box("a", lidar=1)]

        self.assertAlmostEqual(expected_supported(rows, frames), 1.0, places=12)

    def test_boxes_that_were_never_supported_contribute_nothing(self):
        frames = frame_table(totals(a=(10, 5)), {"a"})

        self.assertEqual(expected_supported([box("a", lidar=0)], frames), 0.0)

    def test_a_frame_needing_no_reduction_keeps_all_its_support(self):
        frames = frame_table(totals(a=(40, 400)), {"a"})
        rows = [box("a", lidar=1), box("a", lidar=7)]

        self.assertAlmostEqual(expected_supported(rows, frames), 2.0, places=12)

    def test_matching_can_only_reduce_support_never_increase_it(self):
        frames = frame_table(totals(a=(50_000, 600)), {"a"})
        rows = [box("a", lidar=n) for n in (1, 2, 5, 40)]

        self.assertLess(expected_supported(rows, frames), len(rows))


class DrawTests(unittest.TestCase):
    def frames_and_rows(self, boxes=60):
        frames = frame_table(totals(a=(20_000, 400), b=(15_000, 300)), {"a", "b"})
        rows = [box("a" if i % 2 else "b", lidar=3) for i in range(boxes)]
        return frames, group_by_frame(rows)

    def test_the_same_seed_and_draw_give_the_same_count(self):
        frames, grouped = self.frames_and_rows()

        self.assertEqual(draw_supported(grouped, frames, SEED, 0),
                         draw_supported(grouped, frames, SEED, 0))

    def test_different_draws_give_different_counts(self):
        frames, grouped = self.frames_and_rows()
        counts = {draw_supported(grouped, frames, SEED, i) for i in range(12)}

        self.assertGreater(len(counts), 1)

    def test_a_different_seed_gives_a_different_run(self):
        frames, grouped = self.frames_and_rows()
        first = [draw_supported(grouped, frames, SEED, i) for i in range(8)]
        second = [draw_supported(grouped, frames, SEED + 1, i) for i in range(8)]

        self.assertNotEqual(first, second)

    def test_identical_boxes_in_one_frame_do_not_all_share_one_outcome(self):
        """Regression: one generator per frame, advanced across its boxes.

        Seeding a fresh generator per box would hand every box in a frame the
        same first random value, so identical boxes would always agree and the
        reported spread would collapse.
        """
        frames = frame_table(totals(a=(4_000, 200)), {"a"})
        grouped = group_by_frame([box("a", lidar=4) for _ in range(40)])
        counts = {draw_supported(grouped, frames, SEED, i) for i in range(20)}

        # If every box moved together the count could only ever be 0 or 40.
        self.assertFalse(counts <= {0, 40})

    def test_boxes_below_the_threshold_are_never_counted(self):
        frames = frame_table(totals(a=(4_000, 200)), {"a"})
        grouped = group_by_frame([box("a", lidar=0) for _ in range(10)])

        self.assertEqual(draw_supported(grouped, frames, SEED, 0), 0)

    def test_the_draws_centre_on_the_exact_expected_value(self):
        """The two methods are independent; disagreement means one is wrong."""
        frames = frame_table(totals(a=(30_000, 500)), {"a"})
        rows = [box("a", lidar=n) for n in (2, 4, 6, 8, 10, 15, 20, 30) * 8]
        grouped = group_by_frame(rows)

        exact = expected_supported(rows, frames)
        drawn = np.mean([draw_supported(grouped, frames, SEED, i) for i in range(120)])

        self.assertAlmostEqual(drawn, exact, delta=max(1.5, 0.05 * exact))


class BandOrderTests(unittest.TestCase):
    def test_bands_come_out_in_distance_order_not_alphabetical(self):
        rows = [box("a", band=b) for b in (">=400", "100-150", "0-50", "150-400", "50-100")]

        self.assertEqual(band_order(rows),
                         ["0-50", "50-100", "100-150", "150-400", ">=400"])

    def test_an_unexpected_band_is_kept_rather_than_dropped(self):
        rows = [box("a", band=b) for b in ("0-50", "weird")]

        self.assertIn("weird", band_order(rows))


class SummaryRowTests(unittest.TestCase):
    def summary(self, margin="0.0"):
        frames = frame_table(totals(a=(20_000, 400)), {"a"})
        rows = [box("a", lidar=5, radar=1) for _ in range(20)]
        rows += [box("a", lidar=0, radar=0) for _ in range(5)]
        return summarise_band(rows, frames, "150-400", margin, 1, 20, SEED)

    def test_an_empty_band_returns_nothing_rather_than_a_row_of_zeros(self):
        frames = frame_table(totals(a=(100, 10)), {"a"})

        self.assertIsNone(summarise_band([box("a")], frames, "0-50", "0.0", 1, 5, SEED))

    def test_the_row_has_exactly_the_documented_columns(self):
        self.assertEqual(sorted(self.summary()), sorted(SUMMARY_COLUMNS))

    def test_the_baselines_are_counted_from_the_rows(self):
        summary = self.summary()

        self.assertEqual(summary["boxes"], 25)
        self.assertEqual(summary["full_lidar_supported"], 20)
        self.assertEqual(summary["radar_supported"], 20)

    def test_every_share_matches_its_own_count_and_denominator(self):
        summary = self.summary()

        self.assertAlmostEqual(float(summary["full_lidar_share"]), 20 / 25, places=6)
        self.assertAlmostEqual(float(summary["radar_share"]), 20 / 25, places=6)
        self.assertAlmostEqual(float(summary["matched_expected_share"]),
                               float(summary["matched_expected"]) / 25, places=4)

    def test_the_exact_value_sits_inside_the_drawn_spread(self):
        summary = self.summary()

        self.assertLessEqual(float(summary["matched_p5"]), float(summary["matched_expected"]))
        self.assertLessEqual(float(summary["matched_expected"]), float(summary["matched_p95"]))

    def test_the_seed_and_denominator_travel_with_the_row(self):
        summary = self.summary()

        self.assertEqual(summary["seed"], SEED)
        self.assertEqual(summary["draws"], 20)
        self.assertIn("released box observations", summary["denominator"])

    def test_rows_of_a_different_margin_are_excluded(self):
        self.assertIsNone(self.summary(margin="0.5"))


class LoadingTests(unittest.TestCase):
    def test_frame_totals_sum_channels_and_bands_but_only_the_full_azimuth(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "ranges.csv"
            path.write_text(
                "sample_token,channel,modality,region,band_m,count\n"
                "a,LIDAR_LEFT,lidar,all_azimuth,0-50,100\n"
                "a,LIDAR_LEFT,lidar,all_azimuth,50-100,20\n"
                "a,LIDAR_RIGHT,lidar,all_azimuth,0-50,5\n"
                "a,LIDAR_LEFT,lidar,forward_30deg,0-50,999\n"
                "a,RADAR_LEFT_FRONT,radar,all_azimuth,0-50,7\n",
                encoding="utf-8",
            )
            loaded = load_frame_totals(path)

        self.assertEqual(loaded[("a", "lidar")], 125)
        self.assertEqual(loaded[("a", "radar")], 7)

    def test_a_file_without_usable_rows_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "ranges.csv"
            path.write_text("sample_token,channel,modality,region,band_m,count\n",
                            encoding="utf-8")
            with self.assertRaises(ValueError):
                load_frame_totals(path)

    def test_box_rows_keep_their_margin_so_both_can_be_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "boxes.csv"
            path.write_text(
                "sample_token,band_m,margin_m,lidar_points,radar_points\n"
                "a,150-400,0.0,4,1\n"
                "a,150-400,0.5,9,1\n",
                encoding="utf-8",
            )
            rows = load_box_rows(path)

        self.assertEqual([r["margin_m"] for r in rows], ["0.0", "0.5"])
        self.assertEqual([r["lidar_points"] for r in rows], [4, 9])


class OutputTests(unittest.TestCase):
    def test_written_files_are_byte_identical_and_use_unix_endings(self):
        frames = frame_table(totals(a=(900, 30)), {"a"})
        rows = [{k: ("" if frames["a"][k] is None else frames["a"][k]) for k in BUDGET_COLUMNS}]

        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            written = []
            for name in ("first", "second"):
                path = directory / f"{name}.csv"
                write_csv(rows, path, BUDGET_COLUMNS)
                written.append(path.read_bytes())

            self.assertEqual(written[0], written[1])
            self.assertNotIn(b"\r\n", written[0])

    def test_the_manifest_records_its_inputs_seed_and_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            for name in ("object_counts.csv", "sample_channel_ranges.csv"):
                (directory / name).write_text("x\n", encoding="utf-8")
            frames = frame_table(totals(a=(900, 30), b=(50, 900)), {"a", "b"})
            manifest = build_manifest(directory / "object_counts.csv",
                                      directory / "sample_channel_ranges.csv",
                                      frames, 200, SEED, 1)

        self.assertEqual(manifest["seed"], SEED)
        self.assertEqual(manifest["frames"], 2)
        self.assertEqual(manifest["frames_reduced"], 1)
        self.assertEqual(len(manifest["inputs"]), 2)
        self.assertTrue(all(len(h) == 64 for h in manifest["inputs"].values()))
        self.assertTrue(any("not detection" in limit for limit in manifest["limitations"]))
        self.assertTrue(any("189.5" in limit for limit in manifest["limitations"]))
        json.dumps(manifest)  # must be serialisable as written


if __name__ == "__main__":
    unittest.main()
