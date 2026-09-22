# EXP-0011 — TruckScenes shared-frame coverage and camera score reproduction

- Date: 22 September 2026.
- Project owner: Ricky Yuen; execution and analysis performed through Codex.
- Story: Sprint 3 range comparison, following the local raw-data rebuild.
- Environment: Windows, Python 3.11.9, truckscenes-devkit 1.2.0, NumPy 1.26.4,
  pypcd4 1.4.3, pyquaternion 0.9.9. CPU only, no new model installation or inference.
- Outcome: all 80 official mini_val samples processed across three sensor
  channels, with release calibration and ego-pose alignment. Both official
  camera evaluations reproduced the committed scores exactly.
- Evidence, full commands, tables, plots, filtering reconciliation and limits:
  [raw comparison report](../docs/truckscenes-raw-comparison.md).

This is agent-run experiment evidence. It does not supply human reviewer
acceptance or personal timesheet hours. No new radar/LiDAR detection score,
custom evaluator or causal sensor ranking is claimed.
