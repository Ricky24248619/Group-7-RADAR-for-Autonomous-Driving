# PR #63: PointPillars input-frame review

28 September 2026 · reviewed head `8b95462666b46e2c6ff249e01d3047d9716c51db`

PRs #58 and #59 have merged, recording the LiDAR/radar detector feasibility work.
The only open PR at review time was [#63](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/63),
which extends PointPillars to 80 TruckScenes mini_val samples. Both CI jobs pass.
Its submitted JSON contains 80 sample keys and 596 predicted boxes.

**Changes requested:** the native `LIDAR_TOP_FRONT` input is tilted about 56.23°
from the ego vertical. The new script sends those coordinates directly to an
upright-box PointPillars checkpoint, then rotates the predicted boxes through the
same mounting calibration. All 596 saved output boxes have world-up tilts between
54.60° and 58.20° (median 56.80°), while the associated ground-truth boxes are
upright to numerical precision. This violates the intended upright model input
and box convention; it does not quantify how much of the zero score it explains.

[MMDetection3D's coordinate specification](https://mmdetection3d.readthedocs.io/en/latest/user_guides/coord_sys_tutorial.html)
defines LiDAR z as the gravity axis and yaw-only boxes. A few close class-agnostic
nearest-centre matches cannot validate the input frame or rule out a systematic
problem. The summary's “not a coordinate bug” claim is therefore unsupported.

The submitted review requests a documented upright virtual-LiDAR frame, matching
output transform, geometry regression test and fresh inference/evaluation. Preserve
the existing zero-score output as the historical unrectified run. No replacement
model score is claimed, and PR #63 was not approved or merged.

[Machine-readable audit](evidence/pr63-input-frame-audit.json) includes the saved
prediction hash, calibration quaternion, prediction and annotation tilt ranges.
Reproduce against PR #63's prediction file and local official metadata:

```powershell
python scripts/audit_pointpillars_tilt.py --metadata <TruckScenes-root>/v1.2-mini --predictions <PR63>/scripts/results_mini_val_pointpillars.json
```

This is a review of the stored run and code, not a rerun of PointPillars inference.
