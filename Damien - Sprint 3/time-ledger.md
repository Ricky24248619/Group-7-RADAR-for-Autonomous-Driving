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
| Est. effort, plan as written | 49.5 |
| **Logged** so far | **7.0** |
| Projected logged total, plan finished in full | **51** |
| With the §4 additions | **60.5** |

**Cumulative: 37.0 · remaining to the 60 floor: 23.0**

Finishing the plan in full, Tier 3 included, projects to ~51. The §4 additions
close the rest. See §4 for why the original 79.5 was the wrong unit.

Reconcile against the team timesheet weekly. Note that the Week 7 cumulative sheet and
its break-plus-Week-7 column are different views of the same records and must not be
added together.

---

## Sessions

| Date | Task | Hours | Output | Notes |
|---|---|---|---|---|
| 2026-09-18 | B3, A1 | **2.0** | [PR #33](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/33) CI · [PR #34](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/34) suitability | Measured. Est. effort 5.5 — B3 3.5 + A1 first half 2.0 |
| 2026-09-19 | B2, A2 | **3.0** | [PR #35](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/35) `new_result.py` · [PR #34](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/34) §6 | Measured. Est. effort 9.5 |
| 2026-09-20 | A1 finish, A3, B1 | **2.0** | [PR #34](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/34) §7–§9 · [PR #36](https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving/pull/36) WS1 | Measured. Est. effort 6.0 — A1 2.0 + A3 2.0 + B1 2.0 of its 9.0 |
| | | **7.0** | | **21.0 h of estimated scope. Ratio ≈ 3:1** |

Hours are recorded **per session, not per task**, because per-session is what was
actually measured. Splitting 2.0 h across B3 and A1 by guesswork would reintroduce
exactly the invented precision this file exists to avoid. Estimated effort is carried
in the notes column so the variance stays visible without pretending to a split.

<!--
Row format:

| 2026-09-18 | B3 | 3.5 | `.github/workflows/validate.yml` | Pinned to 3.12; four numpy tests needed extras |
| 2026-09-19 | A1 | 2.0 | `docs/dataset-suitability.md` (draft §1–2) | Sampling descriptions inline per 5dd6a8f |

Use the README's task IDs: A1–A4, B1–B7.
Overruns get logged at their real length and the variance noted, not trimmed to estimate.
-->

---

## Weekly roll-up

| Week | Planned (est. effort) | Logged | Cumulative | Variance and what changed |
|---|---|---|---|---|
| W1 · 17–20 Sep | 6.0 | **7.0** | 37.0 | Hours roughly on plan; **scope was not** — 21.0 h of estimate delivered against 6.0 planned. This is where the 3:1 ratio was found |
| W2 · 21–27 Sep | — | | | Re-plan at the checkpoint: W2's planned work (A1, A2, B1, B2) already landed in W1. A4 and B5 move here |
| W3 · 28 Sep–4 Oct | — | | | Re-plan at the checkpoint. Candidates: B4, B1 entries, review depth |
| W4 · 5–12 Oct | — | | | Re-plan at the checkpoint. Candidates: B6, B7, client contact |
| **Total** | 49.5 est | | | Target 60.5 logged |

At each checkpoint, compare actual against estimate, explain the variance, and cut
optional scope early rather than late — Tier 3 (B6, B7) is the designated drop-zone.

**Stop: Monday 12 October, 5 pm.** Hours after that boundary do not count toward
project work.
