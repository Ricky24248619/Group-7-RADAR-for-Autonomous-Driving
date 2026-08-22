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

## Repository layout

| Path | What it is |
|---|---|
| `DATASET_OVERVIEW.md` | Pre-kickoff research: TruckScenes / TruckDrive facts, sizes, licences |
| `SETUP.md` | The working environment: what's installed, where, how to use it |
| `decision-log.md` | Every decision that constrains the work, with reasoning (D-01…) |
| `docs/dataset-survey-template.md` | Fixed-checklist survey — one per dataset, owner fills, another member reviews |
| `docs/dataset-surveys/` | The surveys themselves (GOOSE, STONE, …) |
| `docs/domain-study-template.md` | WS1 keynote/course study entries |
| `docs/domain-study/` | The study entries |
| `docs/evidence/` | Rendered frames and other evidence referenced by surveys and logs |
| `docs/metrics-definitions.md` | Every metric we report, defined once — nothing undefined leaves this repo |
| `templates/experiment-log-entry.md` | One entry per experiment attempt (installs, model runs, Autoware) |
| `templates/comparison-record.md` | One record per benchmark result, mandatory D-01 identification fields |
| `client-notes/` | Short findings notes written for Adrian and Fabian (RY-4 format) |
| `scripts/` | Utility scripts, each logged in an experiment-log entry |

## Datasets

| Dataset | Status | Role |
|---|---|---|
| MAN **TruckScenes** (NeurIPS 2024) | Primary | Largest annotated 360° 4D-radar dataset; detection + tracking |
| TORC **TruckDrive** (CVPR 2026) | Primary | Long-range (1000 m / 2D, 400 m / 3D); the D-04 dataset |
| **GOOSE** (ICRA 2024) | Feasible — tested 22 Aug | Off-road terrain baseline; raw 360° radar (unlabelled); native ROS bags |
| **STONE** (ICRA 2026) | Parked pending storage | Only off-road dataset with annotated 4D imaging radar; 346 GB single zip, no devkit |

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

## Source documents

Sprint 1 deliverables (Scope of Work, Skills & Resources Audit, Risk Register,
Acceptance Tests, Set of Stories) live in the team OneDrive under
`General/Group_07/`. Decisions D-01–D-04 from the Scope of Work are mirrored in
`decision-log.md` here — this file is the living copy. Risk register IDs
(R-xx) and acceptance test IDs (P-x) referenced around this repo refer to
those OneDrive documents.
