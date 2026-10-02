# Survey: TruckDrive

## 0. Survey metadata

| | |
|---|---|
| Dataset | TruckDrive |
| Surveyed by | Kelsey Chen |
| Date surveyed | 2026-10-02 |
| Reviewed by | Not yet reviewed |
| Review date | Not yet reviewed |
| Survey status | Draft |

## 1. Local dataset coverage

The local TruckDrive mini setup contains all 24 mini scenes. Radar, bounding-box
annotations, lane-line annotations, calibrations and poses are available across the
24 scenes.

Camera and LiDAR data were retained for selected representative scenes rather than
the complete mini split because of the substantially larger storage requirement.
`scene_28_1` and `scene_28_22` contain Camera, LiDAR and Radar data for synchronized
multimodal checks.

| Item | Measured value | Scope |
|---|---:|---|
| Mini scenes | 24 | Local TruckDrive mini setup |
| Radar frames | 12,502 | All 24 mini scenes |
| Bounding-box annotation frames | 4,800 | All 24 mini scenes |
| Lane-line annotation frames | 480 | All 24 mini scenes |
| 3D bounding boxes | 526,148 | All 4,800 bounding-box annotation frames |
| Object classes | 27 | Bounding-box annotations |
| Camera/LiDAR/Radar complete representative scenes | 2 | `scene_28_1` and `scene_28_22` |

All 4,800 bounding-box annotation frames have a matching Radar frame based on the
TruckDrive synchronization ID.

Source: `TruckDrive - Kelsey/dataset-statistics.md`

## 2. Long-range Radar subset

A small consistent Radar subset was selected to examine whether long-range Radar
returns are present across the TruckDrive mini scenes.

One synchronized annotated Radar frame was selected from each of the 24 mini scenes.
For each scene, the first synchronization ID shared by Radar and bounding-box
annotations was used.

| Measurement | Value | Scope |
|---|---:|---|
| Selected scenes | 24 | One sample from each mini scene |
| Selected Radar frames | 24 | One synchronized annotated Radar frame per scene |
| Radar returns | 71,206 | Total across the 24 selected frames |
| Radar returns at 150 m or greater | 6,746 | Total across the 24 selected frames |
| Share at 150 m or greater | 9.47% | 6,746 of 71,206 selected-frame returns |

### Range definition

Radar range was calculated in the Radar coordinate frame as:

`sqrt(x^2 + y^2)`

The resulting range distribution was:

| Range band | Radar returns |
|---|---:|
| 0-25 m | 13,717 |
| 25-50 m | 22,264 |
| 50-80 m | 16,396 |
| 80-100 m | 5,356 |
| 100-150 m | 6,727 |
| 150 m+ | 6,746 |
| **Total** | **71,206** |

The 6,746 long-range returns therefore refer specifically to returns at 150 m or
greater within these 24 selected frames. They do not represent all 12,502 Radar
frames in the TruckDrive mini setup.

These measurements show that long-range Radar data is present in the selected
TruckDrive samples. They do not measure object-detection performance. No detection
model, precision, recall or mAP evaluation was used for these counts.

Source: `TruckDrive - Kelsey/dataset-statistics.md`

## 3. Representative multimodal scenes

Full Camera and LiDAR data were not retained for all 24 mini scenes. Multimodal
checks are therefore limited to the representative scenes for which Camera, LiDAR
and Radar data are locally available.

### `scene_28_1`

`scene_28_1` was the main scene used for TruckDrive setup and viewer verification.

The synchronized sensor check found 258 common Camera/LiDAR/Radar frames.

For the selected sensor-check frame:

| Modality | Available data |
|---|---|
| Camera | 3848 x 2168 RGB image |
| LiDAR | 217,519 points |
| Radar | 2,672 returns |

This scene was also used to verify Camera loading, Aeva LiDAR, Continental Radar,
projected 2D bounding boxes and direct synchronized multimodal access.

### `scene_28_22`

`scene_28_22` was retained as an additional multimodal scene after the 24-scene
Radar survey. Its selected annotated Radar frame contained the largest number of
150 m+ Radar returns among the 24 selected scene samples.

For that selected Radar sample:

| Measurement | Value |
|---|---:|
| Total Radar returns | 4,377 |
| Returns at 100-150 m | 640 |
| Returns at 150 m or greater | 708 |

The synchronized sensor check found 259 common Camera/LiDAR/Radar frames.

For the selected sensor-check frame:

| Modality | Available data |
|---|---|
| Camera | 3848 x 2168 RGB image |
| LiDAR | 451,201 points |
| Radar | 3,038 returns |

These two scenes provide the retained data for paired multimodal examples. They
must not be treated as Camera/LiDAR coverage of the complete 24-scene mini split.

Source: `TruckDrive - Kelsey/dataset-statistics.md`

## 4. Paired Radar and LiDAR evidence

A paired Radar/LiDAR analysis is available for `scene_28_1`. This analysis uses
frames for which the released annotations and required Radar and LiDAR sensor data
share the same synchronization ID.

The paired evidence contains:

| Item | Value |
|---|---:|
| Scene | `scene_28_1` |
| Available annotation frames | 200 |
| Paired frames | 200 |
| Unmatched annotation synchronization IDs | 0 |
| Valid object observations | 8,113 |
| Minimum annotated-object range | 3.89 m |
| Maximum annotated-object range | 399.03 m |

The paired analysis uses the following released sensor data:

| Modality | Sensor data |
|---|---|
| Radar | `conti542/joint_radars/detections` |
| LiDAR | `aeva/joint_lidars/points` |
| LiDAR | `ouster/forward_center/points` |
| LiDAR | `ouster/sideward_left/points` |
| LiDAR | `ouster/sideward_right/points` |
| Annotation | `bounding_boxes` |

Sensor data are matched using the same synchronization key and transformed using
the released calibration information.

A deterministic paired example is also available for `scene_28_1`, using
sample `63` (annotation `63:37`, instance `Vehicle:17`). The annotated
`Vehicle-Passenger` object is at a planar range of approximately 244.70 m.

`docs/evidence/truckdrive/paired-scene-28-1/example_car_200_250m.png`

The underlying paired-frame and object-level records are stored in:

- `docs/evidence/truckdrive/paired-scene-28-1/sensor_frames.csv`
- `docs/evidence/truckdrive/paired-scene-28-1/object_counts.csv`
- `docs/evidence/truckdrive/paired-scene-28-1/manifest.json`

This evidence demonstrates that paired Radar and LiDAR measurements are available
for `scene_28_1`. It is a geometric sensor-support analysis, not a detector
benchmark and does not establish that one modality has better detection performance
than the other.

The paired result applies to this retained scene and must not be interpreted as
paired Radar/LiDAR coverage of all 24 TruckDrive mini scenes.

## 5. Viewer verification and known issues

The previously reported `scene_28_1` viewer issues were re-tested as part of G-9.

| Issue | Current status | Effect on analysis |
|---|---|---|
| NumPy/SciPy dependency conflict | Resolved | No current dependency blocker. The viewer environment uses Python 3.11.11, NumPy 1.26.4 and SciPy 1.14.1. Both packages import successfully and `python -m pip check` reports no broken requirements. |
| Empty Camera channels | Resolved in the current local copy | All 11 Leopard Camera channels contain data. Each contains 259-260 images, so the earlier zero-frame result does not indicate missing Camera data in the current `scene_28_1` setup. |
| 2D bounding-box `x1 >= x0` draw error | Not reproduced in the current test | The Camera image and 2D bounding-box overlay rendered successfully. The earlier experiment did not record the triggering frame, so the previous error cannot yet be isolated or confirmed as globally resolved. |
| Open3D `SetViewPoint()` warnings | Still observed | Repeated warnings were printed while the viewer was open, but they did not prevent the 3D data or 2D Camera/bounding-box views used in the verification from rendering. |

### Camera availability

The current `scene_28_1` copy contains all 11 Leopard Camera channels under:

`camera/leopard/<channel>/images`

The channels contain 259-260 images each. No empty Leopard Camera channel was found
during the current verification.

### Scope of the verification

The successful viewer check confirms that the retained `scene_28_1` data can be
used for the proposed visual and paired examples. It does not prove that every
frame in every TruckDrive mini scene is free from overlay or viewer issues.

The earlier `x1 >= x0` error should therefore remain documented as not reproduced,
rather than being reported as fully resolved.

## 6. Interpretation and limitations

The current TruckDrive evidence supports dataset characterisation and long-range
Radar investigation, but the scope of each result must remain explicit.

- Radar, annotations, calibrations and poses are available across all 24 mini scenes.
- Camera and LiDAR were retained only for selected representative scenes rather than
  the complete 24-scene mini split.
- The 6,746 returns at 150 m or greater come from 24 selected Radar frames, one from
  each mini scene. They are not a count across all 12,502 Radar frames.
- The Radar range measurements use planar range `sqrt(x^2 + y^2)`.
- The paired Radar/LiDAR evidence currently documented here is from `scene_28_1`,
  not from all 24 scenes.
- Radar return counts and paired geometric support are sensor measurements. They are
  not object-detection accuracy, precision, recall or mAP.
- No conclusion that Radar or LiDAR has better detection performance should be drawn
  from these measurements alone.
- The previous 2D overlay error was not reproduced during the latest viewer check,
  but the original triggering frame was not recorded, so it cannot be confirmed as
  globally resolved.
- Open3D `SetViewPoint()` warnings remain visible but did not block the viewer outputs
  used in the current verification.

## 7. Project records and evidence

The main source records supporting this survey are:

- `TruckDrive - Kelsey/dataset-statistics.md`
- `experiment-log/0005-kelsey-truckdrive-setup-statistics.md`
- `experiment-log/0009-fariya-truckdrive-reproduction.md`
- `results/records/0015-truckdrive-saved-evidence-reanalysis.json`
- `results/records/0018-truckdrive-long-range-paired-support.json`
- `results/records/0020-truckdrive-multiscene-long-range-support.json`
- `results/records/0025-truckdrive-class-range-support.json`
- `docs/evidence/truckdrive/paired-scene-28-1/manifest.json`
- `docs/evidence/truckdrive/paired-scene-28-1/sensor_frames.csv`
- `docs/evidence/truckdrive/paired-scene-28-1/object_counts.csv`
- `docs/evidence/truckdrive/paired-scene-28-1/example_car_200_250m.png`

## Before the PR

- [x] Dataset-wide counts have explicit scope.
- [x] The 6,746 long-range Radar returns are explicitly scoped to 24 selected frames.
- [x] The Radar distance definition is recorded.
- [x] Available and missing multimodal coverage is explicit.
- [x] Representative multimodal scenes are identified.
- [x] Paired Radar/LiDAR evidence is referenced with a sample identifier.
- [x] Paired Radar/LiDAR evidence is referenced without presenting it as detector accuracy.
- [x] Viewer dependency, Camera-channel and overlay issues are documented.
- [x] Remaining viewer warnings and limitations are explicit.
- [ ] Independent review by Fatima.