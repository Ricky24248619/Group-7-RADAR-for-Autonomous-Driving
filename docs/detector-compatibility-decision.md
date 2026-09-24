# Detector comparison: compatibility decision

24 September 2026 · EXP-0018 · result 0021

**The model comparison is not ready to run at 200–400 m.** We downloaded and
verified both published L-RadSet PointPillars checkpoints, then inspected their
embedded training configurations. They use input grids ending at approximately
70 m forward. Scoring them on our distant TruckDrive cohort would confound
sensor performance with model input cropping and cross-dataset transfer.

The [completed five-scene geometric-support result](truckdrive-multiscene-result.md)
stands. No new neural inference, detector precision/recall, AP or measured GPU
memory requirement is claimed here.

## What was checked

| Candidate | Verified input extent in x (m) | Availability | Our 200–400 m vehicle centers inside its input rectangle |
|---|---:|---|---:|
| L-RadSet PointPillars LiDAR checkpoint | 0 to 70.2 | Downloaded, ZIP CRC and SHA-256 verified | 0 / 504 |
| L-RadSet PointPillars radar checkpoint | 0 to 70.4 | Downloaded, ZIP CRC and SHA-256 verified | 0 / 504 |
| L-RadSet long-range LiDAR/radar example configs | 0 to 150.4 | Source configurations; downloaded weights have different extents | 0 / 504 |
| TruckDrive full-range LiDAR config | -160 to 272 | Source config; no compatible checkpoint located in the inspected release | 192 / 504 |

These are rectangular **input-region checks**, not detection rates or guaranteed
limits on regressed box centers. The y limits also matter: ±40.2 m for the
L-RadSet configurations and ±108 m for TruckDrive. The raw TruckDrive annotation
centers were compared directly with the declared regions; a cross-platform
learned-model adapter has not been validated. Checkpoint strings were parsed
without executing their configuration or unpickling their Python objects.

The official checkpoint links are in the [L-RadSet model table](https://github.com/crrasjtu/L-RadSet/tree/9eda9266db3109e4f153eeeb43fef3125d213674#8-experiment-results).
The [TruckDrive release instructions](https://github.com/torc-ai/TruckDrive/blob/a09217e877fe6bad821f9828240c4c1b64d29da1/mmdet_project/README.md)
provide a training workflow. Its inspected source contains LiDAR and
LiDAR-camera configurations, with no matching pretrained radar-only comparison
identified. This is an audit of those releases, not proof that no suitable model
exists elsewhere. Pinned source URLs and hashes are in the audit JSON.

## What the TruckDrive full-range crop includes

| Distance band | Vehicle observations | Centers within configured input rectangle |
|---|---:|---:|
| 200–250 m | 173 | 128 |
| 250–300 m | 166 | 64 |
| 300–400 m | 165 | 0 |
| 200–400 m | 504 | 192 (38.10%) |

The aggregate overlaps the three preceding rows. This is why a config named
`fullrange` must not automatically be interpreted as covering all annotations
out to 400 m. Increasing the crop on pretrained weights would change the
experiment; it would not establish training or calibration at those distances.

## Remaining compatibility and compute questions

- The radar checkpoint loads eight stored columns and uses six; LiDAR uses four.
  TruckDrive radar stores 33 columns and its LiDAR streams use different layouts.
  The inspected public L-RadSet loading code does not establish the semantics
  and normalization of every radar feature needed for a verified adapter.
- Sensor calibration, origin/height, intensity or radar-feature scaling, class
  mappings and temporal history must be reconciled before scoring predictions.
- The local GTX 1660 has 6 GB VRAM. CUDA is available in the existing WSL PyTorch
  2.0.1 environment, but the MMDetection stack is absent there. We did not alter
  the working GOOSE environment or install a stack for models that fail the
  required range check. No inference-memory benchmark was performed.
- L-RadSet raw data still requires the author's agreement/request process.
  Checkpoint access does not grant raw-data access. No request was sent.

## Decision and next action

Present the completed sensor-support study now. Treat the learned-detector
comparison as a separate experiment with a concrete model-access prerequisite.

1. Obtain compatible long-range weights, training configs and input-feature
   definitions for both modalities. The most direct lead is the TruckDrive
   authors' released LiDAR configuration and any available radar baseline.
2. Confirm their overlapping input extent, class definitions and temporal
   history. Initially use a common, verified region rather than assuming
   200–400 m is supported. Keep the current five scenes as exploratory data.
3. Validate coordinates numerically and inspect single-frame predictions before
   evaluating newly fixed held-out scenes. Report unmatched predictions as well
   as missed objects, with explicit class and distance matching.
4. Only then benchmark batch-one GPU memory and decide whether additional
   compute is needed. More GPU memory alone cannot supply missing weights or
   repair an incompatible training range.

Draft request for the team/client to send if appropriate:

> We have completed a paired sensor-support analysis on five TruckDrive mini
> scenes and want to test detection performance next. Are trained LiDAR-only
> and radar-only weights available for a common region beyond 200 m, together
> with their exact training configs, feature definitions, temporal preprocessing
> and evaluation split? The public full-range LiDAR config currently declares
> x=-160 to 272 m. Please confirm the intended evaluated region and whether a
> radar baseline is available.

## Reproduction and saved resources

Downloaded weights remain outside Git at `F:/RADAR/models/L-RadSet/pp_lidar.pth`
and `pp_radar.pth`. The repository contains [checkpoint/config metadata and hashes](evidence/detector-compatibility/audit.json)
and [coverage by range](evidence/detector-compatibility/input_roi_coverage.csv).
Every raw annotation consulted was checked against the preceding experiment's
input hashes. The audit uses the standard library and makes no network calls.

```text
python scripts/audit_detector_compatibility.py --model-root <models>/L-RadSet --dataset-root <datasets>/TruckDrive --truckdrive-source <torc-ai/TruckDrive-checkout> --lradset-source <crrasjtu/L-RadSet-checkout>
```

Regression tests cover config parsing without execution, checkpoint string
extraction without unpickling, and rectangular versus radial range boundaries.
