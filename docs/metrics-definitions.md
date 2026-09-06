# Metrics Definitions (WS4)

Owners: **Ricky Yuen** (lead, per Skills & Resources Audit), **Damien Zhang**.
Every metric used in a comparison record must be defined here first — an
undefined metric in a results table is a bug in the results table.

Status: segmentation definitions complete for Sprint 2; detection questions remain
open. D-01 must be confirmed with Fabian before benchmarking begins.

Current evidence, checkpoint availability and a bounded pilot proposal are in the
[dataset comparison](dataset-comparison.md).

## Detection metrics

| Metric | Definition | Notes / caveats |
|---|---|---|
| Precision | TP / (TP + FP) at the matching threshold below | State the IoU / centre-distance threshold with every number |
| Recall | TP / (TP + FN) | same |
| mAP | Mean average precision over classes and thresholds | **Not interchangeable with NDS** (see below) |
| Processing time | Wall-clock per frame (or per batch — state which), on named hardware | Hardware-dependent: only comparable within one machine, noted in the record |

### TruckScenes paired-modality fairness contract (draft)

**Status:** working protocol for review by Fabian before benchmarking. It applies D-01
without deciding the still-open headline metric or custom range bands.

The reference evaluator is the official TruckScenes devkit **v1.2.0** with its
[`detection_cvpr_2024.json`](https://github.com/TUMFTM/truckscenes-devkit/blob/v1.2.0/src/truckscenes/eval/detection/configs/detection_cvpr_2024.json)
configuration and
[`DetectionEval`](https://github.com/TUMFTM/truckscenes-devkit/blob/v1.2.0/src/truckscenes/eval/detection/evaluate.py)
implementation. Under that stock configuration, mAP uses ground-plane centre-distance
thresholds of 0.5, 1, 2 and 4 m; TP errors use 2 m; minimum precision and recall are
0.1; and each sample may contain at most 500 predicted boxes. Record both mAP and the
devkit's nuScenes Detection Score (NDS) until Fabian confirms which one is primary.
An NDS computed on TruckScenes is not comparable with an NDS computed on the nuScenes
dataset.

Two radar-only and LiDAR-only results form a paired comparison only when every row
below is satisfied:

| Comparison field | Contract |
|---|---|
| Dataset | Same TruckScenes release and data-root provenance |
| Evaluation subset | Same split and exact set of sample tokens; an empty prediction list is valid, a missing sample token is not |
| Ground truth | Same annotation release, 12-class detection taxonomy, ignored classes and preprocessing |
| Evaluator | Same devkit commit, config file, matching thresholds, class ranges and missing-value handling |
| Range treatment | Same declared range filter or band edges; empty bands read `no data`, never zero |
| Temporal input | Same past-time horizon; record the sensor-specific number of sweeps actually used |
| Training protocol | Same train/validation split, initialization policy, schedule, augmentations, seed policy and stopping rule |
| Reporting | Same metric set, class set, per-class aggregation and confidence/repeat policy |
| Modality metadata | Radar-only sets `use_radar=true` and LiDAR-only sets `use_lidar=true`; the opposite sensor, camera, map, external data and future frames are `false` in both rows; `use_tta` must match |

A modality-specific input encoder may be necessary. If the two runs use different
model families, materially different capacity, training data or compute budgets, the
result is still useful but must be labelled **model-plus-modality comparison**. It is
not evidence that the sensor alone caused the difference. A sensor-effect claim needs
the same model family and matched protocol, with only unavoidable modality adapters
and the declared sensor input changed. If either row uses camera, map, external data or
future frames, name those auxiliary inputs in the comparison label rather than calling
the result sensor-only.

The stock evaluator filters classes at either 75 m or 150 m, as documented in the
official
[`detection task`](https://github.com/TUMFTM/truckscenes-devkit/blob/v1.2.0/src/truckscenes/eval/detection/README.md).
It therefore produces no official detection metric beyond 150 m. TruckScenes can test
the paired-modality question with the stock evaluator, but D-04's `>150 m` question
requires TruckDrive or an explicitly approved custom TruckScenes configuration.

## Segmentation / terrain metrics (GOOSE, STONE)

D-02 says results are compared only within a task type — so segmentation and
traversability results get their own metric set and **never share a table or
axis with detection metrics** (mAP ↔ mIoU comparisons are meaningless).

### Exact definitions

For a class `c`, computed over the complete named evaluation subset:

- `TP_c`: pixels/points whose prediction and ground truth are both `c`
- `FP_c`: pixels/points predicted as `c` whose ground truth is another scored class
- `FN_c`: pixels/points whose ground truth is `c` but prediction is another class
- **Per-class IoU:** `IoU_c = TP_c / (TP_c + FP_c + FN_c)`
- **Overall accuracy:** number of correctly classified scored pixels/points divided by
  the total number of scored pixels/points. This is prevalence-weighted and must never
  be presented as a substitute for mIoU.

**mIoU** is the arithmetic mean of `IoU_c` over the explicitly declared evaluated
class set `E`. A class with no ground-truth and no predicted members has zero union, so
its IoU is undefined and it is excluded rather than converted to zero. A class absent
from ground truth but predicted by the model has non-zero union and remains in `E` with
IoU zero, so hallucinating an absent class is still penalised. Every reported mIoU must
state `|E|` and list excluded or ignored classes.

This rule matters in GOOSE: R2 found 22 of 64 classes below 0.01% of validation points,
including six with zero points. Blindly averaging placeholder zeros over all 64 would
measure taxonomy sparsity as if it were model failure.

| Metric | Unit being classified | Required reporting context |
|---|---|---|
| 2D per-class IoU / mIoU | Camera-image pixels | Image split, evaluated class set and taxonomy |
| 3D per-class IoU / mIoU | LiDAR points | Point-cloud split, evaluated class set and taxonomy |
| 4-class traversability IoU / mIoU | Pixels, points or voxels — state which | Mapping version and four-class evaluated set |
| Overall accuracy | Same unit as the corresponding IoU | Scored/ignored labels and class distribution |

### Traversability projection rule

A 2D traversability score derived from a 3D point cloud must name the projection used
to select points for each bird's-eye cell. A raw all-return projection can paint tree
canopy and other elevated returns over drivable ground, so it is not interchangeable
with a lowest-return-per-cell ground slice or another terrain-selection rule.

The GOOSE D4 comparison demonstrates the size of this effect. In
`aying_mangfall_2`, the apparent non-traversable share fell from 92% in the raw
projection to 58% with the ground slice; across the inspected scenarios, the blocked
share never increased. The traversable share is not guaranteed to move in one
direction (`garching_uebungsplatz_2` changed from 31% to 26%), so this is a reporting
boundary rather than a correction factor. Every traversability metric must state the
projection, cell size, point-selection rule, height/range limits, and treatment of
empty cells. Results produced by different projection rules must not share a series or
ranking without being labelled as different methods.

### Taxonomy rule

The metric name alone is insufficient. Every value is labelled as exactly one of:

1. **GOOSE full 64-class taxonomy**
2. **GOOSE 8-class challenge remap**
3. **Team 4-class traversability mapping** (`traversability_map.csv` version/commit)

These are three different classification problems and therefore three different
numbers. They never share a series, axis, or ranking. Segmentation mIoU/IoU/accuracy
also never shares a comparison table or axis with detection mAP; no conversion between
them exists.

STONE, if unblocked, uses the same four class names but its voxel grid ends at ±25.6 m.
It must be reported as STONE voxel traversability and not pooled with GOOSE point-wise
traversability.

## Open questions (resolve here before first benchmarking)

1. **Primary detection metric.** TruckScenes provides both mAP and NDS; the draft
   contract records both without mixing them. Confirm with Fabian which is the primary
   modality-comparison metric.
2. **TruckDrive matching criterion.** TruckScenes v1.2.0 is now pinned above. Record
   TruckDrive's official thresholds separately and do not normalise across datasets.
3. **Range bands (D-04).** Confirm band edges: the proposal is 0–50 / 50–100 /
   100–150 / 150–400 m. The stock TruckScenes evaluator ends at 75 or 150 m by class,
   so any custom extension requires explicit approval. Bands with no results read
   "no data", never 0.
4. **Radar-specific metrics.** If no radar-first baseline exists (D-02 gap,
   to confirm with Fabian), what do we report for radar — qualitative
   comparison only? Raise with Fabian alongside D-01/D-04 confirmation.

## Rule of thumb for tables

Every number carries: metric name → defined above; threshold; range band;
dataset + version; modality; model + version. If any of those is missing, the
number can't be compared to anything and shouldn't leave this repo.
