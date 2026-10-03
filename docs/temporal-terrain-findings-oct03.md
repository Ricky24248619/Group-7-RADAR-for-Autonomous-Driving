# Temporal sensing and off-road findings — 3 October 2026

This adds evidence to the [ten consolidated findings](consolidated-findings-oct02.md). It preserves the earlier road, off-road and sensor engineering results. Seven new candidate messages below have different practical decisions; repeated classes, distance bands, settings and replications do not count as extra findings. The combined register now has **17 candidate distinct messages**, pending human review. The target of at least 20 is still outstanding.

These analyses reuse seven TruckDrive clips, all eligible TruckScenes mini observations in ten recordings, 31 selected GOOSE frames from eight recordings, and 17 eligible RADIATE fog frames. Five preselected WildScenes scan/label pairs were newly acquired: 8,497,120 bytes and 531,070 points. All five are training-split examples, used to inspect data and labels. No new GPU inference, detector, fusion model or cross-dataset transfer test was run.

## D11 — An occasional distant return is weaker evidence than a sustained observation

In the TruckDrive forward sector (within 15 degrees of the sensor's forward direction), 104 of 107 labelled vehicle tracks had LiDAR support at least once, while 74 had support in three consecutive sampled observations. Radar supported 101 at least once and 71 for three samples. With at least three returns required per observation, the persistent counts were 72 for LiDAR and 48 for radar.

The first three-sample confirmation was at 200–400 m for 30 LiDAR tracks and 26 radar tracks under the one-return rule. Under the three-return rule, those counts were 28 and four. These are first confirmation ranges across each track's selected forward observations, not a matched cohort proving a recognition advantage. Median time from the start of the confirming run to its third sample was approximately one second, because these data were sampled roughly every half second.

**Use:** define the required duration and density of evidence when studying a truck's information horizon. A future detector or tracker should be evaluated on stable recognition before the required response, rather than point presence alone. The three-sample rule is an analysis choice; its delay is not the sensor's native latency or a measured braking requirement. A forward angle is a route proxy, not proof the object lies in the truck's path.

Sources: [setting summaries](../results/evidence/p3-p4-oct03/road_summary.csv), [track evidence, gzip CSV](../results/evidence/p3-p4-oct03/road_tracks.csv.gz), [sampled episodes, gzip CSV](../results/evidence/p3-p4-oct03/road_episodes.csv.gz).

## D12 — The terrain model also rejects some candidate ground as obstacles

Across the 24 earlier GOOSE frames and seven follow-up frames using the patch-64 outputs, 2,853 of 1,312,878 points on firm-surface-labelled terrain were assigned a blocked model category (0.217%). The same outputs called 26,072 of 953,464 rigid/person/vehicle-hazard-labelled points ground (2.734%). These denominators are different; the percentages are not competing safety scores.

**Use:** distinguish overlooking a hazard from unnecessarily rejecting a candidate route. For off-road missions, a model upgrade should be checked for both error directions. The client can decide how conservatively uncertain terrain should be treated once the vehicle and operating conditions are specified. These are point-label errors under a provisional screening policy; they do not establish that a surface was physically passable or that a route was actually rejected.

Sources: [directional frame counts](../results/evidence/p3-p4-oct03/terrain_directional_frames.csv), [fine classes and predictions by range](../results/evidence/p3-p4-oct03/terrain_fine_predictions.csv). This extends the off-road strand without replacing D05's overlooked-hazard cases or D06's semantic/passability distinction.

## D13 — A majority-ground terrain map can hide a hazard even with correct input labels

Using the fine ground-truth labels and the provisional policy, 4,232 observed half-metre XY columns across the 31 selected frames contained both candidate firm terrain and a rigid/person/vehicle hazard. In 672 of those columns (15.879%), firm-terrain points were the majority after ignored points were excluded. A rule assigning the column only its majority label would therefore discard the hazard's presence even if the point labels were perfect. At one-metre resolution, the corresponding count was 524 of 3,410 mixed columns (15.367%). These resolutions are two analyses of the same data, not independent evidence.

**Use:** preserve hazard presence and vertical structure when converting model points into a terrain representation. Improving point-level AI accuracy alone cannot fix information discarded by the downstream aggregation rule. The counts concern vertical columns, which can include overhead objects; no collision, clearance or physical traversal outcome was measured. Unobserved cells were never scored as free.

Source: [cell diagnostics](../results/evidence/p3-p4-oct03/terrain_cells.csv). Ground-truth-majority and predicted-majority counts remain separate.

## D14 — The inspected WildScenes benchmark cannot score water avoidance

The pinned author's WildScenes 3D configuration maps the native water class to the ignored score label, along with sky and unlabelled points. Thirteen classes remain scored. A favourable result using that configuration does not assess water segmentation. None of the five acquired examples contains water, so this analysis supplies no water recognition result either.

**Use:** retain consequential classes in an evaluation when the intended off-road mission includes them. Future model developers need a separate water check, appropriate labelled examples and a vehicle-specific interpretation of depth or risk. This is a verified evaluation-configuration gap, not evidence that a sensor or model fails in water.

Source: [native taxonomy and author's benchmark mapping](../results/evidence/p3-p4-oct03/wildscenes_taxonomy.csv); pinned source references and hashes in the [terrain manifest](../results/evidence/p3-p4-oct03/terrain_manifest.json).

## D15 — Independent terrain data needs an input compatibility check before testing the existing model

The acquired WildScenes labelled scans contain XYZ coordinates only. The saved GOOSE model configuration collects coordinates plus return strength and expects four input channels. Passing the three-field files unchanged would not reproduce the saved model's input. The native labels also differ: WildScenes has one grass class, whereas the GOOSE evidence distinguishes low and high grass.

**Use:** specify feature preparation and an explicit shared label mapping before evaluating a future model on independent data. The present raw-data inspection is useful preparation, but it is not a successful GOOSE transfer test. Supplying invented strength values would introduce an assumption requiring its own validation; it would not recover measured intensity. Ambiguous class translations remain explicit in the taxonomy table.

Sources: [input and run hashes](../results/evidence/p3-p4-oct03/terrain_manifest.json), [taxonomy](../results/evidence/p3-p4-oct03/wildscenes_taxonomy.csv). The feature mismatch is distinct from D10's existing range-crop limitation.

## D16 — Our independent terrain examples do not yet cover the difficult surfaces needed to qualify off-road use

The five selected WildScenes frames contain 1,176 log-labelled points, 24 rock-labelled points, one mud-labelled point and no water-labelled points. All their planar point ranges are below 45 m. The 31 selected GOOSE frames also contain no water-labelled points. These are properties of the inspected samples, not the full datasets. Log points are present in every WildScenes recording group, but points are not independently counted obstacles.

**Use:** acquire condition-specific evidence for mud, water, sparse rocks and other consequential hazards before generalising the off-road results. Neither more model speed nor a high vegetation/dirt score fills an absent evaluation condition. The five chronological first frames were selected before inspecting their labels; they are an eligibility pilot, not a representative terrain benchmark. They cannot extend the road study's 200–400 m evidence into an off-road long-range claim.

Sources: [independent class/range counts](../results/evidence/p3-p4-oct03/wildscenes_class_range.csv), [frame footprints](../results/evidence/p3-p4-oct03/wildscenes_frames.csv), [frozen example identities](../results/evidence/p3-p4-oct03/wildscenes_selection.json), GOOSE directional frame counts above.

## D17 — Better off-road labels in the saved larger-context run came with more recorded processing time

On the seven matched GOOSE follow-up frames, increasing the saved attention patch from 64 to 128 reduced rigid-hazard points called ground from 2,898 to 1,745, and candidate-ground points called blocked from 1,439 to 1,049. The sum of the seven logged batch times increased from 93.250 to 119.217 seconds (27.847%); the repeated patch-64 run summed to 88.332 seconds. The complete runs, including setup, took 127.85, 122.80 and 154.09 seconds respectively. Observed global GPU memory reached 4,747, 4,966 and 5,953 MiB at the coarse monitoring intervals.

**Use:** evaluate consequential error directions alongside processing cost before selecting a future model setting. An improvement in labels does not establish suitability for a vehicle's response deadline. The earlier D07 regression in one frame remains visible; these pooled directional improvements do not cancel it. Saved desktop batch timings include the tested pipeline, are not a controlled production benchmark, and are not vehicle latency. Sampled global memory is not process peak memory. No new inference was performed for this analysis.

Sources: [saved per-frame cost](../results/evidence/p3-p4-oct03/saved_model_cost.csv), directional counts and run hashes above. D07 concerns whether context helps consistently; D17 concerns the measured cost of the tested change.

## Refinements of existing messages — not additional findings

**D01/D03:** in the seven-clip aligned forward 15-degree sample at 200–400 m, LiDAR supported 345 of 398 vehicle-time observations and radar 154. Twenty-three radar-only observations increased geometric union to 368. Across all forward ranges, four of 38 radar-only episodes persisted for three samples. This adds persistence evidence to complementarity; it is not fusion accuracy.

**D03/D09:** on the same 25,117 TruckScenes observations, the 39 corrected radar-only cases formed 38 episodes, none lasting three sampled observations. Expanding the corrected boxes by 0.5 m left three radar-only cases under the one-return definition. The original rigid-count result had 185 radar-only cases; only 36 remained radar-only after per-point correction with exact boxes. This is sensitivity of apparent complementarity, not grounds for rejecting radar. TruckDrive retained persistent cases, and the unresolved publisher LiDAR-count discrepancy remains a limitation.

**D04:** matching camera visibility, class and range produced 36 clear/adverse description strata across 226 recording-stratum rows. The full selected weather population still has only two rain recordings and one snow recording, so matched descriptive strata do not isolate weather causally. Camera panoramic visibility is not radar visibility.

**D04:** two true fog target footprints each showed seven consecutive strict-contrast samples (gap greater than 20 with at least five bright pixels). None of the 12 rotated comparison footprints showed a three-sample strict run. Under the loose gap-zero rule, two rotated footprints did show three-sample runs. A persistent brightness signal can therefore merit recognition testing, but the controls are unlabelled regions, not verified empty ground truth; these data do not provide detector precision or recall.

**D05–D08:** consequential point errors are reported by frame, fine class and range. Patch-128 versus patch-64 comparisons are restricted to the same seven frames; the earlier 24 are a separate cohort. All raw/prediction hashes and the fine-to-challenge mapping were reconciled. Improving a model remains separate from proving traversal success.

Sources: [radar-only sensitivity](../results/evidence/p3-p4-oct03/radar_only_sensitivity.csv), [weather strata](../results/evidence/p3-p4-oct03/weather_strata.csv), [matched descriptive strata](../results/evidence/p3-p4-oct03/weather_matched_strata.csv), [fog persistence](../results/evidence/p3-p4-oct03/fog_persistence.csv), [road manifest](../results/evidence/p3-p4-oct03/road_manifest.json).

## Reproduction

Use the existing RADAR Python environment and the previously acquired datasets/predictions. Derived evidence contains no raw scans, private planning or client report. Compressed CSVs are ordinary UTF-8 CSV after gzip decompression. The source/output hashes distinguish repository LF text from exact external bytes.

```powershell
python scripts/analyse_p3_p4_road.py --truckscenes-root F:/RADAR/datasets/TruckScenes/man-truckscenes --output-dir results/evidence/p3-p4-oct03

# Optional acquisition on a machine that does not have the selected WildScenes pairs:
# This reads a public metadata listing (~128 MB) and downloads only 8.5 MB of raw data.
python scripts/acquire_wildscenes_selected.py --output-dir F:/RADAR/datasets/WildScenes/selected-oct03

python scripts/analyse_p3_p4_terrain.py --goose-root F:/RADAR/datasets/GOOSE/extracted/goose_3d_val --mapping F:/RADAR/datasets/GOOSE/archives/challenge_label_mapping.csv --original-predictions F:/RADAR/outputs/pointcept/ptv3_stratified24_20260928/result --followup-predictions F:/RADAR/outputs/pointcept/goose_followup7_20261001 --execution F:/RADAR/logs/sprint-followup-oct01/execution.json --wildscenes-audit F:/RADAR/datasets/WildScenes/selected-oct03 --output-dir results/evidence/p3-p4-oct03
```

WildScenes code is pinned to `9eb4e10b4483a634159e2b371be0437e465fe218`; data comes from public CSIRO collection 61541. The data licence is CC BY-NC-SA 4.0. Its noncommercial terms require assessment before commercial reuse. Raw data stays local. Existing GOOSE predictions are not automatically regenerated by these scripts.
