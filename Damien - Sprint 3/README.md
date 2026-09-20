# Damien — Sprint 3 plan

**Owner:** Damien Zhang · **Reviewer:** Fariya Zehrin · **Epic B** · story **DZ-S3-1**
**Written:** 17 September 2026 · **Status: proposed.** Nothing here is agreed until the
20 September checkpoint. Part B in particular expands scope well beyond the story
sheet's allowance and needs explicit team agreement, not silent adoption.

---

## 1. The problem this plan solves

Two things have to be true at the end of Sprint 3, and only one of them is covered by
the story as written.

**DZ-S3-1 must be delivered.** That is the committed work, and Part A does it.

**The recorded hours have to be defensible.** 30 hours logged before Sprint 3, against
a target floor of 60 and a preferred 70–80. DZ-S3-1 carries an 8–12 hour allowance.
Core work alone therefore lands somewhere around 40 hours — roughly 20 short of the
floor and 40 short of the stretch.

The honest way to close that gap is more delivered work, not more generous
accounting. So Part B proposes seven additional packages. Each one is chosen because it
is **already documented somewhere in this repository as missing**, with the citation
given. None of it is invented to fill a timesheet. The project's own domain-study
template puts it better than I can:

> *Rating something Shallow is the correct answer when it's shallow. Padding is worse
> than a gap, because a gap is visible and padding is not.*

The same applies to hours. Log active time as it happens, against the task that
consumed it. If a package comes in under estimate, it comes in under estimate.

### Calendar reality

| | |
|---|---|
| Today | Thursday 17 September |
| Official stop for project work | **Monday 12 October, 5 pm** — 25 days away |
| Teams submission deadline | Wednesday 14 October, 11:59 pm |

49.5 hours across 25 days is **2 hours per day, every day**. That is the actual
commitment being proposed. It is achievable, but only if it starts this week rather
than after the checkpoint.

---

## 2. Part A — DZ-S3-1 as written

> *As the team and client, we want one evidence-backed comparison of dataset
> suitability, so we know which question each dataset can answer.*

**Deliverable:** `docs/dataset-suitability.md` — one document, source-linked
throughout.

### A1 · Suitability comparison — 4.0 h

Build the comparison from the three existing surveys rather than re-deriving anything.
Compare on: released assets, label task and schema, range coverage, setup effort,
storage, tooling, and which experiments are actually feasible on team hardware.

Every measurement carries its sampling description **in the same cell as the number**.
This is the failure mode Ricky caught in `5dd6a8f` — GOOSE's 174.9 M points cover all
961 validation frames, TruckScenes' totals cover one radar and one LiDAR channel on one
sample per scene, and TruckDrive's 6,746 covers one radar frame in each of 24 scenes.
Those three numbers must never again sit side by side looking comparable.

**Hard constraint from D-01:** no cross-dataset ranking on a shared axis. The output is
*which question each dataset can answer*, not *which dataset is best*.

### A2 · GOOSE traversability explainer — 2.5 h

Explain the 64-class → traversability mapping and, more importantly, its dependence on
human labels. The figures group existing annotations; they do not show a model deciding
where a vehicle can drive. Keep the complete 961-frame statistics visibly separate from
the partial 10-frame PTv3 run, and restate the ~5-hour full-pass figure as what it is —
an extrapolation of the processing loop that excludes loading, so a lower bound rather
than a prediction.

Also correct the `~1–6%` figure. That is the per-scenario range from
`findings-damien.md`; the split-level number is **3.8% beyond 100 m, 1.1% beyond
150 m**, which is what the acceptance tests and Scope of Work quote. The Sprint 2
report currently prints the per-scenario range beside split-level numbers.

### A3 · Gap register and validation — 2.0 h

Every claim links to a survey, experiment log or saved record. Unresolved gaps get
recorded as gaps rather than smoothed over. Run both validators after integrating any
new records.

### A4 · Cold read — 2.5 h

The story's real acceptance condition: **an outside-pair reader explains the GOOSE
figure and its limitations**. Show the figure with no narration, record what they say,
and record it unedited — including if they misread it. A misread is the finding.

This closes **P-6** and **DS-4**, open since Sprint 1 and never performed. It needs
someone else's calendar, so book it in week 2, not week 4.

**Part A subtotal: 11.0 h** — within the 8–12 allowance.

---

## 3. Part B — proposed additional work

Ordered by value per hour. Each states the documented gap it closes.

### B1 · WS1 cross-team sensor survey — 9.0 h

**Gap:** P-2 is "partly met" *because* "the cross-team sensor survey (WS1) is
unwritten". DZ-1 is "Partial" for the same reason. `docs/domain-study-template.md`
names DZ-1 (me) as owner — and **`docs/domain-study/` does not exist**. Zero entries.
The repository layout table in the root `README.md` already lists that directory as
"The study entries", so the repo currently promises a folder that was never created.

This is the single largest piece of my own epic still outstanding, and it is the one
gap in the whole repository that names me directly.

- Create `docs/domain-study/`, write 3 entries myself at the template's ~1.5 h each
  (one keynote ≈ 1 h viewing + 30 min notes)
- Fill the Part 1 coverage matrix and chase the other five for one entry each
- Assemble the Part 3 claims ledger — the part the template says actually gets reused
- **Feeds Aiden's AD-3 directly.** Part 2 §B captures the four fields his company
  comparison needs, so he lifts them instead of re-watching everything

**Done when:** P-2's evidence line can be rewritten from "unwritten" to a link, and
Aiden confirms AD-3 can source from it.

### B2 · D8 — the shared results submission path — 7.0 h

**Gap:** my own honest-gaps list says *"D8 never got done — the page letting the other
pairs add results without asking us"*. Sprint 2 report §5 lists it as openly
outstanding; §6.4 says build it. **No Sprint 3 story covers it.** Right now every
result routes through our pair, which is a handover liability the moment we stop.

Not a web service — DZ-4's acceptance test is explicitly that the inheriting team
reproduces a chart **with no live service running**, and the dashboard is descoped
anyway. Build it as tooling instead:

- `scripts/new_result.py` — prompts for each field, refuses to write an invalid
  record, **allocates the next free sequence number automatically**
- A GitHub issue template that collects the same fields for anyone not in a terminal
- A "add your result in 60 seconds" section in `results/README.md`

That auto-numbering is not incidental. Sequence collisions have now hit `main`
**twice** — `5dd6a8f` fixed two duplicate 0006s, two 0007s and two experiment logs;
PR #31 is fixing the same class of failure again this week. Hand-picking "the next free
number" across parallel branches does not work, and the fix is to stop asking people to
do it.

### B3 · Continuous integration — 3.5 h

**Gap:** there is **no `.github/` directory at all**. Zero CI. Both collision incidents
merged green because nothing ran.

A single workflow on every PR and push to main:

```
python scripts/validate_result.py
python scripts/validate_experiment_logs.py
python -m unittest discover -s tests
```

Highest value-per-hour item in this plan. It converts "remember to run the validators",
which the README now asks of everyone and which has already failed twice, into
something that cannot be forgotten. It also makes every future PR reviewable on
evidence rather than trust.

Two known snags to handle honestly: four tests fail to import on Python 3.14 for want
of numpy/matplotlib, and one asserts a JSON error message that changed in 3.14. Pin the
runner to the version the team actually uses and install the dependencies, or mark
those tests as requiring extras — **do not** make the suite green by deleting them.

### B4 · Range-band reporting harness — 7.0 h

**Gap:** P-8 records that "nothing is yet reported by range band" — and reporting by
band, never as one aggregate, is the project's headline requirement. DZ-5 is deferred
"requires more than one completed model run", which may never arrive.

So build the reporting machinery against **data that already exists**, so it is useful
regardless of whether S3-X1 ever runs:

- GOOSE: labelled points per band across all 961 frames — already measured
- TruckScenes: the saved 5,247 FCOS3D predictions and 2,088 ground-truth boxes,
  bucketed by band — computable on CPU from files already in `scripts/`
- TruckDrive: the 6,746 returns ≥150 m, with its 24-frame denominator attached

`scripts/range_report.py` emits one panel per dataset with per-band counts and
denominators. **It must not merge them onto a shared axis** — D-01 forbids it, and
these are three different kinds of evidence: labelled points, model predictions and
sensor returns. Every panel states what was counted and out of what.

**Dependency:** band edges are open question 3 in `docs/metrics-definitions.md`
(proposed 0–50 / 50–100 / 100–150 / 150–400 m) and that document is Ricky's. Get the
edges confirmed at the checkpoint before building, or the output gets rebuilt.

**Payoff:** if S3-X1 does run, its results drop straight into an existing reporting
path instead of needing a reporter written under deadline in week 4.

### B5 · P-5 outside-team reproduction — 4.0 h

**Gap:** P-5 is "partly met" — Ricky reproduced my macOS workflow on Windows, but both
of us are team members, so *"reproduction by an outside-team reader remains
outstanding"*. The 11 September catch-up brief says explicitly that outside-*pair*
reading does not satisfy P-5. **No Sprint 3 story owns it**, so on current plans it
stays open at handover.

Find one person outside the unit, hand them the repository and nothing else, and record
where they get stuck. Budget for the strong likelihood that they *do* get stuck — that
outcome is the finding, and recording it is worth more than a pass.

### B6 · Handover package — 5.0 h

**Gap:** the stated project goal is a documented body of work *"a future team can pick
up and extend"*. RY-S3-1 covers the integrated handover of findings; nobody covers the
infrastructure I built — the results store, validators, session check, survey and
experiment templates, renderer.

One `HANDOVER.md`: what each tool is for, how to run it, what the schema means, what I
would change, and what is deliberately unfinished. Written for someone with no access
to any of us.

### B7 · Sprint 2 report corrections — 2.5 h

**Gap:** `docs/sprint-2/README.md` lists corrections to carry into the final team
version and assigns them to nobody. Two are mine: the 1–6% / 3.8% figure from A2, and
the GOOSE partial-run framing. Also fold in the stale `0007-` path that PR #31 creates.

Cheap, and it stops a known-wrong number reaching the marker.

**Part B subtotal: 38.0 h**

---

## 4. Hours — corrected 20 September

**The original version of this section was wrong, and wrong in a way that mattered.**
It listed one hours column and stacked it into tiers reaching 79. That column was
*estimated effort for the work* and it got treated as *time I would log*. Those are not
the same number, and after the first week the gap is measured rather than theoretical:

> **21.0 h of estimated scope delivered, 7.0 h logged. Roughly 3:1.**

So the tier ladder never mapped to my timesheet. It is rebuilt below with two columns.
Effort is what the work is worth as a planning estimate; logged is what I actually
spend, which is what the timesheet records.

### Delivered so far

| Task | Effort | Logged |
|---|---:|---:|
| B3 · CI | 3.5 | |
| A1 · suitability comparison | 4.0 | |
| A2 · traversability explainer | 2.5 | |
| A3 · verification and gap resolution | 2.0 | |
| B2 · submission path | 7.0 | |
| B1 · WS1 scaffold (of 9.0) | 2.0 | |
| **Total** | **21.0** | **7.0** |

Logged time is recorded per session in [`time-ledger.md`](time-ledger.md), not split
per task, because per-session is what I actually measured. Inventing a per-task split
would be the same error again.

### Remaining

The ratio is not uniform. Some work is inherently mine and cannot compress; some is
mostly delegated.

| Item | Effort | Realistically mine | Why |
|---|---:|---:|---|
| B1 remainder | 7.0 | 2.5 | My source is mine; five other people's viewing is not my time |
| **A4 · cold read** | 2.5 | **2.5** | Entirely mine |
| **B5 · outside-team reproduction** | 4.0 | **4.0** | Entirely mine |
| B4 · range-band harness | 7.0 | 2.0 | Mostly delegated |
| B6 · handover | 5.0 | 1.5 | Mostly delegated |
| B7 · report corrections | 2.5 | 1.0 | Mostly delegated |
| Checkpoint prep | 0.5 | 0.5 | Mine |
| **Total** | **28.5** | **14.0** | |

### Where that lands

| | Logged total |
|---|---:|
| Now | **37** |
| Plan as written, finished in full — **Tier 3 included** | **51** |

**Finishing everything no longer reaches the 60 floor.** That is the real finding, and
it inverts the reading that Tier 3 was spare capacity: Tier 3 is still worth doing,
because B6 and B7 close genuine gaps, but it is worth about 2.5 logged hours rather
than the 7.5 the old table implied.

### Closing the gap with work that is actually required

The items that generate my hours are the same ones the acceptance tests still need,
which is a real alignment rather than a convenient one.

| Addition | Logged | What it closes |
|---|---:|---|
| Review depth on the open PRs | 3.5 | The checkpoint requires me to explain my input, script, output, conclusion and one limitation. I cannot do that for work I have not read |
| Run it myself — reproduce the render, drive `new_result.py`, re-derive the 961 frame sum and the range tables | 2.5 | DS-4, and what the retrospective asked for |
| Re-establish client contact | 2.0 | **P-1 and P-7.** Unowned by any story, and R-28 already names me as its owner |
| A second WS1 source | 1.5 | P-2, the gap this workstream exists to close |
| **Total** | **9.5** | |

**37 + 14 + 9.5 = 60.5.** Defensible line by line.

Reaching 70–80 would need work I am not delegating — a legitimate choice, but not one
this plan arrives at by itself, and better said now than discovered in October.

### Ordering

**B3 first** was right and is done: 3.5 hours of effort that protects everything after
it. Of what is left, **A4 and B5 come first** — 6.5 logged hours, entirely mine, and
they close P-5, P-6 and DS-4, three criteria open since Sprint 1. They also both depend
on other people's calendars, so they are the items that punish being left late.

---

## 5. Schedule

Aligned to the team checkpoints in *New Stories for Sprint 3* §5.

### Week 1 — Thu 17 to Sun 20 Sep · target 6 h

Team checkpoint 20 Sep: agree owners, reviewers, acceptance criteria, scope.

- B3 CI workflow — 3.5 h. Do it first; it protects every PR after it
- A1 started: pull the three surveys into one comparison skeleton — 2.0 h
- Checkpoint prep: table the scope expansion, get range-band edges confirmed — 0.5 h

### Week 2 — Mon 21 to Sun 27 Sep · target 14 h

Team checkpoint: first charts, go/no-go on the conditional benchmark.

- A1 complete — 2.0 h
- A2 GOOSE explainer, including the 3.8% correction — 2.5 h
- B1 WS1: create `docs/domain-study/`, 2 entries, matrix live, chase the other five — 5.5 h
- B2 `new_result.py` with auto-numbering — 4.0 h
- **Book A4 cold read and B5 outside reader now** — both need other people's diaries

### Week 3 — Mon 28 Sep to Sun 4 Oct · target 15 h

Team checkpoint: complete core analyses, cross-pair reproduction and cold reads.

- A3 gap register and validator run — 2.0 h
- **A4 cold read session** — 2.5 h
- B1 third entry, claims ledger, confirm with Aiden for AD-3 — 3.5 h
- B2 issue template and `results/README.md` section — 3.0 h
- B4 range-band harness — 4.0 h

### Week 4 — Mon 5 to Mon 12 Oct 5 pm · target 14.5 h

Team checkpoint: review, handover, rehearse explanations.

- B4 complete, three dataset panels — 3.0 h
- **B5 outside-team reproduction** — 4.0 h
- B6 HANDOVER.md — 5.0 h
- B7 report corrections — 2.5 h (drop first if week 4 compresses)

**Planned total: 49.5 h** — 49.0 h of task work plus 0.5 h checkpoint prep — **→ 79.5 h
cumulative.** At the top of the 70–80 target, with Tier 3 as buffer rather than as a
requirement.

---

## 6. Risks specific to this plan

| Risk | Handling |
|---|---|
| **Scope expansion rejected at the checkpoint.** 49.5 h against an 8–12 h story allowance is a four-fold deviation | Table it explicitly on 20 Sep. Every package cites a documented gap, so the discussion is about priority, not justification. If rejected, Part A still ships and the hours conversation moves to the team |
| **A4 and B5 depend on other people's calendars** | Both booked in week 2 for execution in weeks 3–4. A refusal or a no-show is itself recordable against P-5/P-6 |
| **B4 built on band edges that then change** | Confirm edges at the 20 Sep checkpoint before building. Ricky owns `metrics-definitions.md` |
| **B4 looks like it answers D-04 and does not** | Every panel is coverage, not accuracy. Labelled points, model predictions and sensor returns stay in separate panels, each with its denominator. This is the exact error `5dd6a8f` already had to correct once |
| **Hours logged but under-delivered** | The ledger records active time against a named task with a linked output. A task with hours and no output is visible as such |
| **CI turns red on pre-existing failures and gets ignored** | Fix the environment or mark tests as needing extras. Never delete a failing test to get green |

---

## 7. Boundaries — not mine this sprint

- **RY-S3-1** — the comparison *protocol* is Ricky's. Mine is the dataset *suitability*
  comparison. Adjacent enough to duplicate; settle the line at the checkpoint
- **FZ-S3-1** — Fariya's figures and walkthrough. I review it, I don't write it. If she
  picks GOOSE for her reproduction check, she is testing my documentation, and a failed
  reproduction gets recorded as a failure
- **Autoware, the dashboard, the FastAPI backend** — outside the core plan per the
  Sprint 3 stories, though the Sprint 2 report §6.4 says the opposite. That
  contradiction is the team's to resolve, not mine to resolve by doing the work
- **The conditional S3-X1 benchmark** — Aiden and Fatima. B4 gives it a reporting path
  if it lands

---

## 8. Decisions needed on 20 September

1. Is the Part B expansion accepted, and at which tier?
2. Range-band edges — confirm 0–50 / 50–100 / 100–150 / 150–400 m, or set others
3. Who owns D8 if not me? It is currently unassigned and blocks nobody's story, which
   is exactly how it got missed last sprint
4. Who owns re-establishing client contact? It gates P-1 and P-7 and no story has it
5. Who is Sprint 3 PM? Rotation ran Damien → Aiden → unnamed
6. Does DZ-5 stay in scope given it needs S3-X1, which may not run?
7. Where does the Autoware/dashboard contradiction land?

---

## 9. Files

| File | What it is |
|---|---|
| `README.md` | This plan |
| `time-ledger.md` | Running active-time log against the target |

Outputs land in their existing homes — `docs/dataset-suitability.md`,
`docs/domain-study/`, `scripts/`, `.github/workflows/`, `results/README.md` — not in
this folder. This folder is planning and time records only.
