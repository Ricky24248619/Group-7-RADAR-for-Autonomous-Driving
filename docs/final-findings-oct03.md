# Twenty LiDAR/radar and off-road findings

Analysis completed 3 October 2026; synthesis finalized 6 October 2026. This synthesis preserves the earlier findings and applies the reviewed consolidations. Each numbered finding answers a different practical question. Repeated classes, ranges and settings support the finding rather than increase the count. The D-identifiers remain stable when findings are cited elsewhere.

Road measurements are annotation-conditioned return presence, not recognition. Terrain measurements are returned-point or map diagnostics, not physical passability. Camera appearance benefits remain an untested question. The 31 GOOSE frames come from eight recording groups; their points/cells are not independent trials.

## Main messages

- **LiDAR provided more distant vehicle information in the tested TruckDrive clips.** At 200–400 m in the two follow-up clips, labelled vehicles contained LiDAR returns in 31 of 36 observations and radar returns in 12. This supports testing LiDAR for early information before a truck must respond. Stable recognition and stopping performance still need to be measured. See D01 and D03, with the supporting temporal evidence below.
- **Good radar coverage of trucks did not describe coverage of every important target.** In the nearby TruckScenes samples, radar support was 99.12% for trucks, 67.66% for adults and 39.00% for cones. The class samples differ, so these are coverage observations rather than proof of a size or material effect. Separate target checks matter when evaluating people and work-zone objects. See D02 and D22.
- **Off-road sensing needs correct terrain interpretation as well as recorded points.** The tested GOOSE model sometimes labelled hazards as ground and candidate ground as obstacles. Even a map built from correct labels could discard a minority hazard under a majority-ground rule. A future evaluation should check these error directions and the map conversion separately. See D05, D06, D12 and D13.
- **A ground label alone does not describe the space available to a vehicle.** The selected terrain maps had unobserved areas, obstacle returns at different vertical levels and ground patches with different shapes. A wider footprint also rejected many positions that passed a single-cell check. These diagnostics identify information to preserve for navigation; they do not certify clearance or a usable route. See D18–D21.
- **Future model upgrades need tests that expose regressions and match the intended use.** More context improved six of seven tested terrain examples, worsened one and increased summed logged batch time by about 28%. Pooled scores hid a weak recording, and important conditions such as water remain unchecked. Camera appearance is a proposed surface-classification study. See D07, D08, D14 and D15; D04, D09, D10 and D23 explain comparison and evaluation limits.

These five messages summarize the twenty findings; they do not add to their count. The detailed sections retain the measured units, selected cohorts, evidence links and limits needed to interpret each conclusion.

## 1. D01 — LiDAR supplied data from distant vehicles more often than radar in the TruckDrive clips analysed.

At 200–400 m in the two new clips, LiDAR supported 31 of 36 labelled vehicle observations (86.11%); radar supported 12 (33.33%). These observations came from 18 tracks. Earlier clips showed the same ordering. Support means at least one return inside a labelled box, not correct vehicle recognition.

**Practical use:** Specify the required sensing horizon before choosing a sensor or model. Study whether the distant returns become stable recognition before the response deadline.

**Limit:** Two new clips, 36 repeated observations from 18 tracks and LiDAR-conditioned annotations. No detector accuracy, warning time, stopping performance or universal sensor ranking is measured.

**Evidence:** [matched_track_summary.csv](../docs/evidence/missing-support/matched_track_summary.csv); [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [truckdrive_holdout_support.csv](../results/evidence/sprint-followup-oct01/truckdrive_holdout_support.csv).

## 2. D02 — Strong radar coverage of nearby trucks did not carry over to people and roadwork objects.

Within 0–25 m in TruckScenes, radar supported 336 of 339 truck observations (99.12%); 136 of 201 adult-pedestrian observations (67.66%); 39 of 100 cone observations (39.00%). Class cohorts differ; this does not isolate material, size or visibility as the cause.

**Practical use:** Include people, bicycles and work-zone objects in acceptance tests, rather than accepting a truck-dominated average.

**Limit:** Different class cohorts, repeated tracks and LiDAR-conditioned labels; all six sensors per modality. These percentages are in-box return presence, not object detection recall or collision avoidance.

**Evidence:** [class_range_support.csv](../results/evidence/sprint-followup-oct01/class_range_support.csv).

## 3. D03 — Radar sometimes supplied object evidence where LiDAR had none.

One radar-only observation in the new distant-vehicle sample increased coverage by either sensor from 86.11% to 88.89%. Earlier clips also contained radar-only observations. Timing and box definitions affect these counts.

**Practical use:** Inspect correctly aligned radar-only episodes before deciding whether radar is worth adding to a LiDAR system. Test recognition benefit separately.

**Limit:** One new radar-only observation is not one additional independently detected vehicle. Geometric union is not fusion accuracy; unannotated objects remain outside this assessment.

**Evidence:** [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [truckdrive_holdout_support.csv](../results/evidence/sprint-followup-oct01/truckdrive_holdout_support.csv).

## 4. D04 — The weather samples do not establish a sensor that wins in every condition.

In the 50–75 m exact-footprint fog subset, strict radar contrast appeared in 9 of 19 observations and above-ground LiDAR support in none. In the separate 50–100 m TruckScenes car samples, rain had 776 observations with LiDAR support 95.62% and radar support 42.40%; snow had 498 observations with LiDAR support 99.40% and radar support 60.84%. These are different recordings and endpoints.

**Practical use:** Use matched clear/adverse recordings from the intended sensor platform before claiming weather capability.

**Limit:** The fog pilot has four tracks overall and no clear-weather control. Radar contrast and LiDAR point presence are different measurements. Rain and snow each use one different recording, with different targets.

**Evidence:** [observations.csv](../docs/evidence/radiate-fog/observations.csv); [radiate-fog-pilot.md](../docs/radiate-fog-pilot.md); [weather_support.csv](../results/evidence/sprint-followup-oct01/weather_support.csv).

## 5. D05 — LiDAR returned terrain points that the tested off-road model sometimes labelled incorrectly.

The selected GOOSE results include grass predicted as ground, low rocks confused with ground, and particular wall and bicycle classification failures. At patch 128, 48.94% of tall-grass points across seven selected frames were called ground. Several other cases are confined to one recording.

**Practical use:** Test rigid hazards and uncertain vegetation separately, and record how often they are labelled as ground.

**Limit:** GOOSE is a LiDAR terrain study, not a paired radar/LiDAR comparison. Scores refer to returned points; selected wall/bicycle cases are limited, and the seven-frame follow-up contains no rocks. Physical traversability and whole-object detection are unmeasured.

**Evidence:** [nearest_ground_diagnostic.csv](../docs/evidence/goose-failure-causes/nearest_ground_diagnostic.csv); [goose-failure-causes.md](../docs/goose-failure-causes.md); [fine_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/fine_class_comparison.csv); [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv).

## 6. D06 — Calling a surface ground did not establish that its surface category was correct.

At context setting 128 across seven selected GOOSE frames, gravel had 16,171 of 16,200 points called ground (99.82%), but 80.07% had the correct natural-ground or artificial-ground category; asphalt had 26,438 of 26,593 points called ground (99.42%), but 89.78% had the correct natural-ground or artificial-ground category.

**Practical use:** Decide which surface distinctions the application needs. Investigate paired camera images and labels for texture/appearance information, then test whether that improves the required categories.

**Limit:** Eight-category returned-point predictions, not a 64-material classifier. No traction, soil strength, roughness, water depth or physical passability measurement is supplied by this result.

**Evidence:** [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv).

## 7. D07 — More context improved most tested terrain examples, but cost more processing and made one example worse.

In seven matched GOOSE frames, context 128 improved overall point-category correctness in six and worsened the flight frame from 86.37% to 83.69%. Summed logged batch time rose from 93.250 to 119.217 seconds (about 28%). No new GPU run was performed in P5.

**Practical use:** Accept a setting only after checking difficult examples and resource cost together. Preserve regressions when an average improves.

**Limit:** Seven selected frames from existing recordings and a bounded context intervention. No full validation, external transfer, production deadline or safe navigation performance is established.

**Evidence:** [frame_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/frame_comparison.csv); [manifest.json](../results/evidence/sprint-followup-oct01/terrain/manifest.json); [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv); [saved_model_cost.csv](../results/evidence/p3-p4-oct03/saved_model_cost.csv).

## 8. D08 — A strong overall terrain score hid a weak result in a different recording.

Pooled soil correctness was 99.53%, dominated by field-path points. Only 7.92% of the 240 soil points in the selected rainy frame had the correct broad category. The samples are uneven and the rainy subset is small. In that rainy frame, 224 of 240 soil points were still called ground; the 7.92% result concerns the finer broad category.

**Practical use:** Report results by relevant recording and condition alongside pooled scores.

**Limit:** One selected frame per recording, uneven points and only 240 soil points in the rainy case. This does not establish a causal rain penalty or performance across all wet terrain.

**Evidence:** [fine_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/fine_class_comparison.csv); [pooled_class_comparison.csv](../results/evidence/sprint-followup-oct01/terrain/pooled_class_comparison.csv).

## 9. D09 — Correcting sensor timing changed how much object evidence appeared to be missing.

On the same 25,117 TruckScenes observations, correcting individual LiDAR point times reduced apparent radar-only observations from 185 to 39. The recount does not reproduce every publisher LiDAR count, so that remaining discrepancy stays visible.

**Practical use:** Verify acquisition timing, motion correction and box conventions before attributing a difference to the hardware.

**Limit:** The corrected recount does not reproduce all publisher LiDAR counts. Exact boxes and expanded boxes answer sensitivity questions; neither result is detector or fusion accuracy.

**Evidence:** [client-comparison-brief.md](../docs/client-comparison-brief.md); [paired-support-verification.json](../docs/evidence/truckscenes/paired-support-verification.json).

## 10. D10 — The inspected software setup could not compare recognition of the distant vehicles.

The inspected pretrained radar/LiDAR model pair accepts inputs only to about 70 m. It therefore cannot test recognition of the 200–400 m vehicles. This is a limitation of the inspected setup, not proof that no suitable model exists.

**Practical use:** Check the input crop, checkpoint features and evaluator before selecting software for long-range recognition.

**Limit:** This is an audit of particular inspected releases and checkpoints dated 24 September/1 October, not proof that no long-range model exists or a new audit of all current models. No new inference is performed.

**Evidence:** [detector-compatibility-decision.md](../docs/detector-compatibility-decision.md); [release-documents.json](../results/evidence/sprint-followup-oct01/models/release-documents.json).

## 11. D12 — The terrain model also rejects some candidate ground as obstacles

Across the original 24 and seven follow-up GOOSE frames at context 64, 2,853 of 1,312,878 candidate-firm-surface points were assigned a blocked category. This is the opposite error direction from hazards being labelled ground. The associated saved predictions were reused, not rerun.

**Practical use:** Track candidate-ground-to-obstacle errors as well as hazard-to-ground errors in future perception acceptance tests.

**Limit:** Provisional semantic screening, repeated point observations and selected frames. Candidate firm surface is not proof of physical/legal route usability; actual planner behaviour and traversal were not measured.

**Evidence:** [terrain_directional_frames.csv](../results/evidence/p3-p4-oct03/terrain_directional_frames.csv).

## 12. D13 — A majority-ground terrain map can hide a hazard even with correct input labels

Among 4,232 half-metre cell observations containing both candidate firm terrain and a rigid/person/vehicle hazard in the 31 selected GOOSE frames, 672 (15.88%) had a ground-truth firm majority. A majority rule would discard the minority hazard even if every input label were correct.

**Practical use:** Retain hazard evidence when converting point labels into a terrain map; a majority ground label can erase a minority hazard.

**Limit:** Oracle semantic diagnostic, not a deployed map. XY cells are vertical columns and can contain overhead geometry. Hazard-presence policy is provisional; these are not collision labels or independent objects.

**Evidence:** [terrain_cells.csv](../results/evidence/p3-p4-oct03/terrain_cells.csv).

## 13. D14 — Important off-road conditions remain unchecked, including water.

The inspected WildScenes benchmark maps native water to its ignored label. Our five preselected WildScenes frames contain 1,176 log points, 24 rock points, one mud point and no water points. The 31 selected GOOSE frames also contain no water points. These are sample limitations, not proof that the full datasets lack those conditions.

**Practical use:** Select adequate water, mud, rock and other mission-relevant examples, and inspect which classes the benchmark actually scores.

**Limit:** Author benchmark configuration and selected samples only. No water performance, water depth, transfer inference or traversal outcome was measured.

**Evidence:** [temporal-terrain-findings-oct03.md](../docs/temporal-terrain-findings-oct03.md); [wildscenes_taxonomy.csv](../results/evidence/p3-p4-oct03/wildscenes_taxonomy.csv); [wildscenes_class_range.csv](../results/evidence/p3-p4-oct03/wildscenes_class_range.csv).

## 14. D15 — Independent terrain data needs an input compatibility check before testing the existing model

The selected WildScenes labelled binary clouds decode as XYZ only, while the inspected GOOSE model input uses XYZ and intensity. Native grass categories also lack the GOOSE short/tall-grass distinction, and other-terrain/other-object require explicit translation. A compatible model transfer was not performed.

**Practical use:** Translate native categories explicitly and verify required input features before a transfer study.

**Limit:** Facts about selected exports and the inspected checkpoint, not every export/model. No transfer accuracy, intensity ablation or missing-feature workaround was measured.

**Evidence:** [wildscenes_taxonomy.csv](../results/evidence/p3-p4-oct03/wildscenes_taxonomy.csv); [terrain_manifest.json](../results/evidence/p3-p4-oct03/terrain_manifest.json).

## 15. D18 — Nearby maps contained substantial gaps with no recorded points.

Across 31 GOOSE scans, 105,904 of 243,660 pooled half-metre cell observations in a 25m disc had no return (43.46%). At one-metre resolution, 16,654 of 61,256 were unobserved (27.19%). These are repeated map-cell observations, not independent square metres.

**Practical use:** Preserve unknown areas in terrain outputs and evaluate how a future system obtains information before using them. An unlabelled gap should not silently become candidate ground.

**Limit:** Fixed disc around selected scans; missing cells may reflect sampling, geometry or occlusion. No clear-route ground truth, sensor failure rate or visibility cause was measured.

**Evidence:** [vehicle_footprint.csv](../results/evidence/p5-oct03/vehicle_footprint.csv).

## 16. D19 — Obstacle returns occurred at different vertical levels, which a flat map does not preserve.

Of 609,511 rigid-hazard points within 25m, 242,801 had a labelled candidate-ground reference within 1m in XY; 366,710 did not. Among the resolved points, 64,920 sat at least 2m above the reference, while 160,235 sat 0.2-2m above it. Vegetation had substantial high returns as well. The height-columns table retains mixed and unresolved columns.

**Practical use:** Retain vertical geometry and uncertainty when studying clearance. Validate local ground, gravity alignment and actual vehicle dimensions before turning these diagnostics into a collision decision.

**Limit:** Nearest-point sensor-frame delta-z is not a validated object height. Lateral separation, slope and cover can change it; unresolved references are retained. No column was declared safely traversable.

**Evidence:** [ground_reference.csv](../results/evidence/p5-oct03/ground_reference.csv); [relative_height.csv](../results/evidence/p5-oct03/relative_height.csv); [height_columns.csv](../results/evidence/p5-oct03/height_columns.csv).

## 17. D20 — Ground-labelled patches had different local shapes, and fine patches often lacked enough support for a shape check.

At 0.5m resolution, 28,958 of 70,807 candidate-ground cell observations met the fixed plane-fit criteria. Their point-to-plane RMS was <=2cm in 20,920, 2-5cm in 7,244 and >5cm in 794. Another 20,927 cells had fewer than five points and 20,922 were too line-like. At 1m, 15,243 of 25,213 met the criteria.

**Practical use:** Use geometry alongside surface categories, and report when shape estimates lack point support. A future model should not turn a semantic ground label into a smoothness or traction guarantee.

**Limit:** Orthogonal plane RMS is a local shape diagnostic, not validated roughness, grade, grip or passability. Eligibility thresholds are analysis choices. Covariance planes do not require gravity alignment, but slope claims would.

**Evidence:** [surface_shape.csv](../results/evidence/p5-oct03/surface_shape.csv).

## 18. D21 — Checking a wider footprint removed many positions that passed a single-cell terrain check.

On 0.5m maps, 61,210 centre-cell observations contained candidate ground and no policy hazard. Requiring complete support for a 1.5m square retained 23,598 (38.55%); a 2.5m square retained 14,371 (23.48%). The 2.5m check lost 11,363 centres to nearby hazards and 35,476 to missing/uncertain support. At 1m resolution, the 1.5m and 2.5m requests both quantise conservatively to a 3m square.

**Practical use:** Evaluate the intended body footprint and supporting terrain around it. Keep insufficient evidence separate from an observed obstacle, and choose a grid fine enough for the required clearance distinction.

**Limit:** Diagnostic square footprints and an oracle semantic policy, not actual vehicle dimensions, steering, wheel contact or route planning. No retained footprint is certified traversable.

**Evidence:** [vehicle_footprint.csv](../results/evidence/p5-oct03/vehicle_footprint.csv).

## 19. D22 — Poor camera visibility did not automatically mean missing LiDAR evidence.

TruckScenes camera visibility level 1 means 0-40% visible in the panoramic camera view. Of 8,125 such exact-box observations, 7,730 had >=1 LiDAR return (95.14%) and 2,196 had >=1 radar return (27.03%). At >=3 returns, the counts were 6,422 and 758. The saved table separates native classes and ranges.

**Practical use:** Assess each modality using its own evidence. Use camera appearance as a potential complement while avoiding the assumption that camera visibility labels describe LiDAR or radar availability.

**Limit:** Annotation-conditioned, repeated object observations with different class/range cohorts. Camera level 1 is partial visibility, not complete invisibility. No through-object sensing, camera-model accuracy or causal occlusion advantage is established.

**Evidence:** [camera_visibility.csv](../results/evidence/p5-oct03/camera_visibility.csv).

## 20. D23 — Radar contrast appeared in both labelled vehicle footprints and unlabelled comparison regions.

In the 17-frame RADIATE fog sample, the loose contrast rule passed 31 of 39 target-footprint observations and 32 of 117 rotated comparison observations. The stricter gap-20 rule passed 17 of 39 and 8 of 117. Two target footprints had three-sample strict runs; no comparison footprint did. Under the loose rule, two comparison footprints had such runs.

**Practical use:** Test background contrast and persistence before equating a radar response with a recognised target. Keep suitable counterexamples in future perception evaluation.

**Limit:** Four labelled tracks and 12 rotated comparison footprints, with repeated frames. Comparison regions are unlabelled, not verified empty. These counts are not false-positive rates, precision or recall; temporal rules are analysis choices.

**Evidence:** [fog_background.csv](../results/evidence/p5-oct03/fog_background.csv).

## Supporting temporal evidence

In the TruckDrive forward sector (within 15 degrees of the sensor's forward direction), 104 of 107 labelled vehicle tracks had LiDAR support at least once, while 74 had support in three consecutive sampled observations. Radar supported 101 at least once and 71 for three samples. With at least three returns required per observation, the persistent counts were 72 for LiDAR and 48 for radar.

The first three-sample confirmation was at 200–400 m for 30 LiDAR tracks and 26 radar tracks under the one-return rule. Under the three-return rule, those counts were 28 and four. These are first confirmation ranges across each track's selected forward observations, not a matched cohort proving a recognition advantage. Median time from the start of the confirming run to its third sample was approximately one second, because these data were sampled roughly every half second.

**Use:** define the required duration and density of evidence when studying a truck's information horizon. A future detector or tracker should be evaluated on stable recognition before the required response, rather than point presence alone. The three-sample rule is an analysis choice; its delay is not the sensor's native latency or a measured braking requirement. A forward angle is a route proxy, not proof the object lies in the truck's path.

Sources: [setting summaries](../results/evidence/p3-p4-oct03/road_summary.csv), [track evidence, gzip CSV](../results/evidence/p3-p4-oct03/road_tracks.csv.gz), [sampled episodes, gzip CSV](../results/evidence/p3-p4-oct03/road_episodes.csv.gz).

This is retained beneath distance and complementary sensing; it does not count as a twenty-first headline.

## Additional off-road data

The pinned RELLIS-3D author release offers paired camera/LiDAR data, separate water/puddle/mud/rubble categories, calibration and pose files. This project audited source metadata only: no RELLIS raw frames or model inference were acquired. Its Velodyne labels are transferred from Ouster, and the inspected benchmark ignores several native classes. These facts matter before selecting a fair follow-up comparison; they do not establish a camera benefit or a sensor winner.

[Pinned dataset facts and source hashes](../results/evidence/p5-oct03/additional_dataset_audit.json). The author README states CC BY-NC-SA 3.0; keep intended reuse eligibility explicit.

## Reproduction

Use the existing dataset roots and saved predictions identified by the source manifests. NumPy and the existing isolated SciPy environment are required for the terrain reference search; no new model inference is triggered.

```text
python scripts/analyse_p5_navigation.py --goose-root <GOOSE-3D-val> --original-predictions <stratified24-result> --followup-predictions <followup7-runs> --truckscenes-root <TruckScenes-root> --output-dir <new-output-directory>
```

[Methods, source hashes and output hashes](../results/evidence/p5-oct03/manifest.json). Ground-reference cutoffs are 1/2m; maps and surface planes use 0.5/1m cells; body checks use conservative cell-centred square footprints. At 1m cells, requested widths 1.5m and 2.5m quantise to the same 3m footprint, so these requests cannot be distinguished at that resolution.

Credit: GOOSE, MAN TruckScenes, TruckDrive, RADIATE, CSIRO WildScenes and RELLIS-3D authors. All raw data, reports and private planning remain outside this findings publication.
