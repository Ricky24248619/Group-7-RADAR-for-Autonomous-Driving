# Dataset findings — 1 October 2026

32 supported findings across TruckScenes, TruckDrive, GOOSE, STONE, RADIATE, Boreas and WildScenes.

These are research findings with denominators and limits. Sensor support means recorded returns inside known annotations; it is not detector recall. GOOSE scores concern labelled returned points. STONE results are conditional on unresolved extrinsics. The weather pilot is not a controlled causal test.

The first 28 findings consolidate and recompute existing project evidence. F29–F32 add a new bounded Boreas sample and a WildScenes metadata audit. New reanalysis also profiles equal-scene TruckScenes support and its radar-only class composition. No new GPU inference or full benchmark was run in this update. The finding count is not evidence of twelve weeks of labour.

See [additional dataset selection and LiDAR/radar evidence](additional-dataset-findings-oct01.md). Reproduction: `python scripts/analyse_findings_oct01.py`, then `python scripts/render_findings_oct01.py`; the additional-data acquisition/audit command is documented in EXP-0029.

## F01 — LiDAR has substantially more distant object support in this subset

**Dataset / evidence:** TruckScenes · recomputed existing project evidence

At 150–400 m, 2,309 annotated observations have 91.73% LiDAR support and 15.16% radar support. The actual maximum object centre is 229.42 m.

**Implication:** Retain LiDAR as the stronger geometric reference for these labelled distant objects.

**Limit:** At least one in-box return; LiDAR-conditioned labels; recorded radar boundary near 190 m; not detector recall or a universal ranking.

**Sources:** [object_counts.csv](../docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv)

## F02 — LiDAR scan motion changes the apparent benefit of radar

**Dataset / evidence:** TruckScenes · recomputed existing project evidence

On the same 25,117 observations, individual-point ego-motion correction reduces radar-only support from 185 to 39.

**Implication:** Deskew before attributing complementary detections to a sensor.

**Limit:** Ego correction only; moving targets and cabin motion remain unresolved.

**Sources:** [object_counts.csv](../docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv); [object_counts.csv](../docs/evidence/truckscenes/paired-all-sensor-support/object_counts.csv)

## F03 — The residual radar-only result depends on box boundaries

**Dataset / evidence:** TruckScenes · recomputed existing project evidence

Expanding every box face by 0.5 m reduces radar-only observations from 39 to 3 over the same 25,117 objects-at-time observations.

**Implication:** Inspect geometry and residual timing before assigning a physical cause to these cases.

**Limit:** Expanded boxes admit background returns and are a sensitivity test, not corrected ground truth.

**Sources:** [object_counts.csv](../docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv)

## F04 — Radar support varies substantially by class even nearby

**Dataset / evidence:** TruckScenes · recomputed existing project evidence

At 0–25 m, radar supports 99.12% of 339 truck observations, 67.66% of 201 adult-pedestrian observations and 39.00% of 100 cone observations.

**Implication:** Report vulnerable road users and small obstacles separately from large vehicles.

**Limit:** Class, view, distance within the band and occlusion differ; reflectivity is not isolated; repeated observations.

**Sources:** [object_counts.csv](../docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv)

## F05 — Changing car identities alone does not explain the range decline

**Dataset / evidence:** TruckScenes · recomputed existing project evidence

For the same 237 car tracks, equal-track radar support falls from 79.95% at 0–50 m to 52.46% at 50–100 m. LiDAR changes from 99.81% to 98.55%.

**Implication:** Follow the same tracks across ranges rather than relying only on a changing pooled population.

**Limit:** Viewpoint, occlusion and target motion are still uncontrolled.

**Sources:** [matched_track_summary.csv](../docs/evidence/missing-support/matched_track_summary.csv)

## F06 — The distant support difference persists when scenes get equal weight

**Dataset / evidence:** TruckScenes · recomputed existing project evidence

At 150–400 m, equal weighting of 9 eligible scenes gives a LiDAR-minus-radar difference of 73.11 percentage points; the smallest scene difference is 57.14 points.

**Implication:** The pooled result is not explained solely by one scene having many labels.

**Limit:** Descriptive scene sensitivity; selected mini scenes and radar range truncation remain; no population confidence interval.

**Sources:** [object_counts.csv](../docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv)

## F07 — The few radar-only observations mostly concern cars

**Dataset / evidence:** TruckScenes · recomputed existing project evidence

Cars account for 33 of 39 exact-box radar-only observations; trailers and trucks contribute two each, and a bicycle and child pedestrian one each.

**Implication:** Prioritise the car cases for overlay and timing inspection when investigating complementarity.

**Limit:** Counts describe annotation observations, not independently recovered objects or successful detections.

**Sources:** [object_counts.csv](../docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv)

## F08 — The pooled long-range vehicle result extends beyond TruckScenes' radar coverage

**Dataset / evidence:** TruckDrive · recomputed existing project evidence

At 200–400 m, 504 vehicle observations from 55 tracks have 84.72% LiDAR and 35.52% radar support under the acquisition-time hypothesis. Static values are 80.36% and 37.50%.

**Implication:** LiDAR is the stronger source of distant vehicle geometry in this selected TruckDrive cohort.

**Limit:** Four eligible clips from five preselected clips; different sensor platform; alignment hypothesis is not verified publisher deskew; not AP.

**Sources:** [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [summary.csv](../docs/evidence/truckdrive-multiscene/summary/summary.csv)

## F09 — Radar complements LiDAR despite lower pooled geometric support

**Dataset / evidence:** TruckDrive · recomputed existing project evidence

The aligned distant cohort contains 25 radar-only observations. Union-of-support rises from LiDAR's 84.72% to 89.68%; 52 observations have neither modality inside the exact box.

**Implication:** Test the radar-only cases with a fusion detector rather than discarding radar on aggregate density.

**Limit:** Annotation-conditioned geometric union, not fusion-detector accuracy or evidence that all added cases are independent objects.

**Sources:** [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [summary.csv](../docs/evidence/truckdrive-multiscene/summary/summary.csv)

## F10 — A single radar return often does not mean a dense object representation

**Dataset / evidence:** TruckDrive · recomputed existing project evidence

Requiring three in-box returns at 200–400 m changes radar-supported observations from 179 to 51 of 504. LiDAR retains 81.15% support versus radar's 10.12%.

**Implication:** Assess spatial information and temporal/Doppler use before treating one return as sufficient recognition evidence.

**Limit:** Three returns is a diagnostic threshold, not a detection criterion; modalities carry different information.

**Sources:** [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [summary.csv](../docs/evidence/truckdrive-multiscene/summary/summary.csv)

## F11 — A small matched passenger-car cohort reverses the pooled ordering

**Dataset / evidence:** TruckDrive · recomputed existing project evidence

For 7 passenger-car tracks across 3 scenes appearing in both range bands, equal-track far support is 27.86% LiDAR versus 50.00% radar at 200–400 m under the aligned, exact-box assumption.

**Implication:** State the population in every sensor comparison; retain counterexamples.

**Limit:** Small, selected and box-margin-sensitive cohort; does not negate the larger mixed-vehicle result.

**Sources:** [matched_track_summary.csv](../docs/evidence/missing-support/matched_track_summary.csv); [what-sensors-miss-by-range.md](../docs/what-sensors-miss-by-range.md)

## F12 — Timing can dominate the apparent inability to see thin roadwork objects

**Dataset / evidence:** TruckDrive · recomputed existing project evidence

For the same 170 barrel observations at 100–150 m, LiDAR support is 28.82% with static calibration and 94.71% under the acquisition-time correction hypothesis.

**Implication:** Validate timestamps and overlays before calling an unsupported barrel a physical sensor failure.

**Limit:** Correction is a sensitivity hypothesis; object motion, label dimensions and extrinsics still matter.

**Sources:** [what-sensors-miss-by-range.md](../docs/what-sensors-miss-by-range.md); [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [summary.csv](../docs/evidence/truckdrive-multiscene/summary/summary.csv)

## F13 — Removing any one eligible scene retains the distant vehicle advantage

**Dataset / evidence:** TruckDrive · recomputed existing project evidence

Equal-scene LiDAR-minus-radar support at 200–400 m is 44.09 percentage points under alignment. Removing any one eligible scene leaves at least 37.75 points.

**Implication:** The selected distant-vehicle result is not driven only by the largest scene.

**Limit:** Descriptive robustness within four eligible clips, not statistical generalisation to all roads or weather.

**Sources:** [truckdrive-multiscene-result.md](../docs/truckdrive-multiscene-result.md); [summary.csv](../docs/evidence/truckdrive-multiscene/summary/summary.csv)

## F14 — Nearby rocks and building surfaces can be misinterpreted as ground

**Dataset / evidence:** GOOSE · recomputed existing project evidence

In the 24-frame patch-64 diagnostic, 813/2012 nearby rock points (40.41%) and 11584/91660 building points (12.64%) receive ground predictions.

**Implication:** Include these terrain failure cases before claiming reliable off-road obstacle handling.

**Limit:** Returned LiDAR points and coarse challenge taxonomy; not percentages of whole rocks/buildings missed or driving-safety scores.

**Sources:** [saved_fine_confusion.csv](../docs/evidence/goose-stratified/ground/saved_fine_confusion.csv)

## F15 — Distant obstacle-labelled points are more often assigned ground in this subset

**Dataset / evidence:** GOOSE · recomputed existing project evidence

Obstacle-candidate points assigned ground rise from 2.99% of 508,645 points at 0–25 m to 14.17% of 10,173 at 100–150 m.

**Implication:** Report obstacle-to-ground confusion by class and range, alongside ground correctness.

**Limit:** Scene/class composition changes; point percentages are not object miss rates and do not isolate range as a cause.

**Sources:** [scenario_group_confusion.csv](../docs/evidence/goose-stratified/ground/scenario_group_confusion.csv); [goose-multiscenario-terrain.md](../docs/goose-multiscenario-terrain.md)

## F16 — One scenario hides much of the distant ground variation

**Dataset / evidence:** GOOSE · recomputed existing project evidence

Ground correctness at 100–150 m is 97.67% when points are pooled, but 89.34% with equal scenario weight. One scenario supplies 85.09% of the 4,888 ground points.

**Implication:** Use per-scenario denominators and macro summaries when explaining terrain performance.

**Limit:** Several scenario denominators are tiny; equal weighting is sensitivity, not an unbiased population estimate.

**Sources:** [scenario_group_confusion.csv](../docs/evidence/goose-stratified/ground/scenario_group_confusion.csv); [goose-multiscenario-terrain.md](../docs/goose-multiscenario-terrain.md)

## F17 — Attention context is a confirmed contributor to selected terrain failures

**Dataset / evidence:** GOOSE · recomputed existing project evidence

With checkpoint, input frames, seed and preprocessing fixed, patch 64→256 reduces pooled rock-to-ground confusion from 49.52% to 22.56%. Correct rock-category predictions reach only 24.90%.

**Implication:** A compatibility setting can contribute to model errors; compare configurations before blaming the sensor.

**Limit:** Three adjacent post-hoc frames; partial improvement; no general benchmark or recommended full-split memory setting.

**Sources:** [context_pooled.csv](../docs/evidence/goose-failure-causes/context_pooled.csv); [goose-failure-causes.md](../docs/goose-failure-causes.md)

## F18 — The nearby rock error is concentrated in one concrete failure case

**Dataset / evidence:** GOOSE · recomputed existing project evidence

One frame supplies 788 of 813 nearby rock-to-ground errors (96.92%). Its labelled rock points span three frame-local instances.

**Implication:** Show the actual difficult frame and test comparable independent cases.

**Limit:** Three frame-local instances are not three independent repeated experiments; nearby views are correlated.

**Sources:** [summary.csv](../docs/evidence/goose-error-cases/summary.csv); [manifest.json](../docs/evidence/goose-error-cases/manifest.json)

## F19 — Correct ground grouping can hide incorrect surface material

**Dataset / evidence:** GOOSE · recomputed existing project evidence

In the earlier ten-frame flight subset, only 34/149 asphalt points at 100–150 m receive artificial-ground predictions; 96 are called natural ground.

**Implication:** Keep material recognition distinct from a binary ground/obstacle grouping.

**Limit:** Tiny distant asphalt denominator; different subset from the 24-frame diagnostic; not a 64-class model evaluation.

**Sources:** [raw_class_errors.csv](../docs/evidence/missing-support/goose-saved/raw_class_errors.csv)

## F20 — Higher aggregate accuracy at distance can reflect an easier class mixture

**Dataset / evidence:** GOOSE · recomputed existing project evidence

Flight-subset point accuracy rises from 83.40% nearby to 96.90% beyond 150 m, where 94.74% of labelled points are vegetation.

**Implication:** A rising aggregate score does not demonstrate that long-range terrain recognition improves.

**Limit:** Single scenario and interrupted model run; class composition, visibility and point selection remain entangled.

**Sources:** [range_accuracy.csv](../docs/evidence/missing-support/goose-saved/range_accuracy.csv); [raw_class_errors.csv](../docs/evidence/missing-support/goose-saved/raw_class_errors.csv)

## F21 — Simple voxel collisions do not explain the inspected rock/building case

**Dataset / evidence:** GOOSE · recomputed existing project evidence

The inspected rock/building points have 0 same-voxel ground/ground-cover collisions across the tested 2.5 cm and 5 cm grids.

**Implication:** Do not attribute this case to simple ground/obstacle voxel merging; attention context remains the tested contributor.

**Limit:** Only this case and these voxel scales; does not exclude all preprocessing effects or label errors.

**Sources:** [voxel_ambiguity.csv](../docs/evidence/goose-failure-causes/voxel_ambiguity.csv)

## F22 — Low rock geometry is associated with ground confusion

**Dataset / evidence:** GOOSE · recomputed existing project evidence

With a ground/ground-cover reference within 1 m in XY, 84.52% of 394 rock points within ±0.2 m vertically are called ground, versus 23.46% of 260 at 0.5–1 m.

**Implication:** Include low protruding rocks when designing an off-road follow-up.

**Limit:** Nearest-point height proxy in one case, not validated object height or an isolated causal geometry effect; snow causality unproven.

**Sources:** [nearest_ground_diagnostic.csv](../docs/evidence/goose-failure-causes/nearest_ground_diagnostic.csv)

## F23 — Radar ground support and raised-geometry support are different questions

**Dataset / evidence:** STONE · recomputed existing project evidence

In the lake recording, aligned radar supports 4.82% of 13,128 near-ground reference voxel observations and 26.30% of 4,741 raised-geometry observations.

**Implication:** Separate ground mapping from the study of protruding obstacles.

**Limit:** LiDAR-derived reference, 0.8 m tolerance and declared ROI; physical radar extrinsics and visibility unresolved; conditional descriptive result.

**Sources:** [comparison.csv](../docs/evidence/stone-environments/comparison.csv); [stone-environments-followup.md](../docs/stone-environments-followup.md)

## F24 — An unresolved coordinate origin can reverse a terrain conclusion

**Dataset / evidence:** STONE · recomputed existing project evidence

Farmland radar support is 29.53% raised versus 17.76% ground with the bridged origin; the ROS origin gives 19.33% raised versus 24.07% ground.

**Implication:** Obtain independently validated numerical radar-to-LiDAR transforms before ranking terrain performance.

**Limit:** Both conventions are sensitivity assumptions, not a proven calibration or complete uncertainty interval.

**Sources:** [comparison.csv](../docs/evidence/stone-environments/comparison.csv); [stone-environments-followup.md](../docs/stone-environments-followup.md)

## F25 — One recording does not capture the variation in radar ground support

**Dataset / evidence:** STONE · recomputed existing project evidence

With the aligned convention, pooled ground support is 17.76% in farmland, 4.82% in lake and 0.94% in land, from 20 sampled frames per recording.

**Implication:** Retain environment-specific results rather than reporting one off-road percentage.

**Limit:** Recording names are publisher categories, not confirmed weather/terrain treatments; calibration and reference bias prevent a causal environment claim.

**Sources:** [comparison.csv](../docs/evidence/stone-environments/comparison.csv); [stone-environments-followup.md](../docs/stone-environments-followup.md)

## F26 — Radar can retain visible evidence in LiDAR-empty annotated fog footprints

**Dataset / evidence:** RADIATE · recomputed existing project evidence

At 50–75 m, 9/19 vehicle observations pass the >20-level local radar contrast criterion, while 0/19 exact footprints contain above-ground LiDAR returns.

**Implication:** The fog case motivates a matched weather/fusion experiment and prevents a blanket sensor ranking.

**Limit:** Radar-derived labels, four tracks across the pilot, no clear-weather control; signal contrast is not detection accuracy or proof that fog caused LiDAR absence.

**Sources:** [observations.csv](../docs/evidence/radiate-fog/observations.csv); [radiate-fog-pilot.md](../docs/radiate-fog-pilot.md)

## F27 — Brightness alone also passes many unlabelled control regions

**Dataset / evidence:** RADIATE · recomputed existing project evidence

The basic radar contrast test passes 32/117 unlabelled controls; the >20-level test passes 8/117. At 50–75 m, the strict test passes 1/57 controls.

**Implication:** Use background controls and threshold sensitivity when presenting a bright radar footprint.

**Limit:** Controls are unlabelled, not verified empty negatives; these fractions are not false-positive rates or independent significance tests.

**Sources:** [unlabelled_controls.csv](../docs/evidence/radiate-fog/unlabelled_controls.csv)

## F28 — The far LiDAR sparsity persists under an optimistic footprint/timing sensitivity

**Dataset / evidence:** RADIATE · recomputed existing project evidence

At 50–75 m, a 1 m footprint expansion gives LiDAR support in 1/19 observations; allowing either adjacent scan as well gives 2/19.

**Implication:** A small footprint expansion alone does not account for all LiDAR-empty far footprints in this pilot.

**Limit:** Future/adjacent scans are an optimistic offline sensitivity, not a real-time sensor score; target/ego motion and occlusion remain unresolved.

**Sources:** [summary.csv](../docs/evidence/radiate-fog/summary.csv)

## F29 — A close file timestamp does not mean the whole scans were simultaneous

**Dataset / evidence:** Boreas · new public sample analysis

Three newly decoded radar scans span 249.980–249.997 ms each; the nearest LiDAR scans span 103.271–103.760 ms. File offsets range from -44.910 to +16.267 ms.

**Implication:** Deskew rolling scans using individual point/azimuth timestamps when moving scenes are compared.

**Limit:** First three chronological scan pairs from one sequence; no motion-error magnitude, weather effect or object accuracy measured.

**Sources:** [boreas_scans.csv](../results/evidence/findings-oct01/additional-datasets/boreas_scans.csv); [manifest.json](../results/evidence/findings-oct01/additional-datasets/manifest.json)

## F30 — Recorded range support depends on the radar representation

**Dataset / evidence:** Boreas · new public sample analysis

Each sample radar image has 3360 range bins, with the documented offset giving a last-bin centre of 199.8864 m. Each paired LiDAR scan contains returns beyond 200 m, with observed maxima 231.00–231.76 m.

**Implication:** Do not score this recorded radar image outside its stored range and interpret the absence as failed object recognition.

**Limit:** Radar bins are intensity samples, LiDAR values are spherical ranges; no shared object/visibility denominator or general hardware range ranking.

**Sources:** [boreas_scans.csv](../results/evidence/findings-oct01/additional-datasets/boreas_scans.csv); [manifest.json](../results/evidence/findings-oct01/additional-datasets/manifest.json)

## F31 — The official 3D validation subset has narrow recording coverage

**Dataset / evidence:** WildScenes · new public sample analysis

The pinned official opt3d split contains 7,517 training, 356 validation and 2,705 test frames. All 356 validation entries belong to K-01; training and test each cover five recording groups.

**Implication:** Use the independent terrain test groups and group-specific scores when checking generalisation from GOOSE.

**Limit:** Metadata audit only; no raw labels or inference. Shared recording groups are not proof of leakage, and do not establish geographic independence.

**Sources:** [wildscenes_splits.json](../results/evidence/findings-oct01/additional-datasets/wildscenes_splits.json); [manifest.json](../results/evidence/findings-oct01/additional-datasets/manifest.json)

## F32 — Camera and LiDAR split totals are not automatically a paired population

**Dataset / evidence:** WildScenes · new public sample analysis

The opt2d test has 2,133 frames and opt3d test 2,705; only 2,061 frame IDs occur in both. No exact train/val/test frame IDs overlap within either dimension.

**Implication:** Join identical frame IDs before any camera-versus-LiDAR terrain comparison.

**Limit:** Identity check alone does not validate timing, projected-label completeness, spatial disjointness or an accuracy comparison.

**Sources:** [wildscenes_splits.json](../results/evidence/findings-oct01/additional-datasets/wildscenes_splits.json); [manifest.json](../results/evidence/findings-oct01/additional-datasets/manifest.json)
