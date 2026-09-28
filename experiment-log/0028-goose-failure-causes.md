# EXP-0028 — GOOSE context intervention and geometry diagnosis

- Date: 2026-09-28
- Owner: Ricky Yuen
- Result: 0033
- Status: bounded diagnostic complete; not full validation or paired radar evaluation.

Selected the difficult January frame 0497 and its immediately preceding/following
validation frames (0496/0498) after reviewing EXP-0027. Three frames, 644,654
points, approximately 8.08 seconds; deliberately correlated cases.

Ran the unchanged published PTv3 checkpoint with attention patches 64, a fresh
64 repeat, 128 and 256. Seed, FP32, flash-off setting, single augmentation and
all other saved configuration fields match. All runs contain End Evaluation and
exited zero. Every patch-64 prediction is identical on repeat. No package changes
or training. Patch 256 approached 5,900/6,144 MiB in sampled GPU readings and its
first fragment was slow; no full-split memory-feasibility claim is made.

Pooled near-range rock-to-ground confusion falls 49.52% → 25.02% → 22.56%, and
building-to-ground confusion 18.43% → 10.18% → 4.12%. Correct rock-category rate
only rises 18.12% → 24.82% → 24.90%; one neighbouring frame gets worse, and some
errors change to other wrong labels. This supports a configuration contribution,
not a universally better model or sensor.

Downloaded matching original camera frames through verified ranges of the public
GOOSE 2D validation ZIP: approximately 13.5 MB transferred, CRC and PNG decoding
verified, SHA-256 recorded. Snow, roadside stone structures and nearby buildings
are visible; no calibrated point/image projection or controlled snow experiment.

Original-frame geometry diagnostics show a strong association between rock
points near labelled-ground elevation and ground predictions, with reference-
distance and ground-cover sensitivities retained. Local normals and unresolved
ground-reference points prevent attributing all building errors to low geometry.
No rock/building target shares a 2.5/5 cm voxel with labelled ground/cover; the
coarse labels match the challenge mapping exactly. Baseline output changes with
subset order are handled through the fresh fixed-order repeat.

Validation: 231 tests, 229 passed and two optional skips; result/log validators;
hash, complete-cohort and configuration-difference checks; visual inspection of
all three camera images and the generated diagnostic figure. Model assets, raw
images and predictions remain on F:.

[Report and reproduction](../docs/goose-failure-causes.md),
[run manifest](../docs/evidence/goose-failure-causes/context_manifest.json),
[camera provenance](../docs/evidence/goose-failure-causes/camera_manifest.json).
