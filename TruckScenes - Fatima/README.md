# TruckScenes RADAR/LiDAR range analysis — Fatima

**Story:** FA-S3-1 · **Epic C** · **Reviewer:** Kelsey Chen

Start here. This page is the map of the folder and the three commands that
rebuild everything. The detail lives in the pages linked at the bottom, so
nothing is explained twice.

Environment setup is in [`../SETUP.md`](../SETUP.md) and is not repeated here.

## Purpose

Measure how far RADAR and LiDAR returns reach on MAN TruckScenes, on a fixed
and declared set of samples, so the two can be compared honestly and anyone
can rebuild the numbers.

This is **coverage analysis**. It counts sensor returns by distance. It is not
a detection benchmark, and no detection model has been run from this folder.

## The workflow

Three scripts, run in this order. Each reads what the one before it wrote.

```bash
# activate the project virtualenv first -- see ../SETUP.md
export TRUCKSCENES_ROOT=/path/to/man-truckscenes

python scripts/truckscenes_sample_manifest.py   # 1. which samples
python scripts/truckscenes_range_bands.py       # 2. the counts
python scripts/plot_truckscenes_range_bands.py  # 3. the charts
```

**1. The sample manifest** fixes which samples are analysed: the first
annotated sample of each of the 10 scenes in `v1.2-mini`, out of 400 annotated
samples. It stores each sample's tokens, channels, timestamp and annotation
count, so the subset can be cited and rebuilt rather than assumed.

**2. The range-band summary** counts returns per distance band, per sample and
in total. Every row states its sample count, modality, channel, band, count,
denominator and what that denominator covers.

**3. The charts** read the summary CSV only. They never open the dataset and
never recompute a count, so every value on a chart traces back to a committed
row.

## Sensors and coordinate frame

| | |
|---|---|
| RADAR | `RADAR_LEFT_FRONT` — one of six |
| LiDAR | `LIDAR_TOP_FRONT` — one of six |
| Frame | each sensor's own frame; range is `sqrt(x² + y²)` with no ego or global transform |

Because no transform is applied, RADAR and LiDAR distances are measured from
**two different physical positions on the truck**.

## Distance bands

Default `0–50 / 50–100 / 100–150 / 150–400 m`, plus an open band above the
highest edge so every return is counted somewhere. The edges are a
command-line option, not a constant, because the band decision is still open:

```bash
python scripts/truckscenes_range_bands.py --band-edges 0,25,50,80,100,150
```

A band that was measured and held nothing is `0`. A band that could not be
measured is `no data`, and its sample drops out of the aggregate sample count.

## Files this produces

| File | What it is |
|---|---|
| `sample-manifest.csv` / `.json` | the declared subset — same rows, two formats |
| `range-bands.csv` | counts and shares per sample, modality and band |
| `../docs/evidence/truckscenes/range_bands_share.png` | shares, on one shared 0–100% axis |
| `../docs/evidence/truckscenes/range_bands_counts.png` | counts, on a shared log axis |

## Tests

```bash
python -m unittest discover -s tests
python scripts/validate_result.py
python scripts/validate_experiment_logs.py
```

The same commands the rest of the repository uses — no separate runner. CI runs
all three on every pull request. Checks specific to this workflow live in
`tests/test_truckscenes_sample_manifest.py`,
`tests/test_truckscenes_range_bands.py`,
`tests/test_plot_truckscenes_range_bands.py` and
`tests/test_truckscenes_reproducibility.py`.

## What this analysis does not show

Four statements that must travel with every number and figure produced here.

**Point presence and point density are not detection performance.** A sensor
returning more points is not the better sensor, and a return at a distance is
not an object identified at that distance. No model has been run, so this work
produces no mAP, precision or recall.

**Returns beyond 150 m do not demonstrate detection beyond 150 m.** The stock
TruckScenes v1.2.0 evaluator filters detection classes at 75 m or 150 m by
class and therefore produces no detection score past 150 m at all. Testing the
beyond-150 m question needs an approved custom evaluator configuration, or
TruckDrive, and would be reported separately.

**The results depend on field of view and sampling.** One RADAR channel against
one LiDAR channel, each one of six, with different fields of view that are not
accounted for. Ten samples out of 400. Every percentage is a share of the
returns in this subset, never of the dataset.

**This analysis establishes nothing about weather.** The manifest includes every
scene without filtering on conditions. A handful of differently labelled scenes
cannot support a weather claim, and none is made.

## Where the detail is

| Page | Covers |
|---|---|
| [`SAMPLE-MANIFEST.md`](SAMPLE-MANIFEST.md) | the subset: what it contains, why it exists, how to rebuild it |
| [`RANGE-BANDS.md`](RANGE-BANDS.md) | the summary and charts: columns, bands, measured result, full limits |
| [`RANGE-BANDS-OPEN-QUESTION.md`](RANGE-BANDS-OPEN-QUESTION.md) | why the band edges are unresolved, and who decides |
| [`ACCEPTANCE-CHECK.md`](ACCEPTANCE-CHECK.md) | how a teammate verifies they get the same result |
| [`SUMMARY.md`](SUMMARY.md) · [`findings-fatima.md`](findings-fatima.md) | Sprint 2 setup, visualisation and findings |
| [`dataset-statistics.md`](dataset-statistics.md) | measured `v1.2-mini` inventory |
| [`../docs/dataset-surveys/truckscenes.md`](../docs/dataset-surveys/truckscenes.md) | the dataset survey — sensors, licence, fit |
