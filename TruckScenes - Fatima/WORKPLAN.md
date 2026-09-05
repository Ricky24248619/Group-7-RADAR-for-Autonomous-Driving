# MAN TruckScenes workplan

## Work completed

- Downloaded and checked the `v1.2-mini` data outside the repository.
- Installed the official devkit in an isolated Python environment.
- Loaded metadata and inspected sensor and annotation tables.
- Generated paired RADAR/LiDAR visualisations for all 10 mini scenes.
- Recorded measured statistics, setup details, limitations and test coverage.

## Current status

The local data pipeline is ready for repeatable exploration on macOS. Scripts accept a command-line dataset path or the `TRUCKSCENES_ROOT` environment variable, so no personal path is stored in the repository. Dataset characterisation and devkit feasibility have been recorded, but model inference has not started.

## Next technical steps

1. Review the current survey, measurements and representative images.
2. Identify one compatible pretrained TruckScenes 3D-detection baseline.
3. Confirm its sensor inputs, checkpoint availability, licence and hardware requirements.
4. Run a small, fixed inference feasibility test.
5. If successful, define a controlled evaluation by range band and record the appropriate detection metrics.
6. If it cannot run, document the attempted configuration and failure as a project result.
