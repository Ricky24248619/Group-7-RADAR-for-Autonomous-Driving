"""Measure the local TruckDrive mini dataset."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np


RANGE_EDGES = [0, 25, 50, 80, 100, 150, float("inf")]
RANGE_NAMES = [
    "0-25m",
    "25-50m",
    "50-80m",
    "80-100m",
    "100-150m",
    "150m+",
]


def sync_id(path):
    """Return the synchronized frame ID from a TruckDrive filename."""
    return path.stem.split("_")[0]


def scene_number(path):
    """Return the numeric suffix of a TruckDrive mini scene."""
    return int(path.name.split("_")[-1])


def range_counts(points):
    """Count radar detections in radial distance bands."""
    distance = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2)

    return [
        int(np.count_nonzero((distance >= low) & (distance < high)))
        for low, high in zip(RANGE_EDGES[:-1], RANGE_EDGES[1:])
    ]


def load_boxes(path):
    """Load one TruckDrive bounding-box annotation file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def analyse_scene(scene):
    """Measure radar and annotation data for one TruckDrive scene."""
    radar_dir = (
        scene
        / "radar"
        / "conti542"
        / "joint_radars"
        / "detections"
    )
    boxes_dir = scene / "annotations" / "bounding_boxes"
    lanes_dir = scene / "annotations" / "lane_lines"

    radar_files = sorted(radar_dir.glob("*.bin"))
    box_files = sorted(boxes_dir.glob("*.json"))
    lane_files = sorted(lanes_dir.glob("*.json"))

    radar_by_id = {sync_id(path): path for path in radar_files}
    boxes_by_id = {sync_id(path): path for path in box_files}

    common_ids = sorted(set(radar_by_id) & set(boxes_by_id))

    class_counts = Counter()
    total_boxes = 0

    for path in box_files:
        boxes = load_boxes(path)
        total_boxes += len(boxes)

        for box in boxes:
            class_counts[box.get("class-id", "UNKNOWN")] += 1

    selected_sync = None
    selected_detections = 0
    selected_ranges = [0] * len(RANGE_NAMES)

    if common_ids:
        selected_sync = common_ids[0]
        radar = np.fromfile(
            radar_by_id[selected_sync],
            dtype=np.float64,
        ).reshape(-1, 33)

        selected_detections = radar.shape[0]
        selected_ranges = range_counts(radar)

    return {
        "scene": scene.name,
        "radar_frames": len(radar_files),
        "box_frames": len(box_files),
        "lane_frames": len(lane_files),
        "common_frames": len(common_ids),
        "total_boxes": total_boxes,
        "classes": class_counts,
        "selected_sync": selected_sync,
        "selected_detections": selected_detections,
        "selected_ranges": selected_ranges,
    }


def main():
    """Measure every available TruckDrive mini scene."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Directory containing TruckDrive scene folders.",
    )
    args = parser.parse_args()

    scenes = sorted(
        args.root.glob("scene_28_*"),
        key=scene_number,
    )

    print(f"Scenes found: {len(scenes)}")
    print()

    results = []
    all_classes = Counter()
    all_ranges = np.zeros(len(RANGE_NAMES), dtype=int)

    for scene in scenes:
        result = analyse_scene(scene)
        results.append(result)

        all_classes.update(result["classes"])
        all_ranges += result["selected_ranges"]

        print(
            f"{result['scene']}: "
            f"radar={result['radar_frames']}, "
            f"box_frames={result['box_frames']}, "
            f"lane_frames={result['lane_frames']}, "
            f"common={result['common_frames']}, "
            f"boxes={result['total_boxes']}, "
            f"sample={result['selected_sync']}, "
            f"detections={result['selected_detections']}, "
            f"100-150m={result['selected_ranges'][4]}, "
            f"150m+={result['selected_ranges'][5]}"
        )

    print()
    print("Overall")
    print(f"  Scenes: {len(results)}")
    print(
        "  Radar frames:",
        sum(result["radar_frames"] for result in results),
    )
    print(
        "  Bounding-box frames:",
        sum(result["box_frames"] for result in results),
    )
    print(
        "  Lane-line frames:",
        sum(result["lane_frames"] for result in results),
    )
    print(
        "  Bounding boxes:",
        sum(result["total_boxes"] for result in results),
    )

    print()
    print("Object classes")

    for name, count in all_classes.most_common():
        print(f"  {name}: {count}")

    print()
    print("Radar range distribution")
    print("One annotated synchronized radar frame per scene:")

    for name, count in zip(RANGE_NAMES, all_ranges):
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()