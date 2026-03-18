#!/usr/bin/env python3
"""
LUMIX Tether UI Inspector - Scans and prints the UI tree structure
Run with: uv run inspect_tether.py
"""

import sys
from windows_use.uia.controls import Control, WindowControl
from windows_use.uia.core import GetScreenSize


def print_control_tree(control: Control, indent: int = 0, max_depth: int = 10) -> None:
    """Recursively print the UI control tree."""
    if indent > max_depth:
        return

    prefix = "  " * indent
    try:
        name = control.Name if control.Name else "(no name)"
        class_name = control.ClassName if control.ClassName else "(no class)"
        automation_id = control.AutomationId if control.AutomationId else "(no id)"
        control_type = control.ControlTypeName
        handle = control.NativeWindowHandle

        print(f"{prefix}[{control_type}] '{name}'")
        print(f"{prefix}  Class: {class_name}")
        print(f"{prefix}  AutomationId: {automation_id}")
        print(f"{prefix}  Handle: 0x{handle:X}")

        try:
            rect = control.BoundingRectangle
            print(f"{prefix}  Rect: ({rect.left}, {rect.top}) - ({rect.right}, {rect.bottom}) [{rect.width()}x{rect.height()}]")
        except:
            print(f"{prefix}  Rect: (unable to get)")

        print()
    except Exception as e:
        print(f"{prefix}Error getting control info: {e}")
        return

    # Recursively print children
    try:
        for child in control.GetChildren():
            print_control_tree(child, indent + 1, max_depth)
    except:
        pass


def find_and_print_lumix_windows() -> None:
    """Find all LUMIX Tether related windows and print their structure."""
    print("=" * 60)
    print("LUMIX Tether UI Inspector")
    print("=" * 60)
    print()

    screen_width, screen_height = GetScreenSize()
    print(f"Screen size: {screen_width}x{screen_height}")
    print()

    # Find all top-level windows
    print("Searching for LUMIX Tether windows...")
    print()

    # Get root desktop
    root = Control()

    # Find all windows with LUMIX in the name
    lumix_windows = []

    def search_windows(control: Control, depth: int = 0) -> None:
        """Recursively search for LUMIX windows."""
        if depth > 2:  # Only search top-level windows
            return

        try:
            name = control.Name
            if name and "LUMIX" in name.upper():
                lumix_windows.append(control)
                return
        except:
            pass

        try:
            for child in control.GetChildren():
                search_windows(child, depth + 1)
        except:
            pass

    search_windows(root)

    if not lumix_windows:
        print("No LUMIX Tether windows found!")
        print("Please ensure LUMIX Tether is running.")
        return

    print(f"Found {len(lumix_windows)} LUMIX Tether window(s):")
    print()

    for i, window in enumerate(lumix_windows):
        print("=" * 60)
        print(f"Window {i + 1}: {window.Name}")
        print("=" * 60)
        print()
        print_control_tree(window, max_depth=6)


def search_for_buttons(target_window: Control) -> None:
    """Search for specific button controls in the window."""
    print()
    print("=" * 60)
    print("Searching for buttons...")
    print("=" * 60)
    print()

    # Search for buttons by iterating through all controls
    def find_buttons(control: Control, depth: int = 0) -> list:
        """Find all button controls."""
        buttons = []
        if depth > 10:
            return buttons

        try:
            control_type = control.ControlTypeName
            if control_type == "ButtonControl":
                buttons.append(control)
            elif control_type == "CheckBoxControl":
                buttons.append(control)
            elif control_type == "EditControl":
                buttons.append(control)
        except:
            pass

        try:
            for child in control.GetChildren():
                buttons.extend(find_buttons(child, depth + 1))
        except:
            pass

        return buttons

    buttons = find_buttons(target_window)

    print(f"Found {len(buttons)} interactive controls:")
    print()

    for i, btn in enumerate(buttons):
        try:
            name = btn.Name if btn.Name else "(no name)"
            aid = btn.AutomationId if btn.AutomationId else "(no id)"
            ctype = btn.ControlTypeName
            print(f"{i + 1}. [{ctype}] '{name}' (AutomationId: '{aid}')")
        except:
            pass


def search_for_shutter(target_window: Control) -> None:
    """Search specifically for shutter-related controls."""
    print()
    print("=" * 60)
    print("Searching for shutter-related controls...")
    print("=" * 60)
    print()

    # Search for controls with shutter/photo related names
    def find_shutter_controls(control: Control, depth: int = 0) -> list:
        """Find all shutter-related controls."""
        matches = []
        if depth > 10:
            return matches

        try:
            name = control.Name if control.Name else ""
            auto_id = control.AutomationId if control.AutomationId else ""
            search_text = (name + " " + auto_id).lower()

            if any(keyword in search_text for keyword in ["shutter", "photo", "record", "capture", "trigger"]):
                matches.append(control)
        except:
            pass

        try:
            for child in control.GetChildren():
                matches.extend(find_shutter_controls(child, depth + 1))
        except:
            pass

        return matches

    matches = find_shutter_controls(target_window)

    if not matches:
        print("No shutter-related controls found.")
    else:
        print(f"Found {len(matches)} shutter-related controls:")
        print()
        for i, match in enumerate(matches):
            try:
                name = match.Name if match.Name else "(no name)"
                aid = match.AutomationId if match.AutomationId else "(no id)"
                ctype = match.ControlTypeName
                rect = match.BoundingRectangle
                print(f"{i + 1}. [{ctype}] '{name}'")
                print(f"   AutomationId: '{aid}'")
                print(f"   Position: ({rect.left}, {rect.top}) size: {rect.width()}x{rect.height()}")
                print()
            except Exception as e:
                print(f"{i + 1}. Error: {e}")
                print()


def main():
    """Main inspection function."""
    # First, try to find the main LUMIX Tether window
    print("Looking for main LUMIX Tether window...")
    print()

    try:
        main_window = WindowControl(searchDepth=1, Name="LUMIX Tether")
        if main_window.Exists(2, 0.5):
            print("Found main window: 'LUMIX Tether'")
            print()
            print("=" * 60)
            print("Main Window Structure")
            print("=" * 60)
            print()
            print_control_tree(main_window, max_depth=8)
            search_for_buttons(main_window)
            search_for_shutter(main_window)
            return
    except:
        pass

    # Try alternate patterns
    patterns = ["LUMIX Tether for Streaming", "LUMIX"]

    for pattern in patterns:
        try:
            window = WindowControl(searchDepth=1, Name=pattern)
            if window.Exists(1, 0.5):
                print(f"Found window: '{pattern}'")
                print()
                print_control_tree(window, max_depth=8)
                search_for_buttons(window)
                search_for_shutter(window)
                return
        except:
            pass

    # If no specific window found, show all LUMIX windows
    find_and_print_lumix_windows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
