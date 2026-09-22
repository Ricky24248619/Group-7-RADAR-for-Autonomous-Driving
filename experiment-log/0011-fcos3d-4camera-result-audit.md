# EXP-0011 — Independent audit of the EXP-0010 four-camera FCOS3D result

- **Date started / completed:** 2026-09-22 / 2026-09-22
- **Owner:** Aiden Blampain
- **Workstream / story:** AD-S3-1 ("Camera-result audit and detector
  feasibility"), acceptance bullet 1. Produces
  `results/records/0012-fcos3d-4camera-audit.json`.

## Goal

AD-S3-1 requires checking calibration, preprocessing, box coordinates and
camera/sample coverage for the EXP-0010 four-camera output, adding visual
checks against annotations, and recording channel-level success/skip —
while explicitly keeping the low-score cause open unless a controlled check
isolates it. This audit does exactly those checks, deliberately using code
paths EXP-0006/EXP-0010 never called, so a bug shared between "produce the
result" and "check the result" can't hide from it.

## Method

Four checks, implemented in `scripts/audit_fcos3d_4camera_result.py`:

1. **Camera/sample data coverage** (full 80-sample `mini_val`, no inference):
   confirms every sample's ground truth actually has all 4 camera channels.
2. **Geometric visibility audit of the existing EXP-0010 predictions**
   (`results_mini_val_fcos3d_4cam.json`, no rerun): every saved global-frame
   predicted box is reprojected, with the devkit's own
   `TruckScenes.boxes_to_sensor()` + `box_in_image()`, into each of that
   sample's 4 cameras. EXP-0010's output never recorded which camera
   produced which box, so this is a geometric visibility **proxy**, not
   literal per-call provenance — reported as such.
3. **A small instrumented rerun** (4 samples spread across both `mini_val`
   scenes — split indices 0, 20, 40, 60 — all 4 cameras, 16 calls total),
   writing predictions to a separate audit-only file
   (`audit_fcos3d_4camera/instrumented_rerun_results.json`) tagged with
   `source_camera`. EXP-0010's own result file is untouched. This gives
   genuine per-call success/skip counts.
4. **Round-trip check**: for every box from step 3 (source camera known
   with certainty), reproject it — again with the devkit's own
   `boxes_to_sensor()`/`box_in_image()`, never with
   `truckscenes_fcos3d_infer.py`'s own conversion math — into that *same*
   camera. A box that round-trips validly confirms the calibration/
   box-coordinate conversion is geometrically consistent, checked by code
   that had no part in producing the result.

Visual overlays (devkit ground-truth boxes in green, our predicted boxes in
red, both drawn with the same wireframe routine over the real camera image)
were rendered for all 16 sample/camera pairs from step 3.

## Environment

Same `truckscenes-devkit/detection-env` venv and FCOS3D checkpoint as
EXP-0006/EXP-0010, reused as-is — no changes. One new finding: `Box.render()`
needs the optional `truckscenes-devkit[all]` visualization extras, not
installed in `detection-env` by design (installing them risks re-upgrading
numpy past the `<2` pin EXP-0006 fought to establish). Worked around by
drawing box wireframes directly with `view_points()` (same corner convention
and edge pattern as the devkit's own `render_box`) instead of installing
anything.

## Results

**1. Coverage — clean.** All 80 `mini_val` samples have all 4 camera
channels present in `sample["data"]`. Zero missing. "4 cameras" was never
silently short of data for any sample.

**2. Geometric visibility (existing EXP-0010 predictions, 5,247 boxes).**

| | value |
|---|---|
| Boxes reprojecting into **zero** cameras | 5 / 5,247 (0.10%) |
| Boxes reprojecting into **more than one** camera | 1,815 / 5,247 (34.6%) — expected, adjacent camera pairs overlap |
| Valid fraction, CAMERA_LEFT_FRONT | 33.8% |
| Valid fraction, CAMERA_RIGHT_FRONT | 34.8% |
| Valid fraction, CAMERA_LEFT_BACK | 19.7% |
| Valid fraction, CAMERA_RIGHT_BACK | 46.5% |

99.9% of predicted boxes are geometrically plausible from at least one
camera — a coordinate bug producing systematically nonsensical positions
would not look like this. The per-camera spread (LEFT_BACK lowest,
RIGHT_BACK highest) is noted but not explained by this audit; it may reflect
scene content or truck-mounting asymmetry rather than a defect.

**3. Instrumented rerun — 16 calls (4 samples × 4 cameras).**

| Status | Count |
|---|---|
| success (≥1 box ≥ score threshold) | 13 |
| skip — zero detections above threshold | 3 |
| skip — no camera data | 0 |

No call skipped for lack of data (consistent with check 1). FCOS3D *is*
running and producing output on the large majority of camera views —
the near-zero mAP is not explained by the model failing to execute or
returning nothing; whatever the cause, it happens after detection, not
instead of it.

**4. Round-trip check — 247/247 boxes valid (100%) in all 4 cameras.**

| Camera | Valid / Total |
|---|---|
| CAMERA_LEFT_FRONT | 62 / 62 |
| CAMERA_RIGHT_FRONT | 46 / 46 |
| CAMERA_LEFT_BACK | 61 / 61 |
| CAMERA_RIGHT_BACK | 78 / 78 |

Every single predicted box, checked with code that never produced it,
correctly reprojects into the camera it actually came from. **This rules out
a coordinate-transform/calibration bug in the box-conversion pipeline** —
the strongest and most direct answer this audit gives to bullet 1's
calibration/box-coordinate check.

**Visual check (16 overlays, `scripts/audit_fcos3d_4camera/overlays/`).**
Two samples reviewed directly: predicted boxes (red) cluster in generally
the right image region as ground truth (green) — not flipped, not behind
the camera, not off in an unrelated part of the frame — but are frequently
thin/sliver-shaped and duplicated densely over single large objects
(shipping containers, trailers), rather than one clean box per object. This
is a localization/scale failure pattern, consistent with EXP-0010's
evaluator output (mASE 0.9849, mATE 1.0448), not a sign-flip or frame-swap
bug. **New observation, not previously flagged**: both scenes in `mini_val`
are container/logistics yards — a visually distinct domain from nuScenes'
street driving footage, independent of camera height/pitch. This is a
second plausible contributing factor to the domain gap, alongside the
camera-height hypothesis from EXP-0006, and this audit cannot separate the
two.

## Outcome

- [x] Success — worked as intended

## What this does and does not establish

**Established, with direct evidence:**
- No coordinate-transform/calibration bug (100% round-trip validity, code
  that never produced the result)
- No missing-data explanation (0/80 samples missing a camera channel)
- The model runs and produces output on ~81% of individual camera views in
  the audited subset — failure is in what it predicts, not whether it runs

**Still open** (per AD-S3-1's explicit instruction not to close this without
a controlled isolating check):
- Whether camera height/pitch (EXP-0006's hypothesis) or scene-domain
  content (container yards vs. nuScenes' streets, newly observed here) is
  the dominant cause — or both, unseparated
- A controlled check that isolates either variable (e.g. a camera-height-only
  synthetic manipulation, or scoring against nuScenes-style street scenes
  from TruckScenes if any exist in a larger split) has not been run

## Decision

- [x] Change approach — the audit is complete for what a non-controlled
      check can establish. The remaining open question (height vs. scene
      domain) needs a controlled experiment, not more auditing of the
      existing result, and is out of scope for AD-S3-1's bullet 1.
- [ ] Retry
- [ ] Stop

**Time spent:** approximately 2 hours (script development reusing devkit
geometry primitives, one CPU rerun, analysis, write-up).

## Next action

Move to AD-S3-1's remaining bullets: the ≤2-hour radar and LiDAR detector
feasibility checks, and the go/no-go note.
