#!/usr/bin/env python3
"""Backward-compatible entry point for the nuScenes LiDAR viewer."""

from lidar_visualizer.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
