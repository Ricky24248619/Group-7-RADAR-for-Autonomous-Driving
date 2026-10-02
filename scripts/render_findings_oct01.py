#!/usr/bin/env python3
"""Build the findings register from verified measurements; no client report output."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/evidence/findings-oct01"

def build_findings(facts, scans, splits):
    findings = []
    def add(dataset, title, statement, implication, limits, source, measurement_key, new=False):
        findings.append({"id": f"F{len(findings)+1:02d}", "dataset": dataset, "title": title,
                         "statement": statement, "implication": implication, "limits": limits,
                         "evidence_type": "new public sample analysis" if new else "recomputed existing project evidence",
                         "sources": source, "measurement_key": measurement_key})
    ts, td, g = facts["truckscenes"], facts["truckdrive"], facts["goose"]
    ts_source = ["docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv"]
    td_source = ["docs/truckdrive-multiscene-result.md", "docs/evidence/truckdrive-multiscene/summary/summary.csv"]
    goose_source = ["docs/evidence/goose-stratified/ground/scenario_group_confusion.csv", "docs/goose-multiscenario-terrain.md"]
    a = ts["by_range"]["150-400"]
    add("TruckScenes", "LiDAR has substantially more distant object support in this subset",
        f"At 150–400 m, {a['observations']:,} annotated observations have {a['lidar_percent']:.2f}% LiDAR support and {a['radar_percent']:.2f}% radar support. The actual maximum object centre is {ts['max_object_range_m']:.2f} m.",
        "Retain LiDAR as the stronger geometric reference for these labelled distant objects.",
        "At least one in-box return; LiDAR-conditioned labels; recorded radar boundary near 190 m; not detector recall or a universal ranking.", ts_source, "truckscenes.by_range.150-400")
    add("TruckScenes", "LiDAR scan motion changes the apparent benefit of radar",
        f"On the same {ts['population']['observations']:,} observations, individual-point ego-motion correction reduces radar-only support from {ts['rigid_matched']['radar_only']} to {ts['population']['radar_only']}.",
        "Deskew before attributing complementary detections to a sensor.",
        "Ego correction only; moving targets and cabin motion remain unresolved.", ts_source + ["docs/evidence/truckscenes/paired-all-sensor-support/object_counts.csv"], "truckscenes.rigid_matched")
    add("TruckScenes", "The residual radar-only result depends on box boundaries",
        f"Expanding every box face by 0.5 m reduces radar-only observations from {ts['population']['radar_only']} to {ts['expanded']['radar_only']} over the same {ts['population']['observations']:,} objects-at-time observations.",
        "Inspect geometry and residual timing before assigning a physical cause to these cases.",
        "Expanded boxes admit background returns and are a sensitivity test, not corrected ground truth.", ts_source, "truckscenes.expanded")
    truck, cone, pedestrian = (ts["near_classes"][name] for name in ("vehicle.truck", "movable_object.trafficcone", "human.pedestrian.adult"))
    add("TruckScenes", "Radar support varies substantially by class even nearby",
        f"At 0–25 m, radar supports {truck['radar_percent']:.2f}% of {truck['observations']} truck observations, {pedestrian['radar_percent']:.2f}% of {pedestrian['observations']} adult-pedestrian observations and {cone['radar_percent']:.2f}% of {cone['observations']} cone observations.",
        "Report vulnerable road users and small obstacles separately from large vehicles.",
        "Class, view, distance within the band and occlusion differ; reflectivity is not isolated; repeated observations.", ts_source, "truckscenes.near_classes")
    track = next(row for row in facts["matched_tracks"] if row["dataset"] == "TruckScenes")
    add("TruckScenes", "Changing car identities alone does not explain the range decline",
        f"For the same {track['tracks']} car tracks, equal-track radar support falls from {float(track['radar_near_percent']):.2f}% at 0–50 m to {float(track['radar_far_percent']):.2f}% at 50–100 m. LiDAR changes from {float(track['lidar_near_percent']):.2f}% to {float(track['lidar_far_percent']):.2f}%.",
        "Follow the same tracks across ranges rather than relying only on a changing pooled population.",
        "Viewpoint, occlusion and target motion are still uncontrolled.", ["docs/evidence/missing-support/matched_track_summary.csv"], "matched_tracks")
    add("TruckScenes", "The distant support difference persists when scenes get equal weight",
        f"At 150–400 m, equal weighting of {a['scenes']} eligible scenes gives a LiDAR-minus-radar difference of {a['equal_scene_difference_pp']:.2f} percentage points; the smallest scene difference is {a['min_scene_difference_pp']:.2f} points.",
        "The pooled result is not explained solely by one scene having many labels.",
        "Descriptive scene sensitivity; selected mini scenes and radar range truncation remain; no population confidence interval.", ts_source, "truckscenes.by_range.150-400")
    add("TruckScenes", "The few radar-only observations mostly concern cars",
        f"Cars account for {ts['radar_only_classes']['vehicle.car']} of {ts['population']['radar_only']} exact-box radar-only observations; trailers and trucks contribute two each, and a bicycle and child pedestrian one each.",
        "Prioritise the car cases for overlay and timing inspection when investigating complementarity.",
        "Counts describe annotation observations, not independently recovered objects or successful detections.", ts_source, "truckscenes.radar_only_classes")
    a = td["aligned"]["vehicles_200_400"]
    b = td["static"]["vehicles_200_400"]
    add("TruckDrive", "The pooled long-range vehicle result extends beyond TruckScenes' radar coverage",
        f"At 200–400 m, {a['observations']} vehicle observations from {a['tracks']} tracks have {a['lidar_percent']:.2f}% LiDAR and {a['radar_percent']:.2f}% radar support under the acquisition-time hypothesis. Static values are {b['lidar_percent']:.2f}% and {b['radar_percent']:.2f}%.",
        "LiDAR is the stronger source of distant vehicle geometry in this selected TruckDrive cohort.",
        "Four eligible clips from five preselected clips; different sensor platform; alignment hypothesis is not verified publisher deskew; not AP.", td_source, "truckdrive.aligned.vehicles_200_400")
    add("TruckDrive", "Radar complements LiDAR despite lower pooled geometric support",
        f"The aligned distant cohort contains {a['radar_only']} radar-only observations. Union-of-support rises from LiDAR's {a['lidar_percent']:.2f}% to {a['union_percent']:.2f}%; {a['neither']} observations have neither modality inside the exact box.",
        "Test the radar-only cases with a fusion detector rather than discarding radar on aggregate density.",
        "Annotation-conditioned geometric union, not fusion-detector accuracy or evidence that all added cases are independent objects.", td_source, "truckdrive.aligned.vehicles_200_400")
    density = td["aligned"]["vehicles_200_400_min3"]
    add("TruckDrive", "A single radar return often does not mean a dense object representation",
        f"Requiring three in-box returns at 200–400 m changes radar-supported observations from {a['both']+a['radar_only']} to {density['both']+density['radar_only']} of {a['observations']}. LiDAR retains {density['lidar_percent']:.2f}% support versus radar's {density['radar_percent']:.2f}%.",
        "Assess spatial information and temporal/Doppler use before treating one return as sufficient recognition evidence.",
        "Three returns is a diagnostic threshold, not a detection criterion; modalities carry different information.", td_source, "truckdrive.aligned.vehicles_200_400_min3")
    track = next(row for row in facts["matched_tracks"] if row["dataset"] == "TruckDrive" and row["variant"] == "aligned")
    add("TruckDrive", "A small matched passenger-car cohort reverses the pooled ordering",
        f"For {track['tracks']} passenger-car tracks across {track['scenes']} scenes appearing in both range bands, equal-track far support is {float(track['lidar_far_percent']):.2f}% LiDAR versus {float(track['radar_far_percent']):.2f}% radar at 200–400 m under the aligned, exact-box assumption.",
        "State the population in every sensor comparison; retain counterexamples.",
        "Small, selected and box-margin-sensitive cohort; does not negate the larger mixed-vehicle result.", ["docs/evidence/missing-support/matched_track_summary.csv", "docs/what-sensors-miss-by-range.md"], "matched_tracks")
    barrels_a, barrels_b = td["aligned"]["barrels_100_150"], td["static"]["barrels_100_150"]
    add("TruckDrive", "Timing can dominate the apparent inability to see thin roadwork objects",
        f"For the same {barrels_a['observations']} barrel observations at 100–150 m, LiDAR support is {barrels_b['lidar_percent']:.2f}% with static calibration and {barrels_a['lidar_percent']:.2f}% under the acquisition-time correction hypothesis.",
        "Validate timestamps and overlays before calling an unsupported barrel a physical sensor failure.",
        "Correction is a sensitivity hypothesis; object motion, label dimensions and extrinsics still matter.", ["docs/what-sensors-miss-by-range.md"] + td_source, "truckdrive.aligned.barrels_100_150")
    add("TruckDrive", "Removing any one eligible scene retains the distant vehicle advantage",
        f"Equal-scene LiDAR-minus-radar support at 200–400 m is {a['equal_scene_difference_pp']:.2f} percentage points under alignment. Removing any one eligible scene leaves at least {a['leave_one_scene_out_min_pp']:.2f} points.",
        "The selected distant-vehicle result is not driven only by the largest scene.",
        "Descriptive robustness within four eligible clips, not statistical generalisation to all roads or weather.", td_source, "truckdrive.aligned.vehicles_200_400")
    rock, building = g["fine_ground"]["rock/0-25"], g["fine_ground"]["building/0-25"]
    add("GOOSE", "Nearby rocks and building surfaces can be misinterpreted as ground",
        f"In the 24-frame patch-64 diagnostic, {rock['ground_errors']}/{rock['points']} nearby rock points ({rock['ground_error_percent']:.2f}%) and {building['ground_errors']}/{building['points']} building points ({building['ground_error_percent']:.2f}%) receive ground predictions.",
        "Include these terrain failure cases before claiming reliable off-road obstacle handling.",
        "Returned LiDAR points and coarse challenge taxonomy; not percentages of whole rocks/buildings missed or driving-safety scores.", ["docs/evidence/goose-stratified/ground/saved_fine_confusion.csv"], "goose.fine_ground")
    near, far = g["obstacle_candidate"]["0-25"], g["obstacle_candidate"]["100-150"]
    add("GOOSE", "Distant obstacle-labelled points are more often assigned ground in this subset",
        f"Obstacle-candidate points assigned ground rise from {near['pooled_ground_percent']:.2f}% of {near['points']:,} points at 0–25 m to {far['pooled_ground_percent']:.2f}% of {far['points']:,} at 100–150 m.",
        "Report obstacle-to-ground confusion by class and range, alongside ground correctness.",
        "Scene/class composition changes; point percentages are not object miss rates and do not isolate range as a cause.", goose_source, "goose.obstacle_candidate")
    far = g["ground_surface"]["100-150"]
    add("GOOSE", "One scenario hides much of the distant ground variation",
        f"Ground correctness at 100–150 m is {far['pooled_ground_percent']:.2f}% when points are pooled, but {far['equal_scenario_ground_percent']:.2f}% with equal scenario weight. One scenario supplies {far['largest_scenario_share_percent']:.2f}% of the {far['points']:,} ground points.",
        "Use per-scenario denominators and macro summaries when explaining terrain performance.",
        "Several scenario denominators are tiny; equal weighting is sensitivity, not an unbiased population estimate.", goose_source, "goose.ground_surface.100-150")
    context = {(row["variant"], row["true_class"]): row for row in g["context"]}
    p64, p256 = context["p64", "rock"], context["p256", "rock"]
    add("GOOSE", "Attention context is a confirmed contributor to selected terrain failures",
        f"With checkpoint, input frames, seed and preprocessing fixed, patch 64→256 reduces pooled rock-to-ground confusion from {float(p64['ground_category_percent']):.2f}% to {float(p256['ground_category_percent']):.2f}%. Correct rock-category predictions reach only {float(p256['correct_coarse_percent']):.2f}%.",
        "A compatibility setting can contribute to model errors; compare configurations before blaming the sensor.",
        "Three adjacent post-hoc frames; partial improvement; no general benchmark or recommended full-split memory setting.", ["docs/evidence/goose-failure-causes/context_pooled.csv", "docs/goose-failure-causes.md"], "goose.context")
    concentration = next(row for row in g["error_concentration"] if row["true_class"] == "rock" and row["band_m"] == "0-25")
    add("GOOSE", "The nearby rock error is concentrated in one concrete failure case",
        f"One frame supplies {concentration['most_error_frame_points']} of {concentration['ground_category_points']} nearby rock-to-ground errors ({float(concentration['most_error_frame_share_percent']):.2f}%). Its labelled rock points span three frame-local instances.",
        "Show the actual difficult frame and test comparable independent cases.",
        "Three frame-local instances are not three independent repeated experiments; nearby views are correlated.", ["docs/evidence/goose-error-cases/summary.csv", "docs/evidence/goose-error-cases/manifest.json"], "goose.error_concentration")
    asphalt = g["flight_surface_errors"][0]
    add("GOOSE", "Correct ground grouping can hide incorrect surface material",
        f"In the earlier ten-frame flight subset, only {asphalt['correct_coarse_label']}/{asphalt['points']} asphalt points at 100–150 m receive artificial-ground predictions; {asphalt['most_common_wrong_points']} are called natural ground.",
        "Keep material recognition distinct from a binary ground/obstacle grouping.",
        "Tiny distant asphalt denominator; different subset from the 24-frame diagnostic; not a 64-class model evaluation.", ["docs/evidence/missing-support/goose-saved/raw_class_errors.csv"], "goose.flight_surface_errors")
    accuracy = {row["band_m"]: row for row in g["flight_range_accuracy"]}
    vegetation_share = 100*g["flight_far_vegetation_points"]/int(accuracy["150+"]["points"])
    add("GOOSE", "Higher aggregate accuracy at distance can reflect an easier class mixture",
        f"Flight-subset point accuracy rises from {float(accuracy['0-25']['accuracy_percent']):.2f}% nearby to {float(accuracy['150+']['accuracy_percent']):.2f}% beyond 150 m, where {vegetation_share:.2f}% of labelled points are vegetation.",
        "A rising aggregate score does not demonstrate that long-range terrain recognition improves.",
        "Single scenario and interrupted model run; class composition, visibility and point selection remain entangled.", ["docs/evidence/missing-support/goose-saved/range_accuracy.csv", "docs/evidence/missing-support/goose-saved/raw_class_errors.csv"], "goose.flight_range_accuracy")
    collisions = sum(int(row["same_voxel_reference_points"]) for row in g["voxel_ambiguity"])
    add("GOOSE", "Simple voxel collisions do not explain the inspected rock/building case",
        f"The inspected rock/building points have {collisions} same-voxel ground/ground-cover collisions across the tested 2.5 cm and 5 cm grids.",
        "Do not attribute this case to simple ground/obstacle voxel merging; attention context remains the tested contributor.",
        "Only this case and these voxel scales; does not exclude all preprocessing effects or label errors.", ["docs/evidence/goose-failure-causes/voxel_ambiguity.csv"], "goose.voxel_ambiguity")
    height = [row for row in g["ground_height_proxy"] if row["true_class"] == "rock" and row["reference"] == "ground_surface_and_cover" and float(row["max_xy_distance_m"]) == 1]
    low = next(row for row in height if row["vertical_difference_band"] == "-0.2:0.2")
    raised = next(row for row in height if row["vertical_difference_band"] == "0.5:1")
    add("GOOSE", "Low rock geometry is associated with ground confusion",
        f"With a ground/ground-cover reference within 1 m in XY, {float(low['ground_category_percent']):.2f}% of {low['points']} rock points within ±0.2 m vertically are called ground, versus {float(raised['ground_category_percent']):.2f}% of {raised['points']} at 0.5–1 m.",
        "Include low protruding rocks when designing an off-road follow-up.",
        "Nearest-point height proxy in one case, not validated object height or an isolated causal geometry effect; snow causality unproven.", ["docs/evidence/goose-failure-causes/nearest_ground_diagnostic.csv"], "goose.ground_height_proxy")
    s = facts["stone"]
    lake_ground, lake_raised = s["lake"]["aligned/near_ground_geometry"], s["lake"]["aligned/raised_geometry"]
    stone_source = ["docs/evidence/stone-environments/comparison.csv", "docs/stone-environments-followup.md"]
    add("STONE", "Radar ground support and raised-geometry support are different questions",
        f"In the lake recording, aligned radar supports {lake_ground['radar_percent']:.2f}% of {lake_ground['reference_voxels']:,} near-ground reference voxel observations and {lake_raised['radar_percent']:.2f}% of {lake_raised['reference_voxels']:,} raised-geometry observations.",
        "Separate ground mapping from the study of protruding obstacles.",
        "LiDAR-derived reference, 0.8 m tolerance and declared ROI; physical radar extrinsics and visibility unresolved; conditional descriptive result.", stone_source, "stone.lake")
    f = s["farmland"]
    add("STONE", "An unresolved coordinate origin can reverse a terrain conclusion",
        f"Farmland radar support is {f['aligned/raised_geometry']['radar_percent']:.2f}% raised versus {f['aligned/near_ground_geometry']['radar_percent']:.2f}% ground with the bridged origin; the ROS origin gives {f['ros_origin/raised_geometry']['radar_percent']:.2f}% raised versus {f['ros_origin/near_ground_geometry']['radar_percent']:.2f}% ground.",
        "Obtain independently validated numerical radar-to-LiDAR transforms before ranking terrain performance.",
        "Both conventions are sensitivity assumptions, not a proven calibration or complete uncertainty interval.", stone_source, "stone.farmland")
    add("STONE", "One recording does not capture the variation in radar ground support",
        f"With the aligned convention, pooled ground support is {s['farmland']['aligned/near_ground_geometry']['radar_percent']:.2f}% in farmland, {lake_ground['radar_percent']:.2f}% in lake and {s['land']['aligned/near_ground_geometry']['radar_percent']:.2f}% in land, from 20 sampled frames per recording.",
        "Retain environment-specific results rather than reporting one off-road percentage.",
        "Recording names are publisher categories, not confirmed weather/terrain treatments; calibration and reference bias prevent a causal environment claim.", stone_source, "stone")
    fog = facts["radiate"]
    add("RADIATE", "Radar can retain visible evidence in LiDAR-empty annotated fog footprints",
        f"At 50–75 m, {fog['far']['radar_strict']}/{fog['far']['observations']} vehicle observations pass the >20-level local radar contrast criterion, while {fog['far']['lidar_any']}/{fog['far']['observations']} exact footprints contain above-ground LiDAR returns.",
        "The fog case motivates a matched weather/fusion experiment and prevents a blanket sensor ranking.",
        "Radar-derived labels, four tracks across the pilot, no clear-weather control; signal contrast is not detection accuracy or proof that fog caused LiDAR absence.", ["docs/evidence/radiate-fog/observations.csv", "docs/radiate-fog-pilot.md"], "radiate.far")
    add("RADIATE", "Brightness alone also passes many unlabelled control regions",
        f"The basic radar contrast test passes {fog['controls_basic_pass']}/{fog['controls']} unlabelled controls; the >20-level test passes {fog['controls_strict_pass']}/{fog['controls']}. At 50–75 m, the strict test passes {fog['far_controls']['strict_pass']}/{fog['far_controls']['observations']} controls.",
        "Use background controls and threshold sensitivity when presenting a bright radar footprint.",
        "Controls are unlabelled, not verified empty negatives; these fractions are not false-positive rates or independent significance tests.", ["docs/evidence/radiate-fog/unlabelled_controls.csv"], "radiate.far_controls")
    expanded = next(row for row in fog["margin_sensitivity"] if row["band_m"] == "50-75" and float(row["margin_m"]) == 1)
    add("RADIATE", "The far LiDAR sparsity persists under an optimistic footprint/timing sensitivity",
        f"At 50–75 m, a 1 m footprint expansion gives LiDAR support in {expanded['lidar_any']}/{expanded['observations']} observations; allowing either adjacent scan as well gives {expanded['lidar_any_adjacent']}/{expanded['observations']}.",
        "A small footprint expansion alone does not account for all LiDAR-empty far footprints in this pilot.",
        "Future/adjacent scans are an optimistic offline sensitivity, not a real-time sensor score; target/ego motion and occlusion remain unresolved.", ["docs/evidence/radiate-fog/summary.csv"], "radiate.margin_sensitivity")
    extra_source = ["results/evidence/findings-oct01/additional-datasets/boreas_scans.csv", "results/evidence/findings-oct01/additional-datasets/manifest.json"]
    add("Boreas", "A close file timestamp does not mean the whole scans were simultaneous",
        f"Three newly decoded radar scans span {min(float(row['radar_span_ms']) for row in scans):.3f}–{max(float(row['radar_span_ms']) for row in scans):.3f} ms each; the nearest LiDAR scans span {min(float(row['lidar_span_ms']) for row in scans):.3f}–{max(float(row['lidar_span_ms']) for row in scans):.3f} ms. File offsets range from {min(float(row['file_offset_ms']) for row in scans):+.3f} to {max(float(row['file_offset_ms']) for row in scans):+.3f} ms.",
        "Deskew rolling scans using individual point/azimuth timestamps when moving scenes are compared.",
        "First three chronological scan pairs from one sequence; no motion-error magnitude, weather effect or object accuracy measured.", extra_source, "boreas_scans", True)
    add("Boreas", "Recorded range support depends on the radar representation",
        f"Each sample radar image has {scans[0]['radar_range_bins']} range bins, with the documented offset giving a last-bin centre of {float(scans[0]['last_bin_center_m']):.4f} m. Each paired LiDAR scan contains returns beyond 200 m, with observed maxima {min(float(row['lidar_max_spherical_range_m']) for row in scans):.2f}–{max(float(row['lidar_max_spherical_range_m']) for row in scans):.2f} m.",
        "Do not score this recorded radar image outside its stored range and interpret the absence as failed object recognition.",
        "Radar bins are intensity samples, LiDAR values are spherical ranges; no shared object/visibility denominator or general hardware range ranking.", extra_source, "boreas_scans", True)
    w = splits["splits"]["opt3d"]
    wild_source = ["results/evidence/findings-oct01/additional-datasets/wildscenes_splits.json", "results/evidence/findings-oct01/additional-datasets/manifest.json"]
    add("WildScenes", "The official 3D validation subset has narrow recording coverage",
        f"The pinned official opt3d split contains {w['train']['frames']:,} training, {w['val']['frames']} validation and {w['test']['frames']:,} test frames. All {w['val']['frames']} validation entries belong to K-01; training and test each cover five recording groups.",
        "Use the independent terrain test groups and group-specific scores when checking generalisation from GOOSE.",
        "Metadata audit only; no raw labels or inference. Shared recording groups are not proof of leakage, and do not establish geographic independence.", wild_source, "wildscenes_splits.splits.opt3d", True)
    cross = splits["cross_dimension_id_overlap"]
    w2 = splits["splits"]["opt2d"]
    add("WildScenes", "Camera and LiDAR split totals are not automatically a paired population",
        f"The opt2d test has {w2['test']['frames']:,} frames and opt3d test {w['test']['frames']:,}; only {cross['test/test']:,} frame IDs occur in both. No exact train/val/test frame IDs overlap within either dimension.",
        "Join identical frame IDs before any camera-versus-LiDAR terrain comparison.",
        "Identity check alone does not validate timing, projected-label completeness, spatial disjointness or an accuracy comparison.", wild_source, "wildscenes_splits.cross_dimension_id_overlap", True)
    return findings

def render():
    facts = json.loads((EVIDENCE / "measurements.json").read_text(encoding="utf-8"))
    with (EVIDENCE / "additional-datasets/boreas_scans.csv").open(newline="", encoding="utf-8") as stream:
        scans = list(csv.DictReader(stream))
    splits = json.loads((EVIDENCE / "additional-datasets/wildscenes_splits.json").read_text())
    findings = build_findings(facts, scans, splits)
    for finding in findings:
        for source in finding["sources"]:
            if not (ROOT / source).is_file():
                raise ValueError("Missing finding source: " + source)
    (EVIDENCE / "findings.json").write_text(json.dumps({"date": "2026-10-01", "count": len(findings), "findings": findings}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Dataset findings — 1 October 2026", "", f"{len(findings)} supported findings across TruckScenes, TruckDrive, GOOSE, STONE, RADIATE, Boreas and WildScenes.", "",
             "These are research findings with denominators and limits. Sensor support means recorded returns inside known annotations; it is not detector recall. GOOSE scores concern labelled returned points. STONE results are conditional on unresolved extrinsics. The weather pilot is not a controlled causal test.", "",
             "The first 28 findings consolidate and recompute existing project evidence. F29–F32 add a new bounded Boreas sample and a WildScenes metadata audit. New reanalysis also profiles equal-scene TruckScenes support and its radar-only class composition. No new GPU inference or full benchmark was run in this update. The finding count is not evidence of twelve weeks of labour.", "",
             "See [additional dataset selection and LiDAR/radar evidence](additional-dataset-findings-oct01.md). Reproduction: `python scripts/analyse_findings_oct01.py`, then `python scripts/render_findings_oct01.py`; the additional-data acquisition/audit command is documented in EXP-0029.", ""]
    for finding in findings:
        lines += [f"## {finding['id']} — {finding['title']}", "", f"**Dataset / evidence:** {finding['dataset']} · {finding['evidence_type']}", "", finding["statement"], "",
                  f"**Implication:** {finding['implication']}", "", f"**Limit:** {finding['limits']}", "",
                  "**Sources:** " + "; ".join(f"[{Path(source).name}](../{source})" for source in finding["sources"]), ""]
    (ROOT / "docs/dataset-findings-oct01.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {len(findings)} findings; all cited local evidence exists.")

if __name__ == "__main__":
    render()
