# TruckScenes LiDAR detector: go/no-go decision

25 September 2026 · EXP-0019 · result 0022

**Go — with a different candidate than originally planned.** CenterPoint,
informally flagged as the next step since EXP-0006, is a no-go on this
machine. PointPillars, checked as a direct substitute, is verified runnable:
code, checkpoint and licence all confirmed, two small preprocessing fixes
applied and tested, and a real minimal execution completed on one true
TruckScenes LiDAR sample.

This does not reopen D-04 (already answered on TruckDrive,
`docs/dataset-suitability.md` §5/§7) or TruckScenes' own recorded radar-range
limit (~189.52 m). It answers a narrower question: can a second modality run
on TruckScenes at all, for a defensible camera-vs-LiDAR comparison on the one
dataset this project has a working zero-shot camera baseline for.

## What was checked

| Candidate | Code | Checkpoint | Licence | Hardware | Minimal execution |
|---|---|---|---|---|---|
| CenterPoint (nuScenes-pretrained) | Available, mmdet3d 1.4.0 | Available (OpenMMLab model zoo) | Apache-2.0 | **No — `spconv` has no Windows wheel, CPU or CUDA** | Not attempted — blocked before this step |
| PointPillars (nuScenes-pretrained) | Available, mmdet3d 1.4.0 | Downloaded, SHA-256 verified | Apache-2.0 | **Yes — CPU, seconds per sample** | **Verified — 41 raw boxes, 11 ≥ 0.10 score, one real sample** |

## Why CenterPoint fails, precisely

Not "no CUDA" — a narrower, verified claim. CenterPoint's `SparseEncoder`
middle layer needs `spconv`. `pip install spconv` (the package PyPI labels as
the CPU build) fails outright on this machine. Checked why rather than
assumed: PyPI's release metadata for `spconv==2.3.8` lists wheels only for
`manylinux2014_x86_64` across Python 3.9–3.13 — **no Windows wheel exists for
the CPU package at all.** The CUDA variants (`spconv-cu114` etc.) would need
an NVIDIA GPU, which this machine also doesn't have (`nvidia-smi` absent,
reconfirmed). Both paths are closed, independently.

## Why PointPillars works

Its `PointPillarsScatter` middle encoder uses dense BEV pseudo-image features
and ordinary 2D convolutions — no sparse-conv dependency. Confirmed by
grepping every PointPillars base config in the installed mmdet3d for
`SparseEncoder`/`spconv`: zero matches. It uses the same nuScenes 10-class
output as FCOS3D, so the existing `NUSC_TO_TRUCKSCENES` class mapping is
directly reusable — no new mapping work.

Two adaptations were needed, both found empirically (not predicted in
advance) and both small:

1. TruckScenes' own devkit returns 4-feature points (x, y, z, intensity);
   the nuScenes loading pipeline expects a 5th zeroed "sweep time-lag"
   column even though the voxel encoder itself only consumes 4. Caught via
   a real `IndexError` on the first attempt. Fixed by zero-padding — a
   standard single-sweep convention, not a hack.
2. `inference_detector` returns a `(result, data)` tuple, unlike the
   mono-camera API used for FCOS3D. One-line unpack.

## What this minimal execution does and does not show

Shows: the candidate loads, adapted TruckScenes data reaches it in the
expected shape, and it produces a plausible box count on one real frame, on
CPU, in seconds.

Does not show: detection accuracy, a class-level score, or anything about
whether TruckScenes' domain gap (camera height, scene content — see
EXP-0016's still-open findings) also affects LiDAR. One sample, no
ground-truth comparison, by design — this is a feasibility gate, not the
benchmark.

## Fallback if a full run underperforms

PointPillars' published nuScenes score (mAP 34.33, NDS 49.1) is already
well below CenterPoint's (mAP 56.1+), so a weaker zero-shot TruckScenes
result than a CenterPoint run might have given is expected, not a surprise
to explain away. If a full 80-sample run comes back nearly zero the way
FCOS3D's single-camera run did, the same posture applies as EXP-0006/0010:
diagnose it (EXP-0016's lesson — a visibility check is not a metric-accuracy
check, so any follow-up claim needs a real numeric comparison, not a
projection check) rather than just report the number.

## Next action

1. Radar candidate feasibility check (AD-S3-1's other half of this bullet).
2. If the team wants the full result: extend this minimal execution to all
   80 `mini_val` samples and score with the devkit's evaluator, mirroring
   EXP-0010's camera methodology exactly, so the two modalities are
   comparable on the same split and metric.

## Reproduction

```text
python truckscenes_fcos3d_infer.py-style script (see experiment-log/0019)
--dataroot <man-truckscenes> --config <pointpillars nus-3d config>
--checkpoint checkpoints/pointpillars_nus_20210826_225857-f19d00a3.pth
```

Checkpoint: `checkpoints/pointpillars_nus_20210826_225857-f19d00a3.pth`
(not committed — 220MB+ model weights stay outside Git, same convention as
the FCOS3D checkpoint), SHA-256
`f19d00a38e6b775f38a45a9a3ca3ecaec20a5585a3caf44622423e2d5f75d5d0`.
