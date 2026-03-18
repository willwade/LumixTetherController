@echo off
REM Build script for LUMIX Tether Bridge Windows executable

echo ====================================
echo LUMIX Tether Bridge Build Script
echo ====================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: uv is not installed or not in PATH
    echo Please install uv from: https://github.com/astral-sh/uv
    exit /b 1
)

REM Run ruff to check code quality
echo [1/3] Running ruff linting...
uv run ruff check main.py
if %errorlevel% neq 0 (
    echo ERROR: Ruff check failed. Please fix linting issues before building.
    exit /b 1
)
echo Ruff check passed!
echo.

REM Run ruff format check
echo [2/3] Running ruff format check...
uv run ruff format --check main.py
if %errorlevel% neq 0 (
    echo WARNING: Code formatting issues detected. Running auto-format...
    uv run ruff format main.py
)
echo Format check passed!
echo.

REM Build executable with PyInstaller
echo [3/3] Building Windows executable...
uv run pyinstaller --onefile --name lumix-tether --clean --noconfirm main.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

echo.
echo ====================================
echo Build completed successfully!
echo ====================================
echo.
echo Executable location: dist\lumix-tether.exe
echo.
echo You can now use lumix-tether.exe directly in Grid 3 or from command line.
echo Example: dist\lumix-tether.exe --action shutter
echo.
