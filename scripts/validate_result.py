#!/usr/bin/env python3
"""Validate benchmark result records against ``results/README.md`` (task D6).

Every result this project reports lives in one JSON file under ``results/records``.
The validator deliberately rejects malformed records instead of letting Python's
permissive JSON decoder or truthiness rules turn schema errors into valid results.

    python scripts/validate_result.py                    # every record
    python scripts/validate_result.py --summary          # table of what we have
    python scripts/validate_result.py results/records/0001-x.json

Unknown top-level fields are allowed and only warned about, so the schema can grow
additively without invalidating older records. Documented field types and values are
enforced.
"""

import argparse
import datetime as dt
import json
import math
import pathlib
import re
import sys
from collections.abc import Iterable
from typing import Any

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

STRING_FIELDS = set(IDENTIFICATION) | {
    "id", "title", "owner", "date", "status", "task_type", "modality", "split",
}
OPTIONAL_STRING_FIELDS = {
    "model", "conditions", "notes", "error", "blocker", "recommendation",
    "supersedes",
}

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

# These describe a dataset or environment rather than scoring a model.
NON_MODEL_TASKS = {"dataset-characterisation", "feasibility-test"}

MODALITIES = ["camera", "lidar", "radar", "fusion", "none"]
STATUSES = ["success", "partial", "failure"]

# DZ-3: a failure record without these is not a result, it is a shrug.
FAILURE_REQUIRED = ["error", "attempted_fixes", "blocker", "recommendation"]

METRIC_KEYS = {"name", "value", "scope", "unit"}
MEASUREMENT_KEYS = {"name", "value", "scope", "unit"}

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


class StrictJSONError(ValueError):
    """Raised when input uses a construct the JSON result format forbids."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StrictJSONError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise StrictJSONError(f"non-standard numeric constant {value!r}")


def load_record(path: pathlib.Path) -> tuple[Any | None, str | None]:
    """Load strict JSON, returning an error string instead of raising."""
    try:
        text = path.read_text(encoding="utf-8-sig")
        return (
            json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_json_constant,
            ),
            None,
        )
    # CPython raises ValueError for integers beyond its safe digit limit and
    # RecursionError for excessively nested arrays/objects. Both are malformed
    # records, not validator crashes.
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        return None, f"not valid JSON: {exc}"


def _normalise_metric_name(name: str) -> str:
    """Normalise case/spacing while retaining exact whole-name matching."""
    return " ".join(name.split()).casefold()


# Exact canonical metric names from docs/metrics-definitions.md. Do not use suffix
# or substring tests here: e.g. "published baseline mIoU" is not the mIoU metric.
RATIO_METRIC_NAMES = frozenset(
    {
        "precision",
        "recall",
        "map",
        "per-class iou",
        "2d per-class iou",
        "3d per-class iou",
        "4-class traversability iou",
        "miou",
        "overall accuracy",
    }
)
NONNEGATIVE_METRIC_NAMES = frozenset({"processing time"})


def parse_defined_metrics(text: str) -> frozenset[str]:
    """Extract names explicitly defined by the metrics document.

    Definitions are the first column of a Markdown ``Metric`` table, plus the
    explicitly defined bold terms in the segmentation formula section. Composite
    table cells such as ``2D per-class IoU / mIoU`` declare both names. The returned
    set is suitable for exact membership checks; prose containing a metric name does
    not accidentally define a new one.
    """
    names: set[str] = set()
    in_metric_table = False

    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^\|\s*Metric\s*\|", stripped, flags=re.IGNORECASE):
            in_metric_table = True
            continue
        if in_metric_table:
            if not stripped.startswith("|"):
                in_metric_table = False
            else:
                cells = [cell.strip() for cell in stripped.strip("|").split("|")]
                first = cells[0] if cells else ""
                if first and not re.fullmatch(r":?-{3,}:?", first):
                    first = re.sub(r"[`*_]", "", first).strip()
                    for name in re.split(r"\s+/\s+", first):
                        if name:
                            names.add(_normalise_metric_name(name))

        # The exact-definition prose includes bullet definitions and ``mIoU is``.
        match = re.match(r"^\s*-\s+\*\*([^*]+?)\*\*\s*", line)
        if match:
            name = match.group(1).rstrip(":").strip()
            if name:
                names.add(_normalise_metric_name(name))
        match = re.match(r"^\s*\*\*([^*]+?)\*\*\s+is\b", line)
        if match:
            names.add(_normalise_metric_name(match.group(1)))

    return frozenset(names)


def defined_metrics() -> frozenset[str] | None:
    """Return metric names explicitly declared in ``metrics-definitions.md``."""
    try:
        return parse_defined_metrics(METRICS_DOC.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError):
        return None


def blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().upper() in {"TBD", "TODO", "N/A", "-"}
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _is_number(value: Any) -> bool:
    # JSON integers are exact and always finite, including values too large to cast
    # to a C double. Booleans are deliberately excluded even though bool subclasses
    # int in Python.
    if type(value) is int:
        return True
    return type(value) is float and math.isfinite(value)


def _json_locations(value: Any, prefix: str = "$") -> Iterable[tuple[str, float]]:
    """Yield every non-finite float and its JSON-like location."""
    if isinstance(value, float) and not math.isfinite(value):
        yield prefix, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _json_locations(child, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _json_locations(child, f"{prefix}[{index}]")


def _check_nonempty_string_list(
    record: dict[str, Any], field: str, errors: list[str], *, required: bool
) -> bool:
    """Validate a list of non-empty strings and return whether its type is valid."""
    if field not in record:
        return False
    value = record[field]
    if not isinstance(value, list):
        errors.append(f"'{field}' must be a non-empty list of non-empty strings")
        return False
    if required and not value:
        errors.append(f"'{field}' must be a non-empty list of non-empty strings")
        return True
    for index, item in enumerate(value):
        if not isinstance(item, str) or blank(item):
            errors.append(f"'{field}[{index}]' must be a non-empty string")
    return True


def _check_named_values(
    record: dict[str, Any],
    field: str,
    allowed_keys: set[str],
    errors: list[str],
    warnings: list[str],
    metric_names: frozenset[str] | None,
) -> None:
    if field not in record:
        return
    values = record[field]
    if not isinstance(values, list):
        errors.append(f"'{field}' must be a list of objects")
        return

    singular = "metric" if field == "metrics" else "measurement"
    for index, item in enumerate(values):
        where = f"{field}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where} must be an object with name and value")
            continue

        for key in item:
            if key not in allowed_keys:
                warnings.append(f"{where}: unknown {singular} field '{key}'")

        name = item.get("name")
        if not isinstance(name, str) or blank(name):
            errors.append(f"{where}.name must be a non-empty string")
            name = None

        if "value" not in item:
            errors.append(f"{where} has no value")
        elif not _is_number(item["value"]):
            errors.append(f"{where}.value must be a finite JSON number")

        normalised_name = (
            _normalise_metric_name(name) if name is not None else None
        )
        value = item.get("value")
        # Apply semantic ranges only to exact names which the loaded definitions
        # actually declare. Measurements deliberately have no universal range.
        if (
            field == "metrics"
            and normalised_name is not None
            and metric_names is not None
            and normalised_name in metric_names
            and _is_number(value)
        ):
            if normalised_name in RATIO_METRIC_NAMES and not 0 <= value <= 1:
                errors.append(
                    f"{where}.value for '{name}' must be between 0 and 1 inclusive"
                )
            elif (
                normalised_name in NONNEGATIVE_METRIC_NAMES and value < 0
            ):
                errors.append(
                    f"{where}.value for '{name}' must be non-negative"
                )

        for string_key in ("scope", "unit"):
            if string_key in item and (
                not isinstance(item[string_key], str) or blank(item[string_key])
            ):
                errors.append(f"{where}.{string_key} must be a non-empty string")

        if field == "metrics" and name is not None:
            if metric_names is None:
                warnings.append(f"{where}: cannot check '{name}', metrics doc not found")
            elif normalised_name not in metric_names:
                errors.append(
                    f"{where}: metric '{name}' is not exactly defined in "
                    "docs/metrics-definitions.md. Define it there first — an "
                    "undefined metric in a results table is a bug in the results table"
                )
            if "scope" not in item:
                warnings.append(
                    f"{where} '{name}': no 'scope' — which class set, split or "
                    "range band does this number cover?"
                )


def _check_evidence_paths(record: dict[str, Any], errors: list[str]) -> None:
    evidence = record.get("evidence")
    if not isinstance(evidence, list):
        return

    repo_root = REPO.resolve()
    for index, raw_path in enumerate(evidence):
        if not isinstance(raw_path, str) or blank(raw_path):
            continue  # The list-shape check reports this.
        where = f"evidence[{index}]"
        try:
            path = pathlib.Path(raw_path)
            # PureWindowsPath catches drive/UNC paths even if this runs in Linux CI.
            if path.is_absolute() or pathlib.PureWindowsPath(raw_path).is_absolute():
                errors.append(f"{where} must be a repo-relative path: '{raw_path}'")
                continue
            resolved = (repo_root / path).resolve()
            try:
                resolved.relative_to(repo_root)
            except ValueError:
                errors.append(f"{where} escapes the repository: '{raw_path}'")
                continue
            if not resolved.exists():
                errors.append(f"{where} does not exist in the repository: '{raw_path}'")
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"{where} is not a usable repo-relative path: {exc}")


def check(
    path: pathlib.Path | str, metric_names: frozenset[str] | str | None
):
    """Return ``(errors, warnings)`` for one record; malformed input never raises."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        record_path = pathlib.Path(path)
    except (TypeError, ValueError, OSError) as exc:
        return [f"invalid record path: {exc}"], []

    record, load_error = load_record(record_path)
    if load_error:
        return [load_error], []
    if not isinstance(record, dict):
        return ["top level must be a JSON object"], []

    # Preserve the helper's old raw-document calling convention while still doing
    # exact membership checks. ``defined_metrics()`` now returns the parsed set.
    if isinstance(metric_names, str):
        metric_names = parse_defined_metrics(metric_names)

    for location, value in _json_locations(record):
        errors.append(f"{location} must be finite, got {value!r}")

    for field in REQUIRED:
        if field not in record:
            errors.append(f"missing required field '{field}'")
        elif blank(record[field]):
            note = (
                " (D-01: this is what makes results comparable)"
                if field in IDENTIFICATION else ""
            )
            errors.append(f"'{field}' is blank{note}")

    for key in record:
        if key not in REQUIRED + OPTIONAL:
            warnings.append(
                f"unknown field '{key}' — fine if the schema grew, a typo otherwise"
            )

    for field in STRING_FIELDS:
        if field in record and not isinstance(record[field], str):
            errors.append(f"'{field}' must be a non-empty string")
    for field in OPTIONAL_STRING_FIELDS:
        if field in record and (
            not isinstance(record[field], str) or blank(record[field])
        ):
            errors.append(f"'{field}' must be a non-empty string when present")

    version = record.get("schema_version")
    if "schema_version" in record and (
        type(version) is not int or version != SCHEMA_VERSION
    ):
        errors.append(
            f"schema_version must be exactly integer {SCHEMA_VERSION}; got {version!r}"
        )

    environment = record.get("environment")
    if "environment" in record and not isinstance(environment, dict):
        errors.append("'environment' must be a non-empty object")

    _check_nonempty_string_list(record, "commands", errors, required=True)
    _check_nonempty_string_list(record, "evidence", errors, required=True)
    _check_evidence_paths(record, errors)

    task = record.get("task_type")
    if isinstance(task, str) and task not in TASK_TYPES:
        errors.append(f"task_type '{task}' is not one of: {', '.join(TASK_TYPES)}")

    modality = record.get("modality")
    if isinstance(modality, str) and modality not in MODALITIES:
        errors.append(f"modality '{modality}' is not one of: {', '.join(MODALITIES)}")

    status = record.get("status")
    if isinstance(status, str) and status not in STATUSES:
        errors.append(f"status '{status}' is not one of: {', '.join(STATUSES)}")

    # DZ-3: failures are first-class, which means they carry the same burden of detail.
    if status in ("failure", "partial"):
        for field in ("error", "blocker", "recommendation"):
            if field not in record or not isinstance(record[field], str) or blank(record[field]):
                errors.append(
                    f"status is '{status}', so '{field}' must be a non-empty string "
                    "(DZ-3: a failed run is a first-class result)"
                )
        if "attempted_fixes" not in record:
            errors.append(
                f"status is '{status}', so 'attempted_fixes' is required "
                "(DZ-3: a failed run is a first-class result)"
            )
        else:
            _check_nonempty_string_list(record, "attempted_fixes", errors, required=True)
    elif "attempted_fixes" in record:
        _check_nonempty_string_list(record, "attempted_fixes", errors, required=False)

    metrics = record.get("metrics")
    if (
        status == "success"
        and (not isinstance(metrics, list) or not metrics)
        and isinstance(task, str)
        and task not in NON_MODEL_TASKS
    ):
        warnings.append("status is 'success' but no metrics recorded — intentional?")
    if (
        isinstance(task, str)
        and task in NON_MODEL_TASKS
        and isinstance(metrics, list)
        and metrics
    ):
        warnings.append(
            f"task_type '{task}' carries evaluation metrics — did you mean "
            "'measurements'? Metrics are scores against ground truth; measurements "
            "describe a dataset or environment"
        )

    _check_named_values(
        record, "metrics", METRIC_KEYS, errors, warnings, metric_names
    )
    _check_named_values(
        record, "measurements", MEASUREMENT_KEYS, errors, warnings, metric_names
    )

    hours = record.get("hours_spent")
    if "hours_spent" in record and (not _is_number(hours) or hours < 0):
        errors.append("'hours_spent' must be a finite non-negative JSON number")

    rid = record.get("id")
    if isinstance(rid, str):
        if not re.fullmatch(r"[0-9]{4}-[a-z0-9-]+", rid):
            errors.append(f"id '{rid}' must be NNNN-kebab-case")
        if record_path.stem != rid:
            errors.append(f"id '{rid}' does not match filename '{record_path.stem}'")

    date = record.get("date")
    if isinstance(date, str):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            errors.append(f"date '{date}' must be YYYY-MM-DD")
        else:
            try:
                dt.date.fromisoformat(date)
            except ValueError:
                errors.append(f"date '{date}' is not a valid calendar date")

    return errors, warnings


def summary(paths: list[pathlib.Path]) -> None:
    print(f"\n{'id':<36}{'status':<9}{'task':<28}{'dataset':<16}owner")
    print("-" * 100)
    for path in paths:
        record, error = load_record(path)
        if error or not isinstance(record, dict):
            print(f"{path.stem:<36}{'INVALID':<9}")
            continue
        status = record.get("status")
        mark = (
            {"success": GREEN, "partial": YELLOW, "failure": RED}.get(status, "")
            if isinstance(status, str)
            else ""
        )
        print(
            f"{str(record.get('id', path.stem)):<36}"
            f"{mark}{str(record.get('status', '?')):<9}{RESET}"
            f"{str(record.get('task_type', '?')):<28}"
            f"{str(record.get('dataset', '?'))[:15]:<16}"
            f"{record.get('owner', '?')}"
        )
    print()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="*", help="Records to check. Default: all of them.")
    ap.add_argument("--summary", action="store_true", help="List records, do not check")
    args = ap.parse_args()

    # TEMPLATE.json is copied, not validated by default; it contains placeholders.
    paths = (
        [pathlib.Path(path) for path in args.paths]
        or sorted(path for path in RECORDS.glob("*.json") if path.stem != "TEMPLATE")
    )
    if not paths:
        print(
            f"No records under {RECORDS} yet — only the template. "
            "Copy it to get started; see results/README.md."
        )
        return 0

    if args.summary:
        summary(paths)
        return 0

    metric_names = defined_metrics()
    if metric_names is None:
        print(
            f"{YELLOW}WARN{RESET}  {METRICS_DOC} not found or unreadable — "
            "metric names cannot be checked\n"
        )

    total_errors = 0
    for path in paths:
        errors, warnings = check(path, metric_names)
        total_errors += len(errors)
        state = f"{RED}INVALID{RESET}" if errors else f"{GREEN}valid{RESET}"
        print(f"{state}  {path.name}")
        for warning in warnings:
            print(f"    {YELLOW}warn{RESET}  {warning}")
        for error in errors:
            print(f"    {RED}FAIL{RESET}  {error}")

    print()
    if total_errors:
        print(f"{RED}{total_errors} error(s) across {len(paths)} record(s).{RESET}")
        return 1
    print(f"{GREEN}All {len(paths)} record(s) valid.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
