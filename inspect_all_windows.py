#!/usr/bin/env python3
"""
Comprehensive Window Inspector - Lists all top-level windows
Run with: uv run inspect_all_windows.py
"""

import sys
from windows_use.uia.controls import Control, WindowControl
from windows_use.uia.core import GetScreenSize


def print_control_tree(control: Control, indent: int = 0, max_depth: int = 6) -> None:
    """Recursively print the UI control tree with details."""
    if indent > max_depth:
        return

    prefix = "  " * indent
    try:
        name = control.Name if control.Name else "(no name)"
        class_name = control.ClassName if control.ClassName else "(no class)"
        automation_id = control.AutomationId if control.AutomationId else ""
        control_type = control.ControlTypeName
        handle = control.NativeWindowHandle

        # Print basic info
        print(f"{prefix}[{control_type}] '{name}'")
        if class_name != "(no class)":
            print(f"{prefix}  Class: {class_name}")
        if automation_id:
            print(f"{prefix}  AutomationId: '{automation_id}'")

        # Print bounding rect
        try:
            rect = control.BoundingRectangle
            if rect.width() > 0 and rect.height() > 0:
                print(f"{prefix}  Rect: ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
        except:
            pass

        # Print value if it exists
        try:
            if control.HasValueProperty:
                value = control.GetValue()
                if value:
                    print(f"{prefix}  Value: '{value}'")
        except:
            pass

        print()
    except Exception as e:
        print(f"{prefix}Error: {e}")
        return

    # Recursively print children
    try:
        for child in control.GetChildren():
            print_control_tree(child, indent + 1, max_depth)
    except Exception:
        pass


def list_all_windows() -> None:
    """List all windows using WindowControl with a broad search."""
    print("=" * 60)
    print("Searching for all visible windows...")
    print("=" * 60)
    print()

    screen_width, screen_height = GetScreenSize()
    print(f"Screen size: {screen_width}x{screen_height}")
    print()

    # Search for all windows using RegexName pattern
    # This will match any window
    try:
        # Use GetRootControl to get the desktop
        from windows_use.uia.controls import GetRootControl

        root = GetRootControl()
        print("Got root control, type:", root.ControlTypeName)
        print()

        # Get children (top-level windows)
        children = []
        try:
            child = root.GetFirstChildControl()
            while child:
                children.append(child)
                child = child.GetNextSiblingControl()
        except:
            pass

        if not children:
            print("No top-level windows found!")
            return

        print(f"Found {len(children)} top-level windows:")
        print()

        lumix_windows = []

        for i, window in enumerate(children):
            try:
                name = window.Name if window.Name else "(no name)"
                class_name = window.ClassName if window.ClassName else "(no class)"
                handle = window.NativeWindowHandle
                control_type = window.ControlTypeName

                # Check for LUMIX
                is_lumix = False
                if name and "lumix" in name.lower():
                    is_lumix = True
                    lumix_windows.append(window)
                elif class_name and "lumix" in class_name.lower():
                    is_lumix = True
                    lumix_windows.append(window)

                marker = " <-- LUMIX!" if is_lumix else ""

                print(f"{i + 1:3d}. [{control_type}] '{name}'{marker}")
                if class_name != "(no class)":
                    print(f"      Class: {class_name}")

                try:
                    rect = window.BoundingRectangle
                    if rect.width() > 0:
                        print(f"      Rect: ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
                except:
                    pass

                print()
            except Exception as e:
                print(f"{i + 1:3d}. Error: {e}")
                print()

        # If we found LUMIX windows, inspect them
        if lumix_windows:
            print()
            print("=" * 60)
            print(f"Found {len(lumix_windows)} LUMIX window(s) - inspecting...")
            print("=" * 60)
            print()

            for i, window in enumerate(lumix_windows):
                print()
                print("=" * 60)
                print(f"LUMIX Window {i + 1}: {window.Name}")
                print("=" * 60)
                print()
                print_control_tree(window, max_depth=8)

    except Exception as e:
        print(f"Error listing windows: {e}")
        import traceback
        traceback.print_exc()


def search_specific_patterns() -> None:
    """Search for specific LUMIX window patterns."""
    print()
    print("=" * 60)
    print("Searching for specific LUMIX patterns...")
    print("=" * 60)
    print()

    patterns = [
        "LUMIX Tether",
        "LUMIX",
        "GH5",
        "Panasonic",
    ]

    for pattern in patterns:
        try:
            print(f"Trying pattern: '{pattern}'")
            window = WindowControl(searchDepth=1, Name=pattern)
            if window.Exists(1, 0.5):
                print(f"  FOUND! Inspecting...")
                print()
                print_control_tree(window, max_depth=8)
                print()
                continue
            print(f"  Not found")
        except Exception as e:
            print(f"  Error: {e}")


def main():
    """Main inspection function."""
    print("Comprehensive Window Inspector")
    print("Looking for LUMIX Tether windows...")
    print()

    list_all_windows()
    search_specific_patterns()


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
