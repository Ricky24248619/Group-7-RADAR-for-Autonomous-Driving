# Dataset Survey Template

**CITS3200 Group 07 · one survey per dataset · owner fills, another member reviews**

Copy this file to `docs/dataset-surveys/<dataset>.md`, fill it in, open a PR.

---

## Why the fields are fixed

Every entry uses the same fields in the same order so the six surveys can be read
side by side. If a field does not apply to your dataset, say so explicitly — do not
delete the row and do not leave it blank. A survey that silently drops a field is not
comparable to one that kept it.

Two of our recorded decisions depend on this document being precise:

- **D-01** requires every benchmark result to name its dataset, full sensor
  configuration and annotation schema. Sections 3 and 4 below are where those come
  from. If they are vague here, results built on them are not comparable later.
- **D-03** turns on whether an off-road dataset with radar exists at all. Section 2's
  `Radar present` and `Domain` fields are what answer it. Answer them carefully.

## Status vocabulary — use these words exactly

Every claim carries one of four statuses. Never leave a field blank, and never guess.

| Status | Means |
|---|---|
| **Confirmed** | You verified it yourself against a primary source. Link it. |
| **Unverified** | A source claims it; you have not checked. Link the claim. |
| **Not found** | You looked and could not find it. Say where you looked. |
| **N/A** | The category genuinely does not apply to this dataset. Say why. |

"Not found" is a real result, not a gap in your work. A dataset with no published
licence is a finding — record it as Not found and move on.

Every factual claim needs a source link. If you cannot link it, it is Unverified.

---
---

# Survey: `<DATASET NAME>`

## 0. Survey metadata

| | |
|---|---|
| Dataset | |
| Surveyed by | |
| Date surveyed | |
| Reviewed by | *(a member other than the surveyor)* |
| Review date | |
| Survey status | Draft / Reviewed |

---

## 1. Identity

| Field | Value | Status | Source |
|---|---|---|---|
| Official name | | | |
| Other names used | *(incl. what the client calls it)* | | |
| Authors / organisation | | | |
| Venue and year | | | |
| Paper | | | |
| Project page | | | |
| Devkit repository | | | |
| Data host | | | |

> **Naming note.** Adrian referred to datasets as "MAN" and "TORC"; published
> materials say "TruckScenes" and "TruckDrive". Record both names so no document
> ends up referring to two things that are one, or one thing that is two.

---

## 2. Fixed checklist — mandatory, complete every row

This is the comparable core. These rows must be filled for every dataset in the
project, and are what get lifted into the summary comparison table.

| Field | Value | Status | Source |
|---|---|---|---|
| **Domain** — on-road / off-road / both | | | |
| **Radar present** — Yes / No | | | |
| Radar type if present — 3D / 4D / N/A | | | |
| LiDAR present — Yes / No | | | |
| Camera present — Yes / No | | | |
| **Primary task** — detection / segmentation / tracking / planning / other | | | |
| **Annotation geometry** — 3D boxes / 2D boxes / semantic seg / instance seg / none | | | |
| **Licence** | | | |
| Commercial use permitted — Yes / No | | | |
| Share-alike obligation — Yes / No | | | |
| Access gating — open / account / licence acceptance / request | | | |
| **Total download size** | | | |
| Smallest usable subset and its size | | | |
| Data format(s) | | | |
| **Devkit available** — Yes / No | | | |
| Devkit language and licence | | | |
| Annotated frame count | | | |
| Max annotation range | | | |

---

## 3. Sensor configuration

Required by **D-01** as a mandatory field on every recorded result. Be specific —
"6 LiDAR" is not enough if the models mean different things.

| Modality | Count | Make / model | Key specs (range, rate, resolution) | Status | Source |
|---|---|---|---|---|---|
| Radar | | | | | |
| LiDAR | | | | | |
| Camera | | | | | |
| IMU / GNSS | | | | | |
| Other | | | | | |

**Coverage:** *(360°? forward only? state the arrangement.)*

**Calibration / extrinsics published:** *(Yes / No — needed for any fusion work.)*

---

## 4. Annotation schema

Also mandatory under **D-01**.

| Field | Value | Status | Source |
|---|---|---|---|
| Annotation type | | | |
| Class count and taxonomy | | | |
| Are classes grouped / regrouped? | | | |
| Attributes per object | | | |
| Objects tracked across frames? | | | |
| Splits provided (train/val/test) | | | |
| Annotated vs unannotated frame counts | | | |
| Schema derived from another dataset? | | | |

> If the schema derives from nuScenes or KITTI, say so — it usually means existing
> models and tooling port across with modest effort, which materially changes effort
> estimates.

---

## 5. Access and licence

| Field | Value | Status | Source |
|---|---|---|---|
| Licence name and version | | | |
| Link to licence text | | | |
| Non-commercial restriction? | | | |
| Restrictions on downstream / handover use | | | |
| Attribution required? | | | |
| Steps to obtain access | | | |
| Time from request to access | | | |
| Egress or bandwidth cost | | | |

**Handover implication.** This project is handed to a subsequent team. State plainly
whether that team could still use this dataset and any results derived from it, or
flag it for Adrian if unclear. Do not assume.

---

## 6. Tooling and feasibility

Record what actually happened, not what should have happened. **A failed install is a
first-class result** — log it here and in the installation problems log (FA-3).

| Field | Value |
|---|---|
| Devkit install attempted? | Yes / No |
| Install outcome | Worked / Failed / Partial |
| OS and environment used | |
| Python / CUDA / dependency versions | |
| Errors encountered | *(exact messages)* |
| Fixes attempted | |
| Hours spent | |
| **Single frame loaded and visualised?** | Yes / No |
| Evidence | *(screenshot path, notebook, or log link)* |
| Recommended next step | |

> Proving one frame loads is enough to demonstrate feasibility. Do not build a
> pipeline to answer this section.

---

## 7. Fit for this project

Judgement, not description. Be direct — a negative verdict is useful.

**Supports the D-04 long-range question?** *(Do models degrade past ~150 m, and does
4D radar degrade less than LiDAR? A dataset with no radar, or with annotation range
under ~150 m, cannot test this. Say so.)*

**Supports the D-03 off-road direction?** *(Off-road terrain, ground vs not-ground,
drivable edges, negative obstacles. Note whether it carries radar — an off-road
dataset without radar answers only half the question.)*

**Supports on-road → off-road transfer?** *(Fabian's stated interest. Would this
dataset serve as a source or target domain?)*

**Published baselines available?** *(Model names, task types, headline numbers. Task
type matters — under D-02 we compare only within a task type.)*

**Blockers:**

**Verdict:** Primary candidate / Secondary / Reference only / Not suitable — *and one
sentence of why.*

---

## 8. Open questions and sources

**Open questions** *(anything needing Adrian or Fabian — flag rather than assume)*

- [ ]

**Sources**

1.

---

## Before you open the PR

- [ ] Every row in Section 2 has a value and a status — none blank
- [ ] Every Confirmed claim has a link
- [ ] Sensor configuration (§3) and annotation schema (§4) are specific enough to
      paste into a results record under D-01
- [ ] Failed installs recorded in §6 rather than omitted
- [ ] Verdict in §7 is stated plainly, including if it is "not suitable"
- [ ] Open questions listed in §8 rather than resolved by guesswork
