# P-5 reproduction run: 29 September 2026 (substitute, not outside-team)

**Read this first.** The team decided on 29 September that no reproducer outside the
unit will be found before the 12 October stop, and closed B5 with this substitute run.
The run is a cold, scripted walkthrough of
[`outside-reproduction-protocol.md`](../outside-reproduction-protocol.md) in a fresh
clone, performed by an AI coding assistant (Claude Code) at Damien's request. **It does not
satisfy P-5.** P-5 asks for *a person outside the team*. This is neither a person nor
independent of the team. P-5 therefore stays **partly met** and goes to handover as an
open item. What this run does establish is that the instructions work as written on
a clean checkout, and where they would confuse a real outsider.

Reproducer: Claude Code (AI assistant), run on Damien's behalf. **Not outside the team**
Relationship to the team: tool used by a team member
Machine and OS: MacBook, macOS 15 (Darwin 24.6.0), Apple Silicon
Python version: 3.11.15 (Homebrew)
Commit: `ab595bd` (fresh `git clone` of `main`, 29 Sep 14:25 AWST)
Total time taken: under 1 minute of machine time (clone 18 s, venv + install 7 s, steps 1–3 ~6 s)
Help given during the run: none. The protocol was followed as written

## Step 1: project checks
Outcome: **pass**
Exact output:
```
All 32 record(s) valid.
PASS: experiment-log locations, sequence numbers and title IDs.
ERROR  <clone>/docs/metrics-definitions.md not found or unreadable — metric validation cannot run
OK (skipped=10)
```
The `ERROR` line is printed **during the unit tests**, not by the validator run. It comes
from a test that deliberately exercises the missing-file path in
`scripts/validate_result.py`, and the file does exist. The 10 skips are tests marked as
needing optional SciPy or TruckScenes devkit extras, which `requirements-ci.txt` does not
install. Both are expected, but **the protocol said only "tests OK"**, and a real outsider
seeing red `ERROR` text would reasonably stop and report a failure.

## Step 2: regenerate the figure
Outcome: **pass**
```
plotted 110 CSV row(s) from range-bands.csv
Per-modality sample counts are in the captions; no dataset was read
```

## Step 3: byte comparison
Identical: **yes**. `cmp` printed nothing for both `range_bands_counts.png` and
`range_bands_share.png`.

## Step 4: what they thought the figure measures
**Not recorded.** This reproducer had already read the project, so any answer would be
informed, not cold, and would be worthless as P-6 evidence. Left blank rather than filled.

## Where they got stuck
Nowhere. The only likely snag for a human is the Step 1 `ERROR` line described above.

## What we changed as a result
`outside-reproduction-protocol.md` Step 1 now says what the expected output looks like,
including the harmless `ERROR` line and the skip count, so a real reproducer does not
stop there. **That fix is untested by anyone outside the team.**
