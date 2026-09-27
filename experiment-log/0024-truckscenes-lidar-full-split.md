# EXP-0024 — PointPillars (nuScenes-pretrained) zero-shot on TruckScenes, full 80-sample `mini_val`, scored

- **Date started / completed:** 2026-09-27 / 2026-09-27
- **Owner:** Aiden Blampain
- **Workstream / story:** Follow-on to AD-S3-1 (EXP-0019, `docs/truckscenes-lidar-detector-decision.md`
  "Next action" item 2) — no new story ID assigned. Produces
  `results/records/0029-truckscenes-lidar-detector-full-split.json`.

## Goal

EXP-0019 verified PointPillars loads and runs on one TruckScenes LiDAR
sample, deliberately unscored. This extends that exact candidate,
preprocessing and channel to all 80 official `mini_val` samples and scores
it with the devkit's own detection evaluator, mirroring EXP-0010's camera
methodology (same split, same evaluator invocation, same submission format)
so the LiDAR result is comparable to FCOS3D's camera result on the same
split.

## Environment

Identical to EXP-0019 — same `truckscenes-devkit/detection-env` venv, same
checkpoint (`checkpoints/pointpillars_nus_20210826_225857-f19d00a3.pth`,
SHA-256 `f19d00a3...` as recorded in EXP-0019), same machine (Ryzen 7 5700U,
no NVIDIA GPU, CPU-only).

## Dataset / data subset

MAN TruckScenes `v1.2-mini`, official `mini_val` split (80 samples), same
split EXP-0006/0010 used. Single channel: `LIDAR_TOP_FRONT` — the one
channel EXP-0019 verified feasible. TruckScenes splits LiDAR sensing across
six physically separate units (unlike nuScenes' single roof-mounted LiDAR
this checkpoint was trained against); merging multiple TruckScenes channels
into one cloud is a materially different, unverified experiment and stayed
out of scope here — see `scripts/truckscenes_pointpillars_infer.py`'s
docstring for why.

## Steps and commands

```bash
python scripts/truckscenes_pointpillars_infer.py \
  --dataroot <man-truckscenes> --version v1.2-mini --split mini_val \
  --config <pointpillars nus-3d config .py> \
  --checkpoint checkpoints/pointpillars_nus_20210826_225857-f19d00a3.pth \
  --start 0 --end 10 --out results_mini_val_pointpillars.json
# ...repeated with --start 10 --end 80 for the remainder — single-LiDAR-
# channel inference is much faster than 4-camera FCOS3D (~0.7s/sample vs.
# tens of seconds), so this fit in two chunks instead of EXP-0010's ~20.

python -m truckscenes.eval.detection.evaluate results_mini_val_pointpillars.json \
  --dataroot <man-truckscenes> --version v1.2-mini --eval_set mini_val \
  --output_dir ./metrics_pointpillars --plot_examples 0 --render_curves 0
```

## Outcome

- [x] Success — worked as intended (as a scored run: it completed, produced
      a trustworthy measurement, and is diagnosed below — "success" says
      nothing about whether the model detected well)

All 80 `mini_val` samples produced predictions on the one channel used
(596 boxes total). The evaluator ran to completion with no errors.

| Metric | EXP-0010 (FCOS3D, 4 cameras) | EXP-0024 (PointPillars, 1 LiDAR channel) |
|---|---|---|
| mAP | 0.0046 | **0.0000** |
| NDS | 0.0038 | 0.0000 |
| mATE / mASE / mAOE / mAVE / mAAE | 1.0448 / 0.9849 / 1.0000 / 1.0000 / 1.0000 | 1.0000 / 1.0000 / 1.0000 / 1.0000 / 1.0000 |
| Predicted boxes | 5,247 | 596 |
| Ground-truth boxes (after filtering) | 2,088 | 2,088 |

Per-class AP is exactly 0.000 for **every** class, with no exception —
unlike EXP-0010, which had a nonzero `traffic_cone` AP (0.051). Full numbers:
`scripts/pointpillars_truckscenes_metrics_summary.json`.

## Diagnostic: is this a coordinate bug or a genuine zero-shot miss?

Following EXP-0006's precedent (don't just report a zero, diagnose it),
computed nearest-match distance from every predicted box centre to the
nearest ground-truth box centre in the same sample, across all 80 samples,
596 predicted boxes:

| | min | median | p90 | max | mean |
|---|---|---|---|---|---|
| Nearest-match distance (m) | 0.41 | 8.74 | 22.68 | 42.62 | 10.61 |

This is a **different error profile than EXP-0006's camera result**, which
found errors scaling smoothly with range (5–21m, the signature of a
monocular depth bias). Here the spread is wide and bimodal-looking: some
predictions land within half a metre of a real object (0.41m minimum), but
the median (8.74m) is still well beyond the evaluator's largest 4m matching
threshold. This is consistent with the box-conversion geometry being
correct (translations and sizes for individual boxes are plausible and in
the right neighbourhood — spot-checked against ground truth for two
samples), rather than a systematic global transform bug, which would push
every match far off, not just most of them.

**Not diagnosed here, and worth flagging as a real gap**: this distance
check ignores predicted class. A close match with the wrong
`detection_name` still scores zero AP under the evaluator's class-matched
protocol, and this run did not check how many of the close matches (near
the 0.41m end) also have the correct class. That per-class match analysis
is the natural next step before treating "some boxes are well-localised" as
more than a hint.

## Decision

- [ ] Retry
- [x] Change approach — same posture as EXP-0006/0010/0019's stated
      fallback: a zero score from zero-shot cross-dataset transfer is
      itself informative, not a failure to fix. PointPillars zero-shot on
      TruckScenes LiDAR does not recover meaningful detection performance,
      consistent with (not contradicting) the project's D-04 answer already
      being sourced from TruckDrive.
- [ ] Stop

**Time spent:** approximately 20 minutes elapsed tool time (inference: two
chunks, ~20s + ~52s; evaluator: <1s; diagnostic distance check: a few
minutes) — much faster than EXP-0010's 1.5 hours, since one LiDAR channel
on 80 samples is far cheaper than 4 camera images on 80 samples.

## Next action

The per-class match analysis flagged above (does a close-distance match
also have the correct predicted class?) is the natural follow-up before
reading anything further into the 0.41m minimum. Otherwise, this closes out
`docs/truckscenes-lidar-detector-decision.md`'s "next action" item 2 — the
project's TruckScenes camera+LiDAR comparison (per
`docs/ad-s3-1-detector-feasibility-summary.md`) is now fully scored on both
modalities, both zero-shot, both effectively zero mAP, both diagnosed rather
than just reported.
