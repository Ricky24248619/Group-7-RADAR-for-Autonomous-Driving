# EXP-0024 — PointPillars (nuScenes-pretrained) zero-shot on TruckScenes, full 80-sample `mini_val`, scored

- **Date started / completed:** 2026-09-27 / 2026-10-04 (rectified rerun after PR #63 review, 3 Oct;
  all six LiDAR channels compared, 4 Oct)
- **Owner:** Aiden Blampain
- **Workstream / story:** Follow-on to AD-S3-1 (EXP-0019, `docs/truckscenes-lidar-detector-decision.md`
  "Next action" item 2) — no new story ID assigned. Produces
  `results/records/0029-truckscenes-lidar-detector-full-split.json`.

## Goal

EXP-0019 verified PointPillars loads and runs on one TruckScenes LiDAR
sample, deliberately unscored. This extends that candidate and channel to
all 80 official `mini_val` samples and scores it with the devkit's own
detection evaluator, mirroring EXP-0010's camera methodology (same split,
same evaluator invocation, same submission format) so the LiDAR result is
comparable to FCOS3D's camera result on the same split.

## Revision history

The first run (27 September) fed native `LIDAR_TOP_FRONT` points straight to
the checkpoint and scored mAP 0.0000. The PR #63 review
([`docs/pr63-input-frame-review.md`](../docs/pr63-input-frame-review.md))
found that the channel is mounted pitched about 56.23° from vertical, while
the checkpoint expects an upright LiDAR with yaw-only boxes. All 596 saved
boxes came out tilted 54.6–58.2° in world frame against upright ground
truth. This log's original claim, that a class-agnostic nearest-match check
showed "correct box-conversion geometry rather than a systematic transform
bug", was unsupported and is **withdrawn**.

The unrectified run is kept unchanged as the historical record
(`scripts/results_mini_val_pointpillars.json`, SHA-256 `4bb681c0…`, the file
the review audited, and `scripts/pointpillars_truckscenes_metrics_summary.json`).
The result this log reports is the rectified rerun below.

## Environment

Identical to EXP-0019: the `truckscenes-devkit/detection-env` venv, the
checkpoint `checkpoints/pointpillars_nus_20210826_225857-f19d00a3.pth`
(SHA-256 recorded in EXP-0019), config
`pointpillars_hv_secfpn_sbn-all_8xb4-2x_nus-3d`, and the same machine
(Ryzen 7 5700U, no NVIDIA GPU, CPU-only).

## Dataset / data subset

MAN TruckScenes `v1.2-mini`, official `mini_val` split (80 samples), the
same split EXP-0006/0010 used. The main run uses `LIDAR_TOP_FRONT`, the one
channel EXP-0019 verified. All six channels were then run separately
([channel comparison](#channel-comparison-4-october)). Merging the six into
one cloud is a different experiment and stays out of scope (see the script's
docstring).

## Input frame (the fix)

`scripts/truckscenes_pointpillars_infer.py` now moves each point cloud into
an **upright virtual LiDAR** that matches nuScenes' `LIDAR_TOP`, which the
checkpoint was trained on, before running inference:

- z is the world gravity axis, so it stays upright even when the ego pose
  is pitched or rolled on a slope;
- x/y follow the ego heading turned by nuScenes' −90° LiDAR yaw, so x points
  right and y forward;
- the origin is 1.84 m (the nuScenes LiDAR height; the checkpoint's anchors
  sit at z = −1.8) above the ground point directly below the real sensor.
  TruckScenes' ego origin is at ground level: annotated box bottoms have
  median z = 0.004 m in ego frame, and near-field `LIDAR_TOP_FRONT` ground
  returns median −0.02 m.

Predicted boxes leave through the same frame the points entered by. Only
the frame changes; no points are added or dropped. `--input-frame native`
reproduces the historical run.

**Geometry checks:**

- `tests/test_truckscenes_pointpillars_infer.py` (9 tests, CI-safe, no
  devkit or model needed) uses the real calibration quaternion. It checks
  that the virtual z axis is world-up on a slope, that the axes and ground
  height match nuScenes, that points reach global unchanged by the detour,
  that output boxes are upright with the correct heading and velocity, and
  that the native path still reproduces the reviewed 56.23° tilt.
- Rerunning with `--input-frame native` reproduced the audited historical
  file box for box: same 596 boxes and classes, every field within 2×10⁻⁶
  (float32 noise). The refactor does not change the old path.
- The reviewer's `scripts/audit_pointpillars_tilt.py` on the new
  predictions gives a world-up tilt of **0.0° (min, median and max) over
  all 1,904 boxes**, matching the ground truth's 0.0–1.2×10⁻⁶°
  ([`docs/evidence/pr63-input-frame-audit-upright.json`](../docs/evidence/pr63-input-frame-audit-upright.json)).

## Steps and commands

```bash
python scripts/truckscenes_pointpillars_infer.py \
  --dataroot <man-truckscenes> --version v1.2-mini --split mini_val \
  --config <mmdet3d>/configs/pointpillars/pointpillars_hv_secfpn_sbn-all_8xb4-2x_nus-3d.py \
  --checkpoint checkpoints/pointpillars_nus_20210826_225857-f19d00a3.pth \
  --input-frame upright --out results_mini_val_pointpillars_upright.json

python -m truckscenes.eval.detection.evaluate results_mini_val_pointpillars_upright.json \
  --dataroot <man-truckscenes> --version v1.2-mini --eval_set mini_val \
  --output_dir ./metrics_pointpillars_upright --plot_examples 0 --render_curves 0

python scripts/audit_pointpillars_tilt.py --metadata <man-truckscenes>/v1.2-mini \
  --predictions scripts/results_mini_val_pointpillars_upright.json \
  --output docs/evidence/pr63-input-frame-audit-upright.json

python scripts/pointpillars_channel_coverage.py --dataroot <man-truckscenes>
```

The historical run is the same first command with `--input-frame native`.
The channel comparison repeats the first, second and last commands with
`--channel <LIDAR_*>` for each of the other five LiDARs.

## Outcome

- [x] Success: the rectified run completed, its output frame is verified
      upright, and it was scored. "Success" says nothing about whether the
      model detected well.

| Metric | EXP-0010 (FCOS3D, 4 cameras) | EXP-0024 historical (native, tilted) | **EXP-0024 rectified (upright)** |
|---|---|---|---|
| mAP | 0.0046 | 0.0000 | **0.0067** |
| NDS | 0.0038 | 0.0000 | 0.0807 |
| mATE / mASE / mAOE | 1.0448 / 0.9849 / 1.0000 | 1.0000 / 1.0000 / 1.0000 | 0.8668 / 0.8081 / 0.8708 |
| mAVE / mAAE | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 4.7001 / 0.6803 |
| Predicted boxes (score ≥ 0.10) | 5,247 | 596 | 1,904 |
| Scored ground-truth boxes | 2,088 | 2,088 | 2,088 |

Rectified per-class AP: pedestrian **0.041**, trailer **0.022**, truck
**0.017**, and 0.000 for every other class. The unrectified run scored
exactly 0.000 for every class. Full numbers:
`scripts/pointpillars_truckscenes_metrics_summary_upright.json`.

As in EXP-0010, NDS and the TP-error metrics are shown for completeness but
not reported as validated metrics (NDS is open in `docs/metrics-definitions.md`).
The mAVE of 4.70 is inflated by the motorcycle class (AVE 34.0, with zero
AP) and should not be read as a velocity result.

## Context: what the one channel can see

The evaluator scores every ground-truth box that passes its own class-range
and point filters, and those filters count points from all six LiDARs and
the radars. The detector receives only `LIDAR_TOP_FRONT`. Using the
evaluator's own GT loading and filtering, `scripts/pointpillars_channel_coverage.py`
counts how many scored boxes hold at least one point from that channel in
the same keyframe
([`docs/evidence/pr63-channel-coverage.json`](../docs/evidence/pr63-channel-coverage.json)):

| | Scored GT boxes | With ≥1 `LIDAR_TOP_FRONT` point |
|---|---|---|
| All classes | 2,088 | **499 (23.9%)** |
| car | 926 | 117 |
| trailer | 408 | 160 |
| truck | 392 | 151 |
| traffic_sign | 166 | 9 |
| pedestrian | 132 | 58 |
| motorcycle / traffic_cone / barrier | 26 / 24 / 14 | 4 / 0 / 0 |

Boxes with channel points have a median ego distance of 18.4 m; boxes
without any have a median of 36.6 m. About three quarters of the scored
ground truth is invisible to the model's only input, which caps achievable
recall on this protocol. This is an input-coverage measure, not an
explanation of the score: at least one point is a very low bar, and the
remaining causes (domain shift from a nuScenes roof LiDAR to a forward-pitched
truck LiDAR, point density, class taxonomy) are not separated here.

## Channel comparison (4 October)

`LIDAR_TOP_FRONT` sees under a quarter of the scored objects, so the same
rectified pipeline was run on each of the other five LiDARs separately: same
80 samples, checkpoint, score threshold and evaluator, with `--channel` as
the only change. Every channel's output boxes are upright (max world-up tilt
0.0000°). The two roof corner LiDARs are also pitched (about 55°), and the
upright frame handles them the same way.

| LiDAR | Mounting | Scored GT with ≥1 point | **mAP** | NDS | Predicted boxes |
|---|---|---|---|---|---|
| **`LIDAR_LEFT`** | side, level | 1,452 (69.5%) | **0.0555** | 0.1229 | 4,196 |
| `LIDAR_RIGHT` | side, level | 1,411 (67.6%) | 0.0466 | 0.1137 | 4,099 |
| `LIDAR_TOP_LEFT` | roof, tilted ~55° | 656 (31.4%) | 0.0125 | 0.0739 | 2,411 |
| `LIDAR_TOP_RIGHT` | roof, tilted ~55° | 890 (42.6%) | 0.0107 | 0.0555 | 2,467 |
| `LIDAR_TOP_FRONT` | roof, tilted ~56° (blind-spot) | 499 (23.9%) | 0.0067 | 0.0807 | 1,904 |
| `LIDAR_REAR` | rear, level | 484 (23.2%) | 0.0057 | 0.0553 | 2,082 |

`LIDAR_LEFT` per-class AP: motorcycle 0.231, car **0.202**, traffic_cone
0.104, trailer 0.046, pedestrian 0.038, barrier 0.033, truck 0.012.
`LIDAR_RIGHT`: car **0.239**, motorcycle 0.223, trailer 0.063, pedestrian
0.025, truck 0.009. Full numbers, coverage and prediction hashes:
[`docs/evidence/pr63-channel-comparison/summary.json`](../docs/evidence/pr63-channel-comparison/summary.json).
The `LIDAR_LEFT` predictions are kept in
`scripts/results_mini_val_pointpillars_lidar_left.json`.

**Reading:**
- **Channel choice dominates.** The best single channel, `LIDAR_LEFT`
  (the devkit's own default LiDAR), scores about 8× the channel first used.
- **Score tracks coverage.** The two channels that reach about 70% of the
  scored objects score highest; the four reaching 23–43% score far lower.
  The side LiDARs also differ in being level-mounted, so coverage is not the
  only difference between rows. The ordering is evidence, not a controlled
  isolation of cause.
- **Cars are recognised when visible.** Car AP of 0.20–0.24 on the side
  LiDARs, zero-shot, compares with 0.000 on `LIDAR_TOP_FRONT`.
- **Small samples:** the motorcycle AP rests on 26 scored objects and should
  not be leaned on.
- **Still low overall:** trucks, trailers and traffic signs, most of the
  scored objects, stay near zero. Traffic signs and animals have no nuScenes
  class at all, so they can never score.

## Decision

- [ ] Retry
- [x] Change approach: same posture as EXP-0006/0010/0019's stated
      fallback. With a valid input frame and the best single channel,
      zero-shot PointPillars reaches mAP 0.0555 on TruckScenes (car AP
      about 0.2). That is a real but limited transfer, still far from the
      checkpoint's nuScenes performance. The camera+LiDAR TruckScenes
      comparison is now scored on both modalities with valid geometry
      (camera 0.0046, LiDAR 0.0555). This is consistent with the project's
      D-04 answer coming from TruckDrive.
- [ ] Stop

**Time spent:** about 20 minutes for the first (historical) run, plus about
an hour for the rectification, tests, two 80-sample reruns (native check
and upright, each under two minutes of CPU inference), evaluation and the
coverage check, plus about 30 minutes for the five-channel comparison (8
minutes of CPU time). These times are approximate.

## Next action

- If the team wants a fairer LiDAR number, the next experiment is merging
  all six TruckScenes LiDARs into the same upright virtual frame. The single
  channels already reach up to 69.5% of scored objects, and a merged cloud
  reaches at least that many, but it needs its own calibration and timing checks.
- Optionally, restrict scoring to the boxes the channel can see. That would
  be a non-standard protocol and would have to be reported as such, never
  in place of the official score above.
