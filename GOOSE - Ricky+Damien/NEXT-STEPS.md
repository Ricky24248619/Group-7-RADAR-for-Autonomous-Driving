# Next steps — Damien & Ricky, from 29 August 2026

**Read this after [`WORKPLAN.md`](WORKPLAN.md).** Same conventions: task IDs, disjoint
file ownership, `scripts/session_check.py` before every session and every commit,
branch per person, PR reviewed by the other. Numbering continues from the last
fortnight — `D6…` and `R6…`.

**Status of this file:** shared/frozen, like `WORKPLAN.md`. It should be added to the
`FROZEN` list in `scripts/session_check.py` — a one-line change either of us can make,
but only with the other's agreement.

---

## 1. Where we actually are

| | |
|---|---|
| **Done and merged** | D1–D5 (Damien), R1–R3, R5 (Ricky). Nine PRs. GOOSE is characterised, mapped, rendered, surveyed |
| **Loose ends** | R4 has 2 experiment-log entries; its definition of done asks for 3. `docs/metrics-definitions.md` does not yet carry the projection caveat from D4 |
| **Needs a human, not an agent** | Cold read of the client figure and of survey §7, by Kelsey or Fatima |
| **Blocked externally** | Kaya — waiting on Adrian. STONE — dropped at the 29 Aug meeting |

### The gap this phase closes

**Nobody on the team has run a model yet. On any dataset.** Six weeks in, the repo
holds characterisation and tooling and zero results. Adrian's kickoff framing was
explicit:

> *"We would find some open source solutions that are out there... and basically we're
> just trying to run them on the data sets. So okay, we ran this algorithm, we spent X
> number of days trying to get it going, we couldn't get it going — or yep, we got it
> working but it doesn't perform very well."*

That is the deliverable. We have not started it.

**And the team has just split by dataset**, which is exactly when three incompatible
result formats get created in parallel and have to be reconciled later. That is risk
**R-12** arriving on schedule.

So this phase does two things at once: produce the project's first model result, and
build the one place all three pairs record results into.

---

## 2. The split — and why this way round

| | Damien | Ricky |
|---|---|---|
| **Owns** | The results store and its schema (DZ-3 / DZ-4) | Running the model, and closing last fortnight's loose ends |
| **Why** | It is his epic, and four people depend on the schema | **He has the GPU.** A GTX 1660, 6 GiB — the only CUDA hardware on the team |
| **Blocked by** | Nothing | Nothing for the run itself |

**One dependency, and it points the opposite way to last time.** Last fortnight Ricky
produced the contract (`traversability_map.csv`) and Damien consumed it. This time
Damien produces the contract (the result schema) and Ricky's run writes into it. Only
**R8** depends on **D6**; the run itself (R7) does not, so nobody waits.

**Target for D6: 3 September**, same checkpoint as before.

---

## 3. Environment notes before starting

### Ricky — you deleted your dataset copy

Experiment log 0001 records that the archive and extracted split were removed after
R2 to free C: space before an OS reinstall. **R7 needs the data back.** See
`WORKPLAN.md` §2.3 — 3.3 GB download, 3.3 GB extracted, and remember `curl.exe` and
`tar`, not `curl` and `Expand-Archive`.

### The baseline

The GOOSE devkit ships **pretrained PTv3 weights** and a published result, so this is
inference and evaluation, not training:

```
weights: https://bwsyncandshare.kit.edu/s/ExDe9x5gsDCQ2kW/download/challenge_ptv3.pth
published val result: mIoU 0.8096 · mAcc 0.8576 · allAcc 0.9197
```

Per-class IoU from `goose_dataset/pointcloud_processing/README.md`:

| Class | IoU | | Class | IoU |
|---|---|---|---|---|
| other | 0.9686 | | vehicle | 0.8954 |
| artificial_structures | 0.8773 | | vegetation | 0.9179 |
| artificial_ground | 0.7097 | | human | 0.8302 |
| natural_ground | 0.8220 | | obstacle | **0.4554** |

**Having a published number to reproduce is why GOOSE is the right place to start.**
Matching it validates the whole pipeline; missing it is itself informative.

### ⚠️ The likely blocker — read this before planning R7

**The published baseline reports on the 8-class *challenge* taxonomy. The downloadable
validation split ships 64-class `labels/` only — there is no `labels_challenge/`
directory in the archive.** Verified 29 Aug.

So evaluating against the published number needs a 64→8 mapping that we do not
currently have. `common/goose_kitti-visualizer.yaml` carries the 8 class *names and
colours* but its `learning_map_inv` is empty. Options, in order of preference:

1. Find the official mapping in the devkit, the Pointcept fork, or the docs
2. Ask the maintainers — they answer within days and are responsive
3. Derive it ourselves from the class names, and **state clearly that our numbers are
   not comparable to the published ones**

**Resolve this first.** If it cannot be resolved, the run can still produce predictions
and a qualitative result, but not a number comparable to 0.8096.

### If the GPU is not enough

6 GiB is tight for PTv3. Ladder, in order:

1. Ricky's GTX 1660
2. Google Colab free tier (T4, 16 GiB) — but the devkit image targets CUDA 11.7, which
   may not match Colab's runtime
3. **A dated failure record.** RY-3 asks for *"a small baseline evaluation run or
   documented feasibility test... or a dated failure record stating the error, the
   attempted fix, and a clear recommendation."* A documented failure satisfies it.

Do not spend more than **two days** fighting the environment before writing it up as a
result and moving on.

---
---

# TASKS — DAMIEN

## D6 — The results record schema ⚠️ *blocks R8 — deliver by 3 September*

**Goal.** One documented format that every benchmark result in this project is recorded
in, whichever dataset or pair produced it. This is DZ-4's core.

**Design constraints, from our own documents:**

- **D-01** — dataset, full sensor configuration and annotation schema are *mandatory*
  fields that cannot be blank. That is what stops cross-dataset comparison at the data
  layer rather than relying on whoever reads the chart.
- **D-02** — task type is mandatory; comparison happens only within a task type.
- **DZ-4 acceptance** — the handover team clones the repo and reproduces a chart with
  **no live service running**. So: plain files in git, no database server.
- **DZ-3 acceptance** — a failed run is a first-class record, not a discarded one.
  Environment, error, hours spent, blocker.
- **Skills Audit** — avoid account-gated tooling; it becomes a handover liability.

**Steps.**
1. Write `results/README.md` defining the schema and how to add a record.
2. Use **one JSON file per result** under `results/records/`, not one shared file.
   Two people adding results on different branches then never conflict — the same
   reasoning behind the disjoint file ownership in `WORKPLAN.md` §6.
3. Write `scripts/validate_result.py`, mirroring `validate_traversability_map.py`:
   mandatory D-01 fields non-blank, task type from a controlled list, metric names
   present in `docs/metrics-definitions.md`, `status` one of
   `success | partial | failure`.
4. Make the schema **grow additively** — DZ-3 requires that adding a metric later does
   not invalidate existing records.

**Done when.** `scripts/validate_result.py` passes on at least one real record and
fails, with a clear message, on a record missing any mandatory field.

**Output.** `results/README.md` · `scripts/validate_result.py`

---

## D7 — Record the GOOSE work already done

**Goal.** Prove the schema against real results rather than hypothetical ones, and stop
the last fortnight's findings living only in prose.

**Steps.** Write records for what we already have — the dataset characterisation (R2),
the traversability mapping run (D3), and the feasibility test (D5 §6, a success), plus
**at least one failure**: the Pointcept/PTv3 baseline being unrunnable on Apple Silicon
is a real, dated, first-class result.

**Done when.** Every record validates, and the set includes at least one failure.

**Output.** `results/records/*.json`

> If writing a real result into the schema is awkward, the schema is wrong. Fix the
> schema, not the record.

---

## D8 — One page so the other two pairs can use it

**Goal.** Fariya/Kelsey (TruckDrive) and Aiden/Fatima (TruckScenes) are about to
generate results. They need to write into this store without asking either of us how.

**Steps.** A short "how to add a result" section in `results/README.md` — copy the
template, fill it, run the validator, open a PR. Include one worked example.

**Done when.** Someone outside this pair can add a valid record without asking a
question. **Test it by asking one of them**, not by assuming.

---
---

# TASKS — RICKY

## R6 — Close last fortnight's two loose ends

**Goal.** Finish R4 and R5 to their stated definitions of done.

**Steps.**
1. **Third experiment-log entry.** R4 asks for at least three; `experiment-log/` has
   two. The missing one is the traversability rendering (D3) — R4 says to write it from
   Damien's notes in `findings-damien.md`.
2. **Add the projection caveat to `docs/metrics-definitions.md`.** From D4: a
   traversability metric computed from a plain bird's-eye projection **systematically
   understates drivable ground** — roughly halving the apparent blocked share.
   `aying_mangfall_2` goes 92% → 58% non-traversable under a lowest-return-per-cell
   ground slice. Any traversability number must state which projection produced it.

**Done when.** Three entries exist; the caveat is in the metrics document.

---

## R7 — Run the pretrained PTv3 baseline ⚠️ *the point of this phase*

**Goal.** The project's first model result. Or the project's first documented, dated
reason it could not be produced. **Both count.**

**Steps.**
1. Re-download the 3D validation split (`WORKPLAN.md` §2.3).
2. **Resolve the 64→8 challenge-taxonomy mapping first** — see §3 above. It is the most
   likely blocker and it is cheap to check before investing in the environment.
3. Set up Pointcept per `goose_dataset/pointcloud_processing/README.md`, download the
   weights, run against the validation split.
4. Record everything as you go: environment, exact commands, exact errors, hours.

**Done when.** Either a per-class IoU and mIoU compared against the published 0.8096,
**or** a dated failure record with the error, what was attempted, and a recommended
next option.

**Time-box: two days.** Then write it up either way.

**Output.** An experiment-log entry, and a result record via R8.

> **This is the first time anyone on the team has tried to run a model.** Whatever
> happens is worth reporting to Adrian and Fabian — a working reproduction, or a
> concrete account of what stops us. Both answer his kickoff question.

---

## R8 — Record the run *(depends on D6)*

**Goal.** The baseline run, success or failure, recorded in Damien's schema.

**Done when.** `scripts/validate_result.py` passes on it.

> If the schema cannot express your run, say so rather than distorting the run to fit.
> That is a bug in D6 and Damien fixes it.

---

## 4. File ownership — extends `WORKPLAN.md` §6

| Owner | Adds |
|---|---|
| **Damien** | `results/**` · `scripts/validate_result.py` |
| **Ricky** | `experiment-log/**` (already) · `docs/metrics-definitions.md` (already) |
| **Frozen** | This file · `WORKPLAN.md` · `SUMMARY.md` · `GOOSE-CONTEXT.md` · `scripts/session_check.py` · `scripts/validate_*.py` |

`results/records/*.json` is Damien's until D8 lands, after which **anyone may add a new
record file**; nobody edits someone else's.

---

## 5. Definition of done for this phase

- [ ] Result schema documented and validated (D6)
- [ ] Existing GOOSE work recorded, including at least one failure (D7)
- [ ] Another pair can add a record without asking us (D8)
- [ ] Third experiment-log entry exists (R6)
- [ ] Projection caveat recorded in metrics definitions (R6)
- [ ] Baseline run produces a number **or** a dated failure record (R7)
- [ ] That run is recorded in the schema (R8)
- [ ] One PR each, reviewed by the other

## 6. Out of scope

| Not doing | Why |
|---|---|
| Training any model | The project runs existing models; it does not train from scratch |
| STONE | Dropped at the 29 Aug meeting |
| Kaya | Blocked on Adrian; nothing we can do |
| A dashboard or backend | Fariya's FZ-2/FZ-4. The store must work without one (DZ-4) |
| Camera↔LiDAR fusion | Broken upstream — `WORKPLAN.md` §4.4 |
| Chasing GOOSE radar | Not obtainable — see the survey §6 |
