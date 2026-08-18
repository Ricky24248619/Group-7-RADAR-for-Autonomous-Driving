# Survey: STONE

> **Stub — not owned by DZ.** Pre-filled on 18 Aug 2026 with facts verified from the
> project repository so the pair taking STONE starts from evidence rather than a blank
> page. **Everything marked TODO is still yours to do**, and the Confirmed rows should
> be spot-checked rather than trusted. Follow
> [`../dataset-survey-template.md`](../dataset-survey-template.md).

## 0. Survey metadata

| | |
|---|---|
| Dataset | STONE |
| Surveyed by | *(TODO — assign)* |
| Date surveyed | Stub 2026-08-18 |
| Reviewed by | *(must be from a different pair)* |
| Survey status | **Stub** |

Bears on decision **D-03** and risk **R-24** *(R-24 owner: DZ — flag findings to him)*

---

## 1. Identity

| Field | Value | Status | Source |
|---|---|---|---|
| Official name | STONE | Confirmed | [konyul/STONE](https://github.com/konyul/STONE) |
| Venue and year | **ICRA 2026** (accepted) | Confirmed | repo |
| Authors / organisation | *(TODO)* | Not found | |
| Paper | *(TODO)* | Not found | |
| Devkit repository | https://github.com/konyul/STONE | Confirmed | direct |
| Data host | *(TODO)* | Not found | |

---

## 2. Fixed checklist

| Field | Value | Status | Source |
|---|---|---|---|
| **Domain** | **Off-road** — grassland, farmland, construction sites, lakes; day and night | Confirmed | repo |
| **Radar present** | **Yes — 3× 4D imaging radar** | Confirmed | repo |
| Radar type | **4D imaging**, Continental **ARS 548 RDI** | Confirmed | repo |
| LiDAR present | Yes — 1× Hesai OT128, 128-channel | Confirmed | repo |
| Camera present | Yes — 6× RGB, surround view | Confirmed | repo |
| **Primary task** | **Voxel-level 3D traversability prediction** | Confirmed | repo |
| **Annotation geometry** | Voxel-level, 4 traversability classes: Free, Traversable, Potentially Traversable, Non-Traversable. **No 3D bounding boxes** | Confirmed | repo |
| **Licence** | **CC BY-NC-ND 4.0** (data) · Apache 2.0 (code) | Confirmed | repo |
| Commercial use permitted | **No** | Confirmed | licence |
| Share-alike obligation | N/A — ND instead, see §5 | Confirmed | licence |
| Access gating | *(TODO)* | Not found | |
| **Total download size** | *(TODO)* | Not found | |
| Smallest usable subset | *(TODO)* | Not found | |
| Data format(s) | Repository conventions follow nuScenes / Occ3D-nuScenes | Confirmed | repo |
| **Devkit available** | Yes — Apache 2.0 | Confirmed | repo |
| Annotated frame count | *(TODO)* | Not found | |
| Max annotation range | *(TODO)* | Not found | |

---

## 3. Sensor configuration

| Modality | Count | Make / model | Key specs | Status |
|---|---|---|---|---|
| **Radar** | **3** | Continental **ARS 548 RDI** | 4D imaging | Confirmed |
| LiDAR | 1 | Hesai OT128 | 128 channels | Confirmed |
| Camera | 6 | *(TODO)* | Surround view | Confirmed / models TODO |
| GNSS / INS / IMU | *(TODO)* | | | Confirmed present |

**Coverage / arrangement:** *(TODO)* · **Calibration published:** *(TODO)*

> **Note for whoever takes this.** The ARS 548 is the same Continental family as
> TruckDrive's ARS540, and `DATASET_OVERVIEW.md:158` records an existing ROS 2 driver
> ([ars548_ros](https://github.com/robotics-upo/ars548_ros)). That is a real bridge to
> the Autoware strand — worth telling Fariya (FZ-1) and Kelsey (KL-3).

---

## 4. Annotation schema — TODO

Class definitions, splits, frame counts, voxel resolution. Note the repo follows
**Occ3D-nuScenes** conventions, so occupancy-prediction tooling may port across —
verify, because it materially changes effort estimates.

---

## 5. Access and licence

| Field | Value | Status |
|---|---|---|
| Licence | **CC BY-NC-ND 4.0** | Confirmed |
| Non-commercial restriction | **Yes** | Confirmed |
| **NoDerivatives** | **Yes — the binding constraint** | Confirmed |
| Code licence | Apache 2.0 | Confirmed |

> ⚠️ **Raise before downloading.** *NoDerivatives* is stricter than anything else we
> are using — stricter than TruckDrive's non-commercial licence. Publishing benchmark
> results is fine, but redistributing modified or converted data is not: **no converted
> copy of STONE can be committed to the repository**, including ROS 2 bag conversions
> or repackaged subsets. That collides with the handover requirement (P-5: a person
> outside the team clones the repo and reproduces a result).
>
> The register covers TruckDrive's licence at R-04 but has **nothing for STONE**. It
> needs a new risk with an owner, and a written question to Adrian alongside the R-04
> one Fatima owns. We would then be carrying four incompatible licences: CC BY-SA
> (GOOSE), CC BY-NC-SA (TruckScenes), Torc NC (TruckDrive), CC BY-NC-ND (STONE).

---

## 6. Tooling and feasibility — TODO

Install the devkit, load one frame, screenshot. Record failures as results.

---

## 7. Fit for this project

**Why this is the most important survey right now.** STONE is the only candidate that
is off-road *and* carries annotated 4D imaging radar. Decision D-03 was written on the
premise that the client's off-road preference and the project's radar focus could not
be served by the same dataset. **STONE shows that premise is false**, and GOOSE's raw
360° radar reinforces it. Getting this survey done unblocks Sprint 2 planning.

Its task — voxel-level traversability across Free / Traversable / Potentially
Traversable / Non-Traversable — is close to a direct restatement of what Adrian asked
for at kickoff: *"what is ground, what is not the ground, what can I drive over, what
can I crash into... there is an edge and you can drive off it."*

**Supports D-04 (long-range)?** *(TODO — depends on annotation range. Probably not:
traversability, not detection, and off-road ranges are typically short.)*

**Supports D-03 (off-road)?** **Yes — strongest candidate.**

**Published baselines?** *(TODO.)*

**Verdict:** *(TODO — but on current evidence, likely primary for the off-road strand.)*

---

## 8. Open questions

- [ ] Annotation range, frame count, splits, download size
- [ ] Is radar **annotated**, or present raw alongside LiDAR-derived labels?
- [ ] Access route — is data actually downloadable yet, or paper-only pre-ICRA?
- [ ] **For Adrian:** CC BY-NC-ND vs our handover requirement (see §5)
- [ ] Does the Occ3D-nuScenes convention let existing occupancy models run directly?

**Sources**

1. [konyul/STONE](https://github.com/konyul/STONE) — retrieved 18 Aug 2026
