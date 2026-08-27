# Domain Study Template — company keynotes and AV courses

**CITS3200 Group 07 · Workstream WS1 · one entry per source · owner DZ-1 (Damien)**

Copy the entry block in Part 2 into `docs/domain-study/<yourname>-<source>.md`, fill
it, open a PR. Add your row to the coverage matrix in Part 1 in the same PR.

---

## Why this exists

Adrian's suggestion at kickoff: *"I can send you a link of different self-driving
company names. You type in company name and the word 'keynote' and you will find a one
hour pitch from that company about how their tech works."* He asked that each of us
take a **different** one.

This template makes six people's viewing add up to one survey instead of six
disconnected sets of notes. **DZ-1's acceptance tests are what shape it:**

- *"Coverage gaps are visible at a glance without re-reading the whole document"* →
  Part 1, the coverage matrix. Fill your row or the matrix is useless.
- *"Shallow areas are marked as such rather than padded"* → the depth rating in each
  entry. **Rating something Shallow is the correct answer when it's shallow.** Padding
  is worse than a gap, because a gap is visible and padding is not.
- *"New material arrives mid-project, no restructuring is needed"* → one file per
  source. Never edit someone else's entry; add your own.
- *"A team member can point to a documented pro or con with a source attached"* →
  Part 3, the claims ledger. This is the part that actually gets reused.

**Feeds Aiden's AD-3.** His story is a comparison of leading autonomous trucking
companies on technology, autonomy level, sensor configuration and deployment status.
Part 2 §B captures exactly those four fields so he can lift them straight out rather
than watching everything again. Timebox: **one keynote ≈ 1 hour, plus ~30 min notes.**

---

## Part 1 — Coverage matrix

Add one row when you finish. Keep it to one line. This is the at-a-glance artefact.

| Source | Type | Who | Date | Radar | LiDAR | Camera | Fusion | Off-road | Depth |
|---|---|---|---|---|---|---|---|---|---|
| *e.g. Kodiak keynote* | Keynote | | | ✅ | ✅ | ✅ | ⚠️ | ❌ | Medium |
| | | | | | | | | | |

**Key:** ✅ covered in useful detail · ⚠️ mentioned only · ❌ not covered · Depth =
Shallow / Medium / Deep

### Suggested sources — claim one, don't duplicate

Working in three pairs (MAN, STONE, TruckDrive). Take one source per person, not per
pair, so six sources get covered.

| # | Source | Claimed by |
|---|---|---|
| 1 | [Bonn — Self-Driving Cars 2021](https://www.ipb.uni-bonn.de/sdc-2021/index.html) *(academic, sensor fundamentals)* | |
| 2 | [Coursera — Self-Driving Cars specialisation](https://www.coursera.org/specializations/self-driving-cars) *(structured, longest)* | |
| 3 | **Torc Robotics** keynote *(they built TruckDrive — highest relevance)* | |
| 4 | **Aurora** keynote *(trucking, sensor-first)* | |
| 5 | **Kodiak Robotics** keynote *(trucking, off-road/defence work)* | |
| 6 | **Waabi** or **Plus** keynote *(contrasting approach)* | |

> Prefer trucking companies over robotaxi ones — closer to our problem, and it's what
> Aiden's AD-3 comparison needs. If a keynote turns out to be pure marketing with no
> technical content, **record that and stop watching**. A 20-minute negative result
> beats an hour of nothing.

---
---

## Part 2 — Entry block *(copy from here)*

# `<SOURCE NAME>`

| | |
|---|---|
| Source type | Keynote / Course / Talk / Paper |
| Link | |
| Company or institution | |
| Duration and date watched | |
| Notes by | |
| **Depth rating** | Shallow / Medium / Deep |

**Depth rating means:** *Shallow* — I got the gist, could not defend a technical claim
from it. *Medium* — I can explain their approach and its trade-offs. *Deep* — I could
answer a challenge question from Fabian.

## A. What they actually said

Three to six bullets. Their argument, not a transcript. If they made a claim you found
surprising or doubtful, mark it — that is more useful than a summary.

-

## B. Company profile → feeds Aiden's AD-3

*(Skip this section for courses.)*

| Field | Value | Confidence |
|---|---|---|
| Primary technology approach | | |
| Level of autonomy claimed | | |
| **Sensor configuration** *(radar? 4D? counts if stated)* | | |
| Deployment status *(pilot / commercial / testing)* | | |
| Operating domain *(highway / urban / yard / off-road)* | | |
| Stated open problems | | |

**Confidence:** Stated explicitly / Implied / My inference

## C. Sensor content

Only what this source actually covered. **Write "not covered" freely** — that is what
makes the matrix in Part 1 honest.

| Modality | What they said about strengths | Weaknesses / failure modes | Covered? |
|---|---|---|---|
| Radar | | | |
| LiDAR | | | |
| Camera | | | |
| Fusion | | | |

**Anything on 4D radar specifically?** *(Our project's focus. Most sources will say
nothing — record that, it is itself a finding about how new this is.)*

**Anything on off-road or unstructured environments?** *(Adrian and Fabian's stated
interest.)*

## D. Relevance to our decisions

- **D-04 (long-range):** does this source say anything about detection range limits or
  degradation past ~150 m?
- **D-03 (off-road):** anything on terrain, traversability, ground vs not-ground?
- **R-21 (no radar-first baseline):** do they name any radar-first detection model?

## E. Terms I did not understand

Feeds Fatima's glossary (FA-2). List them even if you looked them up — if it was new
to you it is new to someone else.

-

## F. Worth escalating to Fabian

Anything technical you could not resolve, or a claim you think is wrong.

-

---
---

## Part 3 — Claims ledger

**This is the part that gets reused.** DZ-1's acceptance test says any team member must
be able to point to a documented pro or con *with a source attached*. One row per
claim, appended as you go. Do not restructure — append only.

| # | Claim | Modality | Source | Timestamp / page | Confidence | Added by |
|---|---|---|---|---|---|---|
| 1 | *e.g. Radar penetrates dust and fog where LiDAR returns are scattered* | Radar | | | Stated | |
| | | | | | | |

**Confidence:** *Stated* — the source asserts it directly · *Evidenced* — the source
shows data · *Contested* — sources disagree, note both · *Inferred* — your reading

> A **Contested** row is more valuable than an agreeing one. If two companies disagree
> about whether radar or LiDAR wins in fog, log both rows and flag it — that
> disagreement is a finding, and probably a question for Fabian.

---

## Before you open the PR

- [ ] Row added to the Part 1 coverage matrix
- [ ] Depth rating is honest — Shallow where it was shallow
- [ ] "Not covered" written where the source was silent, rather than left blank
- [ ] Section B filled if this was a company keynote, so Aiden can use it
- [ ] At least two rows added to the Part 3 claims ledger with a timestamp
- [ ] Unfamiliar terms listed in §E for the glossary
