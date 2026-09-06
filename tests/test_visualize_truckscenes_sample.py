"""Regression tests for MAN TruckScenes visualisation controls."""

import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from visualize_truckscenes_sample import bounded_scene_count  # noqa: E402


class SceneCountTests(unittest.TestCase):
    def test_clamps_to_available_scenes(self):
        self.assertEqual(bounded_scene_count(5, 10), 5)
        self.assertEqual(bounded_scene_count(99, 10), 10)

    def test_forces_positive_count_when_scenes_exist(self):
        self.assertEqual(bounded_scene_count(0, 10), 1)
        self.assertEqual(bounded_scene_count(-2, 10), 1)

    def test_empty_dataset_returns_zero(self):
        self.assertEqual(bounded_scene_count(5, 0), 0)


if __name__ == "__main__":
    unittest.main()
