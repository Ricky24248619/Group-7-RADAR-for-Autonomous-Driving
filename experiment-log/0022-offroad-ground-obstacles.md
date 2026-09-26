# EXP-0022 — Off-road ground versus obstacle candidates

- Date: 2026-09-26
- Owner: Ricky Yuen
- Status: LiDAR diagnostic and access audit complete; paired terrain study open.
- Result: 0027.

Partitioned all 64 GOOSE labels into ground surfaces, ground cover, obstacle
candidates, vegetation, ambiguous geometry, water and excluded labels. Regrouped
the verified 961-frame inventory, then scored the ten saved PTv3 frames using
ground/obstacle prediction categories while retaining unresolved vegetation/other.
Checked every saved scan, label and prediction hash against the preceding study.
No new inference or dependencies.

Ground-surface points assigned a ground category fall from 98.38% at 0–25 m to
65.20% at 100–150 m in this small single-scene subset. This is broader than exact
surface-material classification and does not measure terrain coverage or safe
driveability. Above-ground height and holes were not measured.

Downloaded and parsed STONE sequence metadata, confirming three radar point-cloud
topics and LiDAR, all with 1,781 messages. The listed 78.74 GB SQLite bag was not
downloaded. Current README and paper use different grid configurations; actual
labels and synchronization remain unverified. Updated the old survey with these
specific access findings without treating the candidate as a completed benchmark.

See [report, limitations and reproduction](../docs/offroad-ground-and-obstacles.md)
and [metadata audit](../docs/evidence/offroad-ground/stone_metadata_audit.json).
