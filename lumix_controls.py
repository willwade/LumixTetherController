#!/usr/bin/env python3
"""
LUMIX Tether control position manager.

Handles calibration data and calculates control positions relative to window size.
"""

import json
import os
from pathlib import Path
from windows_use.uia.controls import WindowControl

CALIBRATION_FILE = Path(__file__).parent / "lumix_calibration.json"


# Default fallback positions (as percentages of window size)
# These are used if no calibration file exists
DEFAULT_POSITIONS = {
    "shutter": {"relative_x": 0.699, "relative_y": 0.084},  # ~70% right, 8.4% down
    "ae": {"relative_x": 0.583, "relative_y": 0.084},        # ~58% right, 8.4% down
    "aperture": {"relative_x": 0.377, "relative_y": 0.187},  # 37.7% right (233px), 18.7% down (288px)
    "iso": {"relative_x": 0.631, "relative_y": 0.266},       # 63.1% right (390px), 26.6% down (411px)
    "wb": {"relative_x": 0.377, "relative_y": 0.266},        # 37.7% right (233px), 26.6% down (411px)
}


def load_calibration():
    """Load calibration data from file."""
    if CALIBRATION_FILE.exists():
        try:
            with open(CALIBRATION_FILE) as f:
                data = json.load(f)
                return data.get("controls", {})
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def get_control_position(window: WindowControl, control_id: str) -> tuple[int, int] | None:
    """
    Get the click position for a control, using calibration data.

    Args:
        window: The LUMIX Tether main window
        control_id: The control identifier (e.g., "shutter", "ae", "aperture", "iso", "wb")

    Returns:
        Tuple of (x, y) screen coordinates, or None if not found
    """
    # Try calibration data first
    calibration = load_calibration()
    if calibration and control_id in calibration:
        data = calibration[control_id]
        rel_x = data["relative_x"]
        rel_y = data["relative_y"]
    elif control_id in DEFAULT_POSITIONS:
        # Use default fallback
        data = DEFAULT_POSITIONS[control_id]
        rel_x = data["relative_x"]
        rel_y = data["relative_y"]
    else:
        return None

    # Calculate actual position based on current window size
    rect = window.BoundingRectangle
    click_x = int(rect.left + rel_x * rect.width())
    click_y = int(rect.top + rel_y * rect.height())

    return (click_x, click_y)


def get_all_control_positions(window: WindowControl) -> dict[str, tuple[int, int]]:
    """
    Get all control positions for the current window.

    Args:
        window: The LUMIX Tether main window

    Returns:
        Dictionary mapping control IDs to (x, y) coordinates
    """
    positions = {}
    for control_id in DEFAULT_POSITIONS.keys():
        pos = get_control_position(window, control_id)
        if pos:
            positions[control_id] = pos
    return positions


def save_calibration(data: dict) -> bool:
    """
    Save calibration data to file.

    Args:
        data: Calibration data dictionary with "controls" key

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False
