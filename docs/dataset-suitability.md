# Dataset suitability — which question each dataset can answer

**22 September evidence update:** see [the new comparison report](sprint3-dataset-findings.md)
for the 400-sample TruckScenes run and 961-frame GOOSE analysis. TruckDrive data held
by the pair below has not been reproduced on Ricky's machine: account access is
granted, but the file download was blocked by Chrome.

**Story DZ-S3-1 · Owner: Damien Zhang · Reviewer: Fariya Zehrin**
**Started 18 September · refreshed 24 September 2026 · Status: in progress.** Sections 1–7 are complete against
current evidence. Section 8 is a live gap register. Section 9 lists what is still
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
| Radar present | **Yes — 6 sensors, 360°. Raw only, not annotated** | Yes — 6 × Continental ARS 548 RDI, 4D | Yes — 10 4D radars |
| Radar type | Smartmicro UMRR, 77/79 GHz. **Not described as 4D imaging**; elevation unverified | **4D** — range, azimuth, elevation, Doppler | Continental 4D; released joint stream is named `conti542` |
| LiDAR | 3 units (1 × 128-ch, 2 × 32-ch) | 6 units (2 × Pandar64, 4 × Ouster OS0) | 7 long-range FMCW + 3 short-range LiDARs |
| Camera | 6 RGB/NIR + 1 thermal IR | 4 × Sekonix SF3324 | 11–15 cameras |
| **Annotated modalities** | **RGB + LiDAR only.** Radar, NIR, thermal, INS released raw and unlabelled | Boxes shared across LiDAR and radar | Boxes over the sensor suite |
| Max annotation range | Not published. **Measured ~±200 m** on val frames | **>230 m** | **±400 m** (paper) |

TruckDrive sensor counts above were corrected against the
[official release card](https://huggingface.co/datasets/Torc-Robotics/TruckDrive)
on 22 September; the older table mixed camera and LiDAR counts.

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
the quantities include labelled LiDAR points and raw sensor returns, with different
sampling and sensor geometry.

Historical band edges differ: GOOSE uses 50–100 m while TruckDrive splits
50–80 and 80–100 m. The 21 September working protocol in
[`metrics-definitions.md`](metrics-definitions.md) adopts 0–50 / 50–100 /
100–150 / 150–400 / >=400 m for new descriptive coverage runs. Historical
tables remain as measured; adopting common edges does not make their different
denominators or coordinate frames comparable.

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

### MAN TruckScenes — selected-channel return coverage

*Denominators: 4,571 RADAR_LEFT_FRONT returns and 165,588 LIDAR_TOP_FRONT
points, each across the first annotated sample in each of ten mini scenes.*

| Band | Radar returns | LiDAR points |
|---|---:|---:|
| [0, 50) m | 1,655 | 165,520 |
| [50, 100) m | 1,670 | 53 |
| [100, 150) m | 941 | 15 |
| [150, 400) m | 305 | 0 |
| >=400 m | 0 | 0 |

Source: [committed range CSV](../TruckScenes%20-%20Fatima/range-bands.csv).
These are planar distances in each sensor's own coordinate frame. The selected
LiDAR is a downward-tilted Ouster OS0 blind-spot sensor; its plane and field of
view differ from the selected radar. These counts do not establish that radar
outperforms LiDAR. See the [sensor check](../TruckScenes%20-%20Fatima/SENSOR-CHECK.md)
and [coverage workflow](../TruckScenes%20-%20Fatima/RANGE-BANDS.md).
CSV arithmetic and plot regeneration passed; an independent raw-data rebuild
remains open.

**The radar has a hard recorded boundary at ~189.52 m.** Re-reading all 2,400 radar
keyframe files — six channels across the complete 400-sample mini release — gives
**1,145,496 unfiltered returns and zero at or beyond 190 m** in the original sensor
frame. All six channel maxima agree to within 0.000003 m, at ~189.5241 m. That is a
measured property of the downloaded point clouds, not a published sensor
specification, and its cause is not identified; it does not prove the physical radar
cannot measure farther.

It does mean **TruckScenes cannot fairly test radar detection at arbitrary longer
distances.** The actual labelled long-range observations span **150.009–229.418 m**,
with only seven beyond 225 m and none at or beyond 250 m — so the earlier
"150–400 m" figure was a storage bin, not evidence of coverage to 400 m. Source:
[long-range evidence audit](long-range-evidence-audit.md), EXP-0014, record 0017.

**Prediction and ground-truth box coverage remains separate work.**
The dataset annotates beyond 230 m, but the stock
evaluator filters classes at 75 m or 150 m and therefore **produces no detection score
beyond 150 m at all**, so testing D-04 here needs an agreed custom evaluator
configuration rather than more compute.

Package B4 proposes box-level range analysis. The 5,247 FCOS3D predictions are saved in
`scripts/results_mini_val_fcos3d_4cam.json`; the reported 2,088 ground-truth boxes
are a count, not a committed box-level export. Reproduction also needs the mini
metadata: annotations, samples, sample_data and ego_pose, plus calibrated_sensor
if a sensor-relative origin is chosen. The dataset holder must confirm the input
location and access before B4 starts; no owner or path is confirmed here.

The inference script saves predictions in global coordinates. Compute distances
relative to a declared, time-aligned ego or sensor origin, not the global origin.
Agree planar versus 3D distance, band boundaries and sample/class filters in
`metrics-definitions.md`, then apply the same convention to predictions and truth.
Verify joins for all 80 sample tokens and report missing metadata explicitly.
These counts describe coverage; they do not become per-band accuracy without a
separate matching and evaluation protocol.

### TORC TruckDrive — long-range vehicle geometric support

Beyond coverage: **does an annotated vehicle box actually contain a return?** Five mini
scenes, scene indices fixed before inspecting results, 40 evenly spaced annotation
timestamps per scene.

*Denominator: 504 vehicle observations from 55 scene-qualified tracks at 200–400 m.
Tracks recur across bands, so track counts must not be added down the column.*

| Distance | Observations / tracks | LiDAR / radar (static) | LiDAR / radar (aligned) | Scenes favouring LiDAR |
|---|---:|---:|---:|---:|
| 100–150 m | 309 / 66 | 91.26% / 86.73% | 92.56% / 86.08% | 2/4 · 3/4 |
| 150–200 m | 283 / 65 | 83.75% / 69.26% | 86.22% / 68.90% | 4/4 |
| 200–250 m | 173 / 51 | 78.03% / 58.96% | 80.35% / 53.76% | 4/4 |
| 250–300 m | 166 / 44 | 83.13% / 39.76% | 84.94% / 38.55% | 4/4 |
| 300–400 m | 165 / 33 | 80.00% / 12.73% | 89.09% / 13.33% | 4/4 |
| **200–400 m** | **504 / 55** | **80.36% / 37.50%** | **84.72% / 35.52%** | **4/4** |

Source: [five-scene result](truckdrive-multiscene-result.md), EXP-0017, record 0020.

**This runs counter to the project's founding hypothesis and should be reported as
such.** D-04 asks whether 4D radar degrades *less* than LiDAR at long range. In this
subset it degrades considerably *more* — radar in-box support falls from 86.73% at
100–150 m to 12.73% at 300–400 m, while LiDAR stays near 80%. A negative answer to our
own hypothesis is a result, not a failure, and Adrian said at kickoff that negative
results count.

Four limits that bound it. It is **geometric support, not detection accuracy** — no
model was run. It covers **five numbered clips**, not independent recording sessions or
a random sample, with correlated repeated observations. A rising percentage in a
farther band can reflect *which vehicles remain in view* rather than better sensing at
range. And it describes **these released sensor configurations**: TruckDrive's radar is
not TruckScenes' radar, so this does not transfer across datasets — D-01 again.

### Reading these three together

The only cross-dataset statement the evidence supports is about **suitability**: GOOSE's
labelled data is overwhelmingly near-field, with 1.1% of points beyond 150 m and no
labelled radar at all, so it cannot address D-04. TruckScenes has boxes shared across
LiDAR and radar, which made it the natural matched-sensor candidate — but its recorded
radar stops at ~189.52 m, so it cannot test the band D-04 asks about. TruckDrive is the
only one of the three carrying annotated vehicles into 200–400 m with both modalities
recorded, which is why the long-range result comes from there. A matched *detector*
comparison on that subset is no longer merely conditional: no published checkpoint
accepts input at those distances.

Those are statements about what each dataset is *made of*. The one performance-shaped
result now available — TruckDrive's in-box support — is **within** a single dataset,
which is what D-01 permits. There is still no cross-dataset comparison, and no
detection accuracy from any of them.

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

## 7. What each dataset can and cannot answer

The point of the preceding six sections, in two tables.

### Against the project's actual questions

| Question | GOOSE | MAN TruckScenes | TORC TruckDrive |
|---|---|---|---|
| **D-04** — does perception degrade past 150 m? | **No.** 1.10% of labelled points beyond 150 m, and no labelled radar in the released assets | **No, and now for a measured reason.** Recorded radar stops at **~189.52 m** across all 1,145,496 returns; labelled long-range observations reach only 229.418 m. The evaluator's 150 m ceiling is the *second* constraint, not the first | **Answered descriptively, and against our hypothesis.** 504 vehicle observations at 200–400 m: LiDAR in-box support **80.36%** against radar **37.50%**, favouring LiDAR in 4/4 eligible scenes. Geometric support, not detection accuracy |
| **Matched radar vs LiDAR detection** | **Not with the current released-label workflow.** No radar detection ground truth established | **Not testable at range** — see the recorded radar boundary in §5 | **Not runnable with published checkpoints.** Both L-RadSet PointPillars checkpoints crop input at ~70 m: **0 of 504** of our 200–400 m vehicle centres fall inside either. TruckDrive's own full-range config covers 192/504 but has no matching pretrained radar-only model in the inspected release |
| **Off-road terrain and traversability** | **Yes — and only GOOSE** | No — on-road | No — on-road |
| **Sensor coverage by range** | Yes, for labelled LiDAR points | Yes, ten samples of one radar and one tilted blind-spot LiDAR; geometry differs | Yes, for radar returns |
| **Reproducible on team hardware** | Yes, macOS and Windows | Yes, CPU-only inference viable | Viewer yes; no model run attempted |

**The short version, as of 24 September.** GOOSE is the off-road dataset and cannot
address D-04. TruckScenes looked like the matched-sensor dataset and is ruled out at
range by its *recorded data*, not merely its evaluator. TruckDrive carries the
long-range evidence and has produced the project's one substantive D-04 result — which
points the opposite way to the founding hypothesis.

**The detector comparison that would have settled it is not runnable this semester.**
No published checkpoint accepts input at the distances in question. That is a
reportable negative finding with an identified cause, and materially more useful than
running out of time.

### Experiments that are actually feasible before 12 October

Rewritten 24 September. Three rows that were "conditional" have since resolved, two of
them to **no**.

| Experiment | Feasible? | What it turns on |
|---|---|---|
| TruckDrive long-range support, more scenes or classes | **Yes, and proven** | Five scenes done (EXP-0017). The method is established; extending it is download and compute cost, not a new question |
| TruckScenes box-level range analysis | **Possible, largely pointless** | Metadata is now held (Ricky). But the recorded radar stops at ~189.52 m, so it cannot speak to 200–400 m. Do it only if someone needs the <190 m band specifically |
| Radar or LiDAR detector at 200–400 m | **No** | **Resolved by EXP-0018.** Both L-RadSet checkpoints crop input at ~70 m; 0/504 of our distant vehicle centres fall inside. Not a compute problem — no compatible published model exists in the inspected releases |
| Matched radar-vs-LiDAR detector benchmark (S3-X1) | **No, this semester** | Follows directly from the row above. Training a compatible model from scratch is outside the agreed scope |
| GOOSE PTv3 full split | **Technically, not usefully** | ~5.1 h lower bound on the one GTX 1660, and Ricky's approval. Produces segmentation mIoU, which has no detection equivalent — it does not serve D-04 even if it completes |
| Cross-dataset accuracy ranking | **Never** | Forbidden by D-01, and none of the numbers would support it anyway |

**What this leaves as the project's answer to D-04:** a within-dataset descriptive
result on TruckDrive, plus a documented reason why the detector comparison could not be
run. That is a narrower deliverable than Sprint 1 imagined, and it is honestly bounded.

---

## 8. Gap register

Every unresolved item found while assembling this document. Gaps are recorded as gaps.

| # | Gap | Evidence | Holder |
|---|---|---|---|
| G-1 | **No TruckDrive survey exists** in template form. Its facts here come from Kelsey's statistics and summary, not a reviewed survey | DS-4 records "statistics recorded; survey not in template form" | Kelsey — KL-S3-1 |
| G-2 | **Open file-level reconciliation.** GOOSE val is published as 960 and extracts as 961. The eight scenario counts sum to 961, establishing internal arithmetic only; this does not rule out a duplicate or extra frame. Compare the local file inventory with the published inventory before resolving the discrepancy | `dataset-statistics.md` §3 vs `goose.md` §2 | Damien — inventory comparison pending |
| G-3 | **TruckScenes total size unverified** — ~560 GB carried from `DATASET_OVERVIEW.md`, never remeasured against the current AWS listing | `truckscenes.md` §2, marked Unverified | Open |
| G-4 | **Working coverage protocol recorded.** New runs use five explicit bands; historical tables retain their original bins. Shared edges alone do not fix different coordinate frames, subsets or fields of view | `metrics-definitions.md`, 21 September protocol | Ricky — team walkthrough pending |
| G-5 | **Closed — overtaken.** TruckScenes return coverage is delivered (FA-S3-1) and the box-level analysis B4 proposed is moot at long range: the recorded radar boundary at ~189.52 m means no box-level work there can address 200–400 m. Superseded by EXP-0014 and EXP-0017 | `long-range-evidence-audit.md`, EXP-0017 | Closed |
| G-6 | **TruckDrive licence clause unresolved** — non-commercial, plus the AV-business prohibition, against a stated CC/open-source deliverable | `DATASET_OVERVIEW.md` | Needs a client decision |
| G-7 | **TruckDrive camera/LiDAR coverage is partial** — 2 of 24 scenes. Any multimodal TruckDrive claim must state this, not imply full-mini coverage | `TruckDrive - Kelsey/SUMMARY.md` | Kelsey — KL-S3-1 |
| G-8 | **GOOSE radar is not 4D as far as our sources go.** The survey records Smartmicro UMRR-96 (79 GHz, 0.4–55 m) and UMRR-11 (77 GHz, 1–175 m), neither described as 4D imaging, and elevation is nowhere asserted. Since the radar is unlabelled anyway this does not change any conclusion — but GOOSE must not be listed as a 4D-radar dataset. Settling it needs the Smartmicro datasheets, which we do not hold | `goose.md` §2–3 | Me — narrowed; needs a vendor datasheet |
| G-9 | **TruckDrive empty camera channels and NumPy/SciPy warning** unresolved on the second machine | EXP-0009 | Fariya + Kelsey |
| G-10 | **Cause of the ~189.52 m radar boundary is unknown.** All six channels agree to 0.000003 m across 1,145,496 returns, which strongly suggests a shared acquisition or processing limit — but it is a measured property of the downloaded clouds, not an established sensor specification, and it does not prove the physical radar cannot measure farther | EXP-0014, record 0017 | Ricky |
| G-11 | **No compatible long-range detector identified.** Audit of the inspected L-RadSet and TruckDrive releases only; it is not proof that no suitable model exists elsewhere | EXP-0018, record 0021 | Aiden — open |

---

## 9. Outstanding for this document

Per the A1/A2/A3 breakdown in `Damien - Sprint 3/README.md`:

- [x] A1 — comparison built from the three surveys, with denominators inline (§2–5),
      and what each dataset can and cannot answer (§7)
- [x] A2 — GOOSE traversability explainer (§6): the 64-class mapping, its dependence
      on human labels, and the 961-frame statistics kept separate from the 10-frame run
- [x] A3 — link check, arithmetic check, class/level check and both validators run;
      see *Verification* below
- [x] Internal GOOSE frame-count sum checked and G-8 sensor claim narrowed
- [ ] G-2 file-level reconciliation and G-8 vendor-datasheet confirmation
- [ ] **A4** — cold read by a reader outside the GOOSE pair, recorded unedited.
      **The one acceptance condition this document cannot satisfy by itself**, and the
      one that closes P-6 and DS-4
- [ ] Fold in the TruckDrive survey once KL-S3-1 delivers it, replacing the
      statistics-derived rows here

### Verification

Run on every change to this document, not once at the end:

| Check | Method | Result |
|---|---|---|
| Every relative link resolves | Each Markdown link target resolved against the repo | Rechecked on 21 September; all resolve |
| Range tables sum to their stated totals | GOOSE → 174,891,807; TruckDrive → 71,206; TruckScenes radar → 4,571 and LiDAR → 165,588 | All exact |
| Every class in §6 sits at the level claimed | Each name cross-checked against `traversability_map.csv` | Pass — **caught `water` mis-filed in my own draft** |
| Per-scenario frames sum to the split | §3 of `dataset-statistics.md` | 961, exact |
| Record and log identity | `validate_result.py`, `validate_experiment_logs.py` | Passed on the integrated branch, 21 September; 11 result records validated |

No number in this document was re-derived; each was read from a merged record and
checked against its source. Where a number appears twice in the repository with
different values, the discrepancy is recorded in §8 rather than silently resolved.

---

## 10. Sources

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
| [`docs/metrics-definitions.md`](metrics-definitions.md) | Evaluator limits and working descriptive coverage protocol |
| [`decision-log.md`](../decision-log.md) | D-01 comparison basis, D-04 research question, D-05/D-06 |
| [`GOOSE - Ricky+Damien/traversability_map.csv`](../GOOSE%20-%20Ricky+Damien/traversability_map.csv) | All 64 class assignments and rationales |
| [`GOOSE - Ricky+Damien/traversability-map-notes.md`](../GOOSE%20-%20Ricky+Damien/traversability-map-notes.md) | The 14 contested assignments |
| [`GOOSE - Ricky+Damien/GOOSE-SUMMARY.md`](../GOOSE%20-%20Ricky+Damien/GOOSE-SUMMARY.md) | PTv3 gates, the canopy correction, the withdrawn `bush` claim |
| [`docs/long-range-evidence-audit.md`](long-range-evidence-audit.md) | TruckScenes recorded radar boundary; EXP-0014, record 0017 |
| [`docs/truckdrive-multiscene-result.md`](truckdrive-multiscene-result.md) | Five-scene long-range support; EXP-0017, record 0020 |
| [`docs/detector-compatibility-decision.md`](detector-compatibility-decision.md) | Checkpoint input-extent audit; EXP-0018, record 0021 |
| `experiment-log/0005`, `0009` | TruckDrive setup and reproduction |

**Not used:** the Sprint 2 project report narrative. Where it and a merged record
disagree — as with the `~1–6%` figure in §5 — the merged record is taken as correct and
the discrepancy is recorded for correction.
