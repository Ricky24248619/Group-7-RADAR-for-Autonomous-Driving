"""Prevent the log collisions and nested paths seen during branch integration."""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from validate_experiment_logs import check


class ExperimentLogTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.folder.name)
        self.addCleanup(self.folder.cleanup)

    def write(self, name, title):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(title + "\n", encoding="utf-8")

    def test_unique_flat_entries_and_readme_pass(self):
        self.write("README.md", "# Experiment log")
        self.write("0001-first.md", "# EXP-0001 — Setup")
        self.write("0002-second.md", "## EXP-0002 — Evaluation")
        self.assertEqual(check(self.root), [])

    def test_duplicate_numbers_are_rejected_even_in_nested_folder(self):
        self.write("0006-camera.md", "# EXP-0006 — Camera")
        self.write("experiment-log/0006-reproduction.md", "# EXP-0006 — Reproduction")
        errors = check(self.root)
        self.assertTrue(any("Duplicate EXP-0006" in error for error in errors))
        self.assertTrue(any("directly in experiment-log/" in error for error in errors))

    def test_renamed_file_requires_matching_title(self):
        self.write("0007-setup.md", "# EXP-0004 — Setup")
        self.assertTrue(any("heading must contain EXP-0007" in error for error in check(self.root)))

    def test_escaped_heading_and_placeholder_filename_are_rejected(self):
        self.write("0009-reproduction.md", r"\# EXP-0009 — Reproduction")
        self.write("NNNN-template.md", "# EXP-NNNN — Template")
        errors = check(self.root)
        self.assertTrue(any("heading must contain EXP-0009" in error for error in errors))
        self.assertTrue(any("expected NNNN-short-name.md" in error for error in errors))

    def test_missing_directory_fails(self):
        self.assertTrue(check(self.root / "missing"))


if __name__ == "__main__":
    unittest.main()
