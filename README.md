# RADAR for Autonomous Driving — Group 7

CITS3200 Professional Computing · Semester 2 2026 · Team 07
Client: **Adrian Boeing** · Technical mentor: **Fabian Deuser** (on all meetings)
IP: Creative Commons / open source · Multiple teams on this project

**Goal:** an evidence-based comparison of RADAR, LiDAR and camera perception for
autonomous trucking — running existing open-source models on public datasets,
recording everything reproducibly, and handing over a documented body of work to
a future team.

**Headline research question (D-04, pending confirmation with Fabian):** do
current models fail beyond ~150 m, and does 4D radar degrade less than LiDAR at
that range? Reported by range band, never as one aggregate number.

**Five-scene follow-up (24 September):** [TruckDrive long-range vehicle result](docs/truckdrive-multiscene-result.md)
covers 190 matched sampled frames, with per-scene, timing, box-margin and track checks.
LiDAR has stronger 200-400 m vehicle geometric support in these selected scenes; this is not detector accuracy.

**Class and distance study (26 September):** [what is missing at short and long range?](docs/what-sensors-miss-by-range.md)
breaks paired sensor support down by native object class, tests the same tracks near/far,
and identifies timing-sensitive thin objects and an exception to the pooled LiDAR advantage.
A separate diagnostic of ten saved GOOSE prediction frames examines terrain-label errors.

**Off-road follow-up (26 September):** [ground surfaces versus obstacle candidates](docs/offroad-ground-and-obstacles.md)
separates ground-category errors from surface-material errors and inventories distant GOOSE points. The [STONE paired terrain pilot](docs/stone-paired-terrain-pilot.md)
now processes 20 frames of actual radar, LiDAR and terrain labels. Radar calibration
sensitivity limits the floor-versus-protrusion conclusion; hole detection remains open.

**Detector next step:** [checkpoint compatibility decision](docs/detector-compatibility-decision.md)
records downloaded weights, verified input ranges and the requirements for a valid learned-model comparison.

**New cross-dataset findings (22 September):** [long-range radar versus LiDAR, including TruckDrive](docs/long-range-cross-dataset-review.md)
adds a verified 200-frame TruckDrive scene out to 399 m, vehicle/distance/point-density
profiles and acquisition-time sensitivity. L-RadSet and Boreas-RT are assessed as
independent follow-ups. One scene and geometric support do not establish detector accuracy.

**Latest evidence audit (22 September):** [does LiDAR work better at long range?](docs/long-range-evidence-audit.md)
checks scene/class/track sensitivity and discovers a recorded radar boundary near
189.52 m. The supported claim concerns this dataset's geometric support, not a
universal sensor or detector ranking.

**Client briefing (22 September):** [paired radar/LiDAR results and next experiment](docs/client-comparison-brief.md)
covers all 12 sensor channels, per-point LiDAR motion correction and 25,117 matched
object observations. These are geometric support results, not detector accuracy.

**Dataset findings (22 September):** [expanded dataset comparisons and next steps](docs/sprint3-dataset-findings.md)
cover 400 TruckScenes samples, all 961 GOOSE frames and a reanalysis of saved
TruckDrive evidence. The saved-table report is historical for TruckDrive; the new paired scene is linked above.
Matched detector evaluation remains open.
Earlier planning: [11 September catch-up brief](docs/meetings/2026-09-11-catchup.md)
and [dataset comparison / next experiment](docs/dataset-comparison.md).
The August GOOSE next-steps file is historical; its unchecked tasks are not a current
status report. The project has bounded inference and a scored camera submission,
but no verified matched radar/LiDAR benchmark yet.

## Team

| Member | Epic | Owns |
|---|---|---|
| Fariya Zehrin | A | Simulation (Autoware) and results presentation |
| Damien Zhang | B | Fundamentals, off-road domain, benchmarking infrastructure |
| Fatima Sher | C | 4D RADAR detection research and project documentation |
| Kelsey Chen | D | Dataset exploration and sensor visualisation |
| Aiden Blampain | E | Industry and technology review |
| Ricky Yuen | F | Evaluation framework, reproducibility, coordination |

PM rotates each sprint: Damien (sprint 1) → Aiden (sprint 2) → …

Sprint 2 work was organised as Damien/Ricky (GOOSE), Aiden/Fatima (TruckScenes),
and Fariya/Kelsey (TruckDrive), per D-08. Confirm the next allocation at the catch-up.

## Repository layout

| Path | What it is |
|---|---|
| `DATASET_OVERVIEW.md` | Pre-kickoff research: TruckScenes / TruckDrive facts, sizes, licences |
| `SETUP.md` | The working environment: what's installed, where, how to use it |
| `decision-log.md` | Every decision that constrains the work, with reasoning (D-01…) |
| `docs/dataset-survey-template.md` | Fixed-checklist survey — one per dataset, owner fills, another member reviews |
| `docs/dataset-surveys/` | The surveys themselves (GOOSE, STONE, …) |
| `docs/domain-study-template.md` | WS1 keynote/course study entries |
| `docs/domain-study/` | WS1 index — coverage matrix, source assignments, claims ledger — and the study entries |
| `docs/evidence/` | Rendered frames and other evidence referenced by surveys and logs |
| `docs/metrics-definitions.md` | Every metric we report, defined once — nothing undefined leaves this repo |
| `templates/experiment-log-entry.md` | One entry per experiment attempt (installs, model runs, Autoware) |
| `templates/comparison-record.md` | One record per benchmark result, mandatory D-01 identification fields |
| `client-notes/` | Short findings notes written for Adrian and Fabian (RY-4 format) |
| `scripts/` | Utility scripts, each logged in an experiment-log entry |
| `docs/HANDOVER-TOOLING.md` | How the shared tooling works, where it is weak, and what is deliberately unfinished |

## Datasets

| Dataset | Status | Role |
|---|---|---|
| MAN **TruckScenes** (NeurIPS 2024) | Primary | Largest annotated 360° 4D-radar dataset; detection + tracking |
| TORC **TruckDrive** (CVPR 2026) | Primary | Long-range (1000 m / 2D, 400 m / 3D); the D-04 dataset |
| **GOOSE** (ICRA 2024) | Characterised; PTv3 partial at 10/961 frames; closeout proposed | Off-road terrain segmentation. Released assets used here do not support a paired labelled radar/LiDAR experiment |
| **STONE** (ICRA 2026) | Reopened as a bounded research pilot, 26 Sep; historical D-06 retained | 20 paired frames processed on CPU; physical radar calibration remains unresolved |

Surveys live in `docs/dataset-surveys/` — status, sensors, licence and fit
assessment for each. Raw datasets are never committed (see `.gitignore`).

## How we work

1. **If it isn't recorded, it didn't happen.** Dataset facts go in a survey;
   experiment attempts (installs, runs, visualisations, Autoware work) go in
   `experiment-log/` using the template. Failures get dated records — the client
   has explicitly said negative results count.
2. **Comparison stays within a dataset and within a task type** (D-01, D-02).
   The comparison template enforces this with mandatory fields.
3. **Pull request review** for everything. Survey and template conventions
   require an owner *and* a different reviewer.
4. **Decisions that constrain the work go in `decision-log.md`** and are raised
   with Adrian at sprint boundaries, not applied silently.

Before submitting result or experiment-log changes:

```bash
python scripts/validate_result.py
python scripts/validate_experiment_logs.py
```

These validate record structure and log identity. They do not establish experiment
completion or scientific correctness.

[GitHub Actions](.github/workflows/checks.yml) runs both, plus the test suite, on
every pull request — so a numbering collision or a broken record is caught before
review rather than after merge. Running them locally first is still faster than
waiting for the run.

## Sprint 2 deliverables

The [Sprint 2 submission package](docs/sprint-2/README.md) contains the current
team report, proposed Sprint 3 stories, combined retrospective and supporting
documents. Read its report-correction notes before using the narrative claims.
The package is a dated OneDrive snapshot, not proof of formal submission.

## Source documents

Sprint 1 deliverables (Scope of Work, Skills & Resources Audit, Risk Register,
Acceptance Tests, Set of Stories) live in the team OneDrive under
`General/Group_07/`. Decisions D-01–D-04 from the Scope of Work are mirrored in
`decision-log.md` here — this file is the living copy. Risk register IDs
(R-xx) and acceptance test IDs (P-x) referenced around this repo refer to
those OneDrive documents.

The [revised deliverables](Revised%20Sprint%201%20Deliverables/) and
[project handbook](docs/PROJECT-HANDBOOK.md) are also stored here. The revised
documents retain the original IDs and state acceptance gaps; merging them does not
establish client approval.
