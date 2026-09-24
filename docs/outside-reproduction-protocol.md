# Outside-team reproduction — P-5

**Story B5 · owner Damien Zhang · 24 September 2026**

P-5: *"A person outside the team can clone the repository and reproduce a documented
result from a clean machine."* Ricky reproducing Damien's macOS workflow on Windows is
useful cross-platform evidence, but both are team members, so this stays **outstanding**
until an outsider runs it.

This page is the whole task. Hand it to someone who is not in CITS3200 Group 7, then
record what happens.

---

## Why this target was chosen

It needs **no dataset**. The datasets are hundreds of gigabytes, licence-gated, and
two of them cannot legally be handed to an outsider. A reproduction that requires one
is a reproduction nobody will ever run.

The figures in `docs/evidence/truckscenes/` are generated from a **committed CSV**, and
`scripts/plot_truckscenes_range_bands.py` never opens the dataset. So the output is
byte-comparable: either the regenerated PNG matches the committed one or it does not,
and there is nothing to argue about.

Verified before writing this: regenerating both figures in a clean Python 3.11
environment produced files **byte-identical** to the committed ones.

---

## Instructions for the reproducer

*Everything below is self-contained. You need Python 3.11 and git. Roughly 15 minutes.
You do not need to understand the project.*

**Please do not ask us for help while you work.** Where you get stuck is the
measurement. If you are stuck for more than five minutes, write down what you tried and
stop — that is a complete and useful result.

```bash
git clone https://github.com/Ricky24248619/Group-7-RADAR-for-Autonomous-Driving.git
cd Group-7-RADAR-for-Autonomous-Driving

python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-ci.txt
```

**Step 1 — do the project's own checks pass?**

```bash
python scripts/validate_result.py
python scripts/validate_experiment_logs.py
python -m unittest discover -s tests
```

Expected: all records valid, logs PASS, tests OK.

**Step 2 — regenerate a published figure from committed data.**

```bash
python scripts/plot_truckscenes_range_bands.py --output-dir /tmp/repro
```

**Step 3 — does it match what is published?**

```bash
# macOS/Linux
cmp /tmp/repro/range_bands_counts.png docs/evidence/truckscenes/range_bands_counts.png
cmp /tmp/repro/range_bands_share.png  docs/evidence/truckscenes/range_bands_share.png
```

```powershell
# Windows
Get-FileHash /tmp/repro/range_bands_counts.png, docs/evidence/truckscenes/range_bands_counts.png
```

No output from `cmp` means identical.

**Step 4 — open `/tmp/repro/range_bands_counts.png` and answer one question in your own
words:** what do you think this figure is measuring?

---

## Recording form

Copy into `docs/evidence/p5-reproduction-<date>.md`, fill it in, commit it.
**A failed reproduction is a complete result** and is recorded as one — do not retry it
into a pass, and do not tidy up what they wrote.

```markdown
# P-5 outside-team reproduction — <date>

Reproducer: <name or role, e.g. "final-year CS student, not in this unit">
Relationship to the team: <must be outside Group 7>
Machine and OS:
Python version:
Total time taken:
Help given during the run: <none / describe exactly — any help weakens the result>

## Step 1 — project checks
Outcome: pass / fail
Exact output or error:

## Step 2 — regenerate the figure
Outcome: pass / fail
Exact output or error:

## Step 3 — byte comparison
Identical: yes / no
If no, what differed:

## Step 4 — what they thought the figure measures
Verbatim, unedited:

## Where they got stuck
Step, elapsed time, exact error text:

## What we changed as a result
<Documentation fixes this produced. If nothing, say so.>
```

---

## How to read the outcome

**They finish with identical bytes** — P-5 is met for this result. Say exactly that: one
documented result reproduced by one outsider on one machine. It does not mean the whole
repository reproduces.

**They get stuck** — that is the finding, and arguably the more useful one. Record the
step and the exact error, fix the documentation, and note that the fix is untested until
someone else runs it cold.

**The bytes differ** — record it rather than explaining it away. A matplotlib or
fontconfig difference is a legitimate cause, but it means the "regenerate and diff"
reproducibility claim needs qualifying, and that qualification belongs in
`TruckScenes - Fatima/RANGE-BANDS.md`.

**Step 4 is a bonus P-6 data point**, not a substitute for the cold read — see
[`cold-read-protocol.md`](cold-read-protocol.md).
