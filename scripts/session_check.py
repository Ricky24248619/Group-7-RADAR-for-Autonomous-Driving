#!/usr/bin/env python3
"""Pre-flight check before starting or finishing a work session on the GOOSE sprint.

Two people work this repo from different machines with different AI assistants. This
script is the guard that keeps them from colliding. Run it at the START of every
session and again BEFORE every commit.

    python scripts/session_check.py --who damien
    python scripts/session_check.py --who ricky

It checks, in order:
  1. You are on your own branch, not main and not the other person's
  2. Your branch is up to date with origin/main (and tells you how to fix it)
  3. Every file you have touched belongs to you
  4. No dataset files have crept into the repo

Exit code 0 means clear to work. Non-zero means read the output and fix it first.
Nothing here modifies the repository — it only reports.
"""

import argparse
import fnmatch
import pathlib
import subprocess
import sys

# --- Ownership. Agreed in WORKPLAN.md §6. Do not edit without the other person. ----

OWNERSHIP = {
    "damien": [
        "scripts/goose_render_frame.py",
        "scripts/goose_traversability.py",
        "scripts/goose_contact_sheet.py",
        "docs/dataset-surveys/goose.md",
        "docs/evidence/*",
        "GOOSE - Ricky+Damien/findings-damien.md",
    ],
    "ricky": [
        "scripts/goose_stats.py",
        "GOOSE - Ricky+Damien/traversability_map.csv",
        "GOOSE - Ricky+Damien/dataset-statistics.md",
        "experiment-log/*",
        "docs/metrics-definitions.md",
    ],
}

# Changing these needs both people to agree — they are the contract, not the work.
FROZEN = [
    "GOOSE - Ricky+Damien/WORKPLAN.md",
    "GOOSE - Ricky+Damien/SUMMARY.md",
    "GOOSE - Ricky+Damien/GOOSE-CONTEXT.md",
    "scripts/session_check.py",
    "scripts/validate_traversability_map.py",
    ".gitignore",
    ".gitattributes",
]

BRANCH_PREFIX = "goose/{who}-w"          # goose/damien-w1, goose/ricky-w2, ...
DATASET_SUFFIXES = (".bin", ".label", ".zip", ".pcd")

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout.strip()


def owns(who, path):
    for pattern in OWNERSHIP[who]:
        if fnmatch.fnmatch(path, pattern) or path == pattern:
            return True
        if pattern.endswith("/*") and path.startswith(pattern[:-1]):
            return True
    return False


def owner_of(path):
    for who in OWNERSHIP:
        if owns(who, path):
            return who
    if path in FROZEN:
        return "FROZEN"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--who", required=True, choices=sorted(OWNERSHIP),
                    help="Which of you is running this")
    args = ap.parse_args()
    who = args.who
    problems, warnings = [], []

    print(f"\n{DIM}{'=' * 66}{RESET}")
    print(f"  Session check — {who}")
    print(f"{DIM}{'=' * 66}{RESET}\n")

    # 1. Branch ------------------------------------------------------------------
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    expected = BRANCH_PREFIX.format(who=who)
    if branch == "main":
        problems.append(
            f"You are on main. Never work on main.\n"
            f"      git checkout -b {expected}1 origin/main")
    elif not branch.startswith(expected):
        problems.append(
            f"Branch '{branch}' is not yours. Yours start with '{expected}'.\n"
            f"      If this is {('ricky' if who == 'damien' else 'damien')}'s branch, "
            f"switch off it now.")
    else:
        print(f"  {GREEN}OK{RESET}   on your own branch: {branch}")

    # 2. Up to date with main ----------------------------------------------------
    print(f"  {DIM}..{RESET}   fetching origin")
    git("fetch", "origin", "--prune", check=False)

    behind = git("rev-list", "--count", "HEAD..origin/main", check=False)
    if behind and behind != "0":
        warnings.append(
            f"origin/main has {behind} commit(s) you do not have.\n"
            f"      Rebase before you start, or you will conflict later:\n"
            f"      git pull --rebase origin main")
    else:
        print(f"  {GREEN}OK{RESET}   up to date with origin/main")

    # Has the other person landed something on main? Useful signal, not a problem.
    other = "ricky" if who == "damien" else "damien"
    recent = git("log", "--oneline", "-5", "origin/main", check=False)
    if recent:
        print(f"\n  {DIM}Last commits on origin/main:{RESET}")
        for line in recent.splitlines():
            print(f"    {DIM}{line}{RESET}")

    # 3. Ownership of everything touched -----------------------------------------
    changed = set()
    for cmd in (["diff", "--name-only"],                 # unstaged
                ["diff", "--name-only", "--cached"],     # staged
                ["diff", "--name-only", "origin/main...HEAD"]):   # committed on branch
        out = git(*cmd, check=False)
        changed.update(f for f in out.splitlines() if f)

    untracked = [f for f in git("ls-files", "--others", "--exclude-standard",
                                check=False).splitlines() if f]
    changed.update(untracked)

    if changed:
        print(f"\n  Files you have touched ({len(changed)}):")
        for path in sorted(changed):
            o = owner_of(path)
            if o == who:
                print(f"    {GREEN}yours{RESET}    {path}")
            elif o == "FROZEN":
                warnings.append(
                    f"'{path}' is a shared/frozen file.\n"
                    f"      Only change it with {other}'s agreement, at a checkpoint.")
                print(f"    {YELLOW}FROZEN{RESET}   {path}")
            elif o is None:
                print(f"    {YELLOW}new{RESET}      {path}  "
                      f"{DIM}(not in the ownership table — fine if it's genuinely new){RESET}")
            else:
                problems.append(
                    f"'{path}' belongs to {o}, not you. Revert it and ask them:\n"
                    f"      git checkout origin/main -- \"{path}\"")
                print(f"    {RED}THEIRS{RESET}   {path}")
    else:
        print(f"\n  {DIM}No local changes yet.{RESET}")

    # 4. Dataset files must never enter the repo ---------------------------------
    strays = [f for f in changed if f.lower().endswith(DATASET_SUFFIXES)]
    if strays:
        problems.append(
            "Dataset files are about to enter the repo. They must not:\n      "
            + "\n      ".join(strays))

    # --- Verdict ----------------------------------------------------------------
    print()
    for w in warnings:
        print(f"  {YELLOW}WARN{RESET}  {w}")
    for p in problems:
        print(f"  {RED}STOP{RESET}  {p}")

    print(f"\n{DIM}{'=' * 66}{RESET}")
    if problems:
        print(f"  {RED}NOT CLEAR TO WORK{RESET} — fix the STOP items above.\n")
        return 1
    if warnings:
        print(f"  {YELLOW}CLEAR, WITH WARNINGS{RESET} — read them before continuing.\n")
        return 0
    print(f"  {GREEN}CLEAR TO WORK{RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
