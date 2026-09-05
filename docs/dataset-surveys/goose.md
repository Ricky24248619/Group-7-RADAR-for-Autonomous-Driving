# Survey: GOOSE (German Outdoor and Offroad Dataset)

> **Reference example** for [`../dataset-survey-template.md`](../dataset-survey-template.md).
> All sections complete. §6 **passed** on 22 Aug; §7 was rewritten on 28 Aug once the
> dataset was actually understood rather than merely obtained; §6 and §7 were corrected
> again on 5 Sep after the published baseline was actually run. Note how uncertain facts
> are marked rather than guessed, how the install gotchas are kept in §6 rather than
> dropped once solved, and how **three** conclusions this survey previously stated with
> confidence were later corrected in place rather than quietly edited away.

## 0. Survey metadata

| | |
|---|---|
| Dataset | GOOSE (+ GOOSE-Ex extension) |
| Surveyed by | Damien Zhang (DZ) |
| Date surveyed | 2026-08-18 · feasibility 2026-08-22 · §7 rewritten 2026-08-28 · baseline result 2026-09-05 |
| Reviewed by | *(pending — must be a member other than DZ)* |
| Review date | |
| Survey status | **Complete — pending review** (D5) |

Story **DZ-2** · Workstream **WS2** · Bears on risk **R-24** and decision **D-03**

> ⚠️ **Correction, 18 Aug 2026.** An earlier draft recorded GOOSE as having no radar,
> based on the sensor list on the project landing page. That was wrong. The landing
> page lists only the *annotated* modalities. The paper's platform section documents
> **six radar sensors** on MuCAR-3, and states all raw sensor data is released in ROS
> bag format. GOOSE does carry radar — unlabelled, but present. See §3 and §7.

---

## 1. Identity

| Field | Value | Status | Source |
|---|---|---|---|
| Official name | GOOSE — German Outdoor and Offroad Dataset | Confirmed | [goose-dataset.de](https://goose-dataset.de/) |
| Other names used | "the goose dataset" (Fabian, 4 Aug meeting) | Confirmed | Meeting transcript |
| Authors | Mortimer, Hagmanns, Granero, Luettel, Petereit, Wuensche | Confirmed | [arXiv:2310.16788](https://arxiv.org/abs/2310.16788) |
| Organisation | Fraunhofer IOSB *(full affiliation list unverified)* | Confirmed / partial | [devkit repo org](https://github.com/FraunhoferIOSB/goose_dataset) |
| Venue and year | **ICRA 2024** | Confirmed | arXiv listing |
| Paper | *The GOOSE Dataset for Perception in Unstructured Environments* — [arXiv:2310.16788](https://arxiv.org/abs/2310.16788) | Confirmed | direct |
| Companion paper | *Excavating in the Wild: The GOOSE-Ex Dataset* — [arXiv:2409.18788](https://arxiv.org/pdf/2409.18788) | Confirmed | docs |
| Project page | https://goose-dataset.de/ | Confirmed | direct |
| Devkit repository | [FraunhoferIOSB/goose_dataset](https://github.com/FraunhoferIOSB/goose_dataset) | Confirmed | direct |
| Data host | Direct download from project site; raw data also on [academictorrents.com](https://academictorrents.com/) | Confirmed | docs |

---

## 2. Fixed checklist

| Field | Value | Status | Source |
|---|---|---|---|
| **Domain** | **Off-road** — unstructured outdoor; forest, campus, grassland, urban fringe; all four seasons, varied weather | Confirmed | paper §V-A |
| **Radar present** | **Yes — 6 sensors, 360° coverage.** Raw only; **not annotated** | Confirmed | paper, platform section |
| Radar type if present | Smartmicro UMRR automotive radar, 77/79 GHz. **Not described as 4D imaging** — elevation capability unverified | Confirmed / type open | paper |
| LiDAR present | Yes — 3 units (1×128-ch + 2×32-ch) | Confirmed | paper |
| Camera present | Yes — 6 RGB/NIR + 1 thermal IR | Confirmed | paper |
| **Primary task** | **Semantic segmentation** (2D and 3D) | Confirmed | paper §V |
| **Annotation geometry** | Pixel-wise 2D semantic + instance; pointwise 3D semantic + instance (SemanticKITTI format). **No 3D bounding boxes** | Confirmed | paper §IV-D |
| **Licence** | **CC BY-SA 4.0** (dataset) · **MIT** (devkit code) | Confirmed | devkit repo |
| Commercial use permitted | Yes — no NC clause | Confirmed | licence |
| Share-alike obligation | **Yes** — propagates to derivatives | Confirmed | licence |
| Access gating | Open — no account or licence acceptance step found | Confirmed | project site |
| **Total download size** | **~62.4 GB** (GOOSE) + **~30 GB** (GOOSE-Ex). Raw ROS bags additional and unquantified | Confirmed | docs |
| Smallest usable subset | Validation split — **2.9 GB** (2D) or **3.3 GB** (3D) | Confirmed | docs |
| Data format(s) | `.png` images + labels; `.bin` point clouds (float32 XYZ + remission); `.label` (SemanticKITTI, uint32); `goose_label_mapping.csv`; **raw ROS bags** + YAML metadata | Confirmed | docs |
| **Devkit available** | Yes | Confirmed | repo |
| Devkit language and licence | Python · MIT | Confirmed | repo |
| Annotated frame count | **10,000** labelled image/point-cloud pairs, of 15,000 total frames | Confirmed | paper + site |
| Max annotation range | Not published. **Measured ~±200 m** on val frames — see §6 | Confirmed (empirical) | this survey |

**Splits:** train 7,830 · val 960 · test 1,210 (= 10,000). Labels published for **train
and val only**; test labels withheld for the leaderboard competitions. *(Confirmed —
paper §V-A, docs.)*

**Download sizes by split:** 2D — 22.5 / 2.9 / 3.4 GB. 3D — 27 / 3.3 / 3.3 GB.

---

## 3. Sensor configuration

Platform: **MuCAR-3**. GOOSE-Ex adds two further platforms (ALICE excavator, Spot
quadruped) with different suites — treat as separate configurations under D-01.

| Modality | Count | Make / model | Key specs | Status |
|---|---|---|---|---|
| **Radar** | **5** | Smartmicro UMRR-96 Type 153 | 79 GHz, medium-range mode, **0.4–55 m** | Confirmed |
| **Radar** | **1** | Smartmicro UMRR-11 Type 132 | 77 GHz, long-range mode, **1–175 m** | Confirmed |
| LiDAR | 1 | Velodyne Alpha Prime | 128 channels | Confirmed |
| LiDAR | 2 | Ouster OS0 | 32 channels, tilted ±45° for lateral close obstacles; **annotated** | Confirmed |
| Camera | 4 | Basler acA2440-20gc | RGB, roof-mounted 360° view, 50 Hz, 45° HFOV | Confirmed |
| Camera | 1 | JAI FSFE-3200D | RGB+NIR prism, Fujinon TF6MA-1 6 mm, 10 Hz, 59° HFOV | Confirmed |
| Camera | 1 | Basler acA2440-20gc | RGB on pan/tilt mobile platform, Kowa LM8HC 8 mm, 10 Hz, 54° HFOV | Confirmed |
| Camera | 1 | FLIR A615 | Thermal IR, front-facing, low-light modality | Confirmed |
| INS / GNSS | 1 | Oxford RT3000v3 | INS with differential RTK-GNSS over LTE (NTRIP) | Confirmed |

**Radar coverage:** *"Six radar sensors are mounted around the vehicle to provide 360
degree radar detections with only small blind spots on the sides."* (paper)

**Calibration / extrinsics published:** Yes — calibration data and procedures in the
dataset documentation. *(Confirmed.)*

---

## 4. Annotation schema

| Field | Value | Status |
|---|---|---|
| Annotation type | Pixel-wise 2D semantic + instance; pointwise 3D semantic + instance | Confirmed |
| Class count | **64 semantic classes** | Confirmed |
| Grouping | Higher-level groups: Animal, Construction, Human, Object, Road, Sign, Sky, Terrain, Vegetation, Vehicle, Void, Water. *(Docs say "11 groups" but list 12 — verify whether Void is excluded.)* | Confirmed / count open |
| Instance annotation | On the most common *thing* classes only | Confirmed |
| **Annotated modalities** | **RGB images and LiDAR point clouds only. Radar, NIR, thermal and INS are released raw and unlabelled.** | Confirmed |
| Splits | train 7,830 / val 960 / test 1,210 | Confirmed |
| Label format | SemanticKITTI-style `.label`, uint32 packing semantic + instance IDs | Confirmed |
| Schema derived from | Label *format* follows SemanticKITTI; taxonomy stated as purpose-built, covering both outdoor and urban scenarios | Confirmed |

**Structure:** `setup` (platform + sensor suite) → `scenario` (one recording day) →
`sequence` (one ROS bag + YAML metadata).

---

## 5. Access and licence

| Field | Value | Status |
|---|---|---|
| Licence | CC BY-SA 4.0 (data) · MIT (code) | Confirmed |
| Non-commercial restriction | **No** — least restrictive of our candidates | Confirmed |
| Share-alike | **Yes** — derivative datasets must carry CC BY-SA 4.0 | Confirmed |
| Attribution required | Yes | Confirmed |
| Steps to obtain access | Direct download; no gating found | Confirmed |
| Egress cost | None identified; torrent mirror available | Confirmed |

**Handover implication.** The most permissive licence in our set — commercial use
allowed, no NoDerivatives clause, and the MIT devkit can be modified and redistributed
freely. Share-alike is the only real constraint: a derived dataset must stay CC BY-SA.
Publishing benchmark results is unaffected. **This makes GOOSE the safest dataset to
build shareable, reusable tooling around**, which matters given the handover
requirement — compare STONE (CC BY-NC-ND, no derivatives) and TruckDrive (Torc NC).

---

## 6. Tooling and feasibility — **PASSED** 22 Aug 2026

| Field | Value |
|---|---|
| Devkit install attempted? | **Yes** |
| Install outcome | **Worked** |
| OS and environment | macOS 24.6 (Apple Silicon), Python 3.11 in `~/.venvs/radar` |
| Dependencies added | `vispy 0.16.2`, `PyQt5`. **No CUDA required** |
| Data used | `goose_3d_val.zip`, 3.3 GB — integrity verified, 1,925 files |
| Extracted contents | **961 point clouds + 961 labels** in `lidar/val/`, `labels/val/` |
| **Frame loaded and visualised?** | **Yes — two frames, two different scenarios** |
| Evidence | [`goose_frame_000.png`](../evidence/goose_frame_000.png) · [`goose_frame_500.png`](../evidence/goose_frame_500.png) |
| Tooling written | [`scripts/goose_render_frame.py`](../../scripts/goose_render_frame.py) |
| Hours spent | ~1 session, mostly download time |

**Result.** `2022-07-22_flight__0071` — 169,883 points, 17 classes, dominated by bush
35.9%, low_grass 20.6%, high_grass 19.7%, hedge 12.1%, asphalt 6.1%.
`2022-12-07_aying_hills__0124` — 200,915 points, a winter scene with snow: forest
34.6%, building 24.9%, soil 9.0%. Both render coherently — a driveable track through
vegetation, ego vehicle at the origin.

**Empirical range.** Labelled points extend to roughly **±200 m** in both frames
(frame 000: x ∈ [−192, 198] m). Section 2 previously recorded max annotation range as
"not found"; this is measured, not published, but it shows GOOSE is not a short-range
dataset. Point density at that distance is sparse — do not read it as usable
long-range supervision without checking.

### Three gotchas — for the installation log (FA-3)

None blocked the work, but each costs an hour if hit cold.

1. **The visualiser looks for `labels_challenge/`; the split ships `labels/`.**
   `pointcloud_processing/tools/visualize_3d_data.py` defaults to a directory the
   download does not contain, and exits reporting a missing sequence folder.
2. **Two taxonomies, and mixing them fails silently.** The bundled
   `common/goose_kitti-visualizer.yaml` is an **8-class** challenge remap with a **BGR**
   colour map. The downloaded labels are the **full 64-class** set, described by
   `goose_label_mapping.csv` with **hex** colours. Colouring 64-class labels with the
   8-class map renders most of the scene as unknown **without raising an error**.
   Anyone comparing GOOSE class counts against another dataset must say which taxonomy
   they mean.
3. **Scans and labels do not share a filename stem.** Scans end `_vls128.bin`, labels
   end `_goose.label`. The join key is everything up to the final underscore.

### The published baseline — attempted, and it runs

*Superseded 5 Sep. This section previously said the baselines were not runnable and
required Kaya, the DGX Spark or Colab. That was true of the survey machine and wrong
about the team.*

The point-cloud baseline (Pointcept / PTv3, `pointcloud_processing/README.md`) ships as
a Docker image tested against CUDA 11.7.

**It cannot run on Apple Silicon**, which has no CUDA path under any configuration —
recorded as
[`0005-ptv3-baseline-apple-silicon`](../../results/records/0005-ptv3-baseline-apple-silicon.json).
That is **R-08**, not a GOOSE problem, and it is cleanly separated from visualisation,
which needs only vispy.

**It does run on the team's GTX 1660**, 6 GiB, under WSL 2 — recorded as
[`0006-goose-ptv3-gtx1660-partial`](../../results/records/0006-goose-ptv3-gtx1660-partial.json)
with the full protocol in
[`experiment-log/0004`](../../experiment-log/0004-goose-ptv3-partial-validation.md).

| | |
|---|---|
| Precision | **FP32.** AMP failed with `!all_profile_res.empty() assert faild. can't find suitable algorithm for 0` |
| Bounded gates | Smallest frame (30,263 pts) 8.6 s; largest frame (270,720 pts) 35.4 s. **No out-of-memory** |
| Full attempt | **10 of 961 frames**, then stopped deliberately at Ricky's hardware-load limit |
| Throughput | ~18.9 s/frame, so a complete validation is **≈5.1 hours** of sustained GPU |

**So 6 GiB is sufficient, and time is the constraint rather than memory.** That is a
different answer from the one this survey previously gave, and it changes what we ask
the client for: not "can we have a machine", but "a complete run costs five hours of
sustained load on our only CUDA laptop".

### The raw ROS bags — resolved, and not in our favour

The annotated splits contain **LiDAR and labels only — no radar**. The paper says all
raw sensor data is released in ROS bag format, which is where the radar lives, so the
plan was to download one bag and list its topics.

That is no longer the fastest route to an answer, because the maintainers have given
one directly:

- **The released bags carry a reduced sensor set.** *"The ROS Bags available on the
  GOOSE DB only contain a minimal set of sensors to reduce the file sizes... We are
  still in the process of uploading and releasing the full raw sensor data."* A user
  inspecting them found even the **surround cameras** missing
  ([#17](https://github.com/FraunhoferIOSB/goose_dataset/issues/17)).
- **There is no convenient way to download them.** *"There is currently no convenient
  way to download the GOOSE ROS Bag data"* — the torrent has no seeders and a
  replacement download service is still being built
  ([#23](https://github.com/FraunhoferIOSB/goose_dataset/issues/23)).
- **They are ROS 1**, stated directly by the first author in
  [#18](https://github.com/FraunhoferIOSB/goose_dataset/issues/18).

`scripts/goose_bag_topics.py` is ready — pure Python, no ROS install — so the check
takes one command whenever the full raw data is published. Pursuing it was deliberately
**deferred** for Sprint 2: if the radar cannot be obtained, whether it is 4D imaging has
no practical bearing on the work. Recorded under risk R-24 and `decision-log.md` D-05.

---

## 7. Fit for this project

**Verdict: secondary, and the only one of our four datasets we can actually work on
today.** GOOSE is the off-road terrain dataset, the cheapest route to an Autoware demo,
and the one that answers the question Adrian asked at kickoff. It is not the dataset for
4D radar and not the dataset for long range, and it should never be planned as if it
were.

### What it can do

**1. Off-road terrain — drivable versus not.** This is its purpose and it works. All
eight validation scenarios render into coherent traversability views in which the
drivable points form a connected route, including dense woodland where that route is a
narrow ribbon. See
[`goose_traversability_sheet.png`](../evidence/goose_traversability_sheet.png) and the
client-facing version at
[`goose_client_figure.png`](../evidence/goose_client_figure.png).

The 64-class taxonomy separates terrain (asphalt, cobble, gravel, soil, snow) from
vegetation (low grass, high grass, bush, moss, tree root), which is ground-versus-not-
ground made explicit. Our own four-class mapping over it lives in
`GOOSE - Ricky+Damien/traversability_map.csv`.

**2. On-road → off-road transfer, as the target domain.** Fabian's stated interest. The
obstacle is task mismatch: on-road datasets are detection, GOOSE is segmentation, so
transfer needs a shared task formulation rather than reusing a detection head.

**3. The cheapest path to a running Autoware demo.** `DATASET_OVERVIEW.md:161` records
that no TruckScenes→ROS 2 converter exists and that writing one is likely real project
work. GOOSE distributes natively as ROS bags with published calibration.
**Now confirmed ROS 1, not ROS 2** — the dataset authors say so directly in
[issue #18](https://github.com/FraunhoferIOSB/goose_dataset/issues/18). Conversion is
still needed, but far less of it. Relevant to FZ-1 and KL-3 regardless of what happens
to the off-road strand.

### What it cannot do

**Decision D-04, the long-range question — no, for two independent reasons.** The task
is segmentation, so mAP by range band has no equivalent. And measured over all 961
frames and 174,891,807 labelled points (R2), **62.9% of points fall within 25 m and only
3.8% beyond 100 m, 1.1% beyond 150 m.** There is barely any data in the range band D-04
is about. This is a firmer answer than the survey previously gave and it should close
the question: nobody should propose GOOSE for D-04 later in the project.

**The 4D radar question — no.** See §5. The radar exists on the vehicle but is not
labelled, not in the annotated download, not in the reduced-sensor bags that are
currently obtainable, and never described as 4D imaging.

**Sensor fusion — no.** The authors have confirmed a bug in their export step: camera
and LiDAR of the same frame are not reliably time-aligned, and the ground-truth masks
**cannot be matched by projection using the published extrinsics**. Fusion work here
will produce broken results through no fault of the person doing it.

**Cross-dataset comparison — never.** Segmentation results must not share an axis with
TruckScenes or TruckDrive detection results (D-01, D-02).

### Limitations — read before building anything on this

| | |
|---|---|
| **Camera↔LiDAR misalignment** | Authors confirmed an export bug; masks cannot be matched by projection ([#18](https://github.com/FraunhoferIOSB/goose_dataset/issues/18)). Fusion is not viable |
| **Radar not obtainable** | Released bags carry a reduced sensor set; full raw data still unreleased; torrent has no seeders ([#17](https://github.com/FraunhoferIOSB/goose_dataset/issues/17), [#23](https://github.com/FraunhoferIOSB/goose_dataset/issues/23)) |
| **Bags are ROS 1** | Conversion required for ROS 2 / Autoware |
| **Data quality** | Some LiDAR scans are missing sections; at least one RGB frame is out of sequence |
| **Two taxonomies** | 64-class full set and an 8-class challenge remap ship together and are not interchangeable. Any reported number must say which it used |
| **Overhead projection misleads** | A plain bird's-eye view paints canopy over the ground beneath. Taking the lowest return per 0.4 m cell roughly **halves** the apparent blocked share — `aying_mangfall_2` goes 92% → 58% non-traversable. Any traversability metric from a raw BEV projection will systematically understate drivable ground |
| **Scenario is a confound** | Terrain type drives effective range more than weather does. Open farmland reaches 6.3% of points at 100–150 m; dense woodland has almost nothing past 50 m. Results from different scenarios are not comparable without saying which |
| **Class diversity varies 11 to 40** | `garching_2` has 11 classes present, `neubiberg_rain` has 40. A per-scenario mIoU is meaningless without stating the classes present (R5) |
| **Snow is one recording day** | `aying_mangfall_2` only. Nothing general can be said about snow from this dataset |
| **The rain/sunny pair is not a weather comparison** | Rain frames are *denser* and more consistent (198k, 193–202k) than sunny (134k, 69–206k). The routes differ, so scene content dominates. Do not cite it as weather robustness |
| **Frame count discrepancy** | Published metadata says 960 validation frames; the downloadable archive contains 961 paired files. We use the archive count |
| **GOOSE-Ex is a different platform** | Excavator and quadruped, different sensor suites — a separate configuration under D-01 |

### Published baselines

The paper evaluates state-of-the-art 2D image segmentation and 3D single-scan
point-cloud segmentation. Live leaderboards exist for 2D semantic, 2D fine-grained
semantic, and 3D semantic segmentation. The bundled baseline is Pointcept / PTv3,
shipped as a Docker image tested against CUDA 11.7. *(Model names and scores — TODO,
needs the paper's results tables.)*

**The published 3D result is mIoU 0.8096** on the 8-class challenge taxonomy
(`pointcloud_processing/README.md`). **We have not reproduced it**, and the reasons are
worth separating:

1. **The pipeline is not the obstacle.** PTv3 runs on the team's GTX 1660 in FP32. See
   §6 — 6 GiB is sufficient and a complete validation is a ~5.1 hour job.
2. **The run was stopped at 10 of 961 frames**, so what we have is 1% of a split. Those
   values are recorded as diagnostics, not metrics.
3. **Even a completed run would not be directly comparable** to 0.8096 without
   recomputation. Pointcept averages IoU over classes with zero union; this repository's
   definition excludes them (`docs/metrics-definitions.md`). Two different numbers can
   be produced from identical predictions, so the definition must be stated.

So the honest position is: **the model runs, and we have no benchmark score.** Not
because of the hardware, but because we chose not to hold a student laptop at 99%
utilisation for five hours, and because the comparison needs a metric definition settled
first.

*(Model names and scores from the paper's results tables — TODO.)*

### Evidence

| Artefact | What it shows |
|---|---|
| [`goose_contact_sheet.png`](../evidence/goose_contact_sheet.png) | All 8 scenarios, 64-class view — the seasonal and terrain range |
| [`goose_traversability_sheet.png`](../evidence/goose_traversability_sheet.png) | All 8 scenarios as drivable / uncertain / blocked |
| [`goose_client_figure.png`](../evidence/goose_client_figure.png) | The client-facing figure: what the ground is made of, beside what a vehicle can drive on |
| [`goose_frame_000.png`](../evidence/goose_frame_000.png) · [`goose_frame_500.png`](../evidence/goose_frame_500.png) | Single-frame detail, summer and winter |
| `GOOSE - Ricky+Damien/dataset-statistics.md` | Full measurement over 961 frames and 174.9M points |
| [`results/records/0006-...json`](../../results/records/0006-goose-ptv3-gtx1660-partial.json) | The bounded PTv3 run: what executed, what was stopped, and why |
| [`experiment-log/0004`](../../experiment-log/0004-goose-ptv3-partial-validation.md) | Full protocol, gates and the runtime patch for that run |

---

## 8. Open questions and sources

**Open questions**

- [x] ~~Does GOOSE have radar?~~ **Yes** — six Smartmicro units, 360°, raw only.
- [x] ~~Are radar topics present in the distributed ROS bags?~~ **Effectively no** —
      the maintainers confirm the released bags carry a reduced sensor set and the full
      raw data is unpublished. See §6.
- [x] ~~Are the bags ROS 1 or ROS 2?~~ **ROS 1**, per the first author in
      [#18](https://github.com/FraunhoferIOSB/goose_dataset/issues/18).
- [ ] Are Smartmicro UMRR-96/UMRR-11 **4D imaging** or conventional automotive radar?
      **Deferred, not dropped** — with the radar unobtainable this has no bearing on
      current work. Ask Fabian when the full raw data is published.
- [ ] **For Adrian and Fabian:** both off-road candidates now carry radar — STONE with
      3× annotated 4D imaging radar, GOOSE with 6× unannotated automotive radar. D-03's
      premise that off-road datasets lack radar is **false**. Recommend re-scoping the
      off-road strand rather than treating it as blocked.
- [x] ~~Can the published baseline run on team hardware?~~ **Yes** — FP32 on a GTX 1660,
      6 GiB, ~18.9 s/frame. Memory is not the constraint; five hours of sustained load is.
- [ ] **Is a complete PTv3 reproduction worth five hours of a student laptop?** A
      client decision, put to Adrian in the 1 Sep note. If yes, it should run on remote
      or deliberately limited compute rather than sustained local load.
- [ ] Before any score is reported, settle whether we recompute under this repository's
      mIoU definition or quote Pointcept's. **They differ**, and identical predictions
      would produce two different numbers.
- [ ] Confirm whether higher-level class groups number 11 or 12
- [ ] Extract baseline model names and scores from the paper's results tables
- [ ] **Needs a human:** the client figure has not had a cold read by anyone outside
      this pair. Kelsey or Fatima should say what they think it shows before it goes to
      Adrian — D4's own acceptance test.

**Sources**

1. [GOOSE landing page](https://goose-dataset.de/) — 18 Aug 2026
2. [GOOSE documentation](https://goose-dataset.de/docs/) — structure, classes, setup
3. Mortimer et al., *The GOOSE Dataset for Perception in Unstructured Environments*,
   ICRA 2024 — [arXiv:2310.16788](https://arxiv.org/abs/2310.16788)
4. [FraunhoferIOSB/goose_dataset](https://github.com/FraunhoferIOSB/goose_dataset) —
   issues [#17](https://github.com/FraunhoferIOSB/goose_dataset/issues/17),
   [#18](https://github.com/FraunhoferIOSB/goose_dataset/issues/18),
   [#23](https://github.com/FraunhoferIOSB/goose_dataset/issues/23)
5. Initial client meeting transcript, 4 Aug 2026
6. `GOOSE - Ricky+Damien/dataset-statistics.md` — R2, all 961 frames, 27 Aug 2026
7. `GOOSE - Ricky+Damien/findings-damien.md` — D1/D3/D4 working notes
