# GOOSE Workplan — Ricky & Damien

**Fortnight:** 27 August – 10 September 2026 · **Sprint:** 2 · **Workstream:** WS2
**Owners:** Damien Zhang (DZ) · Ricky Yuen (RY)
**Repo:** `Ricky24248619/Group-7-RADAR-for-Autonomous-Driving`

---

## 0. How to use this file

This plan is written to be executed by a person working with an AI assistant. It is
**self-contained**: an assistant reading only this file, with no memory of prior
conversations, should be able to do the work.

- Tasks are `D1…D5` (Damien) and `R1…R5` (Ricky). **Do only your own tasks.**
- Each task states **Goal / Inputs / Steps / Done when / Output**. "Done when" is
  written as something checkable, not a feeling.
- File ownership is **disjoint by design** — see §6. Two people running AI agents in
  the same repo will produce merge conflicts unless nobody edits anyone else's files.
  If a task seems to need you to edit a file you do not own, stop and ask the owner.
- If a step fails, that is **data, not defeat**. Record it (§7) and continue. The
  client has stated explicitly that negative results count.

### Rules for AI assistants working on this plan

1. **Never commit dataset files.** The dataset lives outside the repo at
   `~/datasets/goose/`. Nothing under that path is ever added to git. If `git status`
   shows `.bin`, `.label`, `.zip` or `.png` frames from the dataset, stop.
2. **Never push to `main`.** Work on a branch, open a PR. `main` requires review.
3. **Never edit files owned by the other person** (§6).
4. **Do not install packages globally.** Use the project venv at `~/.venvs/radar`.
5. **Do not attempt to run the Pointcept / PTv3 baselines.** They require CUDA and a
   Docker image; the team's machines are Apple Silicon. This is recorded as risk R-08
   and is out of scope for this fortnight.
6. **Pin versions** in any install command you write into documentation.
7. **State uncertainty.** If a number is measured, say so. If it is from a paper, cite
   it. Do not present an estimate as a measurement.

---

## 1. What this fortnight is for

Two weeks of understanding GOOSE well enough to say what it can and cannot do for this
project — and producing one figure that shows the client their own question answered
with their own preferred dataset.

Background on why GOOSE matters and how it fits the project is in
[`GOOSE-CONTEXT.md`](GOOSE-CONTEXT.md). **Read that first if you have not.**

Three objectives, from the agreed scope:

| # | Objective | Tasks |
|---|---|---|
| 1 | **Understand the data** — look at it, measure it, describe it | D1, D2, R1, R2 |
| 2 | **Build the drivable / not-drivable view** — the client's actual question, rendered | R3, D3, D4 |
| 3 | **Write up what we learned** — survey §7, limitations, experiment logs | D5, R4, R5 |

**Explicitly deferred:** chasing the GOOSE radar. The maintainers have confirmed the
downloadable ROS bags carry a reduced sensor set, and there is no convenient download
for the full raw data. Since the radar is not obtainable, the question of whether the
Smartmicro units are 4D imaging has no practical effect on this fortnight's work.
*Recorded as a deliberate deferral, not an oversight — it remains an open item under
risk R-24 and in `decision-log.md` D-05.*

---

## 2. Environment setup

Damien's machine is already configured. **Ricky: run this first.**

### 2.1 Verify the venv

```bash
~/.venvs/radar/bin/python --version        # expect Python 3.11.x
```

If that fails, create it (needs Homebrew `python@3.11`; the devkit requires <3.12):

```bash
mkdir -p ~/.venvs
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv ~/.venvs/radar
~/.venvs/radar/bin/pip install numpy matplotlib pyyaml vispy==0.16.2 PyQt5 rosbags
```

> The venv lives outside the project folder deliberately. The project path contains
> spaces, which breaks console-script shebangs. See `SETUP.md` in the repo root.

### 2.2 Get the data (3.3 GB download, 3.3 GB extracted)

```bash
mkdir -p ~/datasets/goose/zips
cd ~/datasets/goose/zips
curl -# -L -O https://goose-dataset.de/storage/goose_3d_val.zip

mkdir -p ~/datasets/goose/goose_3d_val
cd ~/datasets/goose/goose_3d_val
unzip -q ~/datasets/goose/zips/goose_3d_val.zip
```

### 2.3 Verify

```bash
cd ~/datasets/goose/goose_3d_val
find lidar -name '*.bin' | wc -l      # expect 961
find labels -name '*.label' | wc -l   # expect 961
ls lidar/val/                         # expect 8 scenario directories
```

### 2.4 Clone the devkit (optional, for the official viewer)

```bash
cd "<repo root>"
git clone https://github.com/FraunhoferIOSB/goose_dataset.git
```

Already in `.gitignore`. Not required for any task below.

### 2.5 Smoke test

```bash
cd "<repo root>"
~/.venvs/radar/bin/python scripts/goose_render_frame.py \
  --root ~/datasets/goose/goose_3d_val --index 0 --out /tmp/smoke.png
```

Expect: `Found 961 annotated frames.`, a class distribution table, and a PNG written.
**If this works, your environment is correct.**

---

## 3. What you are working with

The **validation split** of GOOSE 3D: 961 annotated LiDAR frames across 8 scenarios,
covering summer, winter, rain and sun.

| Scenario | Season / condition |
|---|---|
| `2022-07-22_flight` | Summer |
| `2022-08-30_siegertsbrunn_feldwege` | Summer, field tracks |
| `2022-09-21_garching_uebungsplatz_2` | Autumn, training ground |
| `2022-12-07_aying_hills` | Winter, hills |
| `2023-01-20_aying_mangfall_2` | Winter |
| `2023-03-03_garching_2` | Early spring |
| `2023-05-15_neubiberg_rain` | Spring, **rain** |
| `2023-05-17_neubiberg_sunny` | Spring, **sunny** |

That last pair is unusually valuable — the same location two days apart in different
weather. If you want to say anything about weather sensitivity, that is the comparison.

**Data formats**
- Point clouds: `lidar/val/<scenario>/<name>_vls128.bin` — float32 `[x, y, z, intensity]`
- Labels: `labels/val/<scenario>/<name>_goose.label` — uint32, semantic id in the low
  16 bits, instance id in the high 16 bits
- Class names and colours: `goose_label_mapping.csv` in the split root — 64 classes

---

## 4. Known gotchas — read before you debug

These are already solved in `scripts/goose_render_frame.py`. They are listed so nobody
rediscovers them.

1. **Scans and labels do not share a filename stem.** Scans end `_vls128.bin`, labels
   end `_goose.label`. The join key is everything up to the final underscore.
2. **There are two different taxonomies and mixing them fails silently.** The devkit's
   `common/goose_kitti-visualizer.yaml` is an **8-class** challenge remap with **BGR**
   colours. The downloaded labels are the **full 64-class** set with **hex** colours in
   `goose_label_mapping.csv`. Using the 8-class map on 64-class labels renders most of
   the scene as unknown and raises no error.
3. **The devkit viewer expects `labels_challenge/`; the download ships `labels/`.**
4. **Camera and LiDAR are not reliably time-aligned.** The dataset authors have
   confirmed a bug in their export step: ground-truth masks for the camera image and
   the LiDAR sweep of the same frame **cannot be matched by projection using the
   published extrinsics** ([issue #18](https://github.com/FraunhoferIOSB/goose_dataset/issues/18)).
   **Do not attempt camera↔LiDAR fusion on this data.** Some LiDAR scans are also
   missing sections, and at least one RGB frame is out of sequence.

---

## 5. Schedule

| | Damien | Ricky |
|---|---|---|
| **Week 1** (27 Aug – 3 Sep) | **D1** frame sweep · **D2** refactor renderer for class grouping | **R1** environment + smoke test · **R2** dataset statistics · **R3** traversability mapping |
| **Checkpoint** — 3 Sep | Both: 30-minute sync. R3 must be delivered here; D3 depends on it. | |
| **Week 2** (4 – 10 Sep) | **D3** traversability renderer · **D4** client figure · **D5** survey §7 + limitations | **R4** experiment log entries · **R5** metrics definitions for segmentation |
| **End** — 10 Sep | Joint PR, each reviewing the other's files | |

**The one cross-person dependency is R3 → D3.** Ricky delivers the traversability
mapping by the 3 September checkpoint; Damien implements against it in week 2. Damien's
week-1 tasks are deliberately independent so nobody is blocked.

---

## 6. File ownership — do not cross these lines

| Owner | Files |
|---|---|
| **Damien** | `scripts/goose_render_frame.py` · `scripts/goose_traversability.py` · `docs/dataset-surveys/goose.md` · `docs/evidence/**` · `GOOSE - Ricky+Damien/findings-damien.md` |
| **Ricky** | `GOOSE - Ricky+Damien/traversability_map.csv` · `GOOSE - Ricky+Damien/dataset-statistics.md` · `experiment-log/**` · `docs/metrics-definitions.md` |
| **Shared — edit only at the checkpoint, together** | `GOOSE - Ricky+Damien/WORKPLAN.md` · `GOOSE - Ricky+Damien/SUMMARY.md` |

**Branches:** `goose/damien-week1`, `goose/ricky-week1`, etc. One PR each at the end of
each week, or one joint PR at the end of the fortnight — agree at the checkpoint.

---

## 7. Recording failures

Anything that does not work gets an entry in `experiment-log/` using
`templates/experiment-log-entry.md`. Include the **exact** error text, copy-pasted, not
paraphrased — paraphrased errors are unsearchable. Ricky owns that directory; if you
are Damien and you hit a failure, write it up in `findings-damien.md` and Ricky will
fold it in at the checkpoint.

---
---

# TASKS — DAMIEN

## D1 — Frame sweep across all 8 scenarios

**Goal.** Build visual intuition for what GOOSE actually contains, and produce a
contact sheet that shows the seasonal and terrain range in one image.

**Inputs.** `~/datasets/goose/goose_3d_val`, `scripts/goose_render_frame.py`

**Steps.**
1. Render at least two frames from each of the 8 scenarios. Frame indices are ordered
   by scenario, so sample across the full 0–960 range rather than clustering.
2. Look at them. Note where the class mix changes with season, where the LiDAR looks
   sparse or broken, and any frame that looks wrong.
3. Write observations into `findings-damien.md` — at least one line per scenario.
4. Build a contact sheet: a single image tiling one bird's-eye view per scenario,
   labelled with scenario name and season.

**Done when.** `docs/evidence/goose_contact_sheet.png` exists and shows all 8
scenarios; `findings-damien.md` has an observation per scenario.

**Output.** `docs/evidence/goose_contact_sheet.png` · `findings-damien.md`

> Guidance for the assistant: extend `goose_render_frame.py` with a `--contact-sheet`
> mode, or write a small separate script. Do not duplicate the loading logic — import
> from the existing module.

---

## D2 — Refactor the renderer to support class grouping

**Goal.** Make the renderer able to colour points by an arbitrary grouping of the 64
classes, so D3 can drop in Ricky's traversability mapping without a rewrite.

**Inputs.** `scripts/goose_render_frame.py`

**Steps.**
1. Extract the class-mapping load into a function that accepts either the 64-class
   `goose_label_mapping.csv` **or** a grouping file with columns
   `label_key, class_name, group_name, group_colour` (the format R3 will produce —
   see §8).
2. When a grouping file is supplied, remap each point's class id to its group before
   colouring, and show group names in the legend.
3. Keep the existing 64-class behaviour as the default. **Do not break it** — D1's
   output must still reproduce.

**Done when.** Both of these run and produce different, correct images:
```bash
~/.venvs/radar/bin/python scripts/goose_render_frame.py --root ~/datasets/goose/goose_3d_val --index 0 --out /tmp/a.png
~/.venvs/radar/bin/python scripts/goose_render_frame.py --root ~/datasets/goose/goose_3d_val --index 0 --group-map <any-valid-grouping.csv> --out /tmp/b.png
```

**Output.** Updated `scripts/goose_render_frame.py`

> Until R3 lands, test with a throwaway two-group mapping you write yourself. Delete it
> afterwards — the real one is Ricky's deliverable.

---

## D3 — Traversability renderer *(depends on R3)*

**Goal.** Render GOOSE frames coloured by traversability rather than by material —
the picture that answers *"what can I drive over, what can I crash into."*

**Inputs.** `traversability_map.csv` from R3, refactored renderer from D2

**Steps.**
1. Create `scripts/goose_traversability.py` (or a documented flag on the existing
   script) that renders using Ricky's mapping.
2. Render the same frames as D1, in traversability colours.
3. **Sanity check every one.** Ask of each: does the drivable region look like
   somewhere a vehicle could actually go? If a gravel track reads as non-traversable,
   the mapping is wrong — take it back to Ricky rather than patching it in code.
4. Record any class whose assignment you disagree with in `findings-damien.md`.

**Done when.** Traversability renders exist for all 8 scenarios and the drivable
region is visually coherent in at least 6 of them. Disagreements are recorded, not
silently fixed.

**Output.** `scripts/goose_traversability.py` · `docs/evidence/goose_traversability_*.png`

---

## D4 — The client figure

**Goal.** One image suitable for putting in front of Adrian and Fabian without
narration.

**Steps.**
1. Pick the frame that most clearly shows a drivable route through non-drivable
   surroundings.
2. Produce a two-panel figure: the 64-class material view beside the traversability
   view, same frame, same viewpoint.
3. Caption it in plain language — what the client is looking at and why it matters.
   No jargon, no metric names.

**Done when.** A single PNG a reader unfamiliar with the project can interpret in
under 60 seconds. Test it on a teammate outside this pair.

**Output.** `docs/evidence/goose_client_figure.png`

> This is the artefact most likely to restart the conversation with Adrian. It shows
> their preferred dataset answering the question they described at kickoff. Spend
> proportionate care on it.

---

## D5 — Survey §7 and limitations

**Goal.** Update `docs/dataset-surveys/goose.md` with what the fortnight established.

**Steps.**
1. Rewrite §7 "Fit for this project" now that GOOSE is actually understood — what it
   can do, what it cannot, and the verdict.
2. Add a **Limitations** subsection covering: camera↔LiDAR temporal misalignment
   (authors confirmed, fusion not viable), reduced-sensor ROS bags, ROS 1 not ROS 2,
   radar not obtainable, incomplete LiDAR scans.
3. Link the evidence images produced in D1, D3 and D4.
4. Update the §0 metadata block — date, status.

**Done when.** A teammate who has not touched GOOSE can read §7 and correctly state
what the dataset is for and what it cannot answer.

**Output.** Updated `docs/dataset-surveys/goose.md`

---
---

# TASKS — RICKY

## R1 — Environment and smoke test

**Goal.** Get a working GOOSE environment on your machine and confirm it independently
of Damien's.

**Steps.** Follow §2 end to end. Run the §2.5 smoke test.

**Done when.** The smoke test prints `Found 961 annotated frames.` and writes a PNG.

**Output.** An experiment-log entry recording the setup — including anything that did
not work first time. This is the first clean-machine reproduction of Damien's setup,
which makes it evidence for acceptance criterion **P-5**. Treat it as a real result.

> If setup fails on your machine, that failure is more valuable than a success. Record
> the exact error.

---

## R2 — Dataset statistics

**Goal.** Quantify what Damien is looking at. Move from "it looks like mostly grass"
to measured numbers.

**Steps.** Write a script that walks all 961 frames and computes:
1. Class frequency across the whole split — total points per class, share of all points
2. Per-scenario class distribution — how does the mix change across season and weather
3. Points per frame: min, max, mean, median
4. Radial range distribution — what fraction of labelled points fall in 0–25 m,
   25–50, 50–100, 100–150, 150 m+
5. Which of the 64 classes are effectively absent (say, under 0.01% of points)

**Done when.** `dataset-statistics.md` contains all five, as tables, with the script
that produced them committed alongside.

**Output.** `GOOSE - Ricky+Damien/dataset-statistics.md` + the script

> Item 4 matters beyond this fortnight. Damien measured labelled points out to roughly
> ±200 m, which was unexpected. Knowing the *density* at range tells the team whether
> GOOSE has anything to say about long-range perception, which is decision **D-04**.
>
> Item 5 matters for honesty: a 64-class dataset where 20 classes barely appear is
> effectively a 44-class dataset, and any mIoU averaged over all 64 is misleading.

---

## R3 — Traversability mapping ⚠️ **blocks D3 — deliver by 3 September**

**Goal.** Decide, for each of GOOSE's 64 classes, whether a vehicle can drive on it.
This is the judgement at the centre of the fortnight, and it is deliberately yours
rather than buried in Damien's code — so it is explicit, reviewable and arguable.

**Use STONE's four-class scheme**, so our terminology matches the off-road literature
and carries over if the STONE strand ever unblocks:

| ID | Class | Meaning |
|---|---|---|
| 0 | **Free** | Open space, no surface — sky, void |
| 1 | **Traversable** | Drive on it normally — asphalt, gravel, soil, low grass |
| 2 | **Potentially Traversable** | Possible but uncertain or risky — high grass (hides what's beneath), shallow debris, moss |
| 3 | **Non-Traversable** | Do not — tree trunks, buildings, water, rocks, people, vehicles |

**Steps.**
1. Read the full class list in `goose_label_mapping.csv` (64 entries).
2. Produce `traversability_map.csv` with columns:
   `label_key, class_name, traversability_id, traversability_name, rationale`
3. **Every row needs a one-line rationale.** The hard cases are the point: is
   `high_grass` traversable or potentially traversable? Is `snow` traversable, or does
   it hide what's underneath? Is `water` always non-traversable, or does depth matter?
   Write your reasoning — a reviewer must be able to disagree with a specific line.
4. Flag the genuinely uncertain ones in a "contested" section for the checkpoint.

**Done when.** All 64 classes are assigned, each with a rationale, and the file loads:
```bash
~/.venvs/radar/bin/python -c "import csv; r=list(csv.DictReader(open('GOOSE - Ricky+Damien/traversability_map.csv'))); print(len(r), 'rows'); assert len(r)==64"
```

**Output.** `GOOSE - Ricky+Damien/traversability_map.csv`

> This is a real research contribution, not clerical work. There is no official
> GOOSE traversability mapping — you are creating the team's, and it becomes the thing
> we defend to Fabian. A defensible mapping with honest uncertainty beats a confident
> one that quietly guesses.

---

## R4 — Experiment log entries

**Goal.** Turn the fortnight into reproducible records, per your own RY-2 template.

**Steps.** Write entries in `experiment-log/` for: the environment setup (R1), the
statistics run (R2), and Damien's traversability rendering (D3) using his notes from
`findings-damien.md`. Create the `experiment-log/` directory — it is referenced by both
templates but does not exist yet.

**Done when.** At least three entries exist, each complete enough that a stranger could
repeat the work or understand why they cannot.

**Output.** `experiment-log/0001-*.md` onwards

---

## R5 — Segmentation metrics definitions

**Goal.** Fill in the segmentation half of `docs/metrics-definitions.md`, which is
currently marked "to define precisely (Ricky)".

**Steps.**
1. Define **mIoU** precisely: intersection over union per class, averaged over classes
   — and state explicitly which classes are included, since averaging over absent
   classes distorts the number (see R2 item 5).
2. Define per-class IoU and overall accuracy.
3. State the rule that segmentation metrics never share a table or axis with detection
   metrics — mIoU and mAP are not comparable. This is decision **D-02**.
4. Note which taxonomy any reported mIoU refers to: 64-class, 8-class challenge remap,
   or our 4-class traversability mapping. **They are three different numbers.**

**Done when.** Every metric the GOOSE work might report is defined before any number
is produced.

**Output.** Updated `docs/metrics-definitions.md`

---

## 8. Interface contract — `traversability_map.csv`

The one place the two halves of this plan meet. Ricky writes it; Damien's code reads
it. Neither should change the format without telling the other.

```csv
label_key,class_name,traversability_id,traversability_name,rationale
0,undefined,0,Free,"No surface assigned; excluded from traversability scoring."
23,asphalt,1,Traversable,"Paved surface, the reference drivable case."
50,low_grass,1,Traversable,"Short vegetation over ground; standard off-road driving surface."
51,high_grass,2,Potentially Traversable,"Drivable in principle but conceals the ground and any obstacle in it."
28,tree_trunk,3,Non-Traversable,"Rigid vertical obstacle; collision."
```

- `label_key` — integer, matches `goose_label_mapping.csv`
- `traversability_id` — 0–3, per the table in R3
- `rationale` — one sentence, required, never blank

Damien's renderer supplies the group colours; Ricky does not need to choose them.

---

## 9. Definition of done for the fortnight

- [ ] All 8 scenarios rendered and observed (D1)
- [ ] Renderer supports arbitrary class groupings without breaking 64-class mode (D2)
- [ ] All 64 classes assigned a traversability class with a written rationale (R3)
- [ ] Traversability renders exist and are visually coherent (D3)
- [ ] One client-ready figure a stranger can read in 60 seconds (D4)
- [ ] Dataset statistics measured, not estimated (R2)
- [ ] Survey §7 rewritten with limitations recorded (D5)
- [ ] Segmentation metrics defined before any metric is reported (R5)
- [ ] At least three experiment-log entries, including any failures (R4)
- [ ] One PR per person, each reviewed by the other

---

## 10. Out of scope this fortnight

Listed so an assistant does not helpfully wander into them.

| Not doing | Why |
|---|---|
| Running Pointcept / PTv3 baselines | Requires CUDA + Docker; team is on Apple Silicon (R-08) |
| Camera↔LiDAR fusion | Authors confirmed the frames are not reliably time-aligned (§4.4) |
| Downloading GOOSE 2D images | Not needed for traversability work on point clouds |
| Chasing GOOSE radar | Not obtainable — see §1 |
| Anything involving STONE | Parked pending ~645 GiB storage; see `docs/dataset-surveys/stone.md` |
| Training any model | The project runs existing models; it does not train from scratch |
| Autoware / ROS 2 integration | Belongs to FZ-1 and KL-3, not this pair |
