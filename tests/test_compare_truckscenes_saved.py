"""Reject comparisons that would hide incompatible inputs or missing coverage."""
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_truckscenes_saved import SOURCES, compare_cameras, summarize_coverage


class CameraComparisonTests(unittest.TestCase):
    def setUp(self):
        self.inputs = [json.loads((ROOT / SOURCES[key]).read_text()) for key in
                       ("one_predictions", "four_predictions", "one_metrics", "four_metrics")]

    def test_saved_submission_retains_all_original_boxes(self):
        result, samples, _ = compare_cameras(*self.inputs)
        self.assertEqual((result["sample_count"], result["exactly_retained_boxes"],
                          result["added_boxes"], result["removed_boxes"]), (80, 959, 4288, 0))
        self.assertEqual(sum(x["four_camera_boxes"] for x in samples), 5247)

    def test_rejects_different_sample_set(self):
        self.inputs[1]["results"].pop(next(iter(self.inputs[1]["results"])))
        with self.assertRaisesRegex(ValueError, "sample sets"):
            compare_cameras(*self.inputs)

    def test_rejects_different_evaluator(self):
        self.inputs[3]["all"]["cfg"]["dist_th_tp"] = 4
        with self.assertRaisesRegex(ValueError, "configurations"):
            compare_cameras(*self.inputs)

    def test_rejects_undeclared_or_different_modality(self):
        for value in (True, None):
            with self.subTest(value=value):
                self.inputs[1]["meta"]["use_radar"] = value
                with self.assertRaisesRegex(ValueError, "Input flags"):
                    compare_cameras(*self.inputs)

    def test_rejects_wrong_box_token(self):
        box = next(b for v in self.inputs[1]["results"].values() for b in v)
        box["sample_token"] = "different"
        with self.assertRaisesRegex(ValueError, "Box token"):
            compare_cameras(*self.inputs)

    def test_rejects_inconsistent_saved_metric(self):
        self.inputs[3]["all"]["mean_ap"] = 0.5
        with self.assertRaisesRegex(ValueError, "mAP disagrees"):
            compare_cameras(*self.inputs)

    def test_retention_counts_duplicates_instead_of_collapsing_them(self):
        token = next(k for k, v in self.inputs[0]["results"].items() if v)
        self.inputs[0]["results"][token].append(deepcopy(self.inputs[0]["results"][token][0]))
        result, _, _ = compare_cameras(*self.inputs)
        self.assertEqual(result["removed_boxes"], 1)
        self.assertEqual(result["exactly_retained_boxes"], 959)


class CoverageComparisonTests(unittest.TestCase):
    def setUp(self):
        with (ROOT / SOURCES["coverage"]).open(newline="") as stream:
            self.rows = list(csv.DictReader(stream))

    def test_observed_zero_differs_from_undefined_share(self):
        rows = [r for r in self.rows if r["scope"] == "per_sample"][:5]
        for row in rows:
            row["point_count"] = row["denominator_points"] = "0"
        summary, samples = summarize_coverage(rows)
        self.assertEqual(samples[0]["returns_ge150m"], 0)
        self.assertIsNone(samples[0]["share_ge150m"])
        self.assertIsNone(summary["radar"]["pooled_share_ge150m"])

    def test_missing_modality_sample_is_not_filled_as_zero(self):
        token = next(r["sample_token"] for r in self.rows if r["scope"] == "per_sample")
        rows = [r for r in self.rows if not (r["sample_token"] == token and r["modality"] == "lidar")]
        summary, _ = summarize_coverage(rows)
        self.assertEqual(summary["radar"]["sample_count"], 10)
        self.assertEqual(summary["lidar"]["sample_count"], 9)

    def test_rejects_missing_band_and_wrong_total(self):
        rows = [r for r in self.rows if r["scope"] == "per_sample"]
        with self.assertRaisesRegex(ValueError, "five-band"):
            summarize_coverage(rows[1:])
        rows[0]["point_count"] = "10000"
        with self.assertRaisesRegex(ValueError, "denominator"):
            summarize_coverage(rows)

    def test_pooled_share_is_weighted_by_returns_not_frames(self):
        summary, _ = summarize_coverage(self.rows)
        radar = summary["radar"]
        self.assertEqual(radar["samples_with_returns_ge150m"], 9)
        self.assertAlmostEqual(radar["pooled_share_ge150m"], 305 / 4571)
        self.assertNotAlmostEqual(radar["pooled_share_ge150m"], radar["median_sample_share_ge150m"])


if __name__ == "__main__":
    unittest.main()
