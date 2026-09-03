# EXP-0004 — MAN TruckScenes mini setup and paired sensor visualisation

- **Date started / completed:** 2026-08-18 / 2026-09-03
- **Owner:** Fatima Sher
- **Workstream / story:** WS2 / FA-1, FA-3

## Goal

Determine whether the official TruckScenes devkit can load the locally downloaded v1.2-mini dataset on Apple Silicon and reproducibly render matched 4D RADAR and LiDAR samples with ground-truth annotations.

## Environment

- macOS 26.3.1, Darwin arm64, Apple Silicon MacBook Air.
- Python 3.11.4 in the isolated `truckscenes-env` virtual environment.
- `truckscenes-devkit==1.2.0`, `numpy==2.4.6`, `matplotlib==3.11.1`, `pypcd4==1.4.3`, `pyquaternion==0.9.9`.
- Native macOS execution. No CUDA device was required for dataset loading, measurement or rendering.

## Dataset / data subset

- MAN TruckScenes `v1.2-mini`, downloaded from the official distribution.
- All 10 mini scenes and their 400 annotated samples were loaded.
- The first annotated sample from each scene was selected for paired evidence.
- Channels used: `RADAR_LEFT_FRONT` and `LIDAR_TOP_FRONT`.
- Ground truth: TruckScenes/nuScenes-style oriented 3D boxes, 27-category metadata.
- Raw dataset location is supplied at runtime and is intentionally outside Git.

## Steps and commands

```bash
python3 -m venv truckscenes-env
source truckscenes-env/bin/activate
python -m pip install "truckscenes-devkit[all]==1.2.0"
export TRUCKSCENES_ROOT=/path/to/man-truckscenes
python scripts/visualize_truckscenes_sample.py --scene-count 10
python scripts/truckscenes_stats.py
python scripts/validate_result.py results/records/0006-truckscenes-mini-characterisation.json
python scripts/validate_result.py results/records/0007-truckscenes-macos-devkit-feasibility.json
```

## Outcome

- [x] Success — worked as intended
- [ ] Partial — describe what worked and what did not
- [ ] Failure — did not achieve the goal

The devkit loaded 10 scenes, 400 annotated samples, 25,750 annotation records and 43,556 sample-data records. The scripts generated 20 images: one matched RADAR/LiDAR pair for every scene. Across those selected samples, `RADAR_LEFT_FRONT` contained 4,571 points and `LIDAR_TOP_FRONT` contained 165,588 points. RADAR contained 305 returns at radial distance 150 m or greater.

The orange boxes in the images are supplied dataset ground truth, not model predictions. No object-detection model was run, so this experiment produces no mAP, precision or recall.

## Attempted fixes

1. Rendering initially encountered a compatibility problem because devkit 1.2.0 expects `matplotlib.cm.get_cmap`, which is absent in the installed Matplotlib version.
2. Added a narrow compatibility mapping to `matplotlib.colormaps.get_cmap` before the devkit renderer is used.
3. Re-ran the visualisation; all selected RADAR and LiDAR images were produced successfully.
4. Replaced the original machine-specific dataset path with `--data-root` and `TRUCKSCENES_ROOT` options so teammates can reproduce the scripts.

## Decision

- [ ] Retry
- [x] Change approach — move from setup validation to a time-boxed pretrained-model feasibility study
- [ ] Stop — this path is closed

**Time spent:** Approximately 6 hours across download/setup, dataset inspection, visualisation, statistics and initial documentation.

## Next action

Review the dataset survey and reproduce at least one scene, then choose one existing TruckScenes-compatible 3D-detection checkpoint and record its hardware, licence, sensor inputs and evaluation compatibility before attempting inference.
