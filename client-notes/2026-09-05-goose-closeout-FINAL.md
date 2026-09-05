# Client Note — GOOSE closeout

**Supersedes** the 30 August and 1 September proposals. Ready to send.

**From:** Team 07 · **To:** Adrian Boeing, Fabian · **Date:** 5 September 2026
**Re:** What GOOSE answered, what it cannot, and where we go next

---

## What we tested

Whether GOOSE — the off-road dataset you asked us to keep — can answer the question you
set at kickoff: *what can I drive over, what can I crash into?* And whether we could run
its published model on it, which is the benchmarking exercise you described.

## What happened

**GOOSE works, and we have finished with it.** Two of us set it up independently, on
macOS and Windows, and both reproduced the same result from a clean machine. We measured
the full validation split — 961 frames, 174.9 million hand-labelled points — and mapped
its 64 surface types into four levels: drivable, uncertain, not drivable, and free
space.

![Ground material and traversability interpretation](../docs/evidence/goose_client_figure.png)

**What this figure is, and is not.** It is our interpretation of the dataset authors'
human labels, not a model prediction. It shows that GOOSE can support your question,
subject to vehicle-specific judgement. It does not show a system detecting anything.

### Four findings

1. **GOOSE cannot answer the long-range question.** 62.9% of its labelled points lie
   within 25 m and only 3.8% beyond 100 m. Long range stays with TruckDrive, where the
   team has already measured 6,746 radar detections at 150 m or beyond.

2. **GOOSE cannot give a fair radar-versus-LiDAR comparison.** Its vehicle carries six
   radars, but the downloadable data provides no radar ground truth and no radar-first
   baseline for the same task. The authors have confirmed the released raw files contain
   only a reduced sensor set. The direct sensor comparison belongs on TruckScenes.

3. **The published model runs, and we have no score.** Its PTv3 baseline needs CUDA. It
   cannot run on Apple Silicon at all. It does run on our one NVIDIA laptop in FP32, and
   we completed 10 of 961 frames before stopping deliberately — a full pass is about
   **five hours of sustained load** on a student machine. The partial numbers are
   diagnostics, not a benchmark.

4. **A completed run still would not be directly comparable to the published score.**
   The reference implementation and our own metric definition average over different
   class sets, so identical predictions produce two different numbers. Any reported
   score has to state which definition it used.

## What it means

The **terrain half** of your off-road interest is answerable, and we have answered it on
the dataset you asked us to keep. The **radar half** is not answerable on GOOSE. It
needed STONE, which we dropped on 29 August: a single 346 GB download, no toolkit in its
repository, and maintainers who have not replied since March. We would revisit it if
those blockers changed.

A longer GOOSE run would add a reproduction score. It would not add radar evidence. So
the comparison should move to TruckScenes, which is the only dataset carrying radar,
LiDAR and camera against the same ground truth.

**One constraint remains unresolved and it is not GOOSE-specific.** A complete benchmark
on any dataset needs compute we do not have. The Kaya application is still with you — we
have a Principal Investigator thanks to you agreeing, and the remaining paperwork needs
your sign-off.

## What we need from you

**Please confirm we should close GOOSE here, keep the partial run as the honest result,
and move the radar-versus-LiDAR work to TruckScenes.**

That is one decision and it unblocks the next three weeks. If a complete GOOSE
reproduction still has value to you, say so and we will schedule it on remote or
deliberately limited compute rather than running a laptop flat for five hours.

If you have twenty minutes for the Kaya paperwork at any point, that remains the
difference between describing what these datasets contain and measuring how models
perform on them.

---

*Everything above is documented in our repository with evidence: dataset surveys,
measured statistics, and a record of every attempt including the ones that failed. A
fuller write-up of the GOOSE work is in `GOOSE - Ricky+Damien/GOOSE-SUMMARY.md`.*
