# TruckScenes workplan

**Status reconciled with the recorded review on 11 September 2026.**

## Work completed

- Installed and verified `truckscenes-devkit` and the `v1.2-mini` dataset
  independently on Windows; ran the official tutorial notebook end to end.
- Built a dedicated CPU-only detection environment (`detection-env`) able to
  run `mmdet3d`, separate from the devkit's own tutorial venv.
- Recorded a pretrained FCOS3D camera-only zero-shot submission containing all
  80 `mini_val` sample tokens. The saved evaluator reports mAP 0.0.
- The submission has 959 boxes in 63 nonempty entries. Completion logs are needed
  for its 17 empty entries because the runner pre-fills them. The author's reported
  80-sample inference has not been independently verified.
- Camera-height/domain shift is a hypothesis. Reference conversion code alone
  does not rule out calibration or integration errors, and an aggregate zero does
  not establish range degradation.
- The scored submission and review limitations are in
  [EXP-0006](../experiment-log/0006-fcos3d-truckscenes-zeroshot.md) and
  [result 0007](../results/records/0007-fcos3d-truckscenes-zeroshot.json).
  Aiden's earlier Windows tutorial log was in closed, unmerged PR #20;
  Fatima's separate mini exploration is now [EXP-0007](../experiment-log/0007-fatima-truckscenes-setup-visualisation.md).

## Current status

TruckScenes devkit and dataset setup is confirmed working on Windows with no
GPU. A scored camera-only submission exists; its zero-score cause and complete
inference coverage remain unresolved. No LiDAR or radar model run is recorded here,
so no matched sensor comparison or range-degradation conclusion is established.

## Next stage

1. Use the saved predictions, input images, calibration and chunk logs to verify
   completion and known geometry. Record what remains unknown; expanding camera
   coverage is a later experiment, after these checks.
2. With Fatima and Ricky, select one usable radar or LiDAR detector and verify its
   checkpoint, training data, preprocessing, labels and compute requirements.
   A nuScenes-pretrained CenterPoint candidate would be a transfer experiment;
   its name alone does not establish TruckScenes compatibility.
3. Follow the existing [comparison protocol](../docs/dataset-comparison.md):
   fix samples, annotations and evaluator before a bounded feasibility check.
   Stock TruckScenes class ranges stop at 75 or 150 m; a >150 m score needs a
   separate agreed evaluation protocol.
4. Update the already merged [survey](../docs/dataset-surveys/truckscenes.md)
   with verified results. NDS and TP errors are now defined in
   [metrics definitions](../docs/metrics-definitions.md); retain no-match and
   protocol caveats when interpreting the saved output.
