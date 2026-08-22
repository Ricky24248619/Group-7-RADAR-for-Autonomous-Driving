# Comparison Record — Result Template (RY-1)

One file (or one row, once the results store exists) per recorded result.
Governs decision **D-01**: comparison happens within a dataset, never across
datasets on a shared axis.

**The first block is mandatory — an entry with any of these blank is not a
valid entry.** That is deliberate: it enforces D-01 at the data layer instead
of relying on whoever reads the chart later.

---

## Mandatory identification (D-01 — cannot be blank)

| Field | Value |
|---|---|
| Dataset name | (e.g. TruckDrive v1.0 — exact name and version) |
| Full sensor configuration | (every sensor used in this run, e.g. "1× front radar, 1× roof LiDAR" — not "the sensors") |
| Annotation schema | (label set + format + version, e.g. "3D boxes, 9 classes, nuScenes-style") |
| Task type | (e.g. LiDAR 3D detection / camera–LiDAR fusion / 2D detection — governs D-02) |

## Run details

| Field | Value |
|---|---|
| Model / tool + version | (exact repo commit or release tag) |
| Modality used | (camera / LiDAR / radar / fusion — which inputs this run received) |
| Data split / conditions | (train/val/test, scene subset, weather, day/night if relevant) |
| Owner | |
| Date | |
| Evidence link | (link to the experiment-log entry and/or the raw output file in this repo) |

## Results

| Range band | Metric 1 | Metric 2 | Processing time | Notes |
|---|---|---|---|---|
| 0–50 m | | | | |
| 50–100 m | | | | |
| 100–150 m | | | | |
| 150–400 m | | | | |

Report **by range band** (D-04). If a band has no results, write "no data" —
never 0. Metrics are defined in `docs/metrics-definitions.md`; don't invent a
metric that isn't defined there, add it to that document first.

## Limitations

What this result does and does not show. Be honest — this field is what makes
the comparison defensible rather than misleading.
