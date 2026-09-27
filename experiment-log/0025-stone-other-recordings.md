# EXP-0025 — STONE lake and land recording follow-up

- Date: 2026-09-28
- Owner: Ricky Yuen
- Result: 0030
- Status: conditional support analysis complete; radar physical calibration unresolved.

Extended the existing bounded extractor to two inspected releases with
metadata-derived topic boundaries and per-row/count/frame checks. Processed
20 preselected interior frames per recording. Shared ZIP metadata/cache is reused;
raw sample outputs are kept in separate recording folders on F:.

Lake near-ground radar support is 4.82% versus 26.30% for raised geometry under
the bridged/time-aligned hypothesis. Land gives 0.94% versus 40.65%. The alternative
ROS-origin sensitivity preserves that ordering in both added recordings; the
historical farmland ordering reverses. These are LiDAR-derived voxel populations,
not unbiased sensor recall or independent object instances.

Both added bags contain the same zero-translation radar TF entries. No new
authoritative physical mounting calibration was found. The analysis preserves
that limitation rather than fitting calibration to the scored surfaces.

[Report and reproduction](../docs/stone-environments-followup.md),
[per-recording comparison](../docs/evidence/stone-environments/comparison.csv).
