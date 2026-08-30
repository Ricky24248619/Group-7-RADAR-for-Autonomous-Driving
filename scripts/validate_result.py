#!/usr/bin/env python3
"""Validate benchmark result records against the schema in results/README.md (task D6).

Every result this project reports lives in one JSON file under results/records/,
whichever dataset or pair produced it. This validator is what stops the schema being a
suggestion.

    python scripts/validate_result.py                    # every record
    python scripts/validate_result.py --summary          # table of what we have
    python scripts/validate_result.py results/records/0001-x.json

What it enforces, and why:

* Decision D-01 -- dataset, sensor configuration and annotation schema can never be
  blank. That is what keeps cross-dataset comparison impossible at the data layer
  rather than depending on whoever reads the chart later.
* Decision D-02 -- task_type comes from a controlled list, because comparison happens
  only within a task type.
* Story DZ-3 -- a failed run is a first-class record. If status is not success, the
  error, what was attempted and a recommendation are all mandatory.
* Story DZ-4 -- a metric name must already be defined in docs/metrics-definitions.md.
  An undefined metric in a results table is a bug in the results table.

Unknown extra fields are allowed and only warned about, so the schema can grow
additively without invalidating records written before the new field existed.
"""

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
RECORDS = REPO / "results" / "records"
METRICS_DOC = REPO / "docs" / "metrics-definitions.md"

SCHEMA_VERSION = 1

# D-01: these three identify what a number is *of*. Blank is never acceptable.
IDENTIFICATION = ["dataset", "sensor_configuration", "annotation_schema"]

REQUIRED = IDENTIFICATION + [
    "schema_version", "id", "title", "owner", "date", "status", "task_type",
    "modality", "split", "environment", "commands", "evidence",
]

OPTIONAL = [
    "model", "conditions", "hours_spent", "metrics", "measurements", "range_bands",
    "notes", "error", "attempted_fixes", "blocker", "recommendation", "supersedes",
]

# D-02. Comparison happens only within one of these.
TASK_TYPES = [
    "3d-object-detection",
    "2d-object-detection",
    "camera-lidar-fusion-detection",
    "3d-multi-object-tracking",
    "semantic-segmentation-2d",
    "semantic-segmentation-3d",
    "traversability-prediction",
    "depth-estimation",
    "end-to-end-planning",
    # Not model runs, but they produce numbers we cite, so they are recorded too.
    "dataset-characterisation",
    "feasibility-test",
]

# These produce numbers we cite, but not *evaluation* numbers. They describe a dataset
# or an environment rather than scoring a model, so they are not expected to carry
# metrics — see the metrics/measurements distinction in results/README.md.
NON_MODEL_TASKS = {"dataset-characterisation", "feasibility-test"}

MODALITIES = ["camera", "lidar", "radar", "fusion", "none"]
STATUSES = ["success", "partial", "failure"]

# DZ-3: a failure record without these is not a result, it is a shrug.
FAILURE_REQUIRED = ["error", "attempted_fixes", "blocker", "recommendation"]

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def defined_metrics():
    """Metric names Ricky's metrics-definitions.md declares. Lowercased for matching."""
    if not METRICS_DOC.is_file():
        return None
    return METRICS_DOC.read_text(encoding="utf-8-sig").lower()


def blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().upper() in {"TBD", "TODO", "N/A", "-"}
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def check(path, metrics_text):
    """Return (errors, warnings) for one record."""
    errors, warnings = [], []
    try:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return [f"not valid JSON: {exc}"], []
    if not isinstance(record, dict):
        return ["top level must be a JSON object"], []

    for field in REQUIRED:
        if field not in record:
            errors.append(f"missing required field '{field}'")
        elif blank(record[field]):
            note = " (D-01: this is what makes results comparable)" \
                if field in IDENTIFICATION else ""
            errors.append(f"'{field}' is blank{note}")

    for key in record:
        if key not in REQUIRED + OPTIONAL:
            warnings.append(f"unknown field '{key}' — fine if the schema grew, "
                            f"a typo otherwise")

    if record.get("schema_version") not in (None, SCHEMA_VERSION):
        warnings.append(f"schema_version {record['schema_version']} != "
                        f"{SCHEMA_VERSION} — written against a different schema")

    if (task := record.get("task_type")) and task not in TASK_TYPES:
        errors.append(f"task_type '{task}' is not one of: {', '.join(TASK_TYPES)}")

    if (mod := record.get("modality")) and mod not in MODALITIES:
        errors.append(f"modality '{mod}' is not one of: {', '.join(MODALITIES)}")

    status = record.get("status")
    if status and status not in STATUSES:
        errors.append(f"status '{status}' is not one of: {', '.join(STATUSES)}")

    # DZ-3: failures are first-class, which means they carry the same burden of detail.
    if status in ("failure", "partial"):
        for field in FAILURE_REQUIRED:
            if blank(record.get(field)):
                errors.append(f"status is '{status}', so '{field}' is required "
                              f"(DZ-3: a failed run is a first-class result)")
    if (status == "success" and blank(record.get("metrics"))
            and task not in NON_MODEL_TASKS):
        warnings.append("status is 'success' but no metrics recorded — intentional?")
    if task in NON_MODEL_TASKS and not blank(record.get("metrics")):
        warnings.append(f"task_type '{task}' carries evaluation metrics — did you mean "
                        f"'measurements'? Metrics are scores against ground truth; "
                        f"measurements describe a dataset or environment")

    # DZ-4: nothing gets reported under a name that has not been defined first.
    for i, metric in enumerate(record.get("metrics") or []):
        where = f"metrics[{i}]"
        if not isinstance(metric, dict):
            errors.append(f"{where} must be an object with name and value")
            continue
        name = metric.get("name")
        if blank(name):
            errors.append(f"{where} has no name")
            continue
        if "value" not in metric:
            errors.append(f"{where} '{name}' has no value")
        if metrics_text is None:
            warnings.append(f"{where}: cannot check '{name}', metrics doc not found")
        elif name.lower() not in metrics_text:
            errors.append(
                f"{where}: metric '{name}' is not defined in "
                f"docs/metrics-definitions.md. Define it there first — an undefined "
                f"metric in a results table is a bug in the results table")
        if "scope" not in metric:
            warnings.append(f"{where} '{name}': no 'scope' — which class set, split "
                            f"or range band does this number cover?")

    for i, m in enumerate(record.get("measurements") or []):
        if not isinstance(m, dict) or blank(m.get("name")) or "value" not in m:
            errors.append(f"measurements[{i}] needs at least a name and a value")

    if (rid := record.get("id")) and not re.fullmatch(r"[0-9]{4}-[a-z0-9-]+", str(rid)):
        warnings.append(f"id '{rid}' is not NNNN-kebab-case; filenames stay sortable "
                        f"if it is")
    if rid and path.stem != rid:
        warnings.append(f"id '{rid}' does not match filename '{path.stem}'")

    if (date := record.get("date")) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(date)):
        errors.append(f"date '{date}' must be YYYY-MM-DD")

    return errors, warnings


def summary(paths):
    print(f"\n{'id':<36}{'status':<9}{'task':<28}{'dataset':<16}owner")
    print("-" * 100)
    for p in paths:
        try:
            r = json.loads(p.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            print(f"{p.stem:<34}{'INVALID':<9}"); continue
        mark = {"success": GREEN, "partial": YELLOW, "failure": RED}.get(
            r.get("status"), "")
        print(f"{str(r.get('id', p.stem)):<36}"
              f"{mark}{str(r.get('status', '?')):<9}{RESET}"
              f"{str(r.get('task_type', '?')):<28}"
              f"{str(r.get('dataset', '?'))[:15]:<16}"
              f"{r.get('owner', '?')}")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="Records to check. Default: all of them.")
    ap.add_argument("--summary", action="store_true", help="List records, do not check")
    args = ap.parse_args()

    # TEMPLATE.json is the thing you copy, not a result. It holds placeholder values
    # by design, so it is skipped unless named explicitly.
    paths = ([pathlib.Path(p) for p in args.paths]
             or sorted(p for p in RECORDS.glob("*.json") if p.stem != "TEMPLATE"))
    if not paths:
        print(f"No records under {RECORDS} yet — only the template. "
              f"Copy it to get started; see results/README.md.")
        return 0

    if args.summary:
        summary(paths)
        return 0

    metrics_text = defined_metrics()
    if metrics_text is None:
        print(f"{YELLOW}WARN{RESET}  {METRICS_DOC} not found — "
              f"metric names cannot be checked\n")

    total_errors = 0
    for path in paths:
        errors, warnings = check(path, metrics_text)
        total_errors += len(errors)
        state = f"{RED}INVALID{RESET}" if errors else f"{GREEN}valid{RESET}"
        print(f"{state}  {path.name}")
        for w in warnings:
            print(f"    {YELLOW}warn{RESET}  {w}")
        for e in errors:
            print(f"    {RED}FAIL{RESET}  {e}")

    print()
    if total_errors:
        print(f"{RED}{total_errors} error(s) across {len(paths)} record(s).{RESET}")
        return 1
    print(f"{GREEN}All {len(paths)} record(s) valid.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
