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

## Outcome

TruckScenes devkit and dataset setup worked correctly on the first attempt
(EXP-0004). The first real detection result (EXP-0006) came back at:

- mAP: 0.0000 across all 12 detection classes
- 959 predicted boxes vs. 2,088 ground-truth boxes, front-left camera only
- Nearest-match errors of 5-21m, scaling with range

This is real evidence of camera-height domain gap — TruckScenes' cameras sit
at ~2.1m vs. nuScenes' ~1.5m car-mounted cameras — directly relevant to the
project's D-04 range-degradation question, and a legitimate first data point
even though the number is zero.

## Sample data

Full dataset statistics (table row counts, sensor suite, split sizes) are in
[`dataset-statistics.md`](dataset-statistics.md). The detection run's method,
obstacles hit, and full reasoning are in
[`experiment-log/0006-fcos3d-truckscenes-zeroshot.md`](../experiment-log/0006-fcos3d-truckscenes-zeroshot.md).

## Current limits

- Only one of TruckScenes' four cameras was used for the detection run
  (CPU-only inference is slow — ~28s/image on this hardware). All 80
  `mini_val` samples were still scored; this costs recall, not coverage.
- No LiDAR or radar detection model has been run. This machine has no
  NVIDIA GPU, and the strongest published baseline (LiDAR CenterPoint) needs
  `spconv`, which has no practical CPU path.
- NDS and the TP-error metrics (mATE, mASE, mAOE, mAVE, mAAE) came out of
  the same evaluator run but are not reported as validated metrics here,
  because NDS is an explicitly open question in `docs/metrics-definitions.md`
  (assigned to Ricky) and the TP-error metrics aren't defined there yet.
- No `docs/dataset-surveys/truckscenes.md` has been written — dataset
  exploration sits under Kelsey's epic (D), so that survey should be
  coordinated with her rather than started solo from this folder.

## Next stage

- Extend camera coverage to all 4 cameras once more CPU time (or a GPU) is
  available.
- Try the LiDAR path (CenterPoint, also nuScenes-pretrained) on a machine
  with an NVIDIA GPU — it doesn't share FCOS3D's depth-estimation failure
  mode and was the paper's strongest baseline.
- Confirm with Kelsey whether `docs/dataset-surveys/truckscenes.md` should
  follow from this work.
