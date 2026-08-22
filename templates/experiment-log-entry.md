# Experiment Log — Entry Template

One file per experiment attempt in `experiment-log/`, numbered sequentially
(`0001-short-name.md`). Successes AND failures both get entries — the client has
said negative results count as results, and an unlogged failure gets repeated
by someone else.

**What belongs here vs in a dataset survey:** *dataset* facts and feasibility
(characters, sensors, licence, whether it can be obtained) go in
`docs/dataset-surveys/<dataset>.md` — see `stone.md` §6 for a worked example of
a dated failure record inside a survey. This log is for *experiments*: devkit
installs, model runs, Autoware attempts, visualisation scripts, anything with
commands and an outcome.

Fill in every section; write "none" or "N/A" rather than deleting a section.
The test for a good entry: **a teammate who wasn't there can reproduce it from
a clean machine, or understands exactly why they can't.**

---

## EXP-NNNN — short descriptive name

- **Date started / completed:**
- **Owner:** (who ran it)
- **Workstream / story:** (e.g. WS2 / KL-2)

### Goal

What question does this attempt answer? One or two sentences.

### Environment

OS and version, Python version, key package versions, GPU if any, whether this
was native / WSL2 / Docker / lab machine. If this is the first entry on a
freshly set-up machine, say so — clean-machine setups are exactly what we want
recorded.

### Dataset / data subset

Dataset name, exact subset or scene IDs used, where the data came from, how
much was downloaded. If no dataset yet (e.g. devkit install test), say so.

### Steps and commands

The actual commands run, in order, enough to repeat them. Pin versions in
install commands (`pip install x==1.2.3`, not `pip install x`).

### Outcome

- [ ] Success — worked as intended
- [ ] Partial — describe what worked and what didn't
- [ ] Failure — did not achieve the goal

Describe what happened, including the *exact* error text (copy-paste, don't
paraphrase — paraphrased errors are unsearchable).

### Attempted fixes

What was tried to resolve any errors, in order, and what happened after each.

### Decision

- [ ] Retry (what exactly, and when)
- [ ] Change approach (to what)
- [ ] Stop — this path is closed

**Time spent:** (hours — helps the timesheets and tells the next team what
this cost)

### Next action

The single next concrete step, with an owner if it isn't the same person.
