"""Protocol regressions: unseen selection, denominators, and verified ZIP inputs."""
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_goose_followup import unseen_index
from acquire_truckdrive_followup import member
from analyse_sprint_followup import terrain_summary, equal_track_support, class_range_rows, hash_repository_text


class FollowupTests(unittest.TestCase):
    def test_repository_hash_is_stable_across_git_line_endings(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.json"
            path.write_bytes(b'{\n  "value": 1\n}\n')
            original = hash_repository_text(path)
            path.write_bytes(b'{\r\n  "value": 1\r\n}\r\n')
            self.assertEqual(hash_repository_text(path), original)
            path.write_bytes(b'{\n  "value": 2\n}\n')
            self.assertNotEqual(hash_repository_text(path), original)

    def test_unseen_selection_changes_only_for_previously_evaluated_ids(self):
        self.assertEqual(unseen_index(100, set()), 33)
        self.assertEqual(unseen_index(100, {33,34}), 35)
        with self.assertRaises(ValueError):
            unseen_index(3, {1})

    def test_empty_class_is_unknown_not_zero(self):
        self.assertIsNone(terrain_summary((0,0,0))["correct_percent"])
        self.assertIsNone(terrain_summary((0,0,0))["called_ground_percent"])
        with self.assertRaises(ValueError):
            terrain_summary((5,6,0))

    def test_track_weighting_preserves_scene_identity(self):
        rows = [dict(scene="a", instance_token="same", lidar_points="1", radar_points="0") for _ in range(9)]
        rows.append(dict(scene="b", instance_token="same", lidar_points="0", radar_points="1"))
        result = equal_track_support(rows)
        self.assertEqual(result["equal_track_lidar_percent"], 50)
        self.assertEqual(result["equal_track_radar_percent"], 50)
        self.assertIsNone(equal_track_support([])["equal_track_lidar_percent"])

    def test_range_boundaries_and_empty_bands(self):
        rows = [dict(scene="a", instance_token="id", category="car", range_m="25", lidar_points="1", radar_points="0")]
        result = class_range_rows(rows, "test")
        self.assertEqual(result[0]["observations"], 0)
        self.assertEqual(result[1]["observations"], 1)
        self.assertIsNone(result[0]["radar_percent"])

    def test_changed_cached_zip_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            info = zipfile.ZipInfo("test.bin")
            info.file_size, info.CRC = 4, 0
            (directory / "test.bin").write_bytes(b"bad")
            with self.assertRaisesRegex(ValueError, "Existing input changed"):
                member({}, info, directory)

    def test_zip_path_cannot_escape_raw_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "Unsafe ZIP path"):
                member({}, zipfile.ZipInfo("../escape.bin"), Path(temporary))


if __name__ == "__main__":
    unittest.main()
