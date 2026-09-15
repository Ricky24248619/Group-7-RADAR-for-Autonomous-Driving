#!/usr/bin/env python3
"""Check experiment-log locations, unique numbers and matching title IDs.

    python scripts/validate_experiment_logs.py

This checks log identity only, not experiment completion or scientific validity.
"""

import argparse
import pathlib
import re


LOGS = pathlib.Path(__file__).resolve().parents[1] / "experiment-log"


def check(directory: pathlib.Path) -> list[str]:
    if not directory.is_dir():
        return [f"Experiment-log directory not found: {directory}"]
    errors = []
    numbers = {}
    for path in sorted(directory.rglob("*.md")):
        if path.name == "README.md" and path.parent == directory:
            continue
        relative = path.relative_to(directory).as_posix()
        if path.parent != directory:
            errors.append(f"{relative}: place entries directly in experiment-log/")
        match = re.fullmatch(r"([0-9]{4})-.+\.md", path.name)
        if not match:
            errors.append(f"{relative}: expected NNNN-short-name.md")
            continue
        number = match[1]
        if number in numbers:
            errors.append(f"Duplicate EXP-{number}: {numbers[number]} and {relative}")
        numbers[number] = relative
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except (OSError, UnicodeError) as error:
            errors.append(f"{relative}: cannot read UTF-8 text: {error}")
            continue
        title = next((line.strip() for line in lines if line.strip()), "")
        if not re.match(rf"^#{{1,6}}\s+EXP-{number}\b", title):
            errors.append(f"{relative}: first heading must contain EXP-{number}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=pathlib.Path, default=LOGS)
    errors = check(parser.parse_args().directory)
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print("PASS: experiment-log locations, sequence numbers and title IDs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
