# TruckScenes baseline and CPU evaluator preflight

**Date:** 5 September 2026. **Owner:** Ricky Yuen.

## Goal and scope

Resolve what can be checked before selecting a model or allocating sustained compute.
This is a source-availability review and synthetic evaluator check, not model inference
or a dataset benchmark. No sensor data, model weights, CUDA packages or training runs
are needed.

## Checkpoint review

The [dataset comparison](../docs/dataset-comparison.md#truckscenes-checkpoint-check)
records the candidate sources and their limitations. No compatible downloadable
TruckScenes detector checkpoint was verified in those sources. The official PETR
configuration names a local checkpoint path and custom dataset/metric classes; copying
that configuration does not supply their implementation or the weights. HyperDet's
checked paper describes a future release. RadarGen has a different task and uses cameras.

No model was selected, downloaded or executed. The next action is to obtain and inspect
matching code, preprocessing and weights with Aiden/Fatima, or agree a clearly labelled
transfer experiment. This availability gap is separate from pending compute access.

## CPU check

Environment: Windows, Python 3.11, separate `radar-truckscenes-review` venv. It leaves the
existing GOOSE/RADAR venv unchanged. Direct packages: `truckscenes-devkit==1.2.0`,
`numpy==1.26.4`, `matplotlib==3.8.4`, `scipy==1.13.1`. Core devkit dependencies resolved
to `pyquaternion==0.9.9`, `pypcd4==1.4.3` and `tqdm==4.70.0` during this check.

Reproduce from the repository root on a machine with Python 3.11:

```powershell
py -3.11 -m venv "$env:USERPROFILE\.venvs\radar-truckscenes-review"
$TS_PY = "$env:USERPROFILE\.venvs\radar-truckscenes-review\Scripts\python.exe"
& $TS_PY -m pip install truckscenes-devkit==1.2.0 numpy==1.26.4 matplotlib==3.8.4 scipy==1.13.1 pyquaternion==0.9.9 pypcd4==1.4.3 tqdm==4.70.0
& $TS_PY scripts/truckscenes_eval_smoke.py
```

On macOS/Linux, create the venv with `python3.11 -m venv`, then use its `bin/python`
with the same package pins and script. Execution there has not been verified by Ricky.

The check loads the official `detection_cvpr_2024` config and calls the devkit's own
`accumulate` and `calc_ap`, rather than implementing a second metric. Synthetic boxes
exercise JSON round-trip, explicit empty samples, perfect predictions, missing
predictions, a confident false positive, and the strict centre-distance boundary.

**Result: passed on Windows on 5 September 2026.** All assertions passed and
`python -m pip check` reported no broken requirements. Synthetic AP values are not
recorded as model measurements.

Limits: this does not exercise real dataset loading, calibration/transforms, class
mapping, range filtering, model inference, NDS or the full `DetectionEval` pipeline.
Those remain part of the proposed pilot. No complete benchmark or GPU-feasibility
conclusion follows from this check.
