# TruckDrive workplan

## Work completed

- Set up the official TruckDrive viewer and dataset tools on Windows.
- Verified Camera, LiDAR and Radar loading and visualisation.
- Prepared Radar, annotations, calibrations and poses for all 24 mini scenes.
- Retained Camera and LiDAR for `scene_28_1` and `scene_28_22` as representative multimodal scenes.
- Generated dataset statistics and synchronized sensor-loading checks.
- Recorded setup details, measurements and basic Camera/LiDAR/Radar evidence.

## Current status

The TruckDrive mini dataset is ready for repeatable local exploration. All 24 scenes can be used for Radar and annotation analysis, while `scene_28_1` and `scene_28_22` provide complete Camera/LiDAR/Radar examples. Dataset loading and basic characterisation are complete, but no object-detection model has been run.

## Next stage

The completed setup, statistics and sensor-loading workflow will be handed over to Fariya for the next TruckDrive stage.

The next stage will focus on:

1. Representative Camera/LiDAR/Radar visualisations.
2. Documentation of dataset structure, sensors, annotations, classes and range observations.
3. Completing `docs/dataset-surveys/truckdrive.md`.
4. Preparing presentation-ready figures.