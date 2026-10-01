# EXP-0029 — Finding evidence reanalysis and additional dataset audit

- **Date started / completed:** 1 October 2026
- **Owner:** Ricky Yuen; analysis executed using Codex on the local CPU
- **Workstream / story:** WS1/WS2/WS4, sensor evidence, additional dataset fit and reproducibility

## Goal

Produce at least 20 evidence-supported findings; add relevant independent
datasets and LiDAR/radar research. The GitHub update contains findings and their
reproduction/evidence. The theoretical client report is created locally outside
the repository, as requested; no client message is sent.

## Environment

Windows; existing Python 3.11.9 RADAR environment; standard library for committed
table reanalysis; existing NumPy and Pillow for new Boreas decoding. No package
installation, GPU inference, checkpoint execution, model training or full dataset
download. Original main snapshot: `e47197b`.

## Dataset / data subset

- TruckScenes: committed exact/expanded raw-recount tables, 389 paired frames,
  25,117 annotation observations; rigid timing restricted to the same population.
- TruckDrive: committed static/aligned counts from five preselected mini clips;
  common annotation identities only; 504 long-range vehicle observations, 55 tracks.
- GOOSE: committed 24-frame, eight-scenario confusion counts; original ten-frame
  flight subset; separate three-frame context intervention and geometry diagnostic.
- STONE: committed 60-frame, three-recording, conditional geometric support.
- RADIATE: committed 17-frame public fog pilot; 39 vehicle observations and controls.
- New Boreas: three chronological public Navtech scans and nearest LiDAR scans
  from `boreas-2021-09-02-11-42`, 16,441,068 raw bytes outside Git.
- New WildScenes: six pinned official split CSVs; metadata only, no raw terrain.
- Dual-Radar, RADIal and VoD: pinned primary-source review only; no raw data used.

## Steps and commands

```text
python scripts/analyse_additional_datasets.py --acquire --source-root <outside-repo>
python scripts/analyse_findings_oct01.py
python scripts/render_findings_oct01.py
python -m unittest discover -s tests -v
python scripts/validate_result.py
python scripts/validate_experiment_logs.py
git diff --check
python scripts/session_check.py --who ricky
```

Existing local research inputs were used for the initial additional-data analysis
without `--acquire`; the acquire route pins the same documentation revisions and
implements the same bounded public selection. Every consumed raw/metadata input
has a recorded byte count/SHA-256; existing table inputs are hashed separately.
The new acquisition route was rerun from a clean source directory: all three
additional-data output files reproduced byte-for-byte, including the source
manifest. The analysis rejects a raw source directory inside this Git repository.

Validation: 239 unit tests completed successfully, with 11 existing optional
runtime tests skipped; all eight new focused tests pass. All 34 result records
validate, experiment-log validation passes, and the ownership/session guard is
clear. Optional raw-runtime skips are not claimed as freshly run geometry tests.

## Outcome

- [x] Success — 32 supported findings with measured statements, implications,
  limits and source references generated in `docs/dataset-findings-oct01.md`.
- [ ] Partial
- [ ] Failure

This is successful descriptive analysis, not completion of the matched detector
benchmark. Twenty-eight findings consolidate/recompute existing project evidence;
four derive from new Boreas sample/WildScenes metadata work. The reanalysis also
profiles equal-scene TruckScenes support and radar-only classes. Primary-source
notes add five candidate datasets without claiming five completed benchmarks.

The significant new sample result is radar rotation duration approximately 250 ms
versus approximately 103 ms per LiDAR scan despite file offsets within 50 ms.
The significant metadata result is WildScenes opt3d validation entirely in K-01;
camera/LiDAR test populations require an exact ID join. Raw sources remain outside
Git; only derived results and manifests are committed.

## Attempted fixes

The workspace root is not itself a Git repository, so the desktop managed-worktree
tool could not create the checkout. A regular Git worktree was created from current
`origin/main`. GitHub CLI is not independently authenticated; the existing Git
credential helper provides authenticated GitHub REST access without printing secrets.

## Decision

- [ ] Retry
- [ ] Change approach
- [x] Stop — this bounded analysis is complete; detector, physical calibration and
  controlled weather questions remain separate future work.

**Time spent:** not claimed as member hours; automation runtime is not twelve weeks
of labour. Use actual member timesheets for any effort claim.

## Next action

Review the findings PR through the repository process. Use the locally generated
theoretical report for rehearsal/client discussion if the team chooses. Obtain a
compatible paired detector protocol, independent STONE radar extrinsics and a
multi-sequence weather control before strengthening those respective claims.
