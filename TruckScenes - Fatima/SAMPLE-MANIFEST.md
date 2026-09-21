# Matched TruckScenes sample manifest

**Owner:** Fatima Sher · **Story:** FA-S3-1 · **Reviewer:** Kelsey Chen

## What it is

`sample-manifest.csv` and `sample-manifest.json` are the declared list of MAN
TruckScenes samples that this project's radar/LiDAR analysis is measured on.
Same rows in both formats — CSV for reading in a spreadsheet, JSON for scripts.

One row per sample, carrying: scene name and token, sample token, sample
timestamp, the radar and LiDAR channel names, the radar and LiDAR sample-data
tokens, the annotation count, the coordinate frame, the inclusion rule, and
whether both channels were actually present.

## Why it exists

FA-S3-1 is done only when *another member can rerun the saved sample list and
obtain the same summary*. Until now the subset existed only as a line of code
inside `scripts/truckscenes_stats.py`, so "the samples" could not be checked,
cited or reused without reading that script. Writing the subset down first also
fixes the denominator for every count produced later: a chart can now say
exactly what it counted and out of what.

The manifest deliberately contains **no generation timestamp and no machine
details**, so regenerating it on a different machine on a different day
produces a byte-identical file. A file that changes on every run cannot be used
to prove two people analysed the same thing.

## Sampling policy

Unchanged from Sprint 2 — this file records the existing policy, it does not
introduce a new one:

> The first annotated sample of every scene in v1.2-mini
> (`scene['first_sample_token']`), in devkit scene-table order. All scenes are
> included; nothing is filtered on weather, location or content.

That is **10 samples out of the 400 annotated samples** in the mini split.

## Channels

| Role | Channel | Note |
|---|---|---|
| Radar | `RADAR_LEFT_FRONT` | one of the six ARS 548 RDI radars |
| LiDAR | `LIDAR_TOP_FRONT` | one of the six LiDAR sensors |

Both match the channels used by the existing evidence images and statistics, so
the manifest describes the same data those figures came from.

## Coordinate frame

Point clouds are read straight from their `.pcd` files, so each cloud is in
**its own sensor's coordinate frame**. No transform to the ego-vehicle or
global frame is applied anywhere in this analysis. Any range computed from
these samples is therefore measured from that sensor's own origin, and radar
and LiDAR ranges are measured from two different physical positions on the
truck.

## How to regenerate

```bash
# activate the project virtualenv first -- its location differs per machine,
# see SETUP.md
export TRUCKSCENES_ROOT=/path/to/man-truckscenes
python scripts/truckscenes_sample_manifest.py
```

`TRUCKSCENES_ROOT` is the folder containing `v1.2-mini/`, `samples/` and
`sweeps/`.

Or pass the path directly with `--data-root`. Output locations can be changed
with `--csv-output` and `--json-output`.

Check the result is unchanged:

```bash
git diff --stat "TruckScenes - Fatima/sample-manifest.csv"
```

No output means the regenerated manifest matches the committed one.

## Limits

- 10 of 400 annotated samples, and one of six radars against one of six LiDARs.
  This is a declared development subset, not full sensor or dataset coverage.
- The manifest records **which samples are analysed**. It contains no point
  counts, no range bands and no model output, and it is not evidence about
  detection performance.
- A row whose `record_status` is not `complete` is kept, not dropped, so the
  gap stays visible in the denominator.
