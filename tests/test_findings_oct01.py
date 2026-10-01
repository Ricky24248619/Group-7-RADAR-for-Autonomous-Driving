"""Regression checks for denominators, paired identities and split interpretation."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

analysis = module("analyse_findings_oct01")
additional = module("analyse_additional_datasets")

class FindingEvidenceTests(unittest.TestCase):
    def row(self, scene, annotation, track="track", lidar=0, radar=0):
        return dict(scene=scene, annotation_token=annotation, instance_token=track,
                    margin_m="0", category="Vehicle", lidar_points=str(lidar), radar_points=str(radar))

    def test_empty_population_is_not_zero_accuracy(self):
        result = analysis.support([])
        self.assertIsNone(result["lidar_percent"])
        self.assertIsNone(result["radar_percent"])
        self.assertIsNone(result["equal_scene_difference_pp"])

    def test_negative_counts_and_nonpositive_threshold_rejected(self):
        with self.assertRaises(ValueError):
            analysis.support([self.row("a", "1", lidar=-1)])
        with self.assertRaises(ValueError):
            analysis.support([], 0)

    def test_union_and_scene_qualified_tracks(self):
        rows = [self.row("a", "1", lidar=1), self.row("b", "1", radar=1), self.row("b", "2")]
        result = analysis.support(rows)
        self.assertEqual(result["tracks"], 2)
        self.assertEqual(result["lidar_only"], 1)
        self.assertEqual(result["radar_only"], 1)
        self.assertEqual(result["neither"], 1)
        self.assertAlmostEqual(result["union_percent"], 200/3)

    def test_scene_macro_does_not_equal_observation_weighting(self):
        rows = [self.row("a", str(i), lidar=1) for i in range(10)] + [self.row("b", "1", radar=1)]
        result = analysis.support(rows)
        self.assertEqual(result["equal_scene_difference_pp"], 0)
        self.assertGreater(result["lidar_percent"], result["radar_percent"])

    def test_timing_comparison_matches_observations_and_scene(self):
        a = [self.row("a", "1"), self.row("b", "1"), self.row("a", "2")]
        b = [self.row("b", "1")]
        first, second = analysis.match_rows(a, b)
        self.assertEqual([row["scene"] for row in first], ["b"])
        self.assertEqual(len(second), 1)

    def test_duplicate_observation_rejected(self):
        row = self.row("a", "1")
        with self.assertRaises(ValueError):
            analysis.match_rows([row, row], [row])

    def test_split_overlap_uses_frame_ids_not_recording_groups(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for dimension in ("opt2d", "opt3d"):
                for split in ("train", "val", "test"):
                    path = directory / "data/splits" / dimension / (split + ".csv")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("w", newline="") as stream:
                        writer = csv.DictWriter(stream, fieldnames=["id", "label_path"])
                        writer.writeheader()
                        writer.writerow({"id": split, "label_path": "WildScenes3d/K-01/Labels/" + split})
            result = additional.audit_splits(directory)
            self.assertEqual(result["within_dimension_id_overlap"]["opt3d"]["train/test"], 0)
            self.assertEqual(result["cross_dimension_id_overlap"]["test/test"], 1)

    def test_checked_register_retains_32_distinct_evidenced_findings(self):
        catalog = json.loads((ROOT / "results/evidence/findings-oct01/findings.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["findings"]), 32)
        self.assertEqual(len({row["id"] for row in catalog["findings"]}), 32)
        for row in catalog["findings"]:
            self.assertTrue(row["limits"])
            for source in row["sources"]:
                self.assertTrue((ROOT / source).is_file(), source)

if __name__ == "__main__":
    unittest.main()
