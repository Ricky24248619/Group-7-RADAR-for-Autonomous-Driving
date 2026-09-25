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
- Investigated the low score using reference box conversions and prediction-to-
  ground-truth distances. Domain shift remains a hypothesis; those diagnostics
  do not exclude coordinate or preprocessing errors.
- Re-ran the same model against all 4 TruckScenes cameras (EXP-0010), to
  check whether single-camera coverage was hiding a better result.
- Audited metadata channel coverage and image-frustum visibility (EXP-0016,
  AD-S3-1). Added ground-truth overlays and recorded per-camera outcomes for
  a four-sample rerun. These checks do not establish metric box accuracy.
- Checked LiDAR detector feasibility on TruckScenes (EXP-0019, AD-S3-1).
  CenterPoint is a no-go on this machine (`spconv` has no Windows wheel,
  CPU or CUDA). PointPillars is a verified go: real minimal execution on
  one TruckScenes LiDAR sample, zero-shot, CPU, after two documented
  preprocessing fixes. Not scored -- see the decision note for scope.

## Outcome

TruckScenes devkit and dataset setup worked correctly on the first attempt
(EXP-0004). The first real detection result (EXP-0006, single camera) came
back at:

- mAP: 0.0000 across all 12 detection classes
- 959 predicted boxes vs. 2,088 ground-truth boxes, front-left camera only
- Nearest-match errors of 5-21m, scaling with range

Extending to all 4 cameras (EXP-0010) reinforced rather than overturned this:

- mAP: 0.0046 (still effectively zero), NDS: 0.0038
- 5,247 predicted boxes vs. the same 2,088 ground-truth boxes
- Every vehicle/pedestrian/cyclist class still scores ~0.000-0.002 AP; the
  one exception is `traffic_cone` at 0.051 — flagged as an open question
  (possibly a near-range effect), not yet diagnosed the way the single-camera
  zero was

EXP-0016 found four camera-channel metadata entries for every sample and
source-camera visibility for all 247 tagged boxes in a four-sample rerun.
Thirteen of the 16 rerun calls produced above-threshold boxes. This does not
verify every original inference call or establish metric coordinate accuracy:
doubling camera-relative distance and box dimensions still passed 247/247 in
a review counterexample. Camera height/pitch, scene-domain differences and
preprocessing remain unresolved possible causes of the low score. A controlled
numerical/experimental check is needed before attributing the result to one cause.

## Sample data

Full dataset statistics (table row counts, sensor suite, split sizes) are in
[`dataset-statistics.md`](dataset-statistics.md). The detection runs' methods,
obstacles hit, and full reasoning are in
[`experiment-log/0006-fcos3d-truckscenes-zeroshot.md`](../experiment-log/0006-fcos3d-truckscenes-zeroshot.md)
(single camera) and
[`experiment-log/0010-fcos3d-truckscenes-4camera.md`](../experiment-log/0010-fcos3d-truckscenes-4camera.md)
(all 4 cameras). The independent audit's method and full numbers are in
[`experiment-log/0016-fcos3d-4camera-result-audit.md`](../experiment-log/0016-fcos3d-4camera-result-audit.md),
with visual overlays in `scripts/audit_fcos3d_4camera/overlays/`.

## Current limits

- No LiDAR or radar detection model has been run. This machine has no
  NVIDIA GPU, and the strongest published baseline (LiDAR CenterPoint) needs
  `spconv`, which has no practical CPU path.
- The `traffic_cone` AP signal from EXP-0010 hasn't been diagnosed with the
  same rigor as the single-camera zero (no per-class distance analysis yet)
  — worth a quick follow-up before reading anything into it.
- EXP-0016 checks visibility, not metric coordinate correctness. Transform,
  preprocessing, height and scene-domain causes remain unresolved.
- NDS and the TP-error metrics (mATE, mASE, mAOE, mAVE, mAAE) came out of
  the same evaluator run but are not reported as validated metrics here,
  because NDS is an explicitly open question in `docs/metrics-definitions.md`
  (assigned to Ricky) and the TP-error metrics aren't defined there yet.
- The shared survey is available at `docs/dataset-surveys/truckscenes.md`;
  coordinate updates with its contributors.

## Next stage

- AD-S3-1's remaining work: a radar detector feasibility check (LiDAR side
  done — EXP-0019, `docs/truckscenes-lidar-detector-decision.md`), then a
  combined go/no-go note covering both modalities.
- If the team wants the full LiDAR result: extend EXP-0019's minimal
  execution to all 80 `mini_val` samples, scored with the devkit's
  evaluator, mirroring EXP-0010's camera methodology.
- Optionally re-run EXP-0006's nearest-match distance diagnostic on
  EXP-0010's predictions, broken down by class, to check whether the
  `traffic_cone` AP is a genuine near-range effect or noise.
- A controlled check to separate camera-height from scene-domain as the
  cause of the low score (EXP-0016 could not, and deliberately did not
  claim to).
- Try the LiDAR path (CenterPoint, also nuScenes-pretrained) on a machine
  with an NVIDIA GPU — it doesn't share FCOS3D's depth-estimation failure
  mode and was the paper's strongest baseline.
- Keep the shared TruckScenes survey aligned with verified results.
