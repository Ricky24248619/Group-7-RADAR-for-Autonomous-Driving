"""Geometry regression tests for the PointPillars input frame (PR #63 review).

No detector, dataset download or inference: the devkit and mmdet3d imports are
stubbed, and the frame maths is plain numpy. The calibration is the real
LIDAR_TOP_FRONT mounting recorded in docs/evidence/pr63-input-frame-audit.json.
"""

import argparse
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "truckscenes_pointpillars_infer.py"

with mock.patch.dict(sys.modules, {
    name: mock.MagicMock() for name in (
        "truckscenes", "truckscenes.utils", "truckscenes.utils.splits",
        "truckscenes.utils.data_classes", "mmdet3d", "mmdet3d.apis",
    )
}):
    _spec = importlib.util.spec_from_file_location("pointpillars_infer_test", SCRIPT)
    runner = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(runner)

# Real LIDAR_TOP_FRONT calibration: pitched ~56.23 degrees down.
LIDAR_ROTATION = [0.8819862253948842, 0.003842179948389126, 0.4712567637354048, 0.0016119865264838775]
LIDAR_TRANSLATION = [5.008, -0.014, 3.234]
LIDAR2EGO = runner.quat_to_matrix4(LIDAR_TRANSLATION, LIDAR_ROTATION)


def ego_pose(yaw_deg, pitch_deg=0.0, roll_deg=0.0, translation=(100.0, -40.0, 2.0)):
    """ego -> global with a heading and, optionally, a slope under the truck."""
    y, p, r = np.radians([yaw_deg, pitch_deg, roll_deg])
    ry = np.array([[np.cos(p), 0, np.sin(p)], [0, 1, 0], [-np.sin(p), 0, np.cos(p)]])
    rx = np.array([[1, 0, 0], [0, np.cos(r), -np.sin(r)], [0, np.sin(r), np.cos(r)]])
    m = np.eye(4)
    m[:3, :3] = runner.rot_z(y) @ ry @ rx
    m[:3, 3] = translation
    return m


def to_model(points_ego, ego2global, model2global):
    """Ego-frame xyz -> model frame, via the script's own native-point path."""
    native = (points_ego - LIDAR2EGO[:3, 3]) @ LIDAR2EGO[:3, :3]
    return runner.points_to_model_frame(native, LIDAR2EGO, ego2global, model2global)


class QuaternionTests(unittest.TestCase):
    def test_rotation_round_trip_including_negative_trace(self):
        for rotation in (LIDAR_ROTATION, [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0],
                         [0.1, 0.7, -0.7, 0.1], [0.70710678, 0.0, 0.0, -0.70710678]):
            q = np.asarray(rotation) / np.linalg.norm(rotation)
            back = runner.rotation_to_quat(runner.quat_to_rotation(q))
            # q and -q are the same rotation.
            self.assertAlmostEqual(abs(float(np.dot(back, q))), 1.0, places=9)

    def test_audit_calibration_tilt_is_reproduced(self):
        # Same figure the review recorded: the native frame is not upright.
        self.assertAlmostEqual(runner.world_up_tilt_deg(LIDAR_ROTATION), 56.2338, places=3)


class UprightFrameTests(unittest.TestCase):
    def test_model_z_is_world_up_even_on_a_slope(self):
        for pose in (ego_pose(0), ego_pose(137.0), ego_pose(-60.0, pitch_deg=4.0, roll_deg=-2.5)):
            frame = runner.upright_virtual_lidar(LIDAR2EGO, pose)
            np.testing.assert_allclose(frame[:3, :3] @ [0, 0, 1], [0, 0, 1], atol=1e-12)

    def test_axes_match_nuscenes_lidar_top(self):
        # nuScenes LIDAR_TOP: x right of the vehicle, y forward, ground at -1.84 m.
        pose = ego_pose(30.0)
        frame = runner.upright_virtual_lidar(LIDAR2EGO, pose)
        sensor_xy = LIDAR2EGO[:2, 3]
        below_sensor = np.array([[*sensor_xy, 0.0]])
        ahead = below_sensor + [10.0, 0.0, 0.0]
        right = below_sensor + [0.0, -3.0, 0.0]

        np.testing.assert_allclose(to_model(below_sensor, pose, frame), [[0, 0, -1.84]], atol=1e-9)
        np.testing.assert_allclose(to_model(ahead, pose, frame), [[0, 10, -1.84]], atol=1e-9)
        np.testing.assert_allclose(to_model(right, pose, frame), [[3, 0, -1.84]], atol=1e-9)

    def test_points_reach_global_unchanged_by_the_detour(self):
        pose = ego_pose(-75.0, pitch_deg=1.5)
        frame = runner.upright_virtual_lidar(LIDAR2EGO, pose)
        native = np.random.default_rng(0).uniform(-20, 20, size=(50, 5))
        model = runner.points_to_model_frame(native, LIDAR2EGO, pose, frame)

        direct = native[:, :3] @ (pose @ LIDAR2EGO)[:3, :3].T + (pose @ LIDAR2EGO)[:3, 3]
        via_model = model[:, :3] @ frame[:3, :3].T + frame[:3, 3]
        np.testing.assert_allclose(via_model, direct, atol=1e-9)
        np.testing.assert_array_equal(model[:, 3:], native[:, 3:])  # intensity, sweep time

    def test_native_frame_still_reproduces_the_historical_run(self):
        pose = ego_pose(10.0)
        np.testing.assert_allclose(
            runner.model_frame_to_global(LIDAR2EGO, pose, "native"), pose @ LIDAR2EGO)
        with self.assertRaises(ValueError):
            runner.model_frame_to_global(LIDAR2EGO, pose, "sideways")


class BoxOutputTests(unittest.TestCase):
    def boxes(self, model2global, yaw=0.3):
        return runner.boxes_model_to_global(
            centers=[[1.0, 12.0, -1.0]], dims=[[4.5, 1.9, 1.6]], yaws=[yaw],
            velocities=[[0.0, 5.0]], scores=[0.8], labels=[0], model2global=model2global)

    def test_upright_frame_gives_upright_boxes_with_the_right_heading(self):
        pose = ego_pose(40.0, pitch_deg=3.0)
        (box,) = self.boxes(runner.upright_virtual_lidar(LIDAR2EGO, pose), yaw=0.3)

        self.assertAlmostEqual(runner.world_up_tilt_deg(box["rotation"]), 0.0, places=6)
        # Box heading in world = ego heading - 90 deg (nuScenes axes) + model yaw.
        r = runner.quat_to_rotation(box["rotation"])
        self.assertAlmostEqual(np.arctan2(r[1, 0], r[0, 0]), np.radians(40.0 - 90.0) + 0.3, places=9)
        # A box moving along model +y (forward) moves along the ego heading.
        heading = [np.cos(np.radians(40.0)), np.sin(np.radians(40.0))]
        np.testing.assert_allclose(box["velocity"], np.multiply(5.0, heading), atol=1e-9)
        self.assertEqual(box["size"], [1.9, 4.5, 1.6])  # (l, w, h) -> (w, l, h)
        self.assertEqual(box["detection_name"], "car")

    def test_native_frame_reproduces_the_reviewed_tilt(self):
        # Regression for the bug itself: the old path tilts boxes like the sensor.
        (box,) = self.boxes(runner.model_frame_to_global(LIDAR2EGO, ego_pose(0), "native"))
        self.assertAlmostEqual(runner.world_up_tilt_deg(box["rotation"]), 56.23, places=1)


class _Tensor(np.ndarray):
    def numpy(self):
        return np.asarray(self)


def _t(values):
    return np.asarray(values, dtype=float).view(_Tensor)


class _Boxes:
    def __init__(self, center, dims, yaw, tensor):
        self.gravity_center, self.dims, self.yaw, self.tensor = center, dims, yaw, tensor

    def __getitem__(self, keep):
        return _Boxes(self.gravity_center[keep], self.dims[keep], self.yaw[keep], self.tensor[keep])


class MainLoopTests(unittest.TestCase):
    def test_model_sees_rectified_points_and_saved_boxes_are_upright(self):
        pose_record = {"translation": [100.0, -40.0, 2.0], "rotation": [np.cos(0.25), 0, 0, np.sin(0.25)]}
        dataset = SimpleNamespace(
            scene=[{"name": "scene-one", "token": "scene"}],
            sample=[{"token": "s", "scene_token": "scene", "data": {"LIDAR_TOP_FRONT": "sd"}}],
            get=lambda table, token: {
                "sample_data": {"calibrated_sensor_token": "c", "ego_pose_token": "p"},
                "calibrated_sensor": {"translation": LIDAR_TRANSLATION, "rotation": LIDAR_ROTATION},
                "ego_pose": pose_record,
            }[table],
        )
        native_points = np.array([[0.0, 0.0, 0.0, 7.0, 0.0]], dtype=np.float32)
        tensor = np.zeros((2, 9)); tensor[:, 7:9] = [0.0, 1.0]
        boxes = _Boxes(_t([[0, 5, -1], [0, 9, -1]]), _t([[4, 2, 1.5]] * 2), _t([0.0, 0.0]), _t(tensor))
        prediction = SimpleNamespace(bboxes_3d=boxes, scores_3d=_t([0.9, 0.05]), labels_3d=_t([0, 0]))
        runner.inference_detector.return_value = (SimpleNamespace(pred_instances_3d=prediction), None)
        runner.create_splits_scenes.return_value = {"mini_val": ["scene-one"]}

        with tempfile.TemporaryDirectory() as folder:
            output = pathlib.Path(folder) / "predictions.json"
            args = argparse.Namespace(
                dataroot=folder, version="v1.2-mini", split="mini_val", limit=None,
                start=0, end=None, out=str(output), channel="LIDAR_TOP_FRONT",
                score_threshold=0.1, input_frame="upright",
                config="unused.py", checkpoint="unused.pth",
            )
            with mock.patch.object(runner, "parse_args", return_value=args), \
                 mock.patch.object(runner, "TruckScenes", return_value=dataset), \
                 mock.patch.object(runner, "load_padded_points", return_value=native_points), \
                 mock.patch.object(sys, "stdout", new_callable=io.StringIO):
                runner.main()
            saved = json.loads(output.read_text())

        # The sensor sits 3.234 m up, directly above the virtual LiDAR at 1.84 m.
        fed = runner.inference_detector.call_args[0][1]
        np.testing.assert_allclose(fed[0, :3], [0.0, 0.0, 3.234 - 1.84], atol=1e-5)
        self.assertEqual(fed[0, 3], 7.0)

        (box,) = saved["results"]["s"]  # the 0.05-score box is filtered out
        self.assertAlmostEqual(runner.world_up_tilt_deg(box["rotation"]), 0.0, places=6)
        self.assertIn("upright input frame", saved["meta"]["description"])


if __name__ == "__main__":
    unittest.main()
