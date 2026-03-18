#!/usr/bin/env python3
"""
Visual Inspector - Capture screenshots and analyze LUMIX Tether UI
Run with: uv run visual_inspect.py
"""

import sys
from pathlib import Path

from windows_use.uia.controls import WindowControl
from windows_use.uia.core import GetScreenSize, Click
from PIL import Image, ImageDraw, ImageFont


def capture_window_screenshot(window: WindowControl, output_path: str) -> bool:
    """Capture a screenshot of a specific window."""
    try:
        rect = window.BoundingRectangle

        # Get screen capture (using PIL's ImageGrab)
        from PIL import ImageGrab

        # Capture the screen area where the window is
        screenshot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        screenshot.save(output_path)
        return True
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return False


def capture_and_annotate():
    """Capture and annotate LUMIX Tether windows."""
    print("=" * 60)
    print("Visual Inspector - Capturing LUMIX Tether UI")
    print("=" * 60)
    print()

    screen_width, screen_height = GetScreenSize()
    print(f"Screen size: {screen_width}x{screen_height}")
    print()

    # Find all LUMIX windows
    windows_info = []

    # Main window
    try:
        main = WindowControl(searchDepth=1, Name="1: DC-GH5")
        if main.Exists(1, 0.5):
            rect = main.BoundingRectangle
            windows_info.append({
                "name": "Main - 1: DC-GH5",
                "rect": rect,
                "window": main,
                "color": (255, 0, 0)  # Red
            })
            print(f"Found Main: '1: DC-GH5' at ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
    except:
        pass

    # Live View
    try:
        live_view = WindowControl(searchDepth=1, Name="LIVE VIEW")
        if live_view.Exists(1, 0.5):
            rect = live_view.BoundingRectangle
            windows_info.append({
                "name": "Live View",
                "rect": rect,
                "window": live_view,
                "color": (0, 255, 0)  # Green
            })
            print(f"Found: 'LIVE VIEW' at ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
    except:
        pass

    # Preview
    try:
        preview = WindowControl(searchDepth=1, RegexName=r"Preview.*")
        if preview.Exists(1, 0.5):
            rect = preview.BoundingRectangle
            windows_info.append({
                "name": "Preview",
                "rect": rect,
                "window": preview,
                "color": (0, 0, 255)  # Blue
            })
            print(f"Found: '{preview.Name}' at ({rect.left}, {rect.top}) {rect.width()}x{rect.height()}")
    except:
        pass

    if not windows_info:
        print("No LUMIX windows found!")
        return

    print()

    # Create output directory
    output_dir = Path("screenshots")
    output_dir.mkdir(exist_ok=True)

    # Capture full screen with annotations
    print("Capturing screen layout...")
    try:
        from PIL import ImageGrab

        screenshot = ImageGrab.grab()
        draw = ImageDraw.Draw(screenshot)

        # Try to load a font
        try:
            font = ImageFont.truetype("arial.ttf", 20)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
            small_font = font

        # Draw boxes around each window
        for info in windows_info:
            rect = info["rect"]
            color = info["color"]
            name = info["name"]

            # Draw rectangle
            draw.rectangle(
                [(rect.left, rect.top), (rect.right - 1, rect.bottom - 1)],
                outline=color,
                width=3
            )

            # Draw label
            draw.text((rect.left, rect.top - 25), name, fill=color, font=font)

            # Draw dimensions
            dims = f"{rect.width()}x{rect.height()}"
            draw.text((rect.left, rect.bottom + 5), dims, fill=color, font=small_font)

            # Draw center point
            center_x = rect.left + rect.width() // 2
            center_y = rect.top + rect.height() // 2
            draw.ellipse(
                [(center_x - 5, center_y - 5), (center_x + 5, center_y + 5)],
                fill=color
            )

        # Save annotated screenshot
        output_path = output_dir / "layout_annotated.png"
        screenshot.save(output_path)
        print(f"Saved annotated layout: {output_path}")

        # Calculate grid suggestions
        print()
        print("=" * 60)
        print("Grid Layout Analysis")
        print("=" * 60)
        print()

        if len(windows_info) >= 2:
            # Calculate optimal positions
            total_width = sum(w["rect"].width() for w in windows_info)
            max_height = max(w["rect"].height() for w in windows_info)

            print(f"Total width of all windows: {total_width}")
            print(f"Max height: {max_height}")
            print(f"Screen width: {screen_width}")
            print()

            if total_width < screen_width:
                column_width = screen_width // len(windows_info)
                print(f"Suggested 3-column layout (each {column_width}px wide):")
                print()

                for i, info in enumerate(windows_info):
                    x = i * column_width
                    print(f"  {info['name']}: Move to ({x}, 0) size {column_width}x{max_height}")

        print()

        # Generate click coordinates for main window center
        print("=" * 60)
        print("Suggested Click Coordinates")
        print("=" * 60)
        print()

        for info in windows_info:
            rect = info["rect"]
            center_x = rect.left + rect.width() // 2
            center_y = rect.top + rect.height() // 2
            print(f"{info['name']}:")
            print(f"  Center: ({center_x}, {center_y})")
            print(f"  Top-left: ({rect.left}, {rect.top})")
            print(f"  Bottom-right: ({rect.right}, {rect.bottom})")
            print()

    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        import traceback
        traceback.print_exc()

    # Save individual window screenshots
    print()
    print("Capturing individual windows...")
    print()

    for info in windows_info:
        filename = output_dir / f"{info['name'].replace(' ', '_').replace('-', '_')}.png"
        if capture_window_screenshot(info["window"], str(filename)):
            print(f"Saved: {filename}")


def test_click_coordinates():
    """Test clicking at specific coordinates."""
    print()
    print("=" * 60)
    print("Test Click Coordinates")
    print("=" * 60)
    print()
    print("To test a click, run:")
    print("  uv run visual_inspect.py --test-click X Y")
    print()


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test-click":
        if len(sys.argv) > 3:
            try:
                x = int(sys.argv[2])
                y = int(sys.argv[3])
                print(f"Clicking at ({x}, {y})...")
                Click(x, y)
                print("Click executed!")
                return
            except ValueError:
                print("Invalid coordinates")
                return
        else:
            print("Usage: uv run visual_inspect.py --test-click X Y")
            return

    capture_and_annotate()
    test_click_coordinates()


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
