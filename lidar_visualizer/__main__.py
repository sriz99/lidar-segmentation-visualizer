"""Allow running the application with ``python -m lidar_visualizer``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
