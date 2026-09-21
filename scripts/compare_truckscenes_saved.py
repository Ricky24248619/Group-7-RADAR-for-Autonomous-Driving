"""Compare committed TruckScenes outputs without loading data or rerunning inference.

Run from any directory: python scripts/compare_truckscenes_saved.py
Outputs: docs/evidence/truckscenes/comparison/ (JSON, CSVs and PNGs).
This is a saved-output diagnostic, not a new evaluation or a sensor ranking.
"""

from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "one_predictions": "scripts/results_mini_val_fcos3d.json",
    "four_predictions": "scripts/results_mini_val_fcos3d_4cam.json",
    "one_metrics": "scripts/fcos3d_truckscenes_metrics_summary.json",
    "four_metrics": "scripts/fcos3d_truckscenes_metrics_summary_4cam.json",
    "coverage": "TruckScenes - Fatima/range-bands.csv",
}


def compare_cameras(one, four, one_metrics, four_metrics):
    """Require identical saved sample sets, input flags and evaluator configuration."""
    a, b = one["results"], four["results"]
    if not a or a.keys() != b.keys():
        raise ValueError("Camera submissions must contain identical nonempty sample sets")
    config = one_metrics["all"]["cfg"]
    if config != four_metrics["all"]["cfg"]:
        raise ValueError("Evaluator configurations differ")
    flags = {"use_camera": True, "use_lidar": False, "use_radar": False,
             "use_map": False, "use_external": False,
             "use_future_frames": False, "use_tta": False}
    for artifact in (one, four, one_metrics, four_metrics):
        if any(artifact["meta"].get(k) is not v for k, v in flags.items()):
            raise ValueError("Input flags do not describe matching camera-only runs")

    samples = []
    for token in sorted(a):
        for boxes in (a[token], b[token]):
            if any(box["sample_token"] != token for box in boxes):
                raise ValueError("Box token disagrees with its sample key")
        ca = Counter(json.dumps(box, sort_keys=True) for box in a[token])
        cb = Counter(json.dumps(box, sort_keys=True) for box in b[token])
        retained = sum((ca & cb).values())
        samples.append({"sample_token": token, "one_camera_boxes": len(a[token]),
                        "four_camera_boxes": len(b[token]),
                        "exactly_retained_boxes": retained,
                        "added_boxes": sum((cb - ca).values()),
                        "removed_boxes": sum((ca - cb).values())})

    classes = sorted(config["class_range"])
    thresholds = config["dist_ths"]
    class_rows = []
    for name in classes:
        for threshold in thresholds:
            values = [m["all"]["label_aps"][name][str(float(threshold))]
                      for m in (one_metrics, four_metrics)]
            if any(not math.isfinite(x) or not 0 <= x <= 1 for x in values):
                raise ValueError("AP must be finite and between zero and one")
            class_rows.append({"class": name, "matching_threshold_m": threshold,
                               "one_camera_ap": values[0], "four_camera_ap": values[1]})
    for m in (one_metrics, four_metrics):
        for name in classes:
            expected = statistics.mean(m["all"]["label_aps"][name].values())
            if not math.isclose(expected, m["all"]["mean_dist_aps"][name], abs_tol=1e-12):
                raise ValueError("Saved class AP disagrees with threshold average")
        expected = statistics.mean(m["all"]["mean_dist_aps"].values())
        if not math.isclose(expected, m["all"]["mean_ap"], abs_tol=1e-12):
            raise ValueError("Saved mAP disagrees with class average")

    summary = {
        "sample_count": len(samples),
        "one_camera_boxes": sum(x["one_camera_boxes"] for x in samples),
        "four_camera_boxes": sum(x["four_camera_boxes"] for x in samples),
        "one_camera_empty_entries": sum(not boxes for boxes in a.values()),
        "four_camera_empty_entries": sum(not boxes for boxes in b.values()),
        "exactly_retained_boxes": sum(x["exactly_retained_boxes"] for x in samples),
        "added_boxes": sum(x["added_boxes"] for x in samples),
        "removed_boxes": sum(x["removed_boxes"] for x in samples),
        "one_camera_map": one_metrics["all"]["mean_ap"],
        "four_camera_map": four_metrics["all"]["mean_ap"],
        "one_camera_nds": one_metrics["all"]["nd_score"],
        "four_camera_nds": four_metrics["all"]["nd_score"],
        "four_camera_map_without_traffic_cone": statistics.mean(
            four_metrics["all"]["mean_dist_aps"][c] for c in classes if c != "traffic_cone"),
        "four_camera_map_by_matching_threshold": {
            str(float(t)): statistics.mean(four_metrics["all"]["label_aps"][c][str(float(t))]
                                          for c in classes) for t in thresholds},
        "evaluator_config": config,
    }
    return summary, samples, class_rows


def summarize_coverage(rows):
    """Summarize >=150 m returns per available sample; zero denominator is undefined."""
    grouped = defaultdict(list)
    for row in rows:
        if row["scope"] == "per_sample":
            grouped[(row["sample_token"], row["modality"])].append(row)
    samples = []
    for (token, modality), group in sorted(grouped.items()):
        group.sort(key=lambda x: float(x["band_lower_m"]))
        bounds = [(float(x["band_lower_m"]), float(x["band_upper_m"])) for x in group]
        if bounds != [(0, 50), (50, 100), (100, 150), (150, 400), (400, math.inf)]:
            raise ValueError("Coverage needs the complete five-band working protocol")
        first = group[0]
        for key in ("denominator_points", "scene_name", "sample_index", "channel", "coordinate_frame"):
            if len({row[key] for row in group}) != 1:
                raise ValueError(f"Inconsistent coverage {key}")
        total = int(first["denominator_points"])
        counts = [int(x["point_count"]) for x in group]
        if min(counts) < 0 or sum(counts) != total:
            raise ValueError("Coverage bands do not sum to the denominator")
        distant = sum(counts[3:])
        samples.append({"sample_index": int(first["sample_index"]),
                        "sample_token": token, "scene_name": first["scene_name"],
                        "modality": modality, "channel": first["channel"],
                        "coordinate_frame": first["coordinate_frame"],
                        "total_returns": total, "returns_ge150m": distant,
                        "share_ge150m": distant / total if total else None})
    if not samples:
        raise ValueError("No per-sample coverage rows")
    summary = {}
    for modality in sorted({x["modality"] for x in samples}):
        group = [x for x in samples if x["modality"] == modality]
        shares = [x["share_ge150m"] for x in group if x["share_ge150m"] is not None]
        distant = sum(x["returns_ge150m"] for x in group)
        total = sum(x["total_returns"] for x in group)
        summary[modality] = {
            "sample_count": len(group), "total_returns": total, "returns_ge150m": distant,
            "samples_with_returns_ge150m": sum(x["returns_ge150m"] > 0 for x in group),
            "pooled_share_ge150m": distant / total if total else None,
            "median_sample_share_ge150m": statistics.median(shares) if shares else None,
            "min_sample_share_ge150m": min(shares) if shares else None,
            "max_sample_share_ge150m": max(shares) if shares else None,
            "largest_sample_fraction_of_distant_returns":
                max(x["returns_ge150m"] for x in group) / distant if distant else None,
        }
    return summary, samples


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_comparisons(output, coverage, classes):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    indices = sorted({x["sample_index"] for x in coverage})
    ymax = max(14, 120 * max(x["share_ge150m"] or 0 for x in coverage))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, modality in zip(axes, ("radar", "lidar")):
        group = sorted((x for x in coverage if x["modality"] == modality), key=lambda x: x["scene_name"])
        for row in group:
            index = row["sample_index"]
            if row["share_ge150m"] is not None:
                ax.scatter(index, 100 * row["share_ge150m"], color="#3168ba")
            else:
                ax.text(index, 0, "no data", rotation=90)
        ax.set(title=f"{group[0]['channel']} ({len(group)} samples)",
               xlabel="Manifest sample index", xticks=indices, ylim=(-0.5, ymax))
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Returns at >=150 m / this sample's returns (%)")
    fig.suptitle("Long-range return coverage varies between the sampled scenes")
    fig.text(0.02, 0.02, "Own-sensor planar distances; different fields of view. Top Front LiDAR is a tilted blind-spot Ouster.\n"
             "One sample per scene, ten scenes. Return coverage does not measure object-detection accuracy.", fontsize=9)
    fig.tight_layout(rect=(0, 0.12, 1, 0.95))
    fig.savefig(output / "coverage_by_sample.png", dpi=150, metadata={"Software": None})
    plt.close(fig)

    names = sorted({x["class"] for x in classes})
    thresholds = sorted({x["matching_threshold_m"] for x in classes})
    values = [[100 * next(x["four_camera_ap"] for x in classes
                         if x["class"] == name and x["matching_threshold_m"] == threshold)
               for threshold in thresholds] for name in names]
    fig, ax = plt.subplots(figsize=(8, 7))
    chart = ax.imshow(values, aspect="auto", vmin=0, vmax=max(20, max(map(max, values))), cmap="Blues")
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color="white" if value > 12 else "black")
    ax.set(xticks=range(len(thresholds)), xticklabels=[f"{x:g} m" for x in thresholds],
           yticks=range(len(names)), yticklabels=names,
           xlabel="Centre-distance matching threshold (not distance from the truck)",
           title="Four-camera saved AP is concentrated in traffic cones\nOne-camera saved AP is zero in every cell")
    fig.colorbar(chart, ax=ax, label="Average precision (%)")
    fig.text(0.02, 0.02, "Saved mini_val evaluator output; 80 sample tokens, 12 classes. No new inference/evaluation.\n"
             "A 4 m match tolerance is not evidence of detection at 4 m range or beyond 150 m.", fontsize=9)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(output / "camera_ap_thresholds.png", dpi=150, metadata={"Software": None})
    plt.close(fig)


def main():
    data = {name: json.loads((ROOT / path).read_text(encoding="utf-8"))
            for name, path in SOURCES.items() if name != "coverage"}
    camera, camera_rows, class_rows = compare_cameras(
        data["one_predictions"], data["four_predictions"], data["one_metrics"], data["four_metrics"])
    with (ROOT / SOURCES["coverage"]).open(encoding="utf-8", newline="") as stream:
        coverage, coverage_rows = summarize_coverage(list(csv.DictReader(stream)))
    camera_tokens = set(data["one_predictions"]["results"])
    coverage_tokens = {x["sample_token"] for x in coverage_rows}
    output = ROOT / "docs/evidence/truckscenes/comparison"
    output.mkdir(parents=True, exist_ok=True)
    summary = {"analysis": "saved-output comparison; no inference or raw-data rebuild",
               "source_sha256_lf_normalized_utf8": {
                   path: hashlib.sha256((ROOT / path).read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                   for path in SOURCES.values()},
               "camera": camera, "coverage": coverage,
               "coverage_camera_token_overlap": len(camera_tokens & coverage_tokens)}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n",
                                         encoding="utf-8", newline="\n")
    write_csv(output / "camera_samples.csv", camera_rows)
    write_csv(output / "camera_class_ap.csv", class_rows)
    write_csv(output / "coverage_samples.csv", coverage_rows)
    plot_comparisons(output, coverage_rows, class_rows)
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
