# EXP-0027 — Fresh GOOSE ground-category evaluation across eight scenarios

- Date: 2026-09-28
- Owner: Ricky Yuen
- Result: 0032
- Status: bounded 24-frame inference and analysis completed; full validation not run.

Selected three interior-quantile frames from each of eight scenarios before
inference, then ran the existing published challenge PTv3 checkpoint on the
GTX 1660 in WSL. Same documented compatibility settings as EXP-0004: FP32,
patch size 64, FlashAttention off, one augmentation, seed 20260831. No installs
or training. The initial PYTHONPATH import failure was corrected before inference.

The new run completed all 24 frames / 4,192,081 points in approximately six
minutes of the evaluation loop. End Evaluation and process exit 0 were verified;
selection, config, checkpoint, runtime patch and input/output hashes are recorded.
Older saved predictions and reports were preserved.

At 0–25 m versus 100–150 m, pooled true-ground points assigned ground are
98.63% versus 97.67%; obstacle points assigned ground are 2.99% versus 14.17%.
The earlier one-scenario ground drop is not representative of this wider sample:
one scenario contributes 85.1% of distant ground, and equal-scenario correctness
is only 89.34% in that band. Buildings contribute 91.3% of distant obstacle-to-
ground errors. Nearby rock points also show substantial confusion, but this is
not an instance-level rock detection rate. Thin class/scenario groups and repeated
points preclude a controlled range or general environment conclusion.

Extended the existing analyzers to accept a verified subset manifest and emit
per-scenario groups. Added selection-completeness/hash checks and regression tests.
Independently checked per-frame and per-scenario sums against every pooled bucket.
Full suite: 226 tests, 224 passed and two optional skips. Result/log validators
and diff whitespace checks passed. The intentionally missing-file validator test
prints an expected error line even when the suite succeeds.

Also audited STONE's 458,212 archive names and seven exported calibrations;
no numerical physical radar extrinsics were found in the inspected sources.
The paper says calibration was performed. The report now specifies the exact
missing transforms/conventions without treating zero ROS translations as verified.

[Report and complete reproduction commands](../docs/goose-multiscenario-terrain.md),
[runtime manifest](../docs/evidence/goose-stratified/runtime.json),
[STONE audit](../docs/evidence/stone-environments/calibration_audit.json).

## Same-day case follow-up

Reused the same verified 24 predictions for per-frame rock/building errors and
frame-local rock instance counts; no new inference or downloads. Nearby rocks
occur in three selected frames from two scenarios, only seven frame-local
instance observations. One January frame supplies 96.92% of nearby rock and
98.75% of nearby building ground-confusion errors. Rock instance 79 in that frame
alone supplies 86.72% of the nearby rock errors. The distant rock result consists
of six points on one instance in one frame and is not generalisable.

The [case report](../docs/goose-error-cases.md) includes post-hoc error-count-
selected point overlays and preserves selection bias and raw-z limitations.
Added a regression check that unassigned instance zero is excluded and partial
instance errors retain their point denominator. Final suite: 227 tests, 225 passed,
two optional skips. Model outputs remain unchanged.
