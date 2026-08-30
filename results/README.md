# Results store

Every benchmark result this project reports lives here, as one JSON file per result
under [`records/`](records/) — whichever dataset produced it and whoever ran it.

```bash
python scripts/validate_result.py            # check every record
python scripts/validate_result.py --summary  # see what we have
```

Owner: **Damien Zhang** (DZ-3, DZ-4). Schema version **1**.

---

## Why it is shaped this way

Four constraints came from our own documents, not from preference.

**One file per result, not one shared file.** Three pairs are working three datasets in
parallel on separate branches. A shared spreadsheet or a single JSON array produces a
merge conflict every time two people record something in the same week. Separate files
never conflict. This is the same reasoning as the disjoint file ownership in
`GOOSE - Ricky+Damien/WORKPLAN.md` §6.

**Plain files in git, no database.** DZ-4's acceptance test is that the team inheriting
this project can clone the repository and reproduce a chart **with no live service
running**. The Skills Audit makes the same point from the other direction: anything
needing an account the next team cannot access becomes a handover liability.

**Three identification fields can never be blank.** Decision **D-01** says comparison
happens within a dataset, never across datasets on a shared axis. Rather than trusting
whoever reads the chart to remember that, `dataset`, `sensor_configuration` and
`annotation_schema` are mandatory on every record. A number that cannot say what it is
*of* cannot be plotted against anything.

**Failures are records too.** Story DZ-3 requires that a run which did not work is
captured as a first-class result — environment, error, hours spent, blocker — rather
than discarded. Adrian said the same thing at kickoff: *"we spent X number of days
trying to get it going, we couldn't get it going"* is a reportable outcome. So if
`status` is not `success`, the validator demands `error`, `attempted_fixes`, `blocker`
and `recommendation`.

---

## How to add a result

1. Copy [`records/TEMPLATE.json`](records/TEMPLATE.json) to
   `records/NNNN-short-name.json`, using the next free number.
2. Fill it in. Do not delete fields you cannot answer — say what is true
   (`"unknown"`, `"none"`, `"not measured"`) so the gap is visible.
3. Run `python scripts/validate_result.py records/NNNN-short-name.json`.
4. Open a PR. Nobody edits anyone else's record; you only add your own.

If a metric you want to report is not yet defined in
[`../docs/metrics-definitions.md`](../docs/metrics-definitions.md), **the validator will
reject it**. Define it there first — that document is Ricky's (R5).

> **If a real result is awkward to express in this schema, the schema is wrong.** Raise
> it rather than distorting the run to fit. Changing the schema is a small job;
> discovering later that recorded numbers meant different things is not.

---

## Fields

### Required

| Field | Meaning |
|---|---|
| `schema_version` | `1` |
| `id` | `NNNN-kebab-case`, matching the filename |
| `title` | One line a human can scan |
| `owner` | Who ran it |
| `date` | `YYYY-MM-DD` |
| `status` | `success` · `partial` · `failure` |
| **`dataset`** | **D-01.** Name *and version* — "GOOSE 3D val (2024-07 archive)", not "GOOSE" |
| **`sensor_configuration`** | **D-01.** Which sensors this run actually used, not what the vehicle carries |
| **`annotation_schema`** | **D-01.** Label set, format, version — "GOOSE 64-class semantic, SemanticKITTI `.label`" |
| `task_type` | **D-02.** Controlled list, below. Comparison happens only within one |
| `modality` | `camera` · `lidar` · `radar` · `fusion` · `none` |
| `split` | Which split and subset, e.g. "validation, all 961 frames" |
| `environment` | OS, hardware, Python, key package versions. Enough to know why a number might differ |
| `commands` | List of commands, in order, sufficient to repeat this |
| `evidence` | Repo-relative paths to figures, logs, experiment-log entries |

### Optional

| Field | Meaning |
|---|---|
| `model` | Name and version or commit. Omit for characterisation records |
| `conditions` | Weather, scenario, time of day where it matters |
| `metrics` | List of `{name, value, scope, unit?}` — see below |
| `range_bands` | Banded results where the task supports it (**D-04**) |
| `hours_spent` | What this cost. The next team wants to know |
| `notes` | Anything a reader needs in order not to over-read the number |
| `supersedes` | `id` of a record this replaces |

### Required when `status` is `partial` or `failure`

| Field | Meaning |
|---|---|
| `error` | The **exact** error text, copy-pasted. Paraphrased errors are unsearchable |
| `attempted_fixes` | What was tried, in order, and what happened after each |
| `blocker` | The one thing that stopped it |
| `recommendation` | Retry with what, change to what, or stop |

### Metrics, and why `measurements` is a separate thing

```json
"metrics": [
  {"name": "mIoU", "value": 0.8096, "scope": "8-class challenge taxonomy, val split"}
]
```

A **metric** scores a model against ground truth. `name` must appear in
`docs/metrics-definitions.md` or the record is rejected. `scope` is warned about rather
than enforced, because a bare mIoU is close to meaningless — R5 requires every reported
mIoU to state its evaluated class set, and GOOSE ships two taxonomies that are not
interchangeable.

```json
"measurements": [
  {"name": "labelled points", "value": 174891807, "scope": "all 961 val frames"}
]
```

A **measurement** describes a dataset or an environment. It is not scored against
anything, so it needs no entry in the metrics document.

> This distinction was added in D7, after writing the first real records. The dataset
> characterisation had numbers everyone will cite — 174.9 million points, 62.9% within
> 25 m — that are plainly not evaluation metrics, and forcing them through `metrics`
> would have meant defining "point count" in a document about mIoU and mAP. Worse, it
> would have let a point count sit in the same column as an mIoU in some future table.
>
> Records with `task_type` of `dataset-characterisation` or `feasibility-test` are
> therefore not expected to carry `metrics`, and are warned if they do.

### Task types

`3d-object-detection` · `2d-object-detection` · `camera-lidar-fusion-detection` ·
`3d-multi-object-tracking` · `semantic-segmentation-2d` ·
`semantic-segmentation-3d` · `traversability-prediction` · `depth-estimation` ·
`end-to-end-planning` · `dataset-characterisation` · `feasibility-test`

The last two are not model runs, but they produce numbers we cite elsewhere, so they
are recorded on the same terms.

---

## Growing the schema

New fields may be added at any time. The validator **warns** about unknown fields
rather than rejecting them, so records written before a field existed stay valid —
DZ-3 requires that the metric set can expand without invalidating earlier results.

Making an existing field required, or changing what one means, is a breaking change:
raise `SCHEMA_VERSION`, say why here, and leave old records alone.
