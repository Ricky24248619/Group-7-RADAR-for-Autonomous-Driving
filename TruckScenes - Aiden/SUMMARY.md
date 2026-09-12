# TruckScenes exploration summary

## Completed

- Set up and validated the official `truckscenes-devkit` (1.2.0) on Windows,
  independently of the dataset, confirming the two install correctly against
  each other.
- Verified the `v1.2-mini` dataset structure and ran the official tutorial
  notebook end to end with zero errors.
- Built a second, separate CPU-only venv (`detection-env`) capable of running
  an actual open-source 3D detector (`mmdet3d`) — not just the devkit's own
  data-loading tutorial.
- Ran a pretrained (nuScenes-trained) FCOS3D monocular detector zero-shot
  against all 80 `mini_val` samples, and scored it with the devkit's own
  detection evaluator.
- Diagnosed the result rather than just reporting the number: confirmed a
  real domain-gap finding, not a coordinate-transform bug, by reusing
  mmdet3d's own reference box-conversion math and checking prediction-to-
  ground-truth distances directly.
- Re-ran the same model against all 4 TruckScenes cameras (EXP-0007), to
  check whether single-camera coverage was hiding a better result.

## Outcome

TruckScenes devkit and dataset setup worked correctly on the first attempt
(EXP-0004). The first real detection result (EXP-0006, single camera) came
back at:

- mAP: 0.0000 across all 12 detection classes
- 959 predicted boxes vs. 2,088 ground-truth boxes, front-left camera only
- Nearest-match errors of 5-21m, scaling with range

Extending to all 4 cameras (EXP-0007) reinforced rather than overturned this:

- mAP: 0.0046 (still effectively zero), NDS: 0.0038
- 5,247 predicted boxes vs. the same 2,088 ground-truth boxes
- Every vehicle/pedestrian/cyclist class still scores ~0.000-0.002 AP; the
  one exception is `traffic_cone` at 0.051 — flagged as an open question
  (possibly a near-range effect), not yet diagnosed the way the single-camera
  zero was

This is real evidence of camera-height domain gap — TruckScenes' cameras sit
at ~2.1m vs. nuScenes' ~1.5m car-mounted cameras — directly relevant to the
project's D-04 range-degradation question, and a legitimate first data point
even though the number is (still, essentially) zero.

## Sample data

Full dataset statistics (table row counts, sensor suite, split sizes) are in
[`dataset-statistics.md`](dataset-statistics.md). The detection runs' methods,
obstacles hit, and full reasoning are in
[`experiment-log/0006-fcos3d-truckscenes-zeroshot.md`](../experiment-log/0006-fcos3d-truckscenes-zeroshot.md)
(single camera) and
[`experiment-log/0007-fcos3d-truckscenes-4camera.md`](../experiment-log/0007-fcos3d-truckscenes-4camera.md)
(all 4 cameras).

## Current limits

- No LiDAR or radar detection model has been run. This machine has no
  NVIDIA GPU, and the strongest published baseline (LiDAR CenterPoint) needs
  `spconv`, which has no practical CPU path.
- The `traffic_cone` AP signal from EXP-0007 hasn't been diagnosed with the
  same rigor as the single-camera zero (no per-class distance analysis yet)
  — worth a quick follow-up before reading anything into it.
- NDS and the TP-error metrics (mATE, mASE, mAOE, mAVE, mAAE) came out of
  the same evaluator run but are not reported as validated metrics here,
  because NDS is an explicitly open question in `docs/metrics-definitions.md`
  (assigned to Ricky) and the TP-error metrics aren't defined there yet.
- No `docs/dataset-surveys/truckscenes.md` has been written — dataset
  exploration sits under Kelsey's epic (D), so that survey should be
  coordinated with her rather than started solo from this folder.

## Next stage

- Optionally re-run EXP-0006's nearest-match distance diagnostic on
  EXP-0007's predictions, broken down by class, to check whether the
  `traffic_cone` AP is a genuine near-range effect or noise.
- Try the LiDAR path (CenterPoint, also nuScenes-pretrained) on a machine
  with an NVIDIA GPU — it doesn't share FCOS3D's depth-estimation failure
  mode and was the paper's strongest baseline.
- Confirm with Kelsey whether `docs/dataset-surveys/truckscenes.md` should
  follow from this work.
