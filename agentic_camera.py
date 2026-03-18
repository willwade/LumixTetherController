#!/usr/bin/env python3
"""
Agentic Camera Controller - LLM-powered intelligent camera control

This module enables natural language control of the LUMIX Tether camera
using OpenAI's GPT-4o for vision analysis and decision-making.
"""

import base64
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from windows_use.uia.controls import Control, WindowControl
from windows_use.uia.core import Click, GetScreenSize


class CameraAgent:
    """Intelligent camera agent using Vision LLM."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize the camera agent.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.main_window = None
        self.live_view = None
        self.preview_window = None

    def connect(self) -> bool:
        """Connect to LUMIX Tether windows."""
        self.main_window = self._find_main_window()
        self.live_view = self._find_live_view_window()
        self.preview_window = self._find_preview_window()
        return self.main_window is not None

    def _find_main_window(self) -> Control | None:
        """Find the main LUMIX Tether window."""
        try:
            window = WindowControl(searchDepth=1, Name="1: DC-GH5")
            if window.Exists(1, 0.5):
                return window
        except Exception:
            pass
        return None

    def _find_live_view_window(self) -> Control | None:
        """Find the LIVE VIEW window."""
        try:
            window = WindowControl(searchDepth=1, Name="LIVE VIEW")
            if window.Exists(1, 0.5):
                return window
        except Exception:
            pass
        return None

    def _find_preview_window(self) -> Control | None:
        """Find the Preview window."""
        try:
            window = WindowControl(searchDepth=1, RegexName=r"Preview.*")
            if window.Exists(1, 0.5):
                return window
        except Exception:
            pass
        return None

    def capture_live_view_screenshot(self) -> bytes | None:
        """
        Capture a screenshot of the Live View window.

        Returns:
            Screenshot image data as bytes, or None if failed.
        """
        if not self.live_view:
            return None

        try:
            from PIL import ImageGrab

            rect = self.live_view.BoundingRectangle
            screenshot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))

            # Convert to bytes
            from io import BytesIO

            buffer = BytesIO()
            screenshot.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None

    def encode_image_base64(self, image_data: bytes) -> str:
        """Encode image data to base64 string."""
        return base64.b64encode(image_data).decode("utf-8")

    def analyze_scene(self, prompt: str) -> dict[str, Any]:
        """
        Analyze the current camera view using GPT-4o Vision.

        Args:
            prompt: Natural language description of what to analyze.

        Returns:
            Dictionary with analysis results including suggested actions.
        """
        screenshot = self.capture_live_view_screenshot()
        if not screenshot:
            return {"error": "Could not capture Live View screenshot"}

        base64_image = self.encode_image_base64(screenshot)

        # Build the analysis prompt
        system_prompt = """You are an intelligent camera assistant for a Panasonic GH5M2 camera.
You can see the Live View and help with:
- Scene analysis (what's in frame, lighting, composition)
- Camera settings recommendations (aperture, ISO, shutter speed)
- Focus point suggestions (x, y coordinates for Touch AF)
- Photography techniques

When suggesting camera actions, respond in JSON format:
{
    "analysis": "Your scene analysis here",
    "recommendations": ["list of recommendations"],
    "actions": [
        {
            "type": "shutter|record|focus|layout|wait",
            "description": "what to do",
            "coordinates": {"x": 0, "y": 0}  // for focus actions only
        }
    ],
    "camera_settings": {
        "aperture": "f/2.8",
        "iso": 400,
        "shutter_speed": "1/125"
    }
}

Be specific with coordinates. The Live View window size will be provided."""

        # Get Live View dimensions
        rect = self.live_view.BoundingRectangle if self.live_view else None
        if rect:
            window_info = f"\nLive View window: {rect.width()}x{rect.height()} pixels at ({rect.left}, {rect.top})"
        else:
            window_info = ""

        user_prompt = f"""User Request: {prompt}

{window_info}

Analyze the scene and provide specific camera control recommendations."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                },
                            },
                        ],
                    },
                ],
                max_tokens=1000,
            )

            result = response.choices[0].message.content

            # Try to parse as JSON
            import json

            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If not JSON, return as text analysis
                return {
                    "analysis": result,
                    "actions": [],
                }

        except Exception as e:
            return {"error": f"LLM analysis failed: {e}"}

    def execute_actions(self, actions: list[dict[str, Any]]) -> bool:
        """
        Execute camera actions based on LLM recommendations.

        Args:
            actions: List of action dictionaries from the LLM.

        Returns:
            True if all actions executed successfully, False otherwise.
        """
        for action in actions:
            action_type = action.get("type")
            description = action.get("description", "")

            print(f"Executing: {description}")

            try:
                if action_type == "shutter":
                    self._click_shutter()
                elif action_type == "record":
                    self._click_record()
                elif action_type == "focus":
                    coords = action.get("coordinates", {})
                    x = coords.get("x", 0)
                    y = coords.get("y", 0)
                    self._click_focus(x, y)
                elif action_type == "layout":
                    self._apply_layout(action.get("layout", "grid"))
                elif action_type == "wait":
                    import time

                    duration = action.get("duration", 1.0)
                    time.sleep(duration)
                else:
                    print(f"Unknown action type: {action_type}")

            except Exception as e:
                print(f"Error executing action: {e}")
                return False

        return True

    def _click_shutter(self):
        """Click the shutter button."""
        if not self.main_window:
            raise Exception("Main window not connected")

        rect = self.main_window.BoundingRectangle
        button_x = rect.left + rect.width() // 2
        button_y = rect.top + 60
        Click(button_x, button_y)

    def _click_record(self):
        """Click the record button."""
        if not self.main_window:
            raise Exception("Main window not connected")

        rect = self.main_window.BoundingRectangle
        button_x = rect.left + rect.width() // 2 - 80
        button_y = rect.top + 60
        Click(button_x, button_y)

    def _click_focus(self, x: int, y: int):
        """
        Click at specific coordinates in Live View for Touch AF.

        Args:
            x: X coordinate relative to Live View window
            y: Y coordinate relative to Live View window
        """
        if not self.live_view:
            raise Exception("Live View window not connected")

        rect = self.live_view.BoundingRectangle
        absolute_x = rect.left + x
        absolute_y = rect.top + y

        # Bring Live View to foreground
        from windows_use.uia.core import SetForegroundWindow

        handle = self.live_view.NativeWindowHandle
        SetForegroundWindow(handle)

        import time

        time.sleep(0.1)
        Click(absolute_x, absolute_y)

    def _apply_layout(self, layout: str):
        """Apply window layout (grid or focus)."""
        screen_width, screen_height = GetScreenSize()

        if layout == "grid":
            self._apply_grid_layout(screen_width, screen_height)
        elif layout == "focus":
            self._apply_focus_layout(screen_width, screen_height)

    def _apply_grid_layout(self, screen_width: int, screen_height: int):
        """Apply 3-column grid layout."""
        live_view_width = int(screen_width * 0.50)
        preview_width = int(screen_width * 0.25)
        main_width = screen_width - live_view_width - preview_width

        from windows_use.uia.core import MoveWindow

        if self.live_view:
            handle = self.live_view.NativeWindowHandle
            MoveWindow(handle, 0, 0, live_view_width, screen_height)

        if self.preview_window:
            handle = self.preview_window.NativeWindowHandle
            MoveWindow(handle, live_view_width, 0, preview_width, screen_height)

        if self.main_window:
            handle = self.main_window.NativeWindowHandle
            MoveWindow(handle, live_view_width + preview_width, 0, main_width, screen_height)

    def _apply_focus_layout(self, screen_width: int, screen_height: int):
        """Apply focus layout with maximized Live View."""
        sidebar_width = 300

        from windows_use.uia.core import MoveWindow

        if self.live_view:
            handle = self.live_view.NativeWindowHandle
            MoveWindow(handle, 0, 0, screen_width - sidebar_width, screen_height)

        if self.main_window:
            handle = self.main_window.NativeWindowHandle
            MoveWindow(handle, screen_width - sidebar_width, 0, sidebar_width, screen_height)


def demo_agentic_mode(prompt: str):
    """
    Demonstrate agentic camera control with LLM.

    Args:
        prompt: Natural language prompt for the LLM.
    """
    print("=" * 60)
    print("Agentic Camera Control")
    print("=" * 60)
    print()

    # Initialize agent
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    agent = CameraAgent()

    print("Connecting to LUMIX Tether...")
    if not agent.connect():
        print("Error: Could not connect to LUMIX Tether. Ensure it's running.")
        return

    print(f"Connected! Found windows:")
    print(f"  - Main: {agent.main_window.Name if agent.main_window else 'N/A'}")
    print(f"  - Live View: {agent.live_view.Name if agent.live_view else 'N/A'}")
    print(f"  - Preview: {agent.preview_window.Name if agent.preview_window else 'N/A'}")
    print()

    print(f"Analyzing scene with prompt: '{prompt}'")
    print()

    # Analyze scene
    result = agent.analyze_scene(prompt)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    # Display analysis
    if "analysis" in result:
        print("Scene Analysis:")
        print(result["analysis"])
        print()

    if "recommendations" in result:
        print("Recommendations:")
        for rec in result["recommendations"]:
            print(f"  - {rec}")
        print()

    if "camera_settings" in result:
        print("Suggested Camera Settings:")
        settings = result["camera_settings"]
        for key, value in settings.items():
            print(f"  - {key}: {value}")
        print()

    # Execute actions
    if "actions" in result and result["actions"]:
        print("Executing Actions:")
        print()

        if agent.execute_actions(result["actions"]):
            print("All actions executed successfully!")
        else:
            print("Some actions failed to execute.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: uv run agentic_camera.py \"your natural language prompt\"")
        print()
        print("Examples:")
        print('  uv run agentic_camera.py "Take a portrait photo"')
        print('  uv run agentic_camera.py "Focus on the center subject"')
        print('  uv run agentic_camera.py "The scene is too dark, fix exposure"')
        sys.exit(1)

    demo_agentic_mode(" ".join(sys.argv[1:]))
