# Decision Log

Every decision that constrains how the work is done, recorded so it is visible
to the client, the team, and the team that inherits this project. D-01 to D-04
were made in Sprint 1 and first recorded in the Scope of Work (OneDrive,
`General/Group_07/`); this file is the living copy. New decisions are appended,
never edited in place — superseding a decision gets a new entry referencing the
old one.

Format: **ID — title** / date / status / decision / reasoning / raised by.

---

## D-01 — Basis of comparison: model performance, not sensor hardware
**Date:** Sprint 1 (by 12 Aug 2026) · **Status:** to be confirmed with Fabian before benchmarking begins

**Decision.** Compare model performance on annotated data, treating sensor
modality as a variable *within* a single dataset — same dataset, same
annotations, same split, differing modality. Raw sensor hardware comparison is
a documented literature exercise (WS1), not benchmark numbers.

**Enforcement.** Results from different datasets are never plotted on a shared
axis without an explicit statement of what differs. Every recorded result names
its dataset, sensor configuration and annotation schema (mandatory fields in
the comparison template; the source of truth for those is each dataset survey,
§3–§4). Cross-dataset observations are qualitative commentary, labelled as such.

**Reasoning.** TruckScenes (6 LiDAR, 6 radar, 4 camera) and TruckDrive (10 LiDAR,
10 radar, 11–15 camera) do not share a sensor configuration, so results on one
are not directly comparable to results on the other.

**Raised by:** Fariya Zehrin, Sprint 1 review.

---

## D-02 — Candidate detection models, and a gap worth reporting
**Date:** Sprint 1 (by 12 Aug 2026) · **Status:** active; radar-baseline gap to be confirmed with Fabian

**Decision.** Candidate models are TransFusion-L, BEVFusion, Far3D, DINO,
CenterPoint, MUTR3D and UniAD (named in the TruckDrive materials). They span
several task definitions (LiDAR 3D detection, camera–LiDAR fusion, camera
long-range 3D detection, 2D detection, multi-camera 3D tracking, end-to-end),
so comparison happens only within a task type, recorded alongside every result.

**Gap.** None of these candidates is radar-first; radar appears at best as a
fusion input. The possible absence of an off-the-shelf radar detection baseline
is itself a finding — confirm with Fabian, report to Adrian early.

**Raised by:** team, Sprint 1 dataset research.

---

## D-03 — Off-road direction: client preference vs dataset reality
**Date:** Sprint 1 (by 12 Aug 2026) · **Status:** materially updated by D-05

**Decision.** Off-road (mine sites, forests; ground-vs-not-ground, drivable
terrain; on-road→off-road transfer) is the client's preferred direction, kept
as active investigation rather than committed scope until the dataset question
is resolved with Adrian and Fabian.

**Sprint-1 premise.** "The datasets that carry radar are on-road highway
datasets" — off-road + radar was believed not to exist. **D-05 corrects this:
the premise is false.**

**Raised by:** team with client input, Sprint 1.

---

## D-04 — Research question: the long-range gap
**Date:** Sprint 1 (by 12 Aug 2026) · **Status:** to be confirmed with Fabian before being committed as the headline question

**Decision.** The project's testable question: do current models fail beyond
~150 m (TruckDrive reports 31–99% drops on 3D perception; benchmarks to 1000 m
/ 2D and 400 m / 3D), and does 4D radar close that gap better than LiDAR?
Results by range band; empty bands show as gaps, not zeros; a negative answer
is a valid, reported outcome. **Dataset fit:** TruckDrive yes; TruckScenes
(>230 m annotation range) plausibly; GOOSE no (longest radar 175 m,
segmentation task); STONE no (±25.6 m voxel grid).

**Raised by:** from Fariya Zehrin's dataset research, Sprint 1.

---

## D-05 — Off-road strand after the STONE and GOOSE surveys
**Date:** week 5, 22 Aug 2026 · **Status:** recorded; client questions consolidated in `client-notes/2026-08-offroad-strand-update-DRAFT.md`

**Inputs:** DZ dataset surveys, 21–22 Aug (`docs/dataset-surveys/stone.md`,
`docs/dataset-surveys/goose.md`, Damien branch, pending merge) and the client's
11 Aug email ("happy for you to use other data sets IN ADDITION to GOOSE — but
not eliminating GOOSE").

**Findings recorded:**

1. **STONE is parked pending storage, not failed.** It is the only dataset
   found that is off-road *with annotated 4D imaging radar* (3× Continental
   ARS 548, delivered as separate ROS bags not aligned to labels). Blocked on:
   322.6 GiB monolithic zip, no sample split (~645 GiB working space needed),
   no devkit (repo contains no code; maintainers unanswered since March),
   CC BY-NC-ND licence that may collide with the P-5 handover requirement. Its
   traversability voxel grid spans ±25.6 m, so it can never serve D-04.
2. **GOOSE is feasible and secondary.** Devkit installed, data downloaded,
   frames rendered, evidence attached (22 Aug). Carries six Smartmicro radars,
   360°, raw and **unlabelled**, **not confirmed as 4D imaging**. Task is
   semantic segmentation (no 3D boxes). Native ROS-bag distribution makes it
   the cheapest path to an Autoware demo (FZ-1 / KL-3). Wrong dataset for both
   D-04 and the 4D-radar benchmark question.
3. **D-03's premise is corrected.** Off-road radar exists in two forms —
   annotated 4D imaging (STONE) and raw unannotated (GOOSE). The off-road
   strand is viable, not blocked; it becomes a **resourcing question** (storage
   decides STONE) and a **definition question** (is GOOSE's radar 4D at all?).

**Decisions:**

- Damien proceeds with GOOSE as the off-road terrain baseline and Autoware
  entry point, satisfying the client's GOOSE requirement.
- STONE is not downloaded to any laptop; storage is resolved first
  (Kaya / DGX Spark / lab storage — a client question).
- Off-road strand re-scoping is raised with Adrian and Fabian at the next
  meeting via the client note, rather than treated as blocked.

**Open items:** ~645 GiB storage for STONE (client) · Smartmicro UMRR 4D or
not (Fabian) · STONE licence vs P-5 (client) · radar topics present in GOOSE
bags + ROS 1 vs 2 (`rosbag info`, DZ).

**Raised by:** Damien Zhang (surveys); consolidated and recorded by Ricky Yuen.

---

## D-06 — STONE dropped from the current plan
**Date:** reported team meeting 29 Aug 2026; recorded here 5 Sep 2026 · **Status:** team-reported decision; client notification unverified

**Decision.** Supersede D-05's storage-only hold: STONE is dropped from the current
plan, revisitable if access, tooling and licence/handover blockers change. It is not
disproved as an off-road radar dataset.

**Evidence.** The proposed 30 August GOOSE client note (PR #13), the revised scope
in PR #22 and the replacement draft in PR #18 report the meeting outcome. A draft
note is not evidence of delivery to Adrian; record a dated sent communication separately.

**Recorded by:** Ricky Yuen, reconciling the review documents; meeting outcome reported by Damien Zhang.

---

## D-07 — Proposed Autoware deferral
**Date:** 5 Sep 2026 · **Status:** Sprint 3 proposal in the revised scope; team confirmation pending

**Proposal.** Defer Autoware feasibility while the team completes dataset and baseline
work. Revisit Linux/ROS 2 access and dataset conversion before scheduling it. GOOSE's
released ROS 1 bags are not directly a ROS 2/Autoware input.

**Evidence.** Revised Scope of Work §7 and Revised Set of Stories in PR #22. These
documents propose the schedule; this entry does not claim client approval or a booked run.

**Recorded by:** Ricky Yuen, from Damien Zhang's revised scope.

---

## D-08 — Sprint 2 work organised by dataset pair
**Date:** 5 Sep 2026 (retrospective record) · **Status:** current working structure; future epic schedule proposed

**Decision.** Record the structure used in Sprint 2: Damien/Ricky on GOOSE,
Aiden/Fatima on TruckScenes and Fariya/Kelsey on TruckDrive. Work is evidenced by
PRs #17, #21 and #23. The revised scope proposes returning to epics in Sprint 3;
confirm that schedule at the checkpoint.

**Client communication.** The proposed 30 August note does not establish notification.
A dated sent communication is still needed for that part of P-7.

**Recorded by:** Ricky Yuen, from the dataset work and Damien Zhang's revised scope.

---

## D-09 — Record work and variance while client approval is pending
**Date:** 5 Sep 2026 (retrospective record) · **Status:** working position reported in the revised scope; client approval pending

**Decision.** Record completed work, blockers and proposed scope changes while approval
remains unresolved. This does not make the revised scope client-approved or satisfy
P-7's notification requirement. Keep the client note draft until its documented
review gates are met, then record when it is sent.

**Evidence.** Revised Scope of Work §1/§9, the unsent client notes and PR #18's
survey/cold-read gates. No delivery date is inferred from a draft's filename.

**Recorded by:** Ricky Yuen, reconciling Damien Zhang's revised scope with the repository evidence.
