# TruckScenes mini dataset statistics

These measurements come from the local MAN TruckScenes `v1.2-mini` split prepared
for this project (devkit `1.2.0`, dataroot layout confirmed against the devkit's
loader in `experiment-log/0004-truckscenes-windows-devkit-tutorial.md`).

---

## 1. Dataset coverage

| Table | Rows |
|---|---:|
| sample | 400 |
| scene | 10 |
| sample_data | 43,556 |
| sample_annotation | 25,750 |
| instance | 1,094 |
| ego_pose | 20,116 |
| ego_motion_cabin | 20,090 |
| ego_motion_chassis | 20,089 |
| category | 27 |
| sensor | 18 |
| calibrated_sensor | 18 |
| attribute | 11 |
| weather_annotation | 10 |
| visibility | 4 |

`sweeps/` is not present in this local copy — the mini archive ships keyframes
(`samples/`) only, not intermediate-frame sensor data.

---

## 2. Sensor suite

16 sensors across 3 modalities, all present under `samples/`:

| Modality | Channels |
|---|---|
| Camera (4) | `CAMERA_LEFT_FRONT`, `CAMERA_RIGHT_FRONT`, `CAMERA_LEFT_BACK`, `CAMERA_RIGHT_BACK` |
| LiDAR (6) | `LIDAR_LEFT`, `LIDAR_RIGHT`, `LIDAR_REAR`, `LIDAR_TOP_FRONT`, `LIDAR_TOP_LEFT`, `LIDAR_TOP_RIGHT` |
| Radar (6) | `RADAR_LEFT_FRONT`, `RADAR_RIGHT_FRONT`, `RADAR_LEFT_BACK`, `RADAR_RIGHT_BACK`, `RADAR_LEFT_SIDE`, `RADAR_RIGHT_SIDE` |

Camera images are 1980x943 — a different resolution and aspect ratio to
nuScenes' 1600x900, and mounted higher (~2.1m, per `calibrated_sensor`) than
nuScenes' car-mounted cameras (~1.5m). That height difference turned out to
matter — see §4.

---

## 3. `mini_val` split

| Item | Value |
|---|---:|
| Scenes | 2 |
| Samples (keyframes) | 80 |

Confirmed via `truckscenes.utils.splits.create_splits_scenes()["mini_val"]`,
not assumed from the table counts above.

---

## 4. Zero-shot camera detection result

A pretrained (nuScenes-trained) FCOS3D monocular 3D detector was run against
all 80 `mini_val` samples, front-left camera only, with no fine-tuning on
TruckScenes. Full method and reasoning: `experiment-log/0006-fcos3d-truckscenes-zeroshot.md`
and `results/records/0007-fcos3d-truckscenes-zeroshot.json`.

| Measurement | Value |
|---|---:|
| Samples evaluated | 80 / 80 (front-left camera only) |
| Predicted boxes (score >= 0.10) | 959 |
| Ground-truth boxes (after range/visibility filtering) | 2,088 |
| mAP | 0.0000 |

This is a diagnosed result, not a broken pipeline: nearest prediction-to-
ground-truth distances measured 5-21m and scale with range, the signature of
monocular depth misestimation rather than a coordinate-transform bug — every
match falls just outside even the loosest 4m matching threshold. Read as
evidence of camera-height domain gap (see §2), not as "the model doesn't
work" or "the pipeline is broken."

The evaluator also reports NDS and the five TP-error metrics (mATE, mASE,
mAOE, mAVE, mAAE) from the same run; those aren't listed here because NDS is
an explicitly open, unresolved question in `docs/metrics-definitions.md`
(assigned to Ricky) and the TP-error metrics aren't defined there yet either.
Raw numbers are in the evidence files referenced above if useful once that
decision lands.

---

## 5. Interpretation and limits

- Only one of four cameras was used for the detection run (CPU-only
  inference, ~28s/image on this hardware — four cameras across 80 samples
  would take roughly two hours). All 80 samples' ground truth was still
  scored; missing cameras cost recall, not coverage.
- No LiDAR or radar model has been run. This machine has no NVIDIA GPU, and
  the paper's own LiDAR baseline (CenterPoint) needs `spconv`, which has no
  practical CPU path — see `experiment-log/0006` for the full reasoning.
- The mAP above describes one zero-shot camera model's cross-dataset
  transfer, not TruckScenes' inherent difficulty, and must not be compared
  against a from-scratch-trained baseline without noting that difference.
- `sweeps/` (non-keyframe sensor data) was never downloaded for this local
  copy — anything needing inter-keyframe data is out of scope until it is.
