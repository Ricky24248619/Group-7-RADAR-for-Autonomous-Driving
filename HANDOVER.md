# Handover — RADAR for Autonomous Driving (Group 7)

CITS3200 · Semester 2 2026 · written 6 October 2026 for the group that continues this work.

This is the entry point. It assumes you cannot ask any of us anything. It tells you:
- what we were asked and what we established;
- how to get set up and reproduce the main results;
- what is still open, and the traps that cost us time.

Each section links to the detailed document rather than repeating it.

---

## 0. Start here

**First hour, in this order:**

1. **This file**, all of it.
2. [`docs/final-findings-oct03.md`](docs/final-findings-oct03.md): the team's final sensor and terrain findings (D01–D23), each with evidence and limits.
3. [`evidence/Report_Final_Final_v2.docx`](evidence/Report_Final_Final_v2.docx): the results walkthrough, one figure per result, with its limitation.
4. [`decision-log.md`](decision-log.md): the decisions that constrain the work (D-01…D-09). **D-01** (compare only within a dataset) and **D-04** (the long-range question) matter most.
5. [`docs/HANDOVER-TOOLING.md`](docs/HANDOVER-TOOLING.md): the shared tooling (results store, validators, CI) and where it is weak.

**Then check your checkout works**, with no dataset, GPU or devkit needed:

```bash
git clone https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving.git
cd Group-7-RADAR-for-Autonomous-Driving
python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-ci.txt
python scripts/validate_result.py
python scripts/validate_experiment_logs.py
python -m unittest discover -s tests
```

**Use Python 3.11.** Later versions change a JSON error message the tests assert on, and skip some test modules.

---

## 1. The project in brief

| | |
|---|---|
| Client | Adrian Boeing |
| Technical mentor | Fabian Deuser |
| Goal | An evidence-based comparison of radar, LiDAR and camera perception for **autonomous trucking**: run existing open-source models on public datasets, record everything reproducibly, and hand over a body of work a future team can extend |
| Headline question (D-04) | Do current models fail beyond about 150 m, and does 4D radar degrade less than LiDAR at that range? Report by range band, never as one number |
| Client interest | Also off-road and unstructured terrain (D-03, D-05) |
| Ground rules | Compare within a dataset and task, never across datasets (D-01, D-02). Negative results count: failures are recorded as findings |
| IP | Creative Commons / open source. **Note:** TruckScenes, STONE and TruckDrive data licences are **non-commercial**, so check reuse before publishing derived data |

We worked in dataset pairs: **TruckScenes** (Aiden, Fatima), **TruckDrive** (Fariya, Kelsey) and **GOOSE/STONE/RADIATE** (Damien, Ricky).

---

## 2. What we established

Two kinds of result appear below. Keep them apart:

- **Sensor support / coverage:** did at least one radar or LiDAR return land inside a human-labelled object? No model is involved. It shows whether evidence is *present*.
- **Detection:** did a trained model *find and correctly label* the object? It is scored with mAP.

### 2.1 Long range (D-04): TruckDrive, the only dataset that can test it

- **LiDAR carries far more evidence on distant vehicles than radar.** At 200–400 m:
  - five scenes, 504 vehicle observations: LiDAR **80.36%**, radar **37.50%**;
  - two further clips: LiDAR **31 of 36**, radar **12 of 36**.
- **This is sensor support, not detection.** Radar occasionally has evidence where LiDAR has none (D03).
- **No available model can test recognition at 200–400 m.** The inspected pretrained radar/LiDAR pair crops its input at about **70 m**; 0 of 504 distant vehicle centres fall inside it (D10).
- **Torc's own TruckDrive paper reaches the same conclusion:** current models "do not generalize to ranges beyond 150 meters".

**Evidence:**
- [`docs/truckdrive-multiscene-result.md`](docs/truckdrive-multiscene-result.md)
- [`docs/detector-compatibility-decision.md`](docs/detector-compatibility-decision.md)
- [`evidence/truckdrive/`](evidence/truckdrive/)

### 2.2 Detection on TruckScenes: the only scored detector results

Every model was pretrained on nuScenes (a car in city traffic) and run **zero-shot**, with no training on trucks. The test set is the official `mini_val` split: 80 samples, 2,088 scored objects.

| Sensor input | Model | mAP | Notes |
|---|---|---|---|
| **All 6 LiDARs merged** | PointPillars | **0.1005** | Model sees 94.9% of objects. **Car AP 0.41**, traffic cone 0.26, trailer 0.11, **truck 0.009** |
| Best single LiDAR (`LIDAR_LEFT`) | PointPillars | 0.0555 | Level side sensor; sees 69.5% of objects |
| 4 cameras | FCOS3D | 0.0046 | Boxes point the right way but at the wrong depth |
| 6 radars | — | — | **No radar detector could run**: one candidate has no published checkpoint, the other is blocked by a manual download and missing preprocessing config |

**How to read these scores:**

- **Trucks are a recognition problem, not a visibility problem.** The merged LiDAR cloud has points on all 392 scored trucks, yet truck AP is 0.009. The checkpoint does not recognise heavy trucks and trailers, which its city training lacked.
- **The camera result is most likely a depth problem.** Truck cameras sit about 2.1 m high against nuScenes' 1.5 m, and depth errors grow with range. The cause is not fully isolated.
- **mAP on `mini_val` cannot exceed about 0.58.** The evaluator averages 12 classes:
  - four (bus, other vehicle, bicycle, animal) have **no objects** in `mini_val`, and the devkit scores an empty class as 0;
  - traffic signs (166 objects) are not a nuScenes class, so no nuScenes model can score them.

**Evidence:**
- LiDAR: [EXP-0024](experiment-log/0024-truckscenes-lidar-full-split.md), [record 0029](results/records/0029-truckscenes-lidar-detector-full-split.json), [`docs/evidence/pr63-channel-comparison/`](docs/evidence/pr63-channel-comparison/)
- Camera: [EXP-0010](experiment-log/0010-fcos3d-truckscenes-4camera.md), [EXP-0016](experiment-log/0016-fcos3d-4camera-result-audit.md)
- Radar: [EXP-0020](experiment-log/0020-truckscenes-radar-detector-feasibility.md), [`docs/truckscenes-radar-detector-decision.md`](docs/truckscenes-radar-detector-decision.md)

### 2.3 Near range and weather: TruckScenes, RADIATE

- **Radar coverage depends on the object type** (0–25 m):
  - trucks: radar 99.12%, LiDAR 100%;
  - adult pedestrians: radar 67.66%;
  - traffic cones: radar 39.00%.

  A truck-dominated average hides weak targets (D02).
- **Radar coverage of the same cars falls with distance**, from 80% at 0–50 m to 52% at 50–100 m, while LiDAR stays above 98%.
- **No sensor wins in every weather.**
  - In a small RADIATE fog sample, radar showed strict contrast on 9 of 19 vehicles at 50–75 m, where LiDAR had above-ground returns on none.
  - In TruckScenes rain and snow recordings, LiDAR kept 95–99% car coverage at 50–100 m and radar 42–61% (D04).
- **TruckScenes' recorded radar stops at about 189.5 m on every channel**, so it cannot test 200–400 m.
- **Timing correction matters.** Correcting LiDAR point times cut apparent radar-only observations from 185 to 39 (D09).

**Evidence:**
- [`docs/client-level-conclusions-oct01.md`](docs/client-level-conclusions-oct01.md)
- [`docs/client-comparison-brief.md`](docs/client-comparison-brief.md)
- [`docs/radiate-fog-pilot.md`](docs/radiate-fog-pilot.md)
- [`TruckScenes - Fatima/`](TruckScenes%20-%20Fatima/)

### 2.4 Off-road terrain: GOOSE, STONE

- **GOOSE** (LiDAR terrain segmentation, PTv3 at a reduced setting on a GTX 1660):
  - ground is recognised as ground 97–99% of the time;
  - the failure that matters is **obstacles labelled ground**: low rocks, tall grass (49% called ground), walls;
  - a larger attention context helps most cases but costs about 28% more time and made one case worse (D05–D08, D12);
  - map conversion can hide hazards: a majority-ground rule discards a minority hazard even with correct labels (D13);
  - nearby maps have large unobserved gaps (D18), and a footprint check removes many single-cell "ground" positions (D21).
- **STONE** is the only off-road dataset with labelled 4D radar. LiDAR supports nearly all terrain; radar sees little near-ground terrain. Radar calibration is unresolved, and one result flips with the calibration convention (G-13).
- **Water and mud are essentially absent** from the samples we examined (D14).

**Evidence:**
- [`docs/goose-multiscenario-terrain.md`](docs/goose-multiscenario-terrain.md)
- [`docs/goose-failure-causes.md`](docs/goose-failure-causes.md)
- [`docs/stone-environments-followup.md`](docs/stone-environments-followup.md)
- [`GOOSE - Ricky+Damien/`](GOOSE%20-%20Ricky+Damien/)

### 2.5 Industry check (AD-3)

We checked our findings against what Aurora, Kodiak, Torc, Plus, Waabi and Gatik publish.

- **Industry agrees** that long range relies on LiDAR, that models fail past 150 m, and that nobody runs radar-first perception.
- **Two tensions to raise with the client:**
  - weather: industry treats radar as *the* bad-weather sensor;
  - model transfer: Waabi claims zero-retraining transfer between trucks, without published evidence.

See [`docs/ad-3-industry-check.md`](docs/ad-3-industry-check.md) and the claims ledger in [`docs/domain-study/README.md`](docs/domain-study/README.md).

---

## 3. Datasets

Raw data is **never committed**; see `.gitignore`. Each dataset survey in [`docs/dataset-surveys/`](docs/dataset-surveys/) records sensors, licence and fit.

| Dataset | Role | Access | Licence | What it can and cannot answer |
|---|---|---|---|---|
| **MAN TruckScenes** | Paired 4D radar, LiDAR and camera on a truck; detection | Anonymous AWS S3 ([survey](docs/dataset-surveys/truckscenes.md)) | CC BY-NC-SA 4.0 | Radar vs LiDAR to about 190 m; detection. **Cannot** test 200–400 m |
| **TORC TruckDrive** | Long range: 3D labels to 400 m | Hugging Face, gated: accept the licence first ([overview](DATASET_OVERVIEW.md)) | Non-commercial | The only dataset for D-04. No compatible pretrained long-range detector |
| **GOOSE** | Off-road LiDAR terrain segmentation | Open ([survey](docs/dataset-surveys/goose.md)) | CC BY-SA 4.0 | Terrain labels. **No usable labelled radar** in the released assets |
| **STONE** | Off-road with labelled 4D radar | Public Drive link ([survey](docs/dataset-surveys/stone.md)) | CC BY-NC-ND 4.0 | Off-road radar vs LiDAR, short range. Radar calibration unresolved |
| **RADIATE** | Radar in fog | Public sample | CC BY-NC-SA 4.0 (figure use) | Fog pilot only; no clear-weather control |

**Storage:** TruckScenes `mini` is about 9.6 GB. The full `trainval` is about 560 GB compressed and needs about **1.1 TB** to download and extract. Arrange lab storage before planning any full-split or training work.

---

## 4. Getting set up to run experiments

`requirements-ci.txt` only runs the checks. Running experiments needs separate, heavier environments:

| Environment | For | How |
|---|---|---|
| TruckScenes devkit | Loading data, coverage analyses | [`SETUP.md`](SETUP.md); Fatima's [EXP-0007](experiment-log/0007-fatima-truckscenes-setup-visualisation.md); [acceptance check](TruckScenes%20-%20Fatima/ACCEPTANCE-CHECK.md) |
| `detection-env` (Python 3.11.9, torch 2.1.0+cpu, mmcv 2.1.0, mmdet 3.3.0, mmdet3d 1.4.0, truckscenes-devkit 1.2.0, numpy 1.26.4) | FCOS3D and PointPillars on TruckScenes. **CPU-only is enough**: about 4 minutes for all 80 samples with six LiDARs merged | Package versions in [record 0029](results/records/0029-truckscenes-lidar-detector-full-split.json); setup notes in [EXP-0006](experiment-log/0006-fcos3d-truckscenes-zeroshot.md) and [EXP-0019](experiment-log/0019-truckscenes-lidar-detector-feasibility.md) |
| GOOSE / PTv3 | Terrain segmentation | [EXP-0001](experiment-log/0001-ricky-windows-goose-setup.md), [EXP-0004](experiment-log/0004-goose-ptv3-partial-validation.md). **Needs an NVIDIA GPU**; we ran a reduced attention setting on a GTX 1660 |
| TruckDrive viewer | Visualisation, support analysis | Kelsey's [EXP-0005](experiment-log/0005-kelsey-truckdrive-setup-statistics.md); [`TruckDrive - Kelsey/`](TruckDrive%20-%20Kelsey/); viewer notes in the final report |
| STONE | Paired terrain pilot | [`requirements-stone.txt`](requirements-stone.txt), [`docs/stone-paired-terrain-pilot.md`](docs/stone-paired-terrain-pilot.md) |

**Model weights are not committed.** Download them and check their hashes:
- **PointPillars** `pointpillars_nus_20210826_225857-f19d00a3.pth`; SHA-256 in [`docs/truckscenes-lidar-detector-decision.md`](docs/truckscenes-lidar-detector-decision.md).
- **FCOS3D** `fcos3d_r101_caffe_fpn_gn-head_dcn_2x8_1x_nus-mono3d_20210715_235813-4bed5239.pth`; see EXP-0010.

### Reproduce the headline detection result (about 5 minutes, CPU)

```bash
python scripts/truckscenes_pointpillars_infer.py \
  --dataroot <man-truckscenes> --version v1.2-mini --split mini_val \
  --config <mmdet3d>/configs/pointpillars/pointpillars_hv_secfpn_sbn-all_8xb4-2x_nus-3d.py \
  --checkpoint <pointpillars .pth> --channel ALL --out results_all_lidars.json
python -m truckscenes.eval.detection.evaluate results_all_lidars.json \
  --dataroot <man-truckscenes> --version v1.2-mini --eval_set mini_val \
  --output_dir ./metrics_all --plot_examples 0 --render_curves 0
python scripts/pointpillars_channel_coverage.py --dataroot <man-truckscenes> --channel ALL
```

**Expected output:** mAP 0.1005, coverage 0.949. `--channel LIDAR_LEFT` (or any single channel) runs one sensor. The input is aligned upright by default.

Every other result has its exact commands in its experiment log (`experiment-log/NNNN-*.md`) and result record (`results/records/NNNN-*.json`).

---

## 5. How the repository works

| Path | What it is |
|---|---|
| `results/records/` | **One JSON per result**, including failures. The validator refuses blank `dataset`, `sensor_configuration` and `annotation_schema` (D-01). Add one with `python scripts/new_result.py` |
| `experiment-log/` | One entry per attempt (installs, runs, audits), from `templates/experiment-log-entry.md` |
| `docs/metrics-definitions.md` | Every reported metric, defined once. The validator rejects undefined metric names |
| `docs/dataset-suitability.md` | What each dataset can answer, plus the **gap register (G-xx)** |
| `decision-log.md` | Decisions D-01…D-09, with reasoning |
| `scripts/`, `tests/` | Analysis scripts, each tied to an experiment log; CI-safe tests that stub the heavy devkits |
| Pair folders (`TruckScenes - …`, `TruckDrive - Kelsey`, `GOOSE - Ricky+Damien`) | Each pair's working notes, statistics and summaries |
| `docs/domain-study/` | Literature and keynote entries and the claims ledger (append-only) |
| `Revised Sprint 1 Deliverables/` | Scope, risk register, acceptance tests and stories, with current status |

**Conventions:**
- Every change goes through a pull request with a reviewer.
- CI runs both validators and the tests on Ubuntu **and Windows**. Keep Windows: two line-ending bugs only failed there.

---

## 6. What is open, and what we would do next

In rough priority order. Gap IDs refer to the register in `docs/dataset-suitability.md`.

1. **Fine-tune a LiDAR detector on TruckScenes training data.**
   - **Why first:** trucks and trailers are fully visible but unrecognised. Training on truck data is the obvious fix, and the current pipeline (`--channel ALL`, upright frame) is ready to evaluate it.
   - **Needs:** a GPU and about 1.1 TB of storage for `trainval`.
   - **Scope:** training was outside our plan, so agree it with the client.
2. **Long-range detection on TruckDrive (D-04, G-11).** No published checkpoint accepts 200–400 m input. TruckDrive's own full-range LiDAR config covers 192 of the 504 distant vehicles, but has no matching pretrained radar model. A real answer to D-04 likely means training both modalities on TruckDrive with matched settings.
3. **A runnable radar detector (G-11, EXP-0020).**
   - L-RadSet needs a manual Google Drive download and its preprocessing config recovered.
   - K-Radar/RTNH has no published checkpoint.
   - Without one of these, no radar-vs-LiDAR *detection* comparison is possible.
4. **A matched weather test (D04).** Clear and adverse recordings from the same platform, before claiming either sensor "handles weather". Industry assumes radar; our small samples do not settle it.
5. **Cause of the 189.5 m radar boundary in TruckScenes (G-10).** All six channels agree to the micrometre, which suggests an acquisition setting. Worth asking MAN.
6. **Smaller open gaps:**
   - G-13: STONE radar calibration.
   - G-2: GOOSE 960 published vs 961 extracted frames.
   - G-8: the GOOSE radar model is not confirmed as 4D.
   - G-4: range-band protocol walkthrough.
7. **Off-road follow-ups:**
   - collect water, mud and rock examples (D14);
   - test whether camera appearance improves surface categories (D06);
   - evaluate hazard-preserving map conversion (D13);
   - check input compatibility before transferring to WildScenes or RELLIS-3D (D15).
8. **Process items never closed:**

   | Item | Status | Detail |
   |---|---|---|
   | **P-1** | Cannot be assessed | Client acceptance; no client response recorded |
   | **P-5** | Partly met | Reproduction by someone outside the team |
   | **P-6 / DS-4** | Partly met | Cold read of a figure and survey by an unfamiliar reader. The prompts are ready in [`docs/cold-read-protocol.md`](docs/cold-read-protocol.md) |
   | **P-8** | Partly met | D-04 answered for sensor support, not for detection |

   You are ideal candidates for P-5 and P-6: you are outsiders. Try reproducing one result from a clean clone and record what happened.

---

## 7. Traps that cost us time

- **Check a sensor's mounting before feeding it to a model.**
  - TruckScenes `LIDAR_TOP_FRONT` is a blind-spot sensor pitched about 56° downward and rated to 35 m. The two roof corner LiDARs are also pitched.
  - Models trained on nuScenes expect a level roof LiDAR.
  - Use `--input-frame upright` (the default) and prefer the side LiDARs or `--channel ALL`.
- **Coverage is not detection.** A return inside a box shows evidence is present, not that anything recognised it. Every figure states which it is.
- **Labels can favour a sensor.** TruckScenes and TruckDrive boxes were drawn largely from LiDAR, which favours LiDAR coverage. RADIATE labels come from radar.
- **The stock TruckScenes evaluator filters by class range (75 m or 150 m).** It produces no score beyond 150 m. On `mini_val`, mAP is capped at about 0.58 (see §2.2).
- **Timing and motion correction change the answer.** Correct per-point timestamps before attributing a difference to hardware (D09).
- **Windows:**
  - `spconv` has no Windows wheel, which rules out CenterPoint on CPU there;
  - write files with `newline=""` or the tests fail on Windows only;
  - call `curl.exe` explicitly in PowerShell.
- **Record-number collisions.** Two branches can both take "the next free number". CI catches it, but only after the second PR. Check `results/records/` and `experiment-log/` on `main` just before you open a PR.
- **Gated downloads.** TruckDrive needs the Hugging Face licence accepted first. One browser download from Hugging Face's CDN failed with Chrome's `ERR_BLOCKED_BY_CLIENT`, which usually means a browser extension; see [`docs/sprint3-dataset-findings.md`](docs/sprint3-dataset-findings.md). Try another browser or a command-line download.

---

## 8. People and provenance

| Member | Epic | Main areas |
|---|---|---|
| Fariya Zehrin | A | TruckDrive; results walkthrough (final report) |
| Damien Zhang | B | Off-road (GOOSE), shared tooling (results store, validators, CI), domain study |
| Fatima Sher | C | TruckScenes sensors, coverage and range bands, documentation |
| Kelsey Chen | D | TruckDrive data, visualisation and evidence |
| Aiden Blampain | E | TruckScenes detection (FCOS3D, PointPillars), radar/LiDAR detector feasibility, industry check (AD-3) |
| Ricky Yuen | F | Evaluation protocol, findings synthesis, GOOSE/STONE/RADIATE analyses, reproducibility |

Script ownership is listed in [`docs/HANDOVER-TOOLING.md`](docs/HANDOVER-TOOLING.md#provenance). Notes written for the client and mentor are in [`client-notes/`](client-notes/).
