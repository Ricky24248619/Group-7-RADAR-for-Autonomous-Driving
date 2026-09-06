"""Render paired MAN TruckScenes RADAR and LiDAR sample views."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import cm

if not hasattr(cm, "get_cmap"):
    cm.get_cmap = matplotlib.colormaps.get_cmap

try:
    from truckscenes import TruckScenes
except ModuleNotFoundError:  # Allows argument/helper tests without the optional devkit.
    TruckScenes = None


VERSION = "v1.2-mini"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    configured_root = os.environ.get("TRUCKSCENES_ROOT")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(configured_root) if configured_root else None,
        help="Dataset root, or set TRUCKSCENES_ROOT.",
    )
    parser.add_argument("--scene-count", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "sample_visualizations",
    )
    return parser.parse_args()


def bounded_scene_count(requested: int, available: int) -> int:
    """Clamp a requested scene count to the non-empty available range."""
    if available < 1:
        return 0
    return min(max(requested, 1), available)


def main() -> None:
    args = parse_args()
    if args.data_root is None:
        raise SystemExit("Provide --data-root or set TRUCKSCENES_ROOT.")
    if TruckScenes is None:
        raise SystemExit("Install truckscenes-devkit before rendering the dataset.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    trucksc = TruckScenes(version=VERSION, dataroot=str(args.data_root), verbose=True)
    scene_count = bounded_scene_count(args.scene_count, len(trucksc.scene))

    for scene_number, scene in enumerate(trucksc.scene[:scene_count], start=1):
        sample = trucksc.get("sample", scene["first_sample_token"])
        scene_dir = args.output_dir / f"scene_{scene_number:02d}"
        scene_dir.mkdir(parents=True, exist_ok=True)
        channels = {
            "RADAR_LEFT_FRONT": scene_dir / "radar_left_front.png",
            "LIDAR_TOP_FRONT": scene_dir / "lidar_top_front.png",
        }

        for channel, output_path in channels.items():
            trucksc.render_sample_data(
                sample["data"][channel],
                with_anns=True,
                axes_limit=80,
                point_scale=2.0,
                out_path=str(output_path),
            )
            print(f"Created {channel}: {output_path}")

        print(f"Scene: {scene['name']}")
        print(f"Conditions: {scene['description']}")
        print(f"Sample token: {sample['token']}")


if __name__ == "__main__":
    main()
