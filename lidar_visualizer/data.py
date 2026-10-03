"""nuScenes metadata parsing and binary LiDAR/lidarseg readers."""

import json
from pathlib import Path

import numpy as np

from .colors import DISPLAY_CLASS_NAMES

FrameFiles = tuple[Path, Path]


def read_scan(path: Path) -> np.ndarray:
    """Read nuScenes float32 records (x, y, z, intensity, ring), returning XYZ."""
    values = np.fromfile(path, dtype=np.float32)
    if values.size % 5:
        raise ValueError(f"{path} contains {values.size} floats; expected a multiple of 5")
    return values.reshape(-1, 5)[:, :3]


def read_labels(path: Path, point_count: int) -> np.ndarray:
    """Read uint8 lidarseg labels and verify one label exists per point."""
    labels = np.fromfile(path, dtype=np.uint8)
    if len(labels) != point_count:
        raise ValueError(f"{path} has {len(labels)} labels for {point_count} points")
    return labels


def load_scene_frames(
    dataroot: Path,
    version: str,
    scene_query: str | None,
) -> tuple[str, list[FrameFiles], dict[int, str]]:
    """Resolve one scene's ordered LIDAR_TOP key frames and matching labels."""
    metadata = dataroot / version

    def read_table(name: str) -> list[dict]:
        path = metadata / f"{name}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing nuScenes metadata table: {path}")
        return json.loads(path.read_text())

    scenes = read_table("scene")
    samples = read_table("sample")
    sample_data = read_table("sample_data")
    calibrations = read_table("calibrated_sensor")
    sensors = read_table("sensor")
    lidarseg = read_table("lidarseg")

    if not scenes:
        raise ValueError(f"No scenes found in {metadata}")
    if scene_query is None:
        print("Available scenes:")
        for i, scene in enumerate(scenes, start=1):
            print(f"  {i:2}. {scene['name']} — {scene['description']} ({scene['nbr_samples']} samples)")
        scene_query = input("Choose a scene by number or name: ").strip()

    selected = next((scene for scene in scenes if scene["name"] == scene_query), None)
    if selected is None:
        try:
            scene_index = int(scene_query)
            if not 1 <= scene_index <= len(scenes):
                raise IndexError
            selected = scenes[scene_index - 1]
        except (ValueError, IndexError):
            names = ", ".join(scene["name"] for scene in scenes)
            raise ValueError(f"Unknown scene {scene_query!r}. Choose a number or one of: {names}")

    sample_by_token = {record["token"]: record for record in samples}
    sensor_by_token = {record["token"]: record["channel"] for record in sensors}
    calibration_sensor = {record["token"]: record["sensor_token"] for record in calibrations}
    data_by_sample: dict[str, list[dict]] = {}
    for record in sample_data:
        data_by_sample.setdefault(record["sample_token"], []).append(record)
    label_by_data = {record["sample_data_token"]: record["filename"] for record in lidarseg}

    frames: list[FrameFiles] = []
    sample_token = selected["first_sample_token"]
    while sample_token:
        sample = sample_by_token[sample_token]
        candidates = [
            record
            for record in data_by_sample.get(sample_token, [])
            if record["is_key_frame"]
            and sensor_by_token.get(calibration_sensor.get(record["calibrated_sensor_token"])) == "LIDAR_TOP"
        ]
        if len(candidates) != 1:
            raise ValueError(f"Expected one LIDAR_TOP key frame for sample {sample_token}, found {len(candidates)}")

        data = candidates[0]
        label_file = label_by_data.get(data["token"])
        if label_file is None:
            raise FileNotFoundError(f"No lidarseg label metadata for LIDAR_TOP sample_data {data['token']}")
        frames.append((dataroot / data["filename"], dataroot / label_file))
        sample_token = sample["next"]

    return selected["name"], frames, DISPLAY_CLASS_NAMES
