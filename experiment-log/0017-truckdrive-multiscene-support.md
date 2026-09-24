# EXP-0017 — Five-scene TruckDrive long-range vehicle support

- Date: 2026-09-24
- Owner: Ricky Yuen
- Status: completed descriptive analysis; no new detector run.

Extended the pilot with scenes 6, 12, 18 and 24, fixed before outcome inspection.
Used 40 timestamp-spaced frames per scene and 190 matched frames after
pose-boundary exclusions. The 200-400 m vehicle cohort contains 504
observations and 55 scene-qualified tracks. Static support is
80.36% / 37.50% and aligned support is 84.72% / 35.52% (LiDAR / radar).

Selection, reproduction, sensitivity tables, exceptions and scientific limits are
in [the result](../docs/truckdrive-multiscene-result.md) and
[protocol](../docs/truckdrive-multiscene-protocol.md). Result record: 0020.
Preserve the geometric-support interpretation; do not relabel these as detection rates.
