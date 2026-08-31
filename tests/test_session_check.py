"""Focused regression tests for the shared session guard."""

import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from session_check import is_dataset_file, owner_of  # noqa: E402


class SessionCheckTests(unittest.TestCase):
    def test_next_steps_is_frozen(self):
        self.assertEqual(
            owner_of("GOOSE - Ricky+Damien/NEXT-STEPS.md"),
            "FROZEN",
        )

    def test_stone_and_checkpoint_files_are_protected(self):
        for path in ("stone/drive.bag", "stone/labels.npz", "models/GOOSE.PTH"):
            with self.subTest(path=path):
                self.assertTrue(is_dataset_file(path))


if __name__ == "__main__":
    unittest.main()
