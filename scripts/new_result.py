#!/usr/bin/env python3
"""Write a valid result record without needing to know the schema (task D8).

    python scripts/new_result.py

Asks for each field in turn, allocates the next free sequence number, and
refuses to write anything ``validate_result.py`` would reject.

Why this exists
---------------
Adding a result previously meant copying ``TEMPLATE.json``, reading
``results/README.md`` to learn the controlled vocabularies, and hand-picking
"the next free number". In practice the other pairs asked the GOOSE pair to do
it, which made one pair a bottleneck on everyone else's evidence and a handover
liability the moment that pair stops.

Hand-picking numbers also does not work across parallel branches. Git reports no
conflict when two branches each add a differently-named file, so two people both
take "the next free number", both are right on their own branch, and main ends up
with two records claiming one identifier. That has happened to this project
twice. Local allocation prevents local collisions; independent Git branches
still require validation against current main before merging.

Every rule enforced here is imported from ``validate_result`` rather than
restated, so the two can never drift. If the schema changes, this script follows
it automatically.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import validate_result as vr

RECORDS = vr.RECORDS
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

BOLD, DIM, GREEN, RED, YELLOW, RESET = (
    "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[0m"
)


def next_sequence_number(records_dir: pathlib.Path = RECORDS) -> str:
    """Return the next free NNNN, one past the highest already present.

    Deliberately one past the *highest* rather than the first gap. A gap is
    usually a record that was renumbered or withdrawn, and reusing its number
    would make an existing citation point at different work.
    """
    highest = 0
    if records_dir.is_dir():
        for path in records_dir.glob("*.json"):
            match = re.match(r"([0-9]{4})-", path.name)
            if match:
                highest = max(highest, int(match[1]))
    return f"{highest + 1:04d}"


class Prompter:
    """Wraps input so tests can drive the script without a terminal."""

    def __init__(self, reader: Callable[[str], str] | None = None,
                 writer: Callable[[str], None] | None = None) -> None:
        self._read = reader if reader is not None else input
        self._write = writer if writer is not None else (lambda s: print(s))

    def say(self, text: str = "") -> None:
        self._write(text)

    def ask(self, label: str, *, default: str = "", required: bool = True,
            help_text: str = "") -> str:
        if help_text:
            self.say(f"  {DIM}{help_text}{RESET}")
        suffix = f" [{default}]" if default else ""
        while True:
            answer = self._read(f"  {label}{suffix}: ").strip()
            if not answer and default:
                return default
            if answer and not vr.blank(answer):
                return answer
            if not required:
                return ""
            # vr.blank also rejects TBD/TODO/N/A/-, which the validator treats as
            # blank. Saying so here beats being rejected after 14 more questions.
            self.say(f"  {RED}Required. 'TBD', 'TODO', 'N/A' and '-' count as "
                     f"blank — write what is actually true.{RESET}")

    def choose(self, label: str, options: list[str], *, default: str = "") -> str:
        self.say()
        for index, option in enumerate(options, 1):
            self.say(f"    {index:2}. {option}")
        while True:
            raw = self.ask(label, default=default)
            if raw in options:
                return raw
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1]
            self.say(f"  {RED}Pick a number 1–{len(options)}, or type the value.{RESET}")

    def ask_list(self, label: str, *, help_text: str = "",
                 required: bool = True) -> list[str]:
        if help_text:
            self.say(f"  {DIM}{help_text}{RESET}")
        self.say(f"  {DIM}One per line. Blank line ends the list.{RESET}")
        items: list[str] = []
        while True:
            line = self._read(f"  {label}[{len(items) + 1}]: ").strip()
            if not line:
                if items or not required:
                    return items
                self.say(f"  {RED}At least one entry required.{RESET}")
                continue
            items.append(line)

    def yes_no(self, label: str, *, default: bool = False) -> bool:
        answer = self.ask(label, default="y" if default else "n").lower()
        return answer.startswith("y")


def _ask_named_values(prompter: Prompter, kind: str,
                      defined: frozenset[str] | None) -> list[dict[str, Any]]:
    """Collect metrics or measurements, each with the scope that bounds it."""
    entries: list[dict[str, Any]] = []
    if kind == "metrics" and defined is not None:
        if defined:
            prompter.say(f"  {DIM}Defined in docs/metrics-definitions.md: "
                         f"{', '.join(sorted(defined))}{RESET}")
        else:
            prompter.say(f"  {YELLOW}No metrics are defined yet. Define one in "
                         f"docs/metrics-definitions.md first — the validator "
                         f"rejects undefined metric names.{RESET}")
    while prompter.yes_no(f"Add {'another' if entries else 'a'} {kind[:-1]}?",
                          default=not entries and kind == "metrics"):
        name = prompter.ask("  name")
        raw_value = prompter.ask("  value (number)")
        try:
            value: Any = int(raw_value)
        except ValueError:
            try:
                value = float(raw_value)
            except ValueError:
                prompter.say(f"  {RED}Not a number — entry skipped.{RESET}")
                continue
        scope = prompter.ask(
            "  scope", help_text="Which class set, split or range band this "
                                 "number covers. An unscoped number is unusable.")
        entry: dict[str, Any] = {"name": name, "value": value, "scope": scope}
        unit = prompter.ask("  unit", required=False)
        if unit:
            entry["unit"] = unit
        entries.append(entry)
    return entries


def build_record(prompter: Prompter, *, number: str,
                 today: str | None = None) -> tuple[str, dict[str, Any]]:
    """Ask for every field and return ``(short_name, record)``."""
    today = today or dt.date.today().isoformat()

    prompter.say(f"\n{BOLD}New result record{RESET}  {DIM}→ "
                 f"results/records/{number}-<name>.json{RESET}\n")

    while True:
        short_name = prompter.ask(
            "Short name for the filename",
            help_text="kebab-case, e.g. goose-ptv3-full-run")
        if NAME_RE.match(short_name):
            break
        prompter.say(f"  {RED}Lower-case letters, digits and single hyphens "
                     f"only.{RESET}")

    record: dict[str, Any] = {
        "schema_version": vr.SCHEMA_VERSION,
        "id": f"{number}-{short_name}",
        "title": prompter.ask("Title", help_text="One line a human can scan."),
        "owner": prompter.ask("Owner"),
        "date": prompter.ask("Date", default=today),
    }
    record["status"] = prompter.choose("Status", vr.STATUSES, default="success")

    prompter.say(f"\n{BOLD}Identification{RESET} {DIM}— D-01. These three say what "
                 f"the number is *of*. Never blank.{RESET}")
    record["dataset"] = prompter.ask(
        "Dataset", help_text="Name AND version, e.g. 'GOOSE 3D val (2024-07 archive)'")
    record["sensor_configuration"] = prompter.ask(
        "Sensor configuration",
        help_text="Sensors this run actually used, not what the vehicle carries.")
    record["annotation_schema"] = prompter.ask(
        "Annotation schema", help_text="Label set, format, version.")

    prompter.say(f"\n{BOLD}What was run{RESET}")
    record["task_type"] = prompter.choose("Task type", vr.TASK_TYPES)
    record["modality"] = prompter.choose("Modality", vr.MODALITIES)
    record["split"] = prompter.ask("Split", help_text="Which split and subset.")

    if record["task_type"] not in vr.NON_MODEL_TASKS:
        record["model"] = prompter.ask("Model", help_text="Name and version or commit.")
    conditions = prompter.ask("Conditions", required=False,
                              help_text="Weather, scenario, time of day, where it "
                                        "matters. Blank to skip.")
    if conditions:
        record["conditions"] = conditions

    prompter.say(f"\n{BOLD}Environment{RESET}")
    record["environment"] = {
        "os": prompter.ask("OS"),
        "hardware": prompter.ask("Hardware"),
        "python": prompter.ask("Python"),
        "packages": {},
    }
    prompter.say(f"  {DIM}Key packages and versions. Blank name ends the "
                 f"list.{RESET}")
    while True:
        package = prompter.ask("  package", required=False)
        if not package:
            break
        record["environment"]["packages"][package] = prompter.ask("  version")

    prompter.say(f"\n{BOLD}Reproduction{RESET}")
    record["commands"] = prompter.ask_list(
        "command", help_text="The exact commands, in order, sufficient to repeat this.")

    prompter.say(f"\n{BOLD}Numbers{RESET}")
    metrics = _ask_named_values(prompter, "metrics", vr.defined_metrics())
    if metrics:
        record["metrics"] = metrics
    measurements = _ask_named_values(prompter, "measurements", None)
    if measurements:
        record["measurements"] = measurements

    prompter.say(f"\n{BOLD}Provenance{RESET}")
    hours = prompter.ask("Hours spent", required=False)
    if hours:
        try:
            record["hours_spent"] = float(hours) if "." in hours else int(hours)
        except ValueError:
            prompter.say(f"  {YELLOW}Not a number — omitted.{RESET}")
    record["evidence"] = prompter.ask_list(
        "evidence", help_text="Repo-relative paths to figures, logs, experiment-log "
                              "entries.")
    notes = prompter.ask("Notes", required=False,
                         help_text="Anything a reader needs in order not to over-read "
                                   "the number.")
    if notes:
        record["notes"] = notes

    if record["status"] != "success":
        prompter.say(f"\n{BOLD}Because this did not succeed{RESET} {DIM}— DZ-3. A "
                     f"failure record without these is a shrug, not a result.{RESET}")
        record["error"] = prompter.ask(
            "Error", help_text="The EXACT error text, copy-pasted. Paraphrased "
                               "errors are unsearchable.")
        record["attempted_fixes"] = prompter.ask_list(
            "attempted fix", help_text="What was tried, in order, and what happened "
                                       "after each.")
        record["blocker"] = prompter.ask("Blocker",
                                         help_text="The one thing that stopped it.")
        record["recommendation"] = prompter.ask(
            "Recommendation", help_text="Retry with what, change to what, or stop.")

    return short_name, record


def write_and_validate(record: dict[str, Any], path: pathlib.Path
                       ) -> tuple[bool, list[str], list[str]]:
    """Write the record, then validate it. Removes the file if it fails.

    Written first and validated on disk rather than in memory, so what gets
    checked is exactly the bytes a reviewer will read — including anything JSON
    serialisation itself changes.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # A per-number exclusive reservation covers differently named records too.
    # ponytail: local writers only; cross-branch collisions require merge validation.
    reservation = path.parent / f".{path.stem[:4]}.lock"
    try:
        lock = reservation.open("x", encoding="utf-8")
    except FileExistsError:
        return False, ["Sequence is reserved by another writer; retry. If its "
                       "process crashed, remove the stale lock after checking."], []
    try:
        with lock:
            matches = list(path.parent.glob(f"{path.stem[:4]}-*.json"))
            if matches:
                return False, [f"Sequence already used by {matches[0].name}; retry."], []
            try:
                output = path.open("x", encoding="utf-8")
            except FileExistsError:
                return False, [f"{path.name} already exists; nothing overwritten."], []
            try:
                with output:
                    output.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
                errors, warnings = vr.check(path, vr.defined_metrics())
                if errors:
                    path.unlink()
                    return False, errors, warnings
                return True, [], warnings
            except BaseException:
                path.unlink(missing_ok=True)
                raise
    finally:
        reservation.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-dir", type=pathlib.Path, default=RECORDS,
                        help="where records live (default: results/records)")
    args = parser.parse_args(argv)

    prompter = Prompter()
    number = next_sequence_number(args.records_dir)

    try:
        short_name, record = build_record(prompter, number=number)
    except (KeyboardInterrupt, EOFError):
        prompter.say(f"\n{YELLOW}Cancelled. Nothing written.{RESET}")
        return 130

    # A second writer may have finished while the user was answering prompts.
    number = next_sequence_number(args.records_dir)
    record["id"] = f"{number}-{short_name}"
    path = args.records_dir / f"{number}-{short_name}.json"
    if path.exists():
        prompter.say(f"{RED}{path} already exists. Nothing written.{RESET}")
        return 1

    ok, errors, warnings = write_and_validate(record, path)
    for warning in warnings:
        prompter.say(f"{YELLOW}warning{RESET}  {warning}")
    if not ok:
        prompter.say(f"\n{RED}Not written — the record would not validate:{RESET}")
        for error in errors:
            prompter.say(f"  {error}")
        prompter.say("\nNothing was saved. Fix the answers above and run again.")
        return 1

    prompter.say(f"\n{GREEN}Written{RESET}  {path}")
    prompter.say(f"\nNext: open a PR. CI runs the validators; you can run them now "
                 f"with\n  python scripts/validate_result.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
