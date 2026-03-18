#!/usr/bin/env python3
"""
LUMIX Tether Bridge (Grid 3 & AI Edition)

An automation bridge that allows Grid 3 (AAC software) and Large Language Models
to control the Panasonic GH5M2 via the LUMIX Tether desktop application.

Uses Windows-Use framework (based on Python-UIAutomation-for-Windows) to interact
with the UI automation tree.
"""

import os
import sys

import click

from windows_use.uia.controls import Control, WindowControl
from windows_use.uia.core import (
    Click,
    GetScreenSize,
    MoveWindow,
    SetForegroundWindow,
)

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
    type=click.Choice(["shutter", "record", "lv-on", "af-on"], case_sensitive=False),
    help="Deterministic action to perform (no LLM involved)",
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
def main(action: str | None, layout: str | None, ai: str | None, verbose: bool):
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

        # Find the main window
        main_window = find_main_window()

        if main_window is None:
            click.echo(
                "Error: LUMIX Tether application not found. Please ensure it's running.",
                err=True,
            )
            sys.exit(1)

        if verbose:
            click.echo(f"[DEBUG] Found main window: {main_window.Name}")

        # Execute the requested command
        if action:
            execute_deterministic_action(main_window, action, verbose)
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


def execute_deterministic_action(window: Control, action: str, verbose: bool):
    """
    Execute deterministic UI actions without LLM involvement.

    Args:
        window: LUMIX Tether main window control
        action: Action to perform (shutter, record, lv-on, af-on)
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


def click_shutter_button(window: Control, verbose: bool):
    """
    Click the physical shutter button in the Recording Panel.

    Uses coordinate-based clicking as the Qt/QML UI doesn't expose standard UI controls.
    The shutter button is at the top of the main window.
    """
    if verbose:
        click.echo("[DEBUG] Clicking shutter button...")

    try:
        # Get the window position
        rect = window.BoundingRectangle

        # Based on visual inspection, the shutter button is at the top center of the main window
        # The main window is typically 484px wide
        # Shutter button appears to be approximately 40px from the top, centered horizontally

        # Calculate shutter button position (top-center of window, accounting for title bar)
        # Title bar is typically ~32px, controls start after that
        button_x = rect.left + rect.width() // 2
        button_y = rect.top + 60  # Approximate position based on UI structure

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

    click.echo(
        "Warning: Live View window not found. Please open it manually from LUMIX Tether.",
        err=True,
    )


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
