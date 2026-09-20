"""The submission path must allocate numbers itself and refuse invalid records."""

import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import new_result as nr


class ScriptedPrompter(nr.Prompter):
    """Drives the script from a list of answers instead of a terminal."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.output = []
        self.prompts = []
        super().__init__(reader=self._next, writer=self.output.append)

    def _next(self, prompt):
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError(f"ran out of answers at {prompt!r}")
        return self.answers.pop(0)

    @property
    def said(self):
        return "\n".join(self.output)


# A complete successful characterisation record. Characterisation is used because
# it skips the model question, keeping the script short enough to read.
SUCCESS_ANSWERS = [
    "goose-val-recount",                 # short name
    "Recount of the GOOSE validation split",
    "Damien Zhang",
    "2026-09-19",
    "1",                                 # status -> success
    "GOOSE 3D val (2024-07 archive)",
    "1x Velodyne Alpha Prime, 128-channel",
    "SemanticKITTI .label, 64 classes",
    "dataset-characterisation",          # typed rather than numbered
    "lidar",
    "val, all 961 frames",
    "",                                  # conditions skipped
    "macOS 26.3.1",                      # environment
    "Apple M-series",
    "3.11.15",
    "numpy", "2.4.6",                    # one package
    "",                                  # end packages
    "python scripts/goose_stats.py",     # commands
    "",
    "n",                                 # no metrics
    "y",                                 # one measurement
    "labelled_points", "174891807", "all 961 val frames", "",
    "n",                                 # no more measurements
    "3",                                 # hours
    "GOOSE - Ricky+Damien/dataset-statistics.md",
    "",                                  # end evidence
    "Counts labelled points, not detections.",
]


class NextSequenceNumberTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.folder.name)
        self.addCleanup(self.folder.cleanup)

    def touch(self, name):
        (self.root / name).write_text("{}", encoding="utf-8")

    def test_empty_directory_starts_at_one(self):
        self.assertEqual(nr.next_sequence_number(self.root), "0001")

    def test_missing_directory_starts_at_one(self):
        self.assertEqual(nr.next_sequence_number(self.root / "nope"), "0001")

    def test_one_past_the_highest(self):
        self.touch("0001-a.json")
        self.touch("0009-b.json")
        self.assertEqual(nr.next_sequence_number(self.root), "0010")

    def test_gaps_are_not_reused(self):
        # 0002 is missing because it was renumbered or withdrawn. Reusing it would
        # point an existing citation at different work.
        self.touch("0001-a.json")
        self.touch("0003-c.json")
        self.assertEqual(nr.next_sequence_number(self.root), "0004")

    def test_existing_duplicates_do_not_stall_allocation(self):
        # The exact state main was in twice: two records claiming one number.
        self.touch("0008-one.json")
        self.touch("0008-two.json")
        self.assertEqual(nr.next_sequence_number(self.root), "0009")

    def test_template_and_unnumbered_files_are_ignored(self):
        self.touch("TEMPLATE.json")
        self.touch("notes.json")
        self.assertEqual(nr.next_sequence_number(self.root), "0001")


class BuildRecordTests(unittest.TestCase):
    def test_successful_record_has_every_required_field(self):
        prompter = ScriptedPrompter(SUCCESS_ANSWERS)
        name, record = nr.build_record(prompter, number="0012")
        self.assertEqual(name, "goose-val-recount")
        self.assertEqual(record["id"], "0012-goose-val-recount")
        import validate_result as vr
        for field in vr.REQUIRED:
            self.assertIn(field, record, f"{field} missing")
            self.assertFalse(vr.blank(record[field]), f"{field} blank")

    def test_characterisation_is_not_asked_for_a_model(self):
        prompter = ScriptedPrompter(SUCCESS_ANSWERS)
        _, record = nr.build_record(prompter, number="0012")
        self.assertNotIn("model", record)
        self.assertFalse(any("Model" in p for p in prompter.prompts))

    def test_blank_and_placeholder_answers_are_refused(self):
        # "TBD" is blank as far as the validator is concerned, so the script has to
        # reject it at the prompt rather than let it through to a failed write.
        answers = ["", "TBD", "N/A", "-"] + SUCCESS_ANSWERS
        prompter = ScriptedPrompter(answers)
        name, _ = nr.build_record(prompter, number="0012")
        self.assertEqual(name, "goose-val-recount")
        self.assertIn("Required", prompter.said)

    def test_bad_short_name_is_refused(self):
        answers = ["Not KebabCase", "has spaces", "trailing-"] + SUCCESS_ANSWERS
        prompter = ScriptedPrompter(answers)
        name, _ = nr.build_record(prompter, number="0012")
        self.assertEqual(name, "goose-val-recount")

    def test_status_can_be_chosen_by_number_or_by_name(self):
        by_name = list(SUCCESS_ANSWERS)
        by_name[4] = "success"
        _, record = nr.build_record(ScriptedPrompter(by_name), number="0012")
        self.assertEqual(record["status"], "success")

    def test_failure_record_collects_the_four_mandatory_fields(self):
        answers = list(SUCCESS_ANSWERS)
        answers[4] = "3"  # failure
        answers += [
            "RuntimeError: CUDA out of memory",
            "Reduced batch size to 1 — same error",
            "",
            "6 GB of VRAM is not enough for this configuration",
            "Retry on a larger GPU, or stop",
        ]
        _, record = nr.build_record(ScriptedPrompter(answers), number="0012")
        self.assertEqual(record["status"], "failure")
        import validate_result as vr
        for field in vr.FAILURE_REQUIRED:
            self.assertIn(field, record)
            self.assertFalse(vr.blank(record[field]))

    def test_measurement_keeps_its_scope(self):
        _, record = nr.build_record(ScriptedPrompter(SUCCESS_ANSWERS), number="0012")
        self.assertEqual(record["measurements"][0]["scope"], "all 961 val frames")
        self.assertEqual(record["measurements"][0]["value"], 174891807)


class WriteAndValidateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.folder.name)
        self.addCleanup(self.folder.cleanup)

    def test_valid_record_is_written_and_passes_the_validator(self):
        _, record = nr.build_record(ScriptedPrompter(SUCCESS_ANSWERS), number="0012")
        path = self.root / "0012-goose-val-recount.json"
        ok, errors, _ = nr.write_and_validate(record, path)
        self.assertTrue(ok, errors)
        self.assertTrue(path.exists())
        written = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(written["id"], "0012-goose-val-recount")

    def test_invalid_record_leaves_no_file_behind(self):
        # A half-written record on disk is worse than no record: the next run
        # allocates around it and the validator fails for everyone.
        ok, errors, _ = nr.write_and_validate(
            {"schema_version": 1, "id": "0012-broken"}, self.root / "0012-broken.json")
        self.assertFalse(ok)
        self.assertTrue(errors)
        self.assertFalse((self.root / "0012-broken.json").exists())

    def test_written_file_ends_with_a_newline(self):
        _, record = nr.build_record(ScriptedPrompter(SUCCESS_ANSWERS), number="0012")
        path = self.root / "0012-goose-val-recount.json"
        nr.write_and_validate(record, path)
        self.assertTrue(path.read_text(encoding="utf-8").endswith("}\n"))

    def test_duplicate_sequence_preserves_existing_record(self):
        _, record = nr.build_record(ScriptedPrompter(SUCCESS_ANSWERS), number="0012")
        first = self.root / "0012-goose-val-recount.json"
        self.assertTrue(nr.write_and_validate(record, first)[0])
        original = first.read_bytes()
        record["id"] = "0012-other"
        second = self.root / "0012-other.json"
        self.assertFalse(nr.write_and_validate(record, second)[0])
        self.assertFalse(second.exists())
        self.assertEqual(first.read_bytes(), original)
        self.assertFalse((self.root / ".0012.lock").exists())

    def test_reserved_sequence_is_not_written_or_unlocked(self):
        lock = self.root / ".0012.lock"
        lock.touch()
        _, record = nr.build_record(ScriptedPrompter(SUCCESS_ANSWERS), number="0012")
        path = self.root / "0012-goose-val-recount.json"
        self.assertFalse(nr.write_and_validate(record, path)[0])
        self.assertFalse(path.exists())
        self.assertTrue(lock.exists())

    def test_existing_file_is_never_overwritten(self):
        path = self.root / "0012-goose-val-recount.json"
        path.write_text("original", encoding="utf-8")
        self.assertFalse(nr.write_and_validate({}, path)[0])
        self.assertEqual(path.read_text(encoding="utf-8"), "original")

    def test_main_reallocates_after_prompting(self):
        original_build = nr.build_record
        def build_with_other_writer(prompter, *, number):
            self.assertEqual(number, "0001")
            (self.root / "0001-concurrent.json").write_text("{}", encoding="utf-8")
            return original_build(ScriptedPrompter(SUCCESS_ANSWERS), number=number)
        with patch.object(nr, "build_record", side_effect=build_with_other_writer), \
                patch.object(nr, "Prompter", return_value=ScriptedPrompter([])):
            self.assertEqual(nr.main(["--records-dir", str(self.root)]), 0)
        result = json.loads((self.root / "0002-goose-val-recount.json").read_text())
        self.assertEqual(result["id"], "0002-goose-val-recount")


if __name__ == "__main__":
    unittest.main()
