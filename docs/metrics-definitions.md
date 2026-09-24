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
| Range treatment | Same declared range filter or band edges; measured coverage counts may be zero, while unavailable measurements and undefined scores read `no data` |
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
3. **Range bands (D-04).** The 21 September working coverage protocol below fixes
   descriptive bands. A custom detection benchmark beyond the stock class ranges
   still requires explicit approval; coverage bands do not change the evaluator.
4. **Radar-specific metrics.** If no radar-first baseline exists (D-02 gap,
   to confirm with Fabian), what do we report for radar — qualitative
   comparison only? Raise with Fabian alongside D-01/D-04 confirmation.

## Rule of thumb for tables

Every number carries: metric name → defined above; threshold; range band;
dataset + version; modality; model + version. If any of those is missing, the
number can't be compared to anything and shouldn't leave this repo.


## Sprint 3 working coverage protocol — 21 September 2026

Prepared for RY-S3-1 under Ricky's instruction to complete the protocol work.
This is the implementation baseline for descriptive sensor-return counts;
it does not claim client approval of a new detection metric or evaluator.

- Bands are **[0,50), [50,100), [100,150), [150,400), [400,infinity) metres**.
  A return exactly on an edge goes into the band starting at that edge.
  Parameters remain available for explicitly labelled alternative analyses.
- The existing FA-S3-1 output uses planar `sqrt(x*x+y*y)` in each sensor's own
  stored frame. It has separate physical origins and, for the tilted LiDAR,
  a different plane from ego-ground distance. Preserve that definition and label
  it; do not relabel the historical counts as ego-frame or 3D ranges.
- Scope: the first annotated sample of each of ten mini scenes; one
  `RADAR_LEFT_FRONT` and one `LIDAR_TOP_FRONT` channel. Report each modality's
  available sample count and its own return denominator. Missing channels must
  not be described as a complete matched sample set.
- A measured count of no returns is **0**. Unavailable data is **no data**.
  A share with denominator zero is undefined and also **no data**. An empty
  ground-truth band has no defined detection score merely because it has zero
  returns; detection scoring must follow its separately declared evaluator.
- Reject non-finite ranges and band definitions that leave near returns out of
  the denominator. Do not silently drop invalid coordinates.
- These panels describe channel coverage. They cannot rank modalities, prove
  weather robustness, or establish object detection beyond 150 m.
- A future fairer geometry comparison needs a declared common ego frame/time,
  transformed clouds, overlapping field of view and matched sample tokens.
  Publish that as a new analysis with its own manifest and outputs.

The stock detection evaluator and its class limits remain unchanged. Fabian's
confirmation of any custom detection protocol, primary metric and TruckDrive
matching criterion remains outstanding.

### Saved-output comparison diagnostics

The [22 September raw comparison](truckscenes-raw-comparison.md) additionally
reports counts in a reference ego x-y plane, using the nearest ego pose to each
annotated sample timestamp. Sensor clouds use the release calibration and
acquisition ego poses to reach that reference. Its forward region is x>0,
absolute ego azimuth <=30°, without an elevation filter. Denominators are all
returns from the named channel inside the named region across the 80 mini_val
samples. Raw box-centre counts use the same frame and report both full azimuth
and forward region; they do not apply evaluator filters or imply box matching.
These are new descriptive measurements; the stock evaluator remains unchanged.

The [TruckScenes saved-output analysis](truckscenes-saved-comparison.md) adds
descriptive diagnostics, not a new evaluation protocol:

- **Per-sample >=150 m share:** returns in [150,400) and [400,infinity), divided
  by all returns in that sample/channel. A zero denominator is undefined.
- **Pooled share:** sum of distant returns divided by sum of available returns.
  **Median sample share:** median of the defined per-sample shares, giving each
  sample equal weight. Report sample counts alongside both.
- **Exact retained/added/removed boxes:** multiset comparison of complete saved
  box dictionaries within the same sample token; key ordering is ignored and
  duplicate multiplicity is preserved. These count records, not unique objects,
  correct detections or completed inference jobs.
- **Eleven-class AP mean excluding traffic cones:** unweighted mean of the saved
  per-class APs for the other eleven classes. This sensitivity diagnostic is
  separate from the official twelve-class mAP and never replaces it.
