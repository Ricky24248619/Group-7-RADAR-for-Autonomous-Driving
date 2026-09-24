import sys
from pathlib import Path
import unittest
import importlib.util
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from truckscenes_paired_support import inside_box, summarize, deskew_cloud


class PairedSupportTests(unittest.TestCase):
    def test_width_length_order_and_inclusive_3d_boundaries(self):
        points = np.array([[2, 2.01, 0, 0], [1, 0, 1.01, 0], [1.5, 0, 0, 1.51]])
        np.testing.assert_array_equal(inside_box(points, np.zeros(3), np.eye(3), [2,4,3]), [True,False,False,False])
        self.assertTrue(inside_box(points, np.zeros(3), np.eye(3), [2,4,3], .5).all())

    def test_rotated_translated_box(self):
        rotation = np.array([[0,-1,0],[1,0,0],[0,0,1]])
        center = np.array([10,20,30])
        points = rotation @ np.array([[1.9,2.1],[.9,.9],[0,0]]) + center[:,None]
        np.testing.assert_array_equal(inside_box(points, center, rotation, [2,4,2]), [True,False])

    def test_empty_and_invalid_geometry(self):
        self.assertEqual(len(inside_box(np.empty((3,0)), np.zeros(3), np.eye(3), [1,2,3])), 0)
        for size, margin in [([0,2,3],0), ([1,2,3],-.1), ([1,2,np.nan],0)]:
            with self.assertRaises(ValueError):
                inside_box(np.zeros((3,1)), np.zeros(3), np.eye(3), size, margin)

    def test_paired_outcomes_and_threshold(self):
        rows = [dict(lidar_points=l, radar_points=r, instance_token=str(i))
                for i, (l,r) in enumerate([(4,4),(4,0),(0,4),(0,0),(1,2)])]
        one = summarize(rows)
        three = summarize(rows, 3)
        self.assertEqual([one[k] for k in ('both','lidar_only','radar_only','neither')], [2,1,1,1])
        self.assertEqual([three[k] for k in ('both','lidar_only','radar_only','neither')], [1,1,1,2])

    @unittest.skipUnless(importlib.util.find_spec('scipy'), 'Raw-runtime SciPy extra')
    def test_per_point_translation_rotation_and_duplicate_times(self):
        poses = np.array([0, 10000])
        translation = np.array([[0,0,0], [10,0,0]])
        quaternion = np.array([[1,0,0,0], [np.sqrt(.5),0,0,np.sqrt(.5)]])
        points = np.array([[1,1,1,1], [0,0,0,0], [0,0,0,0]])
        result = deskew_cloud(points, [0,5000,5000,10000], np.eye(4), np.eye(4), poses, translation, quaternion)
        np.testing.assert_allclose(result, [[1,5+np.sqrt(.5),5+np.sqrt(.5),10],
                                           [0,np.sqrt(.5),np.sqrt(.5),1],[0,0,0,0]], atol=1e-12)

    @unittest.skipUnless(importlib.util.find_spec('scipy'), 'Raw-runtime SciPy extra')
    def test_per_point_rejects_pose_gap_and_extrapolation(self):
        for times, poses in [([5000], [0,30000]), ([-1], [0,10000]), ([10001], [0,10000])]:
            with self.assertRaises(ValueError):
                deskew_cloud(np.zeros((3,1)), times, np.eye(4), np.eye(4), np.array(poses),
                             np.zeros((2,3)), np.array([[1,0,0,0],[1,0,0,0]]))

    @unittest.skipUnless(importlib.util.find_spec('truckscenes'), 'Raw-runtime devkit extra')
    def test_geometry_agrees_with_official_devkit(self):
        from pyquaternion import Quaternion
        from truckscenes.utils.data_classes import Box
        from truckscenes.utils.geometry_utils import points_in_box
        rng = np.random.default_rng(7)
        for _ in range(50):
            q = Quaternion(axis=rng.normal(size=3), angle=rng.uniform(-3,3))
            center, size = rng.normal(size=3), rng.uniform(.5,5,size=3)
            points = rng.normal(size=(3,1000))*3
            np.testing.assert_array_equal(inside_box(points,center,q.rotation_matrix,size),
                                          points_in_box(Box(center,size,q),points))


if __name__ == '__main__':
    unittest.main()
