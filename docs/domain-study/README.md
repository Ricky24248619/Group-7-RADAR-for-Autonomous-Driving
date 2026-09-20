# Domain study — WS1

**Workstream WS1 · story DZ-1 · owner Damien Zhang**

Six people watching six different sources, adding up to one survey instead of six
disconnected sets of notes. This file is the living index: the coverage matrix, who has
claimed which source, and the claims ledger.

**To add an entry:** copy Part 2 of
[`../domain-study-template.md`](../domain-study-template.md) into
`docs/domain-study/<yourname>-<source>.md`, fill it, add your row to the matrix below
and at least two rows to the claims ledger, then open a PR.

> **Status: no entries yet.** The structure below is live and the sources are assigned,
> but every row is empty because nobody has watched anything. That is the honest state
> of WS1, and it is why **P-2 sits at "partly met"** — the per-dataset surveys and the
> handbook exist, the cross-team sensor survey does not.

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
| *(none yet)* | | | | | | | | | |

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
| 5 | [Bonn — Self-Driving Cars 2021](https://www.ipb.uni-bonn.de/sdc-2021/index.html) | Academic, sensor fundamentals | Damien | |
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
| | | | | | | |

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
