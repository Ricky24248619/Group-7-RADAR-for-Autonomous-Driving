#!/usr/bin/env python3
"""Validate traversability_map.csv against the interface contract in WORKPLAN.md §9.

This file is the one hand-off between Ricky and Damien: Ricky authors it, Damien's
renderer consumes it. If it is malformed the failure surfaces in Damien's code, days
later, looking like a rendering bug. So both sides run this instead.

    Ricky, before handing over:  python scripts/validate_traversability_map.py
    Damien, on receipt:          python scripts/validate_traversability_map.py

Exit code 0 means the contract holds.
"""

import argparse
import csv
import pathlib
import sys

REQUIRED_COLUMNS = ["label_key", "class_name", "traversability_id",
                    "traversability_name", "rationale"]

# Agreed scheme, borrowed from STONE so our vocabulary matches the off-road literature.
CLASSES = {
    0: "Free",
    1: "Traversable",
    2: "Potentially Traversable",
    3: "Non-Traversable",
}

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MAP = REPO / "GOOSE - Ricky+Damien" / "traversability_map.csv"


def load_reference(dataset_root):
    """The 64 official GOOSE classes, from the mapping shipped inside the split."""
    ref = pathlib.Path(dataset_root).expanduser() / "goose_label_mapping.csv"
    if not ref.is_file():
        return None
    with ref.open(newline="", encoding="utf-8-sig") as fh:
        return {int(r["label_key"]): r["class_name"] for r in csv.DictReader(fh)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", default=str(DEFAULT_MAP))
    ap.add_argument("--dataset-root", default=None,
                    help="Extracted split, to cross-check class ids and names")
    args = ap.parse_args()

    path = pathlib.Path(args.map)
    if not path.is_file():
        sys.exit(f"Not found: {path}")

    errors, warnings = [], []

    # utf-8-sig tolerates the byte-order mark Excel writes on Windows.
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"Missing required column(s): {', '.join(missing)}\n"
                     f"Found: {reader.fieldnames}")
        rows = list(reader)

    print(f"Reading {path.name} — {len(rows)} rows\n")

    seen = {}
    for i, row in enumerate(rows, start=2):          # row 1 is the header
        key_raw = (row.get("label_key") or "").strip()
        try:
            key = int(key_raw)
        except ValueError:
            errors.append(f"row {i}: label_key '{key_raw}' is not an integer")
            continue

        if key in seen:
            errors.append(f"row {i}: label_key {key} already defined on row {seen[key]}")
        seen[key] = i

        tid_raw = (row.get("traversability_id") or "").strip()
        try:
            tid = int(tid_raw)
        except ValueError:
            errors.append(f"row {i} (key {key}): traversability_id '{tid_raw}' "
                          f"is not an integer")
            continue

        if tid not in CLASSES:
            errors.append(f"row {i} (key {key}): traversability_id {tid} is not 0-3")
        else:
            name = (row.get("traversability_name") or "").strip()
            if name != CLASSES[tid]:
                errors.append(f"row {i} (key {key}): id {tid} should be "
                              f"'{CLASSES[tid]}', found '{name}'")

        if not (row.get("rationale") or "").strip():
            errors.append(f"row {i} (key {key}, {row.get('class_name')}): "
                          f"rationale is blank — every row needs one")

    # Cross-check against the real GOOSE class list where we can.
    if args.dataset_root:
        ref = load_reference(args.dataset_root)
        if ref is None:
            warnings.append(f"No goose_label_mapping.csv under {args.dataset_root} — "
                            f"skipped the class cross-check")
        else:
            for key in sorted(set(ref) - set(seen)):
                errors.append(f"missing GOOSE class {key} ({ref[key]}) — "
                              f"every class needs an assignment")
            for key in sorted(set(seen) - set(ref)):
                errors.append(f"label_key {key} is not a GOOSE class")
            for row in rows:
                try:
                    k = int(row["label_key"])
                except ValueError:
                    continue
                if k in ref and row["class_name"].strip() != ref[k]:
                    warnings.append(f"key {k}: class_name '{row['class_name']}' "
                                    f"differs from GOOSE's '{ref[k]}'")
    else:
        warnings.append("Run with --dataset-root to check all 64 classes are covered")

    if len(rows) != 64:
        (errors if args.dataset_root else warnings).append(
            f"expected 64 rows, found {len(rows)}")

    # Distribution is not a pass/fail, but a wildly skewed mapping is worth seeing.
    counts = {}
    for row in rows:
        try:
            counts[int(row["traversability_id"])] = \
                counts.get(int(row["traversability_id"]), 0) + 1
        except (ValueError, KeyError):
            pass
    if counts:
        print("Assignment distribution")
        for tid in sorted(CLASSES):
            n = counts.get(tid, 0)
            bar = "#" * n
            print(f"  {tid}  {CLASSES[tid]:<24} {n:>3}  {bar}")
            if n == 0:
                warnings.append(f"no class assigned to '{CLASSES[tid]}' — "
                                f"intentional, or an oversight?")
        print()

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")

    print()
    if errors:
        print(f"INVALID — {len(errors)} error(s). Do not hand this over yet.")
        return 1
    print("VALID — contract holds. Safe to hand over.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
