#!/usr/bin/env python3
"""Recompute descriptive findings from committed evidence, retaining denominators."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/evidence/findings-oct01"

def support(rows, threshold=1):
    if not isinstance(threshold, int) or threshold < 1:
        raise ValueError("Return threshold must be a positive integer")
    counts = Counter()
    for row in rows:
        lidar_count, radar_count = int(row["lidar_points"]), int(row["radar_points"])
        if min(lidar_count, radar_count) < 0:
            raise ValueError("Return counts cannot be negative")
        lidar = lidar_count >= threshold
        radar = radar_count >= threshold
        counts["both" if lidar and radar else "lidar_only" if lidar else "radar_only" if radar else "neither"] += 1
    n = len(rows)
    result = {key: counts[key] for key in ("both", "lidar_only", "radar_only", "neither")}
    result.update(observations=n, scenes=len({row["scene"] for row in rows}),
                  tracks=len({(row["scene"], row["instance_token"]) for row in rows}))
    for key, numerator in (("lidar_percent", counts["both"]+counts["lidar_only"]),
                           ("radar_percent", counts["both"]+counts["radar_only"]),
                           ("union_percent", n-counts["neither"])):
        result[key] = 100*numerator/n if n else None
    groups = defaultdict(list)
    for row in rows:
        groups[row["scene"]].append(row)
    differences = [100*sum((int(row["lidar_points"]) >= threshold)-(int(row["radar_points"]) >= threshold)
                           for row in group)/len(group) for group in groups.values()]
    result["equal_scene_difference_pp"] = statistics.mean(differences) if differences else None
    result["min_scene_difference_pp"] = min(differences) if differences else None
    result["leave_one_scene_out_min_pp"] = min((sum(differences)-value)/(len(differences)-1)
                                                for value in differences) if len(differences) > 1 else None
    return result

def exact(rows):
    return [row for row in rows if float(row["margin_m"]) == 0]

def identity(row):
    return row["scene"], row["annotation_token"], float(row["margin_m"])

def match_rows(first, second):
    def index(rows):
        output = {identity(row): row for row in rows}
        if len(output) != len(rows):
            raise ValueError("Duplicate scene-qualified annotation observation")
        return output
    a, b = index(first), index(second)
    keys = sorted(a.keys() & b.keys())
    for key in keys:
        if a[key]["category"] != b[key]["category"] or a[key]["instance_token"] != b[key]["instance_token"]:
            raise ValueError("Compared annotation identity changed")
    return [a[key] for key in keys], [b[key] for key in keys]

def analyse(output):
    output.mkdir(parents=True, exist_ok=True)
    inputs = {}
    def load(relative):
        path = ROOT / relative
        data = path.read_bytes()
        inputs[relative] = hashlib.sha256(data).hexdigest()
        if path.suffix == ".json":
            return json.loads(data)
        with path.open(newline="", encoding="utf-8-sig") as stream:
            return list(csv.DictReader(stream))
    ts_path = "docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv"
    ts_all = load(ts_path)
    ts = exact(ts_all)
    expanded = [row for row in ts_all if float(row["margin_m"]) == 0.5]
    if {(row["scene"], row["annotation_token"]) for row in ts} != {(row["scene"], row["annotation_token"]) for row in expanded}:
        raise ValueError("Exact and expanded boxes do not have identical observations")
    rigid, point = match_rows(exact(load("docs/evidence/truckscenes/paired-all-sensor-support/object_counts.csv")), ts)
    if len(point) != len(ts):
        raise ValueError("Rigid/per-point comparison lost observations")
    facts = {"truckscenes": {"population": support(ts), "rigid_matched": support(rigid),
                             "expanded": support(expanded),
                             "by_range": {band: support([row for row in ts if row["band_m"] == band])
                                          for band in ("0-50", "50-100", "100-150", "150-400")},
                             "max_object_range_m": max(float(row["range_m"]) for row in ts),
                             "radar_count_agreements": sum(row["radar_points"] == row["publisher_radar_points"] for row in ts),
                             "lidar_count_agreements": sum(row["lidar_points"] == row["publisher_lidar_points"] for row in ts)}}
    radar_only = [row for row in ts if int(row["radar_points"]) > 0 and int(row["lidar_points"]) == 0]
    facts["truckscenes"]["radar_only_classes"] = dict(sorted(Counter(row["category"] for row in radar_only).items()))
    facts["truckscenes"]["near_classes"] = {category: support([row for row in ts if row["category"] == category and float(row["range_m"]) < 25])
                                             for category in ("vehicle.car", "vehicle.truck", "human.pedestrian.adult", "movable_object.trafficcone")}
    static, aligned = [], []
    for scene in ("scene_28_1", "scene_28_6", "scene_28_12", "scene_28_18", "scene_28_24"):
        a, b = match_rows(load(f"docs/evidence/truckdrive-multiscene/{scene}/static/object_counts.csv"),
                          load(f"docs/evidence/truckdrive-multiscene/{scene}/aligned/object_counts.csv"))
        static.extend(a)
        aligned.extend(b)
    td = {}
    for variant, rows in (("static", static), ("aligned", aligned)):
        vehicles = [row for row in exact(rows) if row["category"].startswith("Vehicle") and 200 <= float(row["range_m"]) < 400]
        barrels = [row for row in exact(rows) if row["category"] == "RoadObstruction-Barrel" and 100 <= float(row["range_m"]) < 150]
        td[variant] = {"vehicles_200_400": support(vehicles), "vehicles_200_400_min3": support(vehicles, 3),
                       "barrels_100_150": support(barrels)}
    facts["truckdrive"] = td
    facts["matched_tracks"] = [row for row in load("docs/evidence/missing-support/matched_track_summary.csv")
                                if float(row["margin_m"]) == 0 and
                                ((row["dataset"] == "TruckScenes" and row["category"] == "vehicle.car" and row["near_band"] == "0-50" and row["far_band"] == "50-100")
                                 or (row["dataset"] == "TruckDrive" and row["category"] == "Vehicle-Passenger" and row["near_band"] == "100-150" and row["far_band"] == "200-400"))]
    scenario = load("docs/evidence/goose-stratified/ground/scenario_group_confusion.csv")
    fine = load("docs/evidence/goose-stratified/ground/saved_fine_confusion.csv")
    goose = {}
    for group in ("ground_surface", "obstacle_candidate"):
        goose[group] = {}
        for band in ("0-25", "100-150", "150+"):
            rows = [row for row in scenario if row["true_group"] == group and row["band_m"] == band and int(row["points"]) > 0]
            points = sum(int(row["points"]) for row in rows)
            ground = sum(int(row["ground_category_points"]) for row in rows)
            goose[group][band] = {"points": points, "called_ground": ground,
                                  "pooled_ground_percent": 100*ground/points if points else None,
                                  "equal_scenario_ground_percent": statistics.mean(100*int(row["ground_category_points"])/int(row["points"]) for row in rows) if rows else None,
                                  "largest_scenario_share_percent": 100*max(int(row["points"]) for row in rows)/points if points else None}
    goose["fine_ground"] = {}
    for cls, band in (("rock", "0-25"), ("building", "0-25"), ("building", "100-150")):
        rows = [row for row in fine if row["true_class"] == cls and row["band_m"] == band]
        n = sum(int(row["points"]) for row in rows)
        errors = sum(int(row["points"]) for row in rows if row["predicted_class"] in ("natural_ground", "artificial_ground"))
        goose["fine_ground"][cls+"/"+band] = {"points": n, "ground_errors": errors, "ground_error_percent": 100*errors/n}
    goose["context"] = load("docs/evidence/goose-failure-causes/context_pooled.csv")
    goose["error_concentration"] = load("docs/evidence/goose-error-cases/summary.csv")
    goose["voxel_ambiguity"] = load("docs/evidence/goose-failure-causes/voxel_ambiguity.csv")
    goose["ground_height_proxy"] = load("docs/evidence/goose-failure-causes/nearest_ground_diagnostic.csv")
    flight_classes = load("docs/evidence/missing-support/goose-saved/raw_class_errors.csv")
    goose["flight_surface_errors"] = [row for row in flight_classes if row["raw_class"] == "asphalt" and row["band_m"] == "100-150"]
    goose["flight_far_vegetation_points"] = sum(int(row["points"]) for row in flight_classes if row["model_truth"] == "vegetation" and row["band_m"] == "150+")
    goose["flight_range_accuracy"] = load("docs/evidence/missing-support/goose-saved/range_accuracy.csv")
    facts["goose"] = goose
    stone = defaultdict(lambda: defaultdict(list))
    for row in load("docs/evidence/stone-environments/comparison.csv"):
        if row["elevation_deg"] == "10" and float(row["tolerance_m"]) == 0.8:
            stone[row["recording"]][row["variant"]+"/"+row["group"]].append(row)
    facts["stone"] = {}
    for recording, groups in stone.items():
        facts["stone"][recording] = {}
        for group, rows in groups.items():
            n = sum(int(row["reference_voxels"]) for row in rows)
            facts["stone"][recording][group] = {"reference_voxels": n,
                                                  "lidar_percent": 100*sum(int(row["lidar_supported"]) for row in rows)/n,
                                                  "radar_percent": 100*sum(int(row["radar_supported"]) for row in rows)/n}
    fog = [row for row in load("docs/evidence/radiate-fog/observations.csv") if float(row["margin_m"]) == 0]
    controls = load("docs/evidence/radiate-fog/unlabelled_controls.csv")
    facts["radiate"] = {"observations": len(fog), "frames": len({row["frame"] for row in fog}),
                        "tracks": len({row["track"] for row in fog}), "controls": len(controls),
                        "controls_basic_pass": sum(int(row["radar_contrast_pass"]) for row in controls),
                        "controls_strict_pass": sum(int(row["radar_contrast_gap20"]) for row in controls),
                        "far": {"observations": len([row for row in fog if row["band_m"] == "50-75"]),
                                "lidar_any": sum(int(row["lidar_above_ground_returns"]) > 0 for row in fog if row["band_m"] == "50-75"),
                                "radar_strict": sum(int(row["radar_contrast_gap20"]) for row in fog if row["band_m"] == "50-75")},
                        "far_controls": {"observations": len([row for row in controls if row["band_m"] == "50-75"]),
                                         "strict_pass": sum(int(row["radar_contrast_gap20"]) for row in controls if row["band_m"] == "50-75")}}
    facts["radiate"]["margin_sensitivity"] = load("docs/evidence/radiate-fog/summary.csv")
    (output / "measurements.json").write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps({"date": "2026-10-01", "inputs_sha256": inputs,
        "method": "Reanalysis of committed count/confusion evidence. Scene-qualified identities, paired timing subsets, exact denominators; empty rates are null.",
        "limits": "No new raw recount or model inference. This verifies arithmetic and provenance, not independent physical calibration or annotation correctness."}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input_tables": len(inputs), "truckscenes_observations": len(ts),
                      "truckdrive_aligned_long_range": td["aligned"]["vehicles_200_400"],
                      "goose_rock_near": goose["fine_ground"]["rock/0-25"], "radiate_far": facts["radiate"]["far"]}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    analyse(parser.parse_args().output_dir)
