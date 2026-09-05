# TruckDrive exploration summary

## Completed

- Set up and validated the official TruckDrive viewer on Windows.
- Verified Camera, LiDAR and Radar loading and visualisation.
- Prepared Radar, annotations, calibrations and poses for all 24 mini scenes.
- Retained Camera and LiDAR for `scene_28_1` and `scene_28_22`.
- Generated dataset-wide statistics and synchronized sensor-loading checks.
- Added basic Camera, LiDAR and Radar evidence.

## Outcome

TruckDrive data loading and basic dataset exploration worked successfully.

Across the 24 mini scenes, the local statistics measured:

- 12,502 Radar frames
- 4,800 bounding-box annotation frames
- 480 lane-line annotation frames
- 526,148 3D bounding boxes
- 27 object classes

One annotated Radar frame was selected from each scene for range analysis. Across these 24 selected frames, 6,746 Radar detections were measured at 150 m or greater.

`scene_28_22` was selected as an additional representative multimodal scene because its selected Radar frame contained the highest number of 150 m+ detections among the 24 scene samples.

## Sample visualisations

Basic Camera, LiDAR and Radar evidence from `scene_28_1` is stored in:

- `docs/evidence/truckdrive-kelsey/scene28_1_camera.png`
- `docs/evidence/truckdrive-kelsey/scene28_1_lidar.png`
- `docs/evidence/truckdrive-kelsey/scene28_1_radar.png`

These images demonstrate successful dataset loading and sensor visualisation.

## Current limits

The complete mini split was not downloaded with every modality because it is approximately 282.71 GB compressed. Camera and LiDAR were retained only for selected representative scenes.

No object-detection model has been run. Radar return counts and long-range measurements are therefore not measures of detection accuracy, precision, recall or mAP.

## Next stage

The completed setup, statistics and sensor-loading workflow can now be used by Fariya for TruckDrive visualisation, dataset documentation and the final dataset survey.