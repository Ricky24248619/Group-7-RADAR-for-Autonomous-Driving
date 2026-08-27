# GOOSE Workplan — Ricky & Damien

**Fortnight:** 27 August – 10 September 2026 · **Sprint:** 2 · **Workstream:** WS2
**Owners:** Damien Zhang (DZ) · Ricky Yuen (RY)
**Repo:** `Ricky24248619/Group-7-RADAR-for-Autonomous-Driving`

---

## 0. How to use this file

This plan is written to be executed by a person working with an AI assistant. It is
**self-contained**: an assistant reading only this file, with no memory of prior
conversations, should be able to do the work.

- Tasks are `D1…D5` (Damien) and `R1…R5` (Ricky). **Do only your own tasks.**
- Each task states **Goal / Inputs / Steps / Done when / Output**. "Done when" is
  written as something checkable, not a feeling.
- File ownership is **disjoint by design** — see §6. Two people running AI agents in
  the same repo will produce merge conflicts unless nobody edits anyone else's files.
  If a task seems to need you to edit a file you do not own, stop and ask the owner.
- If a step fails, that is **data, not defeat**. Record it (§8) and continue. The
  client has stated explicitly that negative results count.

### Rules for AI assistants working on this plan

1. **Never commit dataset files.** The dataset lives at `$DATA` (§2.0), outside the
   repo on both platforms. Nothing under that path is ever added to git. If
   `git status` shows `.bin`, `.label` or `.zip` files from the dataset, stop.
2. **Never push to `main`.** Work on a branch, open a PR. `main` requires review.
3. **Never edit files owned by the other person** (§6). This is enforced by
   `scripts/session_check.py` — run it at the start of every session and before every
   commit, and treat a non-zero exit as a hard stop (§7).
4. **Do not install packages globally.** Use the project venv — `$PY` in §2.0.
5. **Do not attempt to run the Pointcept / PTv3 baselines.** They require CUDA.
   Damien's machine is Apple Silicon and cannot. Ricky's Windows machine *might* — see
   §2.8 — but that is a team decision, not something to start mid-task. Out of scope
   for this fortnight either way (risk R-08).
6. **This is a cross-platform pair.** Damien is on macOS, Ricky on Windows. Where a
   step differs, both are given. Use `$PY` and `$DATA` from §2.0 rather than hardcoding
   paths. PowerShell needs `& $PY ...` to invoke a command held in a variable.
7. **Any script either of us writes must run on both.** Use `pathlib`, not string paths.
   Never hardcode `/` separators, `/tmp`, or `C:\`. Write files with an explicit
   `encoding="utf-8"`.
8. **Pin versions** in any install command you write into documentation.
9. **State uncertainty.** If a number is measured, say so. If it is from a paper, cite
   it. Do not present an estimate as a measurement.

---

## 1. What this fortnight is for

Two weeks of understanding GOOSE well enough to say what it can and cannot do for this
project — and producing one figure that shows the client their own question answered
with their own preferred dataset.

Background on why GOOSE matters and how it fits the project is in
[`GOOSE-CONTEXT.md`](GOOSE-CONTEXT.md). **Read that first if you have not.**

Three objectives, from the agreed scope:

| # | Objective | Tasks |
|---|---|---|
| 1 | **Understand the data** — look at it, measure it, describe it | D1, D2, R1, R2 |
| 2 | **Build the drivable / not-drivable view** — the client's actual question, rendered | R3, D3, D4 |
| 3 | **Write up what we learned** — survey §7, limitations, experiment logs | D5, R4, R5 |

**Explicitly deferred:** chasing the GOOSE radar. The maintainers have confirmed the
downloadable ROS bags carry a reduced sensor set, and there is no convenient download
for the full raw data. Since the radar is not obtainable, the question of whether the
Smartmicro units are 4D imaging has no practical effect on this fortnight's work.
*Recorded as a deliberate deferral, not an oversight — it remains an open item under
risk R-24 and in `decision-log.md` D-05.*

---

## 2. Environment setup

**This pair works across two operating systems.** Damien is on macOS (Apple Silicon),
Ricky is on Windows. Every command below is given for both.

### 2.0 Shell conventions — set these once per session

The rest of this document refers to `$PY` (the venv's Python) and `$DATA` (the dataset
root) rather than repeating platform-specific paths. Set them at the start of every
session, then every later command works unchanged on both machines.

**macOS / Linux — bash or zsh**
```bash
PY=~/.venvs/radar/bin/python
DATA=~/datasets/goose/goose_3d_val
```

**Windows — PowerShell** (not Command Prompt)
```powershell
$PY   = "$env:USERPROFILE\.venvs\radar\Scripts\python.exe"
$DATA = "C:\goose\goose_3d_val"
```

> **Why call the exe directly instead of activating the venv?** On Windows,
> `Activate.ps1` is blocked by the default script execution policy on many managed
> machines. Calling `python.exe` by full path sidesteps that entirely and never needs
> an administrator. Use `& $PY ...` — the `&` is PowerShell's call operator and is
> required when the command is held in a variable.

> **Why is the Windows data path `C:\goose` and not under your user folder?** Windows
> has a 260-character path limit by default. GOOSE filenames are long — e.g.
> `2022-08-30_siegertsbrunn_feldwege__0123_1661856789012345678_goose.label` is 71
> characters before any directories. Keeping the dataset near the drive root leaves
> headroom. If you would rather put it elsewhere, that is fine, but keep the path short.

### 2.1 Python 3.11

The devkit requires Python `>=3.8,<3.12`, so 3.11 it is. Newer versions will fail.

**macOS**
```bash
brew install python@3.11
```

**Windows**
```powershell
winget install Python.Python.3.11
py -3.11 --version        # expect Python 3.11.x
```
Or the installer from [python.org](https://www.python.org/downloads/). Tick **"Add
python.exe to PATH"**. Avoid the Microsoft Store build — it sandboxes file access in
ways that confuse venvs.

### 2.2 Create the venv and install packages

**macOS**
```bash
mkdir -p ~/.venvs
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv ~/.venvs/radar
PY=~/.venvs/radar/bin/python
$PY -m pip install --upgrade pip
$PY -m pip install numpy matplotlib pyyaml
```

**Windows**
```powershell
py -3.11 -m venv "$env:USERPROFILE\.venvs\radar"
$PY = "$env:USERPROFILE\.venvs\radar\Scripts\python.exe"
& $PY -m pip install --upgrade pip
& $PY -m pip install numpy matplotlib pyyaml
```

Those three packages are all the tasks in this plan need. **Optional extras**, only if
you want the devkit's interactive viewer (`vispy`, `PyQt5`) or to inspect ROS bags
(`rosbags`) — neither is required here:

```
vispy==0.16.2  PyQt5  rosbags
```

> The venv lives **outside** the project folder on both platforms. On macOS this is
> because the project path contains spaces, which breaks console-script shebangs (see
> `SETUP.md`). On Windows it keeps paths short. Same location, different reason.

### 2.3 Get the data — 3.3 GB download, 3.3 GB extracted

**macOS**
```bash
mkdir -p ~/datasets/goose/zips ~/datasets/goose/goose_3d_val
curl -# -L -o ~/datasets/goose/zips/goose_3d_val.zip \
  https://goose-dataset.de/storage/goose_3d_val.zip
cd ~/datasets/goose/goose_3d_val
unzip -q ~/datasets/goose/zips/goose_3d_val.zip
```

**Windows**
```powershell
New-Item -ItemType Directory -Force -Path C:\goose\zips, C:\goose\goose_3d_val | Out-Null

curl.exe -# -L -o C:\goose\zips\goose_3d_val.zip `
  https://goose-dataset.de/storage/goose_3d_val.zip

tar -xf C:\goose\zips\goose_3d_val.zip -C C:\goose\goose_3d_val
```

> ⚠️ **Two Windows traps here, both of which will waste your afternoon.**
>
> 1. **`curl` in PowerShell is an alias for `Invoke-WebRequest`**, which is a different
>    program with different flags. It will fail or silently produce a broken file. You
>    must write **`curl.exe`** with the extension.
> 2. **Use `tar`, not `Expand-Archive`.** `tar` ships with Windows 10 and 11 and
>    extracts this archive in a couple of minutes. `Expand-Archive` is pure PowerShell
>    and can take the better part of an hour on a 3.3 GB zip with 1,925 files.

### 2.4 Verify

**macOS**
```bash
find $DATA/lidar -name '*.bin' | wc -l       # expect 961
find $DATA/labels -name '*.label' | wc -l    # expect 961
ls $DATA/lidar/val/                          # expect 8 scenario directories
```

**Windows**
```powershell
(Get-ChildItem "$DATA\lidar"   -Recurse -Filter *.bin).Count      # expect 961
(Get-ChildItem "$DATA\labels" -Recurse -Filter *.label).Count     # expect 961
Get-ChildItem "$DATA\lidar\val" -Directory | Select-Object -ExpandProperty Name
```

### 2.5 Clone the devkit — optional

```
git clone https://github.com/FraunhoferIOSB/goose_dataset.git
```

Run from the repo root. Already in `.gitignore`. **Not required for any task below** —
it is only needed for the official interactive viewer.

### 2.6 Smoke test

Run from the repo root.

**macOS**
```bash
$PY scripts/goose_render_frame.py --root $DATA --index 0 --out /tmp/smoke.png
```

**Windows**
```powershell
& $PY scripts\goose_render_frame.py --root $DATA --index 0 --out $env:TEMP\smoke.png
```

Expect `Found 961 annotated frames.`, a class distribution table, and a PNG written.
**If this works, your environment is correct.** Open the PNG and check it looks like
the committed examples in `docs/evidence/`.

### 2.7 Git line endings — Windows only, do this once

```powershell
git config --global core.autocrlf true
```

The repo carries a `.gitattributes` that normalises text files, but setting this stops
your editor turning whole files into one-line diffs. It matters here because Ricky
authors `traversability_map.csv` and Damien's code reads it — a CRLF surprise in a
shared data file is an annoying thing to debug.

### 2.8 Check for an NVIDIA GPU — Windows only, 30 seconds

```powershell
nvidia-smi
```

**If this prints a table showing a GPU, tell the team immediately.** Risk **R-08** in
the register says no team member has a discrete NVIDIA GPU, and that has never actually
been audited. Damien's machine is Apple Silicon and definitively cannot run CUDA. If
Ricky's Windows machine has an NVIDIA card with enough VRAM, then the Pointcept / PTv3
baselines — currently listed as out of scope in §11 — may become runnable locally, and
several downstream assumptions about needing Kaya or Colab change.

If it prints "not recognized" or nothing, that confirms R-08 as written. Either answer
is a useful result; record it in the R1 experiment-log entry.

---

## 3. What you are working with

The **validation split** of GOOSE 3D: 961 annotated LiDAR frames across 8 scenarios,
covering summer, winter, rain and sun.

| Scenario | Season / condition |
|---|---|
| `2022-07-22_flight` | Summer |
| `2022-08-30_siegertsbrunn_feldwege` | Summer, field tracks |
| `2022-09-21_garching_uebungsplatz_2` | Autumn, training ground |
| `2022-12-07_aying_hills` | Winter, hills |
| `2023-01-20_aying_mangfall_2` | Winter |
| `2023-03-03_garching_2` | Early spring |
| `2023-05-15_neubiberg_rain` | Spring, **rain** |
| `2023-05-17_neubiberg_sunny` | Spring, **sunny** |

That last pair is unusually valuable — the same location two days apart in different
weather. If you want to say anything about weather sensitivity, that is the comparison.

**Data formats**
- Point clouds: `lidar/val/<scenario>/<name>_vls128.bin` — float32 `[x, y, z, intensity]`
- Labels: `labels/val/<scenario>/<name>_goose.label` — uint32, semantic id in the low
  16 bits, instance id in the high 16 bits
- Class names and colours: `goose_label_mapping.csv` in the split root — 64 classes

---

## 4. Known gotchas — read before you debug

These are already solved in `scripts/goose_render_frame.py`. They are listed so nobody
rediscovers them.

1. **Scans and labels do not share a filename stem.** Scans end `_vls128.bin`, labels
   end `_goose.label`. The join key is everything up to the final underscore.
2. **There are two different taxonomies and mixing them fails silently.** The devkit's
   `common/goose_kitti-visualizer.yaml` is an **8-class** challenge remap with **BGR**
   colours. The downloaded labels are the **full 64-class** set with **hex** colours in
   `goose_label_mapping.csv`. Using the 8-class map on 64-class labels renders most of
   the scene as unknown and raises no error.
3. **The devkit viewer expects `labels_challenge/`; the download ships `labels/`.**
4. **Camera and LiDAR are not reliably time-aligned.** The dataset authors have
   confirmed a bug in their export step: ground-truth masks for the camera image and
   the LiDAR sweep of the same frame **cannot be matched by projection using the
   published extrinsics** ([issue #18](https://github.com/FraunhoferIOSB/goose_dataset/issues/18)).
   **Do not attempt camera↔LiDAR fusion on this data.** Some LiDAR scans are also
   missing sections, and at least one RGB frame is out of sequence.

---

## 5. Schedule

| | Damien | Ricky |
|---|---|---|
| **Week 1** (27 Aug – 3 Sep) | **D1** frame sweep · **D2** refactor renderer for class grouping | **R1** environment + smoke test · **R2** dataset statistics · **R3** traversability mapping |
| **Checkpoint** — 3 Sep | Both: 30-minute sync. R3 must be delivered here; D3 depends on it. | |
| **Week 2** (4 – 10 Sep) | **D3** traversability renderer · **D4** client figure · **D5** survey §7 + limitations | **R4** experiment log entries · **R5** metrics definitions for segmentation |
| **End** — 10 Sep | Joint PR, each reviewing the other's files | |

**The one cross-person dependency is R3 → D3.** Ricky delivers the traversability
mapping by the 3 September checkpoint; Damien implements against it in week 2. Damien's
week-1 tasks are deliberately independent so nobody is blocked.

---

## 6. File ownership — do not cross these lines

Every file either belongs to one of us, is frozen, or is genuinely new. **You may only
create or modify files you own.** This is what makes it safe for two agents to work the
same repository at the same time.

| Owner | Files |
|---|---|
| **Damien** | `scripts/goose_render_frame.py` · `scripts/goose_traversability.py` · `scripts/goose_contact_sheet.py` · `docs/dataset-surveys/goose.md` · `docs/evidence/*` · `GOOSE - Ricky+Damien/findings-damien.md` |
| **Ricky** | `scripts/goose_stats.py` · `GOOSE - Ricky+Damien/traversability_map.csv` · `GOOSE - Ricky+Damien/dataset-statistics.md` · `experiment-log/*` · `docs/metrics-definitions.md` |
| **Frozen** — needs both of us to agree, at a checkpoint | `WORKPLAN.md` · `SUMMARY.md` · `GOOSE-CONTEXT.md` · `scripts/session_check.py` · `scripts/validate_traversability_map.py` · `.gitignore` · `.gitattributes` |

This table is **enforced by a script**, not by memory — see §7. If you need a file you
do not own, stop and message the other person. Do not edit it "just this once".

> Creating a genuinely new file not in this table is fine — the check will flag it as
> `new` rather than blocking you. Mention it at the checkpoint so the table stays true.

---

## 7. Git protocol — follow this exactly

This section exists because we are two people, on two operating systems, running two
different AI assistants against one repository. Conflicts are avoided by procedure, not
by luck.

### 7.1 The branch model — decided, not up for improvisation

**One branch per person per week.** Four branches across the fortnight:

| Week | Damien | Ricky |
|---|---|---|
| 1 (27 Aug – 3 Sep) | `goose/damien-w1` | `goose/ricky-w1` |
| 2 (4 – 10 Sep) | `goose/damien-w2` | `goose/ricky-w2` |

**Neither of us ever commits to `main`.** All work reaches `main` through a pull
request reviewed by the other person.

Why per-week rather than one branch each for the fortnight: the R3 → D3 handoff needs
Ricky's `traversability_map.csv` to reach Damien on **3 September**. Merging week-1
branches at the checkpoint moves it through `main`, which means Damien picks it up with
an ordinary `git pull` instead of cherry-picking from someone else's branch. It also
keeps each PR small enough to actually review.

### 7.2 Start of every session — run this first

```bash
# macOS
$PY scripts/session_check.py --who damien
```
```powershell
# Windows
& $PY scripts\session_check.py --who ricky
```

It fetches from origin and checks four things: that you are on your own branch, that
you are not behind `origin/main`, that every file you have touched belongs to you, and
that no dataset files are about to be committed.

**Exit code 0 means proceed. Non-zero means fix what it prints before doing any work.**
It never modifies the repository — it only reports.

### 7.3 Starting a week

```bash
git checkout main
git pull origin main
git checkout -b goose/<you>-w<n>
```

### 7.4 Resuming work mid-week

```bash
git checkout goose/<you>-w<n>
git fetch origin --prune
git pull --rebase origin main      # pick up anything the other person has merged
```

Rebase, not merge, so the branch stays a clean line of your own commits.

### 7.5 Before every commit

Run the session check again. Then:

```bash
git status                # confirm nothing unexpected is staged
git add <your files>      # name them; never `git add -A` or `git add .`
git commit
```

> `git add -A` is how dataset files and other people's work end up in commits. Name
> what you are adding.

### 7.6 Finishing a week

```bash
git fetch origin
git pull --rebase origin main
$PY scripts/session_check.py --who <you>     # must exit 0
git push -u origin goose/<you>-w<n>
gh pr create --base main --head goose/<you>-w<n>
```

Then request review from the other person. **Merge order at the 3 September checkpoint
is Ricky first, then Damien** — Damien's week-2 work depends on Ricky's CSV being on
`main`.

### 7.7 If you hit a conflict

You should not, given §6. If you do, it means the ownership table was crossed or is
wrong. **Do not resolve it by picking a side.** Stop, message the other person, and fix
the table at a checkpoint. A conflict here is a signal about the plan, not a routine
git chore.

### 7.8 Rules for AI assistants — restated because they matter

- Run `session_check.py` at the start of the session and before every commit. Treat a
  non-zero exit as a hard stop, not a warning.
- Never `git push` to `main`. Never `git push --force` to any shared branch.
- Never `git add -A` / `git add .` — add named paths.
- Never edit a file the ownership table assigns to the other person, even if it looks
  like a one-line fix, and even if the user asks in the moment. Say that it is not ours
  to change and suggest raising it with the owner.
- If `session_check.py` reports `origin/main` has moved, rebase before continuing.

### 7.9 Branch protection — one-time setup, Ricky only

**Damien does not have admin on this repository and cannot do this.** Ricky, please set
it before work starts — it turns the rules above from a convention into something the
platform enforces.

GitHub → repository **Settings** → **Rules** → **Rulesets** → **New branch ruleset**:

| Setting | Value |
|---|---|
| Name | `protect-main` |
| Enforcement status | **Active** |
| Target branches | Include default branch (`main`) |
| Restrict deletions | ✅ |
| Block force pushes | ✅ |
| Require a pull request before merging | ✅ |
| — Required approvals | **1** |
| — Dismiss stale approvals on new commits | ✅ |

Leave "Require status checks" off — we have no CI.

> With one approval required and only two of us, we each become the other's gate. That
> is the intent: it is the independent-reviewer rule from the survey template, enforced
> by the platform rather than remembered.

---

## 8. Recording failures

Anything that does not work gets an entry in `experiment-log/` using
`templates/experiment-log-entry.md`. Include the **exact** error text, copy-pasted, not
paraphrased — paraphrased errors are unsearchable. Ricky owns that directory; if you
are Damien and you hit a failure, write it up in `findings-damien.md` and Ricky will
fold it in at the checkpoint.

---
---

# TASKS — DAMIEN

## D1 — Frame sweep across all 8 scenarios

**Goal.** Build visual intuition for what GOOSE actually contains, and produce a
contact sheet that shows the seasonal and terrain range in one image.

**Inputs.** `$DATA` (§2.0), `scripts/goose_render_frame.py`

**Steps.**
1. Render at least two frames from each of the 8 scenarios. Frame indices are ordered
   by scenario, so sample across the full 0–960 range rather than clustering.
2. Look at them. Note where the class mix changes with season, where the LiDAR looks
   sparse or broken, and any frame that looks wrong.
3. Write observations into `findings-damien.md` — at least one line per scenario.
4. Build a contact sheet: a single image tiling one bird's-eye view per scenario,
   labelled with scenario name and season.

**Done when.** `docs/evidence/goose_contact_sheet.png` exists and shows all 8
scenarios; `findings-damien.md` has an observation per scenario.

**Output.** `docs/evidence/goose_contact_sheet.png` · `findings-damien.md`

> Guidance for the assistant: extend `goose_render_frame.py` with a `--contact-sheet`
> mode, or write a small separate script. Do not duplicate the loading logic — import
> from the existing module.

---

## D2 — Refactor the renderer to support class grouping

**Goal.** Make the renderer able to colour points by an arbitrary grouping of the 64
classes, so D3 can drop in Ricky's traversability mapping without a rewrite.

**Inputs.** `scripts/goose_render_frame.py`

**Steps.**
1. Extract the class-mapping load into a function that accepts either the 64-class
   `goose_label_mapping.csv` **or** a grouping file with columns
   `label_key, class_name, group_name, group_colour` (the format R3 will produce —
   see §9).
2. When a grouping file is supplied, remap each point's class id to its group before
   colouring, and show group names in the legend.
3. Keep the existing 64-class behaviour as the default. **Do not break it** — D1's
   output must still reproduce.

**Done when.** Both of these run and produce different, correct images:
```bash
# macOS
$PY scripts/goose_render_frame.py --root $DATA --index 0 --out /tmp/a.png
$PY scripts/goose_render_frame.py --root $DATA --index 0 --group-map <grouping.csv> --out /tmp/b.png
```
```powershell
# Windows
& $PY scripts\goose_render_frame.py --root $DATA --index 0 --out $env:TEMP\a.png
& $PY scripts\goose_render_frame.py --root $DATA --index 0 --group-map <grouping.csv> --out $env:TEMP\b.png
```

Damien owns this file and works on macOS, but **the script must stay cross-platform** —
Ricky runs it too. Use `pathlib`, never hardcode `/` separators or `/tmp`.

**Output.** Updated `scripts/goose_render_frame.py`

> Until R3 lands, test with a throwaway two-group mapping you write yourself. Delete it
> afterwards — the real one is Ricky's deliverable.

---

## D3 — Traversability renderer *(depends on R3)*

**Goal.** Render GOOSE frames coloured by traversability rather than by material —
the picture that answers *"what can I drive over, what can I crash into."*

**Inputs.** `traversability_map.csv` from R3, refactored renderer from D2

**Steps.**
1. Create `scripts/goose_traversability.py` (or a documented flag on the existing
   script) that renders using Ricky's mapping.
2. Render the same frames as D1, in traversability colours.
3. **Sanity check every one.** Ask of each: does the drivable region look like
   somewhere a vehicle could actually go? If a gravel track reads as non-traversable,
   the mapping is wrong — take it back to Ricky rather than patching it in code.
4. Record any class whose assignment you disagree with in `findings-damien.md`.

**Done when.** Traversability renders exist for all 8 scenarios and the drivable
region is visually coherent in at least 6 of them. Disagreements are recorded, not
silently fixed.

**Output.** `scripts/goose_traversability.py` · `docs/evidence/goose_traversability_*.png`

---

## D4 — The client figure

**Goal.** One image suitable for putting in front of Adrian and Fabian without
narration.

**Steps.**
1. Pick the frame that most clearly shows a drivable route through non-drivable
   surroundings.
2. Produce a two-panel figure: the 64-class material view beside the traversability
   view, same frame, same viewpoint.
3. Caption it in plain language — what the client is looking at and why it matters.
   No jargon, no metric names.

**Done when.** A single PNG a reader unfamiliar with the project can interpret in
under 60 seconds. Test it on a teammate outside this pair.

**Output.** `docs/evidence/goose_client_figure.png`

> This is the artefact most likely to restart the conversation with Adrian. It shows
> their preferred dataset answering the question they described at kickoff. Spend
> proportionate care on it.

---

## D5 — Survey §7 and limitations

**Goal.** Update `docs/dataset-surveys/goose.md` with what the fortnight established.

**Steps.**
1. Rewrite §7 "Fit for this project" now that GOOSE is actually understood — what it
   can do, what it cannot, and the verdict.
2. Add a **Limitations** subsection covering: camera↔LiDAR temporal misalignment
   (authors confirmed, fusion not viable), reduced-sensor ROS bags, ROS 1 not ROS 2,
   radar not obtainable, incomplete LiDAR scans.
3. Link the evidence images produced in D1, D3 and D4.
4. Update the §0 metadata block — date, status.

**Done when.** A teammate who has not touched GOOSE can read §7 and correctly state
what the dataset is for and what it cannot answer.

**Output.** Updated `docs/dataset-surveys/goose.md`

---
---

# TASKS — RICKY

## R1 — Environment and smoke test ⚠️ **do this in the first two days**

**Goal.** Get a working GOOSE environment on Windows and confirm it independently of
Damien's macOS setup.

**Why it is urgent.** Every task you have depends on this, and it is the step most
likely to go wrong — the tooling was built and tested on macOS. If Windows throws
something unexpected, you want to find out on day one, not day four with the
3 September checkpoint looming.

**Steps.**
1. Follow §2 end to end, using the **Windows** blocks.
2. Run the §2.6 smoke test. Open the PNG and compare it against the committed examples
   in `docs/evidence/` — it should look equivalent.
3. Run §2.7 (git line endings) and §2.8 (GPU check).

**Done when.** The smoke test prints `Found 961 annotated frames.`, writes a PNG, and
that PNG looks like the committed examples.

**Output.** An experiment-log entry recording the setup, including anything that did
not work first time and the exact error text.

> **This is the most valuable single task in the fortnight, and it is easy to
> undervalue.** It is the first clean-machine, different-OS reproduction of Damien's
> work, which is precisely what acceptance criterion **P-5** demands — a person outside
> the original setup clones the repo and reproduces a documented result. A cross-platform
> reproduction is stronger evidence than a second macOS one would be.
>
> So if setup fails, **that failure is the result** — record it rather than quietly
> working around it. Any macOS assumption baked into `goose_render_frame.py` needs to
> come back to Damien as a bug, not be patched locally on your copy.

### R1b — GPU audit (30 seconds, potentially significant)

Run `nvidia-smi` (§2.8) and record the outcome.

Risk **R-08** states no team member has a discrete NVIDIA GPU, and the Skills Audit
assigns Aiden to audit team hardware in week 1 — as far as this pair knows, that audit
never happened. Damien's Apple Silicon machine definitively cannot run CUDA. **If your
Windows machine has an NVIDIA GPU, R-08 may be wrong**, which would change what the
whole team believes about needing Kaya or Colab, and could put the Pointcept / PTv3
baselines back in scope for a later sprint.

Report either answer to the team. Note the GPU model and VRAM if there is one.

---

## R2 — Dataset statistics

**Goal.** Quantify what Damien is looking at. Move from "it looks like mostly grass"
to measured numbers.

**Steps.** Write a script that walks all 961 frames and computes:
1. Class frequency across the whole split — total points per class, share of all points
2. Per-scenario class distribution — how does the mix change across season and weather
3. Points per frame: min, max, mean, median
4. Radial range distribution — what fraction of labelled points fall in 0–25 m,
   25–50, 50–100, 100–150, 150 m+
5. Which of the 64 classes are effectively absent (say, under 0.01% of points)

**Done when.** `dataset-statistics.md` contains all five, as tables, and
`scripts/goose_stats.py` reproduces them from a clean checkout.

**Output.** `GOOSE - Ricky+Damien/dataset-statistics.md` · `scripts/goose_stats.py`

> Item 4 matters beyond this fortnight. Damien measured labelled points out to roughly
> ±200 m, which was unexpected. Knowing the *density* at range tells the team whether
> GOOSE has anything to say about long-range perception, which is decision **D-04**.
>
> Item 5 matters for honesty: a 64-class dataset where 20 classes barely appear is
> effectively a 44-class dataset, and any mIoU averaged over all 64 is misleading.

---

## R3 — Traversability mapping ⚠️ **blocks D3 — deliver by 3 September**

**Goal.** Decide, for each of GOOSE's 64 classes, whether a vehicle can drive on it.
This is the judgement at the centre of the fortnight, and it is deliberately yours
rather than buried in Damien's code — so it is explicit, reviewable and arguable.

**Use STONE's four-class scheme**, so our terminology matches the off-road literature
and carries over if the STONE strand ever unblocks:

| ID | Class | Meaning |
|---|---|---|
| 0 | **Free** | Open space, no surface — sky, void |
| 1 | **Traversable** | Drive on it normally — asphalt, gravel, soil, low grass |
| 2 | **Potentially Traversable** | Possible but uncertain or risky — high grass (hides what's beneath), shallow debris, moss |
| 3 | **Non-Traversable** | Do not — tree trunks, buildings, water, rocks, people, vehicles |

**Steps.**
1. Read the full class list in `goose_label_mapping.csv` (64 entries).
2. Produce `traversability_map.csv` with columns:
   `label_key, class_name, traversability_id, traversability_name, rationale`
3. **Every row needs a one-line rationale.** The hard cases are the point: is
   `high_grass` traversable or potentially traversable? Is `snow` traversable, or does
   it hide what's underneath? Is `water` always non-traversable, or does depth matter?
   Write your reasoning — a reviewer must be able to disagree with a specific line.
4. Flag the genuinely uncertain ones in a "contested" section for the checkpoint.

**Done when.** All 64 classes are assigned, each with a rationale, and the file loads:
```powershell
& $PY scripts\validate_traversability_map.py --dataset-root $DATA
```

It must print **`VALID — contract holds.`** That check verifies all 64 GOOSE classes
are covered, every id is 0–3 with a matching name, no rationale is blank, and no class
is duplicated or invented. **Run it before you hand over, not after Damien reports a
bug.** Damien runs the same command on receipt.

Save the file with plain commas. Excel on Windows may write semicolons depending on
your locale, which the validator will reject — a plain text editor or
`pandas.to_csv(..., index=False)` avoids it. A UTF-8 byte-order mark is fine; both the
validator and Damien's renderer read `utf-8-sig`.

**Output.** `GOOSE - Ricky+Damien/traversability_map.csv`

> This is a real research contribution, not clerical work. There is no official
> GOOSE traversability mapping — you are creating the team's, and it becomes the thing
> we defend to Fabian. A defensible mapping with honest uncertainty beats a confident
> one that quietly guesses.

---

## R4 — Experiment log entries

**Goal.** Turn the fortnight into reproducible records, per your own RY-2 template.

**Steps.** Write entries in `experiment-log/` for: the environment setup (R1), the
statistics run (R2), and Damien's traversability rendering (D3) using his notes from
`findings-damien.md`. Create the `experiment-log/` directory — it is referenced by both
templates but does not exist yet.

**Done when.** At least three entries exist, each complete enough that a stranger could
repeat the work or understand why they cannot.

**Output.** `experiment-log/0001-*.md` onwards

---

## R5 — Segmentation metrics definitions

**Goal.** Fill in the segmentation half of `docs/metrics-definitions.md`, which is
currently marked "to define precisely (Ricky)".

**Steps.**
1. Define **mIoU** precisely: intersection over union per class, averaged over classes
   — and state explicitly which classes are included, since averaging over absent
   classes distorts the number (see R2 item 5).
2. Define per-class IoU and overall accuracy.
3. State the rule that segmentation metrics never share a table or axis with detection
   metrics — mIoU and mAP are not comparable. This is decision **D-02**.
4. Note which taxonomy any reported mIoU refers to: 64-class, 8-class challenge remap,
   or our 4-class traversability mapping. **They are three different numbers.**

**Done when.** Every metric the GOOSE work might report is defined before any number
is produced.

**Output.** Updated `docs/metrics-definitions.md`

---

## 9. Interface contract — `traversability_map.csv`

The one place the two halves of this plan meet. Ricky writes it; Damien's code reads
it. Neither should change the format without telling the other.

```csv
label_key,class_name,traversability_id,traversability_name,rationale
0,undefined,0,Free,"No surface assigned; excluded from traversability scoring."
23,asphalt,1,Traversable,"Paved surface, the reference drivable case."
50,low_grass,1,Traversable,"Short vegetation over ground; standard off-road driving surface."
51,high_grass,2,Potentially Traversable,"Drivable in principle but conceals the ground and any obstacle in it."
28,tree_trunk,3,Non-Traversable,"Rigid vertical obstacle; collision."
```

- `label_key` — integer, matches `goose_label_mapping.csv`
- `traversability_id` — 0–3, per the table in R3
- `traversability_name` — must match the id exactly
- `rationale` — one sentence, required, never blank

Damien's renderer supplies the group colours; Ricky does not need to choose them.

**Both sides validate the same way**, so a malformed file is caught at the hand-off
rather than surfacing days later as a rendering bug:

```bash
$PY scripts/validate_traversability_map.py --dataset-root $DATA
```

Neither of us changes this format without telling the other — the validator is a frozen
file (§6).

---

## 10. Definition of done for the fortnight

- [ ] All 8 scenarios rendered and observed (D1)
- [ ] Renderer supports arbitrary class groupings without breaking 64-class mode (D2)
- [ ] All 64 classes assigned a traversability class with a written rationale (R3)
- [ ] Traversability renders exist and are visually coherent (D3)
- [ ] One client-ready figure a stranger can read in 60 seconds (D4)
- [ ] Dataset statistics measured, not estimated (R2)
- [ ] Survey §7 rewritten with limitations recorded (D5)
- [ ] Segmentation metrics defined before any metric is reported (R5)
- [ ] At least three experiment-log entries, including any failures (R4)
- [ ] Branch protection enabled on `main` by Ricky (§7.9)
- [ ] `validate_traversability_map.py` prints VALID before the hand-off (R3)
- [ ] `session_check.py` exits 0 before every PR is opened
- [ ] One PR per person per week, each reviewed by the other

---

## 11. Out of scope this fortnight

Listed so an assistant does not helpfully wander into them.

| Not doing | Why |
|---|---|
| Running Pointcept / PTv3 baselines | Requires CUDA. Impossible on Damien's Apple Silicon; possible on Ricky's machine only if §2.8 finds an NVIDIA GPU — a team decision, not a task here (R-08) |
| Camera↔LiDAR fusion | Authors confirmed the frames are not reliably time-aligned (§4.4) |
| Downloading GOOSE 2D images | Not needed for traversability work on point clouds |
| Chasing GOOSE radar | Not obtainable — see §1 |
| Anything involving STONE | Parked pending ~645 GiB storage; see `docs/dataset-surveys/stone.md` |
| Training any model | The project runs existing models; it does not train from scratch |
| Autoware / ROS 2 integration | Belongs to FZ-1 and KL-3, not this pair |
