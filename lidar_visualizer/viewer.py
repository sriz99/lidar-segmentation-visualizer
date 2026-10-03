"""Open3D GUI for navigating scene key frames and toggling segmentation."""

import sys

import numpy as np
import open3d as o3d
from open3d.visualization import gui, rendering

from .colors import DISPLAY_CLASS_COLORS, DISPLAY_CLASS_NAMES, label_colors
from .data import FrameFiles, read_labels, read_scan

UNSEGMENTED_COLOR = (0.18, 0.20, 0.23)


def run_viewer(
    scene_name: str,
    frames: list[FrameFiles],
    start_index: int = 0,
    point_size: float = 2.0,
    camera_height: float = 1.5,
) -> int:
    """Launch the Open3D scene viewer for the selected scene."""

    def frame_data(index: int) -> tuple[np.ndarray, np.ndarray]:
        scan_path, label_path = frames[index]
        if not scan_path.is_file():
            raise FileNotFoundError(f"LiDAR file not found: {scan_path}")
        if not label_path.is_file():
            raise FileNotFoundError(f"Lidarseg label file not found: {label_path}")
        points = read_scan(scan_path)
        labels = read_labels(label_path, len(points))
        return points, labels

    index = start_index
    points, current_labels = frame_data(index)
    segmentation_enabled = True

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    cloud.colors = o3d.utility.Vector3dVector(label_colors(current_labels))

    app = gui.Application.instance
    app.initialize()
    window = app.create_window(f"nuScenes LiDAR segmentation — {scene_name}", 1440, 900)
    scene_view = gui.SceneWidget()
    scene_view.scene = rendering.Open3DScene(window.renderer)
    scene_view.scene.set_background([1.0, 1.0, 1.0, 1.0])
    material = rendering.MaterialRecord()
    material.shader = "defaultUnlit"
    material.point_size = point_size
    scene_view.scene.add_geometry("cloud", cloud, material)
    scene_view.scene.add_geometry(
        "axes", o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0), rendering.MaterialRecord()
    )
    scene_view.setup_camera(60.0, cloud.get_axis_aligned_bounding_box(), [0.0, 0.0, camera_height])

    panel = gui.Vert(0, gui.Margins(12, 12, 12, 12))
    panel.add_child(gui.Label("Lidarseg class legend"))
    panel.add_child(gui.Label(f"{scene_name} · {len(frames)} key frames"))
    panel.add_child(gui.Label("← / → or A / D: change frame"))
    panel.add_child(gui.Label("Q: close window"))
    segmentation_toggle = gui.Checkbox("Show segmentation colors")
    segmentation_toggle.checked = True
    panel.add_child(segmentation_toggle)

    legend = gui.ScrollableVert(0, gui.Margins(0, 8, 0, 0))
    for label_id, class_name in DISPLAY_CLASS_NAMES.items():
        row = gui.Horiz(6, gui.Margins(0, 0, 0, 0))
        rgb = np.round(np.asarray(DISPLAY_CLASS_COLORS[label_id]) * 255).astype(np.uint8)
        swatch_pixels = np.broadcast_to(rgb, (16, 16, 3)).copy()
        row.add_child(gui.ImageWidget(o3d.geometry.Image(swatch_pixels)))
        row.add_child(gui.Label(f"{label_id:02d}  {class_name}"))
        legend.add_child(row)
    panel.add_child(legend)

    window.add_child(scene_view)
    window.add_child(panel)

    def on_layout(_context: object) -> None:
        content = window.content_rect
        panel_width = 340
        scene_view.frame = gui.Rect(content.x, content.y, content.width - panel_width, content.height)
        panel.frame = gui.Rect(content.x + content.width - panel_width, content.y, panel_width, content.height)

    window.set_on_layout(on_layout)

    def set_segmentation(enabled: bool) -> None:
        nonlocal segmentation_enabled
        segmentation_enabled = enabled
        if enabled:
            display_colors = label_colors(current_labels)
        else:
            display_colors = np.full((len(current_labels), 3), UNSEGMENTED_COLOR, dtype=np.float64)
        cloud.colors = o3d.utility.Vector3dVector(display_colors)
        scene_view.scene.remove_geometry("cloud")
        scene_view.scene.add_geometry("cloud", cloud, material)
        window.post_redraw()

    segmentation_toggle.set_on_checked(set_segmentation)

    def show(new_index: int) -> bool:
        nonlocal index, current_labels
        index = new_index % len(frames)
        try:
            new_points, new_labels = frame_data(index)
        except (OSError, ValueError) as exc:
            print(f"Could not load frame {index}: {exc}", file=sys.stderr)
            return False

        cloud.points = o3d.utility.Vector3dVector(new_points)
        current_labels = new_labels
        if segmentation_enabled:
            display_colors = label_colors(current_labels)
        else:
            display_colors = np.full((len(current_labels), 3), UNSEGMENTED_COLOR, dtype=np.float64)
        cloud.colors = o3d.utility.Vector3dVector(display_colors)
        scene_view.scene.remove_geometry("cloud")
        scene_view.scene.add_geometry("cloud", cloud, material)
        print(f"{scene_name} — frame {index + 1}/{len(frames)}: {frames[index][0].name}")
        return True

    def on_key(event: gui.KeyEvent) -> bool:
        if event.type == gui.KeyEvent.Type.DOWN:
            if event.key == gui.KeyName.Q:
                window.close()
                return True
            if event.key in (gui.KeyName.RIGHT, gui.KeyName.D):
                return show(index + 1)
            if event.key in (gui.KeyName.LEFT, gui.KeyName.A):
                return show(index - 1)
        return False

    window.set_on_key(on_key)
    print(f"{scene_name} — frame {index + 1}/{len(frames)}: {frames[index][0].name}")
    print(f"Loaded {len(frames)} LIDAR_TOP key frames. Use ←/→ or A/D to change frames; press Q to quit.")
    app.run()
    return 0
