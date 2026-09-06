"""Exercise checkpoint retries without a detector, dataset download or inference."""

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


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "truckscenes_fcos3d_infer.py"


class FcosCheckpointTests(unittest.TestCase):
    def test_retry_replaces_selected_sample_and_preserves_other_chunks(self):
        # The actual CLI loop and JSON checkpointing run; external model/data APIs do not.
        with mock.patch.dict(sys.modules, {
            name: mock.MagicMock() for name in (
                "pyquaternion", "truckscenes", "truckscenes.utils.splits", "mmdet3d.apis"
            )
        }):
            spec = importlib.util.spec_from_file_location("fcos_checkpoint_test", SCRIPT)
            runner = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runner)

        dataset = SimpleNamespace(
            scene=[{"name": "scene-one", "token": "scene"}],
            sample=[
                {"token": token, "scene_token": "scene", "data": {"CAMERA_LEFT_FRONT": "image"}}
                for token in ("selected", "other-chunk")
            ],
            get=lambda table, token: {
                "sample_data": {"calibrated_sensor_token": "calib", "ego_pose_token": "pose", "filename": "image.jpg"},
                "calibrated_sensor": {"camera_intrinsic": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "translation": [0, 0, 0], "rotation": [1, 0, 0, 0]},
                "ego_pose": {"translation": [0, 0, 0], "rotation": [1, 0, 0, 0]},
            }[table],
        )
        prediction = mock.MagicMock()
        kept = mock.MagicMock()
        prediction.scores_3d.__ge__.return_value = kept
        kept.sum.return_value = 1
        runner.inference_mono_3d_detector.return_value.pred_instances_3d = prediction
        runner.create_splits_scenes.return_value = {"mini_val": ["scene-one"]}

        with tempfile.TemporaryDirectory() as folder:
            output = pathlib.Path(folder) / "predictions.json"
            untouched = [{"sample_token": "other-chunk", "detection_score": 0.6}]
            output.write_text(json.dumps({"results": {
                "selected": [{"sample_token": "selected", "detection_score": 0.1}],
                "other-chunk": untouched,
            }}))
            args = argparse.Namespace(
                dataroot=folder, version="v1.2-mini", split="mini_val", limit=None,
                start=0, end=1, out=str(output), cameras=["CAMERA_LEFT_FRONT"],
                config="unused.py", checkpoint="unused.pth",
            )
            with mock.patch.object(runner, "parse_args", return_value=args), \
                 mock.patch.object(runner, "TruckScenes", return_value=dataset), \
                 mock.patch.object(runner, "quat_to_matrix4", return_value=None), \
                 mock.patch.object(runner, "boxes_cam_to_global", side_effect=lambda *a: [{"detection_score": 0.9}]), \
                 mock.patch.object(sys, "stdout", new_callable=io.StringIO):
                for _ in range(2):
                    runner.main()
                    saved = json.loads(output.read_text())["results"]
                    self.assertEqual(saved["selected"], [{"sample_token": "selected", "detection_score": 0.9}])
                    self.assertEqual(saved["other-chunk"], untouched)

                # A rerun with no surviving predictions must also clear stale boxes.
                kept.sum.return_value = 0
                runner.main()
                saved = json.loads(output.read_text())["results"]
                self.assertEqual(saved["selected"], [])
                self.assertEqual(saved["other-chunk"], untouched)


if __name__ == "__main__":
    unittest.main()
