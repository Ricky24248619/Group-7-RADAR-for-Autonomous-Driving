# Survey: GOOSE (German Outdoor and Offroad Dataset)

> **Reference example** for [`../dataset-survey-template.md`](../dataset-survey-template.md).
> Sections 1–5 and 7 are complete. Section 6 is deliberately empty — the feasibility
> test has not been run. Note how uncertain facts are marked rather than guessed.

## 0. Survey metadata

| | |
|---|---|
| Dataset | GOOSE (+ GOOSE-Ex extension) |
| Surveyed by | Damien Zhang (DZ) |
| Date surveyed | 2026-08-18 |
| Reviewed by | *(pending — must be a member other than DZ)* |
| Review date | |
| Survey status | Draft |

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
| Max annotation range | Not stated; bounded by LiDAR range | Not found | — |

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

## 6. Tooling and feasibility

**Not yet attempted.** Per DZ-2's acceptance test, visualising a single frame locally
is sufficient — do not build a pipeline to answer this.

| Field | Value |
|---|---|
| Devkit install attempted? | No — pending |
| Install outcome | |
| OS and environment used | |
| Errors encountered | |
| Hours spent | |
| **Single frame loaded and visualised?** | No — pending |
| Evidence | |

**Priority feasibility task — inspect one raw ROS bag.** The paper says all raw sensor
data is released in ROS bag format. Download one sequence bag and list its topics
(`rosbag info` / `ros2 bag info`). This single command answers the highest-value open
question in this survey: whether radar topics are actually present in the distributed
bags, and whether they are ROS 1 or ROS 2. Budget under a day.

---

## 7. Fit for this project

**Supports the D-04 long-range question?** **No.** D-04 asks whether 3D detection
collapses beyond ~150 m. GOOSE's longest-range radar reaches 175 m and the other five
stop at 55 m, and the dataset provides segmentation rather than 3D boxes, so mAP by
range band has no direct equivalent. Wrong dataset for D-04.

**Supports the D-03 off-road direction?** **Yes — more than first assessed.** GOOSE is
a genuine off-road dataset whose class taxonomy is built around exactly the problem
Adrian described in the kickoff: terrain classes (asphalt, cobble, gravel, soil, snow)
separated from vegetation classes (low grass, high grass, bush, moss, tree root), which
is ground-versus-not-ground and drivable-versus-not made explicit. And it carries 360°
radar in the raw bags. The gap is that **the radar is unlabelled** — any radar work
here is unsupervised, cross-modal, or requires our own annotation.

**Supports on-road → off-road transfer?** Plausibly as a **target** domain — Fabian's
stated interest. Obstacle: on-road datasets are detection, GOOSE is segmentation, so
transfer needs a shared task formulation rather than reusing a detection head.

**Unexpected finding — GOOSE ships ROS bags natively.** `DATASET_OVERVIEW.md:161`
records that no TruckScenes→ROS 2 converter exists and that writing one is likely a
real chunk of project work. GOOSE sidesteps that entirely: its native distribution
format *is* ROS bags with published calibration. If the Autoware strand (FZ-1, KL-3)
proceeds, **GOOSE is the cheapest path to a working Autoware demo** by a wide margin.
Worth telling Fariya and Kelsey regardless of what happens to the off-road strand.
Caveat: ROS 1 vs ROS 2 is unconfirmed — a ROS 1 bag needs conversion, which is routine
but not free.

**Published baselines.** The paper evaluates state-of-the-art 2D image segmentation and
3D single-scan point-cloud segmentation. Live leaderboard competitions exist for 2D
semantic, 2D fine-grained semantic, and 3D semantic segmentation. *(Model names and
scores — TODO, needs the paper's results tables.)*

**Blockers:**
- Radar is **unlabelled** — no supervised radar task available out of the box
- Radar is Smartmicro automotive, **not confirmed as 4D imaging** — may not serve a
  project focused on 4D RADAR specifically
- Segmentation, not detection — under D-01 must never share an axis with
  TruckScenes/TruckDrive detection results
- GOOSE-Ex platforms have different sensor suites — separate configurations

**Verdict:** **Secondary — off-road terrain baseline and Autoware entry point.** Not
the dataset for the 4D radar question, and not for D-04. But it is a strong off-road
terrain dataset with the most permissive licence in our set, native ROS bag
distribution, and raw 360° radar available for unsupervised or cross-modal work. Its
best use is as the radar-free-*labelled* off-road baseline that STONE's 4D radar
results are compared against.

---

## 8. Open questions and sources

**Open questions**

- [x] ~~Does GOOSE have radar?~~ **Yes** — six Smartmicro units, 360°, raw only.
- [ ] **Highest value:** are radar topics actually present in the distributed ROS bags?
      Answered by `rosbag info` on one sequence. Owner: DZ.
- [ ] Are the bags ROS 1 or ROS 2? Determines conversion cost for the Autoware strand.
- [ ] Are Smartmicro UMRR-96/UMRR-11 **4D imaging** radars (elevation channel) or
      conventional 3D automotive radar? The paper does not say. Needs the datasheets.
      **This determines whether GOOSE counts toward the project's 4D RADAR focus at
      all** — put it to Fabian.
- [ ] **For Adrian and Fabian:** both off-road candidates now carry radar — STONE with
      3× annotated 4D imaging radar, GOOSE with 6× unannotated automotive radar. D-03's
      premise that off-road datasets lack radar is **false**. Recommend re-scoping the
      off-road strand rather than treating it as blocked.
- [ ] Confirm whether higher-level class groups number 11 or 12
- [ ] Extract baseline model names and scores from the paper's results tables

**Sources**

1. [GOOSE landing page](https://goose-dataset.de/) — 18 Aug 2026
2. [GOOSE documentation](https://goose-dataset.de/docs/) — structure, classes, setup
3. Mortimer et al., *The GOOSE Dataset for Perception in Unstructured Environments*,
   ICRA 2024 — [arXiv:2310.16788](https://arxiv.org/abs/2310.16788)
4. [FraunhoferIOSB/goose_dataset](https://github.com/FraunhoferIOSB/goose_dataset)
5. Initial client meeting transcript, 4 Aug 2026
