# Dataset suitability — which question each dataset can answer

**Story DZ-S3-1 · Owner: Damien Zhang · Reviewer: Fariya Zehrin**
**Started 18 September 2026 · Status: in progress.** Sections 1–6 are complete against
current evidence. Section 7 is a live gap register. Section 8 lists what is still
outstanding and who holds it.

---

## 1. What this document is, and what it deliberately is not

Three pairs each got one dataset working in Sprint 2. This document puts the three
side by side **on suitability** — what each one is made of, and therefore which
question it can answer.

It does **not** rank them, and that is a constraint rather than a preference. D-01
fixes comparison *within* a dataset, never across datasets on a shared axis. The
reason is concrete: GOOSE reports semantic segmentation over labelled points,
TruckScenes reports 3D detection over annotated boxes, and TruckDrive's long-range
figure counts raw radar returns. Those are three different kinds of number. Putting
them on one axis produces a ranking that looks meaningful and is not.

So the output here is *which question each dataset can answer*, never *which dataset
is best*.

### The denominator rule

Every measurement below carries its sampling description **in the same cell as the
number**. This is not housekeeping — it is a defect this project has already had to
repair once. Commit `5dd6a8f` found the three headline dataset figures sitting side by
side in an evidence table as though they were comparable, when:

- GOOSE's point count covers **all 961 validation frames**
- TruckScenes' totals cover **one radar and one LiDAR channel, on one sample per scene**
- TruckDrive's long-range figure covers **one radar frame in each of 24 scenes**

A number that cannot say what it is *of* cannot be compared with anything. If a cell
below ever loses its denominator, that is a regression.

---

## 2. Identity and released assets

| | **GOOSE** | **MAN TruckScenes** | **TORC TruckDrive** |
|---|---|---|---|
| Domain | Off-road — forest, campus, grassland, urban fringe; four seasons | On-road — motorway, feeder road, city, terminal | On-road — long-range highway |
| Primary task | Semantic segmentation (2D + 3D) | 3D object detection and tracking | 3D object detection |
| Annotation geometry | Pointwise + pixelwise semantic/instance labels. **No 3D boxes** | Oriented 3D bounding boxes | 3D bounding boxes + lane lines |
| Radar present | **Yes — 6 sensors, 360°. Raw only, not annotated** | Yes — 6 × Continental ARS 548 RDI, 4D | Yes — 7 long-range + 3 short-range |
| Radar type | Smartmicro UMRR, 77/79 GHz. **Not described as 4D imaging**; elevation unverified | **4D** — range, azimuth, elevation, Doppler | ARS540 family, long-range |
| LiDAR | 3 units (1 × 128-ch, 2 × 32-ch) | 6 units (2 × Pandar64, 4 × Ouster OS0) | 11–15 per the paper's comparison table |
| Camera | 6 RGB/NIR + 1 thermal IR | 4 × Sekonix SF3324 | Present |
| **Annotated modalities** | **RGB + LiDAR only.** Radar, NIR, thermal, INS released raw and unlabelled | Boxes shared across LiDAR and radar | Boxes over the sensor suite |
| Max annotation range | Not published. **Measured ~±200 m** on val frames | **>230 m** | **±400 m** (paper) |

**The single most consequential row is "annotated modalities".** GOOSE ships radar, but
not labelled radar. That one fact is why GOOSE cannot answer the project's headline
question no matter how much compute is applied to it, and it is the reason the GOOSE
strand was closed out rather than extended.

---

## 3. Access, licence and cost

| | **GOOSE** | **MAN TruckScenes** | **TORC TruckDrive** |
|---|---|---|---|
| Licence | **CC BY-SA 4.0** (data) · MIT (devkit) | **CC BY-NC-SA 4.0** | **Torc Non-Commercial v1.0** |
| Commercial use | **Permitted** — no NC clause | Prohibited | Prohibited, with an extra clause below |
| Share-alike | Yes, propagates to derivatives | Yes | Per Torc terms |
| Access gating | Open — no account found | Open via AWS, no sign-in | **Gated** — Hugging Face, licence acceptance |
| Total size | ~62.4 GB + ~30 GB (GOOSE-Ex) | ~560 GB train/val (**unverified** — not remeasured locally) | 28.8 TB total; **mini alone ~282.71 GB compressed** |
| Smallest usable subset | **2.9 GB** (2D val) / 3.3 GB (3D val) | **~9.6 GB** (v1.2-mini, downloaded) | Mini, partially retained — see §4 |
| Devkit | Python, MIT | Python, Apache-2.0, pip-installable | Repo-only, per-component READMEs |

> **Licence flag for the handover, needs a decision.** Our project IP is stated as
> Creative Commons / open source. TruckDrive's licence is not a CC licence, and it
> additionally **prohibits internal research by any entity whose primary or substantial
> business involves developing autonomous vehicle systems**. Adrian's affiliation makes
> that clause worth checking explicitly rather than assuming. Recorded in
> `DATASET_OVERVIEW.md` since Sprint 1; still unresolved.

---

## 4. What we actually hold, and on what hardware

Distinct from what each dataset publishes. This is the row that decides what can be
run before 12 October.

| | **GOOSE** | **MAN TruckScenes** | **TORC TruckDrive** |
|---|---|---|---|
| Held locally | Full validation split — **961 paired LiDAR/label frames**, 8 scenarios | **v1.2-mini** — 10 scenes, 400 annotated samples, 18 calibrated channels | **24 mini scenes.** Radar, annotations, calibration, poses for all 24; **camera and LiDAR for only `scene_28_1` and `scene_28_22`** |
| Why not more | Full split not needed for characterisation | Full release ~560 GB | Complete mini ~282.71 GB compressed — storage-bound, not choice |
| Setup outcome | Worked, macOS + Windows | Worked, macOS + Windows | Worked, Windows; second-machine reproduction reported with unresolved warnings |
| Setup cost | Documented in EXP-0001/0003 | **~6 h** (Fatima, incl. download and first visualisation) | EXP-0005; EXP-0009 records a folder-layout fix and added dependencies |
| Known install snag | — | Devkit 1.2.0 expects `matplotlib.cm.get_cmap`, removed in current matplotlib; narrow compat shim applied | NumPy/SciPy compatibility warning and **empty camera channels**, both unresolved |
| Model run achieved | PTv3, **10 of 961 frames**, modified config, then stopped | FCOS3D zero-shot, **80/80 mini_val samples**, 4 cameras, CPU | **None** |
| Compute ceiling | One GTX 1660, 6 GB — the team's only CUDA device | CPU-only inference viable (~28 s/image single camera) | — |

**Hardware is the binding constraint on all three.** The ~5-hour GOOSE full-pass figure
is an extrapolation of the measured processing loop that **excludes data loading**, so
it is a lower bound, not a prediction of a run nobody has performed.

---

## 5. Range coverage — three separate panels

These panels are **coverage**, not accuracy. None of them shows whether a model detects
anything. They are presented separately and are **not to be merged onto a shared axis**:
the three quantities are labelled LiDAR points, raw radar returns, and nothing at all.

Note also that the band edges differ between the two datasets that have them — GOOSE
uses 50–100, TruckDrive splits 50–80 and 80–100. Harmonising them is open question 3 in
`metrics-definitions.md` (proposed 0–50 / 50–100 / 100–150 / 150–400 m) and is Ricky's
to confirm. Until then these tables are reproduced as measured rather than re-bucketed.

### GOOSE — labelled LiDAR points
*Denominator: 174,891,807 labelled points across all 961 validation frames.*

| Band | Points | Share |
|---|---:|---:|
| 0–25 m | 110,012,621 | 62.90% |
| 25–50 m | 40,237,112 | 23.01% |
| 50–100 m | 17,934,607 | 10.25% |
| 100–150 m | 4,779,044 | 2.73% |
| **150 m+** | **1,928,423** | **1.10%** |

**3.84% of labelled points fall beyond 100 m.** Note for the Sprint 2 report: the
`~1–6%` figure printed there is the *per-scenario* range from `findings-damien.md`, not
this split-level figure. The split-level numbers are what the acceptance tests and the
Scope of Work quote.

### TORC TruckDrive — raw radar returns
*Denominator: 71,206 returns across 24 selected annotated radar frames — one frame per
scene, not the full mini split.*

| Band | Returns | Share |
|---|---:|---:|
| 0–25 m | 13,717 | 19.26% |
| 25–50 m | 22,264 | 31.27% |
| 50–80 m | 16,396 | 23.03% |
| 80–100 m | 5,356 | 7.52% |
| 100–150 m | 6,727 | 9.45% |
| **150 m+** | **6,746** | **9.47%** |

18.92% of returns fall beyond 100 m. These are **sensor returns, not detections**.
Point presence at range shows the sensor produces data there and nothing more.

### MAN TruckScenes — not yet measured

No range-band distribution exists. The dataset annotates beyond 230 m, but the stock
evaluator filters classes at 75 m or 150 m and therefore **produces no detection score
beyond 150 m at all**, so testing D-04 here needs an agreed custom evaluator
configuration rather than more compute.

This gap is what package B4 in my Sprint 3 plan proposes to close, using the 5,247
saved FCOS3D predictions and 2,088 ground-truth boxes already in `scripts/`.

### Reading these three together

The only cross-dataset statement the evidence supports is about **suitability**: GOOSE's
labelled data is overwhelmingly near-field, with 1.1% of points beyond 150 m and no
labelled radar at all, so it cannot address D-04. TruckDrive's retained radar has
substantially more of its returns at long range, which is why it is the D-04 dataset.
TruckScenes is the only one of the three with **boxes shared across LiDAR and radar**,
which makes it the matched-sensor dataset.

That is a statement about what each is *made of*. It is not a performance comparison,
and no performance comparison is available from any of them yet.

---

## 6. The GOOSE traversability figures — what they show

The figures that answer Adrian's off-road question are the most likely thing in this
project to be over-read, so this section states plainly what produced them.

### The mapping is a judgement, deliberately recorded as data

All **64 GOOSE semantic classes** are assigned to one of four traversability levels
borrowed from the STONE dataset, each with a written rationale:

| Level | Classes | Members |
|---|---:|---|
| 0 · Free | 4 | `undefined`, `ego_vehicle`, `sky`, `outlier` — not surface questions at all; excluded from scoring |
| 1 · Traversable | 9 | `asphalt`, `gravel`, `soil`, `low_grass`, `cobble`, `sidewalk`, `bikeway`, `pedestrian_crossing`, `road_marking` |
| 2 · Potentially Traversable | 12 | `snow`, `leaves`, `moss`, `curb`, `rail_track`, `debris`, `crops`, `bridge`, `tunnel`, `high_grass`, `scenery_vegetation`, `tree_root` |
| 3 · Non-Traversable | 39 | `water`, `traffic_cone`, and the remaining object, vegetation and structure classes |

*Source: all 64 rows of [`traversability_map.csv`](../GOOSE%20-%20Ricky+Damien/traversability_map.csv).*

This is a judgement call, not a calculation, and it is treated as one. **Fourteen
assignments are recorded as genuinely contested** in
[`traversability-map-notes.md`](../GOOSE%20-%20Ricky+Damien/traversability-map-notes.md),
each with the open question attached — whether `snow` should be conditional or simply
unknown, whether `sidewalk`'s legality belongs in a physical mapping at all, whether
`high_grass` hiding holes makes it uncertain or blocked. Note `water` sits at
Non-Traversable on an explicit unknown-depth rule: shallow water is crossable, but the
class carries no depth, so the conservative reading wins.

The mapping lives in a CSV rather than in the renderer's code, and the notes require it
to stay there: *"Assignments should change in `traversability_map.csv`, never as
hard-coded exceptions in Damien's renderer."* That is what makes the judgement
reviewable — Fabian or Adrian can disagree with **one line**, with its stated rationale,
rather than with the whole approach.

### What the figures therefore do not show

They group **existing human labels**. They do not show a model deciding where a vehicle
can drive, and they do not establish a connected, vehicle-safe route. Apparent
corridors in woodland are apparent corridors in the annotation, which is a different
claim.

### Two claims this pair had to withdraw

Both are recorded because the correction is the useful part.

**The canopy conclusion was wrong because the instrument was.** An absolute height
threshold suggested woodland scenes were genuinely blocked at ground level. On sloping
ground, absolute height does not separate canopy from terrain. Taking the lowest return
per 0.4 m ground cell roughly **halves** the apparent blocked share — one scene moved
from **92% to 58% non-traversable**. The conclusion did not survive a better instrument.

**The `bush` claim was overstated and withdrawn.** The argument was that this single
assignment decided whether a scene read as a drivable corridor or a blocked one.
Rendering it both ways showed the Traversable share is **identical to one decimal
place** either way; `bush` only moves points between *uncertain* and *blocked*.

### Complete statistics and the partial model run are different evidence

The most common misreading available here is to let the 961-frame characterisation lend
its completeness to the 10-frame model run. They are kept apart:

| Evidence | What it covers | What it supports |
|---|---|---|
| Split characterisation | **All 961 validation frames**, 174,891,807 labelled points | Scale, class distribution, range distribution |
| Traversability figures | All 8 scenarios, derived from human labels | The team's interpretation of the annotation |
| PTv3 inference | **10 of 961 frames**, modified configuration, then stopped | Bounded feasibility on 6 GiB — nothing about accuracy |
| Bounded gates | Smallest frame 30,263 pts / 8.6 s; largest 270,720 pts / 35.4 s | No out-of-memory at these sizes |
| **~5.1 hour full-pass figure** | Extrapolation of 18.94 s/frame mean loop-body time over 10 frames, **excluding data loading** | A lower bound. **Not a measured runtime** |
| Published 0.8096 mIoU | The GOOSE authors' score for PTv3 | **Nothing this project measured.** Never report it as ours |

No GOOSE accuracy number was produced by this project. The run established that the
pipeline executes on the available hardware, and stopped there deliberately.

---

## 7. Gap register

Every unresolved item found while assembling this document. Gaps are recorded as gaps.

| # | Gap | Evidence | Holder |
|---|---|---|---|
| G-1 | **No TruckDrive survey exists** in template form. Its facts here come from Kelsey's statistics and summary, not a reviewed survey | DS-4 records "statistics recorded; survey not in template form" | Kelsey — KL-S3-1 |
| G-2 | **GOOSE val split: 960 published, 961 extracted.** The survey records both without reconciling them. Every measurement here uses the measured 961 | `goose.md` §2 vs §6 and `dataset-statistics.md` | Me — resolve before this document is final |
| G-3 | **TruckScenes total size unverified** — ~560 GB carried from `DATASET_OVERVIEW.md`, never remeasured against the current AWS listing | `truckscenes.md` §2, marked Unverified | Open |
| G-4 | **Band edges not harmonised** — GOOSE 50–100 vs TruckDrive 50–80/80–100. Blocks any combined range reporting | `metrics-definitions.md` open question 3 | Ricky |
| G-5 | **No TruckScenes range-band distribution** exists at all | §5 above | Proposed as B4 |
| G-6 | **TruckDrive licence clause unresolved** — non-commercial, plus the AV-business prohibition, against a stated CC/open-source deliverable | `DATASET_OVERVIEW.md` | Needs a client decision |
| G-7 | **TruckDrive camera/LiDAR coverage is partial** — 2 of 24 scenes. Any multimodal TruckDrive claim must state this, not imply full-mini coverage | `TruckDrive - Kelsey/SUMMARY.md` | Kelsey — KL-S3-1 |
| G-8 | **GOOSE radar elevation capability unverified** — Smartmicro UMRR is not described as 4D imaging. Affects how GOOSE is described in any radar comparison | `goose.md` §2 | Me |
| G-9 | **TruckDrive empty camera channels and NumPy/SciPy warning** unresolved on the second machine | EXP-0009 | Fariya + Kelsey |

---

## 8. Outstanding for this document

Per the A1/A2/A3 breakdown in `Damien - Sprint 3/README.md`:

- [x] A1 — comparison built from the three surveys, with denominators inline
- [x] A2 — GOOSE traversability explainer (§6): the 64-class mapping, its dependence
      on human labels, and the 961-frame statistics kept separate from the 10-frame run
- [ ] **A3** — every claim link-checked to a survey, log or record; both validators run
- [ ] **A4** — cold read by a reader outside the GOOSE pair, recorded unedited
- [ ] Resolve G-2 and G-8, which are mine
- [ ] Fold in the TruckDrive survey once KL-S3-1 delivers it, replacing the
      statistics-derived rows here

---

## 9. Sources

Every claim above traces to one of these. No number in this document was
re-derived; each was read from a merged record.

| Source | Used for |
|---|---|
| [`docs/dataset-surveys/goose.md`](dataset-surveys/goose.md) | GOOSE identity, sensors, annotation schema, licence, tooling |
| [`docs/dataset-surveys/truckscenes.md`](dataset-surveys/truckscenes.md) | TruckScenes identity, sensors, schema, licence, setup cost |
| [`GOOSE - Ricky+Damien/dataset-statistics.md`](../GOOSE%20-%20Ricky+Damien/dataset-statistics.md) | 961 frames, 174,891,807 points, range distribution |
| [`TruckDrive - Kelsey/dataset-statistics.md`](../TruckDrive%20-%20Kelsey/dataset-statistics.md) | 24 scenes, 12,502 radar frames, 526,148 boxes, range bands |
| [`TruckDrive - Kelsey/SUMMARY.md`](../TruckDrive%20-%20Kelsey/SUMMARY.md) | Retained modality coverage, storage constraint |
| [`TruckScenes - Aiden/dataset-statistics.md`](../TruckScenes%20-%20Aiden/dataset-statistics.md) | Mini table counts, channel names, mini_val figures |
| [`DATASET_OVERVIEW.md`](../DATASET_OVERVIEW.md) | TruckDrive identity, sizes, licence terms |
| [`docs/metrics-definitions.md`](metrics-definitions.md) | Evaluator range limits, open band-edge question |
| [`decision-log.md`](../decision-log.md) | D-01 comparison basis, D-04 research question, D-05/D-06 |
| [`GOOSE - Ricky+Damien/traversability_map.csv`](../GOOSE%20-%20Ricky+Damien/traversability_map.csv) | All 64 class assignments and rationales |
| [`GOOSE - Ricky+Damien/traversability-map-notes.md`](../GOOSE%20-%20Ricky+Damien/traversability-map-notes.md) | The 14 contested assignments |
| [`GOOSE - Ricky+Damien/GOOSE-SUMMARY.md`](../GOOSE%20-%20Ricky+Damien/GOOSE-SUMMARY.md) | PTv3 gates, the canopy correction, the withdrawn `bush` claim |
| `experiment-log/0005`, `0009` | TruckDrive setup and reproduction |

**Not used:** the Sprint 2 project report narrative. Where it and a merged record
disagree — as with the `~1–6%` figure in §5 — the merged record is taken as correct and
the discrepancy is recorded for correction.
