# Acceptance check — TruckScenes range-band workflow

**Owner:** Fatima Sher · **Story:** FA-S3-1 · **Reviewer:** Kelsey Chen

FA-S3-1 is done when *another member can rerun the saved sample list and
obtain the same summary*. This page is how that is checked. It also supplies
evidence toward project criterion **P-5** (someone outside the pair can clone
the repository and reproduce a documented result) and **DS-5** (every result
validates against the shared schema).

No new validator was written for this. The checks are unittest cases that the
existing suite and the existing CI workflow already run.

## What a teammate runs

```bash
# 1. Nothing but the repository — no dataset needed.
python -m unittest discover -s tests
python scripts/validate_result.py
python scripts/validate_experiment_logs.py

# 2. With the dataset on disk, rebuild everything from scratch.
export TRUCKSCENES_ROOT=/path/to/man-truckscenes
python scripts/truckscenes_sample_manifest.py
python scripts/truckscenes_range_bands.py
python scripts/plot_truckscenes_range_bands.py
git status --short
```

Step 1 passes or fails on its own. In step 2, an empty `git status` for
`sample-manifest.csv`, `sample-manifest.json` and `range-bands.csv` is the
result that matters: the rebuilt files are identical to the committed ones,
so the subset and the summary are the same ones this analysis reports.

## The criteria

| # | Test | How it is checked | Automated in CI |
|---|---|---|---|
| **A-1** | *Given* the repository, *when* a teammate looks for the analysed subset, *then* every artefact it depends on is present and non-empty | `CommittedArtefactTests` | Yes |
| **A-2** | *Given* the manifest, *when* compared with the range-band CSV, *then* both describe exactly the same sample tokens, channels and coordinate frame | `ManifestMatchesAnalysisTests` | Yes |
| **A-3** | *Given* a sample missing a channel, *when* the summary is aggregated, *then* the aggregate sample count shrinks rather than hiding the gap | `test_aggregate_sample_count_matches_the_samples_with_that_channel` | Yes |
| **A-4** | *Given* the summary, *when* its arithmetic is checked, *then* band counts sum to the stated denominator, per-sample counts sum to the aggregate, and every share matches its own count and denominator | `SummaryArithmeticTests` | Yes |
| **A-5** | *Given* the committed figures, *when* inspected, *then* they are valid PNGs carrying no date or build stamp | `FigureStampTests` | Yes |
| **A-6** | *Given* the dataset, *when* the manifest and summary are regenerated, *then* the files are byte-identical to the committed ones | `git status` after step 2 above | **No** — needs the dataset |
| **A-7** | *Given* the committed CSV, *when* the figures are regenerated twice on one machine, *then* both renders are byte-identical | `test_figures_are_byte_identical_across_runs` | Yes |

A-1 to A-5 and A-7 run on every pull request through the existing
`.github/workflows/checks.yml`. A-6 cannot: the dataset is 9.6 GB and is never
committed, so no CI runner can rebuild the manifest. It is a person-run check,
which is why the command and the expected result are written out above.

## What these checks are for

The rest of the test suite checks that each script behaves correctly on
made-up inputs. These check something different — that the files **actually
committed** still agree with each other.

That is the failure this workflow is most exposed to. If someone regenerates
the manifest but not the summary, every percentage in the analysis quietly
starts describing a different subset of samples, every script still runs, and
every other test still passes. A-2 and A-4 are what notice.

## Known limits

**A-6 does not extend to the figures.** PNG bytes are not reproducible across
operating systems, because text is rendered with the host's own fonts. The
same script on macOS and on Linux produces visually identical figures of
different byte length. Date and software stamps are stripped, so a figure is
reproducible against itself on one machine (A-7), but a cross-machine
comparison should be made on the CSVs, not the images.

**Reproducing the numbers is not the same as validating them.** These checks
establish that two people analysing this subset get the same summary. They say
nothing about whether the subset is large enough, whether the chosen channels
are representative, or what the numbers mean. Those limits are in
[`RANGE-BANDS.md`](RANGE-BANDS.md) and
[`RANGE-BANDS-OPEN-QUESTION.md`](RANGE-BANDS-OPEN-QUESTION.md).

**A-6 has not yet been performed by anyone outside this pair.** Until Kelsey
or another member runs step 2 on their own machine and reports the outcome,
P-5 remains partly met for this workflow, exactly as the revised acceptance
tests record it for the project as a whole.

The 21 September integration review passed the automated checks on Windows
and regenerated both plots from the committed CSV. This verifies the plotting
and committed-artefact checks; it does not close A-6. See the
[review evidence](../docs/sprint-3-review-2026-09-21.md).
