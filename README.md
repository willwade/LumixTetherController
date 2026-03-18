# LUMIX Tether Bridge (Grid 3 & AI Edition)

An automation bridge that allows **Grid 3** (AAC software) and **Large Language Models** to control the Panasonic GH5M2 via the LUMIX Tether desktop application.

This tool uses the **Windows-Use** framework to interact with the UI automation tree, providing a reliable CLI interface where standard keyboard shortcuts are missing.

## Features

- **Deterministic Actions**: High-speed, reliable camera control without LLM involvement
- **Window Management**: Arrange LUMIX Tether windows into predictable layouts
- **Grid 3 Integration**: CLI designed for "Run Program" cells
- **Agentic Mode**: Vision LLM-powered intelligent camera control with GPT-4o

## Requirements

- **OS**: Windows 10/11 (UI Automation requires Windows)
- **Software**: LUMIX Tether installed and connected to a GH5M2
- **Python**: 3.11+ managed by `uv`
- **API Key**: OpenAI API key for agentic mode (optional)

## Quick Start

### 1. Install `uv`

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the CLI

```bash
uv run main.py --help
```

## CLI Parameters

### Deterministic Actions (`--action`)

Use these for high-speed, reliable tasks. No LLM is involved.

| Parameter | Description |
| :--- | :--- |
| `shutter` | Clicks the physical shutter button in the Recording Panel. |
| `record` | Toggles motion picture recording. |
| `lv-on` | Ensures the Live View window is open. |
| `af-on` | Triggers Touch AF by clicking the center of Live View. |

**Examples:**
```bash
uv run main.py --action shutter
uv run main.py --action af-on
```

### Window Management (`--layout`)

Arranges the scattered LUMIX Tether windows into a predictable grid for the user.

| Value | Description |
| :--- | :--- |
| `grid` | Snaps Recording Panel, Live View, and Preview into a 3-column layout (50% / 25% / 25%). |
| `focus` | Maximizes Live View and moves the control panel to a 300px sidebar. |

**Example:**
```bash
uv run main.py --layout grid
```

### Agentic Mode (`--ai`) - NEW!

Uses GPT-4o Vision to analyze your camera view and intelligently control settings.

**Setup:**
```bash
# Set your OpenAI API key
set OPENAI_API_KEY=sk-your-key-here

# Or export it for the current session
export OPENAI_API_KEY=sk-your-key-here
```

**Examples:**
```bash
# Scene analysis and recommendations
uv run main.py --ai "Describe what you see in the camera view"

# Portrait mode with intelligent settings
uv run main.py --ai "Take a portrait photo with blurry background"

# Intelligent focus on subject
uv run main.py --ai "Focus on the person's face in the frame"

# Low light optimization
uv run main.py --ai "The scene is too dark, adjust exposure settings"

# Multi-step workflow
uv run main.py --ai "Set up for a landscape photo with deep depth of field, focus on the horizon, then take the shot"
```

**What the AI Can Do:**

- **Scene Analysis**: Describe what's in the frame (people, landscapes, objects)
- **Camera Settings**: Suggest optimal aperture, ISO, shutter speed
- **Focus Control**: Automatically focus on specific subjects using Touch AF coordinates
- **Photography Techniques**: Portrait mode, landscape optimization, low light adjustments
- **Multi-Step Workflows**: Combine multiple actions (setup → focus → capture)

## Agentic Mode Capabilities

### 1. Natural Language Camera Control

```
"Take a portrait photo with blurry background"
"Focus on the person's face and lower the aperture"
"The scene is too dark, fix the exposure"
"Switch to video mode and start recording when ready"
```

### 2. Scene-Aware Photography

- **Portrait Mode**: Detect faces, suggest wide aperture (f/2.8), focus on eyes
- **Landscape Mode**: Recommend narrow aperture (f/8-f/11) for deep depth of field
- **Low Light**: Increase ISO, slower shutter, suggest tripod use
- **Action Photography**: Fast shutter speed, continuous autofocus
- **Product Photography**: Clean backgrounds, optimal lighting suggestions

### 3. Smart Workflows

```bash
# HDR Bracketing
uv run main.py --ai "Take 3 bracketed exposures for HDR (-1, 0, +1 EV)"

# Focus Stacking
uv run main.py --ai "Set up for focus stacking - take 5 photos from near to far focus"

# Time Lapse Setup
uv run main.py --ai "Configure for a time lapse: 1 photo every 10 seconds for 5 minutes"

# Event Photography
uv run main.py --ai "Set up for event photography - fast shutter, continuous focus, fill the frame"
```

### 4. Accessibility Features

- **Voice Control**: Use with speech-to-text for hands-free operation
- **Simplified Commands**: Natural language instead of technical settings
- **Grid 3 Integration**: Accessible camera control for AAC users

## Development

### Linting

This project uses [ruff](https://docs.astral.sh/ruff/) for fast Python linting and formatting.

**Check code:**
```bash
uv run ruff check main.py
```

**Format code:**
```bash
uv run ruff format main.py
```

**Auto-fix issues:**
```bash
uv run ruff check --fix main.py
```

### UI Inspection Tools

Several inspection scripts are included to help understand the LUMIX Tether UI:

```bash
# List all windows and find LUMIX Tether
uv run inspect_all_windows.py

# Inspect main window structure
uv run inspect_main.py

# Capture and annotate screenshots
uv run visual_inspect.py
```

### Building Windows Executable

To create a standalone Windows executable:

```bash
uv run build.bat
```

Or manually:
```bash
uv run pyinstaller --onefile --name lumix-tether --clean --noconfirm main.py
```

### Demo Script

Try the agentic mode demo:
```bash
# Windows
demo_agentic.bat

# Or manually
set OPENAI_API_KEY=your-key
uv run main.py --ai "Describe the scene"
```

## Grid 3 Integration Guide

### Deterministic Commands

For Grid 3 "Run Program" cells:

1. **Program:** `C:\path\to\dist\lumix-tether.exe`
2. **Arguments:** `--action shutter`

### Agentic Commands

For AI-powered control (requires API key configuration):

1. **Program:** `C:\path\to\dist\lumix-tether.exe`
2. **Arguments:** `--ai "Take a portrait photo"`

> **Note:** For agentic mode, you'll need to set the `OPENAI_API_KEY` environment variable before launching Grid 3, or bundle it with your application.

### Environment Variable Setup

Create a batch file to set environment variables and launch the app:

```batch
@echo off
set OPENAI_API_KEY=sk-your-key-here
dist\lumix-tether.exe %*
```

Save as `lumix-launcher.bat` and use this in Grid 3 instead of the direct executable.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Grid 3 / CLI                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   main.py (CLI Layer)                       │
│  - Click-based CLI                                          │
│  - Argument validation                                      │
│  - Window detection                                         │
└──────┬──────────────────────────────────────┬──────────────┘
       │                              │
       ▼                              ▼
┌─────────────────────┐    ┌─────────────────────────────────┐
│  Windows-Use        │    │  Agentic Mode (CameraAgent)    │
│  - UI Automation     │    │  - Screenshot capture          │
│  - Window mgmt        │    │  - GPT-4o Vision API           │
│  - Click simulation  │    │  - Scene analysis              │
└──────────┬───────────┘    │  - Action execution            │
           │                └──────────────┬────────────────┘
           │                               │
           ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                LUMIX Tether Application                     │
│  - Recording Panel (1: DC-GH5)                              │
│  - Live View window                                         │
│  - Preview window                                            │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### "LUMIX Tether application not found"

- Ensure LUMIX Tether is running before executing commands
- Check that the window title matches "1: DC-GH5" (may vary by model)

### "OPENAI_API_KEY environment variable not set"

- Set the API key: `set OPENAI_API_KEY=sk-your-key-here` (Windows)
- Or export: `export OPENAI_API_KEY=sk-your-key-here` (Linux/Mac)
- Get your API key from: https://platform.openai.com/api-keys

### "Could not find shutter button"

- The coordinate-based approach is used since Qt/QML UI doesn't expose standard controls
- Ensure LUMIX Tether is the active window
- The tool clicks at the top-center of the main window (adjust if your UI differs)

### Window layout doesn't work

- Ensure all LUMIX Tether windows are open (Recording Panel, Live View, Preview)
- The tool searches for windows by title - ensure your window titles match
- Try running `uv run inspect_all_windows.py` to see detected windows

### Agentic mode suggestions don't execute

- The AI provides recommendations but may not always suggest executable actions
- Try more specific prompts like "focus on the center and take a photo"
- Check that your API key has access to GPT-4o (not all API keys have vision access)

## Example Use Cases

### Portrait Photography

```bash
# Set up for portraits and capture
uv run main.py --layout focus
uv run main.py --ai "Configure for a portrait session with blurry background"
uv run main.py --ai "Focus on the subject's face and take the photo"
```

### Event Photography

```bash
# Fast shutter, continuous operation
uv run main.py --ai "Set up for event photography - fast shutter speed to freeze motion"
uv run main.py --action shutter  # Quick capture when needed
```

### Product Photography

```bash
# Clean, consistent product shots
uv run main.py --layout grid  # Clean workspace view
uv run main.py --ai "Analyze the lighting and suggest product photography settings"
```

### Accessibility / AAC

```bash
# Simple voice commands (via speech-to-text)
uv run main.py --ai "take a photo"
uv run main.py --ai "zoom in on the subject"
uv run main.py --ai "make the background blurry"
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Run the linter before committing: `uv run ruff check --fix main.py`
2. Test with LUMIX Tether running
3. Document any new features

## Credits

- Built with [windows-use](https://github.com/amir20/dothings) - Windows UI Automation framework
- Uses [Python-UIAutomation-for-Windows](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)
- Dependency management with [uv](https://github.com/astral-sh/uv)
- AI powered by [OpenAI GPT-4o](https://openai.com/gpt-4o)
