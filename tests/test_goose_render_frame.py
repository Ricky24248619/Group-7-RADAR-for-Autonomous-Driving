"""Focused regression tests for scan/label pairing."""

import pathlib
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from goose_render_frame import find_frames  # noqa: E402


class FindFramesTests(unittest.TestCase):
    @staticmethod
    def touch(root, relative):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return path

    def test_prefers_full_taxonomy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            scan = self.touch(root, "lidar/scene/frame_vls128.bin")
            full = self.touch(root, "labels/scene/frame_goose.label")
            self.touch(root, "labels_challenge/scene/frame_goose.label")

            self.assertEqual(find_frames(root), [(scan, full)])

    def test_falls_back_to_challenge_taxonomy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            scan = self.touch(root, "lidar/scene/frame_vls128.bin")
            challenge = self.touch(root, "labels_challenge/scene/frame_goose.label")

            self.assertEqual(find_frames(root), [(scan, challenge)])

    def test_rejects_mismatched_frame_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.touch(root, "lidar/scene/scan_vls128.bin")
            self.touch(root, "labels/scene/other_goose.label")
            self.touch(root, "labels_challenge/scene/scan_goose.label")

            with self.assertRaisesRegex(SystemExit, "labels/ frame mismatch"):
                find_frames(root)


if __name__ == "__main__":
    unittest.main()
