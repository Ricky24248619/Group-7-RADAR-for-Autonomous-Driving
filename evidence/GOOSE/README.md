# GOOSE — collated evidence

**Pair:** Ricky Yuen + Damien Zhang · **Collated by** Damien, 30 September 2026
**Dataset:** GOOSE 3D, the German Outdoor and Offroad Dataset (Fraunhofer IOSB). Base
validation split: 961 LiDAR frames across 8 off-road scenarios, with 64-class point labels.

Everything the GOOSE pair established, in one folder. Every figure and table here is a
**byte-identical copy** of committed evidence (`verification.json` has the SHA-256 of
each one). The originals stay where they are so existing links don't break.
`manifest.json` says where each file came from, which script made it, and which result
record and experiment log back it.

---

## The findings, in order of how much they matter

**1. GOOSE is the project's only off-road dataset with labelled points, and it cannot
answer the long-range question.** Across all 961 frames and 174,891,807 labelled points,
**3.84% of points lie beyond 100 m and 1.10% beyond 150 m** (split-level; per-scenario it
ranges ~1–6%). GOOSE also has no labelled radar. Its six radars are Smartmicro units,
not documented as 4D. So it can't test radar vs LiDAR, and it can't test 200–400 m.
→ `01-dataset-characterisation/` · records 0001, 0014

**2. Traversability here is our grouping of human labels, not a model's decision.**
GOOSE's annotators labelled 64 classes. We grouped them into *free / traversable /
potentially traversable / non-traversable* in `traversability_map.csv`, with 14
contested assignments argued in `traversability-map-notes.md`. The rendered figures
show that grouping. They don't show where a vehicle can safely drive.
→ `02-traversability/` · record 0004

**3. The published model (PTv3) runs on team hardware only in a reduced
configuration, and only partly.** Apple Silicon can't run it (no CUDA). On the GTX 1660
(6 GiB) it runs in FP32 with attention patch 64 instead of the published 1024. The full
split was stopped after **10 of 961 frames** at 18.94 s/frame. The ~5.1 h full-split
figure is an extrapolation of loop time, so it's a lower bound, not a measurement. Our
numbers are therefore **diagnostics of a modified configuration**, never a reproduction
of the published 0.8096 mIoU.
→ `03-ptv3-10frame-saved-predictions/` · records 0005, 0006, 0026

**4. Ground is recognised well across scenarios; obstacles mistaken for ground is the
real failure.** On 24 fresh frames (three per scenario, 4,192,081 points), ground points
are assigned a ground category **97–99% of the time in every distance band**. Obstacle
points called ground rise from **2.99% at 0–25 m to 14.17% at 100–150 m**. The earlier
10-frame result, where ground recognition dropped with distance, did **not** hold up
across scenarios: 85% of the 100–150 m ground points come from one easy scenario.
→ `04-ground-vs-obstacle/`, `05-ptv3-24frame-eight-scenarios/` · records 0027, 0032

**5. Those obstacle errors are few obstacles, not many.** 96.92% of nearby
rock-to-ground errors come from **one frame** (three rock instances), and 98.75% of nearby
building errors from the same frame. "40% of rock points confused" must never be read
as "40% of rocks missed".
→ `06-error-cases/`

**6. Part of the cause is our reduced configuration.** On three fixed frames, raising the
attention patch from 64 → 128 → 256 cuts nearby rock-called-ground from **49.52% → 25.02%
→ 22.56%** and building-called-ground from **18.43% → 10.18% → 4.12%**. A repeat of the
baseline gave identical predictions, so the change is real and not noise. It is not a
full fix: many rocks just move to a different wrong label.
→ `07-failure-causes/` · record 0033

**7. The workflow reproduces on a second machine.** Ricky reproduced Damien's macOS
setup on Windows (EXP-0001), and Fariya independently reproduced frame 0 on 24
September: 961 files, 169,883 points, same class breakdown.
→ `08-reproduction/`

## What GOOSE cannot tell us
- Nothing about **radar**: no radar labels, so no radar result of any kind.
- Nothing about **200–400 m**: 1.10% of points are beyond 150 m.
- Nothing about **object detection**: the labels are per-point segmentation, with no boxes.
- Nothing about **safe driving**: "ground" is not "drivable". Slope, softness, water depth
  and clearance aren't labelled, and an empty patch in a scan isn't a hole.
- The model numbers are for **one reduced configuration** on 10–24 frames, not a benchmark.

## Open items
- **G-2:** the published val split is **960** frames and our extract has **961**. The eight
  scenario counts sum to 961, but that only proves internal arithmetic. The file-level
  comparison against the published inventory hasn't been done.
- **G-8:** the GOOSE radars aren't 4D as far as our sources go. Confirming it needs the
  Smartmicro datasheets.
- A full-split PTv3 run at the published patch size (1024) has not been attempted.

## Three claims we withdrew (kept because they're instructive)
1. **"GOOSE has no radar."** The landing page lists only *annotated* modalities, and the
   paper documents six radars.
2. **"Woodland is blocked at ground level."** That came from an absolute-height cut, which
   fails on slopes. Taking the lowest return per 0.4 m cell roughly halves the blocked
   share (one scene went from 92% to 58%).
3. **"Assigning `bush` decides whether a corridor exists."** The traversable share is
   identical to one decimal place either way.

## Folder map

| Folder | Contents | Record(s) |
|---|---|---|
| `01-dataset-characterisation/` | Contact sheet, sample frames, class/traversability by range CSVs | 0001, 0002, 0003, 0014 |
| `02-traversability/` | Per-scenario traversability renders, bush sensitivity, **the mapping CSV** | 0004 |
| `03-ptv3-10frame-saved-predictions/` | Class/range error tables for the 10 completed frames | 0006, 0026 |
| `04-ground-vs-obstacle/` | 64-label partition, ground/obstacle confusion (includes the STONE metadata audit from the same run) | 0027 |
| `05-ptv3-24frame-eight-scenarios/` | Frame selection, runtime, semantic and ground confusion by range and scenario | 0032 |
| `06-error-cases/` | Per-frame and per-rock-instance error concentration | 0032 |
| `07-failure-causes/` | Patch 64/128/256 comparison, geometry and camera checks | 0033 |
| `08-reproduction/` | Fariya's independent frame-0 render | 0002 |

**Full write-ups:** [`GOOSE-SUMMARY.md`](../../GOOSE%20-%20Ricky+Damien/GOOSE-SUMMARY.md),
[`dataset-statistics.md`](../../GOOSE%20-%20Ricky+Damien/dataset-statistics.md),
[`goose-multiscenario-terrain.md`](../../docs/goose-multiscenario-terrain.md),
[`goose-error-cases.md`](../../docs/goose-error-cases.md),
[`goose-failure-causes.md`](../../docs/goose-failure-causes.md),
[`offroad-ground-and-obstacles.md`](../../docs/offroad-ground-and-obstacles.md),
[`dataset-suitability.md` §6](../../docs/dataset-suitability.md).

See [`results-log.md`](results-log.md) for every GOOSE experiment in date order.
