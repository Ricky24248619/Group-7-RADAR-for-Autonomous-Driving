# EXP-0005 — TruckDrive mini setup and sensor characterisation

- **Date started / completed:** 2026-09-04 / 2026-09-05
- **Owner:** Kelsey Chen
- **Workstream / story:** TruckDrive dataset exploration and sensor loading

## Goal

Confirm that TruckDrive can run locally on Windows, verify synchronized Camera,
LiDAR and Radar access, and characterise the 24-scene mini split for later
visualisation and documentation.

## Environment

- Windows
- Python 3.11.11
- Conda environment: `truckdrive_visualizer`
- NumPy 1.26.4
- Open3D 0.19.0
- PyQt5 5.15.11
- Raw TruckDrive data stored outside the Git repository

## Dataset / data subset

- TruckDrive mini split: 24 scenes (`scene_28_1` to `scene_28_24`)
- Radar, annotations, calibrations and poses available for all 24 scenes
- Camera and LiDAR retained for `scene_28_1` and `scene_28_22`
- `scene_28_22` was selected as an additional representative long-range scene
- The full mini split was not downloaded with every modality because the compressed
  total is approximately 282.71 GB

## Steps and commands

Official viewer:

```powershell
python entrypoint.py `
  --root-dir "C:\Users\Czy20\CITS3200\radar-project\TruckDrive-data\TruckDrive" `
  --recording scene_28_1
```

Dataset statistics:

```powershell
python scripts/truckdrive_stats.py `
  --root "C:\Users\Czy20\CITS3200\radar-project\TruckDrive-data\TruckDrive"
```

Synchronized sensor check:

```powershell
python scripts/truckdrive_sensor_check.py `
  --root "C:\Users\Czy20\CITS3200\radar-project\TruckDrive-data\TruckDrive" `
  --scene scene_28_22
```

The same sensor check was also run successfully on `scene_28_1`.

## Outcome

- [x] Success — worked as intended
- [ ] Partial
- [ ] Failure

The official viewer successfully displayed Camera, Aeva LiDAR and Continental Radar
data.

The 24-scene characterisation measured:

- 12,502 Radar frames
- 4,800 bounding-box annotation frames
- 480 lane-line annotation frames
- 526,148 3D bounding boxes
- 27 object classes

One annotated Radar frame was selected from each scene. Across these 24 samples,
6,746 Radar detections were measured at 150 m or greater.

Direct synchronized Camera/LiDAR/Radar loading succeeded on both `scene_28_1` and
`scene_28_22`.

Detailed measurements are recorded in:

`TruckDrive - Kelsey/dataset-statistics.md`

## Attempted fixes

1. Python `urllib` failed to access the CloudFront listing because of an SSL error.
   `curl.exe` was used instead.
2. OpenCV was unavailable, so Pillow was used to read Camera JPEG files.
3. The first Radar archive was extracted one directory too high; extraction was
   corrected to the official `scene/radar/...` structure.
4. VSCode Pylance initially used the wrong Python interpreter; it was changed to
   `truckdrive_visualizer`.

## Decision

- [ ] Retry
- [x] Change approach — use a lightweight 24-scene Radar/annotation subset and retain
  full multimodal data only for representative scenes
- [ ] Stop

**Time spent:** Work completed across 4–5 September 2026.

## Next action

Provide the statistics and synchronized sensor-loading workflow for the TruckDrive
visualisation and documentation stage, together with basic Camera/LiDAR/Radar evidence.