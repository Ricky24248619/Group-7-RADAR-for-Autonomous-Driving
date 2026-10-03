# EXP-0026 — RADIATE public fog sample diagnostic

- Date: 2026-09-28
- Owner: Ricky Yuen
- Result: 0031
- Status: bounded descriptive analysis complete; no detector/weather causal benchmark.

Downloaded the official public 34.6 MB tiny_foggy archive. Verified its hash and
member CRCs. Of 18 radar frames, 17 pass a 50 ms nearest-LiDAR timing gate;
the final frame is excluded at 128.87 ms. Scored 39 annotated box observations
from four tracks, retaining return counts and image-contrast diagnostics separately.

At 50–75 m, 0/19 exact footprints contain above-ground LiDAR returns, while
16/19 have radar image contrast above their surrounding ring. A stricter >20
grayscale-level contrast margin retains 9/19; 1/57 rotated unlabelled controls
passes it. Expanding footprints by 1 m and allowing neighbouring LiDAR scans
gives support in 2/19, so the distant sparse-LiDAR observation is not eliminated
by these bounded sensitivities.

Radar annotations favour radar-visible targets. This short single fog sample
has no clear-weather control and contains repeated tracks. Controls are not
verified negative objects; contrast is not detection, and static timing/calibration
limitations remain. No causal claim about fog or universal modality ranking.

[Report, figure and reproduction](../docs/radiate-fog-pilot.md),
[manifest](../docs/evidence/radiate-fog/manifest.json).
