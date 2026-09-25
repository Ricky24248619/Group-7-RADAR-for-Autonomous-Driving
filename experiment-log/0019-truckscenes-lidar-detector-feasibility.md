# EXP-0019 — TruckScenes LiDAR detector feasibility (AD-S3-1, bullet 2, LiDAR candidate)

- **Date started / completed:** 2026-09-25 / 2026-09-25
- **Owner:** Aiden Blampain
- **Workstream / story:** AD-S3-1 ("Camera-result audit and detector
  feasibility"), acceptance bullet 2 — LiDAR half. Produces
  `results/records/0022-truckscenes-lidar-detector-feasibility.json`.

## Goal

Time-boxed (≤2 hr) feasibility check for one LiDAR detector candidate on
TruckScenes: verify released code, checkpoint, licence, preprocessing, class
mapping, hardware and a minimal execution path. Not a scored benchmark —
EXP-0006/0010/0016 already established that this project's answer to D-04
(range degradation) now comes from TruckDrive (`docs/dataset-suitability.md`
§5, §7), and TruckScenes' own recorded radar stops at ~189.52 m, so nothing
here reopens that question. This checks whether a second modality is
runnable on TruckScenes at all, for camera/LiDAR/radar comparability on the
one dataset this project has a working zero-shot camera baseline for.

## Candidates checked

**CenterPoint** (nuScenes-pretrained, informally flagged as the next step
since EXP-0006) was the starting candidate — but its `SparseEncoder` middle
layer requires `spconv` for 3D sparse convolution, and that dependency
**cannot be installed on this machine at all**, for a more specific reason
than "no CUDA":

- `pip install spconv` (the CPU-labelled PyPI package) fails outright here.
- Checked why: PyPI's release metadata for `spconv==2.3.8` lists wheels only
  for `manylinux2014_x86_64` (Python 3.9–3.13) — **no Windows wheel exists
  for the CPU package at all.** This is a platform gap, not a missing-CUDA
  gap; even the "CPU" build isn't distributed for Windows.
- The CUDA variants (`spconv-cu114` etc.) need an NVIDIA GPU, which this
  machine doesn't have (`nvidia-smi` absent, reconfirmed today, consistent
  with every prior experiment on this hardware).

CenterPoint is a **no-go on this machine**, full stop — not a compute-time
problem, a package-availability one. See Decision below for the fallback
this ruled in.

**PointPillars** (`pointpillars_hv_secfpn_sbn-all_8xb4-2x_nus-3d`,
nuScenes-pretrained) was checked next, specifically because its
`PointPillarsScatter` middle encoder uses dense BEV pseudo-image features
and standard 2D convolutions — no `spconv` dependency at all. Confirmed by
`grep`-ing every PointPillars base config in the installed mmdet3d for
`SparseEncoder`/`spconv`: zero matches.

## Verification checklist

| Check | Result |
|---|---|
| Released code | mmdet3d 1.4.0, config already present locally (`configs/pointpillars/pointpillars_hv_secfpn_sbn-all_8xb4-2x_nus-3d.py`) |
| Checkpoint | Official nuScenes-pretrained weights, downloaded successfully (19,778,089 bytes), SHA-256 `f19d00a38e6b775f38a45a9a3ca3ecaec20a5585a3caf44622423e2d5f75d5d0`. Published mAP 34.33, NDS 49.1 on nuScenes |
| Licence | Apache-2.0 (mmdetection3d repository licence; no separate checkpoint-specific licence statement found in the model zoo docs — same as the licence already relied on for the FCOS3D checkpoint) |
| Preprocessing | Two real, documented adaptations needed (below) — not a blocker, a fix |
| Class mapping | Same nuScenes 10-class output as FCOS3D. The existing `NUSC_TO_TRUCKSCENES` mapping (`scripts/truckscenes_fcos3d_infer.py`) is directly reusable, no new mapping work needed |
| Hardware | CPU-only, confirmed feasible — completed in a few seconds on one sample |
| Minimal execution path | **Verified working** — see below |

## Preprocessing adaptations found (and fixed)

1. **Point feature count.** TruckScenes' own devkit (`LidarPointCloud.from_file()`)
   returns 4 raw features per point (x, y, z, intensity) from its `.pcd`
   files. The PointPillars nuScenes data-loading pipeline (not just the
   voxel encoder, which only lists `in_channels=4`) expects a 5th column —
   confirmed empirically: the first attempt raised
   `IndexError: index 4 is out of bounds for dimension 1 with size 4` inside
   mmdet3d's `LoadPointsFromDict` transform, which unconditionally zeroes
   column 4 as a per-point "sweep time-lag" marker (nuScenes' convention for
   multi-sweep temporal aggregation). Fix: pad a 5th column of zeros,
   marking every point as the current single sweep — a standard, documented
   adaptation for zero-shot single-sweep inference, not a workaround that
   changes the model's semantics.
2. **`inference_detector` return type.** Unlike
   `inference_mono_3d_detector` (used for FCOS3D, which returns a bare
   result for single images — see EXP-0006 attempted-fix #6), the LiDAR-only
   `inference_detector` returns a `(result, data)` tuple. One-line unpack.

## Minimal execution path — result

Ran zero-shot, CPU-only, on one real TruckScenes sample (`LIDAR_TOP_FRONT`,
scene index 0, 17,180 points, x∈[-13.5, 20.6] y∈[-48.1, 80.8] z∈[-7.4, 24.1]):

```
Model loaded OK. Running inference on one real sample ...
Inference completed. Raw output: 41 boxes (before score threshold).
  score range: [0.0507, 0.3530]
  boxes >= 0.10 score: 11
MINIMAL EXECUTION PATH: SUCCESS
```

This is deliberately **not** a scored result — one sample, no ground-truth
comparison, no class breakdown. It establishes only that the model loads,
the (adapted) TruckScenes data reaches it in the shape it expects, and it
produces a plausible-looking box count on a real frame, in seconds, on this
machine's CPU.

## Outcome

- [x] Success — worked as intended (as a feasibility check: one candidate
      ruled definitively out with a precise cause, a second candidate
      verified runnable end-to-end)

## Decision

- [x] Change approach — CenterPoint is a documented no-go on this hardware
      (Windows + no NVIDIA GPU: `spconv` has no viable install path either
      way). PointPillars is the actual feasible LiDAR candidate for a
      TruckScenes camera-vs-LiDAR comparison, with two small, documented
      preprocessing fixes already applied and verified.
- [ ] Retry
- [ ] Stop

**Fallback if PointPillars' published nuScenes score (mAP 34.33) turns out
too weak zero-shot on TruckScenes to be worth reporting**: same posture as
EXP-0006/0010 — a low or zero score from a zero-shot cross-dataset transfer
is itself informative, provided it's diagnosed rather than just reported,
following the same round-trip/visibility auditing lesson from EXP-0016
(don't claim more than a check actually establishes).

**Time spent:** approximately 2 hours (spconv investigation and CenterPoint
ruling-out, PointPillars config/checkpoint verification, two debugging
iterations to a working minimal execution).

## Next action

Radar candidate feasibility check (AD-S3-1's other half of bullet 2), then
the combined go/no-go note (bullet 3) covering both modalities. Full 80-sample
PointPillars inference + evaluator scoring (mirroring EXP-0010's camera
methodology) is a natural follow-on but is explicitly out of scope for this
feasibility bullet.
