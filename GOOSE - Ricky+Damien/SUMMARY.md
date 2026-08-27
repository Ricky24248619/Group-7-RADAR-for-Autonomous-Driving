# GOOSE — Ricky & Damien, Sprint 2

**The short version, for humans.** Full detail in [`WORKPLAN.md`](WORKPLAN.md);
background in [`GOOSE-CONTEXT.md`](GOOSE-CONTEXT.md).

---

## What we are doing and why

GOOSE is an off-road dataset where humans labelled every LiDAR point and camera pixel
into 64 categories — `low_grass`, `gravel`, `tree_trunk`, `water`, and so on. That
class list is essentially a written-out version of what Adrian asked for at kickoff:
*"What can I drive over? What can I crash into?"*

Over this fortnight we are going to turn that from a claim into a picture. We take the
64 material classes, collapse them into four traversability classes, and render a frame
showing the drivable route through non-drivable surroundings.

**The deliverable that matters most is one image** — the client's own question, answered
with the client's own preferred dataset, that a person can understand in under a minute
without anyone explaining it.

---

## What GOOSE is good for, in one table

| | |
|---|---|
| ✅ Off-road terrain — drivable vs not | The client's stated interest, and workable today |
| ✅ On-road → off-road transfer | Fabian asked for this specifically |
| ✅ Cheapest path to an Autoware demo | The only dataset shipping native ROS bags |
| ❌ Anything about radar | Six radars on the vehicle, but unlabelled, not in the download, and probably not 4D |
| ❌ Object detection benchmarks | It is segmentation. Its scores cannot share a table with TruckScenes or TruckDrive |
| ❌ Sensor fusion | Camera and LiDAR are not reliably time-aligned — the authors confirmed a bug |

---

## How the work splits

The split follows what each of us already owns, and the files are deliberately
non-overlapping so two people running AI assistants in the same repo do not collide.

**Damien — the visual side.** Render frames across all 8 scenarios, refactor the
renderer to support class groupings, build the traversability view, produce the client
figure, and update the survey.

**Ricky — the quantitative and definitional side.** Reproduce the environment from
scratch, measure the dataset properly, define the traversability mapping, write the
experiment logs, and define the segmentation metrics before any number gets reported.

**One handoff between us:** Ricky decides what counts as drivable — all 64 classes, each
with a written rationale — and delivers it as `traversability_map.csv` by the
**3 September checkpoint**. Damien's renderer reads that file. Everything else runs in
parallel, so neither of us is ever blocked waiting.

That mapping is the intellectually interesting part. There is no official GOOSE
traversability mapping; we are making the team's. Is `high_grass` drivable, or does it
hide what is underneath? Is `snow` a surface or a mask over one? Those judgements get
written down with reasons so Fabian can disagree with a specific line rather than the
whole idea.

---

## We're on two different operating systems

Damien is on macOS, Ricky on Windows. The workplan gives every command for both, and
uses `$PY` / `$DATA` variables so the task steps read the same on either machine.

Two consequences worth knowing up front:

**Ricky's environment setup is the highest-value task in the fortnight, and it's first.**
Everything he does depends on it, and all the tooling so far was built and tested on
macOS — so it is also the most likely thing to break. Getting a Windows machine to
reproduce Damien's results is exactly what acceptance criterion **P-5** asks for (someone
outside the original setup clones the repo and reproduces a result), and a cross-platform
reproduction is stronger evidence than a second Mac would be. If it fails, that failure
gets recorded, and any macOS assumption in the code comes back to Damien as a bug.

**Ricky should run `nvidia-smi` on day one.** Risk R-08 says nobody on the team has a
discrete NVIDIA GPU, and that was never actually audited. Damien's Apple Silicon
machine definitively cannot run CUDA. If Ricky's Windows machine has an NVIDIA card,
R-08 is wrong, and several team-wide assumptions about needing Kaya or Colab change.
Thirty seconds to check, potentially significant either way.

---

## Rough timeline

| | Damien | Ricky |
|---|---|---|
| **Week 1** | Frame sweep, contact sheet, renderer refactor | Environment, dataset statistics, traversability mapping |
| **3 Sep** | Checkpoint — mapping handed over | |
| **Week 2** | Traversability renders, client figure, survey update | Experiment logs, metrics definitions |
| **10 Sep** | One PR each, reviewing each other | |

---

## What we are deliberately not doing

- **Chasing the radar.** The maintainers confirmed the downloadable bags carry a
  reduced sensor set and there is no convenient way to get the full raw data. Since we
  cannot obtain it, whether those radars are 4D has no bearing on this fortnight.
  Recorded as a deliberate deferral under risk R-24, not forgotten.
- **Running the published baselines.** They need CUDA. Damien's Mac cannot, and
  whether Ricky's Windows machine can is an open question — see the GPU note above.
  Either way it is risk R-08 and not this fortnight.
- **Sensor fusion.** Broken upstream, see above.
- **Anything on STONE.** Parked pending ~645 GiB of storage.

---

## On the Scope of Work still not being approved

Worth saying plainly: it is not blocking this. Our own Scope of Work is headed *"working
document — subject to change"*, and Adrian told us directly *"I want you to be agile...
you guys as a team decide"* and *"there's no commitment to it — if you look into snow
and go, I'd rather jump on tracking, just change."*

Approval was never the gate for exploring. And the client figure from D4 is probably a
better way to restart that conversation than another email.
