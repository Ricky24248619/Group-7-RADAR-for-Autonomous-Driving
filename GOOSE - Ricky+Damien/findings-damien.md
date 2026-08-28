# Findings — Damien, GOOSE Sprint 2

Working notes for tasks **D1** (frame sweep) and **D2** (renderer refactor).
Week 1, branch `goose/damien-w1`.

---

## D1 — Frame sweep

Rendered and summarised three frames from each of the eight validation scenarios,
plus a contact sheet tiling one bird's-eye view per scenario:
[`docs/evidence/goose_contact_sheet.png`](../docs/evidence/goose_contact_sheet.png).
Produced by `scripts/goose_contact_sheet.py`, which also prints the per-scenario
summary the observations below are drawn from.

### Per-scenario observations

**`2022-07-22_flight` — summer.** A single track running roughly east–west with a
continuous `hedge` line along one side (17% of points) and `tree_crown` on the other.
`low_grass` 28%, `bush` 18%. The drivable corridor is unusually legible — one clear
asphalt strip with vegetation boundaries either side. Good candidate for the D4 client
figure. Largest vertical extent of any scenario, z up to +48 m, which is the tree
canopy rather than terrain.

**`2022-08-30_siegertsbrunn_feldwege` — summer, field tracks.** The most visually
distinctive frame. Agricultural: `soil` field on one side, `low_grass` on the other,
`crops` strips at the edges (23% crops — the only scenario where crops matter). Very
open, and the concentric LiDAR rings are clean and unbroken out to a long way. 29
classes present.

**`2022-09-21_garching_uebungsplatz_2` — autumn, training ground.** `forest` 38%
dominant, with a wide `high_grass` band through the middle. Only 13 classes present —
one of the least diverse scenarios. Densest frames in the split alongside the winter
ones (mean ~199k points).

**`2022-12-07_aying_hills` — winter, hills.** `forest` 35% and `tree_trunk` 18% — by
far the highest tree_trunk share, so this is genuinely inside woodland rather than
alongside it. Sparse-looking in the ±100 m window because 73% of its points fall
within 25 m: the trees occlude everything beyond.

**`2023-01-20_aying_mangfall_2` — winter.** The most extreme range profile in the
split: **89.5% of points within 25 m**, 1.1% between 50–100 m. Also the only scenario
with meaningful `snow` (9%) and `rock` (12%), and high `building` (21%). 30 classes.
Visually near-empty at ±100 m despite averaging 203k points per frame — all of it is
close in.

**`2023-03-03_garching_2` — early spring.** `low_grass` 37%, `forest` 25%,
`tree_crown` 17%. **Only 11 classes present — the least diverse scenario in the split.**
A model evaluated only here would look far better than one evaluated on neubiberg.

**`2023-05-15_neubiberg_rain` — spring, rain.** The most diverse: **40 classes**.
Urban fringe — `asphalt` 11%, `building` 16%, `tree_crown` 20%, plus cars, poles,
signs. Structurally the busiest scene and the closest thing in GOOSE to an on-road
dataset.

**`2023-05-17_neubiberg_sunny` — spring, sunny.** Same location as the rain scenario,
two days later, and it looks completely different: `bush` 28%, `forest` 22%, a large
`crops` region, only 8% building. 35 classes. **Point count is wildly inconsistent —
mean 134k, min 69k, max 206k**, a three-fold spread within one scenario.

---

## Cross-cutting findings

### 1. The ±200 m extent is a thin tail, not usable data

I previously recorded that labelled points reach roughly ±200 m. True, but misleading
on its own. Radial distribution, middle frame of each scenario:

| Scenario | 0–25 m | 25–50 | 50–100 | 100–150 | 150–250 |
|---|---|---|---|---|---|
| flight | 42.4% | 41.5% | 12.9% | 1.7% | 1.6% |
| siegertsbrunn_feldwege | 24.0% | 43.7% | 24.1% | **6.3%** | **2.0%** |
| garching_uebungsplatz_2 | 63.2% | 24.8% | 9.4% | 2.4% | 0.2% |
| aying_hills | 73.1% | 20.2% | 6.0% | 0.7% | 0.0% |
| aying_mangfall_2 | **89.5%** | 7.8% | 1.1% | 1.6% | 0.0% |
| garching_2 | 54.3% | 30.3% | 12.8% | 1.9% | 0.7% |
| neubiberg_rain | 57.2% | 28.7% | 11.7% | 1.8% | 0.6% |
| neubiberg_sunny | 70.6% | 17.2% | 8.4% | 3.2% | 0.7% |

Typically **1–6% of points beyond 100 m and well under 1% beyond 150 m.** This is a
short-to-medium range dataset with a sparse tail.

**Consequence for D-04.** GOOSE cannot contribute to the long-range question. It is not
just that the task is segmentation rather than detection — there is barely any data out
there to score. Worth stating plainly in the survey so nobody proposes it later.

> Sampled one frame per scenario. The systematic version over all 961 frames is
> **Ricky's R2 item 4** — I have not duplicated it.

### 2. Terrain type drives effective range, and it is a bigger effect than weather

Open agriculture (`siegertsbrunn_feldwege`) has the best long-range profile by a wide
margin — 6.3% at 100–150 m. Dense woodland (`aying_hills`, `aying_mangfall_2`) has
almost nothing past 50 m. Occlusion, not sensor limits.

If we ever compare per-scenario results, **scenario terrain type is a confound** and has
to be stated. Two models evaluated on different scenarios are not comparable.

### 3. Class diversity varies enormously between scenarios — 11 to 40

`garching_2` has 11 classes present; `neubiberg_rain` has 40. Two consequences:

- A per-scenario mIoU is not comparable to another scenario's without saying which
  classes were present. **Relevant to Ricky's R5** — averaging IoU over absent classes
  is exactly the distortion to define away.
- If we ever split train/eval by scenario, the domain gap is large.

### 4. Rain vs sunny is not the comparison it looks like

I expected the rain scenario to show degraded LiDAR — scattering, fewer returns. The
opposite: rain frames average **198k points and are very consistent** (193k–202k),
while sunny averages **134k and swings from 69k to 206k**.

I do not think this is a weather effect. The two drives cover different ground — rain
is urban-fringe with buildings, sunny is more open with crops — so scene content
probably dominates. **Do not use this pair as a weather-robustness comparison without
checking the routes overlap.** The 69k-point frame is also worth inspecting against
GitHub issue #18, which reports LiDAR scans with missing sections.

### 5. Snow appears in exactly one scenario

`aying_mangfall_2`, 9% of points. Anything we say about snow rests on a single
recording day. Worth remembering before writing "GOOSE covers snow" anywhere.

---

## D2 — Renderer refactor

`scripts/goose_render_frame.py` now takes `--group-map`, remapping the 64 classes to a
coarser taxonomy before colouring. Default 64-class behaviour is unchanged and D1's
output still reproduces.

Two design decisions worth review at the checkpoint:

**Unmapped classes render magenta and warn, rather than defaulting to group 0.** If
Ricky's mapping misses a class, the frame shows it as an obvious magenta blob and the
console prints which ids are missing. Silent fallback to "Free" would have been the
dangerous default — an unassigned obstacle would render as open space.

**Group colours are blue → amber → red, not green → amber → red.** Roughly 8% of men
have red-green colour vision deficiency, and blue/amber/red stays separable while still
reading as a risk gradient. Happy to revisit for the D4 client figure if green reads
more clearly to Adrian, but the default is the accessible one.

### ⚠️ Inconsistency in the workplan — for the checkpoint, not for me to fix

**D2's step 1 says the grouping file has columns `label_key, class_name, group_name,
group_colour`. The §9 interface contract says `label_key, class_name,
traversability_id, traversability_name, rationale`, and states that Damien's renderer
supplies the colours.** These disagree.

I implemented to **§9**, since it is the section headed "interface contract" and it is
what R3 tells Ricky to produce. The loader also accepts a generic
`group_id`/`group_name` layout so it is not locked to one taxonomy.

`WORKPLAN.md` is a frozen file under §6, so I have not edited it. **Raise at the
3 September checkpoint** and correct D2's wording then.

---

---

## D3 — Traversability renderer

`scripts/goose_traversability.py` renders using Ricky's `traversability_map.csv`. All
eight scenarios rendered:
[`goose_traversability_sheet.png`](../docs/evidence/goose_traversability_sheet.png)
plus a full two-panel view per scenario.

The script takes `--override CLASS=ID` so a contested assignment can be compared from
pictures rather than argued about. **It never writes to the CSV** — under §9,
assignments change in Ricky's file, never as exceptions in my code.

### Sanity check — all 8 pass

D3 asks whether the drivable region looks like somewhere a vehicle could actually go.
**In all eight, the Traversable points form a connected path**, which exceeds the
"at least 6 of 8" bar.

| Scenario | Free | Traversable | Potentially | Non-Traversable |
|---|---|---|---|---|
| flight | 0.3% | 15.2% | 19.1% | 65.4% |
| siegertsbrunn_feldwege | 0.3% | **82.1%** | 17.6% | **0.0%** |
| garching_uebungsplatz_2 | 0.2% | 28.8% | 23.1% | 48.0% |
| aying_hills | 0.3% | **2.6%** | 16.0% | 81.1% |
| aying_mangfall_2 | 0.2% | **2.6%** | 6.1% | **91.2%** |
| garching_2 | 0.1% | 45.9% | 7.0% | 47.0% |
| neubiberg_rain | 0.3% | 23.4% | 1.9% | 74.4% |
| neubiberg_sunny | 0.2% | 11.7% | 34.2% | 53.8% |

Two extremes worth noting rather than treating as errors:

- **`siegertsbrunn_feldwege` has literally 0.0% non-traversable.** Open farmland with
  no obstacle in the frame at all. Plausible, but a frame with no hazard is a poor
  choice for anything meant to demonstrate hazard detection.
- **`aying_mangfall_2` is 91.2% non-traversable on 2.6% traversable.** The vehicle
  clearly drove through it, and the render does show a connected track — it is a
  narrow ribbon through dense woodland. Coherent, but it means woodland scenarios give
  a very unbalanced class distribution. Relevant to Ricky's R5: a per-class IoU here
  will be dominated by one class.

### Correction — my canopy hypothesis was wrong

Looking at the woodland renders I suspected the bird's-eye view was conflating
*overhead canopy* with *ground obstruction* — that a drivable track was being hidden
under forest points from above. I tested it rather than asserting it:

| Scenario | Non-Trav | of which >1.5 m | >3 m | >5 m |
|---|---|---|---|---|
| aying_mangfall_2 | 91.2% | **6%** | 2% | 1% |
| aying_hills | 81.1% | 17% | 7% | 3% |
| neubiberg_sunny | 53.8% | 11% | 4% | 2% |
| flight | 65.4% | **34%** | 14% | 5% |
| garching_2 | 47.0% | **40%** | 20% | 9% |
| garching_uebungsplatz_2 | 48.0% | 34% | 19% | 9% |

**Mostly wrong.** In the dense woodland scenarios only 6–17% of non-traversable points
sit above 1.5 m, so those scenes genuinely are blocked at ground level, not merely
overhung.

**But it holds in the open scenarios** — 34–40% of non-traversable points in `flight`,
`garching_2` and `garching_uebungsplatz_2` are above 1.5 m, and roughly half of those
above 3 m. That is upper vegetation overwriting drivable ground in the projection.

**Consequence for D4.** A plain bird's-eye view overstates obstruction in open scenes.
The client figure should either slice to points below ~1.5 m or take the lowest point
per cell, so the drivable route is not buried under canopy. Carrying this into D4.

### The `bush` A/B — and a correction to my own review

I argued in the PR #6 review that the `bush` assignment was "the difference between a
drivable corridor and a mostly blocked scene". **Rendering it both ways shows I
overstated that.**

| Scenario | Non-Trav, `bush`=3 | Non-Trav, `bush`=2 | Traversable, either |
|---|---|---|---|
| flight | 65.4% | 53.8% | **15.2%** |
| garching_uebungsplatz_2 | 48.0% | **20.8%** | **28.8%** |
| aying_mangfall_2 | 91.2% | 75.1% | **2.6%** |
| garching_2 | 47.0% | 34.8% | **45.9%** |
| neubiberg_rain | 74.4% | 65.2% | **23.4%** |
| aying_hills | 81.1% | 81.0% | **2.6%** |

**The Traversable share is identical in every scenario, to one decimal place.** The
`bush` decision moves points between Potentially Traversable and Non-Traversable and
never into Traversable — so it does not change what reads as drivable at all. It
changes only how much of the scene is called *definitely blocked* versus *uncertain*.

So for the client figure it barely matters. It matters for how we characterise
uncertainty, which is a smaller claim than I made.

**My recommendation is unchanged but the stakes are lower.** I would still put `bush`
at Potentially Traversable: with it at 3, class 2 holds only soft concealment
(high_grass, snow, crops, moss), and the reason to have four classes rather than a
binary is that class 2 marks where genuine uncertainty lives. `bush` spans a 30 cm
shrub and a 3 m thicket under one label — that is the definition of uncertain.

Ricky's opposing principle — infer from the class alone, assume nothing favourable —
is coherent. This is a judgement call for the checkpoint, and one CSV row either way.

Evidence: [`goose_traversability_sheet.png`](../docs/evidence/goose_traversability_sheet.png)
against [`goose_traversability_sheet_bush-as-potential.png`](../docs/evidence/goose_traversability_sheet_bush-as-potential.png).

### Assignments I would question

Per D3 step 4 — recorded, not silently fixed.

| Class | Mapped | My view |
|---|---|---|
| `bush` | Non-Traversable | Prefer Potentially Traversable — see above |
| `forest` | Non-Traversable | Agree, but it is 24.4% of the split and the single biggest driver of the non-traversable share. Worth stating consciously rather than arriving at |
| `sidewalk` | Traversable | Ricky already flags this. Agree with keeping legality out of a physical-traversability map, but it should be stated in the definition rather than implied |

---

## D4 — The client figure

[`docs/evidence/goose_client_figure.png`](../docs/evidence/goose_client_figure.png),
built by `scripts/goose_client_figure.py`. Two panels of one frame — what the ground is
made of, beside what a vehicle could drive on — captioned in plain language with no
jargon or metric names.

**Frame chosen: `2022-07-22_flight`.** Picked by a scoring pass over all eight
scenarios rather than by eye (`--survey`). The score rewards a scene that is genuinely
mixed — enough drivable ground to read as a route, enough blocked ground to read as a
hazard. `flight` scored highest at 37% traversable / 25% uncertain / 38% blocked.
`siegertsbrunn_feldwege` scored zero: 95% drivable and no hazard at all, which is
useless for showing hazard detection however clean it looks.

### The ground slice matters more than I thought — and my D3 test was the wrong one

D3 flagged that a plain overhead view paints tree canopy over the drivable ground
beneath it. I tested that with an absolute height threshold and concluded the woodland
scenes were "genuinely blocked at ground level, not merely overhung". **That conclusion
was wrong**, and the instrument was the problem: on sloping ground, absolute z does not
separate canopy from terrain.

Taking the lowest return in each 0.4 m ground cell is the right test. Same frames, same
±50 m window:

| Scenario | Traversable raw → ground | Non-traversable raw → ground |
|---|---|---|
| flight | 15% → **37%** | 64% → **38%** |
| aying_mangfall_2 | 2% → **12%** | 92% → **58%** |
| garching_2 | 49% → **79%** | 43% → **15%** |
| neubiberg_rain | 26% → **57%** | 72% → **40%** |
| aying_hills | 3% → 6% | 80% → 63% |
| neubiberg_sunny | 13% → 20% | 57% → **11%** |
| garching_uebungsplatz_2 | 31% → 26% | 44% → 22% |
| siegertsbrunn_feldwege | 89% → 95% | 0% → 0% |

**A raw overhead view roughly halves the apparent drivable share and roughly doubles
the apparent blocked share.** Even `aying_mangfall_2` — the scene I claimed was blocked
at ground level — goes from 92% to 58% non-traversable once canopy stops covering the
terrain beneath it.

This matters beyond the figure. Any future traversability metric computed from a plain
bird's-eye projection of GOOSE will systematically understate drivable ground. Worth
recording in `metrics-definitions.md` before any number is reported — **flagging for
Ricky (R5)** rather than editing his file.

### Design decisions

- **Lowest-point-per-cell rather than a height threshold**, for the reason above.
  Cell size 0.4 m, configurable.
- **Legend entries below 0.5% are suppressed.** The first draft showed "Free 0%"
  pointing at nothing visible — exactly the detail that makes a reader distrust a
  figure they cannot interrogate.
- **No jargon in the caption**: no mIoU, no "semantic segmentation", no "point cloud".
  "A laser scanner measures the shape of the ground" and "every measurement has been
  labelled by hand".
- Both panels share one viewpoint and one extent so the eye can move between them.

### Outstanding — needs a human

D4's definition of done includes *"test it on a teammate outside this pair"*. Not done,
and not something I can do. **Kelsey or Fatima should look at it cold and say what they
think it shows**, before it goes anywhere near Adrian. If it does not land in 60 seconds
without narration, it has failed its own test.

## For the checkpoint

- [ ] Confirm §9 is authoritative over D2's column list (above)
- [ ] Ricky: R2 item 4 should extend my radial sampling to all 961 frames
- [ ] Ricky: the 11-vs-40 class spread matters for how R5 defines mIoU
- [x] ~~For R3, the classes I expect to be contested~~ — R3 delivered; `bush` is the
      one I would add to the contested list, with lower stakes than I first claimed
- [x] ~~Branch protection on `main`~~ — enabled 28 Aug
- [x] ~~**`bush`**~~ — Ricky chose A, keep at 3, as a conservative semantic prior with
      a geometry-aware layer to soften it later. Settled; my preference was noted and
      overruled on a reasonable argument
- [ ] **Client figure needs a cold read** from Kelsey or Fatima before it goes to Adrian
- [ ] **For R5:** traversability metrics computed from a plain overhead projection will
      systematically understate drivable ground — see D4
- [ ] Ricky deleted his copy of the dataset, so he cannot re-measure a changed
      assignment — that falls to me in week 2
- [x] ~~D4 should use a height-sliced view~~ — done, and it revealed my D3 height-threshold
      test was the wrong instrument. See D4
- [ ] Ricky edited `scripts/goose_traversability.py` (my file under §6) to fix a real
      bug during review of #7. Correct call, but the ownership rule was written for
      parallel work and does not say what happens during review. Worth one line in §6
