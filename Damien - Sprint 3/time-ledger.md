# Active-time ledger — Damien, Sprint 3

One row per session. Record it **as the work happens**, not reconstructed at the end of
the week — the Sprint 2 retrospective found that the shared team-budget field was blank
and task estimates were not consistently recorded, so no story-by-story
estimate-versus-actual variance could be calculated at all. This file is the fix for my
own half of that.

**Active time only.** Time spent actually working. Not elapsed time, not a run
executing while I do something else, not meetings already logged on the team sheet.

Every row names a task from [`README.md`](README.md) and links the output it produced.
**A row with hours and no output link is visible as such, and that is the point.**

---

## Target

| | Hours |
|---|---|
| Logged before Sprint 3 | 30.0 |
| Floor | 60 |
| Preferred | 70–80 |
| Planned this sprint (§4, Tier 3) | 49.5 |
| Projected total | 79.5 |

**Remaining to floor: 30.0 · to preferred: 40.0–50.0**

Reconcile against the team timesheet weekly. Note that the Week 7 cumulative sheet and
its break-plus-Week-7 column are different views of the same records and must not be
added together.

---

## Sessions

| Date | Task | Hours | Output | Notes |
|---|---|---|---|---|
| 2026-09-18 | B3 | 2.5 | [PR #33](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/33) — `.github/workflows/checks.yml`, `requirements-ci.txt` | Under estimate (3.5). Pinned 3.11 per SETUP.md; 3.14 collects 44 tests not 53. Stacked on #31 so it lands green |
| 2026-09-18 | A1 | 2.0 | [PR #34](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/34) — `docs/dataset-suitability.md` | On estimate. Week-1 portion; remaining 2.0 h of A1 in week 2 |

<!--
Row format:

| 2026-09-18 | B3 | 3.5 | `.github/workflows/validate.yml` | Pinned to 3.12; four numpy tests needed extras |
| 2026-09-19 | A1 | 2.0 | `docs/dataset-suitability.md` (draft §1–2) | Sampling descriptions inline per 5dd6a8f |

Use the README's task IDs: A1–A4, B1–B7.
Overruns get logged at their real length and the variance noted, not trimmed to estimate.
-->

---

## Weekly roll-up

| Week | Planned | Actual | Cumulative | Variance and what changed |
|---|---|---|---|---|
| W1 · 17–20 Sep | 6.0 | 4.5 | 34.5 | B3 came in 1.0 under. 0.5 h checkpoint prep still to do on 20 Sep |
| W2 · 21–27 Sep | 14.0 | | | |
| W3 · 28 Sep–4 Oct | 15.0 | | | |
| W4 · 5–12 Oct | 14.5 | | | |
| **Total** | **49.5** | | | |

At each checkpoint, compare actual against estimate, explain the variance, and cut
optional scope early rather than late — Tier 3 (B6, B7) is the designated drop-zone.

**Stop: Monday 12 October, 5 pm.** Hours after that boundary do not count toward
project work.
