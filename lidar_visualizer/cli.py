"""Command-line interface for the nuScenes LiDAR viewer."""

import argparse
import json
import sys
from pathlib import Path

from .data import load_scene_frames
from .viewer import run_viewer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Choose a nuScenes scene and browse its LIDAR_TOP key frames."
    )
    parser.add_argument("--dataroot", type=Path, default=Path("nuscenes"), help="nuScenes dataset root")
    parser.add_argument("--version", default="v1.0-mini", help="Metadata version directory (default: v1.0-mini)")
    parser.add_argument("--scene", help="Scene number from the menu or scene name (for example scene-0061)")
    parser.add_argument("--start", type=int, default=0, help="Index of the first key frame to show")
    parser.add_argument("--point-size", type=float, default=2.0, help="Rendered point size")
    parser.add_argument("--height", type=float, default=1.5, help="Initial camera height above the sensor")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.dataroot.is_dir():
        print(f"Dataset root not found: {args.dataroot}", file=sys.stderr)
        return 2
    try:
        scene_name, frames, _class_names = load_scene_frames(args.dataroot, args.version, args.scene)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Could not load nuScenes scene: {exc}", file=sys.stderr)
        return 2
    if not frames:
        print(f"No LIDAR_TOP key frames found for {scene_name}", file=sys.stderr)
        return 2
    if not 0 <= args.start < len(frames):
        print(f"--start must be between 0 and {len(frames) - 1}", file=sys.stderr)
        return 2

    try:
        return run_viewer(
            scene_name,
            frames,
            start_index=args.start,
            point_size=args.point_size,
            camera_height=args.height,
        )
    except (OSError, ValueError) as exc:
        print(f"Could not start viewer: {exc}", file=sys.stderr)
        return 2
