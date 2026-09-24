"""CPU-only mini_val coverage comparison in a shared ego frame.

Requires truckscenes-devkit 1.2.0 for the raw run, but helper tests need only NumPy.
No new inference, box matching, custom detection score or sweep accumulation.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from truckscenes_stats import range_counts

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ("RADAR_LEFT_FRONT", "LIDAR_LEFT", "LIDAR_TOP_FRONT")
EDGES = [0, 50, 100, 150, 400, float("inf")]
LABELS = ["0-50", "50-100", "100-150", "150-400", ">=400"]


def transform_points(points, transform):
    points = np.asarray(points, dtype=float)
    transform = np.asarray(transform, dtype=float)
    if points.ndim != 2 or points.shape[0] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite 3xN coordinates")
    if transform.shape != (4, 4) or not np.isfinite(transform).all():
        raise ValueError("Expected finite 4x4 transform")
    return transform[:3, :3] @ points + transform[:3, 3, None]


def align_cloud(points, sensor_to_ego, ego_to_global, reference_to_global):
    """Sensor -> acquisition ego -> global -> reference ego, as in devkit multisweep."""
    transform = np.linalg.inv(reference_to_global) @ ego_to_global @ sensor_to_ego
    return transform_points(points, transform)


def region_counts(points):
    """Count both full-azimuth and forward-sector planar ranges; edges are [low, high)."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[0] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite 3xN coordinates")
    angle = np.arctan2(points[1], points[0])
    # A tiny tolerance keeps mathematically exact sector boundaries inclusive.
    mask = (points[0] > 0) & (np.abs(angle) <= np.deg2rad(30) + 1e-12)
    return {"all_azimuth": range_counts(points, EDGES),
            "forward_30deg": range_counts(points[:, mask], EDGES)}


def check_timing(sample_us, sensor_us, pose_us, reference_us):
    if abs(sensor_us - sample_us) > 50_000:
        raise ValueError("Sensor is more than 50 ms from annotated sample")
    if abs(pose_us - sensor_us) > 10_000 or abs(reference_us - sample_us) > 10_000:
        raise ValueError("Pose is more than 10 ms from its reference time")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot(output, totals):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=True)
    for ax, channel in zip(axes, CHANNELS):
        counts = totals[(channel, "forward_30deg")]
        denominator = sum(counts)
        if denominator == 0:
            ax.set_title(channel)
            ax.text(.5, .5, "No sector returns; share undefined", ha="center", transform=ax.transAxes)
            continue
        shares = [100 * n / denominator for n in counts]
        ax.bar(LABELS, shares, color="#3168ba")
        ax.set(title=f"{channel}\nn={denominator:,} sector returns", xlabel="Ego planar range (m)", ylim=(0, 105))
        ax.tick_params(axis="x", rotation=35)
        for i, value in enumerate(shares):
            ax.text(i, value + 1, f"{value:.2f}%", ha="center", fontsize=8)
    axes[0].set_ylabel("Share of this channel's forward-sector returns (%)")
    fig.suptitle("Raw coverage: same 80 mini_val samples, shared ego frame and forward ±30° sector")
    fig.text(0.02, 0.01, "Different sensors, scan patterns and vertical fields of view; this is not detection accuracy.\n"
             "Rigid ego-motion alignment only: residual timing, scan motion and moving objects are not corrected.", fontsize=9)
    fig.tight_layout(rect=(0, 0.13, 1, 0.94))
    fig.savefig(output / "sensor_coverage.png", dpi=150, metadata={"Software": None})
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    for offset, source in enumerate(("ground_truth", "camera_one", "camera_four")):
        values = totals[(source, "all_azimuth")]
        ax.bar(np.arange(5) + (offset - 1) * .25, values, width=.25, label=source.replace("_", " "))
    ax.set(xticks=np.arange(5), xticklabels=LABELS, xlabel="Box-centre planar range from reference ego (m)",
           ylabel="Box records (not matched objects)", title="Saved predictions and mapped annotations by range — 80 mini_val samples")
    ax.legend()
    fig.text(.02, .02, "Full azimuth; no evaluator range/visibility/point-count filtering. Predictions retain saved scores.\n"
             "Extra predictions are not extra correct detections. This plot does not measure recall or precision.", fontsize=9)
    fig.tight_layout(rect=(0, .12, 1, 1))
    fig.savefig(output / "box_ranges.png", dpi=150, metadata={"Software": None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/evidence/truckscenes/raw-comparison")
    args = parser.parse_args()
    from truckscenes import TruckScenes
    from truckscenes.utils.data_classes import LidarPointCloud, RadarPointCloud
    from truckscenes.utils.geometry_utils import transform_matrix
    from truckscenes.utils.splits import create_splits_scenes
    from truckscenes.eval.detection.utils import category_to_detection_name
    from pyquaternion import Quaternion
    from importlib.metadata import version

    def matrix(record):
        return transform_matrix(np.array(record["translation"]), Quaternion(record["rotation"]))

    truck = TruckScenes(version="v1.2-mini", dataroot=str(args.data_root), verbose=False)
    scene_names = set(create_splits_scenes()["mini_val"])
    samples = sorted((s for s in truck.sample if truck.get("scene", s["scene_token"])["name"] in scene_names),
                     key=lambda s: (s["scene_token"], s["timestamp"]))
    predictions = {name: json.loads((ROOT / "scripts" / filename).read_text(encoding="utf-8"))["results"]
                   for name, filename in (("camera_one", "results_mini_val_fcos3d.json"),
                                          ("camera_four", "results_mini_val_fcos3d_4cam.json"))}
    tokens = {s["token"] for s in samples}
    if len(samples) != 80 or any(set(p) != tokens for p in predictions.values()):
        raise ValueError("Expected both saved submissions to match all 80 official mini_val samples")
    rows, manifest = [], []
    totals = defaultdict(lambda: np.zeros(5, dtype=np.int64))
    class_totals = defaultdict(lambda: np.zeros(5, dtype=np.int64))
    ignored_annotations = 0
    for i, sample in enumerate(samples, 1):
        token = sample["token"]
        reference = truck.getclosest("ego_pose", sample["timestamp"])
        reference_matrix = matrix(reference)
        inverse_reference = np.linalg.inv(reference_matrix)
        record = {"sample_token": token, "scene_token": sample["scene_token"],
                  "sample_timestamp_us": sample["timestamp"], "reference_pose": reference, "sensors": []}

        def add(source, xyz):
            for region, counts in region_counts(xyz).items():
                totals[(source, region)] += counts
                for band, count in zip(LABELS, counts):
                    rows.append({"sample_token": token, "source": source, "region": region,
                                 "band_m": band, "count": count, "denominator": sum(counts)})

        for channel in CHANNELS:
            sd = truck.get("sample_data", sample["data"][channel])
            if sd["sample_token"] != token or not sd["is_key_frame"]:
                raise ValueError("Channel does not reference this annotated sample's keyframe")
            calibration = truck.get("calibrated_sensor", sd["calibrated_sensor_token"])
            if truck.get("sensor", calibration["sensor_token"])["channel"] != channel:
                raise ValueError("Calibration sensor does not match requested channel")
            pose = truck.get("ego_pose", sd["ego_pose_token"])
            check_timing(sample["timestamp"], sd["timestamp"], pose["timestamp"], reference["timestamp"])
            cloud_type = RadarPointCloud if channel.startswith("RADAR") else LidarPointCloud
            cloud = cloud_type.from_file(str(args.data_root / sd["filename"]))
            xyz = align_cloud(cloud.points[:3], matrix(calibration), matrix(pose), reference_matrix)
            add(channel, xyz)
            record["sensors"].append({"channel": channel, "sample_data_token": sd["token"],
                                      "filename": sd["filename"], "timestamp_us": sd["timestamp"],
                                      "calibration": calibration, "acquisition_pose": pose,
                                      "sensor_sample_offset_ms": (sd["timestamp"] - sample["timestamp"]) / 1000,
                                      "pose_sensor_offset_ms": (pose["timestamp"] - sd["timestamp"]) / 1000})
        boxes = {name: data[token] for name, data in predictions.items()}
        boxes["ground_truth"] = []
        for annotation_token in sample["anns"]:
            annotation = truck.get("sample_annotation", annotation_token)
            name = category_to_detection_name(annotation["category_name"])
            if name is None:
                ignored_annotations += 1
            else:
                boxes["ground_truth"].append({"translation": annotation["translation"], "detection_name": name})
        for source, records in boxes.items():
            xyz = transform_points(np.array([b["translation"] for b in records]).reshape(-1, 3).T, inverse_reference)
            add(source, xyz)
            for name in sorted({b["detection_name"] for b in records}):
                selected = xyz[:, [b["detection_name"] == name for b in records]]
                class_totals[(source, name)] += region_counts(selected)["all_azimuth"]
        manifest.append(record)
        if i % 10 == 0:
            print(f"Processed {i}/{len(samples)} samples", flush=True)

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    aggregates = [{"source": source, "region": region, "band_m": band, "count": int(count),
                   "denominator": int(sum(counts)), "sample_count": len(samples)}
                  for (source, region), counts in sorted(totals.items()) for band, count in zip(LABELS, counts)]
    classes = [{"source": source, "class": name, "band_m": band, "count": int(count)}
               for (source, name), counts in sorted(class_totals.items()) for band, count in zip(LABELS, counts)]
    write_csv(output / "sample_ranges.csv", rows)
    write_csv(output / "aggregate_ranges.csv", aggregates)
    write_csv(output / "box_class_ranges.csv", classes)
    provenance = {"dataset": "MAN TruckScenes v1.2-mini", "split": "mini_val", "scene_names": sorted(scene_names),
                  "sample_count": len(samples), "channels": CHANNELS,
                  "reference": "Nearest ego_pose to annotated sample timestamp; planar ego x-y range",
                  "forward_sector": "x>0 and absolute ego azimuth <=30 degrees; no elevation mask",
                  "motion": "Rigid acquisition-ego to reference-ego transform; no per-point deskew or object-motion correction",
                  "ignored_unmapped_annotations": ignored_annotations,
                  "packages": {p: version(p) for p in ("truckscenes-devkit", "numpy", "pypcd4", "pyquaternion")},
                  "input_sha256_lf_normalized": {}, "samples": manifest}
    for name in ("sample", "sample_data", "sample_annotation", "calibrated_sensor", "ego_pose", "sensor", "category", "instance"):
        path = args.data_root / "v1.2-mini" / (name + ".json")
        provenance["input_sha256_lf_normalized"][f"v1.2-mini/{path.name}"] = hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
    for filename in ("results_mini_val_fcos3d.json", "results_mini_val_fcos3d_4cam.json"):
        provenance["input_sha256_lf_normalized"]["scripts/" + filename] = hashlib.sha256((ROOT / "scripts" / filename).read_text().encode()).hexdigest()
    (output / "manifest.json").write_text(json.dumps(provenance, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    plot(output, totals)
    print(json.dumps({f"{k[0]}:{k[1]}": v.tolist() for k, v in totals.items()}, indent=2))


if __name__ == "__main__":
    main()
