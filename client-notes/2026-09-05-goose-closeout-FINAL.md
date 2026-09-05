# Client Note — GOOSE closeout

**Status:** proposed replacement for the 30 August and 1 September notes; prepared for
team review, not sent. The outside-pair readability check was not performed. Record the
team's acceptance of that omission or complete the check before sending.

**From:** Team 07 · **To:** Adrian Boeing, Fabian · **Date:** 5 September 2026
**Re:** What GOOSE answered, what it cannot, and where we go next

---

## What we tested

Whether GOOSE — the off-road dataset you asked us to keep — can answer the question you
set at kickoff: *what can I drive over, what can I crash into?* And whether we could run
its published model on it, which is the benchmarking exercise you described.

## What happened

**The GOOSE characterisation is complete; we propose closing this strand here.** Two
of us set it up independently, on
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
   team measured 6,746 radar returns at 150 m or beyond across 24 selected frames.
   These are sensor returns, not correctly detected objects or an accuracy score.

2. **GOOSE cannot give a fair radar-versus-LiDAR comparison.** Its vehicle carries six
   radars, but the downloadable data provides no radar ground truth and no radar-first
   baseline for the same task. The authors have confirmed the released raw files contain
   only a reduced sensor set. The direct sensor comparison belongs on TruckScenes.

3. **Bounded model inference works, and we have no complete benchmark score.** The
   tested PTv3 path needs CUDA and cannot use the Apple GPU. On the GTX 1660 we completed
   small and large frame gates, then 10 of 961 validation frames before Ricky requested
   that sustained GPU load stop. A roughly five-hour estimate extrapolates from partial
   loop timings and excludes data loading; full-run time and memory remain unverified.
   The partial numbers are diagnostics, not a benchmark.

4. **A completed run still would not be directly comparable to the published score.**
   We used a compatibility patch, FP32, smaller patch sizes, disabled FlashAttention and
   one test augmentation. Our zero-union class rule can also change the reported mean
   relative to the reference evaluator. Any score must state the model configuration,
   taxonomy and evaluated class set.

## What it means

GOOSE supports a documented interpretation of off-road terrain labels; automatic
recognition and vehicle-safe traversability are not established by our figure. The
paired radar question is not answerable with the GOOSE assets available to us. STONE
was the off-road radar candidate we dropped on 29 August: a single 346 GB download, no toolkit in its
repository, and maintainers who have not replied since March. We would revisit it if
those blockers changed.

A completed GOOSE run could add a score under the declared modified protocol, but
would not add radar evidence. We propose TruckScenes for the first controlled sensor
comparison because its devkit is already working for the team. Both TruckScenes and
TruckDrive provide shared scenes with radar, LiDAR, camera and common annotations.
TruckDrive remains the planned long-range comparison; TruckScenes' stock evaluator
ends at 75 or 150 m by class.

**Compute remains a planning constraint.** Suitable sustained compute has not been
confirmed for the planned complete model benchmarks. Each selected baseline still needs
a compatible checkpoint and a small feasibility test to establish its requirements.
Our current project record has the Kaya application awaiting your sign-off.

## What we need from you

**Please confirm we should close GOOSE here, keep the partial run as the honest result,
and move the radar-versus-LiDAR work to TruckScenes.**

That decision would guide the next phase. If a complete GOOSE evaluation still has
value to you, we can scope it on remote or explicitly approved limited compute.

Kaya access would help us plan those larger runs. Dataset comparisons, checkpoint
selection and preparation of the evaluation protocol can proceed while access is pending.

---

*Everything above is documented in our repository with evidence: dataset surveys,
measured statistics, and a record of every attempt including the ones that failed. A
fuller write-up of the GOOSE work is in `GOOSE - Ricky+Damien/GOOSE-SUMMARY.md`.*
