# TruckDrive follow-up protocol

24 September 2026. The earlier complete scene_28_1 run is the pilot.

## Selection

Retain scene_28_1 and add scene_28_6, scene_28_12, scene_28_18 and scene_28_24.
These indices were chosen to spread the follow-up across the numbered 24-scene
mini release before examining new sensor-support outcomes. This is a selected
subset, not a random sample of all driving conditions or independent drives.

Full archives for the four additions total about 23 GB. For a bounded local
analysis, use 40 annotation frames per scene, evenly spaced in timestamp order,
including the first and last: index `round(i * (N - 1) / 39)` for i=0..39.
The switch from full archives to sampled frames was made for download cost
before examining new support outcomes. Retain all annotation files for ego-pose
interpolation; download the selected radar and four LiDAR stream members using
HTTP ranges from the official ZIPs. Verify each extracted member's ZIP CRC and
SHA-256. This is not a claim that every full archive was downloaded or verified.

## Measurement

Reuse the same-sync paired-support pipeline from the pilot. Include every valid
non-ego cuboid in each selected frame; exclude invalid 3D placeholders. Count
returns in the exact oriented box and with each face expanded by 0.5 m. Compare
static calibration and the existing filename acquisition-pose correction
hypothesis. Do not extrapolate poses; compare both timing variants only on
annotations retained by the aligned variant. Missing frames remain visible.

Primary cohort: vehicle annotations at 200 <= planar box-centre range < 400 m.
Report 100-150, 150-200, 200-250, 250-300 and 300-400 m separately. Report
passenger cars, forward +/-30-degree vehicles and all classes as sensitivity
cohorts. Preserve zeros in denominators and report support at >=1, >=3 and >=5
returns. Return counts from different sensors are not equivalent information.

Track and annotation IDs are qualified by scene. Report pooled observations,
each scene, equal-scene means, each scene's effect range, leave-one-scene-out
means, equal-track support and one first qualifying observation per track.
Repeated frames are not independent trials. With five selected clips, do not
present frame-wise binomial confidence intervals as population uncertainty.

## Interpretation and verification

The measured endpoint is geometric support for released annotated objects.
It is not detector recall, precision, AP, or an intrinsic ranking of modalities.
LiDAR-informed annotations, different hardware/fields of view, internal fused-cloud
processing, object motion and unresolved deskew limit causal interpretation.
Preserve any reversals across scenes, distances or sensitivity variants.

Verify sampled input hashes, paired identity and count arithmetic, and compare
selected counts against a full-cloud implementation using explicit box rotation
without the production KD-tree prefilter. This independently checks counting,
but does not independently validate the shared calibration or timing hypothesis.

Sources: [official devkit and mini download](https://github.com/torc-ai/TruckDrive),
[dataset paper](https://arxiv.org/html/2603.02413v1).
