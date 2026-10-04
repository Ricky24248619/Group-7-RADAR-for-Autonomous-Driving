# AD-3: our findings against what trucking companies publish

3 October 2026 · Owner: Aiden Blampain · Reviewer: *(to assign)* · Story AD-3, Epic E

## What this is, and how it differs from the story as written

AD-3 was written in Sprint 1 as *"Comparison of leading autonomous trucking companies"*:
companies compared with each other on technology, autonomy level, sensor configuration
and deployment status. With a week of project time left, a company-against-company
survey would be background reading that none of our results depend on.

**This document reframes AD-3.** It takes the team's own sensor findings and checks each
one against what the leading autonomous trucking companies say publicly. The question is
whether industry agrees with what our data showed, disagrees, or publishes too little to
tell. The company-by-company facts are kept, but only as a short [appendix](#appendix-company-snapshot).
This variance from the original story is recorded here deliberately, per P-7.

## How to read it

- **Our side** is measured evidence: the 20 conclusions in
  [`client-level-conclusions-oct01.md`](client-level-conclusions-oct01.md) (C01–C20) and
  the TruckScenes detector work. Each row links to it.
- **Industry's side** is mostly *claims*: company blogs, filings and trade press. Companies
  publish ranges and capabilities, not scores on any dataset we used, so **no number on
  one side is compared with a number on the other.** The one exception is the TruckDrive
  research paper, released by Torc with Princeton (arXiv, March 2026), which reports
  measured results.
- **Verdicts:**
  - **Agrees:** industry's public position matches our finding.
  - **Tension:** it pulls the other way; these rows are worth raising with the client.
  - **Can't tell:** nobody publishes enough to compare.
- **Scope of the search:** written public sources only, read on 3 October 2026. No
  keynotes were watched and no company was contacted. A missing claim means *not found in
  these sources*, not *not true*.

## Summary

| # | Our finding | What industry says | Verdict |
|---|---|---|---|
| 1 | At 200–400 m, LiDAR covered distant vehicles far more completely than radar | Long-range perception is anchored on long-range (FMCW) LiDAR at 450–500 m; radar is the complement | **Agrees** |
| 2 | No available model can test recognition at 200–400 m | Torc's own TruckDrive paper: current models "do not generalize" past 150 m. Companies claim 450–1,000 m but publish no benchmark | **Agrees** (measured); company claims **can't tell** |
| 3 | No radar-first detector found (R-21) | Every trucking company whose sensors we found (5 of 6) fuses LiDAR, radar and cameras. The nearest thing to radar-first is outside trucking (Mobileye) | **Agrees** |
| 4 | 4D radar is on our datasets' trucks but has no public models | 4D/imaging radar is already on Kodiak's (since 2021), Aurora's and Plus's trucks | **Agrees**, and it explains #3 |
| 5 | Radar covered small objects, pedestrians and signs far less consistently than LiDAR; radar still adds some evidence LiDAR lacks | Radar is used for velocity, weather and long range; cameras and LiDAR handle small objects and semantics | **Agrees** |
| 6 | Fog pilot hints radar helps when LiDAR is sparse; but LiDAR kept strong car coverage in our rain and snow recordings | Radar is presented as *the* adverse-weather sensor; weather limited Aurora's driverless operations ~40% of 2025 | **Tension** |
| 7 | Public checkpoints transfer poorly to a new truck's sensors and mounting; correcting the sensor frame recovers some performance | Waabi claims its stack moved to a differently-sensored truck with zero retraining, but publishes no metrics | **Tension** (unverified claim) |
| 8 | Off-road terrain models confuse rocks, tall grass and walls with ground | Kodiak runs driverless trucks on oilfield lease roads but publishes nothing on terrain perception | **Can't tell** |

---

## 1. Long range: LiDAR, not radar, carries distant vehicles — **Agrees**

**Ours.**
- **TruckDrive (C01):** at 200–400 m, LiDAR had an in-box return on **86.11%** of 36
  vehicle observations and radar on **33.33%**. LiDAR leads in both new clips and in the
  earlier five-clip cohort.
- **TruckScenes, same car tracks (C07):** radar coverage falls from 79.95% at 0–50 m to
  52.46% at 50–100 m, while LiDAR stays above 98%.
- Coverage is sensor returns, not detection.

**Industry.**
- **Aurora:** its FirstLight LiDAR "can detect objects more than 450 meters away", with a
  next generation planned at 1,000 m. Long-range velocity also comes from the LiDAR, which
  can "track the velocity and compute the acceleration of vehicles over 400 meters away".
  Imaging radar is described as the layer that "penetrates dense fog and rain", not the
  long-range sensor [A1, A3].
- **Torc / Daimler Truck:** selected Aeva's FMCW 4D LiDAR, designed for "long-range
  detection up to 500 meters", for series-production trucks from 2027 [T1].
- **Kodiak:** calls the ZF 4D radar its "primary long range radar", tracking velocity "up
  to 350 meters". That is the longest radar claim found, and it is still short of the
  LiDAR claims above. Its forward long-range LiDARs are Luminar Iris [K1, K2].

**Reading.** Aurora and Torc both put long-range geometry on LiDAR, and specifically on
FMCW LiDAR that also measures velocity. TruckDrive was
recorded by Torc with "seven long-range FMCW LiDARs" [T2], so our 200–400 m evidence comes
from the same class of sensor industry is betting on. That makes C01 more relevant to the
client, not less.

## 2. Nothing can yet test recognition at 200–400 m — **Agrees** (measured) / **can't tell** (company claims)

**Ours.** The inspected pretrained LiDAR/radar pair accepts input only to about 70 m, and
0 of 504 vehicle centres at 200–400 m fall inside it (C20, D-04). On TruckScenes, the
stock evaluator stops scoring at 75 or 150 m by class.

**Industry, measured.** Torc's research paper introducing TruckDrive states:
*"state-of-the-art autonomous driving models do not generalize to ranges beyond 150
meters, with drops between 31% and 99% in 3D perception tasks, exposing a systematic
long-range gap that current architectures and training signals cannot close"* [T2]. This
is the same conclusion we reached, from the dataset's own authors.

**Industry, claimed.** Companies state perception horizons of 450 m (Aurora), 500 m (Aeva
for Torc) and "roughly 1,000 meters" (Torc's system as a whole) [A1, T1, T3]. None of
these is published as a detection benchmark, so we cannot check them.

**Reading.** Our D-04 answer, that long-range recognition cannot be tested with available
models, is not a gap in our effort. Torc's own published research says the same thing,
while its product marketing claims far more. That gap between research and marketing is
itself worth telling the client.

## 3. No radar-first baseline — **Agrees**

**Ours.** No radar-first detection model was found that could run on our data (R-21;
EXP-0018, EXP-0020). The radar candidates were blocked by checkpoint access or input
range.

**Industry.**
- **Trucking:** every company in this review describes a fused LiDAR + radar + camera
  stack: Aurora, Kodiak, Torc, Plus and Waabi [A1, K2, T3, P1, W1]. None describes
  radar-first perception. Gatik's sensor detail was not found in the sources read.
- **Mobileye (not a trucking company):** the closest example found. Its imaging radar
  "delivers reliable output independently of cameras or lidars" as a separate redundant
  channel, with detection claims to 315 m [M1]. That is radar as an *independent backup
  channel*, not radar as the primary sensor.

**Reading.** Industry agrees there is no radar-first baseline to borrow. R-21 is a gap in
the field, not something our search missed.

## 4. 4D radar: on the trucks, missing from public models — **Agrees**, and explains #3

**Ours.**
- Both of our trucking datasets carry 4D radar: Continental ARS 548 RDI units on
  TruckScenes ([dataset statistics](../TruckScenes%20-%20Fatima/dataset-statistics.md)),
  and "ten 4D FMCW radars" on TruckDrive [T2].
- Damien's domain-study entry found no mention of 4D radar in 131 minutes of university
  perception teaching ([Bonn entry](domain-study/damien-bonn-sdc2021.md)).

**Industry.**
- **Kodiak:** adopted ZF's 4D radar in **2021**. It explains that measuring elevation lets
  the truck "resolve complex perception scenarios such as a stopped vehicle under a
  bridge" [K1].
- **Aurora and Plus:** both name imaging radar in their sensor suites [A1, P1].

**Reading.** 4D radar reached production trucks years before it reached teaching material
or public pretrained detectors. That timeline explains #3: the hardware exists, but the
open models do not. **Glossary note:** in industry, "4D" now also describes FMCW *LiDAR*
(Aeva, and Aurora's velocity-measuring LiDAR) [T1, A1], so "4D" alone does not mean
radar.

## 5. Radar is weaker on small objects; fusion still adds — **Agrees**

**Ours.** At 0–25 m in TruckScenes, radar coverage relative to LiDAR:

| Object | LiDAR | Radar |
|---|---|---|
| Trucks (C02) | 100% | 99.12% |
| Adult pedestrians (C03) | 99.00% | 67.66% |
| Bicycles (C04) | 100% | 70.00% |
| Traffic cones (C05) | 100% | 39.00% |
| Road signs (C06) | 99.91% | 46.94% |

Radar still adds some object evidence where LiDAR has none (C08).

**Industry.** Roles are split the same way. Aurora gives cameras "semantic details such as
signage, lane markers" and emergency vehicles, and gives radar weather and motion [A1].
Kodiak's case for 4D radar is about separating *overhead* structure (signs, bridges) from
stopped vehicles, which is the classic radar false-alarm problem, not about seeing small
objects [K1]. All companies fuse; none sells radar as a small-object sensor.

**Reading.** Our per-class pattern matches how industry assigns jobs to each sensor. C08
supports industry's fusion choice over dropping radar.

## 6. Weather — **Tension**

**Ours.**
- **Fog (C09):** a tiny RADIATE fog pilot found 9/19 vehicle observations with local radar
  contrast and 0/19 with above-ground LiDAR returns. It is suggestive only.
- **Rain and snow (C10):** in our sampled recordings LiDAR kept strong car coverage at
  50–100 m: rain 95.62% (radar 42.40%), snow 99.40% (radar 60.84%). One recording per
  condition, no controlled comparison.

**Industry.**
- **Kodiak:** radar's ~4 mm wavelength lets it "pass through fog and rain" [K1].
- **Aurora:** imaging radar "penetrates dense fog and rain", and when dust obscures vision
  "the perception system shifts weight to imaging radar" [A1].
- **Weather is the operational bottleneck:** Aurora reports that "inclement weather of all
  types constrained our driverless operations in Texas roughly 40% of the time" in 2025.
  Driverless operation in "rain, fog, and heavy wind" was validated only in early 2026,
  with no mention of snow [A2].

**Reading.** Industry presents radar as *the* adverse-weather sensor. Our data partly
agrees (fog) and partly pulls the other way: LiDAR held up in our rain and snow samples,
where radar's coverage was the weaker one. Neither side has controlled evidence; the
companies give qualitative statements and our samples are small. It is still the most
useful row here for the client:
- weather, not range, is what is currently limiting real driverless trucking;
- "radar wins in bad weather" should be tested per condition rather than assumed, as C10
  already advises.

## 7. Models are tied to their sensors — **Tension** (unverified claim)

**Ours.**
- **Camera:** nuScenes-pretrained FCOS3D scored mAP 0.0046 on TruckScenes (EXP-0010).
- **LiDAR:** PointPillars was first fed TruckScenes' ~56°-pitched LiDAR unrectified and
  scored zero. After rotating the input into the upright frame the checkpoint expects, it
  scores mAP 0.0067 on that sensor and 0.0555 on the best-placed one, a level side LiDAR
  (car AP 0.20) (EXP-0024, PR #63, pending review).
- In both cases a public checkpoint is bound to the sensor layout it was trained on. The
  Bonn lecture makes the same point for LiDAR beam count and mounting.

**Industry.**
- **Waabi claims the opposite.** In July 2026 it reported that its driver, "trained
  exclusively on a Peterbilt 579", drove a Volvo VNL Autonomous truck with no new data,
  fine-tuning or engineering: "directly plug-and-play. Same stack. Same model." The CEO
  said the sensors were in "very different locations" on the two trucks [W2].
- **Caveats:** the report gives no metrics and no independent verification. It also does
  not say whether the sensor hardware was the same model or how calibration was handled
  [W2].
- **Waabi also cites sensor simulation** as how it can "integrate the latest technology
  quickly" [W1].
- No other company publishes cross-sensor transfer results.

**Reading.** This is a real tension, but the two claims are not the same claim.
- **What we tested:** *public* checkpoints trained on a *different dataset* (nuScenes),
  dropped onto a new truck. They scored near zero.
- **What Waabi claims:** its *own* stack moved between two of its *own* trucks.
- **Where they meet:** part of our LiDAR failure turned out to be fixable geometry. Once
  the tilted sensor was rotated into the frame the model expects, PointPillars went from
  zero to a nonzero score. A stack designed from the start to normalise sensor placement
  could plausibly do what Waabi describes.

So the honest conclusion is narrower than "models don't transfer":
- off-the-shelf public models don't transfer to a truck without at least correcting the
  sensor frame;
- one company claims, without published evidence, that a purpose-built stack can.

That claim would be worth asking Waabi or the client about.

## 8. Off-road terrain — **Can't tell**

**Ours.** The terrain model confuses low rocks (C11), tall grass (C12) and walls (C15)
with ground, and pooled scores can hide failures in other environments (C19).

**Industry.** Kodiak is the one trucking company running driverless off public roads:
**28 trucks** on Permian Basin oilfield lease roads for Atlas Energy as of 31 March 2026,
with 100 planned by mid-2027 [K3]. It publishes no terrain-perception detail. Its sensor
claims are about highway scenarios [K1, K2].

**Reading.** This is the area closest to Adrian's and Fabian's off-road interest and the
one industry says least about. Kodiak is the obvious company to ask.

---

## What to tell the client

1. **Our long-range finding matches industry's sensor choice:** distant geometry comes from
   (FMCW) LiDAR, and TruckDrive's sensors are the kind industry is deploying.
2. **Our "can't test 200–400 m recognition" result is shared by Torc's own published
   research.** Company range claims of 450–1,000 m are not backed by published benchmarks.
3. **There is no radar-first baseline in trucking.** 4D radar is on production trucks, but
   public models have not caught up. This is a gap in the field.
4. **Weather is the real operational limit for driverless trucks today,** and industry
   assumes radar covers it. Our small samples say that assumption should be tested per
   condition. This is the most useful open question to raise.
5. **Public models don't drop onto a new truck,** but one company (Waabi) claims its own
   stack does, without published evidence. Our PR #63 result shows part of the gap is
   fixable sensor-frame geometry.
6. **Off-road perception is effectively unpublished**, even by the one company running
   driverless trucks off-highway.

## Limits

- Written public sources only, read on 3 October 2026. Company statements are marketing
  and investor communications, not measurements, except TruckDrive [T2].
- No company was contacted. A missing claim is reported as *not found*, not *absent*.
- Our side inherits every limit in C01–C20: coverage is in-box sensor returns, not
  detection, and samples are small. Nothing here upgrades our findings.
- Waabi, Gatik and Plus publish little sensor detail, so they appear mainly in the appendix.

## Appendix: company snapshot

Context only; status as found on 3 October 2026.

| Company | Deployment status | Sensors (as published) | Source |
|---|---|---|---|
| **Aurora** | Driverless commercial freight on Texas–Arizona routes, including at night. Targets more than 200 driverless trucks by end-2026 | FirstLight FMCW LiDAR (450 m+), imaging radar, cameras | A1–A3 |
| **Kodiak** | 28 driverless trucks on Permian lease roads (31 Mar 2026). Public roads expected 2027 | Gen 5: 4× ZF 4D radar, 2× Luminar Iris + 2× Hesai LiDAR, 10 cameras | K1–K3 |
| **Torc** (Daimler Truck) | Driver-out validation; driverless commercial launch targeted 2027 (Dallas–Laredo first) | Aeva FMCW 4D LiDAR (to 500 m), Innoviz short-range LiDAR, radar, cameras. Built TruckDrive | T1–T3 |
| **Plus** (TRATON, International, IVECO, Hyundai) | Factory-built truck trials; driverless operation expected 2027 | Imaging radar, LiDAR, cameras; primary and secondary sensing systems | P1 |
| **Waabi** (Volvo) | Integrated with Volvo VNL Autonomous; claims zero-retraining transfer between truck models (Jul 2026) | LiDAR, radar, cameras; sensor simulation in Waabi World | W1, W2 |
| **Gatik** | Fully driverless commercial middle-mile operations (26- and 30-ft trucks) since Jan 2026; 10 revenue trucks at announcement, hundreds planned | Not found in the sources read | G1 |

## Sources

Dates are publication dates where shown; all were read on 3 October 2026.

- **A1** Aurora, *Seeing with Superhuman Clarity: the physics and architecture behind the Aurora Driver's perception system*, 23 Jan 2026. https://aurora.tech/newsroom/seeing-with-superhuman-clarity-the-physics-and-architecture-behind-the
- **A2** Aurora Innovation, Q4 2025 shareholder letter (8-K exhibit 99.1), 11 Feb 2026. https://ir.aurora.tech/sec-filings/all-sec-filings/content/0001828108-26-000014/finalaurora25q4sharehold.htm
- **A3** Aurora, *Meet "Fusion", the Aurora Driver's next-generation hardware*, 27 Aug 2021; and *The road never sleeps*, 7 Aug 2025. https://aurora.tech/newsroom/meet-fusion-the-aurora-drivers-next-generation · https://aurora.tech/newsroom/the-road-never-sleeps-auroras-trucks-go-driverless-day-and-night
- **K1** Kodiak, *Taking self-driving trucks to new dimensions with 4D radar*, 28 Sep 2021. https://kodiak.ai/news/taking-self-driving-trucks-to-new-dimensions-with-4d-radar
- **K2** Kodiak, *Kodiak introduces 5th generation autonomous truck*, 6 Apr 2023. https://kodiak.ai/news/kodiak-introduces-5th-generation-autonomous-truck
- **K3** Kodiak, *Atlas expands Kodiak-powered driverless fleet in the Permian* (2026). https://kodiak.ai/news/atlas-driverless-permian-expansion
- **T1** Daimler Truck North America, *Daimler Truck and Torc Robotics select Aeva to supply 4D LiDAR for series-production autonomous trucks*, Jan 2024. https://northamerica.daimlertruck.com/news-stories/2024/daimler-truck-and-torc-robotics-select-aeva-to-supply-advanced-4d-lidar-technology-for-series-production-autonomous-trucks
- **T2** Ghilotti et al., *TruckDrive: Long-Range Autonomous Highway Driving Dataset*, arXiv:2603.02413, Mar 2026; code at github.com/torc-ai/TruckDrive. https://arxiv.org/abs/2603.02413
- **T3** Autonomy Global, *Torc Robotics: steering truck autonomy into the mainstream*, 21 Jan 2026. https://www.autonomyglobal.co/torc-robotics-steering-truck-autonomy-into-the-mainstream-from-the-rubber-to-the-roof/ · Trucking Dive, *Torc Robotics opens first autonomous hub in Texas*. https://www.truckingdive.com/news/torc-robotics-opens-autonomous-hub-texas/749139/
- **P1** PlusAI, *SuperDrive* product page and *PlusAI brings NVIDIA Alpamayo foundation model to autonomous trucks*, 16 Mar 2026. https://www.plus.ai/solutions/superdrive/ · https://secure.businesswire.com/news/home/20260316111292/en/PlusAI-Brings-NVIDIA-Alpamayo-Foundation-Model-to-Autonomous-Trucks
- **W1** Waabi, *Introducing the Waabi Driver*, 15 Nov 2022. https://waabi.ai/insights/introducing-the-waabi-driver
- **W2** FreightWaves, *Waabi proves autonomous truck generalization with Volvo Autonomous Solutions*, 15 Jul 2026. https://www.freightwaves.com/news/autonomous-truck-generalization
- **G1** FreightWaves, *Gatik launches fully driverless commercial trucking operations*, 27 Jan 2026. https://www.freightwaves.com/news/gatik-fully-driverless-trucks
- **M1** Mobileye, *Mobileye's imaging radar takes the wheel*, 10 Jul 2024. https://www.mobileye.com/blog/mobileyes-imaging-radar-takes-the-wheel/
