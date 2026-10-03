"""Class/range and controlled terrain follow-ups with explicit populations.

No detector accuracy is inferred from geometric sensor support. Raw data stays
outside Git; saved predictions are verified against the frozen input selection.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np

from analyse_findings_oct01 import support, match_rows
from analyse_goose_saved_errors import confusion, NAMES
from compare_goose_context import canonical_config
from compare_truckscenes_raw import write_csv

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/evidence/sprint-followup-oct01"
RANGES = ((0,25), (25,50), (50,100), (100,150), (150,200), (200,400))


def hash_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def hash_repository_text(path):
    """Hash UTF-8 text with LF endings so Git checkouts reproduce the digest."""
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def equal_track_support(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["scene"], row["instance_token"]].append(row)
    scores = [support(group) for group in groups.values()]
    return {"equal_track_" + sensor + "_percent": statistics.mean(score[sensor + "_percent"] for score in scores) if scores else None
            for sensor in ("lidar", "radar")}


def class_range_rows(rows, dataset):
    output = []
    for category in sorted({row["category"] for row in rows}):
        for low, high in RANGES:
            group = [row for row in rows if row["category"] == category and low <= float(row["range_m"]) < high]
            output.append(dict(dataset=dataset, category=category, band_m=f"{low}-{high}", **support(group), **equal_track_support(group)))
    return output


def terrain_summary(counts):
    points, correct, ground = map(int, counts)
    if min(points, correct, ground) < 0 or max(correct, ground) > points:
        raise ValueError("Invalid class counts")
    return dict(points=points, correct_points=correct, called_ground_points=ground,
                correct_percent=100*correct/points if points else None,
                called_ground_percent=100*ground/points if points else None)


def analyse_sensors(args):
    sources = {}
    def load(relative):
        path = ROOT / relative
        sources[relative] = hash_repository_text(path)
        with path.open(newline="", encoding="utf-8-sig") as stream:
            return list(csv.DictReader(stream))
    original = load("docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv")
    rows = [row for row in original if float(row["margin_m"]) == 0]
    metadata = args.truckscenes_root / "v1.2-mini"
    annotations = {row["token"]: row for row in json.loads((metadata / "sample_annotation.json").read_text())}
    visibility = {row["token"]: row["level"] for row in json.loads((metadata / "visibility.json").read_text())}
    attributes = {row["token"]: row["name"] for row in json.loads((metadata / "attribute.json").read_text())}
    prior = json.loads((ROOT / "docs/evidence/truckscenes/paired-point-motion-support/manifest.json").read_text())
    for name in ("sample_annotation.json", "visibility.json", "attribute.json"):
        sha = hash_file(metadata / name)
        if sha != prior["metadata_sha256"][name]:
            raise ValueError("TruckScenes metadata changed from verified point recount")
        sources["external:TruckScenes/v1.2-mini/" + name] = sha
    for row in rows:
        annotation = annotations[row["annotation_token"]]
        if annotation["sample_token"] != row["sample_token"] or annotation["instance_token"] != row["instance_token"]:
            raise ValueError("Metadata join changed observation identity")
        row["camera_visibility_level"] = str(visibility[annotation["visibility_token"]])
        row["attributes"] = ";".join(attributes[token] for token in annotation["attribute_tokens"])
    class_ranges = class_range_rows(rows, "TruckScenes mini existing complete eligible sample")
    write_csv(OUTPUT / "class_range_support.csv", class_ranges)
    additional = []
    for category in sorted({row["category"] for row in rows}):
        for low, high in ((0,25), (25,50), (50,100)):
            group = [row for row in rows if row["category"] == category and low <= float(row["range_m"]) < high]
            for level in (1,2,3,4):
                chosen = [row for row in group if row["camera_visibility_level"] == str(level)]
                additional.append(dict(category=category, band_m=f"{low}-{high}", visibility_level=level,
                                       **support(chosen), **equal_track_support(chosen)))
    write_csv(OUTPUT / "visibility_support.csv", additional)
    scene_metadata = prior["scene_descriptions"]
    weather = []
    for condition in ("clear", "overcast", "rain", "snow"):
        for category in ("vehicle.car", "vehicle.truck", "human.pedestrian.adult", "movable_object.trafficcone"):
            for low, high in ((0,25), (25,50), (50,100)):
                group = [row for row in rows if row["category"] == category and low <= float(row["range_m"]) < high
                         and f"weather.{condition};" in scene_metadata[row["scene"]]]
                weather.append(dict(weather=condition, category=category, band_m=f"{low}-{high}", **support(group), **equal_track_support(group)))
    write_csv(OUTPUT / "weather_support.csv", weather)
    static, aligned = [], []
    for scene in ("scene_28_3", "scene_28_15"):
        first = load(f"results/evidence/sprint-followup-oct01/truckdrive/{scene}/static/object_counts.csv")
        second = load(f"results/evidence/sprint-followup-oct01/truckdrive/{scene}/aligned/object_counts.csv")
        a, b = match_rows(first, second)
        static.extend(a)
        aligned.extend(b)
    summaries = []
    for variant, all_rows in (("static", static), ("aligned", aligned)):
        for margin in (0, .5):
            population = [row for row in all_rows if float(row["margin_m"]) == margin]
            for label, group in (("all", population), ("vehicles", [row for row in population if row["category"].startswith("Vehicle")])):
                for low, high in ((0,50), (50,100), (100,150), (150,200), (200,400)):
                    chosen = [row for row in group if low <= float(row["range_m"]) < high]
                    summaries.append(dict(variant=variant, margin_m=margin, cohort=label, band_m=f"{low}-{high}",
                                          **support(chosen), **equal_track_support(chosen)))
    write_csv(OUTPUT / "truckdrive_holdout_support.csv", summaries)
    write_csv(OUTPUT / "truckdrive_holdout_classes.csv", class_range_rows([r for r in aligned if float(r["margin_m"]) == 0], "TruckDrive unseen clips 28_3,28_15"))
    manifest = dict(source_hash_definition="Repository text: UTF-8 with LF endings; external raw files: exact bytes",
                    sources_sha256=sources, existing_truckscenes_observations=len(rows),
                    truckdrive_static_observations=sum(float(row["margin_m"]) == 0 for row in static),
                    truckdrive_aligned_observations=sum(float(row["margin_m"]) == 0 for row in aligned),
                    limits=["Geometric sensor evidence, not detector recall/precision", "Repeated observations and LiDAR-conditioned annotations",
                            "Visibility labels concern all-camera panoramic views, not radar visibility", "Weather is descriptive across different recordings, not causal treatment"])
    (OUTPUT / "sensor_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=2))


def analyse_terrain(args):
    output = OUTPUT / "terrain"
    selection = json.loads((output / "selection.json").read_text())
    previous = json.loads((ROOT / "docs/evidence/goose-failure-causes/context_manifest.json").read_text())
    if hash_file(args.checkpoint) != previous["checkpoint_sha256"] or hash_file(args.mapping) != previous["mapping_sha256"]:
        raise ValueError("Published checkpoint or label mapping changed")
    expected = {row["frame"] for row in selection["inputs"]}
    labels = list(csv.DictReader(args.mapping.open(encoding="utf-8-sig")))
    remap = {int(row["label_key"]): (0 if int(row["challege_category_id"]) == 8 else int(row["challege_category_id"])) for row in labels}
    names = {int(row["label_key"]): row["class_name"] for row in labels}
    configs, runs = {}, {}
    for variant, patch in (("p64",64), ("p64repeat",64), ("p128",128)):
        run = args.runs / variant
        config = (run / "config.py").read_text()
        log = (run / "test.log").read_text()
        if "End Evaluation" not in log or "loaded pred and label" in log:
            raise ValueError("Incomplete evaluation or reused predictions")
        if {p.name.removesuffix("_pred.npy") for p in (run / "result").glob("*_pred.npy")} != expected:
            raise ValueError("Prediction set differs from frozen selection")
        if f"enc_patch_size=[{', '.join([str(patch)]*5)}]" not in config or f"dec_patch_size=[{', '.join([str(patch)]*4)}]" not in config:
            raise ValueError("Wrong patch size")
        configs[variant] = canonical_config(config)
        runs[variant] = dict(config_sha256=hash_file(run / "config.py"), log_sha256=hash_file(run / "test.log"),
                             complete=True, prediction_sha256={})
    if len(set(configs.values())) != 1:
        raise ValueError("Unexpected config differences")
    frame_rows, fine_rows = [], []
    pooled, scenario = defaultdict(lambda: np.zeros(3, dtype=np.int64)), defaultdict(lambda: np.zeros(3, dtype=np.int64))
    changed_rows = []
    for entry in selection["inputs"]:
        name, group = entry["frame"], entry["scenario"]
        paths = {"scan": args.goose_root / "lidar/val" / group / name,
                 "label": args.goose_root / "labels/val" / group / name.replace("_vls128.bin", "_goose.label"),
                 "challenge_label": args.goose_root / "labels_challenge/val" / group / name.replace("_vls128.bin", "_goose.label")}
        if any(hash_file(path) != entry["sha256"][key] for key, path in paths.items()):
            raise ValueError("Frozen input changed")
        xyz = np.fromfile(paths["scan"], dtype="<f4").reshape(-1,4)
        raw = (np.fromfile(paths["label"], dtype="<u4") & 65535).astype(int)
        truth = np.array([remap[int(value)] for value in raw])
        actual = np.fromfile(paths["challenge_label"], dtype="<u4") & 65535
        actual[actual == 8] = 0
        if len(raw) != entry["points"] or len(xyz) != len(raw) or not np.isfinite(xyz).all() or not np.array_equal(truth, actual):
            raise ValueError("Invalid raw pairing or challenge mapping")
        predictions = {}
        distance = np.hypot(xyz[:,0].astype(float), xyz[:,1].astype(float))
        for variant in runs:
            path = args.runs / variant / "result" / (name + "_pred.npy")
            pred = np.load(path, allow_pickle=False)
            matrix = confusion(truth, pred)
            predictions[variant] = pred
            runs[variant]["prediction_sha256"][name] = hash_file(path)
            frame_rows.append(dict(frame=name, scenario=group, variant=variant,
                                   **terrain_summary((len(raw), matrix.trace(), np.isin(pred,(2,3)).sum()))))
            for low, high in ((0,25), (25,50), (50,100), (100,150), (150,float("inf")), (0,float("inf"))):
                band = f"{low}-{high}" if np.isfinite(high) else f"{low}+"
                for key in np.unique(raw):
                    mask = (raw == key) & (distance >= low) & (distance < high)
                    counts = np.array([mask.sum(), (pred[mask] == truth[mask]).sum(), np.isin(pred[mask], (2,3)).sum()])
                    fine_rows.append(dict(frame=name, scenario=group, variant=variant, band_m=band,
                                          category=names[int(key)], model_truth=NAMES[remap[int(key)]], **terrain_summary(counts)))
                    pooled[variant,band,names[int(key)],NAMES[remap[int(key)]]] += counts
                    scenario[variant,band,names[int(key)],group] += counts
        if not np.array_equal(predictions["p64"], predictions["p64repeat"]):
            raise ValueError("Repeated baseline is not prediction-identical")
        a, b = predictions["p64"], predictions["p128"]
        for key in np.unique(raw):
            mask = raw == key
            changed_rows.append(dict(frame=name, scenario=group, category=names[int(key)], points=int(mask.sum()),
                 predictions_changed=int((a[mask] != b[mask]).sum()),
                 wrong_to_correct=int(((a[mask] != truth[mask]) & (b[mask] == truth[mask])).sum()),
                 correct_to_wrong=int(((a[mask] == truth[mask]) & (b[mask] != truth[mask])).sum())))
    pooled_rows = []
    for (variant,band,category,model_truth), counts in sorted(pooled.items()):
        groups = [value for (v,b,c,g), value in scenario.items() if (v,b,c) == (variant,band,category) and value[0] > 0]
        pooled_rows.append(dict(variant=variant, band_m=band, category=category, model_truth=model_truth,
                               recordings=len(groups), **terrain_summary(counts),
                               equal_recording_correct_percent=statistics.mean(100*x[1]/x[0] for x in groups) if groups else None))
    write_csv(output / "frame_comparison.csv", frame_rows)
    write_csv(output / "fine_class_comparison.csv", fine_rows)
    write_csv(output / "pooled_class_comparison.csv", pooled_rows)
    write_csv(output / "prediction_changes.csv", changed_rows)
    execution = json.loads(args.execution.read_text())
    if len(execution) != 3 or any(row["status"] != "success" or row["exit_code"] != 0 for row in execution):
        raise ValueError("Run exit evidence missing")
    (output / "execution.json").write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = dict(frames=selection["frames"], points=selection["points"], baseline_repeat_identical=True,
                    config_differences="output path and attention patch sizes only", runs=runs,
                    selection_sha256=hash_repository_text(output / "selection.json"), mapping_sha256=hash_file(args.mapping),
                    checkpoint_sha256=hash_file(args.checkpoint), execution_sha256=hash_file(args.execution),
                    limits="Seven unseen frames in existing validation recordings; excluded tuning scene; no external dataset or full benchmark. Fine labels judged against eight-class model taxonomy. Point accuracy is not object recall or safe traversability.")
    manifest["selection_hash_definition"] = "Repository UTF-8 text with LF endings"
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k:manifest[k] for k in ("frames","points","baseline_repeat_identical","limits")}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("sensors","terrain"))
    ap.add_argument("--truckscenes-root", type=Path)
    ap.add_argument("--goose-root", type=Path)
    ap.add_argument("--runs", type=Path)
    ap.add_argument("--mapping", type=Path)
    ap.add_argument("--checkpoint", type=Path)
    ap.add_argument("--execution", type=Path)
    args = ap.parse_args()
    required = ("truckscenes_root",) if args.mode == "sensors" else ("goose_root","runs","mapping","checkpoint","execution")
    if any(getattr(args, key) is None for key in required):
        ap.error("Missing required paths for " + args.mode)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (analyse_sensors if args.mode == "sensors" else analyse_terrain)(args)


if __name__ == "__main__":
    main()
