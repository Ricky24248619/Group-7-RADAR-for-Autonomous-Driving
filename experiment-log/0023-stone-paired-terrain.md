# EXP-0023 — STONE paired terrain pilot and calibration sensitivity

- Date: 2026-09-26
- Owner: Ricky Yuen
- Status: bounded extraction and conditional support analysis complete; physical radar calibration unresolved.
- Result: 0028.

Processed 20 uniformly sampled interior frames from the first listed farmland
recording using exact HTTP ranges, read-only APSW, rosbags and ZIP CRC checks.
Created an isolated CPU environment on F:, with no new model inference. Actual
labels are 0.4 m, 200 x 200 x 16, unlike the older paper configuration.

Compared native traversability classes and local-ground-relative geometry at
2–10, 10–20, 20–30 and 30–40 m, three spatial tolerances, two angular ROIs and
three coordinate/timing variants. Free and unknown cells are excluded; local
ground height is unresolved wherever plane evidence is insufficient.

At 0.8 m tolerance, ±10° vertical ROI and bridged/time-aligned radar coordinates,
pooled radar support is 17.76% near ground and 29.53% raised. At the released ROS
origin, this becomes 24.07% and 19.33%: the ordering reverses. LiDAR support is
99.41% and 96.96% under the exported calibration, but labels are LiDAR-derived.
No fair detection-accuracy or universal floor/obstacle ranking is established.

The observed radar timing offsets are −27.66 to +22.58 ms. Motion interpolation
never extrapolates; exported poses pass a strict absolute matrix check. Physical
radar translations, sensor-clock synchronization and occlusion remain unverified.

The [report](../docs/stone-paired-terrain-pilot.md) includes reproduction, counts,
sensitivities and limitations. The [dataset shortlist](../docs/offroad-dataset-next-steps.md)
identifies CORD for independent off-road data, Great Outdoors for 2D radar context,
and RADIATE for a distinct weather study. None of those new candidate datasets was
analysed in this experiment.
