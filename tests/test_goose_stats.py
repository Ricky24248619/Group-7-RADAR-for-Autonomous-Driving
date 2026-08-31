"""Regression tests for deterministic GOOSE statistics report metadata."""

from datetime import date
import pathlib
import sys
import tempfile
import unittest

import numpy as np

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from goose_stats import write_report  # noqa: E402


class WriteReportTests(unittest.TestCase):
    def test_uses_supplied_generation_date_instead_of_stale_literal(self):
        result = {
            "classes": {0: "undefined"},
            "frames": [object()],
            "class_counts": np.array([10], dtype=np.int64),
            "range_counts": np.array([10, 0, 0, 0, 0], dtype=np.int64),
            "scenario_counts": {
                "example_scenario": np.array([10], dtype=np.int64)
            },
            "scenario_points": {"example_scenario": [10]},
            "points_per_frame": np.array([10], dtype=np.int64),
        }

        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "report.md"
            write_report(result, output, generated_on=date(2026, 8, 31))
            report = output.read_text(encoding="utf-8")

        self.assertIn("on 31 August 2026", report)
        self.assertNotIn("on 27 August 2026", report)


if __name__ == "__main__":
    unittest.main()
