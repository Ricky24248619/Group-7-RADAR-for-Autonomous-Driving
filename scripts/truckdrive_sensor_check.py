"""Check synchronized TruckDrive camera, LiDAR and radar data."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def get_sync_id(path):
    """Return the sync ID at the start of a TruckDrive filename."""
    return path.stem.split("_")[0]


def files_by_sync(directory, suffix):
    """Map sync IDs to files in one sensor directory."""
    return {
        get_sync_id(path): path
        for path in directory.glob(f"*{suffix}")
    }


def main():
    """Load one synchronized Camera, LiDAR and Radar frame."""
    parser = argparse.ArgumentParser(
        description="Check synchronized TruckDrive sensor access."
    )
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Directory containing TruckDrive scene folders.",
    )
    parser.add_argument(
        "--scene",
        required=True,
        help="Scene name, for example scene_28_22.",
    )
    parser.add_argument(
        "--sync-id",
        help="Optional sync ID. If omitted, the first common frame is used.",
    )
    args = parser.parse_args()

    scene = args.root / args.scene

    camera_dir = (
        scene
        / "camera"
        / "leopard"
        / "forward_center_medium"
        / "images"
    )
    lidar_dir = (
        scene
        / "lidar"
        / "aeva"
        / "joint_lidars"
        / "points"
    )
    radar_dir = (
        scene
        / "radar"
        / "conti542"
        / "joint_radars"
        / "detections"
    )

    for directory in (camera_dir, lidar_dir, radar_dir):
        if not directory.exists():
            raise FileNotFoundError(f"Missing sensor directory: {directory}")

    camera_files = files_by_sync(camera_dir, ".jpg")
    lidar_files = files_by_sync(lidar_dir, ".bin")
    radar_files = files_by_sync(radar_dir, ".bin")

    common_ids = sorted(
        set(camera_files)
        & set(lidar_files)
        & set(radar_files)
    )

    if not common_ids:
        raise RuntimeError(
            "No common Camera/LiDAR/Radar sync IDs were found."
        )

    if args.sync_id:
        if args.sync_id not in common_ids:
            raise ValueError(
                f"Sync ID {args.sync_id} is not available in all sensors."
            )
        selected = args.sync_id
    else:
        selected = common_ids[0]

    camera_file = camera_files[selected]
    lidar_file = lidar_files[selected]
    radar_file = radar_files[selected]

    with Image.open(camera_file) as image:
        camera_size = image.size
        camera_mode = image.mode

    lidar = np.fromfile(
        lidar_file,
        dtype=np.float64,
    ).reshape(-1, 11)

    radar = np.fromfile(
        radar_file,
        dtype=np.float64,
    ).reshape(-1, 33)

    print(f"Scene: {args.scene}")
    print(f"Common synchronized frames: {len(common_ids)}")
    print(f"Selected sync ID: {selected}")
    print()

    print("Camera")
    print(f"  File: {camera_file.name}")
    print(f"  Resolution: {camera_size[0]} x {camera_size[1]}")
    print(f"  Mode: {camera_mode}")
    print()

    print("LiDAR")
    print(f"  File: {lidar_file.name}")
    print(f"  Points: {lidar.shape[0]}")
    print(f"  Fields per point: {lidar.shape[1]}")
    print()

    print("Radar")
    print(f"  File: {radar_file.name}")
    print(f"  Detections: {radar.shape[0]}")
    print(f"  Fields per detection: {radar.shape[1]}")
    print()

    print("TruckDrive synchronized sensor check passed.")


if __name__ == "__main__":
    main()