# Ten consolidated LiDAR/radar and terrain findings

2 October 2026. This adds plain explanations to the existing evidence; no new experiment is reported. The original [twenty evidence rows](client-level-conclusions-oct01.md), detailed studies and additional-dataset analyses remain intact. Different classes, ranges and replications support a conclusion rather than automatically creating another headline.

Coverage means at least one recorded return inside a labelled box. GOOSE scores describe returned-point categories. Neither endpoint is detector accuracy, physical traversability or safe-driving performance. The terrain strand has no paired radar comparison.

The [source manifest](../results/evidence/p2-oct02/findings_sources.json) records the source revision, original-ID mapping, file hashes and checks of selected counts. These ten messages have different evidence strengths.

## D01 — LiDAR supplied data from distant vehicles more often than radar in the TruckDrive clips analysed.

At 200–400 m, distant labelled vehicles more often contained LiDAR returns than radar returns. This establishes a difference in recorded object coverage for these sensor configurations. It does not show that either system correctly recognised the vehicle.

**Evidence:** At 200–400 m in the two new clips, LiDAR supported 31 of 36 labelled vehicle observations (86.11%); radar supported 12 (33.33%). These observations came from 18 tracks. Earlier clips showed the same ordering. Support means at least one return inside a labelled box, not correct vehicle recognition.

**Why it matters:** Define how far ahead a truck must receive usable information before choosing a sensor and perception setup. The long-range LiDAR coverage gives a reason to test it as an early-warning input.

**Limit:** Two new clips, 36 repeated observations from 18 tracks and LiDAR-conditioned annotations. No detector accuracy, warning time, stopping performance or universal sensor ranking is measured.

**Basis:** Measured within selected clips; unit: labelled vehicle-time observation.

**Sources:** [matched_track_summary.csv](../docs/evidence/missing-support/matched_track_summary.csv); [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [truckdrive_holdout_support.csv](../results/evidence/sprint-followup-oct01/truckdrive_holdout_support.csv).

## D02 — Strong radar coverage of nearby trucks did not carry over to people and roadwork objects.

Radar returned data inside almost all nearby truck boxes, but less often inside pedestrian, bicycle, cone and sign boxes. These target categories therefore need their own coverage checks. The results do not isolate size, material or visibility as the cause.

**Evidence:** Within 0–25 m in TruckScenes, radar supported 336 of 339 truck observations (99.12%); 136 of 201 adult-pedestrian observations (67.66%); 39 of 100 cone observations (39.00%). Class cohorts differ; this does not isolate material, size or visibility as the cause.

**Why it matters:** Specify the target types the system must handle, and verify vulnerable people and small work-zone objects alongside large vehicles.

**Limit:** Different class cohorts, repeated tracks and LiDAR-conditioned labels; all six sensors per modality. These percentages are in-box return presence, not object detection recall or collision avoidance.

**Basis:** Measured within sampled target groups; unit: labelled object-time observation.

**Sources:** [class_range_support.csv](../results/evidence/sprint-followup-oct01/class_range_support.csv).

## D03 — Radar sometimes supplied object evidence where LiDAR had none.

In the new distant sample, one observation had radar returns but no LiDAR returns inside the same labelled box. Counting support from either sensor added that observation. The extra return is evidence to investigate, not proof that a fused system detects more vehicles.

**Evidence:** One radar-only observation in the new distant-vehicle sample increased coverage by either sensor from 86.11% to 88.89%. Earlier clips also contained radar-only observations. Timing and box definitions affect these counts.

**Why it matters:** Evaluate radar's complementary contribution before rejecting it because its average coverage is lower.

**Limit:** One new radar-only observation is not one additional independently detected vehicle. Geometric union is not fusion accuracy; unannotated objects remain outside this assessment.

**Basis:** Measured small complementary contribution; unit: labelled vehicle-time observation.

**Sources:** [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [truckdrive_holdout_support.csv](../results/evidence/sprint-followup-oct01/truckdrive_holdout_support.csv).

## D04 — The weather samples do not establish a sensor that wins in every condition.

The fog pilot showed radar contrast in some vehicle footprints with no above-ground LiDAR returns. LiDAR nevertheless had strong car coverage in the separate rain and snow recordings. Those observations answer different limited questions and cannot establish a weather-caused sensor ranking.

**Evidence:** In the 50–75 m exact-footprint fog subset, strict radar contrast appeared in 9 of 19 observations and above-ground LiDAR support in none. In the separate 50–100 m TruckScenes car samples, rain had 776 observations with LiDAR support 95.62% and radar support 42.40%; snow had 498 observations with LiDAR support 99.40% and radar support 60.84%. These are different recordings and endpoints.

**Why it matters:** Define the weather and visibility conditions that need validation for the intended operation, including what backup evidence must remain available.

**Limit:** The fog pilot has four tracks overall and no clear-weather control. Radar contrast and LiDAR point presence are different measurements. Rain and snow each use one different recording, with different targets.

**Basis:** Mixed endpoints; no causal weather comparison; unit: footprint contrast or in-box support, reported separately.

**Sources:** [observations.csv](../docs/evidence/radiate-fog/observations.csv); [radiate-fog-pilot.md](../docs/radiate-fog-pilot.md); [weather_support.csv](../results/evidence/sprint-followup-oct01/weather_support.csv).

## D05 — LiDAR returned terrain points that the tested off-road model sometimes labelled incorrectly.

Visible grass and rock surfaces could be labelled ground, and some other surfaces received the wrong broad category. The sensor supplied points; the recorded classification still failed. This explains why seeing terrain and correctly interpreting it are separate steps.

**Evidence:** The selected GOOSE results include grass predicted as ground, low rocks confused with ground, and particular wall and bicycle classification failures. At patch 128, 48.94% of tall-grass points across seven selected frames were called ground. Several other cases are confined to one recording.

**Why it matters:** Validate the labels used to judge candidate off-road routes, especially rigid hazards called ground and vegetation whose underlying surface is uncertain.

**Limit:** GOOSE is a LiDAR terrain study, not a paired radar/LiDAR comparison. Scores refer to returned points; selected wall/bicycle cases are limited, and the seven-frame follow-up contains no rocks. Physical traversability and whole-object detection are unmeasured.

**Basis:** Selected point-classification failures; unit: returned labelled point.

**Sources:** [nearest_ground_diagnostic.csv](../docs/evidence/goose-failure-causes/nearest_ground_diagnostic.csv); [goose-failure-causes.md](../docs/goose-failure-causes.md); [fine_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/fine_class_comparison.csv); [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv).

## D06 — Calling a surface ground did not establish that its surface category was correct.

The model labelled nearly all inspected gravel and asphalt points as ground, while its natural-ground versus artificial-ground category was less accurate. Its eight broad categories also do not describe every detailed material or physical property.

**Evidence:** At context setting 128 across seven selected GOOSE frames, gravel had 16,171 of 16,200 points called ground (99.82%), but 80.07% had the correct natural-ground or artificial-ground category; asphalt had 26,438 of 26,593 points called ground (99.42%), but 89.78% had the correct natural-ground or artificial-ground category.

**Why it matters:** Decide whether the application needs only a broad surface label or additional information such as geometry, surface condition or vehicle clearance.

**Limit:** Eight-category returned-point predictions, not a 64-material classifier. No traction, soil strength, roughness, water depth or physical passability measurement is supplied by this result.

**Basis:** Measured distinction between broad and finer categories; unit: returned labelled point.

**Sources:** [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv).

## D07 — Giving the terrain model more context helped most tested frames but made one worse.

With the same checkpoint and controlled settings, the larger context setting improved correctness in six selected frames and reduced it in the flight frame. An improved average therefore did not mean an improvement everywhere.

**Evidence:** Changing context from 64 to 128 improved overall point-category correctness in six of seven selected GOOSE frames. The flight frame fell from 86.37% to 83.69%. The repeated baseline's saved prediction hashes were identical. These are selected diagnostic frames, not the full benchmark.

**Why it matters:** Check candidate settings on important difficult scenes and resource constraints before adopting a configuration.

**Limit:** Seven selected frames from existing recordings and a bounded context intervention. No full validation, external transfer, production deadline or safe navigation performance is established.

**Basis:** Bounded intervention; baseline repeat identical; unit: selected frame and returned labelled point.

**Sources:** [frame_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/frame_comparison.csv); [manifest.json](../results/evidence/sprint-followup-oct01/terrain/manifest.json); [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv).

## D08 — A strong overall terrain score hid a weak result in a different recording.

The pooled soil score was dominated by a field-path frame. Soil points in the selected rainy frame had much lower correct-category performance. The pooled number and the difficult case are both valid descriptions, but they answer different questions.

**Evidence:** Pooled soil correctness was 99.53%, dominated by field-path points. Only 7.92% of the 240 soil points in the selected rainy frame had the correct broad category. The samples are uneven and the rainy subset is small. In that rainy frame, 224 of 240 soil points were still called ground; the 7.92% result concerns the finer broad category.

**Why it matters:** Require results for relevant operating environments instead of relying on a single overall score.

**Limit:** One selected frame per recording, uneven points and only 240 soil points in the rainy case. This does not establish a causal rain penalty or performance across all wet terrain.

**Basis:** Measured aggregation effect; cause unresolved; unit: returned labelled point by recording.

**Sources:** [fine_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/fine_class_comparison.csv); [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv).

## D09 — Correcting sensor timing changed how much object evidence appeared to be missing.

On the same TruckScenes observations, correcting LiDAR point times reduced apparent radar-only support from 185 observations to 39. Some apparent sensor complementarity was therefore a preprocessing effect.

**Evidence:** On the same 25,117 TruckScenes observations, correcting individual LiDAR point times reduced apparent radar-only observations from 185 to 39. The recount does not reproduce every publisher LiDAR count, so that remaining discrepancy stays visible.

**Why it matters:** Check alignment and motion handling before making a hardware or sensor-combination decision from apparent coverage gaps.

**Limit:** The corrected recount does not reproduce all publisher LiDAR counts. Exact boxes and expanded boxes answer sensitivity questions; neither result is detector or fusion accuracy.

**Basis:** Measured timing effect with remaining recount limitation; unit: same matched object-time observation.

**Sources:** [client-comparison-brief.md](../docs/client-comparison-brief.md); [paired-support-verification.json](../docs/evidence/truckscenes/paired-support-verification.json).

## D10 — The inspected software setup could not compare recognition of the distant vehicles.

The inspected radar/LiDAR checkpoints accept inputs only to about 70 m. The 200–400 m vehicle centres therefore lie outside their input region. Running them would mix sensor performance with input cropping and cross-dataset compatibility.

**Evidence:** The inspected pretrained radar/LiDAR model pair accepts inputs only to about 70 m. It therefore cannot test recognition of the 200–400 m vehicles. This is a limitation of the inspected setup, not proof that no suitable model exists.

**Why it matters:** Specify the useful range of the complete perception setup and verify that the evaluator, features and available model inputs cover it.

**Limit:** This is an audit of particular inspected releases and checkpoints dated 24 September/1 October, not proof that no long-range model exists or a new audit of all current models. No new inference is performed.

**Basis:** Verified limitation of inspected setup; unit: checkpoint input-region compatibility.

**Sources:** [detector-compatibility-decision.md](../docs/detector-compatibility-decision.md); [release-documents.json](../results/evidence/sprint-followup-oct01/models/release-documents.json).

## Retained evidence and distinct questions

| Current message | Original evidence rows | Distinct decision |
|---|---|---|
| D01 | C01, C07 | Required forward sensing horizon |
| D02 | C02, C03, C04, C05, C06 | Target-specific coverage requirements |
| D03 | C08 | Value of complementary sensing |
| D04 | C09, C10 | Weather-qualified operating conditions |
| D05 | C11, C12, C15, C16, C18 | Consequential off-road classification failures |
| D06 | C14 | Information needed beyond a ground label |
| D07 | C13, C17 | Configuration acceptance with regressions visible |
| D08 | C19 | Evidence for transfer to the operating environment |
| D09 | Earlier paired timing study | Validity of the sensor comparison |
| D10 | C20 | End-to-end range and comparison feasibility |

The source checks validate the quoted counts and provenance, not the causal explanation or a complete benchmark. The local client explanation and study register are separate from this public findings summary.
