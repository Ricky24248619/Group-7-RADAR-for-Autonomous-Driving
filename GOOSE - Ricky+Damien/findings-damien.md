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

## For the checkpoint

- [ ] Confirm §9 is authoritative over D2's column list (above)
- [ ] Ricky: R2 item 4 should extend my radial sampling to all 961 frames
- [ ] Ricky: the 11-vs-40 class spread matters for how R5 defines mIoU
- [ ] For R3, the classes I expect to be genuinely contested: `high_grass`, `crops`,
      `snow`, `soil`, `debris`, `water`, `moss`. Each is arguably drivable depending on
      depth, season or what it conceals
- [ ] Branch protection on `main` is still not enabled — Ricky, §7.9
