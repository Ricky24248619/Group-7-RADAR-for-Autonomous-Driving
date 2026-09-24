"""Checks for support accounting and range/class boundary failures."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from goose_range_support import class_ranges
from truckscenes_object_support import support_counts, summarize


class DatasetSupportTests(unittest.TestCase):
    def test_missing_count_cannot_be_treated_as_zero_support(self):
        for bad in ({}, {"num_lidar_pts": 1}, {"num_lidar_pts": -1, "num_radar_pts": 2},
                    {"num_lidar_pts": 1, "num_radar_pts": 2.5},
                    {"num_lidar_pts": True, "num_radar_pts": 0}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                support_counts(bad)
        self.assertEqual(support_counts({"num_lidar_pts": 0, "num_radar_pts": 0}), [0, 0])

    def test_paired_denominators_and_unique_instances(self):
        rows = [{"instance_token": "same", "sample_token": str(i),
                 "lidar_points": l, "radar_points": r} for i, (l, r) in enumerate([(5, 0), (2, 1), (0, 2), (0, 0)])]
        result = summarize(rows)
        self.assertEqual(result["box_observations"], 4)
        self.assertEqual(result["unique_instances"], 1)
        self.assertEqual(result["samples"], 4)
        self.assertEqual(result["both_supported"], 1)
        self.assertEqual(result["neither_supported"], 1)
        self.assertEqual(result["radar_support_percent"], 50)
        with self.assertRaises(ValueError):
            summarize([])

    def test_class_and_range_counts_preserve_edge_points(self):
        points = np.array([[x, 0, 1000, 0] for x in (0, 50, 100, 150, 400, -50)])
        counts = class_ranges(points, np.array([0, 1, 1, 1, 0, 1]), [0, 1])
        np.testing.assert_array_equal(counts, [[1, 0, 0, 0, 1], [0, 2, 1, 1, 0]])
        self.assertEqual(int(counts.sum()), len(points))

    def test_unknown_labels_and_corrupt_coordinates_fail(self):
        with self.assertRaises(ValueError):
            class_ranges(np.zeros((1, 4)), np.array([2]), [0, 1])
        with self.assertRaises(ValueError):
            class_ranges(np.array([[1, float("nan"), 0, 0]]), np.array([0]), [0])
        with self.assertRaises(ValueError):
            class_ranges(np.zeros((1, 4)), np.array([], dtype=int), [0])


if __name__ == "__main__":
    unittest.main()
