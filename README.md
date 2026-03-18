# LUMIX Tether Bridge (Grid 3 & AI Edition)

An automation bridge that allows **Grid 3** (AAC software) and **Large Language Models** to control the Panasonic GH5M2 via the LUMIX Tether desktop application.

This tool uses the **Windows-Use** framework to interact with the UI automation tree, providing a reliable CLI interface where standard keyboard shortcuts are missing.

## Features

- **Deterministic Actions**: High-speed, reliable camera control without LLM involvement
- **Window Management**: Arrange LUMIX Tether windows into predictable layouts
- **Grid 3 Integration**: CLI designed for "Run Program" cells
- **Agentic Mode**: Vision LLM-powered camera control (coming soon)

## Requirements

- **OS**: Windows 10/11 (UI Automation requires Windows)
- **Software**: LUMIX Tether installed and connected to a GH5M2
- **Python**: 3.11+ managed by `uv`

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
| `af-on` | Triggers the "Half-press shutter" to lock focus. |

**Example:**
```bash
uv run main.py --action shutter
```

### Window Management (`--layout`)

Arranges the scattered LUMIX Tether windows into a predictable grid for the user.

| Value | Description |
| :--- | :--- |
| `grid` | Snaps Recording Panel, Live View, and Toolbox into a 3-column layout. |
| `focus` | Maximizes Live View and moves the control panel to a side-bar. |

**Example:**
```bash
uv run main.py --layout grid
```

### Agentic Mode (`--ai`)

Passes a natural language string and a screenshot of the Live View to a Vision LLM.

| Parameter | Description |
| :--- | :--- |
| `--ai "prompt"` | Uses an LLM to find subjects in the frame and adjust settings. |

**Example:**
```bash
uv run main.py --ai "Focus on the person's face and lower the aperture for a blurry background"
```

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

### Building Windows Executable

To create a standalone Windows executable:

```bash
uv run build.bat
```

This will:
1. Run ruff to check code quality
2. Build the executable using PyInstaller
3. Output the executable to `dist/lumix-tether.exe`

## Grid 3 Integration Guide

To use this in Grid 3:

1. Create a new **Command** cell.
2. Select **Run Program**.
3. **Program:** `C:\path\to\uv.exe`
4. **Arguments:** `run --project C:\path\to\repo main.py --action shutter`

> **Note:** To prevent the command prompt window from flashing, use the standalone executable (`lumix-tether.exe`) or wrap the command in a VBScript.

### Using Standalone Executable

After building, use the executable directly:

1. **Program:** `C:\path\to\dist\lumix-tether.exe`
2. **Arguments:** `--action shutter`

## How Agentic Mode Works

When using the `--ai` flag, the tool performs the following:

1. **State Capture**: Captures the UI tree (Aperture, ISO, SS) and a screenshot of the `Live View` window
2. **Vision Analysis**: Sends the data to a Vision LLM (e.g., GPT-4o or Claude 3.5 Sonnet)
3. **UI Interaction**: The LLM returns specific coordinates or menu items. The tool then uses `Windows-Use` to:
   - Click the Live View window at `(x, y)` to set **Touch AF**
   - Iterate through the Aperture dropdown to select the target f-stop

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
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Windows-Use (UI Automation)                    │
│  - Control finding and interaction                          │
│  - Window management                                        │
│  - Mouse/keyboard simulation                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                LUMIX Tether Application                     │
│  - Recording Panel                                          │
│  - Live View window                                         │
│  - Toolbox                                                  │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### "LUMIX Tether application not found"

- Ensure LUMIX Tether is running before executing commands
- Check that the window title matches one of the patterns in `find_lumix_tether_window()`

### "Could not find shutter button"

- The UI automation IDs may vary between LUMIX Tether versions
- Use a UI inspection tool (e.g., Accessibility Insights for Windows) to find the correct automation IDs
- The coordinate-based fallback may work in some cases

### Window layout doesn't work

- Ensure all LUMIX Tether windows are open (Recording Panel, Live View, Toolbox)
- The tool searches for windows by title patterns - ensure your window titles match

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
