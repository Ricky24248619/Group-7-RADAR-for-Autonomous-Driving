# Project Handbook — CITS3200 Group 07

**RADAR for Autonomous Driving** · Client: Adrian Boeing · Technical mentor: Fabian
Last updated 4 September 2026

One document explaining what the project is, how the three datasets and their toolkits
work, and what each person's technical stack actually consists of. Written for anyone
on the team, and for the group that inherits this project.

> **This Markdown file is the source of truth.** `PROJECT-HANDBOOK.docx` is generated
> from it by `scripts/build_handbook.py` for sharing outside the repository. Edit the
> Markdown, regenerate the Word file — never the other way round.

---

## 1. What the project actually is

Adrian set it out in the first two minutes of the kickoff:

> *"This project is a little bit loosely defined. It's really just — I don't know
> anything about radar, he doesn't really know much about radar, we like trucks and
> robots and we think they're cool, and so it's an area that we're trying to get
> ourselves a bit up to speed on."*

It is a **learning and benchmarking exercise**, not a product build. Three parts:

1. Understand the self-driving stack and how sensor types differ
2. Focus on trucks, and on 4D radar specifically — both very new
3. Benchmark: detect something with LiDAR, versus camera, versus radar. How do they
   differ, and what are the trade-offs?

The method Adrian described:

> *"We would find some open source solutions that are out there... and basically we're
> just trying to run them on the data sets. So okay, we ran this algorithm, we spent X
> number of days trying to get it going, we couldn't get it going — or yep, we got it
> working but it doesn't perform very well."*

**"We could not get it working" is a reportable result.** That is why this repository
records failures as first-class outcomes rather than discarding them.

---

## 2. Where our work sits in the stack

A self-driving system runs roughly:

```
sensors  →  PERCEPTION  →  prediction  →  planning  →  control
```

- **Sensors** — cameras, LiDAR, radar, GPS/IMU
- **Perception** — turning raw readings into "there is a tree 12 m ahead", or "this
  ground is drivable"
- **Prediction / planning / control** — what moves where, what to do, and steering

**This project lives entirely in perception.** We are not building planning or control.

You cannot test perception by driving a truck around a mine site, so the field uses
**datasets**. Someone already drove a sensor-covered vehicle, recorded everything, and
paid people to label what was in each frame. A dataset gives you three things:

1. **Frozen sensor recordings** — images, LiDAR point clouds, radar returns
2. **Ground truth** — a human's answer for what is actually there
3. **A devkit** — code to load it

You run a model on (1), compare against (2), and get a score. That is benchmarking, and
it is what this project does.

**Autoware** sits alongside as an open-source implementation of the *whole* stack. You
can replay a dataset into it and watch the pipeline run, which is why "does this dataset
ship ROS bags" is a question worth asking.

---

## 3. The one concept everything else depends on

**Object detection** asks *"where are the things?"* Output: a list of 3D boxes. Scored
with **mAP**. This is what TruckScenes and TruckDrive do.

**Semantic segmentation** asks *"what is everything made of?"* Output: a class label for
every pixel and every LiDAR point. Scored with **mIoU**. This is what GOOSE does.

They are not interchangeable and **their scores cannot go in the same table**. That is
what decision **D-01** in `decision-log.md` protects against.

Why it matters: on a highway, detection is right — discrete objects, put boxes round
them. Off-road in a forest or a mine, detection is close to useless. There are no lanes
and often no other vehicles. The real question is *"can I drive on this?"*, which is a
per-point question about terrain. That is segmentation.

---

## 4. The three datasets

Not competing candidates. **Different instruments, each answering one question.**

| | **MAN TruckScenes** | **TruckDrive** | **GOOSE** |
|---|---|---|---|
| Owners | Aiden & Fatima | Fariya & Kelsey | Damien & Ricky |
| Question it answers | Radar vs LiDAR vs camera, like-for-like | Does perception collapse past ~150 m? | Can we tell drivable ground from obstacles, off-road? |
| Published | NeurIPS 2024 | CVPR 2026 | ICRA 2024 |
| Task | 3D object detection | 3D detection, long range | Semantic segmentation |
| Scored with | mAP / NDS | mAP by range band | mIoU |
| Sensors | 6 radar (4D, 360°), 6 LiDAR, 4 camera | 10 radar (4D), 10 LiDAR, 11–15 camera | 3 LiDAR, 7 camera, 6 radar *(radar not distributed)* |
| Range | >230 m | 400 m 3D / 1000 m 2D | ~62.9% of points within 25 m |
| Licence | CC BY-NC-SA 4.0 | Torc Non-Commercial | CC BY-SA 4.0 *(most permissive)* |
| Access | Open, AWS S3 | Hugging Face, licence gate | Open download |
| Size | 9.6 GB mini / 560 GB trainval | 28.8 TB full | 3.3 GB val / ~62 GB all |

**STONE** was a fourth candidate — the only off-road dataset with annotated 4D radar.
**Dropped 29 August:** a single 346 GB download with no sample split, no toolkit in its
repository, and maintainers who have not answered a GitHub issue since March.

### Why the split makes sense

TruckScenes is the **core modality comparison**, because it is the only dataset where
radar and LiDAR see the same scenes with the same ground truth. TruckDrive is where the
**interesting failure** happens — published results show 31–99% degradation past 150 m.
GOOSE is the **client's actual interest**, and the only one we can currently work on
end to end.

---

## 5. How a dataset and its devkit work together

Every dataset follows the same shape, and differs only in the details.

```
   download archive           devkit                    your code
   ----------------           ------                    ---------
   sensor files      ──►  loader / API      ──►   analysis, rendering,
   + label files          (parses formats,        model input
   + metadata JSON         pairs frames,
                           handles calibration)
```

**The devkit's job** is to hide the file formats. Without one you would be parsing
binary point clouds and matching timestamps by hand.

**What differs between the three:**

| | TruckScenes | TruckDrive | GOOSE |
|---|---|---|---|
| Install | `pip install truckscenes-devkit` | Clone repo, per-component setup | Clone repo, plain Python |
| Entry point | `from truckscenes import TruckScenes` | Component scripts | Direct file reads + helper scripts |
| Schema | nuScenes-derived JSON | Own per-scene layout | SemanticKITTI-style `.label` |
| Viewer | Jupyter tutorial notebook | `dataset_viewer` (PyQt5 + Open3D) | vispy visualiser |
| Model code | Not bundled | `mmdet_project` (MMDetection3D) | Pointcept / PTv3 |
| Devkit licence | Apache 2.0 | Apache 2.0 | MIT |
| Maturity | **Highest** — pip-installable, documented, tutorial | Repo-only, per-component READMEs | Middle — works, some rough edges |

**Practical consequence:** TruckScenes is the easiest to start on and its nuScenes
lineage means existing models often port across. TruckDrive's tooling is heavier and
pulls in MMDetection3D, which is CUDA-dependent and version-sensitive. GOOSE sits in
between — trivial to load, but its published baseline needs CUDA.

### The thing that bites everyone

**Datasets ship more than one label taxonomy.** GOOSE has a 64-class set *and* an
8-class challenge remap, in separate downloads. Colouring one with the other's map
fails **silently** — no error, just a wrong picture.

The GOOSE challenge-label download also contains 1,368 validation labels of which only
961 belong to base GOOSE; the other 407 are from GOOSE-Ex, a different platform. Pairing
those naively means silently evaluating across two different sensor suites.

Assume every dataset has a trap like this and go looking for it.

---

## 6. Tech stack by job

Two views: the **dataset pairs** we are working in now, and the **epics** we return to
once every dataset is running.

### 6.1 Shared by everyone

| Layer | What | Why |
|---|---|---|
| Language | **Python 3.11** | The devkits require `>=3.8,<3.12` |
| Environment | venv at `~/.venvs/radar` | Outside the project folder: the path contains spaces, which breaks console scripts on macOS |
| Core libraries | `numpy`, `matplotlib`, `pyyaml` | Everything else is per-job |
| Version control | Git + GitHub, PR review required | 1 approval, no force pushes, stale reviews dismissed |
| Guardrail | `scripts/session_check.py` | Run before every session and commit |
| OS | macOS and Windows both in use | Every documented command is given for both |

**Nobody commits datasets.** Data lives outside the repo — `~/datasets/` on macOS,
`C:\goose\` on Windows.

### 6.2 Damien & Ricky — GOOSE

| | Damien | Ricky |
|---|---|---|
| Focus | Rendering, figures, results infrastructure | Statistics, metrics, model runs |
| Stack | `numpy`, `matplotlib`, `vispy` | `numpy`, `pytest`, Pointcept / PTv3 |
| Hardware | macOS, Apple Silicon — **no CUDA** | Windows + WSL 2, **GTX 1660 6 GiB** |
| Owns | `scripts/goose_render_frame.py`, `goose_traversability.py`, `goose_client_figure.py`, `results/`, the GOOSE survey | `scripts/goose_stats.py`, `traversability_map.csv`, `experiment-log/`, `docs/metrics-definitions.md` |

Ricky's is the **only CUDA machine on the team**, which is why model runs go to him.
PTv3 runs there in FP32 at ~19 s/frame — a full 961-frame validation is about **5 hours**
of sustained GPU load.

### 6.3 Aiden & Fatima — MAN TruckScenes

| | |
|---|---|
| Stack | `truckscenes-devkit` (pip), JupyterLab, `open3d`, `awscli` |
| Data | AWS S3, no account needed. Mini split ~9.6 GB |
| Environment | Same Python 3.11 venv |
| Notes | The easiest devkit to install. Tutorial notebook is the fastest way in |

### 6.4 Fariya & Kelsey — TruckDrive

| | |
|---|---|
| Stack | Repo-cloned devkit, `dataset_viewer` (PyQt5 + Open3D ≥0.18), `aria2` for fast downloads |
| Data | Hugging Face, **licence acceptance required**. Mini split via CloudFront |
| Heavier path | `mmdet_project` uses **MMDetection3D** — CUDA, version-sensitive, needs a GPU |
| Notes | Do the viewer first. Leave MMDetection3D until a GPU is available |

### 6.5 Where the epics land, once datasets are running

| Epic | Owner | Technical stack |
|---|---|---|
| A — Simulation & presentation | Fariya | Ubuntu, ROS 2 Humble, Autoware; React + FastAPI for the dashboard |
| B — Fundamentals, off-road, benchmarking infra | Damien | Python, the results store and validators, comparison plots |
| C — 4D RADAR detection & documentation | Fatima | Devkits, radar literature, experiment documentation |
| D — Dataset exploration & visualisation | Kelsey | Devkits, Open3D / vispy, point-cloud rendering |
| E — Industry & technology review | Aiden | Literature and industry sources; the evaluation framework |
| F — Evaluation framework & reproducibility | Ricky | Python, statistics, metric definitions, experiment logs |

**Autoware note.** It targets **Ubuntu + ROS 2**, not macOS or Windows natively. It
needs a Linux machine, dual boot, VM or Docker. GOOSE is currently the cheapest way in
because it ships ROS bags natively — though they are **ROS 1**, so conversion is still
needed.

---

## 7. How the pieces connect

Three pairs producing results in parallel is exactly how three incompatible formats get
created. Two shared pieces stop that.

### `docs/metrics-definitions.md` — define it before you report it

Every metric used anywhere is defined here first, with its rules: what mIoU averages
over, why absent classes are excluded rather than scored zero, and that segmentation and
detection metrics **never share a table**.

### `results/` — one place, one format

One JSON file per result, under `results/records/`. Validated by
`scripts/validate_result.py`.

```bash
python scripts/validate_result.py            # check every record
python scripts/validate_result.py --summary  # see what we have
```

Three fields can **never** be blank — `dataset`, `sensor_configuration`,
`annotation_schema`. That is decision D-01 enforced at the data layer rather than
trusting whoever reads a chart in week 12. A metric name not already in
`metrics-definitions.md` is **rejected**.

**Failures are records too.** A non-success status requires `error`, `attempted_fixes`,
`blocker` and `recommendation`. Adrian asked for exactly this.

### Working rules

1. **If it isn't recorded, it didn't happen.** Dataset facts go in a survey; experiment
   attempts go in `experiment-log/`; results go in `results/records/`.
2. **Comparison stays within a dataset and within a task type** (D-01, D-02).
3. **Pull request review for everything**, by someone other than the author.
4. **Decisions that constrain the work** go in `decision-log.md`.

---

## 8. Where things live

| Path | What |
|---|---|
| `README.md` | Repo entry point, team, layout |
| `docs/PROJECT-HANDBOOK.md` | **This document** |
| `decision-log.md` | Every decision with its reasoning (D-01…) |
| `DATASET_OVERVIEW.md` | Pre-kickoff research on TruckScenes and TruckDrive |
| `SETUP.md` | The working environment |
| `docs/dataset-survey-template.md` | Fixed-checklist survey, one per dataset |
| `docs/dataset-surveys/` | The surveys themselves |
| `docs/metrics-definitions.md` | Every metric, defined once |
| `docs/evidence/` | Rendered figures |
| `results/` | The results store and its schema |
| `experiment-log/` | One entry per experiment attempt |
| `templates/` | Comparison record and experiment log templates |
| `client-notes/` | Short findings notes for Adrian and Fabian |
| `scripts/` | Utility scripts |
| `GOOSE - Ricky+Damien/` | That pair's workplan and findings |

Sprint 1 deliverables (Scope of Work, Risk Register, Acceptance Tests, Set of Stories)
live in the team OneDrive. Risk IDs (R-xx), acceptance criteria (P-x) and story IDs
(DZ-n, RY-n) referenced around the repository point there.

---

## 9. Current status — 4 September 2026

| | |
|---|---|
| **GOOSE** | Working end to end. Full split measured, traversability map built, client figure produced, PTv3 confirmed to run on a 6 GiB GPU |
| **TruckScenes** | Devkit installed, exploration under way |
| **TruckDrive** | In progress |
| **STONE** | Dropped |
| **Kaya (HPC)** | **Blocked** — awaiting Adrian to complete the application |
| **First model run** | Done, partially. PTv3 on GOOSE, 10 of 961 frames, stopped deliberately |

### The honest gaps

- **No complete benchmark number yet.** The one model run is 1% of a split and recorded
  as diagnostics, not metrics.
- **Kaya is the compute blocker**, and it depends on one person outside the team.
- **Two acceptance tests need a human**, not an agent: someone outside the GOOSE pair
  reading the client figure and the survey cold, and saying what they think they show.
