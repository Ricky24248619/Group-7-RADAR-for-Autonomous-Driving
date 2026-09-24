"""Acceptance checks for the committed TruckScenes Sprint 3 artefacts.

FA-S3-1 is done when "another member can rerun the saved sample list and
obtain the same summary". The other tests in this repository check that each
script behaves correctly on made-up inputs. These check something different:
that the files actually committed to the repository still agree with each
other.

That is the part a teammate depends on. If the manifest and the range-band
CSV ever drift apart -- one regenerated and the other not, say -- every
percentage in the analysis silently starts describing a different subset, and
nothing else in the suite would notice.

These run in CI with no dataset present, because they only read committed
files. The one step that does need the dataset is regenerating the manifest
and CSV themselves, which a person runs and checks with `git status`. See
"TruckScenes - Fatima/ACCEPTANCE-CHECK.md".
"""

import csv
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
FATIMA_DIR = REPO_ROOT / "TruckScenes - Fatima"
MANIFEST_CSV = FATIMA_DIR / "sample-manifest.csv"
MANIFEST_JSON = FATIMA_DIR / "sample-manifest.json"
RANGE_BANDS_CSV = FATIMA_DIR / "range-bands.csv"
FIGURES = [
    REPO_ROOT / "docs" / "evidence" / "truckscenes" / "range_bands_share.png",
    REPO_ROOT / "docs" / "evidence" / "truckscenes" / "range_bands_counts.png",
]

NO_DATA = "no data"
MODALITIES = ("radar", "lidar")


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class CommittedArtefactTests(unittest.TestCase):
    """Step 1: the files a teammate would start from are actually present."""

    def test_every_expected_artefact_is_committed(self):
        for path in [MANIFEST_CSV, MANIFEST_JSON, RANGE_BANDS_CSV, *FIGURES]:
            with self.subTest(path=path.name):
                self.assertTrue(path.exists(), f"{path.name} is missing")
                self.assertGreater(path.stat().st_size, 0, f"{path.name} is empty")

    def test_manifest_csv_and_json_describe_the_same_samples(self):
        csv_tokens = [row["sample_token"] for row in read_csv(MANIFEST_CSV)]
        document = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        json_tokens = [row["sample_token"] for row in document["samples"]]

        self.assertEqual(csv_tokens, json_tokens)
        self.assertEqual(document["sample_count"], len(csv_tokens))


class ManifestMatchesAnalysisTests(unittest.TestCase):
    """Step 2: the analysis was run on the subset the manifest declares."""

    def setUp(self):
        self.manifest = read_csv(MANIFEST_CSV)
        self.bands = read_csv(RANGE_BANDS_CSV)
        self.per_sample = [row for row in self.bands if row["scope"] == "per_sample"]
        self.aggregate = [row for row in self.bands if row["scope"] == "aggregate"]

    def test_analysis_covers_exactly_the_manifest_samples(self):
        manifest_tokens = {row["sample_token"] for row in self.manifest}
        analysed_tokens = {row["sample_token"] for row in self.per_sample}

        self.assertEqual(analysed_tokens, manifest_tokens)

    def test_analysis_uses_the_channels_the_manifest_declares(self):
        for modality, field in (("radar", "radar_channel"), ("lidar", "lidar_channel")):
            with self.subTest(modality=modality):
                declared = {row[field] for row in self.manifest}
                used = {row["channel"] for row in self.bands if row["modality"] == modality}
                self.assertEqual(used, declared)

    def test_analysis_uses_the_coordinate_frame_the_manifest_declares(self):
        declared = {row["coordinate_frame"] for row in self.manifest}
        used = {row["coordinate_frame"] for row in self.bands}

        self.assertEqual(used, declared)

    def test_aggregate_sample_count_matches_the_samples_with_that_channel(self):
        """A missing channel must shrink the aggregate count, not be hidden."""
        for modality, status_field in (("radar", "radar_sample_data_token"),
                                       ("lidar", "lidar_sample_data_token")):
            with self.subTest(modality=modality):
                available = sum(1 for row in self.manifest if row[status_field])
                counts = {
                    int(row["sample_count"])
                    for row in self.aggregate
                    if row["modality"] == modality
                }
                self.assertEqual(counts, {available})


class SummaryArithmeticTests(unittest.TestCase):
    """Step 3: the summary adds up, so no return was dropped or double-counted."""

    def setUp(self):
        self.bands = read_csv(RANGE_BANDS_CSV)

    def rows(self, scope, modality):
        return [
            row
            for row in self.bands
            if row["scope"] == scope and row["modality"] == modality
        ]

    def test_band_counts_sum_to_the_stated_denominator(self):
        for modality in MODALITIES:
            with self.subTest(modality=modality):
                rows = self.rows("aggregate", modality)
                if any(row["point_count"] == NO_DATA for row in rows):
                    self.skipTest(f"{modality} has no measured data in the committed CSV")
                total = sum(int(row["point_count"]) for row in rows)
                denominators = {int(row["denominator_points"]) for row in rows}

                self.assertEqual(len(denominators), 1)
                self.assertEqual(total, denominators.pop())

    def test_per_sample_counts_add_up_to_the_aggregate_for_every_band(self):
        for modality in MODALITIES:
            per_sample = self.rows("per_sample", modality)
            for aggregate_row in self.rows("aggregate", modality):
                band = aggregate_row["band_label"]
                with self.subTest(modality=modality, band=band):
                    if aggregate_row["point_count"] == NO_DATA:
                        continue
                    summed = sum(
                        int(row["point_count"])
                        for row in per_sample
                        if row["band_label"] == band and row["point_count"] != NO_DATA
                    )
                    self.assertEqual(summed, int(aggregate_row["point_count"]))

    def test_shares_are_consistent_with_counts_and_denominators(self):
        for row in self.bands:
            if NO_DATA in (row["point_count"], row["denominator_points"]):
                continue
            denominator = int(row["denominator_points"])
            if denominator == 0:
                continue
            with self.subTest(scope=row["scope"], modality=row["modality"],
                              band=row["band_label"]):
                expected = int(row["point_count"]) / denominator
                self.assertAlmostEqual(
                    float(row["proportion_of_denominator"]), expected, places=5
                )

    def test_every_modality_uses_the_same_bands_in_the_same_order(self):
        orders = {
            modality: [row["band_label"] for row in self.rows("aggregate", modality)]
            for modality in MODALITIES
        }

        self.assertEqual(orders["radar"], orders["lidar"])
        self.assertEqual(len(set(orders["radar"])), len(orders["radar"]))


class FigureStampTests(unittest.TestCase):
    """Step 4: the committed figures carry no build stamp.

    PNG bytes are not identical across operating systems -- font rendering
    differs -- so this does not compare the committed files against a fresh
    render. What it does check is that no date or software stamp was written
    into them, which is the part that would make a figure differ from itself
    on the same machine. Same-machine reproducibility is covered by
    tests/test_plot_truckscenes_range_bands.py.
    """

    def test_committed_figures_are_pngs(self):
        for path in FIGURES:
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_committed_figures_carry_no_date_or_software_stamp(self):
        for path in FIGURES:
            with self.subTest(path=path.name):
                head = path.read_bytes()[:4096]
                self.assertNotIn(b"Date", head)
                self.assertNotIn(b"matplotlib", head.lower())


if __name__ == "__main__":
    unittest.main()
