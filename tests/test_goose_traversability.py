"""Focused regression tests for the traversability comparison helpers."""

import pathlib
import sys
import unittest

import numpy as np

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from goose_traversability import apply_overrides, comparison_summary  # noqa: E402


class ApplyOverridesTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {17: 3, 23: 1}
        self.names = {17: "bush", 23: "asphalt"}
        self.valid_groups = {0, 1, 2, 3}

    def test_applies_named_override_without_mutating_baseline(self):
        updated, changed = apply_overrides(
            self.mapping, self.names, ["bush=2"], self.valid_groups
        )

        self.assertEqual(updated[17], 2)
        self.assertEqual(self.mapping[17], 3)
        self.assertEqual(changed, ["bush: 3 -> 2"])

    def test_rejects_missing_id(self):
        with self.assertRaisesRegex(SystemExit, "must be CLASS=ID"):
            apply_overrides(self.mapping, self.names, ["bush"], self.valid_groups)

    def test_rejects_non_integer_id(self):
        with self.assertRaisesRegex(SystemExit, "must be an integer"):
            apply_overrides(self.mapping, self.names, ["bush=blocked"],
                            self.valid_groups)

    def test_rejects_id_outside_loaded_taxonomy(self):
        with self.assertRaisesRegex(SystemExit, "must be one of 0, 1, 2, 3"):
            apply_overrides(self.mapping, self.names, ["bush=9"], self.valid_groups)


class ComparisonSummaryTests(unittest.TestCase):
    def test_describes_bush_style_amber_red_change(self):
        baseline = np.array([1, 2, 3, 3])
        variant = np.array([1, 2, 2, 2])

        summary = comparison_summary(baseline, variant)

        self.assertIn("Traversable region is identical", summary)
        self.assertIn("amber", summary)
        self.assertIn("red", summary)

    def test_reports_when_traversable_region_changes(self):
        baseline = np.array([1, 2, 3, 3])
        variant = np.array([3, 2, 3, 1])

        summary = comparison_summary(baseline, variant)

        self.assertIn("Traversable region changes", summary)
        self.assertIn("2 points", summary)

    def test_uses_singular_point_wording(self):
        baseline = np.array([1, 2])
        variant = np.array([3, 2])

        self.assertIn("1 point switch", comparison_summary(baseline, variant))

    def test_reports_no_effect_when_overridden_class_is_absent(self):
        groups = np.array([0, 1, 2, 3])

        self.assertEqual(
            comparison_summary(groups, groups.copy()),
            "No rendered points change under this override.",
        )


if __name__ == "__main__":
    unittest.main()
