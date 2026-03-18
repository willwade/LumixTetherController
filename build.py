#!/usr/bin/env python3
"""
Build script for LUMIX Tether Bridge Windows executable.
Run with: uv run build.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n[{description}]")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"ERROR: {description} failed!")
        return False
    print(f"SUCCESS: {description} completed!")
    return True


def main():
    """Main build process."""
    print("=" * 50)
    print("LUMIX Tether Bridge Build Script")
    print("=" * 50)

    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: uv is not installed or not in PATH")
        print("Please install uv from: https://github.com/astral-sh/uv")
        return 1

    # Step 1: Run ruff linting
    if not run_command(
        ["uv", "run", "ruff", "check", "main.py"],
        "[1/3] Running ruff linting..."
    ):
        print("\nERROR: Ruff check failed. Please fix linting issues before building.")
        return 1

    # Step 2: Run ruff format check
    result = subprocess.run(
        ["uv", "run", "ruff", "format", "--check", "main.py"],
        capture_output=True,
    )
    if result.returncode != 0:
        print("\n[2/3] Running ruff format check...")
        print("WARNING: Code formatting issues detected. Running auto-format...")
        if not run_command(
            ["uv", "run", "ruff", "format", "main.py"],
            "[2/3] Auto-formatting code..."
        ):
            return 1
    else:
        print("\n[2/3] Format check passed!")

    # Step 3: Build executable with PyInstaller
    if not run_command(
        [
            "uv",
            "run",
            "pyinstaller",
            "--onefile",
            "--name",
            "lumix-tether",
            "--clean",
            "--noconfirm",
            "main.py",
        ],
        "[3/3] Building Windows executable...",
    ):
        print("\nERROR: PyInstaller build failed.")
        return 1

    print("\n" + "=" * 50)
    print("Build completed successfully!")
    print("=" * 50)
    print("\nExecutable location: dist/lumix-tether.exe")
    print("\nYou can now use lumix-tether.exe directly in Grid 3 or from command line.")
    print('Example: dist\\lumix-tether.exe --action shutter')

    return 0


if __name__ == "__main__":
    sys.exit(main())
