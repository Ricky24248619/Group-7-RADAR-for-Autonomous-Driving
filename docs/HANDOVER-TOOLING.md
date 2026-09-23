# Handover — the shared tooling

**Author: Damien Zhang (Epic B) · 23 September 2026**

Written for someone who inherits this repository with **no access to anyone on the
team**. It covers the shared infrastructure — the results store, the validators, CI,
the ownership guard, the GOOSE renderer and the templates — and says where each one is
weak.

**Scope boundary.** This is the *tooling* handover. The handover of *findings* — what
the project concluded and how confident it is — is RY-S3-1 and lives elsewhere. If you
want to know what the numbers mean, start with `docs/dataset-comparison.md` and the
dataset surveys, not this file.

---

## Ten minutes to a working checkout

You do not need a dataset, a GPU, or any devkit to run everything described here.

```bash
git clone https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving.git
cd Group-7-RADAR-for-Autonomous-Driving
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-ci.txt

python scripts/validate_result.py          # every result record
python scripts/validate_experiment_logs.py # every experiment log
python -m unittest discover -s tests       # the suite
```

If all three pass, your checkout is sound. **Python 3.11 matters** — see
`requirements-ci.txt` for why 3.14 silently collects nine fewer tests.

`requirements-ci.txt` is deliberately *not* the project environment. The devkits and
model stacks (`truckscenes-devkit`, `mmdet3d`, `rosbags`, torch) are large,
platform-specific and in some cases uninstallable on a CI runner. `SETUP.md` is the
environment you install to actually run an experiment.

---

## The results store — `results/`

One JSON file per result under `results/records/`, whichever dataset produced it and
whoever ran it. `results/README.md` explains the design; the short version:

**Three fields can never be blank.** `dataset`, `sensor_configuration` and
`annotation_schema`. Decision **D-01** says comparison happens *within* a dataset,
never across datasets on a shared axis — and rather than trusting a reader to remember
that, the validator refuses a record that cannot say what its number is *of*. `"TBD"`,
`"TODO"`, `"N/A"` and `"-"` all count as blank.

**Failures are records.** If `status` is not `success`, the validator demands `error`,
`attempted_fixes`, `blocker` and `recommendation`. A run that did not work is a
first-class result here. This is not politeness — "we spent three days and could not
get it going" is exactly the finding a successor needs, and it is the one most often
lost.

**One file per record, not one shared file.** Separate files never conflict on merge.
The same reasoning produced `docs/domain-study/README.md` as an index separate from its
template.

**Adding one:** `python scripts/new_result.py` asks for each field, allocates the next
number and refuses to write anything the validator would reject. The manual path is in
`results/README.md`.

---

## The validators

| Script | Checks | Does **not** check |
|---|---|---|
| `validate_result.py` | Record schema, mandatory identification fields, controlled vocabularies, metric names against `docs/metrics-definitions.md`, evidence paths exist and stay inside the repo, duplicate sequence numbers | Whether the experiment ran, whether the number is correct, or whether the conclusion follows |
| `validate_experiment_logs.py` | Log location, unique `EXP-NNNN`, heading matching filename | Anything about the experiment itself |

Say this plainly to anyone who asks: **these check identity and structure, not truth.**
A fabricated result with well-formed fields passes both. The defence against that is
review and reproduction, not tooling.

`scripts/validate_traversability_map.py` checks the GOOSE 64-class → 4-level mapping
CSV is complete and well-formed.

---

## CI — `.github/workflows/checks.yml`

Runs both validators and the test suite on every pull request and every push to
`main`. **On `main` today this is Ubuntu only.** A two-OS matrix adding `windows-latest`
is in PR #43 and had not landed at the time of writing — check
`.github/workflows/checks.yml` for which you actually have.

That distinction is not pedantry. A Ubuntu-only run **cannot see** the platform bugs
this project has already hit: a `write_text` call without `newline=""` emits CRLF on
Windows and LF everywhere else, so a test asserting reproducible output passes on macOS
and Ubuntu and fails only on Windows. Two such defects reached review green, and one of
them I approved on the strength of a macOS-only run. **If the matrix is not in your
workflow file, add it before trusting a green check on anything that writes a file.**

CI exists at all because **sequence collisions reached `main` twice**, with a third open
between two pull requests at the time of writing. Git reports no conflict when two
branches each add a differently-named file, so two people both take "the next free
number", both are right on their own branch, and `main` ends up with two records
claiming one identifier. Review missed it every time.

---

## `scripts/session_check.py` — the ownership guard

Two people working one repository from different machines with different AI assistants.
Run it at the start of a session and before every commit:

```bash
python scripts/session_check.py --who damien
```

It checks you are on your own branch, that the branch is current with `origin/main`,
and that every file you touched belongs to you. File ownership is disjoint by design —
see `GOOSE - Ricky+Damien/WORKPLAN.md` §6.

If you inherit this as a solo worker, this script is the first thing you can delete.

---

## The GOOSE renderer

| Script | Purpose |
|---|---|
| `goose_render_frame.py` | Render one frame; colour points by any grouping of the 64 classes |
| `goose_contact_sheet.py` | All eight scenarios on one sheet — seasonal and terrain range |
| `goose_traversability.py` | Render drivable / uncertain / blocked from `traversability_map.csv` |
| `goose_client_figure.py` | The client-facing figure: ground material beside drivable surface |
| `goose_bag_topics.py` | List topics in the raw ROS bags |

**One decision you should not undo without understanding it.** A plain overhead view
hides drivable ground beneath tree canopy. The renderer takes the *lowest* return in
each 0.4 m ground cell instead. An earlier absolute-height threshold produced the
opposite conclusion and was wrong — on sloping ground, absolute height does not
separate canopy from terrain. Switching to lowest-per-cell roughly **halves** the
apparent blocked share; one scene moved from 92% to 58% non-traversable.

**The judgement lives in data, not code.** `GOOSE - Ricky+Damien/traversability_map.csv`
maps all 64 classes to four levels, each with a written rationale, and
`traversability-map-notes.md` records the fourteen genuinely contested ones. Change
assignments **in the CSV**, never as exceptions in the renderer — that is what lets a
reviewer disagree with one line rather than the whole approach.

These figures group **human labels**. They do not show a model deciding where a vehicle
can drive, and they do not establish a safe route.

---

## Templates

| File | For |
|---|---|
| `docs/dataset-survey-template.md` | One survey per dataset, fixed checklist |
| `docs/domain-study-template.md` | WS1 source study entries; index in `docs/domain-study/README.md` |
| `templates/experiment-log-entry.md` | One entry per experiment attempt (Ricky's) |
| `templates/comparison-record.md` | Benchmark record with D-01 fields (Ricky's) |

---

## What I would change

Honest design criticism, because a successor inherits the consequences.

**Sequential numbering was the wrong identifier scheme.** `NNNN-short-name` is
human-friendly and citable, which is why it was chosen, but it has collided three
times in six weeks. Local allocation cannot see another branch; CI catches it only on the second
merge, after someone has already done the work. A content hash or a branch-prefixed
id would not collide at all, at the cost of uglier citations. If you are starting
fresh, take the ugly identifier.

**`validate_result.py` splits its checks in a way that caused a real bug.** `check()`
validates one file; duplicate-sequence detection lives separately in `main()` (around
line 573). So `new_result.py` could call `check()`, get a pass, and write a duplicate —
which it did, until PR #37 fixed it. A `check_collection()` API alongside `check()`
would have made the mistake impossible. Anything programmatic that "validates" a record
must validate the *collection*, not the file.

**Metrics-before-results is right but too rigid.** The validator rejects a metric name
absent from `docs/metrics-definitions.md`, which is correct — it stops undefined numbers
escaping. But it means a new metric blocks a result record until a different owner
updates a different document. A `proposed` state in the metrics document would keep the
discipline without the stall.

**Evidence paths are checked for existence, not for relevance.** Nothing notices when a
record cites a file that no longer says what it used to. Dead evidence accumulates
silently.

---

## Deliberately unfinished

Recorded rather than hidden, per this project's own rule.

- **The cold read (P-6, DS-4).** No output has been read by someone outside the pair
  that produced it. This was an acceptance test from Sprint 1 and it is still open.
- **Outside-team reproduction (P-5).** One team member reproduced another's workflow
  across macOS and Windows — useful, but both are insiders. Nobody outside the team has
  cloned this and rebuilt a result.
- **WS1, the cross-team sensor survey.** Index, assignments and claims ledger exist at
  `docs/domain-study/`; **zero entries**. Six people each owe one source. This is why
  P-2 sits at "partly met".
- **No matched radar-versus-LiDAR detector benchmark.** The project's headline question
  is unanswered. What exists is dataset characterisation, sensor-coverage counts and
  one camera-only transfer experiment scoring effectively zero.
- **GOOSE validation split: 960 published, 961 extracted.** Internally consistent, cause
  unexplained. Needs a local-versus-published file inventory.

---

## Provenance

Files above are mine unless noted: the results store and its validator (SH-1, SH-2),
`session_check.py`, the GOOSE renderer family, the survey and domain-study templates,
`new_result.py`, the issue form and the CI workflow. `goose_stats.py`,
`metrics-definitions.md`, `validate_experiment_logs.py` and both files in `templates/`
are Ricky Yuen's. TruckScenes scripts are Fatima Sher's and Aiden Blampain's;
TruckDrive scripts are Kelsey Chen's.

Some of this is still in review at the time of writing: `new_result.py` and the issue
form (#35), the WS1 index (#36), the suitability comparison (#34). If a path here does
not exist in your checkout, that PR did not land — check the closed pull requests
before assuming the file was deleted.
