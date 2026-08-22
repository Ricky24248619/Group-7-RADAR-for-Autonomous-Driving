# Metrics Definitions (WS4)

Owners: **Ricky Yuen** (lead, per Skills & Resources Audit), **Damien Zhang**.
Every metric used in a comparison record must be defined here first — an
undefined metric in a results table is a bug in the results table.

Status: skeleton. To be completed before the first benchmark run; D-01 must be
confirmed with Fabian before benchmarking begins.

## Detection metrics

| Metric | Definition | Notes / caveats |
|---|---|---|
| Precision | TP / (TP + FP) at the matching threshold below | State the IoU / centre-distance threshold with every number |
| Recall | TP / (TP + FN) | same |
| mAP | Mean average precision over classes and thresholds | **Not interchangeable with NDS** (see below) |
| Processing time | Wall-clock per frame (or per batch — state which), on named hardware | Hardware-dependent: only comparable within one machine, noted in the record |

## Segmentation / terrain metrics (GOOSE, STONE)

D-02 says results are compared only within a task type — so segmentation and
traversability results get their own metric set and **never share a table or
axis with detection metrics** (mAP ↔ mIoU comparisons are meaningless).

| Metric | Task / dataset | Definition | Status |
|---|---|---|---|
| mIoU (2D) | Semantic segmentation — GOOSE | Mean intersection-over-union over classes; state which taxonomy (GOOSE ships 64-class full and 8-class challenge remaps — they are not interchangeable) | **To define precisely** (Ricky) |
| mIoU (3D) | Point-cloud segmentation — GOOSE | Same, over point-wise labels (SemanticKITTI format) | **To define precisely** (Ricky) |
| Traversability per-class IoU / accuracy | Voxel traversability — STONE | 4 classes (Free / Traversable / Potentially / Non-Traversable); note voxel grid ends at ±25.6 m, so range-banded reporting does not apply | **To define if STONE strand proceeds** |

## Open questions (resolve here before first benchmarking)

1. **NDS vs mAP (nuScenes-style).** NDS blends detection accuracy with
   position, velocity and orientation error, so an NDS number cannot sit in
   the same table as an mAP number without a note. Decide: adopt NDS where
   the devkit provides it, or stay on plain mAP everywhere for comparability?
   *(Assigned to Ricky — the Skills Audit names this explicitly.)*
2. **Matching criterion per dataset.** TruckScenes and TruckDrive may use
   different match thresholds by default; D-01 says within-dataset comparison
   only, so record the default per dataset and don't normalise across them.
3. **Range bands (D-04).** Confirm band edges: proposal is 0–50 / 50–100 /
   100–150 / 150–400 m. Bands with no results read "no data", never 0.
4. **Radar-specific metrics.** If no radar-first baseline exists (D-02 gap,
   to confirm with Fabian), what do we report for radar — qualitative
   comparison only? Raise with Fabian alongside D-01/D-04 confirmation.

## Rule of thumb for tables

Every number carries: metric name → defined above; threshold; range band;
dataset + version; modality; model + version. If any of those is missing, the
number can't be compared to anything and shouldn't leave this repo.
