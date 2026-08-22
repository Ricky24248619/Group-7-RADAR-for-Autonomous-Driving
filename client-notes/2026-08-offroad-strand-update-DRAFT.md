# Client Note — Off-road strand: GOOSE feasible, STONE parked on storage (DRAFT)

> For Adrian and Fabian, in the four-part RY-4 format (what we tested, what
> happened, what it means, what we recommend). Target: readable in under two
> minutes. **Hold until Damien's survey branch is merged and reviewed, then
> send with the sprint update / raise at the next meeting.**

---

**From:** Team 07 · **Date:** week 5–6, August 2026 · **Re:** off-road strand status

## What we tested

Two things: end-to-end feasibility of GOOSE — the dataset you asked us to keep
in the project — (devkit install, download, frame loading and rendering), and
obtainability and fit of STONE (ICRA 2026), the additional off-road candidate
we proposed at kickoff. Both are documented as dataset surveys with evidence in
our repository.

## What happened

**GOOSE passed** on 22 August: installed, downloaded, rendered, evidence
attached. Two findings worth your attention: it carries **six radar sensors
with 360° coverage in its raw ROS bags — unlabelled**, and whether those
Smartmicro radars are 4D imaging or conventional is not stated in the paper.
Its task is semantic segmentation, so it cannot join the detection benchmarks —
but its terrain classes are almost exactly your kickoff framing (drivable vs
crash-into), and because it ships as **native ROS bags**, it is our cheapest
path to a running Autoware demo.

**STONE is real and public but not actionable yet.** It is the only off-road
dataset we have found with **annotated 4D imaging radar** — genuinely rare, and
the best match for the off-road radar interest. But: the download is one
monolithic 346 GB zip with no sample split (≈645 GB of working space needed to
download and extract), the repository contains no devkit, and the maintainers
have not replied to any GitHub issue since March. Its licence (CC BY-NC-ND)
may also collide with our handover requirement that a future team can clone
the repo and reproduce results.

## What it means

The off-road direction is **not blocked — it is a resourcing question**. When
we scoped Sprint 1 we believed off-road datasets lacked radar entirely; that
was wrong. Radar exists off-road in two forms (annotated 4D in STONE, raw 360°
in GOOSE), so the strand is viable if storage for STONE can be found.

## What we recommend

1. **STONE storage:** is ≈645 GB of working space obtainable — Kaya once our
   application is through, the DGX Spark workstation, or lab storage? This one
   decision determines whether the annotated-4D-radar off-road strand happens.
2. **Fabian:** are GOOSE's Smartmicro UMRR-96/UMRR-11 radars 4D imaging
   (elevation channel) or conventional automotive radar? This decides whether
   GOOSE counts toward the 4D RADAR focus or serves as the terrain baseline.
3. **Adrian:** does STONE's CC BY-NC-ND licence conflict with the
   reproducible-handover requirement, given results are publishable but
   converted/redistributed data is not?
4. **Meanwhile, without waiting:** GOOSE terrain work and the Autoware demo on
   GOOSE bags, and the on-road radar benchmarking on TruckScenes / TruckDrive
   with the long-range question (D-04), both continue.
