"""Regression tests for the MAN TruckScenes matched sample manifest."""

import json
import pathlib
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from truckscenes_sample_manifest import (  # noqa: E402
    MANIFEST_FIELDS,
    ManifestError,
    assert_unique_sample_tokens,
    build_manifest_rows,
    manifest_document,
    write_csv,
    write_json,
)


def fake_dataset(samples):
    """Build a stand-in for the devkit's scene table and get() lookup.

    ``samples`` is a list of (scene_name, sample_dict). This keeps the tests
    runnable on CI, which deliberately does not install truckscenes-devkit.
    """
    scenes = []
    by_token = {}
    for index, (scene_name, sample) in enumerate(samples, start=1):
        scenes.append(
            {
                "name": scene_name,
                "token": f"scene-token-{index}",
                "first_sample_token": sample["token"],
            }
        )
        by_token[sample["token"]] = sample

    def get(table, token):
        assert table == "sample"
        return by_token[token]

    return scenes, get


def sample(token, radar="radar-sd", lidar="lidar-sd", anns=3, timestamp=1000):
    data = {}
    if radar is not None:
        data["RADAR_LEFT_FRONT"] = radar
    if lidar is not None:
        data["LIDAR_TOP_FRONT"] = lidar
    return {
        "token": token,
        "timestamp": timestamp,
        "anns": [f"ann-{i}" for i in range(anns)],
        "data": data,
    }


class ManifestFieldTests(unittest.TestCase):
    def test_every_row_has_exactly_the_documented_fields(self):
        scenes, get = fake_dataset([("scene-a", sample("s1")), ("scene-b", sample("s2"))])
        rows = build_manifest_rows(scenes, get)

        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(sorted(row), sorted(MANIFEST_FIELDS))

    def test_records_tokens_channels_timestamp_and_annotation_count(self):
        scenes, get = fake_dataset(
            [("scene-a", sample("s1", radar="r1", lidar="l1", anns=7, timestamp=1695000000))]
        )
        row = build_manifest_rows(scenes, get)[0]

        self.assertEqual(row["scene_name"], "scene-a")
        self.assertEqual(row["sample_token"], "s1")
        self.assertEqual(row["sample_timestamp"], 1695000000)
        self.assertEqual(row["radar_channel"], "RADAR_LEFT_FRONT")
        self.assertEqual(row["radar_sample_data_token"], "r1")
        self.assertEqual(row["lidar_channel"], "LIDAR_TOP_FRONT")
        self.assertEqual(row["lidar_sample_data_token"], "l1")
        self.assertEqual(row["annotation_count"], 7)
        self.assertEqual(row["record_status"], "complete")


class DuplicateTokenTests(unittest.TestCase):
    def test_duplicate_sample_tokens_are_rejected(self):
        scenes, get = fake_dataset([("scene-a", sample("same")), ("scene-b", sample("same"))])
        rows = build_manifest_rows(scenes, get)

        with self.assertRaises(ManifestError) as raised:
            assert_unique_sample_tokens(rows)
        self.assertIn("same", str(raised.exception))

    def test_distinct_sample_tokens_pass(self):
        scenes, get = fake_dataset([("scene-a", sample("s1")), ("scene-b", sample("s2"))])
        assert_unique_sample_tokens(build_manifest_rows(scenes, get))


class MissingChannelTests(unittest.TestCase):
    def test_missing_radar_is_named_not_dropped(self):
        scenes, get = fake_dataset([("scene-a", sample("s1", radar=None))])
        rows = build_manifest_rows(scenes, get)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["radar_sample_data_token"], "")
        self.assertEqual(rows[0]["record_status"], "missing_radar")

    def test_missing_lidar_is_named_not_dropped(self):
        scenes, get = fake_dataset([("scene-a", sample("s1", lidar=None))])
        rows = build_manifest_rows(scenes, get)

        self.assertEqual(rows[0]["lidar_sample_data_token"], "")
        self.assertEqual(rows[0]["record_status"], "missing_lidar")

    def test_missing_both_channels_is_named(self):
        scenes, get = fake_dataset([("scene-a", sample("s1", radar=None, lidar=None))])
        rows = build_manifest_rows(scenes, get)

        self.assertEqual(rows[0]["record_status"], "missing_radar_and_lidar")

    def test_complete_pair_count_excludes_incomplete_rows(self):
        scenes, get = fake_dataset(
            [("scene-a", sample("s1")), ("scene-b", sample("s2", radar=None))]
        )
        document = manifest_document(build_manifest_rows(scenes, get))

        self.assertEqual(document["sample_count"], 2)
        self.assertEqual(document["complete_pair_count"], 1)


class DeterminismTests(unittest.TestCase):
    def test_row_order_follows_scene_order(self):
        scenes, get = fake_dataset(
            [("scene-c", sample("s3")), ("scene-a", sample("s1")), ("scene-b", sample("s2"))]
        )
        rows = build_manifest_rows(scenes, get)

        self.assertEqual([row["scene_name"] for row in rows], ["scene-c", "scene-a", "scene-b"])
        self.assertEqual([row["index"] for row in rows], [1, 2, 3])

    def test_rebuilding_the_same_subset_gives_an_identical_manifest(self):
        scenes, get = fake_dataset([("scene-a", sample("s1")), ("scene-b", sample("s2"))])

        self.assertEqual(build_manifest_rows(scenes, get), build_manifest_rows(scenes, get))

    def test_written_files_are_byte_identical_across_runs(self):
        scenes, get = fake_dataset([("scene-a", sample("s1")), ("scene-b", sample("s2"))])

        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            outputs = []
            for run in ("first", "second"):
                csv_path = directory / f"{run}.csv"
                json_path = directory / f"{run}.json"
                rows = build_manifest_rows(scenes, get)
                write_csv(rows, csv_path)
                write_json(rows, json_path)
                outputs.append((csv_path.read_bytes(), json_path.read_bytes()))

            self.assertEqual(outputs[0], outputs[1])

    def test_written_files_use_unix_line_endings_on_every_platform(self):
        """CRLF would be normalised to LF by git and stop matching the file on disk."""
        scenes, get = fake_dataset([("scene-a", sample("s1")), ("scene-b", sample("s2"))])

        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            csv_path = directory / "manifest.csv"
            json_path = directory / "manifest.json"
            rows = build_manifest_rows(scenes, get)
            write_csv(rows, csv_path)
            write_json(rows, json_path)

            self.assertNotIn(b"\r\n", csv_path.read_bytes())
            self.assertNotIn(b"\r\n", json_path.read_bytes())

    def test_written_json_carries_the_declared_subset_context(self):
        scenes, get = fake_dataset([("scene-a", sample("s1"))])

        with tempfile.TemporaryDirectory() as tmp:
            json_path = pathlib.Path(tmp) / "manifest.json"
            write_json(build_manifest_rows(scenes, get), json_path)
            document = json.loads(json_path.read_text(encoding="utf-8"))

        self.assertEqual(document["radar_channel"], "RADAR_LEFT_FRONT")
        self.assertEqual(document["lidar_channel"], "LIDAR_TOP_FRONT")
        self.assertIn("sensor", document["coordinate_frame"])
        self.assertIn("first annotated sample", document["inclusion_rule"].lower())


if __name__ == "__main__":
    unittest.main()
