"""Regression tests for MAN TruckScenes statistics helpers."""

import pathlib
import sys
import unittest

import numpy as np

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from truckscenes_stats import range_counts  # noqa: E402


class RangeCountTests(unittest.TestCase):
    def test_assigns_points_to_documented_range_bands(self):
        distances = np.array([0, 24.999, 25, 49.999, 50, 79.999, 80, 99.999, 100, 149.999, 150, 200])
        points = np.zeros((3, distances.size), dtype=float)
        points[0] = distances

        self.assertEqual(range_counts(points), [2, 2, 2, 2, 2, 2])

    def test_uses_xy_radial_distance_not_height(self):
        points = np.array([[3.0], [4.0], [200.0]])
        self.assertEqual(range_counts(points), [1, 0, 0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
