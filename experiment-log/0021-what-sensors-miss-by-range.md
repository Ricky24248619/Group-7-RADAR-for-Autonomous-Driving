# EXP-0021 — What sensors and saved predictions miss by class and distance

- Date: 2026-09-26
- Owner: Ricky Yuen
- Status: bounded analysis complete; physical miss attribution and matched detector evaluation remain open.
- Results: 0024 (TruckScenes support), 0025 (TruckDrive support), 0026 (GOOSE saved prediction errors).

Reused verified paired counts to produce 590 class/range/margin/timing cohorts
and 266 matched-track summaries. Analysed all native classes separately, including
near-range bands, static/aligned TruckDrive variants and exact/expanded boxes.
No new raw-data downloads or neural inference were required.

Radar support differs substantially between large vehicles and signs, cones,
pedestrians and roadwork barrels. Timing correction changes TruckDrive thin-object
support dramatically. Seven passenger tracks common to near and far bands show
a margin-sensitive exception to the pooled long-range LiDAR advantage.

Separately scored 10 saved GOOSE PTv3 frames (1,785,024 existing LiDAR points,
one scenario). Asphalt and grass errors are hidden by overall accuracy and its
changing class composition. This completes a diagnostic of the saved subset,
not the original 961-frame benchmark. No radar terrain result was produced.

Commands, definitions, denominators, limits, figures and input hashes are in the
[report](../docs/what-sensors-miss-by-range.md). Verification checks class/support
partitions, total point counts and ten frame accuracies against the original log.
Regression tests cover cohort and confusion-matrix semantics. Record numbers 0022
and 0023 and experiment numbers 0019 and 0020 are reserved by existing PRs 58/59.
