# GOOSE — Work Summary

**Damien Zhang and Ricky Yuen · CITS3200 Group 07 · 18 August – 5 September 2026**

A complete account of the GOOSE strand: what we set out to do, what we found, what we
got wrong and corrected, and what is left. Written to be read start to finish by someone
who was not involved.

---

## 1. Why GOOSE was in the project

Fabian named GOOSE at the kickoff meeting on 4 August, and Adrian's email of 11 August
asked that other datasets be used *"IN ADDITION to GOOSE — but not eliminating GOOSE"*.
So it was a client requirement before it was a technical choice.

It also happened to be a good match for what Adrian said he cared about:

> *"For a self-driving system, understanding the ground — what is ground, what is not
> the ground? What can I drive over? What can I crash into? ... In an open environment
> or a mining environment, there is an edge and you can drive off it and we don't want
> to crash."*

GOOSE is the German Outdoor and Offroad Dataset (Fraunhofer IOSB, ICRA 2024). A research
vehicle drove through forests, farmland, campus grounds and gravel tracks across four
seasons, and humans labelled every LiDAR point and camera pixel into 64 surface types —
`low_grass`, `gravel`, `tree_trunk`, `water`, and so on. That class list is close to a
written-out version of Adrian's question.

---

## 2. What we set out to do

The work agreed in `WORKPLAN.md` on 27 August and extended in `NEXT-STEPS.md`:

| | |
|---|---|
| Understand the data | Load it, look at it, measure it |
| Answer the client's question | Turn 64 material classes into drivable / not drivable, and render it |
| Write it up honestly | A survey stating what GOOSE can and cannot do |
| Run a model | The benchmarking exercise Adrian described |
| Build shared infrastructure | So three pairs on three datasets record results the same way |

We split by strength rather than by task. Damien took rendering, figures and the results
infrastructure; Ricky took statistics, metric definitions and — because he owns the
team's only NVIDIA GPU — the model runs.

---

## 3. What we did

### 3.1 Got it working, twice, on two operating systems

Damien installed the devkit on macOS (Apple Silicon) and rendered a frame. Ricky then
rebuilt the environment from that documentation on Windows and reproduced the same
961-frame result.

That second step tested the setup instructions on another operating system. Acceptance
criterion **P-5** requires reproduction by someone **outside the team**; Ricky's
reproduction is useful supporting evidence but does not satisfy that criterion. It also
turned up a portability bug: the renderer read config files with the platform default
encoding rather than explicit UTF-8.

**Three traps we hit and wrote down** so nobody repeats them:

1. The devkit viewer expects a `labels_challenge/` directory; the download ships
   `labels/`.
2. The bundled colour map is an 8-class remap in BGR; the downloaded labels are the full
   64-class set in hex. Mixing them **silently** renders most of a scene as unknown —
   no error, just a wrong picture.
3. Scans and labels do not share a filename stem (`_vls128.bin` against `_goose.label`).

### 3.2 Measured the whole thing

Rather than quote the paper, Ricky measured all 961 validation frames — **174,891,807
labelled points**.

| Range band | Share of labelled points |
|---|---|
| 0–25 m | **62.9%** |
| 25–50 m | 23.0% |
| 50–100 m | 10.3% |
| 100–150 m | 2.7% |
| 150 m+ | **1.1%** |

He also found **22 of 64 classes fall below 0.01% of points**, six of them with zero
points at all. That drove our mIoU rule: exclude classes absent from both ground truth
and predictions (zero union), but retain a class that the model incorrectly predicts.

### 3.3 Turned 64 material classes into four traversability levels

This is the piece that answers Adrian's question, and it is a judgement call rather than
a calculation. Ricky assigned every one of the 64 classes to one of four levels borrowed
from the STONE dataset — Free, Traversable, Potentially Traversable, Non-Traversable —
**with a written rationale for each**, plus a separate note listing the fourteen he
considered genuinely contested.

Keeping that judgement in a reviewable data file rather than buried in code means Fabian
can disagree with a specific line rather than the whole approach.

Damien rendered it across all eight scenarios. These views illustrate the team's
interpretation of human labels, including apparent corridors in woodland. They do not
establish a connected, vehicle-safe route or demonstrate a model predicting one.

### 3.4 Ran the published model

Adrian's framing was *"find some open source solutions... and basically we're just
trying to run them on the data sets."* GOOSE ships pretrained PTv3 weights with a
published score of **0.8096 mIoU**, so it was the natural place to start.

| | |
|---|---|
| Apple Silicon | The tested Pointcept/PTv3 path requires CUDA and cannot run on the machine's Apple GPU |
| GTX 1660, 6 GiB | Bounded inference completed in FP32; automatic mixed precision failed on a kernel-selection assertion |
| Bounded gates | Smallest frame (30,263 points) 8.6 s; largest (270,720 points) 35.4 s. No out-of-memory |
| Full attempt | **10 of 961 frames**, then stopped deliberately |
| Partial timing | 18.94 s/frame mean loop-body time over 10 frames, excluding dataloader yield time |

The successful gates establish bounded feasibility on 6 GiB, not full-split memory or
runtime feasibility. Multiplying the partial timing by 961 gives about 5.1 hours of
loop-body time; this is an extrapolation, not a measured end-to-end duration. Ricky
requested that sustained GPU load stop. The recorded stop reason was not an OOM error.

The run used the published checkpoint with a documented compatibility patch, FP32,
FlashAttention disabled, patch sizes 64 and one test augmentation. Those settings differ
from the published configuration, so a completed run would be a modified-protocol
result rather than a direct reproduction of the published 0.8096 mIoU.

The partial values are recorded as **diagnostics, not metrics**. Ten frames is 1% of a
split, and a partial score is not a benchmark.

### 3.5 Built infrastructure the other pairs use

Not GOOSE-specific, but it came out of this work:

- **`results/`** — one JSON record per result. `dataset`, `sensor_configuration` and
  `annotation_schema` can never be blank, which enforces decision D-01 at the data layer
  rather than trusting whoever reads a chart later. Failed runs are first-class records
  and must carry error, attempted fixes, blocker and recommendation.
- **`docs/metrics-definitions.md`** — every metric defined before it can be reported.
  The validator rejects a record using an undefined metric name.
- **`scripts/session_check.py`** — file-ownership and branch guard, so two people with
  AI assistants working one repository do not collide.
- **`docs/dataset-survey-template.md`** — the fixed checklist all three datasets are
  surveyed against.

---

## 4. What we found

### GOOSE supports the terrain question

The human material labels support a reviewable traversability interpretation. The
figure demonstrates that mapping, not automatic terrain recognition or vehicle safety.
Readability without narration has not been checked by someone outside the pair.

### GOOSE cannot answer the radar question

The vehicle carries **six radars with 360° coverage** — five Smartmicro UMRR-96 and one
UMRR-11. But:

- they are **not labelled**;
- they are **not in the annotated download**;
- the released raw files carry only a **reduced sensor set**, confirmed by the dataset
  authors on GitHub;
- the paper never calls them **4D imaging**, and their ranges suggest conventional
  automotive radar.

We deliberately stopped chasing this. If the radar cannot be obtained, whether it is 4D
has no practical bearing on the work.

### GOOSE cannot answer the long-range question

Only 3.8% of labelled points are beyond 100 m and 1.1% beyond 150 m. This distribution,
the segmentation task and the unavailable labelled radar comparison make GOOSE a poor
fit for D-04's long-range detection question. Point share alone does not establish the
absence of usable long-range examples or a model's performance there.

### A hidden trap in the challenge labels

The official challenge-label download contains **1,368 validation labels, of which only
961 belong to base GOOSE** — the other 407 are from GOOSE-Ex, a different platform with
a different sensor suite. Pairing them naively means silently evaluating across two
platforms, which is precisely the comparison D-01 exists to prevent.

---

## 5. Three things we got wrong, and corrected

Recorded because the corrections are more informative than the conclusions.

**1. "GOOSE has no radar."** The first draft of the survey said so, from the project
landing page's sensor list. The landing page lists only the *annotated* modalities. The
paper documents six radars. Corrected in place, with the error left visible.

**2. "The bird's-eye view is hiding the drivable track under canopy."** Damien tested
this with an absolute height threshold and concluded the woodland scenes were genuinely
blocked at ground level. That conclusion was wrong because the instrument was: on
sloping ground, absolute height does not separate canopy from terrain. Taking the lowest
return per 0.4 m ground cell roughly **halves** the apparent blocked share — one scene
went from 92% to 58% non-traversable.

**3. "The `bush` assignment is the difference between a drivable corridor and a blocked
scene."** Damien argued this in review. Rendering it both ways showed the Traversable
share is **identical to one decimal place** either way; `bush` only moves points between
*uncertain* and *blocked*. The claim was overstated and was withdrawn.

Ricky separately found **seven real defects** in Damien's code during review, including
a validator that accepted an invalid date, a non-existent evidence path and a
non-numeric metric value; and a loader that silently merged two incompatible label
taxonomies — the exact failure mode the workplan warned about.

---

## 6. What GOOSE is good for, in one table

| | |
|---|---|
| ✅ Off-road terrain interpretation | Human-label mapping and figure produced; readability check and vehicle-specific judgement remain |
| Possible Autoware demo input | Native ROS 1 bags exist; topic coverage, conversion and integration still need checking |
| ✅ On-road → off-road transfer, as target domain | Fabian's stated interest; needs a shared task formulation |
| ❌ Paired radar-versus-LiDAR benchmark | No obtainable labelled radar baseline for this task |
| ❌ D-04 long-range detection comparison | Segmentation task, no paired labelled radar, and sparse long-range coverage |
| ❌ Detection benchmarks | It is segmentation; scores cannot share a table with TruckScenes or TruckDrive |
| ❌ Sensor fusion | Camera and LiDAR are not reliably time-aligned — an export bug the authors confirmed |

---

## 7. Evidence

| Artefact | What it shows |
|---|---|
| `docs/dataset-surveys/goose.md` | The full survey: sensors, licence, limitations, fit |
| `docs/evidence/goose_client_figure.png` | The client-facing figure |
| `docs/evidence/goose_contact_sheet.png` | All 8 scenarios, 64-class view |
| `docs/evidence/goose_traversability_sheet.png` | All 8 scenarios as drivable / uncertain / blocked |
| `dataset-statistics.md` | Full measurement over 961 frames |
| `traversability_map.csv` + notes | All 64 class assignments with rationales |
| `findings-damien.md` | Working notes, including the corrections |
| `results/records/0001`–`0006` | Six result records: four successes, one failure, one partial |
| `experiment-log/0001`–`0004` | Environment setup, statistics, rendering, the model run |

**Six GOOSE result records and four GOOSE experiment logs.**

The companion Word file is generated from this Markdown with `scripts/build_handbook.py`
from the handbook PR (#22). Text and package integrity were checked after regeneration;
page-layout inspection remains pending because the review environment has no LibreOffice
renderer. Use the Markdown for content review until the Word layout has been checked.

---

## 8. What is left

**For anyone continuing GOOSE:**

- **A complete PTv3 run**, only if the client still needs it and suitable compute is
  approved. Fix the protocol and measure end-to-end requirements first; the 5.1-hour
  extrapolation does not establish full-run time or memory needs. Do not restart the
  full local GPU run without Ricky's explicit approval.
- **Settle the mIoU definition first.** The reference implementation averages over
  classes with zero union; ours excludes them. The numbers can differ when such classes
  occur. State the taxonomy and evaluated class set, as well as the runtime changes,
  before comparing any score with a published result.
- **The 2D image split** has not been evaluated by this pair.
- **The raw ROS bags**, if the authors ever publish the full sensor set.
  `scripts/goose_bag_topics.py` is ready to check them in one command.

**Not done, and honest about it:**

- No complete benchmark number exists.
- P-5's reproduction by someone outside the team is not evidenced by our pair's work.
- The outside-pair cold read of the figure and survey — required by our own acceptance
  tests **P-6**, D4 and D5 — **was not performed**. The closeout proposal records that
  it was dropped for time; this is an unmet check, not a pass. The team should record
  acceptance of that omission or complete the check before treating closeout as agreed.

---

## 9. What we would tell the next team

**Assume every dataset ships more than one label taxonomy, and go looking for the trap.**
GOOSE has two, in separate downloads, and mixing them fails silently. Its challenge
labels mix two platforms. We were caught by both.

**Check prerequisites before installing anything.** The Apple Silicon CUDA blocker cost
fifteen minutes because we checked whether Docker and an NVIDIA GPU existed before
starting a build. It could easily have cost a day.

**Record failures with the same care as successes.** Two of our six records are a failure
and a partial. They are the two that most shaped what the team did next, and the client
note is largely built from them.

**Write down judgement calls as data, not code.** The traversability mapping is a CSV
with a rationale per row. Ricky and Damien disagreed about one class; that disagreement
was resolvable by looking at two rendered images, because the judgement lived somewhere
a person could point at.
