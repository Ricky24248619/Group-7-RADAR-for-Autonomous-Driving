# EXP-0013 — Paired all-sensor TruckScenes object support

- Date: 22 September 2026.
- Project owner: Ricky Yuen; execution and analysis through Codex.
- Outcome: all six radar and six LiDAR keyframes recounted against identical oriented annotations. The rigid baseline includes 399 samples; point-wise ego correction includes 389 after whole-sample timing exclusions. Comparisons between preprocessing methods use the same 25,117 annotation tokens.
- Result record: 0016. [Client briefing and reproduction commands](../docs/client-comparison-brief.md).
- Measured: radar count agreement with all 25,117 publisher values; LiDAR exact agreement in 4,164. Apparent radar-only observations fall from 185 to 39 after point-wise ego correction; LiDAR count reproduction remains incomplete.
- Limitations: geometric support, not detector recall, mAP, sensor superiority or learned fusion performance. LiDAR-based annotation selection; repeated observations; residual target motion and cabin articulation; sensitivity to box margins.
- Online resource attempt: official K-Radar radar and LiDAR model downloads both returned a quota-exceeded page, not ZIP files. No new model inference is claimed. No large new dataset or training job was started.
- Validation: seven raw-runtime regression tests plus the full dependency-light suite; CSV/manifest reconciliation, output-hash verification and visual checks of charts. See the verification JSON linked from the briefing.
- The user's request authorizes this cross-dataset work. The legacy session guard's blanket docs/evidence ownership rule remains unchanged. Protected-branch review requirements remain in force.

This log records an agent-executed experiment, not personal timesheet hours or a completed human acceptance review.
