#!/usr/bin/env python3
"""
Agentic Camera Controller - LLM-powered intelligent camera control

This module enables natural language control of the LUMIX Tether camera
using OpenAI's GPT-4o for vision analysis and decision-making.
"""

import base64
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from windows_use.uia.controls import Control, WindowControl
from windows_use.uia.core import Click, GetScreenSize, SetForegroundWindow

# Import control position manager
try:
    from lumix_controls import get_control_position
    CONTROLS_AVAILABLE = True
except ImportError:
    CONTROLS_AVAILABLE = False
    print("Warning: lumix_controls not available, using default positions")

# Import Lumix SDK for direct camera control
try:
    from lumix_sdk import create_sdk, LumixSDK, LMX_DEF_WB_AUTO, LMX_DEF_WB_DAYLIGHT
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Warning: lumix_sdk not available, using coordinate-based control")


class CameraAgent:
    """Intelligent camera agent using Vision LLM."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize the camera agent.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client: OpenAI | None = None  # Lazy initialization
        self.main_window = None
        self.live_view = None
        self.preview_window = None

        # Initialize SDK if available
        self.sdk: LumixSDK | None = None
        if SDK_AVAILABLE:
            try:
                self.sdk = create_sdk()
                if self.sdk:
                    devices = self.sdk.get_devices()
                    if devices and len(devices) > 0:
                        print(f"SDK: Found {len(devices)} device(s): {devices[0]['model']}")
                        if self.sdk.select_device(0) and self.sdk.open_session():
                            print("SDK: Connected to camera successfully!")
                        else:
                            print("SDK: Failed to connect, using coordinate-based control")
                            self.sdk = None
                    else:
                        print("SDK: No devices found, using coordinate-based control")
                        self.sdk = None
                else:
                    self.sdk = None
            except Exception as e:
                print(f"SDK: Initialization failed: {e}")
                self.sdk = None

    def connect(self) -> bool:
        """
        Connect to LUMIX Tether windows.

        Will attempt to launch LUMIX Tether and open Live View if needed.

        Returns:
            True if successfully connected, False otherwise.
        """
        # Try to find main window
        self.main_window = self._find_main_window()

        # If not found, try to launch LUMIX Tether
        if self.main_window is None:
            print("LUMIX Tether not found. Attempting to launch...")
            if self._launch_lumix_tether():
                self.main_window = self._find_main_window()
            else:
                print("Error: Could not launch LUMIX Tether")
                return False

        if not self.main_window:
            print("Error: Main window not available")
            return False

        # Find or open Live View
        self.live_view = self._find_live_view_window()
        if not self.live_view:
            print("Opening Live View...")
            if self.main_window:
                self._open_live_view_from_main(self.main_window)
                self.live_view = self._find_live_view_window()

        # Find preview (optional)
        self.preview_window = self._find_preview_window()

        return True

    def _launch_lumix_tether(self) -> bool:
        """Launch LUMIX Tether application and wait for it to become ready."""
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
            print("LUMIX Tether not found in standard installation paths.")
            return False

        try:
            subprocess.Popen([lumix_path])
            # Wait for window to appear (up to 10 seconds)
            for _ in range(20):
                time.sleep(0.5)
                if self._find_main_window():
                    return True
            return False
        except Exception as e:
            print(f"Error launching LUMIX Tether: {e}")
            return False

    def _open_live_view_from_main(self, main_window: Control) -> bool:
        """Open Live View window from the main window."""
        try:
            handle = main_window.NativeWindowHandle
            SetForegroundWindow(handle)
            time.sleep(0.2)

            rect = main_window.BoundingRectangle

            # Try clicking on the Live View button/menu
            # Common positions - may need adjustment
            Click(rect.left + 100, rect.top + 40)
            time.sleep(0.3)
            Click(rect.left + rect.width() // 4, rect.top + 100)
            time.sleep(0.5)

            return self._find_live_view_window() is not None
        except Exception as e:
            print(f"Error opening Live View: {e}")
            return False

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

    def _extract_json_from_response(self, response: str) -> dict[str, Any] | None:
        """
        Extract JSON from a response that may contain markdown code blocks.

        Args:
            response: The raw response string from the LLM.

        Returns:
            Parsed JSON dict if found, None otherwise.
        """
        import json
        import re

        # First, try direct parsing
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        # Pattern matches ```json ... ``` or ``` ... ```
        patterns = [
            r"```json\s*(.*?)\s*```",  # ```json ... ```
            r"```\s*(.*?)\s*```",      # ``` ... ```
            r"\{.*\}",                 # Raw JSON object (greedy)
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if match.groups() else match.group(0))
                except (json.JSONDecodeError, IndexError):
                    continue

        return None

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
        system_prompt = """You are an autonomous camera assistant for a Panasonic GH5M2 camera, helping users with disabilities.
You can see the Live View and must ACTUALLY EXECUTE camera actions, not just suggest them.

IMPORTANT: You are an AGENT that EXECUTES actions. This is for accessibility - users NEED you to DO things.

USER INTENT INTERPRETATION:
- "Take a photo" / "capture" / "shoot" → EXECUTE shutter action IMMEDIATELY
- "Record video" / "start recording" → EXECUTE record action
- "Focus on X" → EXECUTE focus action at X coordinates
- Settings requests → EXECUTE set_aperture, set_iso, set_wb actions with the value

Your response MUST be valid JSON ONLY - no markdown, no code blocks, no extra text:
{
    "analysis": "Your scene analysis here",
    "recommendations": ["list of recommendations"],
    "actions": [
        {
            "type": "shutter|record|focus|layout|wait|set_aperture|set_iso|set_wb",
            "description": "what to do",
            "coordinates": {"x": 0, "y": 0},
            "duration": 1.0,
            "value": "f/2.8 or 400 or AWB etc"
        }
    ],
    "camera_settings": {
        "aperture": "f/2.8",
        "iso": 400,
        "shutter_speed": "1/125",
        "white_balance": "AWB"
    }
}

Action types:
- "shutter": Click the shutter button to capture a photo (USE THIS when user asks to take a photo!)
- "record": Toggle video recording
- "focus": Click at coordinates (x, y) in Live View to trigger Touch AF
- "layout": Apply window layout ("grid" or "focus")
- "wait": Wait for specified duration (in seconds)
- "set_aperture": Change aperture (value like "f/2.8", "f/4", etc.)
- "set_iso": Change ISO (value like "100", "400", "800", etc.)
- "set_wb": Change white balance (value like "AWB", "Daylight", "Cloudy", etc.)

CRITICAL:
- Return ONLY raw JSON. Do NOT wrap in ```json``` or any markdown.
- When user says "take a photo" or "capture", ALWAYS include a "shutter" action!
- When user asks to change settings, INCLUDE "set_aperture"/"set_iso"/"set_wb" actions with the value!
- This is for users with disabilities who need you to ACT, not just suggest."""

        # Get Live View dimensions
        rect = self.live_view.BoundingRectangle if self.live_view else None
        if rect:
            window_info = f"\nLive View window: {rect.width()}x{rect.height()} pixels at ({rect.left}, {rect.top})"
        else:
            window_info = ""

        user_prompt = f"""User Request: {prompt}

{window_info}

CRITICAL INSTRUCTIONS:
1. If user asks to "take a photo", "capture", "shoot", etc → YOU MUST include a "shutter" action!
2. If user asks to "record" or "video" → YOU MUST include a "record" action!
3. If user asks to "focus" → YOU MUST include a "focus" action with coordinates!
4. This is an AUTONOMOUS agent for accessibility - EXECUTE the requested actions!

Analyze the scene, provide recommendations, and EXECUTE the requested action.
Return JSON only."""

        # Lazy initialize OpenAI client
        if self.client is None:
            if not self.api_key:
                return {"error": "OPENAI_API_KEY not set"}
            self.client = OpenAI(api_key=self.api_key)

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

            # Try to parse as JSON with markdown stripping
            parsed = self._extract_json_from_response(result)

            if parsed:
                # Ensure actions key exists
                if "actions" not in parsed:
                    parsed["actions"] = []
                return parsed
            else:
                # If parsing failed, return as text analysis with no actions
                return {
                    "analysis": result,
                    "recommendations": [],
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
        if not actions:
            print("No actions to execute.")
            return True

        import time

        for i, action in enumerate(actions, 1):
            action_type = action.get("type")
            description = action.get("description", "")

            print(f"[{i}/{len(actions)}] Executing: {description}")

            try:
                if action_type == "shutter":
                    self._click_shutter()
                    print("  [OK] Photo captured!")
                elif action_type == "record":
                    self._click_record()
                    print("  [OK] Recording toggled!")
                elif action_type == "focus":
                    coords = action.get("coordinates", {})
                    x = coords.get("x", 0)
                    y = coords.get("y", 0)
                    self._click_focus(x, y)
                    print(f"  [OK] Focused at ({x}, {y})")
                elif action_type == "layout":
                    layout_type = action.get("layout", "grid")
                    self._apply_layout(layout_type)
                    print(f"  [OK] Applied {layout_type} layout!")
                elif action_type == "wait":
                    duration = action.get("duration", 1.0)
                    print(f"  ... Waiting {duration}s...")
                    time.sleep(duration)
                elif action_type == "set_aperture":
                    value = action.get("value", "")
                    self._set_aperture(value)
                    print(f"  [OK] Set aperture to {value}")
                elif action_type == "set_iso":
                    value = action.get("value", "")
                    self._set_iso(value)
                    print(f"  [OK] Set ISO to {value}")
                elif action_type == "set_wb":
                    value = action.get("value", "")
                    self._set_white_balance(value)
                    print(f"  [OK] Set white balance to {value}")
                else:
                    print(f"  [WARN] Unknown action type: {action_type}")

                # Small delay between actions for stability
                if i < len(actions):
                    time.sleep(0.2)

            except Exception as e:
                print(f"  [ERROR] Error executing action: {e}")
                return False

        return True

    def _click_shutter(self):
        """Trigger shutter using SDK (if available) or coordinate-based fallback."""
        # Try SDK first
        if self.sdk and self.sdk.is_open:
            try:
                if self.sdk.trigger_shutter():
                    print("    [DEBUG] SDK shutter triggered successfully!")
                    return
                print("    [DEBUG] SDK shutter failed, trying coordinate method")
            except Exception as e:
                print(f"    [DEBUG] SDK shutter error: {e}, trying coordinate method")

        # Fallback to coordinate-based method
        if not self.main_window:
            raise Exception("Main window not connected")

        # Bring main window to foreground first
        handle = self.main_window.NativeWindowHandle
        SetForegroundWindow(handle)
        time.sleep(0.2)  # Give window time to come to foreground

        # Get position from calibration (works at any window size)
        if CONTROLS_AVAILABLE:
            pos = get_control_position(self.main_window, "shutter")
            if pos:
                button_x, button_y = pos
            else:
                # Fallback to hardcoded position
                rect = self.main_window.BoundingRectangle
                button_x = rect.left + int(rect.width() * 0.699)
                button_y = rect.top + int(rect.height() * 0.084)
        else:
            rect = self.main_window.BoundingRectangle
            button_x = rect.left + int(rect.width() * 0.699)
            button_y = rect.top + int(rect.height() * 0.084)

        print(f"    [DEBUG] Clicking shutter at ({button_x}, {button_y})")
        Click(button_x, button_y)

    def _click_record(self):
        """Click the record button."""
        if not self.main_window:
            raise Exception("Main window not connected")

        # Bring main window to foreground first
        handle = self.main_window.NativeWindowHandle
        SetForegroundWindow(handle)
        time.sleep(0.2)

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

    def _set_aperture(self, value: str):
        """
        Set aperture using SDK (if available) or coordinate-based fallback.
        """
        # Try SDK first
        if self.sdk and self.sdk.is_open:
            try:
                # Parse f-number from string (e.g., "f/2.8" -> 2.8)
                import re
                match = re.search(r"(\d+\.?\d*)", value)
                if match:
                    f_number = float(match.group(1))
                    if self.sdk.set_aperture_f_stop(f_number):
                        return  # Success!
                    print("    [DEBUG] SDK aperture failed, trying coordinate method")
            except Exception as e:
                print(f"    [DEBUG] SDK aperture error: {e}, trying coordinate method")

        # Fallback to coordinate-based method
        if not self.main_window:
            raise Exception("Main window not connected")

        handle = self.main_window.NativeWindowHandle
        SetForegroundWindow(handle)
        time.sleep(0.2)

        # Get position from calibration
        if CONTROLS_AVAILABLE:
            pos = get_control_position(self.main_window, "aperture")
            if pos:
                control_x, control_y = pos
            else:
                rect = self.main_window.BoundingRectangle
                control_x = rect.left + int(rect.width() * 0.377)
                control_y = rect.top + int(rect.height() * 0.187)
        else:
            rect = self.main_window.BoundingRectangle
            control_x = rect.left + int(rect.width() * 0.377)
            control_y = rect.top + int(rect.height() * 0.187)

        print(f"    [DEBUG] Clicking aperture control at ({control_x}, {control_y})")
        Click(control_x, control_y)
        time.sleep(0.3)

        # Navigate dropdown using arrow keys and select value
        self._select_dropdown_value("aperture", value)

    def _set_iso(self, value: str):
        """
        Set ISO using SDK (if available) or coordinate-based fallback.
        """
        # Try SDK first
        if self.sdk and self.sdk.is_open:
            try:
                # Parse ISO value (e.g., "800", "1600")
                import re
                match = re.search(r"(\d+)", value)
                if match:
                    iso_value = int(match.group(1))
                    if self.sdk.set_iso(iso_value):
                        return  # Success!
                    print("    [DEBUG] SDK ISO failed, trying coordinate method")
            except Exception as e:
                print(f"    [DEBUG] SDK ISO error: {e}, trying coordinate method")

        # Fallback to coordinate-based method
        if not self.main_window:
            raise Exception("Main window not connected")

        handle = self.main_window.NativeWindowHandle
        SetForegroundWindow(handle)
        time.sleep(0.2)

        # Get position from calibration
        if CONTROLS_AVAILABLE:
            pos = get_control_position(self.main_window, "iso")
            if pos:
                control_x, control_y = pos
            else:
                rect = self.main_window.BoundingRectangle
                control_x = rect.left + int(rect.width() * 0.631)
                control_y = rect.top + int(rect.height() * 0.266)
        else:
            rect = self.main_window.BoundingRectangle
            control_x = rect.left + int(rect.width() * 0.631)
            control_y = rect.top + int(rect.height() * 0.266)

        print(f"    [DEBUG] Clicking ISO control at ({control_x}, {control_y})")
        Click(control_x, control_y)
        time.sleep(0.3)

        # Navigate dropdown using arrow keys and select value
        self._select_dropdown_value("iso", value)

    def _set_white_balance(self, value: str):
        """
        Set white balance using SDK (if available) or coordinate-based fallback.
        """
        # Try SDK first
        if self.sdk and self.sdk.is_open:
            try:
                # Map common WB names to SDK constants
                from lumix_sdk import (
                    LMX_DEF_WB_AUTO, LMX_DEF_WB_DAYLIGHT, LMX_DEF_WB_CLOUD,
                    LMX_DEF_WB_SHADE, LMX_DEF_WB_TENGSTEN, LMX_DEF_WB_FLASH,
                )

                wb_map = {
                    "auto": LMX_DEF_WB_AUTO,
                    "awb": LMX_DEF_WB_AUTO,
                    "daylight": LMX_DEF_WB_DAYLIGHT,
                    "cloud": LMX_DEF_WB_CLOUD,
                    "cloudy": LMX_DEF_WB_CLOUD,
                    "shade": LMX_DEF_WB_SHADE,
                    "incandescent": LMX_DEF_WB_TENGSTEN,
                    "tungsten": LMX_DEF_WB_TENGSTEN,
                    "flash": LMX_DEF_WB_FLASH,
                }

                value_lower = value.lower().strip()
                if value_lower in wb_map:
                    if self.sdk.set_white_balance(wb_map[value_lower]):
                        return  # Success!
                    print("    [DEBUG] SDK WB failed, trying coordinate method")
            except Exception as e:
                print(f"    [DEBUG] SDK WB error: {e}, trying coordinate method")

        # Fallback to coordinate-based method
        if not self.main_window:
            raise Exception("Main window not connected")

        handle = self.main_window.NativeWindowHandle
        SetForegroundWindow(handle)
        time.sleep(0.2)

        # Get position from calibration
        if CONTROLS_AVAILABLE:
            pos = get_control_position(self.main_window, "wb")
            if pos:
                control_x, control_y = pos
            else:
                rect = self.main_window.BoundingRectangle
                control_x = rect.left + int(rect.width() * 0.377)
                control_y = rect.top + int(rect.height() * 0.266)
        else:
            rect = self.main_window.BoundingRectangle
            control_x = rect.left + int(rect.width() * 0.377)
            control_y = rect.top + int(rect.height() * 0.266)

        print(f"    [DEBUG] Clicking WB control at ({control_x}, {control_y})")
        Click(control_x, control_y)
        time.sleep(0.3)

        # Navigate dropdown using arrow keys and select value
        self._select_dropdown_value("wb", value)

    def _select_dropdown_value(self, setting_type: str, target_value: str):
        """
        Select a value from a dropdown using arrow keys.

        This is a simplified version that assumes:
        1. The dropdown is already open
        2. Values are in a predictable order
        3. We use arrow keys to navigate and Enter to select

        For production use, this would need to know the exact dropdown
        options and their order for each setting type.
        """
        import ctypes

        # Virtual key codes
        VK_DOWN = 0x28
        VK_UP = 0x26
        VK_HOME = 0x24
        VK_END = 0x23
        VK_RETURN = 0x0D

        # Common aperture values in order (for Panasonic GH5)
        aperture_values = ["f/1.7", "f/2.0", "f/2.8", "f/4.0", "f/5.6", "f/8.0", "f/11", "f/16"]
        iso_values = ["100", "200", "400", "800", "1600", "3200", "6400"]
        wb_values = ["AWB", "Daylight", "Cloudy", "Shade", "Incandescent", "Flash"]

        # Get the value list for this setting type
        if setting_type == "aperture":
            values = aperture_values
        elif setting_type == "iso":
            values = iso_values
        elif setting_type == "wb":
            values = wb_values
        else:
            print(f"    [DEBUG] Unknown setting type: {setting_type}")
            return

        # Normalize target value (handle f/2.8 vs 2.8, etc.)
        target_normalized = target_value.lower().replace("f/", "").replace(".", "").strip()

        # Find the target value in the list
        target_index = -1
        for i, val in enumerate(values):
            val_normalized = val.lower().replace("f/", "").replace(".", "").strip()
            if val_normalized == target_normalized or val.lower() == target_value.lower():
                target_index = i
                break

        if target_index == -1:
            print(f"    [DEBUG] Value '{target_value}' not found in dropdown options")
            return

        # Go to top of dropdown first
        ctypes.windll.user32.keybd_event(VK_HOME, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(VK_HOME, 0, 2, 0)
        time.sleep(0.1)

        # Arrow down to the target position
        for _ in range(target_index):
            ctypes.windll.user32.keybd_event(VK_DOWN, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_DOWN, 0, 2, 0)
            time.sleep(0.05)

        # Press Enter to select
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(VK_RETURN, 0, 2, 0)
        time.sleep(0.2)


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
