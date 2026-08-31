"""Regression tests for the benchmark result validator."""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_result as validator  # noqa: E402


class ResultValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tempdir.name)
        self.evidence = self.root / "evidence.txt"
        self.evidence.write_text("proof\n", encoding="utf-8")
        self.record = {
            "schema_version": 1,
            "id": "0001-valid",
            "title": "Valid record",
            "owner": "Tester",
            "date": "2026-08-31",
            "status": "success",
            "dataset": "GOOSE validation 2026",
            "sensor_configuration": "LiDAR",
            "annotation_schema": "Eight-class challenge labels",
            "task_type": "semantic-segmentation-3d",
            "modality": "lidar",
            "split": "validation, one frame",
            "environment": {"os": "test"},
            "commands": ["python run.py"],
            "evidence": ["evidence.txt"],
            "metrics": [{"name": "mIoU", "value": 0.8, "scope": "8 classes"}],
        }
        self.metric_names = frozenset(
            {
                "precision",
                "recall",
                "map",
                "per-class iou",
                "2d per-class iou",
                "3d per-class iou",
                "4-class traversability iou",
                "miou",
                "overall accuracy",
                "processing time",
            }
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def write(self, record=None, name="0001-valid.json", raw=None):
        path = self.root / name
        if raw is None:
            raw = json.dumps(self.record if record is None else record)
        path.write_text(raw, encoding="utf-8")
        return path

    def check(self, record=None, name="0001-valid.json", raw=None):
        path = self.write(record, name=name, raw=raw)
        with mock.patch.object(validator, "REPO", self.root):
            return validator.check(path, self.metric_names)

    def assert_error_contains(self, errors, text):
        self.assertTrue(
            any(text in error for error in errors),
            f"expected error containing {text!r}; got {errors!r}",
        )

    def test_valid_record_passes(self):
        errors, warnings = self.check()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_exact_previously_false_accepted_record_is_rejected(self):
        record = {
            "schema_version": 1,
            "id": "0001-bad",
            "title": "bad record",
            "owner": "tester",
            "date": "2026-99-99",
            "status": "success",
            "dataset": "x",
            "sensor_configuration": "x",
            "annotation_schema": "x",
            "task_type": "semantic-segmentation-3d",
            "modality": "lidar",
            "split": "x",
            "environment": "not an object",
            "commands": "not a list",
            "evidence": ["missing/file.txt"],
            "metrics": [{"name": "a", "value": "not-a-number", "scope": "x"}],
        }
        errors, _ = self.check(record, name="0001-bad.json")
        for expected in (
            "not a valid calendar date",
            "'environment' must be a non-empty object",
            "'commands' must be a non-empty list",
            "evidence[0] does not exist",
            "metrics[0].value must be a finite JSON number",
            "metric 'a' is not exactly defined",
        ):
            self.assert_error_contains(errors, expected)

    def test_unhashable_task_type_reports_type_error_without_crashing(self):
        record = dict(self.record, task_type=["semantic-segmentation-3d"])
        errors, _ = self.check(record)
        self.assert_error_contains(errors, "'task_type' must be a non-empty string")

    def test_schema_version_requires_exact_integer(self):
        for value in (True, 1.0, 2, "1"):
            with self.subTest(value=value):
                errors, _ = self.check(dict(self.record, schema_version=value))
                self.assert_error_contains(errors, "schema_version must be exactly integer 1")

    def test_root_must_be_object(self):
        errors, _ = self.check(raw="[]")
        self.assertEqual(errors, ["top level must be a JSON object"])

    def test_invalid_json_and_duplicate_keys_are_graceful_errors(self):
        for raw, expected in (
            ("{", "not valid JSON"),
            ('{"schema_version": 1, "schema_version": 1}', "duplicate object key"),
            ('{"value": NaN}', "non-standard numeric constant"),
        ):
            with self.subTest(raw=raw):
                errors, _ = self.check(raw=raw)
                self.assert_error_contains(errors, expected)

    def test_excessively_nested_json_is_a_graceful_invalid_record(self):
        raw = "[" * 2000 + "0" + "]" * 2000
        errors, warnings = self.check(raw=raw)
        self.assertEqual(warnings, [])
        self.assert_error_contains(errors, "not valid JSON")

    @unittest.skipUnless(
        hasattr(sys, "set_int_max_str_digits"),
        "Python runtime has no integer string digit safety limit",
    )
    def test_oversized_integer_is_a_graceful_invalid_record(self):
        old_limit = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            raw = '{"value": ' + "9" * 5000 + "}"
            errors, warnings = self.check(raw=raw)
        finally:
            sys.set_int_max_str_digits(old_limit)
        self.assertEqual(warnings, [])
        self.assert_error_contains(errors, "not valid JSON")

    def test_required_strings_reject_non_strings(self):
        record = dict(self.record, owner=17, dataset=["GOOSE"])
        errors, _ = self.check(record)
        self.assert_error_contains(errors, "'owner' must be a non-empty string")
        self.assert_error_contains(errors, "'dataset' must be a non-empty string")

    def test_commands_and_evidence_require_nonempty_string_items(self):
        record = dict(self.record, commands=["", 7], evidence=[])
        errors, _ = self.check(record)
        self.assert_error_contains(errors, "'commands[0]' must be a non-empty string")
        self.assert_error_contains(errors, "'commands[1]' must be a non-empty string")
        self.assert_error_contains(errors, "'evidence' is blank")

    def test_evidence_must_be_existing_repo_relative_path(self):
        absolute = str(self.evidence.resolve())
        for evidence, expected in (
            ([absolute], "must be a repo-relative path"),
            (["../outside.txt"], "escapes the repository"),
            (["missing.txt"], "does not exist in the repository"),
        ):
            with self.subTest(evidence=evidence):
                errors, _ = self.check(dict(self.record, evidence=evidence))
                self.assert_error_contains(errors, expected)

    def test_metrics_and_measurements_require_object_shape_and_finite_number(self):
        record = dict(
            self.record,
            metrics=["bad", {"name": "mIoU", "value": True}],
            measurements=[{"name": "frames", "value": "infinite"}, {}],
        )
        errors, _ = self.check(record)
        for expected in (
            "metrics[0] must be an object",
            "metrics[1].value must be a finite JSON number",
            "measurements[0].value must be a finite JSON number",
            "measurements[1].name must be a non-empty string",
            "measurements[1] has no value",
        ):
            self.assert_error_contains(errors, expected)

    def test_overflowing_json_number_is_rejected_as_non_finite(self):
        raw = json.dumps(self.record).replace('"value": 0.8', '"value": 1e309')
        errors, _ = self.check(raw=raw)
        self.assert_error_contains(errors, "must be finite")

    def test_arbitrarily_large_json_integer_does_not_crash(self):
        record = dict(self.record)
        record["measurements"] = [
            {"name": "synthetic count", "value": 10**1000, "scope": "test"}
        ]
        errors, _ = self.check(record)
        self.assertEqual(errors, [])

    def test_metric_name_uses_exact_definition_not_substring(self):
        exact = dict(self.record)
        exact["metrics"] = [{"name": "mIoU", "value": 0.8, "scope": "eight classes"}]
        errors, _ = self.check(exact)
        self.assertEqual(errors, [])

        substring = dict(self.record)
        substring["metrics"] = [
            {"name": "IoU", "value": 0.7, "scope": "eight classes"}
        ]
        errors, _ = self.check(substring)
        self.assert_error_contains(errors, "metric 'IoU' is not exactly defined")

    def test_ratio_metrics_must_be_between_zero_and_one(self):
        names = (
            "Precision",
            "Recall",
            "mAP",
            "Per-class IoU",
            "2D per-class IoU",
            "3D per-class IoU",
            "4-class traversability IoU",
            "mIoU",
            "Overall accuracy",
        )
        for name in names:
            for value in (-0.001, 1.001):
                with self.subTest(name=name, value=value):
                    record = dict(self.record)
                    record["metrics"] = [
                        {"name": name.swapcase(), "value": value, "scope": "test"}
                    ]
                    errors, _ = self.check(record)
                    self.assert_error_contains(errors, "between 0 and 1 inclusive")

    def test_ratio_metric_boundary_values_are_valid(self):
        for value in (0, 1, 0.5):
            with self.subTest(value=value):
                record = dict(self.record)
                record["metrics"] = [
                    {"name": "  MIOU  ", "value": value, "scope": "test"}
                ]
                errors, _ = self.check(record)
                self.assertEqual(errors, [])

    def test_processing_time_must_be_nonnegative(self):
        record = dict(self.record)
        record["metrics"] = [
            {"name": "PROCESSING TIME", "value": -0.001, "scope": "per frame"}
        ]
        errors, _ = self.check(record)
        self.assert_error_contains(errors, "must be non-negative")

        record["metrics"][0]["value"] = 0
        errors, _ = self.check(record)
        self.assertEqual(errors, [])

    def test_metric_range_matching_does_not_use_substrings(self):
        record = dict(self.record)
        record["metrics"] = [
            {
                "name": "published baseline mIoU",
                "value": 80.96,
                "scope": "quoted result",
            }
        ]
        errors, _ = self.check(record)
        self.assert_error_contains(errors, "is not exactly defined")
        self.assertFalse(any("between 0 and 1" in error for error in errors))

    def test_parse_defined_metrics_extracts_declared_names_only(self):
        names = validator.parse_defined_metrics(
            """| Metric | Definition |
|---|---|
| mAP | defined |

The prose mentions FakeMetric but does not define it.
- **Overall accuracy:** defined
**mIoU** is defined
"""
        )
        self.assertEqual(names, {"map", "overall accuracy", "miou"})

    def test_check_accepts_raw_metrics_document_without_substring_matching(self):
        path = self.write()
        with mock.patch.object(validator, "REPO", self.root):
            errors, _ = validator.check(path, "**mIoU** is defined")
        self.assertEqual(errors, [])

    def test_invalid_id_and_filename_mismatch_are_errors(self):
        errors, _ = self.check(dict(self.record, id="BAD ID"))
        self.assert_error_contains(errors, "must be NNNN-kebab-case")
        self.assert_error_contains(errors, "does not match filename")

    def test_partial_record_requires_typed_failure_details(self):
        record = dict(
            self.record,
            status="partial",
            error=42,
            attempted_fixes="one command",
            blocker="",
            recommendation=[],
        )
        errors, _ = self.check(record)
        for expected in (
            "'error' must be a non-empty string",
            "'attempted_fixes' must be a non-empty list",
            "'blocker' must be a non-empty string",
            "'recommendation' must be a non-empty string",
        ):
            self.assert_error_contains(errors, expected)


if __name__ == "__main__":
    unittest.main()
