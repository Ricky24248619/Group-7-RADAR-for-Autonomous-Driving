# EXP-0014 — Long-range claim and preprocessing audit

- Date: 22 September 2026.
- Project owner: Ricky Yuen; execution and analysis through Codex.
- Outcome: reused paired observations for range, class, scene, direction, threshold, box-margin and track-weighting sensitivity. Reread every radar keyframe to check the recorded range envelope. Tested four LiDAR counting hypotheses on 30 deterministically selected frames.
- Key qualification: all 1,145,496 recorded radar returns are closer than 190 m to their respective sensors; six channel maxima are approximately 189.524 m. This is an empirical dataset boundary with an unconfirmed cause, not a hardware specification.
- Within 150–180 m, LiDAR/radar geometric support is 93.16%/22.10%; in the forward 30-degree sector it is 93.39%/27.80%. The support difference persists in scene and track checks but remains conditioned on LiDAR-based annotations.
- Publisher LiDAR-count reproduction remains unresolved. The 1-degree mean-time sector approximation matches 336/1,968 counts in the bounded subset; no hypothesis restores full agreement.
- [Evidence audit, literature qualifications and reproduction](../docs/long-range-evidence-audit.md). Result record 0017.
- Validation: subgroup totals, track selection, saved geometry, raw file hashes and deterministic sample selection checked. Raw per-point recount for all 1,968 diagnostic observations equals the previous saved output. Focused regressions and full suite run with existing dependencies.
- No detector inference, full-dataset training, human acceptance signoff or timesheet hours are claimed. Protected-branch gates and the legacy evidence-ownership guard remain unchanged.
