# EXP-0007 — FCOS3D (nuScenes-pretrained) zero-shot on TruckScenes, all 4 cameras, CPU-only

- **Date started / completed:** 2026-09-12 / 2026-09-12
- **Owner:** Aiden Blampain
- **Workstream / story:** Direct follow-on to EXP-0006 (single-camera zero-shot
  run). Produces `results/records/0008-fcos3d-truckscenes-4camera.json`.

## Goal

EXP-0006 scored FCOS3D on only `CAMERA_LEFT_FRONT` as a deliberate compute
scope cut. The listed next step there was to extend coverage to all 4
TruckScenes cameras once more CPU time was available. This run does that,
using the exact same model, checkpoint, and evaluator, with no code changes
beyond letting `--cameras` default to all 4 channels.

## Environment

Identical to EXP-0006 — same `truckscenes-devkit/detection-env` venv, same
checkpoint (`fcos3d_r101_caffe_fpn_gn-head_dcn_2x8_1x_nus-mono3d_20210715_235813-4bed5239.pth`),
same machine (Ryzen 7 5700U, no NVIDIA GPU). Both were still on disk from
EXP-0006 and worked without any reinstall.

## Dataset / data subset

MAN TruckScenes `v1.2-mini`, `mini_val` split (80 samples), same as EXP-0006.
This run used all 4 camera channels (`CAMERA_LEFT_FRONT`, `CAMERA_RIGHT_FRONT`,
`CAMERA_LEFT_BACK`, `CAMERA_RIGHT_BACK`) instead of just one.

## Steps and commands

```bash
python truckscenes_fcos3d_infer.py \
  --dataroot <man-truckscenes> --version v1.2-mini --split mini_val \
  --config <fcos3d config .py> --checkpoint <fcos3d .pth> \
  --start 0 --end 2 --out results_mini_val_fcos3d_4cam.json
# ...repeated with --start/--end sliding in chunks of 4 samples across the
# full 80-sample split (2/6/10/14/.../78/80) — 4 cameras/sample takes ~4x as
# long per sample as EXP-0006's single-camera run, so chunk size was reduced
# from 15 samples (EXP-0006) to 4 to keep each call under the ~10-minute
# foreground ceiling.

python -m truckscenes.eval.detection.evaluate results_mini_val_fcos3d_4cam.json \
  --dataroot <man-truckscenes> --version v1.2-mini --eval_set mini_val \
  --output_dir ./metrics_4cam --plot_examples 0 --render_curves 0
```

## Outcome

- [x] Success — worked as intended

All 80 `mini_val` samples produced predictions across all 4 cameras
(5,247 boxes total, vs. 959 in EXP-0006's single-camera run). The evaluator
ran to completion with no errors.

| Metric | EXP-0006 (1 camera) | EXP-0007 (4 cameras) |
|---|---|---|
| mAP | 0.0000 | 0.0046 |
| NDS | 0.0000 | 0.0038 |
| mATE | 1.0000 | 1.0448 |
| mASE | 1.0000 | 0.9849 |
| mAOE / mAVE / mAAE | 1.0000 | 1.0000 |
| Predicted boxes | 959 | 5,247 (5,240 after filtering) |
| Ground-truth boxes | 2,088 | 2,088 (unchanged — same split) |

Per-class AP is effectively zero everywhere except `traffic_cone` (0.051)
and small nonzero slivers on `truck` (0.001), `pedestrian` (0.002), and
`motorcycle` (0.001) — every other class (car, bus, trailer, other_vehicle,
bicycle, barrier, animal, traffic_sign) is exactly 0.000, same as EXP-0006.

**This does not overturn EXP-0006's domain-gap finding — it reinforces it.**
Extending to 4 cameras did not recover meaningful detection performance;
mAP moved from 0.0000 to 0.0046, i.e. still effectively zero. The
`traffic_cone` AP is the one new data point worth flagging rather than
explaining away: it is plausible that cones are typically annotated at
closer range than vehicles, where FCOS3D's depth error (which EXP-0006
showed scales with range) would matter less. **This is a hypothesis, not a
verified finding** — unlike EXP-0006, this run did not repeat the
nearest-prediction-to-ground-truth distance analysis broken down by class
and range, so the cause of the `traffic_cone` signal is not diagnosed here.
That would be the natural next check before reading anything into it.

## Attempted fixes

One new issue, distinct from EXP-0006's list:

1. **Explicit `run_in_background` was unreliable**, reproducing EXP-0006's
   finding #8 exactly: a chunk launched with `run_in_background: true` was
   silently killed rather than completing, with no error and no partial
   checkpoint (chunk size was 4 samples, and the script only checkpoints at
   the end of a chunk, so nothing was lost — the results file was simply
   unchanged at the pre-chunk sample count). Fix: reverted to the same
   sequential **foreground** calls EXP-0006 settled on. One chunk still
   exceeded the tool's 600s ceiling and was auto-moved to background by the
   harness itself (not requested) — that one *did* complete and checkpoint
   correctly, suggesting the failure mode is specific to explicitly
   requesting background execution up front, not to long-running calls in
   general.

## Decision

- [ ] Retry
- [x] Change approach — camera coverage is no longer the limiting factor;
      the sensible next step is the LiDAR path (CenterPoint), which doesn't
      share FCOS3D's depth-estimation failure mode and was the paper's
      strongest baseline. That still needs a machine with an NVIDIA GPU
      (blocked on this one, same as EXP-0006).
- [ ] Stop

**Time spent:** approximately 1.5 hours, almost entirely CPU inference wall
time (environment and checkpoint were already set up from EXP-0006).

## Next action

Optionally repeat EXP-0006's nearest-match distance diagnostic on this run's
predictions, broken down by class, to check whether the `traffic_cone`
signal is genuinely a near-range effect or noise from a small sample count.
Otherwise, same as EXP-0006: bring this as reinforcing evidence for D-04 and
pursue the GPU-based LiDAR CenterPoint path next.
