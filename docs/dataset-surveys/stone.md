# Survey: STONE

**A Scalable Multi-Modal Surround-View 3D Traversability Dataset for Off-Road Robot Navigation** · ICRA 2026

> **Status: blocked — no devkit exists.** Investigated 21 Aug 2026. The repository
> contains no code at all. The data, however, *is* downloadable via an undocumented
> link. Both findings are recorded below. Follow
> [`../dataset-survey-template.md`](../dataset-survey-template.md).

## 0. Survey metadata

| | |
|---|---|
| Dataset | STONE |
| Surveyed by | Damien Zhang (DZ) |
| Date surveyed | 2026-08-21 |
| Reviewed by | *(pending — must be from a different pair)* |
| Survey status | Draft — §6 is a **dated failure record** per RY-3 |

Bears on decision **D-03**, risks **R-24** (DZ), **R-03 / R-20** (storage, Kelsey), **R-08** (GPU, Aiden)

---

## 1. Identity

| Field | Value | Status | Source |
|---|---|---|---|
| Official name | STONE | Confirmed | [konyul/STONE](https://github.com/konyul/STONE) |
| Venue and year | **ICRA 2026** (accepted Feb 2026) | Confirmed | repo README |
| Authors | Park, Kim, Oh, Yu, J. Park, J. Park, Shin, Cho, Kim, **Choi (corresponding)** | Confirmed | README citation |
| Organisation | Seoul National University — [ADR Lab](https://adr.snu.ac.kr/faculty) | Confirmed | README |
| Paper | [final_paper_compressed.pdf](https://konyul.github.io/STONE-dataset/assets/paper/final_paper_compressed.pdf) | Confirmed | project page |
| Project page | https://konyul.github.io/STONE-dataset | Confirmed | direct |
| Code repository | https://github.com/konyul/STONE — **contains no code** | Confirmed | see §6 |
| Data host | Google Drive, single file `STONE.zip` | Confirmed | project page |

---

## 2. Fixed checklist

| Field | Value | Status |
|---|---|---|
| **Domain** | **Off-road** — grassland, farmland, construction sites, lakes; day and night | Confirmed |
| **Radar present** | **Yes — 3× 4D imaging radar.** Delivered as separate ROS bags, *not* in the sample tree — see §4 | Confirmed |
| Radar type | **4D imaging**, Continental **ARS 548 RDI** | Confirmed |
| LiDAR present | Yes — 1× Hesai OT128, 128-channel, 360° rotating | Confirmed |
| Camera present | Yes — 6× Basler ACE2 2A1920-51gcPRO | Confirmed |
| **Primary task** | Voxel-level **3D traversability prediction** | Confirmed |
| **Annotation geometry** | Voxel grid, 4 classes. **No 3D bounding boxes** | Confirmed |
| **Licence** | **CC BY-NC-ND 4.0** (data) · Apache 2.0 (code) | Confirmed |
| Commercial use | **No** | Confirmed |
| Access gating | **None.** README says "Google Form / Coming Soon"; the project page carries a live public Drive link | Confirmed |
| **Total download size** | **346.3 GB / 322.6 GiB**, one monolithic zip | Confirmed |
| Smallest usable subset | **None — no mini split.** All or nothing | Confirmed |
| Data format(s) | nuScenes-style JSON + `.jpg` + `.pcd.bin`; labels `.npz`; radar `.bag` | Confirmed |
| **Devkit available** | **No** | Confirmed |
| Annotated frame count | Not stated | Not found |
| **Max annotation range** | **±25.6 m** — see §7, this rules out D-04 | Confirmed |

---

## 3. Sensor and platform configuration

**Platform:** Bunker Pro **UGV** — a small tracked ground robot, *not* a truck.
Ubuntu 22.04, **ROS 2 Humble**.

| Modality | Count | Make / model |
|---|---|---|
| **Radar** | **3** | Continental **ARS 548 RDI** 4D imaging |
| LiDAR | 1 | Hesai OT128, 128-ch, 360° rotating |
| Camera | 6 | Basler ACE2 2A1920-51gcPRO |
| GNSS/INS | 1 | NovAtel PIM222A dual-antenna |
| IMU | 1 | EPSON G366P |

> The ARS 548 is the same Continental family as TruckDrive's ARS540, and
> `DATASET_OVERVIEW.md:158` records an existing ROS 2 driver
> ([ars548_ros](https://github.com/robotics-upo/ars548_ros)). With the platform already
> on **ROS 2 Humble**, this is the most Autoware-ready dataset we have found — relevant
> to Fariya (FZ-1) and Kelsey (KL-3).

---

## 4. Annotation schema

| Field | Value |
|---|---|
| Classes | **4** — 0 Free, 1 Traversable, 2 Potentially Traversable, 3 Non-Traversable |
| Label file | `labels.npz` per frame token |
| Voxel size | 0.2 × 0.2 × 0.2 m |
| **Range** | **[−25.6, −25.6, −2.0] → [25.6, 25.6, 4.4] m** |
| Volume | 256 × 256 × 32 |
| Labelling | Automated pipeline, trajectory-guided; geometry-aware (slope, elevation, roughness) |
| Convention | Follows **nuScenes** and **Occ3D-nuScenes** |

**Structure:** `gts/[scene]/[frame_token]/labels.npz` · `samples/{CAM_BACK,
CAM_BACK_LEFT, CAM_BACK_RIGHT, CAM_FRONT, CAM_FRONT_LEFT, CAM_FRONT_RIGHT,
LIDAR_TOP}` · `v1.0-trainval/*.json` (nuScenes schema).

> ⚠️ **Radar is not in the `samples/` tree.** The sample modalities are six cameras and
> `LIDAR_TOP` only; radar ships separately as `.bag` files. So the voxel labels are not
> pre-aligned to radar frames — using radar means timestamp synchronisation and
> extrinsics work of our own. **For a radar-focused project this is the single most
> important caveat in this survey.** Same pattern as GOOSE.

---

## 5. Licence

**CC BY-NC-ND 4.0** — non-commercial *and* **NoDerivatives**, the strictest in our set.

Publishing benchmark results is fine. Redistributing modified or converted data is not:
**no converted copy of STONE may be committed to the repository**, including ROS 2 bag
conversions or repackaged subsets. That collides with **P-5** (someone outside the team
clones the repo and reproduces a result). The register still has **no risk covering
STONE's licence** — R-04 covers TruckDrive only. Needs raising with Adrian alongside
Fatima's R-04 question.

---

## 6. Tooling and feasibility — **dated failure record**

**Attempted:** 21 Aug 2026 · **Outcome:** blocked, not attributable to our environment.

### Finding 1 — there is no devkit

`konyul/STONE` contains **only** `README.md` and `assets/` (logo, teaser images, robot
setup diagram, the paper PDF, two videos). No source files, no `requirements.txt`, no
install instructions. One branch (`main`), **no tags, no releases**. Last push
2026-03-12 — over five months ago.

The README's acknowledgement credits **MMDetection3D**, so any future release will
almost certainly be an MMDet3D fork. That matters for planning: MMDet3D is a heavy,
version-sensitive, **CUDA-dependent** install (see R-08).

### Finding 2 — the maintainers are not responding

Three open issues, **zero replies**:

| # | Opened | By | Asking |
|---|---|---|---|
| 3 | 2026-07-20 | megumin-cloud | Estimated release date |
| 2 | 2026-05-04 | Frunkyzhong | Download link failing — rate-limited |
| 1 | 2026-03-11 | NielsRogge (Hugging Face) | Release dataset + baselines on HF |

Issue #2 confirms a download link has existed since at least May, despite the README
still saying "Coming Soon".

### Finding 3 — the data *is* public, and the README doesn't say so

The **project page** (not the README) links a public Google Drive file:

```
https://drive.google.com/file/d/1LdzE-BqZeEr2Vc9_z1CfiY5IjdqvX_CN/view
```

Verified 21 Aug 2026: resolves to `STONE.zip`, returns Google's "virus scan warning"
interstitial — the standard response for a **large public file** — and serves a ranged
request without authentication. **No Google Form, no approval step.**

```
content-disposition: attachment; filename="STONE.zip"
content-range: bytes 0-0/346343831255      →  346.3 GB  /  322.6 GiB
```

### Finding 4 — it does not fit on a team laptop

| | |
|---|---|
| `STONE.zip` | **322.6 GiB** |
| Free space on the survey machine | **229 GiB** |
| Needed to download *and* extract | **~645 GiB** |

There is **no mini or sample split** — the smallest obtainable unit is the entire
dataset. This is a storage problem before it is a tooling problem.

### Recommended next steps

1. **Do not download to a laptop.** Resolve storage first — this is R-03 / R-20
   (Kelsey). Concrete requirement: **~645 GiB of working space.** Candidates: external
   SSD, UWA network drive, Kaya (now unblocked — Adrian has agreed to act as PI), or
   the DGX Spark workstation.
2. **Email the corresponding author** (Jun Won Choi, SNU ADR Lab) asking whether a
   sample split exists and when code will be released. Three GitHub issues have gone
   unanswered, so email is the better channel. Cheap, and unblocks the whole strand.
3. **Do not wait on a reply to make progress.** See §7 verdict.

---

## 7. Fit for this project

**Supports D-04 (long-range)?** **No — definitively.** The voxel grid spans **±25.6 m**.
D-04 asks whether perception collapses beyond ~150 m. STONE's entire annotated volume
ends at a sixth of that distance. It cannot test the question at any range band that
matters.

**Supports D-03 (off-road)?** **Yes — still the strongest candidate.** It remains the
only dataset we have found that is off-road *and* carries annotated 4D imaging radar,
and its four traversability classes restate Adrian's kickoff framing almost exactly:
*"what is ground, what is not the ground, what can I drive over, what can I crash
into."* The caveats are that radar is unaligned (§4) and the platform is a small UGV
rather than a truck.

**Supports on-road → off-road transfer?** Weakly. Different task (traversability
occupancy vs detection), different platform scale, different range regime. Fabian's
transfer question would need a shared task formulation.

**Blockers:** no devkit · 322.6 GiB single download · no sample split · maintainers
unresponsive · radar not pre-aligned to labels · CC BY-NC-ND blocks committing derived
data · future code will be MMDet3D/CUDA, unusable on Apple Silicon.

**Verdict:** **Primary candidate for the off-road strand, but not actionable this
sprint.** The dataset is real, public and well matched to the client's stated interest.
Nothing about it can be run this week: there is no code to run, and the data will not
fit anywhere we currently have. Treat as **parked pending storage**, not as failed.

---

## 8. Open questions

- [ ] **For Adrian and Fabian:** STONE is the best off-road + 4D radar match and is
      blocked on storage, not on interest. Is ~645 GiB of working space obtainable —
      Kaya, DGX Spark, or lab storage? This decides whether the off-road strand is
      viable at all.
- [ ] **For Adrian:** CC BY-NC-ND vs the P-5 handover requirement (see §5)
- [ ] **For the authors:** does a sample/mini split exist? When is code released?
- [ ] Annotated frame count, splits, baseline model names and scores — in the paper PDF,
      not yet extracted
- [ ] Are the radar `.bag` files ROS 1 or ROS 2? Platform is ROS 2 Humble, so likely
      ROS 2 — worth confirming, it decides Autoware effort

**Sources**

1. [konyul/STONE](https://github.com/konyul/STONE) — README, tree, issues · 21 Aug 2026
2. [STONE project page](https://konyul.github.io/STONE-dataset) — Drive link
3. Drive HTTP headers, ranged request · 21 Aug 2026
4. `DATASET_OVERVIEW.md:158` — ARS 548 ROS 2 driver
