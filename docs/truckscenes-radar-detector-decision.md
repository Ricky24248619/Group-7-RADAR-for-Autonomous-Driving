# TruckScenes radar detector: go/no-go decision

25 September 2026 · EXP-0020 · result 0023

**No-go, for both candidates checked, within this feasibility check's
scope.** Not because standalone radar 3D detection is impossible in
principle, but because neither candidate reached a verifiable minimal
execution here, for specific, documented reasons — not a shrug.

This does not reopen D-04 or TruckScenes' recorded radar-range limit
(`docs/dataset-suitability.md` §5/§7). It reinforces, on a TruckScenes-
specific and non-long-range basis, what G-11 in that document already
records for the long-range case: no compatible published radar detector was
found in the releases inspected.

## What was checked

| Candidate | Code | Checkpoint | Licence | Preprocessing | Result |
|---|---|---|---|---|---|
| L-RadSet PointPillars-Radar | Present at EXP-0018's pinned commit; dataset config missing at current `main` | Google Drive — download blocked by this session's sandbox policy | No licence file found on the repo | 7 TruckScenes fields → 6 model channels, mapping unverifiable (config missing) | **No-go — access blocked** |
| K-Radar / RTNH | Available, Apache-2.0 (in-readme, not a `LICENSE` file) | **None found** — no "checkpoint"/"pretrained" match in the full readme | Code Apache-2.0, dataset CC BY-NC-ND | Not reached | **No-go — no checkpoint** |

## Why mmdet3d itself wasn't the starting point here

Unlike camera (FCOS3D) and LiDAR (PointPillars, CenterPoint), `mmdet3d`
ships **zero** radar-only detector configs — confirmed by grepping every
installed config directory for "radar". Standalone radar-only 3D detection
is a genuinely less mature research area; most published "radar" detectors
fuse with camera or LiDAR rather than standing alone. Both candidates
checked here are external, dataset-specific research repositories, not
OpenMMLab-maintained baselines — a materially different starting position
from the LiDAR check.

## L-RadSet, in more detail

EXP-0018 already partly audited this repository for TruckDrive's 200–400m
question and pinned commit `9eda9266db3109e4f153eeeb43fef3125d213674`. This
check found the repository has since changed: the dataset-specific pipeline
config the radar model imports (`_base_/datasets/radset.py`) no longer
exists at `main` — only `l-radset.py` and `l-radset-long.py` are present.
Whether these are renamed successors or a genuinely different config was not
resolved within this check's scope.

The checkpoint itself is linked from the README (at the pinned commit) via
Google Drive — a fundamentally less reproducible distribution channel than
OpenMMLab's CDN (used for both FCOS3D and PointPillars). An automated
download attempt was **blocked by this session's own sandbox permission
policy** before any response was received from Google's servers — this is a
constraint of the working environment, not evidence the checkpoint itself is
unavailable to a person downloading it manually.

Even granting checkpoint access, the preprocessing gap is real: TruckScenes'
devkit returns 7 raw radar features per point (x, y, z, vrel_x, vrel_y,
vrel_z, rcs); the model's voxel encoder declares 6 input channels. EXP-0019
solved an analogous LiDAR gap (4 vs. 5) by identifying the exact missing
field from a real error message. That option isn't available here without
either the missing dataset config or the checkpoint's own stored tensor
shapes to reverse-engineer the mapping — neither was reachable in this
check.

## K-Radar / RTNH, in more detail

Chosen as a second candidate specifically because it targets 4D imaging
radar, architecturally closer to TruckScenes' Continental ARS 548 RDI than
L-RadSet's sensor. GitHub's API reported no detected licence
(`license: None`) — checked further and found the actual terms stated
inline in the readme rather than a `LICENSE` file (code: Apache-2.0,
dataset: CC BY-NC-ND) — worth correcting rather than reporting the API's
raw signal as "no licence" without follow-up. But a full-text search of the
15,626-character readme for "checkpoint" or "pretrained" found nothing.
Not pursued past that point.

## What would actually unblock this

Not attempted here, to keep this check within scope, but concrete:

1. A human downloads the L-RadSet radar checkpoint manually from the linked
   Google Drive file, outside this sandboxed environment's restrictions.
2. Either locate `radset.py` at the exact pinned commit (or an earlier tag)
   via the GitHub API's commit history, or inspect the downloaded
   checkpoint's stored tensor shapes/state-dict keys directly to infer the
   6-channel input convention without the config.
3. Verify the inferred mapping the same way EXP-0019 verified its
   preprocessing fix — with a real minimal execution on one TruckScenes
   radar sample, not by assuming the mapping is correct.

## Fallback if this remains blocked

Radar-only detection is not the only way to give the project a matched
comparison. The camera (FCOS3D, EXP-0006/0010/0016) and LiDAR (PointPillars,
EXP-0019) results already provide two modalities on TruckScenes. A two-
modality comparison, honestly scoped as such, is a defensible smaller
deliverable if a radar candidate does not clear this bar before the
checkpoint.

## Next action

Combined go/no-go note for AD-S3-1 bullet 3 (`docs/ad-s3-1-detector-feasibility-summary.md`),
covering camera, LiDAR and radar together.
