"""Geometry and timing regressions without the optional raw devkit."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_truckscenes_raw import align_cloud, check_timing, region_counts, transform_points


class RawComparisonTests(unittest.TestCase):
    def test_alignment_applies_extrinsics_and_reference_motion_in_order(self):
        sensor = np.eye(4)
        sensor[:3, 3] = [5, 1, 2]
        acquisition = np.eye(4)
        acquisition[:3, 3] = [100, 200, 10]
        reference = np.eye(4)
        reference[:3, 3] = [110, 200, 10]
        reference[:2, :2] = [[0, -1], [1, 0]]
        point = np.array([[10], [0], [0]])
        # Global point [115,201,12]; relative to reference [5,1,2]; inverse yaw -> [1,-5,2].
        np.testing.assert_allclose(align_cloud(point, sensor, acquisition, reference), [[1], [-5], [2]], atol=1e-12)

    def test_transform_round_trip(self):
        matrix = np.array([[0, -1, 0, 5], [1, 0, 0, 6], [0, 0, 1, 7], [0, 0, 0, 1]])
        points = np.array([[1, 7], [2, 8], [3, 9]])
        np.testing.assert_allclose(transform_points(transform_points(points, matrix), np.linalg.inv(matrix)), points)

    def test_planar_distance_ignores_height_and_assigns_boundaries(self):
        points = np.array([[0, 49, 50, 100, 150, 400], [0]*6, [1000]*6])
        counts = region_counts(points)
        self.assertEqual(counts["all_azimuth"], [2, 1, 1, 1, 1])
        self.assertEqual(counts["forward_30deg"], [1, 1, 1, 1, 1])

    def test_sector_edges_inclusive_and_rear_excluded(self):
        angles = np.deg2rad([-30, 30, 30.01, -30.01, 180])
        points = np.vstack([10*np.cos(angles), 10*np.sin(angles), np.zeros(5)])
        self.assertEqual(sum(region_counts(points)["forward_30deg"]), 2)
        self.assertEqual(sum(region_counts(points)["all_azimuth"]), 5)

    def test_empty_cloud_has_zero_counts(self):
        self.assertEqual(region_counts(np.empty((3, 0)))["forward_30deg"], [0]*5)

    def test_nonfinite_points_rejected(self):
        for bad in (np.nan, np.inf):
            with self.subTest(bad=bad):
                points = np.array([[1], [2], [bad]])
                with self.assertRaises(ValueError):
                    region_counts(points)
                with self.assertRaises(ValueError):
                    transform_points(points, np.eye(4))

    def test_timing_limits_accept_boundary_and_reject_stale_pose_or_sensor(self):
        check_timing(100000, 150000, 160000, 110000)
        for args in [(100000,150001,150001,100000), (100000,100000,110001,100000),
                     (100000,100000,100000,89999)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                check_timing(*args)


if __name__ == "__main__":
    unittest.main()
