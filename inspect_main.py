#!/usr/bin/env python3
"""
Targeted LUMIX Tether Inspector - Focus on main window controls
Run with: uv run inspect_main.py
"""

import sys
from windows_use.uia.controls import Control, WindowControl, ButtonControl, EditControl


def print_control_info(control: Control, indent: int = 0) -> None:
    """Print detailed control information."""
    prefix = "  " * indent
    try:
        name = control.Name if control.Name else "(no name)"
        class_name = control.ClassName if control.ClassName else "(no class)"
        automation_id = control.AutomationId if control.AutomationId else ""
        control_type = control.ControlTypeName

        print(f"{prefix}[{control_type}] '{name}'")
        if automation_id:
            print(f"{prefix}  AutomationId: '{automation_id}'")

        try:
            rect = control.BoundingRectangle
            if rect.width() > 0 and rect.height() > 0:
                print(f"{prefix}  Rect: ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
        except:
            pass

        # Check for clickable patterns
        if control_type == "ButtonControl":
            print(f"{prefix}  *** BUTTON ***")
        elif control_type == "EditControl":
            print(f"{prefix}  *** EDIT ***")

        print()
    except Exception as e:
        print(f"{prefix}Error: {e}")


def find_all_buttons(control: Control, buttons: list, depth: int = 0) -> None:
    """Recursively find all buttons."""
    if depth > 15:
        return

    try:
        control_type = control.ControlTypeName
        name = control.Name if control.Name else ""

        if control_type == "ButtonControl":
            buttons.append((depth, control))

        for child in control.GetChildren():
            find_all_buttons(child, buttons, depth + 1)
    except:
        pass


def find_interactive_controls(control: Control, controls: list, depth: int = 0) -> None:
    """Find all interactive controls (buttons, edits, etc)."""
    if depth > 15:
        return

    try:
        control_type = control.ControlTypeName
        name = control.Name if control.Name else ""

        if control_type in ["ButtonControl", "EditControl", "CheckBoxControl", "ComboBoxControl", "SliderControl"]:
            controls.append((depth, control, control_type))

        for child in control.GetChildren():
            find_interactive_controls(child, controls, depth + 1)
    except:
        pass


def inspect_main_window():
    """Inspect the main LUMIX Tether window."""
    print("=" * 60)
    print("Inspecting Main LUMIX Tether Window")
    print("=" * 60)
    print()

    # Find the main window "1: DC-GH5"
    try:
        main_window = WindowControl(searchDepth=1, Name="1: DC-GH5")
        if not main_window.Exists(2, 0.5):
            print("Main window '1: DC-GH5' not found!")
            print("Trying alternate patterns...")

            # Try alternate patterns
            for pattern in ["DC-GH5", "GH5"]:
                main_window = WindowControl(searchDepth=1, Name=pattern)
                if main_window.Exists(1, 0.5):
                    print(f"Found window: '{pattern}'")
                    break
            else:
                print("Could not find main LUMIX window!")
                return
    except Exception as e:
        print(f"Error finding main window: {e}")
        return

    print(f"Found main window: '{main_window.Name}'")
    print(f"Class: {main_window.ClassName}")
    print()

    # Get window rect
    try:
        rect = main_window.BoundingRectangle
        print(f"Window Rect: ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
        print()
    except:
        pass

    # Find all buttons
    print("=" * 60)
    print("Searching for BUTTONS...")
    print("=" * 60)
    print()

    buttons = []
    find_all_buttons(main_window, buttons)

    print(f"Found {len(buttons)} buttons:")
    print()

    for depth, btn in buttons:
        try:
            name = btn.Name if btn.Name else "(no name)"
            aid = btn.AutomationId if btn.AutomationId else ""
            rect = btn.BoundingRectangle
            prefix = "  " * depth
            print(f"{prefix}[Button] '{name}'")
            if aid:
                print(f"{prefix}  AutomationId: '{aid}'")
            print(f"{prefix}  Position: ({rect.left}, {rect.top})")
            print()
        except Exception as e:
            print(f"Error: {e}")

    # Find all interactive controls
    print()
    print("=" * 60)
    print("Searching for ALL INTERACTIVE CONTROLS...")
    print("=" * 60)
    print()

    controls = []
    find_interactive_controls(main_window, controls)

    print(f"Found {len(controls)} interactive controls:")
    print()

    for depth, ctrl, ctype in controls:
        try:
            name = ctrl.Name if ctrl.Name else "(no name)"
            aid = ctrl.AutomationId if ctrl.AutomationId else ""
            rect = ctrl.BoundingRectangle
            print(f"[{ctype}] '{name}'")
            if aid:
                print(f"  AutomationId: '{aid}'")
            print(f"  Position: ({rect.left}, {rect.top})")
            print()
        except Exception as e:
            print(f"Error: {e}")

    # Look for specific patterns
    print()
    print("=" * 60)
    print("Searching for SHUTTER/PHOTO controls...")
    print("=" * 60)
    print()

    def find_shutter_controls(control: Control, matches: list, depth: int = 0) -> None:
        """Find controls with shutter-related names."""
        if depth > 15:
            return

        try:
            name = control.Name if control.Name else ""
            auto_id = control.AutomationId if control.AutomationId else ""
            search_text = (name + " " + auto_id).lower()

            keywords = ["shutter", "photo", "record", "capture", "trigger", "shoot", "snap"]

            if any(keyword in search_text for keyword in keywords):
                matches.append((depth, control))
        except:
            pass

        try:
            for child in control.GetChildren():
                find_shutter_controls(child, matches, depth + 1)
        except:
            pass

    shutter_controls = []
    find_shutter_controls(main_window, shutter_controls)

    if shutter_controls:
        print(f"Found {len(shutter_controls)} shutter-related controls:")
        print()

        for depth, ctrl in shutter_controls:
            try:
                name = ctrl.Name if ctrl.Name else "(no name)"
                aid = ctrl.AutomationId if ctrl.AutomationId else ""
                ctype = ctrl.ControlTypeName
                rect = ctrl.BoundingRectangle
                print(f"[{ctype}] '{name}'")
                if aid:
                    print(f"  AutomationId: '{aid}'")
                print(f"  Position: ({rect.left}, {rect.top})")
                print(f"  Size: {rect.width()}x{rect.height()}")
                print()
            except Exception as e:
                print(f"Error: {e}")
    else:
        print("No shutter-related controls found by name.")
        print("May need to search by position or visual inspection.")


def inspect_live_view_window():
    """Inspect the LIVE VIEW window."""
    print()
    print("=" * 60)
    print("Inspecting LIVE VIEW Window")
    print("=" * 60)
    print()

    try:
        live_view = WindowControl(searchDepth=1, Name="LIVE VIEW")
        if not live_view.Exists(2, 0.5):
            print("LIVE VIEW window not found!")
            return

        print(f"Found: '{live_view.Name}'")
        print(f"Class: {live_view.ClassName}")

        rect = live_view.BoundingRectangle
        print(f"Rect: ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
        print()

        # Print structure
        print("Window structure:")
        print()
        print_control_info(live_view, indent=0)

        # Look for clickable areas
        def find_clickable(control: Control, clickables: list, depth: int = 0) -> None:
            if depth > 10:
                return
            try:
                ctype = control.ControlTypeName
                if ctype in ["ButtonControl", "PaneControl", "ImageControl", "CustomControl"]:
                    name = control.Name if control.Name else ""
                    clickables.append((depth, ctype, name, control))
                for child in control.GetChildren():
                    find_clickable(child, clickables, depth + 1)
            except:
                pass

        clickables = []
        find_clickable(live_view, clickables)

        print(f"Found {len(clickables)} potentially clickable elements:")
        print()
        for depth, ctype, name, ctrl in clickables[:20]:  # First 20 only
            prefix = "  " * depth
            print(f"{prefix}[{ctype}] '{name}'")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main inspection."""
    inspect_main_window()
    inspect_live_view_window()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
