# Domain Study Template — company keynotes and AV courses

**CITS3200 Group 07 · Workstream WS1 · one entry per source · owner DZ-1 (Damien)**

Copy the entry block in Part 2 into `docs/domain-study/<yourname>-<source>.md`, fill
it, open a PR. Add your row to the coverage matrix and at least two rows to the
claims ledger in [`domain-study/README.md`](domain-study/README.md), in the same PR.

---

## Why this exists

Adrian's suggestion at kickoff: *"I can send you a link of different self-driving
company names. You type in company name and the word 'keynote' and you will find a one
hour pitch from that company about how their tech works."* He asked that each of us
take a **different** one.

This template makes six people's viewing add up to one survey instead of six
disconnected sets of notes. **DZ-1's acceptance tests are what shape it:**

- *"Coverage gaps are visible at a glance without re-reading the whole document"* →
  the coverage matrix in `domain-study/README.md`. Fill your row or it is useless.
- *"Shallow areas are marked as such rather than padded"* → the depth rating in each
  entry. **Rating something Shallow is the correct answer when it's shallow.** Padding
  is worse than a gap, because a gap is visible and padding is not.
- *"New material arrives mid-project, no restructuring is needed"* → one file per
  source. Never edit someone else's entry; add your own.
- *"A team member can point to a documented pro or con with a source attached"* →
  the claims ledger in `domain-study/README.md`. This is the part that gets reused.

**Feeds Aiden's AD-3.** His story is a comparison of leading autonomous trucking
companies on technology, autonomy level, sensor configuration and deployment status.
Part 2 §B captures exactly those four fields so he can lift them straight out rather
than watching everything again. Timebox: **one keynote ≈ 1 hour, plus ~30 min notes.**

---

## Part 1 — Coverage matrix and source assignments

**Both now live in [`domain-study/README.md`](domain-study/README.md)**, alongside the
claims ledger, so this file stays a blank form rather than doubling as the data store.
Six people appending rows to one template conflict on every PR, and a template that
carries real data is no longer copyable.

Claim your source in that file **before** you start watching, so two people do not
watch the same keynote.

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

**Lives in [`domain-study/README.md`](domain-study/README.md).** Append at the bottom;
never restructure or renumber, because a row number may already be cited elsewhere.

Confidence is *Stated*, *Evidenced*, *Contested* or *Inferred*. A **Contested** row —
two sources disagreeing about, say, whether radar or LiDAR wins in fog — is worth more
than an agreeing one, and is probably a question for Fabian.

---

## Before you open the PR

- [ ] Row added to the coverage matrix in `domain-study/README.md`
- [ ] Depth rating is honest — Shallow where it was shallow
- [ ] "Not covered" written where the source was silent, rather than left blank
- [ ] Section B filled if this was a company keynote, so Aiden can use it
- [ ] At least two rows appended to the claims ledger in `domain-study/README.md`, with a timestamp
- [ ] Unfamiliar terms listed in §E for the glossary
