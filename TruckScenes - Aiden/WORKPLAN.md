# TruckScenes workplan

## Work completed

- Installed and verified `truckscenes-devkit` and the `v1.2-mini` dataset
  independently on Windows; ran the official tutorial notebook end to end.
- Built a dedicated CPU-only detection environment (`detection-env`) able to
  run `mmdet3d`, separate from the devkit's own tutorial venv.
- Ran a pretrained FCOS3D monocular detector zero-shot against all 80
  `mini_val` samples (front-left camera) and scored it with the devkit's
  detection evaluator.
- Diagnosed the mAP 0.0 result as a genuine camera-height domain-gap finding
  rather than a pipeline bug, by reusing mmdet3d's own reference box-scoring
  math and checking prediction-to-ground-truth distances directly.
- Recorded both stages properly: `experiment-log/0004` (setup),
  `experiment-log/0006` (detection run), and
  `results/records/0007-fcos3d-truckscenes-zeroshot.json` (validated against
  `scripts/validate_result.py`).

## Current status

TruckScenes devkit and dataset setup is confirmed working on Windows with no
GPU. A first real, diagnosed detection result exists (zero-shot camera-only
FCOS3D, mAP 0.0), reusable as evidence for the project's range-degradation
question. No LiDAR or radar model has been run yet — this machine cannot run
the paper's LiDAR baseline (needs a CUDA GPU for `spconv`).

## Next stage

1. Extend the FCOS3D run to all 4 cameras once more CPU time, or a GPU, is
   available (single-camera coverage was a deliberate compute scope cut, not
   a limitation of the approach).
2. Run the LiDAR path (CenterPoint, also nuScenes-pretrained) on a machine
   with an NVIDIA GPU — the paper's strongest baseline, and not subject to
   FCOS3D's depth-estimation domain-gap failure mode.
3. Coordinate with Kelsey (Epic D — dataset exploration) before starting
   `docs/dataset-surveys/truckscenes.md`, since this folder's statistics
   would feed directly into it.
4. Once NDS and the TP-error metrics are resolved in
   `docs/metrics-definitions.md` (Ricky, open question), re-report the full
   evaluator output rather than mAP alone.
