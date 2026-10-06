"""Regression tests for the density-matched radar/LiDAR support control.

The control only means anything if three things hold: the subsample really is
the size of the radar cloud, the same seed really does give the same answer on
any machine, and "supported" really does mean what it means in the
paired-support analysis this controls for. Each of those is tested here.
"""

import pathlib
import sys
import unittest

import numpy as np

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from truckscenes_density_matched_support import (  # noqa: E402
    DEFAULT_SEED,
    count_supported_boxes,
    draw_generator,
    frame_budget,
    frame_draw,
    matched_indices,
    stable_token_hash,
    summarise_distribution,
    support_distribution,
)
from truckscenes_paired_support import inside_box  # noqa: E402

# One axis-aligned box centred 10 m ahead. Devkit size is width, length,
# height, so this box spans x in [8, 12], y in [-1, 1], z in [-1, 1].
BOX = {
    "center": np.array([10.0, 0.0, 0.0]),
    "rotation": np.eye(3),
    "size_wlh": np.array([2.0, 4.0, 2.0]),
}


def cloud(count, inside=0, seed=0):
    """A 3xN cloud with `inside` points in BOX and the rest far outside it."""
    rng = np.random.default_rng(seed)
    points = np.empty((3, count), dtype=float)
    points[0, :inside] = rng.uniform(8.5, 11.5, inside)
    points[1, :inside] = rng.uniform(-0.5, 0.5, inside)
    points[2, :inside] = rng.uniform(-0.5, 0.5, inside)
    points[0, inside:] = rng.uniform(40.0, 60.0, count - inside)
    points[1, inside:] = rng.uniform(-20.0, 20.0, count - inside)
    points[2, inside:] = rng.uniform(-2.0, 2.0, count - inside)
    return points


def frame(token, lidar, radar, boxes=(BOX,)):
    return {
        "sample_token": token,
        "lidar_points": lidar,
        "radar_points": radar,
        "boxes": list(boxes),
    }


class SeedStabilityTests(unittest.TestCase):
    def test_token_hash_is_the_same_every_call(self):
        self.assertEqual(stable_token_hash("abc123"), stable_token_hash("abc123"))

    def test_token_hash_does_not_use_pythons_randomised_hash(self):
        """Pinned value. If this changes, previously published draws no longer reproduce."""
        self.assertEqual(stable_token_hash("abc123"), 13299360872850233001)

    def test_different_samples_get_different_streams(self):
        self.assertNotEqual(stable_token_hash("sample-a"), stable_token_hash("sample-b"))

    def test_same_seed_and_draw_give_the_same_random_numbers(self):
        first = draw_generator(7, 3, "token").random(5)
        second = draw_generator(7, 3, "token").random(5)

        np.testing.assert_array_equal(first, second)

    def test_each_draw_index_is_a_different_stream(self):
        first = draw_generator(7, 0, "token").random(5)
        second = draw_generator(7, 1, "token").random(5)

        self.assertFalse(np.array_equal(first, second))


class BudgetTests(unittest.TestCase):
    def test_budget_is_the_radar_point_count(self):
        self.assertEqual(frame_budget(1000, 40), (40, True))

    def test_nothing_is_discarded_when_lidar_is_already_smaller(self):
        budget, reduced = frame_budget(12, 40)

        self.assertEqual(budget, 12)
        self.assertFalse(reduced)

    def test_equal_counts_do_not_count_as_reduced(self):
        self.assertEqual(frame_budget(40, 40), (40, False))

    def test_negative_counts_are_refused(self):
        with self.assertRaises(ValueError):
            frame_budget(-1, 10)


class MatchedIndexTests(unittest.TestCase):
    def test_sample_size_equals_the_radar_point_count(self):
        keep = matched_indices(500, 37, draw_generator(DEFAULT_SEED, 0, "t"))

        self.assertEqual(len(keep), 37)

    def test_no_lidar_point_is_drawn_twice(self):
        keep = matched_indices(500, 200, draw_generator(DEFAULT_SEED, 0, "t"))

        self.assertEqual(len(set(keep.tolist())), 200)

    def test_indices_stay_inside_the_cloud(self):
        keep = matched_indices(500, 200, draw_generator(DEFAULT_SEED, 0, "t"))

        self.assertTrue(keep.min() >= 0 and keep.max() < 500)

    def test_every_point_is_kept_when_lidar_has_fewer_points_than_radar(self):
        keep = matched_indices(9, 40, draw_generator(DEFAULT_SEED, 0, "t"))

        np.testing.assert_array_equal(keep, np.arange(9))

    def test_an_empty_radar_cloud_keeps_no_lidar_points(self):
        keep = matched_indices(500, 0, draw_generator(DEFAULT_SEED, 0, "t"))

        self.assertEqual(len(keep), 0)

    def test_the_same_seed_selects_the_same_points(self):
        first = matched_indices(500, 40, draw_generator(DEFAULT_SEED, 0, "t"))
        second = matched_indices(500, 40, draw_generator(DEFAULT_SEED, 0, "t"))

        np.testing.assert_array_equal(first, second)

    def test_a_different_seed_selects_different_points(self):
        first = matched_indices(500, 40, draw_generator(DEFAULT_SEED, 0, "t"))
        second = matched_indices(500, 40, draw_generator(DEFAULT_SEED + 1, 0, "t"))

        self.assertFalse(np.array_equal(first, second))


class SupportDefinitionTests(unittest.TestCase):
    def test_support_matches_the_paired_support_geometry_test(self):
        """Same boxes, same points, same answer as the analysis being controlled for."""
        points = cloud(300, inside=7, seed=1)

        expected = int(
            np.count_nonzero(
                inside_box(points, BOX["center"], BOX["rotation"], BOX["size_wlh"], 0.0)
            )
            >= 1
        )

        self.assertEqual(count_supported_boxes(points, [BOX]), expected)

    def test_one_in_box_return_is_enough(self):
        self.assertEqual(count_supported_boxes(cloud(50, inside=1, seed=2), [BOX]), 1)

    def test_a_box_with_no_returns_is_not_supported(self):
        self.assertEqual(count_supported_boxes(cloud(50, inside=0, seed=3), [BOX]), 0)

    def test_a_higher_threshold_needs_more_returns(self):
        points = cloud(50, inside=2, seed=4)

        self.assertEqual(count_supported_boxes(points, [BOX], threshold=2), 1)
        self.assertEqual(count_supported_boxes(points, [BOX], threshold=3), 0)

    def test_an_empty_cloud_supports_nothing(self):
        self.assertEqual(count_supported_boxes(np.empty((3, 0)), [BOX]), 0)

    def test_the_margin_is_passed_through_to_the_geometry_test(self):
        just_outside = np.array([[10.0], [1.4], [0.0]])  # half-width is 1.0 m

        self.assertEqual(count_supported_boxes(just_outside, [BOX]), 0)
        self.assertEqual(count_supported_boxes(just_outside, [BOX], margin=0.5), 1)


class FrameDrawTests(unittest.TestCase):
    def test_the_matched_cloud_is_the_size_of_the_radar_cloud(self):
        row = frame_draw(frame("t", cloud(800, inside=60, seed=5), cloud(25, inside=1, seed=6)),
                         DEFAULT_SEED, 0)

        self.assertEqual(row["radar_points"], 25)
        self.assertEqual(row["point_budget"], 25)
        self.assertTrue(row["reduced"])

    def test_the_same_seed_and_draw_give_the_same_row(self):
        given = frame("t", cloud(800, inside=60, seed=5), cloud(25, inside=1, seed=6))

        self.assertEqual(frame_draw(given, DEFAULT_SEED, 0), frame_draw(given, DEFAULT_SEED, 0))

    def test_the_baselines_do_not_change_between_draws(self):
        given = frame("t", cloud(800, inside=60, seed=5), cloud(25, inside=1, seed=6))
        rows = [frame_draw(given, DEFAULT_SEED, index) for index in range(10)]

        self.assertEqual({row["full_lidar_supported"] for row in rows}, {1})
        self.assertEqual({row["radar_supported"] for row in rows}, {1})

    def test_subsampling_can_lose_the_only_in_box_return(self):
        """The whole point of the control: thinning the cloud can remove support."""
        given = frame("t", cloud(800, inside=1, seed=7), cloud(5, inside=0, seed=8))
        matched = {frame_draw(given, DEFAULT_SEED, index)["matched_supported"]
                   for index in range(50)}

        self.assertEqual(frame_draw(given, DEFAULT_SEED, 0)["full_lidar_supported"], 1)
        self.assertIn(0, matched)

    def test_a_frame_with_fewer_lidar_points_than_radar_keeps_its_full_result(self):
        given = frame("t", cloud(6, inside=2, seed=9), cloud(80, inside=0, seed=10))
        row = frame_draw(given, DEFAULT_SEED, 0)

        self.assertFalse(row["reduced"])
        self.assertEqual(row["point_budget"], 6)
        self.assertEqual(row["matched_supported"], row["full_lidar_supported"])

    def test_an_empty_radar_cloud_is_flagged_rather_than_hidden(self):
        row = frame_draw(frame("t", cloud(500, inside=40, seed=11), np.empty((3, 0))),
                         DEFAULT_SEED, 0)

        self.assertTrue(row["radar_empty"])
        self.assertEqual(row["point_budget"], 0)
        self.assertEqual(row["matched_supported"], 0)
        self.assertEqual(row["radar_supported"], 0)

    def test_a_cloud_that_is_not_3xn_is_refused(self):
        with self.assertRaises(ValueError):
            frame_draw(frame("t", np.zeros((4, 10)), cloud(5, seed=14)), DEFAULT_SEED, 0)


class DistributionTests(unittest.TestCase):
    def frames(self):
        return [
            frame("token-a", cloud(600, inside=3, seed=15), cloud(20, inside=1, seed=16)),
            frame("token-b", cloud(400, inside=2, seed=17), cloud(15, inside=0, seed=18)),
        ]

    def test_every_draw_is_returned_not_just_an_average(self):
        result = support_distribution(self.frames(), draws=25)

        self.assertEqual(len(result["per_draw"]), 25)
        self.assertEqual([row["draw_index"] for row in result["per_draw"]], list(range(25)))

    def test_the_draws_actually_vary(self):
        result = support_distribution(self.frames(), draws=40)

        self.assertGreater(len({row["matched_supported"] for row in result["per_draw"]}), 1)

    def test_reordering_the_frames_does_not_change_any_frames_draw(self):
        """Streams are seeded from the sample token, not the frame's position."""
        forward = support_distribution(self.frames(), draws=10)
        backward = support_distribution(self.frames()[::-1], draws=10)

        self.assertEqual(forward["per_draw"], backward["per_draw"])

    def test_the_whole_run_repeats_exactly(self):
        first = support_distribution(self.frames(), draws=15)
        second = support_distribution(self.frames(), draws=15)

        self.assertEqual(first, second)

    def test_a_different_seed_gives_a_different_run(self):
        first = support_distribution(self.frames(), draws=15, seed=DEFAULT_SEED)
        second = support_distribution(self.frames(), draws=15, seed=DEFAULT_SEED + 1)

        self.assertNotEqual(first["per_draw"], second["per_draw"])

    def test_baselines_are_counted_once_per_frame_not_once_per_draw(self):
        result = support_distribution(self.frames(), draws=30)

        self.assertEqual(result["frames"], 2)
        self.assertEqual(result["boxes"], 2)
        self.assertEqual(result["full_lidar_supported"], 2)
        self.assertEqual(result["radar_supported"], 1)
        self.assertEqual(result["radar_points"], 35)
        self.assertEqual(result["point_budget"], 35)
        self.assertEqual(result["reduced_frames"], 2)

    def test_the_seed_and_definition_travel_with_the_result(self):
        result = support_distribution(self.frames(), draws=5, seed=1234)

        self.assertEqual(result["seed"], 1234)
        self.assertEqual(result["support_threshold"], 1)
        self.assertEqual(result["box_margin_m"], 0.0)

    def test_at_least_one_draw_is_required(self):
        with self.assertRaises(ValueError):
            support_distribution(self.frames(), draws=0)

    def test_no_frames_is_an_empty_result_not_a_crash(self):
        result = support_distribution([], draws=3)

        self.assertEqual(result["frames"], 0)
        self.assertEqual([row["matched_supported"] for row in result["per_draw"]], [0, 0, 0])


class SummaryTests(unittest.TestCase):
    def summary(self):
        frames = [
            frame("token-a", cloud(600, inside=3, seed=15), cloud(20, inside=1, seed=16)),
            frame("token-b", cloud(400, inside=2, seed=17), cloud(15, inside=0, seed=18)),
        ]
        return summarise_distribution(support_distribution(frames, draws=40))

    def test_the_median_sits_inside_the_observed_range(self):
        summary = self.summary()

        self.assertLessEqual(summary["matched_min"], summary["matched_median"])
        self.assertLessEqual(summary["matched_median"], summary["matched_max"])

    def test_the_percentile_band_sits_inside_the_observed_range(self):
        summary = self.summary()

        self.assertLessEqual(summary["matched_min"], summary["matched_p5"])
        self.assertLessEqual(summary["matched_p95"], summary["matched_max"])

    def test_every_share_is_reported_against_a_named_denominator(self):
        summary = self.summary()

        self.assertEqual(summary["boxes"], 2)
        self.assertIn("released boxes", summary["denominator"])
        self.assertAlmostEqual(summary["full_lidar_share"], 1.0)
        self.assertAlmostEqual(summary["radar_share"], 0.5)

    def test_shares_are_left_blank_rather_than_dividing_by_zero(self):
        empty = frame("token-a", cloud(50, seed=19), cloud(5, seed=20), boxes=[])
        summary = summarise_distribution(support_distribution([empty], draws=3))

        self.assertEqual(summary["boxes"], 0)
        self.assertIsNone(summary["radar_share"])
        self.assertIsNone(summary["matched_median_share"])


if __name__ == "__main__":
    unittest.main()
