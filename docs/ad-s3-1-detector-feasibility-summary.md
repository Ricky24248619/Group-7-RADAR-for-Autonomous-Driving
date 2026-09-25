# AD-S3-1: camera-result audit and detector feasibility — summary

25 September 2026 · Owner: Aiden Blampain · Reviewer: Ricky

Closes out AD-S3-1's three acceptance bullets. Each is a separate piece of
work with its own experiment log, result record and evidence; this ties them
together as the single go/no-go note the story asks for.

## Bullet 1 — camera-result audit

**Done: EXP-0016, result 0019.** Independently audited the EXP-0010
four-camera FCOS3D result using the devkit's own geometry rather than the
code that produced it. Established: full camera/sample data coverage
(80/80), and source-camera visibility for all 247 boxes checked in a
four-sample rerun. **Does not** establish metric coordinate accuracy — a
review counterexample (doubling every box's distance and size still passed
the same check) showed the visibility check is structurally blind to that
class of error, and the log was corrected to say so rather than leave the
overstated version standing. The low-score cause remains open: camera
height/pitch and scene-domain content (both `mini_val` scenes are
container/logistics yards) are both plausible, undistinguished.

## Bullet 2 — one radar and one LiDAR candidate, ≤2hr feasibility each

**LiDAR: go. EXP-0019, result 0022.** CenterPoint (the original candidate)
is a no-go — `spconv` has no Windows wheel, CPU or CUDA. PointPillars (same
checkpoint family, no `spconv` dependency) is verified: code, checkpoint
(SHA-256 checked), licence, and class mapping all confirmed; two small
preprocessing fixes found and applied; a real minimal execution completed on
one true TruckScenes LiDAR sample, CPU, in seconds.

**Radar: no-go. EXP-0020, result 0023.** Two candidates checked
(`mmdet3d` itself ships no radar detector at all). L-RadSet's
PointPillars-Radar checkpoint is Google-Drive-hosted — download blocked by
this session's own sandbox policy — and its dataset-specific preprocessing
config no longer exists in the source repository. K-Radar/RTNH has no
published checkpoint found at all. Neither is a dead end in principle; both
are documented, specific blockers with a concrete unblock path recorded in
`docs/truckscenes-radar-detector-decision.md`, not attempted here to stay
within scope.

## Bullet 3 — this note

**Requirements and fallback, stated plainly:**

| Modality | Status | Exact requirement to proceed | Fallback |
|---|---|---|---|
| Camera | Working (EXP-0006/0010), audited (EXP-0016) | None — already runnable | Controlled height-vs-scene-domain check, still open |
| LiDAR | **Go** (EXP-0019) | Extend PointPillars' verified minimal execution to all 80 `mini_val` samples, scored with the devkit's evaluator (mirrors EXP-0010's methodology exactly) | None needed — candidate already found |
| Radar | **No-go** (EXP-0020) | A human downloads the L-RadSet checkpoint outside this sandbox, then either recovers the missing dataset config or reverse-engineers the 6-channel mapping from the checkpoint itself, verified the same way EXP-0019 verified its LiDAR fix | Report camera + LiDAR as the project's matched-modality comparison on TruckScenes; state radar's absence and why, rather than omit it silently |

**What this leaves as the project's defensible final experiment on
TruckScenes**: a camera + LiDAR comparison (both zero-shot, both audited to
the same standard), not a three-modality one. That is narrower than
originally hoped, for a specific, evidenced reason, not a shrug — consistent
with how `docs/dataset-suitability.md` §7 already frames the project's
answer to D-04 on TruckDrive as "narrower... and honestly bounded."

**What this does not do**: reopen D-04 (answered on TruckDrive), reopen
TruckScenes' recorded radar-range limit, or claim the radar no-go is
permanent — it is scoped to the candidates and access this check reached,
per EXP-0020's own decision note.

## Evidence

- `experiment-log/0016-fcos3d-4camera-result-audit.md`, result 0019
- `experiment-log/0019-truckscenes-lidar-detector-feasibility.md`, result 0022
- `experiment-log/0020-truckscenes-radar-detector-feasibility.md`, result 0023
- `docs/truckscenes-lidar-detector-decision.md`
- `docs/truckscenes-radar-detector-decision.md`
- `TruckScenes - Aiden/SUMMARY.md`
