# EXP-0018 — Pretrained detector compatibility audit

- Date: 2026-09-24
- Owner: Ricky Yuen
- Status: audit complete; learned-detector comparison blocked by compatibility.

Downloaded and checked both L-RadSet PointPillars checkpoints. Embedded
configurations use forward input limits of 70.2 m LiDAR / 70.4 m radar. The
separate long-range examples extend to 150.4 m; they do not match these weights.
None includes our 504 distant vehicle centers in its declared input rectangle.
TruckDrive's full-range LiDAR source config includes 192 / 504, but no compatible
pretrained radar/LiDAR pair was identified. No neural inference was run.

See [decision and reproduction](../docs/detector-compatibility-decision.md),
[audit evidence](../docs/evidence/detector-compatibility/audit.json) and result 0021.
