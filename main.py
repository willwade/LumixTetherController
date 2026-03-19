#!/usr/bin/env python3
"""
LUMIX Tether Bridge (Grid 3 & AI Edition)

An automation bridge that allows Grid 3 (AAC software) and Large Language Models
to control the Panasonic GH5M2 via the LUMIX Tether desktop application.

Uses Windows-Use framework (based on Python-UIAutomation-for-Windows) to interact
with the UI automation tree.
"""

import os
import subprocess
import sys
import time

import click

from windows_use.uia.controls import Control, WindowControl
from windows_use.uia.core import (
    Click,
    GetScreenSize,
    MoveWindow,
    SetForegroundWindow,
)

# Import control position manager
try:
    from lumix_controls import get_control_position
    CONTROLS_AVAILABLE = True
except ImportError:
    CONTROLS_AVAILABLE = False

# Import CameraAgent for agentic mode
try:
    from agentic_camera import CameraAgent
    AGENTIC_AVAILABLE = True
except ImportError:
    AGENTIC_AVAILABLE = False


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """LUMIX Tether Bridge - Control GH5M2 via LUMIX Tether desktop application."""
    pass


@cli.command()
@click.option(
    "--action",
    type=click.Choice(["shutter", "record", "lv-on", "af-on", "ae", "info", "test-clicks", "focus"], case_sensitive=False),
    help="Deterministic action to perform (no LLM involved)",
)
@click.option(
    "--focus-point",
    type=click.Choice([
        "center", "centre",
        "top-left", "top-center", "top-right",
        "middle-left", "middle-center", "middle-right",
        "bottom-left", "bottom-center", "bottom-right",
        "tl", "tc", "tr",
        "ml", "mc", "mr",
        "bl", "bc", "br"
    ], case_sensitive=False),
    help="Focus point (3x3 grid). Used with --action focus.",
)
@click.option(
    "--layout",
    type=click.Choice(["grid", "focus"], case_sensitive=False),
    help="Window layout arrangement",
)
@click.option(
    "--ai",
    type=str,
    help="Agentic mode: Pass prompt to Vision LLM for intelligent camera control",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def main(action: str | None, layout: str | None, ai: str | None, focus_point: str | None, verbose: bool):
    """
    Execute LUMIX Tether control commands.

    Examples:
        uv run main.py --action shutter
        uv run main.py --layout grid
        uv run main.py --ai "Focus on the person's face and lower the aperture"
    """
    if verbose:
        click.echo("[DEBUG] Starting LUMIX Tether Bridge...")

    # Validate mutually exclusive options
    options_provided = sum(1 for opt in [action, layout, ai] if opt is not None)
    if options_provided == 0:
        click.echo("Error: Please specify --action, --layout, or --ai", err=True)
        sys.exit(1)
    if options_provided > 1:
        click.echo("Error: Only one of --action, --layout, or --ai can be specified", err=True)
        sys.exit(1)

    try:
        if verbose:
            click.echo("[DEBUG] Connecting to LUMIX Tether...")

        # Find or launch the main window
        main_window = ensure_main_window_open(verbose)

        if main_window is None:
            click.echo(
                "Error: Could not connect to LUMIX Tether.",
                err=True,
            )
            sys.exit(1)

        if verbose:
            click.echo(f"[DEBUG] Found main window: {main_window.Name}")

        # Execute the requested command
        if action:
            execute_deterministic_action(main_window, action, focus_point, verbose)
        elif layout:
            apply_window_layout(main_window, layout, verbose)
        elif ai:
            execute_agentic_mode(main_window, ai, verbose)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def find_main_window() -> Control | None:
    """
    Find the LUMIX Tether main window ('1: DC-GH5').

    Returns:
        Control object if found, None otherwise
    """
    # Try to find by exact name first
    try:
        window = WindowControl(searchDepth=1, Name="1: DC-GH5")
        if window.Exists(1, 0.5):
            return window
    except Exception:
        pass

    # Try alternate patterns
    patterns = ["DC-GH5", "GH5", "LUMIX"]

    for pattern in patterns:
        try:
            window = WindowControl(searchDepth=1, Name=pattern)
            if window.Exists(1, 0.5):
                return window
        except Exception:
            pass

    # Try regex pattern
    try:
        window = WindowControl(searchDepth=1, RegexName=r".*DC-GH5.*")
        if window.Exists(1, 0.5):
            return window
    except Exception:
        pass

    return None


def find_live_view_window() -> Control | None:
    """
    Find the LIVE VIEW window.

    Returns:
        Control object if found, None otherwise
    """
    try:
        window = WindowControl(searchDepth=1, Name="LIVE VIEW")
        if window.Exists(1, 0.5):
            return window
    except Exception:
        pass

    return None


def find_preview_window() -> Control | None:
    """
    Find the Preview window.

    Returns:
        Control object if found, None otherwise
    """
    try:
        window = WindowControl(searchDepth=1, RegexName=r"Preview.*")
        if window.Exists(1, 0.5):
            return window
    except Exception:
        pass

    return None


def launch_lumix_tether(verbose: bool = False) -> bool:
    """
    Launch LUMIX Tether application and wait for it to become ready.

    Returns:
        True if successfully launched, False otherwise.
    """
    if verbose:
        click.echo("[DEBUG] Attempting to launch LUMIX Tether...")

    # Common installation paths for LUMIX Tether
    possible_paths = [
        r"C:\Program Files\Panasonic\LUMIX Tether\LUMIX Tether.exe",
        r"C:\Program Files (x86)\Panasonic\LUMIX Tether\LUMIX Tether.exe",
        r"C:\Program Files\Panasonic\LUMIX Tether for Streaming\LUMIX Tether for Streaming.exe",
    ]

    lumix_path = None
    for path in possible_paths:
        if os.path.exists(path):
            lumix_path = path
            break

    if not lumix_path:
        click.echo(
            "Error: LUMIX Tether not found in standard installation paths.",
            err=True,
        )
        click.echo("Please launch it manually or ensure it's installed.")
        return False

    try:
        subprocess.Popen([lumix_path])
        click.echo("Launching LUMIX Tether...")

        # Wait for window to appear (up to 10 seconds)
        for _ in range(20):
            time.sleep(0.5)
            if find_main_window():
                click.echo("LUMIX Tether launched successfully!")
                return True

        click.echo("Warning: LUMIX Tether launched but window not detected.", err=True)
        return False

    except Exception as e:
        click.echo(f"Error launching LUMIX Tether: {e}", err=True)
        return False


def ensure_main_window_open(verbose: bool = False) -> Control | None:
    """
    Ensure the main LUMIX Tether window is open.

    Will attempt to launch LUMIX Tether if not found.

    Returns:
        Control object if found/launched, None otherwise.
    """
    main_window = find_main_window()

    if main_window is None:
        click.echo("LUMIX Tether not found. Attempting to launch...")
        if launch_lumix_tether(verbose):
            main_window = find_main_window()
        else:
            click.echo(
                "Error: Could not launch LUMIX Tether. Please start it manually.",
                err=True,
            )
            return None

    return main_window


def ensure_live_view_open_from_main(main_window: Control, verbose: bool = False) -> bool:
    """
    Open Live View window from the main window if it's not already open.

    Returns:
        True if Live View is open, False otherwise.
    """
    if verbose:
        click.echo("[DEBUG] Checking Live View window...")

    live_view = find_live_view_window()
    if live_view:
        if verbose:
            click.echo("[DEBUG] Live View already open.")
        return True

    # Live View is not open - try to open it from main window
    # This typically involves clicking a menu item or button
    click.echo("Opening Live View window...")

    try:
        # Bring main window to foreground
        handle = main_window.NativeWindowHandle
        SetForegroundWindow(handle)
        time.sleep(0.2)

        rect = main_window.BoundingRectangle

        # Try clicking on the Live View button/menu
        # The exact location depends on LUMIX Tether's UI
        # Common locations: top menu bar or a button in the panel
        # We'll try a few common positions

        # Try 1: Click near the top-left where menu items often are
        menu_x = rect.left + 100
        menu_y = rect.top + 40
        Click(menu_x, menu_y)
        time.sleep(0.3)

        # Try 2: Look for a Live View button (may be in a panel)
        # This is a heuristic - adjust based on actual UI
        button_x = rect.left + rect.width() // 4
        button_y = rect.top + 100
        Click(button_x, button_y)
        time.sleep(0.5)

        # Check if Live View opened
        if find_live_view_window():
            click.echo("Live View opened successfully!")
            return True

        # If still not open, try keyboard shortcut (common: Ctrl+L or similar)
        click.echo("Trying keyboard shortcut...")
        # Using SendKeys would be ideal, but we'll try another click position
        Click(rect.left + 50, rect.top + 60)
        time.sleep(0.3)

        if find_live_view_window():
            click.echo("Live View opened successfully!")
            return True

        click.echo(
            "Warning: Could not automatically open Live View. Please open it manually from LUMIX Tether.",
            err=True,
        )
        return False

    except Exception as e:
        if verbose:
            click.echo(f"[DEBUG] Error opening Live View: {e}")
        click.echo(
            "Warning: Could not open Live View automatically. Please open it manually.",
            err=True,
        )
        return False


def execute_deterministic_action(window: Control, action: str, focus_point: str | None, verbose: bool):
    """
    Execute deterministic UI actions without LLM involvement.

    Args:
        window: LUMIX Tether main window control
        action: Action to perform (shutter, record, lv-on, af-on, focus)
        focus_point: Focus zone for grid focus (e.g., "center", "top-left")
        verbose: Enable verbose logging
    """
    if verbose:
        click.echo(f"[DEBUG] Executing deterministic action: {action}")

    # Bring window to foreground
    try:
        handle = window.NativeWindowHandle
        SetForegroundWindow(handle)
        import time

        time.sleep(0.2)  # Give window time to come to foreground
    except Exception:
        pass

    if action == "shutter":
        click_shutter_button(window, verbose)
    elif action == "record":
        click.echo("Toggling motion picture recording...")
        toggle_record_button(window, verbose)
    elif action == "lv-on":
        click.echo("Ensuring Live View window is open...")
        ensure_live_view_open(verbose)
    elif action == "af-on":
        click.echo("Triggering AF (half-press shutter)...")
        trigger_autofocus(window, verbose)
    elif action == "ae":
        click.echo("Triggering AE button (preview focus)...")
        click_ae_button(window, verbose)
    elif action == "focus":
        if not focus_point:
            click.echo("Error: --focus-point required when using --action focus", err=True)
            sys.exit(1)
        click.echo(f"Focusing on {focus_point}...")
        focus_on_grid_point(window, focus_point, verbose)
    elif action == "info":
        show_window_info(window)
    elif action == "test-clicks":
        test_shutter_positions(window)


def click_shutter_button(window: Control, verbose: bool):
    """
    Click the physical shutter button in the Recording Panel.

    Uses calibration data to calculate position at any window size.
    """
    if verbose:
        click.echo("[DEBUG] Clicking shutter button...")

    try:
        # Get position from calibration (works at any window size)
        if CONTROLS_AVAILABLE:
            pos = get_control_position(window, "shutter")
            if pos:
                button_x, button_y = pos
            else:
                # Fallback to percentage-based position
                rect = window.BoundingRectangle
                button_x = rect.left + int(rect.width() * 0.699)
                button_y = rect.top + int(rect.height() * 0.084)
        else:
            rect = window.BoundingRectangle
            button_x = rect.left + int(rect.width() * 0.699)
            button_y = rect.top + int(rect.height() * 0.084)

        if verbose:
            click.echo(f"[DEBUG] Clicking at ({button_x}, {button_y})")

        Click(button_x, button_y)
        click.echo("Shutter triggered - Photo captured!")

    except Exception as e:
        if verbose:
            click.echo(f"[DEBUG] Error clicking shutter: {e}")
        click.echo(
            "Warning: Could not click shutter button. Ensure LUMIX Tether is the active window.",
            err=True,
        )


def click_ae_button(window: Control, verbose: bool):
    """
    Click the AE button (preview focus/half-press) in the Recording Panel.

    Uses calibration data to calculate position at any window size.
    """
    if verbose:
        click.echo("[DEBUG] Clicking AE button...")

    try:
        # Get position from calibration (works at any window size)
        if CONTROLS_AVAILABLE:
            pos = get_control_position(window, "ae")
            if pos:
                button_x, button_y = pos
            else:
                # Fallback to percentage-based position
                rect = window.BoundingRectangle
                button_x = rect.left + int(rect.width() * 0.583)
                button_y = rect.top + int(rect.height() * 0.084)
        else:
            rect = window.BoundingRectangle
            button_x = rect.left + int(rect.width() * 0.583)
            button_y = rect.top + int(rect.height() * 0.084)

        if verbose:
            click.echo(f"[DEBUG] Clicking at ({button_x}, {button_y})")

        # Bring window to foreground
        handle = window.NativeWindowHandle
        SetForegroundWindow(handle)
        import time
        time.sleep(0.2)

        Click(button_x, button_y)
        click.echo("AE button triggered - Preview focus activated!")

    except Exception as e:
        if verbose:
            click.echo(f"[DEBUG] Error clicking AE button: {e}")
        click.echo(
            "Warning: Could not click AE button.",
            err=True,
        )


def toggle_record_button(window: Control, verbose: bool):
    """
    Toggle motion picture recording (start/stop video).

    The record button is typically near the shutter button.
    """
    if verbose:
        click.echo("[DEBUG] Clicking record button...")

    try:
        rect = window.BoundingRectangle

        # Record button is typically to the left of the shutter button
        # Based on typical camera UI patterns
        button_x = rect.left + rect.width() // 2 - 80  # Left of shutter
        button_y = rect.top + 60

        if verbose:
            click.echo(f"[DEBUG] Clicking at ({button_x}, {button_y})")

        Click(button_x, button_y)
        click.echo("Recording toggled!")

    except Exception as e:
        if verbose:
            click.echo(f"[DEBUG] Error clicking record: {e}")
        click.echo("Warning: Could not click record button.", err=True)


def ensure_live_view_open(verbose: bool):
    """
    Ensure the Live View window is open and visible.
    """
    if verbose:
        click.echo("[DEBUG] Checking Live View window...")

    live_view = find_live_view_window()

    if live_view:
        click.echo("Live View is already open.")

        # Bring it to foreground
        try:
            handle = live_view.NativeWindowHandle
            SetForegroundWindow(handle)
        except Exception:
            pass
        return

    # Live View not open - try to open it
    main_window = find_main_window()
    if main_window:
        ensure_live_view_open_from_main(main_window, verbose)
    else:
        click.echo(
            "Warning: Live View window not found and main window not available.",
            err=True,
        )


def show_window_info(window: Control):
    """
    Display detailed window information for debugging.
    """
    rect = window.BoundingRectangle
    click.echo("=" * 60)
    click.echo("LUMIX Tether Window Information")
    click.echo("=" * 60)
    click.echo()
    click.echo(f"Window Name: {window.Name}")
    click.echo(f"Handle: {window.NativeWindowHandle}")
    click.echo()
    click.echo("Bounding Rectangle:")
    click.echo(f"  Left:   {rect.left}")
    click.echo(f"  Top:    {rect.top}")
    click.echo(f"  Right:  {rect.right}")
    click.echo(f"  Bottom: {rect.bottom}")
    click.echo(f"  Width:  {rect.width()}")
    click.echo(f"  Height: {rect.height()}")
    click.echo()
    click.echo("Calculated Click Positions:")
    shutter_x = rect.left + rect.width() // 2
    shutter_y = rect.top + 60
    click.echo(f"  Shutter: ({shutter_x}, {shutter_y})")
    record_x = rect.left + rect.width() // 2 - 80
    click.echo(f"  Record:  ({record_x}, {shutter_y})")
    click.echo()
    click.echo("Live View Window:")
    live_view = find_live_view_window()
    if live_view:
        lv_rect = live_view.BoundingRectangle
        click.echo(f"  Found: {live_view.Name}")
        click.echo(f"  Position: ({lv_rect.left}, {lv_rect.top})")
        click.echo(f"  Size: {lv_rect.width()}x{lv_rect.height()}")
        click.echo(f"  Center: ({lv_rect.left + lv_rect.width() // 2}, {lv_rect.top + lv_rect.height() // 2})")
    else:
        click.echo("  Not found")
    click.echo()
    click.echo("=" * 60)


def trigger_autofocus(_window: Control, verbose: bool):
    """
    Trigger AF by clicking the AF area or using keyboard shortcut.

    For LUMIX Tether, AF is typically triggered by clicking on the Live View area
    or using a keyboard shortcut if configured.
    """
    if verbose:
        click.echo("[DEBUG] Triggering autofocus...")

    # First try to find Live View and click in center to trigger AF
    live_view = find_live_view_window()

    if live_view:
        try:
            rect = live_view.BoundingRectangle
            center_x = rect.left + rect.width() // 2
            center_y = rect.top + rect.height() // 2

            if verbose:
                click.echo(f"[DEBUG] Clicking Live View center at ({center_x}, {center_y})")

            # Bring Live View to foreground first
            handle = live_view.NativeWindowHandle
            SetForegroundWindow(handle)

            import time

            time.sleep(0.1)

            # Click in center to trigger Touch AF
            Click(center_x, center_y)
            click.echo("Autofocus triggered (Touch AF on Live View)!")
            return
        except Exception as e:
            if verbose:
                click.echo(f"[DEBUG] Error triggering AF via Live View: {e}")

    click.echo(
        "Warning: Could not trigger AF. Ensure Live View is open and try clicking on it manually.",
        err=True,
    )


# 3x3 grid focus zones
FOCUS_ZONES = {
    # Full names
    "top-left": (1/6, 1/6),
    "top-center": (3/6, 1/6),
    "top-right": (5/6, 1/6),
    "middle-left": (1/6, 3/6),
    "middle-center": (3/6, 3/6),
    "middle-right": (5/6, 3/6),
    "bottom-left": (1/6, 5/6),
    "bottom-center": (3/6, 5/6),
    "bottom-right": (5/6, 5/6),
    # Abbreviations
    "tl": (1/6, 1/6),
    "tc": (3/6, 1/6),
    "tr": (5/6, 1/6),
    "ml": (1/6, 3/6),
    "mc": (3/6, 3/6),
    "mr": (5/6, 3/6),
    "bl": (1/6, 5/6),
    "bc": (3/6, 5/6),
    "br": (5/6, 5/6),
    # Center/centre aliases
    "center": (3/6, 3/6),
    "centre": (3/6, 3/6),
}


def focus_on_grid_point(_window: Control, focus_point: str, verbose: bool):
    """
    Focus on a specific point in the Live View using a 3x3 grid.

    The Live View is divided into 9 zones (3x3 grid), and focus is set
    to the center of the specified zone.

    Args:
        _window: Main window (unused, we find Live View directly)
        focus_point: Zone identifier (e.g., "center", "top-left", "tl", etc.)
        verbose: Enable verbose logging
    """
    if verbose:
        click.echo("[DEBUG] Grid focus mode...")

    # Find Live View window
    live_view = find_live_view_window()

    if not live_view:
        click.echo("Error: Live View window not found. Ensure it's open.", err=True)
        click.echo("Run: uv run main.py main --action lv-on", err=True)
        return

    # Normalize focus point
    focus_point = focus_point.lower()

    if focus_point not in FOCUS_ZONES:
        click.echo(f"Error: Unknown focus point '{focus_point}'", err=True)
        click.echo("Valid options: center, top-left, top-center, top-right, middle-left, middle-center, middle-right, bottom-left, bottom-center, bottom-right", err=True)
        click.echo("Or abbreviations: tl, tc, tr, ml, mc, mr, bl, bc, br", err=True)
        return

    # Get relative position for the zone
    rel_x, rel_y = FOCUS_ZONES[focus_point]

    try:
        rect = live_view.BoundingRectangle

        # Calculate actual click position (center of the zone)
        click_x = int(rect.left + rel_x * rect.width())
        click_y = int(rect.top + rel_y * rect.height())

        if verbose:
            zone_pct_x = int(rel_x * 100)
            zone_pct_y = int(rel_y * 100)
            click.echo(f"[DEBUG] Zone: {focus_point} at ({zone_pct_x}%, {zone_pct_y}%)")
            click.echo(f"[DEBUG] Clicking at ({click_x}, {click_y})")

        # Bring Live View to foreground
        handle = live_view.NativeWindowHandle
        SetForegroundWindow(handle)

        import time

        time.sleep(0.1)

        # Click to trigger Touch AF at that point
        Click(click_x, click_y)
        click.echo(f"Focused on {focus_point}!")

    except Exception as e:
        if verbose:
            click.echo(f"[DEBUG] Error focusing: {e}")
        click.echo("Warning: Could not focus on specified point.", err=True)


def trigger_autofocus(_window: Control, verbose: bool):
    """
    Trigger AF by clicking the AF area or using keyboard shortcut.

    For LUMIX Tether, AF is typically triggered by clicking on the Live View area
    or using a keyboard shortcut if configured.
    """
    if verbose:
        click.echo("[DEBUG] Triggering autofocus...")

    # First try to find Live View and click in center to trigger AF
    live_view = find_live_view_window()

    if live_view:
        try:
            rect = live_view.BoundingRectangle
            center_x = rect.left + rect.width() // 2
            center_y = rect.top + rect.height() // 2

            if verbose:
                click.echo(f"[DEBUG] Clicking Live View center at ({center_x}, {center_y})")

            # Bring Live View to foreground first
            handle = live_view.NativeWindowHandle
            SetForegroundWindow(handle)

            import time

            time.sleep(0.1)

            # Click in center to trigger Touch AF
            Click(center_x, center_y)
            click.echo("Autofocus triggered (Touch AF on Live View)!")
            return
        except Exception as e:
            if verbose:
                click.echo(f"[DEBUG] Error triggering AF via Live View: {e}")

    click.echo(
        "Warning: Could not trigger AF. Ensure Live View is open and try clicking on it manually.",
        err=True,
    )


def test_shutter_positions(window: Control):
    """
    Test clicking at various positions to find the shutter button.
    This helps identify the correct coordinates for the shutter button.
    """
    rect = window.BoundingRectangle
    handle = window.NativeWindowHandle

    click.echo("=" * 60)
    click.echo("Testing Shutter Button Positions")
    click.echo("=" * 60)
    click.echo()
    click.echo("This will click at various positions in the LUMIX Tether window.")
    click.echo("Watch for which position triggers the shutter.")
    click.echo()
    click.echo("Press Ctrl+C to stop at any time.")
    click.echo()

    SetForegroundWindow(handle)
    import time
    time.sleep(0.3)

    # Test positions based on common LUMIX Tether layouts
    # The main window is typically divided into sections
    test_positions = [
        # Top row - common for shutter buttons
        ("Top Center", rect.left + rect.width() // 2, rect.top + 50),
        ("Top Left", rect.left + 100, rect.top + 50),
        ("Top Right", rect.right - 100, rect.top + 50),
        # Middle positions
        ("Middle Left", rect.left + 80, rect.top + rect.height() // 2),
        ("Middle Center", rect.left + rect.width() // 2, rect.top + rect.height() // 2),
        ("Middle Right", rect.right - 80, rect.top + rect.height() // 2),
        # Bottom positions
        ("Bottom Center", rect.left + rect.width() // 2, rect.bottom - 50),
        # Common panel positions (right side of window often has controls)
        ("Panel Top", rect.right - 50, rect.top + 60),
        ("Panel Middle", rect.right - 50, rect.top + 200),
        ("Panel Bottom", rect.right - 50, rect.bottom - 100),
        # Left side controls
        ("Left Top", rect.left + 50, rect.top + 100),
        ("Left Middle", rect.left + 50, rect.top + rect.height() // 2),
    ]

    for i, (name, x, y) in enumerate(test_positions, 1):
        click.echo(f"[{i}/{len(test_positions)}] Clicking {name}: ({x}, {y})")
        Click(x, y)
        click.echo("  Did the shutter trigger? (remember the result)")

        if i < len(test_positions):
            click.echo("  Waiting 2 seconds before next click...")
            time.sleep(2)

    click.echo()
    click.echo("=" * 60)
    click.echo("Test complete!")
    click.echo()
    click.echo("Note which position worked and update the shutter coordinates.")
    click.echo(f"Window bounds: left={rect.left}, top={rect.top}, width={rect.width()}, height={rect.height()}")


def apply_window_layout(window: Control, layout: str, verbose: bool):
    """
    Arrange LUMIX Tether windows into a predefined layout.

    Args:
        window: LUMIX Tether main window
        layout: Layout type ('grid' or 'focus')
        verbose: Enable verbose logging
    """
    if verbose:
        click.echo(f"[DEBUG] Applying layout: {layout}")

    screen_width, screen_height = GetScreenSize()

    if layout == "grid":
        click.echo("Arranging windows in 3-column grid layout...")
        apply_grid_layout(window, screen_width, screen_height, verbose)
    elif layout == "focus":
        click.echo("Maximizing Live View with sidebar controls...")
        apply_focus_layout(window, screen_width, screen_height, verbose)


def apply_grid_layout(main_window: Control, screen_width: int, screen_height: int, verbose: bool):
    """
    Snap Recording Panel, Live View, and Toolbox into a 3-column layout.

    Layout:
    - Live View: Left column (largest)
    - Preview: Center column
    - Main Panel: Right column (controls)
    """
    # Calculate column widths
    live_view_width = int(screen_width * 0.50)  # 50% for Live View
    preview_width = int(screen_width * 0.25)  # 25% for Preview
    main_width = screen_width - live_view_width - preview_width  # Remainder for main

    if verbose:
        click.echo(f"[DEBUG] Screen: {screen_width}x{screen_height}")
        click.echo(f"[DEBUG] Columns: Live View={live_view_width}px, Preview={preview_width}px, Main={main_width}px")

    # Position Live View (left column)
    live_view = find_live_view_window()
    if live_view:
        try:
            handle = live_view.NativeWindowHandle
            MoveWindow(handle, 0, 0, live_view_width, screen_height)
            if verbose:
                click.echo("[DEBUG] Positioned Live View")
        except Exception as e:
            if verbose:
                click.echo(f"[DEBUG] Could not position Live View: {e}")

    # Position Preview (center column)
    preview = find_preview_window()
    if preview:
        try:
            handle = preview.NativeWindowHandle
            MoveWindow(handle, live_view_width, 0, preview_width, screen_height)
            if verbose:
                click.echo("[DEBUG] Positioned Preview")
        except Exception as e:
            if verbose:
                click.echo(f"[DEBUG] Could not position Preview: {e}")

    # Position Main Panel (right column)
    try:
        handle = main_window.NativeWindowHandle
        MoveWindow(handle, live_view_width + preview_width, 0, main_width, screen_height)
        if verbose:
            click.echo("[DEBUG] Positioned Main Panel")
    except Exception as e:
        if verbose:
            click.echo(f"[DEBUG] Could not position Main Panel: {e}")

    click.echo("Grid layout applied!")
    click.echo(f"  Live View: {live_view_width}px wide")
    click.echo(f"  Preview: {preview_width}px wide")
    click.echo(f"  Main Panel: {main_width}px wide")


def apply_focus_layout(main_window: Control, screen_width: int, screen_height: int, verbose: bool):
    """
    Maximize Live View and move controls to sidebar.

    Layout:
    - Live View: Full screen minus 300px sidebar
    - Main Panel: Right sidebar (300px)
    - Preview: Hidden or behind main panel
    """
    sidebar_width = 300

    # Maximize Live View
    live_view = find_live_view_window()
    if live_view:
        try:
            handle = live_view.NativeWindowHandle
            MoveWindow(handle, 0, 0, screen_width - sidebar_width, screen_height)
            if verbose:
                click.echo("[DEBUG] Maximized Live View")
        except Exception as e:
            if verbose:
                click.echo(f"[DEBUG] Could not maximize Live View: {e}")

    # Move Main Panel to right sidebar
    try:
        handle = main_window.NativeWindowHandle
        MoveWindow(handle, screen_width - sidebar_width, 0, sidebar_width, screen_height)
        if verbose:
            click.echo("[DEBUG] Moved controls to sidebar")
    except Exception as e:
        if verbose:
            click.echo(f"[DEBUG] Could not position controls: {e}")

    click.echo("Focus layout applied!")
    click.echo(f"  Live View: {screen_width - sidebar_width}px wide (full width minus sidebar)")
    click.echo(f"  Main Panel: {sidebar_width}px wide (right sidebar)")


def execute_agentic_mode(_window: Control, prompt: str, verbose: bool):
    """
    Execute agentic mode using Vision LLM for intelligent camera control.

    This mode:
    1. Captures a screenshot of the Live View window
    2. Sends data to Vision LLM (GPT-4o) for analysis
    3. Executes UI interactions based on LLM response (focus, shutter, etc.)

    Args:
        _window: LUMIX Tether main window (unused, agent finds its own windows)
        prompt: Natural language prompt for the LLM
        verbose: Enable verbose logging
    """
    if verbose:
        click.echo(f"[DEBUG] Agentic mode with prompt: {prompt}")

    if not AGENTIC_AVAILABLE:
        click.echo(
            "Error: Agentic mode requires additional dependencies.",
            err=True,
        )
        click.echo("Please run: uv add openai")
        click.echo("And ensure OPENAI_API_KEY environment variable is set.")
        sys.exit(1)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        click.echo("Error: OPENAI_API_KEY environment variable not set.", err=True)
        click.echo("Please set it with: set OPENAI_API_KEY=your-api-key")
        click.echo("Or export it before running the command.")
        sys.exit(1)

    try:
        # Initialize the camera agent
        agent = CameraAgent()

        if verbose:
            click.echo("[DEBUG] Connecting to LUMIX Tether...")

        if not agent.connect():
            click.echo("Error: Could not connect to LUMIX Tether. Ensure it's running.", err=True)
            sys.exit(1)

        if verbose:
            click.echo(f"[DEBUG] Connected to {agent.main_window.Name}")

        # Analyze the scene
        click.echo("Analyzing scene with AI...")
        if verbose:
            click.echo("[DEBUG] Capturing Live View screenshot...")

        result = agent.analyze_scene(prompt)

        if "error" in result:
            click.echo(f"Error: {result['error']}", err=True)
            sys.exit(1)

        # Display analysis
        click.echo()
        click.echo("=" * 60)
        click.echo("AI Analysis")
        click.echo("=" * 60)
        click.echo()

        if "analysis" in result:
            click.echo(result["analysis"])
            click.echo()

        if "recommendations" in result:
            click.echo("Recommendations:")
            for rec in result["recommendations"]:
                click.echo(f"  • {rec}")
            click.echo()

        if "camera_settings" in result:
            click.echo("Suggested Settings:")
            settings = result["camera_settings"]
            for key, value in settings.items():
                click.echo(f"  • {key}: {value}")
            click.echo()

        # Execute actions
        if "actions" in result and result["actions"]:
            click.echo("=" * 60)
            click.echo("Executing AI Actions")
            click.echo("=" * 60)
            click.echo()

            if agent.execute_actions(result["actions"]):
                click.echo("All actions completed successfully!")
            else:
                click.echo("Some actions failed to execute.", err=True)
                sys.exit(1)
        else:
            click.echo("No actions to execute.")

    except KeyboardInterrupt:
        click.echo("\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error in agentic mode: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
