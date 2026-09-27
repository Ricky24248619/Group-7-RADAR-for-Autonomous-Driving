# EXP-0020 — TruckScenes radar detector feasibility (AD-S3-1, bullet 2, radar candidate)

- **Date started / completed:** 2026-09-25 / 2026-09-25
- **Owner:** Aiden Blampain
- **Workstream / story:** AD-S3-1 ("Camera-result audit and detector
  feasibility"), acceptance bullet 2 — radar half. Produces
  `results/records/0023-truckscenes-radar-detector-feasibility.json`.

## Goal

Same scope as EXP-0019 (LiDAR half): time-boxed feasibility check for one
radar detector candidate on TruckScenes — code, checkpoint, licence,
preprocessing, class mapping, hardware, minimal execution path. Same caveat
applies: this does not reopen D-04 (answered on TruckDrive) or TruckScenes'
recorded radar-range limit; it checks whether radar detection is runnable on
TruckScenes at all.

Confirmed first: `mmdet3d` (already installed, used for FCOS3D/PointPillars)
ships **zero** radar-specific detector configs — grepped every installed
config directory name for "radar", no matches. Unlike camera and LiDAR,
there is no OpenMMLab-maintained radar-only 3D detector to start from.
Standalone radar-only 3D object detection is a genuinely less mature area
than camera or LiDAR — most published "radar" detectors are camera+radar or
LiDAR+radar fusion models, not standalone. Two external, dataset-specific
candidates were checked instead.

## Candidate 1: L-RadSet PointPillars-Radar

The same repository EXP-0018 already partly audited for TruckDrive
(`crrasjtu/L-RadSet`), checked here independently for TruckScenes
specifically — a different question from EXP-0018's 200–400m TruckDrive
crop finding.

| Check | Result |
|---|---|
| Code | Config present at the pinned commit EXP-0018 used (`9eda9266...`); **the dataset-specific pipeline config it imports (`_base_/datasets/radset.py`) no longer exists at the repository's current `main`** — only `l-radset.py` and `l-radset-long.py` are present. The repo has moved since EXP-0018 pinned it |
| Checkpoint | Exists — linked from the README at the pinned commit — but hosted on **Google Drive**, not a stable CDN URL like OpenMMLab's. Automated download was **blocked by this environment's own sandbox policy** (not attempted further — see Decision) |
| Licence | **No licence file detected** on the repository (`license: None` via GitHub's API) — same access-uncertainty EXP-0018 already flagged for the raw data ("requires the author's agreement/request process"), now also true of the code/checkpoint as far as this check could establish |
| Preprocessing | `pts_voxel_encoder: in_channels=6` in the radar model config. TruckScenes' own devkit (`RadarPointCloud.from_file()`) returns **7** raw features per point: x, y, z, vrel_x, vrel_y, vrel_z, rcs. Which 6 of L-RadSet's fields these correspond to, and in what order/units, could not be verified — the dataset config that would define this mapping is the missing `radset.py` above |
| Class mapping | Not reached — blocked upstream |
| Hardware | Same PointPillars-family architecture as EXP-0019's LiDAR candidate — no `spconv`, CPU should be viable in principle. Not verified in practice since the checkpoint could not be obtained |
| Minimal execution path | **Not reached** |
| In-domain baseline (context, not a TruckScenes number) | L-RadSet's own published PointPillars-Radar score (mAP 0.403) is already well below its LiDAR counterpart (mAP 0.648) on L-RadSet's *own* native data — a low ceiling even before considering cross-dataset transfer |

## Candidate 2: K-Radar / RTNH

Checked because it's built specifically for 4D imaging radar (`kaist-avelab/K-Radar`),
matching TruckScenes' Continental ARS 548 RDI sensor type more closely than
L-RadSet's radar in principle.

| Check | Result |
|---|---|
| Code | Available, Apache-2.0 (stated in the repo's `readme.md`, under "License and Commercialization Inquiries" — not a top-level `LICENSE` file, which is why GitHub's API reported `license: None`; corrected here rather than left as a false "no licence" claim) |
| Dataset licence | CC BY-NC-ND (non-commercial, no derivatives) — separate from the code licence |
| Checkpoint | **No evidence found.** Searched the repository's `readme.md` (15,626 characters) for "checkpoint" and "pretrained" — zero matches. Not pursued further |

## Outcome

- [x] Success — worked as intended (as a feasibility check: two real
      candidates investigated, neither reaches a verified minimal execution,
      and the reasons are specific and documented rather than a shrug)

## Decision

- [x] Stop (for this feasibility check) — **no-go on radar, for this
      machine, within this check's scope.** Not because the modality is
      impossible in principle, but because neither candidate investigated
      reaches a verifiable minimal execution here:
      - L-RadSet: checkpoint access blocked (Google Drive, sandboxed
        environment) and the exact preprocessing mapping (7 TruckScenes
        fields → 6 model input channels) is unverifiable without a
        dataset config the source repository no longer publishes
      - K-Radar/RTNH: no published checkpoint found at all
- [ ] Retry
- [ ] Change approach

This reinforces, on a TruckScenes-specific and non-long-range basis, the
same conclusion G-11 in `docs/dataset-suitability.md` already records for
the long-range case: no compatible published radar detector was found in
the releases inspected. That gap register entry should be read as broader
than just the 200–400m question now.

**A genuine fallback exists, not attempted here to keep this within scope**:
a human downloading the L-RadSet checkpoint manually from Google Drive
(outside this sandboxed environment's restrictions) and separately
requesting the `radset.py` config or reverse-engineering the 6-channel
mapping from the checkpoint's stored tensor shapes would likely unblock
this — see the decision note for the concrete next step if the team wants
to pursue it.

**Time spent:** actual elapsed tool/session time was approximately
15–20 minutes (config/license/checkpoint-hosting investigation across two
repositories, one blocked download attempt). Consistent with EXP-0019's
correction: this is real elapsed time, not the story's stated ≤2 hour
ceiling.

## Next action

Combined go/no-go note for AD-S3-1 bullet 3, covering both modalities
(LiDAR: go with PointPillars, per EXP-0019; radar: no-go, per this log).
