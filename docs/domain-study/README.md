# Domain study — WS1

**Workstream WS1 · story DZ-1 · owner Damien Zhang**

Six people watching six different sources, adding up to one survey instead of six
disconnected sets of notes. This file is the living index: the coverage matrix, who has
claimed which source, and the claims ledger.

**To add an entry:** copy Part 2 of
[`../domain-study-template.md`](../domain-study-template.md) into
`docs/domain-study/<yourname>-<source>.md`, fill it, add your row to the matrix below
and at least two rows to the claims ledger, then open a PR.

> **Status: 1 of 6 entries (29 September).** Bonn perception is in, written from the
> lecture transcripts. The other five sources are assigned but unclaimed. **P-2 stays at
> "partly met"** until enough entries exist for the matrix to show coverage rather than
> one source.

---

## Why this file exists separately from the template

The template previously held the coverage matrix and claims ledger inside itself, which
made one file both the blank form and the shared data store. Two problems with that:
six people appending rows to one file conflict on every PR, and the template stops being
copyable once it carries real data.

Same reasoning as the results store — *"One file per result, not one shared file…
Separate files never conflict."* Entries are separate files. This index carries only
the two tables that genuinely have to be shared, and the ledger is **append-only** so
two people adding rows at the bottom rarely collide.

---

## Part 1 — Coverage matrix

Add one row when you finish. One line. This is the at-a-glance artefact, and the
acceptance test is that **coverage gaps are visible without re-reading everything**.

| Source | Type | Who | Date | Radar | LiDAR | Camera | Fusion | Off-road | Depth |
|---|---|---|---|---|---|---|---|---|---|
| [Bonn SDC 2021 — Perception 1 & 2](damien-bonn-sdc2021.md) | Course | Damien | 2026-09-29 | ⚠️ | ✅ | ✅ | ❌ | ⚠️ | Medium (Shallow on radar) |

**Key:** ✅ covered in useful detail · ⚠️ mentioned only · ❌ not covered ·
Depth = Shallow / Medium / Deep

**Rating something Shallow is the correct answer when it was shallow.** Padding is
worse than a gap, because a gap is visible and padding is not.

---

## Source assignments

One source per person, not per pair, so six get covered. Claimed here to stop two
people watching the same thing — **put your name in the table and push, before you
start watching**.

| # | Source | Why this one | Proposed | Claimed |
|---|---|---|---|---|
| 1 | **Torc Robotics** keynote | They built TruckDrive. Highest relevance of any source here | Kelsey | |
| 2 | **Aurora** keynote | Trucking, sensor-first | Fariya | |
| 3 | **Kodiak Robotics** keynote | Trucking, and the off-road/defence work Adrian and Fabian care about | Aiden | |
| 4 | **Waabi** or **Plus** keynote | Deliberately contrasting approach | Fatima | |
| 5 | [Bonn — Self-Driving Cars 2021](https://www.ipb.uni-bonn.de/sdc-2021/index.html) | Academic, sensor fundamentals | Damien | Damien — [done](damien-bonn-sdc2021.md) |
| 6 | [Coursera — Self-Driving Cars specialisation](https://www.coursera.org/specializations/self-driving-cars) | Structured, longest — skim the sensor modules only | Ricky | |

Proposals, not assignments — swap freely, but update the table so the swap is visible.

**Timebox: one keynote ≈ 1 h viewing + 30 min notes.** If a keynote turns out to be
pure marketing with no technical content, **record that and stop watching**. A
20-minute negative result beats an hour of nothing, and "this source had nothing
technical in it" is a legitimate entry.

Prefer trucking companies over robotaxi ones — closer to our problem, and it is what
Aiden's **AD-3** comparison needs. Section B of each entry captures exactly the four
fields AD-3 wants (technology approach, autonomy level, sensor configuration,
deployment status), so he can lift them rather than watch everything again.

---

## Part 3 — Claims ledger

**This is the part that gets reused.** DZ-1's acceptance test is that any team member
can point to a documented pro or con **with a source attached**. One row per claim.

**Append at the bottom. Never restructure, never renumber** — a row number may already
be cited somewhere else.

| # | Claim | Modality | Source | Timestamp / page | Confidence | Added by |
|---|---|---|---|---|---|---|
| 1 | Radar measures velocity as well as position, but its image is very low resolution, sparse and noisy compared with camera or LiDAR | Radar | Bonn SDC 2021, Perception 1 | 6:52–7:42 | Stated | Damien |
| 2 | LiDAR point density falls with range until a distant pedestrian is not recognisable. The captioned distance ("15 m") needs checking | LiDAR | Bonn SDC 2021, Perception 2 | 24:26 | Stated (number unverified) | Damien |
| 3 | LiDAR fails on dark (absorbing), highly reflective (range error) and glass (phantom reflection) surfaces | LiDAR | Bonn SDC 2021, Perception 2 | 25:20–28:01 | Stated | Damien |
| 4 | A LiDAR segmentation model trained on a 64-beam sensor transfers badly to a 32-beam one, and changing the sensor mounting changes sampling and affects results | LiDAR | Bonn SDC 2021, Perception 2 | 52:21–54:14 | Evidenced (example shown) | Damien |
| 5 | Sensor fusion is essential and "really hard". The course does not cover it | Fusion | Bonn SDC 2021, Perception 1 | 8:30–9:14 | Stated | Damien |
| 6 | Datasets are mostly good weather; all-weather operation is an open problem for Level 5 | All | Bonn SDC 2021, Perception 1 | 71:41–72:32 | Stated | Damien |
| 7 | **Silence:** no mention of 4D/imaging radar, no radar-first detector, and no range figure past ~150 m in 131 minutes of perception teaching | Radar | Bonn SDC 2021, Perception 1 & 2 | whole | Stated (by absence) | Damien |
| 8 | Long-range perception is anchored on FMCW LiDAR: Aurora claims detection beyond 450 m; Daimler/Torc's Aeva LiDAR is designed for up to 500 m | LiDAR | Aurora newsroom, 23 Jan 2026; Daimler Truck NA press release, Jan 2024 ([AD-3](../ad-3-industry-check.md) A1, T1) | web pages | Stated | Aiden |
| 9 | State-of-the-art models "do not generalize to ranges beyond 150 meters", with 31–99% drops in 3D perception tasks | All | TruckDrive paper, Torc + Princeton, arXiv:2603.02413 ([AD-3](../ad-3-industry-check.md) T2) | abstract | Evidenced | Aiden |
| 10 | 4D radar on a production-intent truck since 2021: elevation lets it separate a stopped vehicle under a bridge from the bridge; velocity tracked to 350 m | Radar | Kodiak blog, 28 Sep 2021 ([AD-3](../ad-3-industry-check.md) K1) | web page | Stated | Aiden |
| 11 | Imaging radar "penetrates dense fog and rain"; in dust "the perception system shifts weight to imaging radar" | Radar / Fusion | Aurora newsroom, 23 Jan 2026 ([AD-3](../ad-3-industry-check.md) A1) | web page | Stated | Aiden |
| 12 | Inclement weather constrained Aurora's driverless operations in Texas roughly 40% of the time in 2025; rain, fog and wind validated only in early 2026 | All | Aurora Q4 2025 shareholder letter, 11 Feb 2026 ([AD-3](../ad-3-industry-check.md) A2) | 8-K exhibit 99.1 | Stated | Aiden |
| 13 | A driving stack trained only on one truck model drove a differently-sensored truck with zero retraining. **Contests row 4.** No metrics or independent verification published | All | FreightWaves on Waabi, 15 Jul 2026 ([AD-3](../ad-3-industry-check.md) W2) | web page | Contested | Aiden |

**Confidence:** *Stated* — the source asserts it directly · *Evidenced* — the source
shows data · *Contested* — sources disagree, log both and flag it · *Inferred* — your
reading, not theirs.

> A **Contested** row is worth more than an agreeing one. If two companies disagree
> about whether radar or LiDAR wins in fog, log both rows and flag it. That
> disagreement is a finding, and probably a question for Fabian.

### What this ledger is specifically for

Three project questions are waiting on it, so bias your notes toward them:

- **D-04, long range.** Does any source say anything about detection range limits, or
  degradation past ~150 m? This is the headline question and we have no external
  evidence on it at all.
- **R-21, no radar-first baseline.** Does any source name a radar-first detection
  model? This is recorded as the most significant unexamined question in the project,
  and one named model would move it.
- **4D radar specifically.** Most sources will say nothing. **Record the silence** — if
  five of six commercial sources never mention 4D radar, that is itself a finding about
  how new it is, and it is directly relevant to why we could not find a baseline.
