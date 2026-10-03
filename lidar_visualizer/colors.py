"""Display class definitions and nuScenes label-to-display mappings."""

import numpy as np

DISPLAY_CLASS_NAMES = {
    0: "void / ignore", 1: "barrier", 2: "bicycle", 3: "bus", 4: "car",
    5: "construction_vehicle", 6: "motorcycle", 7: "pedestrian",
    8: "traffic_cone", 9: "trailer", 10: "truck", 11: "driveable_surface",
    12: "other_flat", 13: "sidewalk", 14: "terrain", 15: "manmade",
    16: "vegetation",
}

# RGB colors in [0, 1], following the requested palette.
DISPLAY_CLASS_COLORS = {
    0: (0.00, 0.00, 0.00), 1: (1.00, 0.65, 0.00), 2: (1.00, 0.41, 0.71),
    3: (0.95, 0.73, 0.00), 4: (0.12, 0.35, 0.95), 5: (0.00, 0.68, 0.75),
    6: (0.82, 0.25, 0.00), 7: (0.90, 0.05, 0.05), 8: (0.98, 0.85, 0.35),
    9: (0.55, 0.27, 0.07), 10: (0.55, 0.15, 0.72), 11: (0.78, 0.20, 0.43),
    12: (0.55, 0.55, 0.55), 13: (0.28, 0.08, 0.42), 14: (0.38, 0.68, 0.25),
    15: (0.25, 0.25, 0.25), 16: (0.00, 0.38, 0.12),
}

# nuScenes mini's 32 source labels mapped to the requested 17 display classes.
NUSCENES_TO_DISPLAY = {
    0: 0, 1: 0, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7, 7: 7, 8: 7,
    9: 1, 10: 0, 11: 0, 12: 8, 13: 0, 14: 2, 15: 3, 16: 3, 17: 4,
    18: 5, 19: 4, 20: 4, 21: 6, 22: 9, 23: 10, 24: 11, 25: 12,
    26: 13, 27: 14, 28: 15, 29: 15, 30: 16, 31: 0,
}


def label_colors(labels: np.ndarray) -> np.ndarray:
    """Map nuScenes lidarseg IDs to RGB colors for the display classes."""
    display_ids = np.zeros_like(labels)
    for nuscenes_id, display_id in NUSCENES_TO_DISPLAY.items():
        display_ids[labels == nuscenes_id] = display_id

    colors = np.empty((len(labels), 3), dtype=np.float64)
    for display_id in np.unique(display_ids):
        colors[display_ids == display_id] = DISPLAY_CLASS_COLORS[int(display_id)]
    return colors
