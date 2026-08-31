"""Focused regression test for client-figure survey options."""

import contextlib
import io
import pathlib
import sys
import unittest
from unittest import mock

import numpy as np

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import goose_client_figure as client_figure  # noqa: E402


class SurveyTests(unittest.TestCase):
    def test_cli_cell_size_reaches_ground_slice(self):
        points = np.array([[0.0, 0.0, 0.0, 1.0]])
        labels = np.array([1])
        argv = ["goose_client_figure.py", "--root", "unused", "--survey",
                "--cell", "1.25"]

        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(client_figure, "load_group_map",
                                  return_value=({1: 1}, {}, {})), \
                mock.patch.object(client_figure, "scenario_frames",
                                  return_value={"scene": ("scan", "label")}), \
                mock.patch.object(client_figure, "load_frame",
                                  return_value=(points, labels)), \
                mock.patch.object(client_figure, "ground_slice",
                                  return_value=np.array([0])) as ground_slice, \
                contextlib.redirect_stdout(io.StringIO()):
            client_figure.main()

        called_points, called_cell = ground_slice.call_args.args
        self.assertIs(called_points, points)
        self.assertEqual(called_cell, 1.25)


if __name__ == "__main__":
    unittest.main()
