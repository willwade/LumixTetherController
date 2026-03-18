@echo off
REM Demo script for Agentic Camera Control
REM This demonstrates the LLM-powered camera control features

echo ====================================
echo LUMIX Tether - Agentic Mode Demo
echo ====================================
echo.

REM Check if API key is set
if "%OPENAI_API_KEY%"=="" (
    echo Error: OPENAI_API_KEY environment variable not set
    echo.
    echo Please set it first:
    echo   set OPENAI_API_KEY=your-api-key-here
    echo.
    exit /b 1
)

echo OpenAI API key is configured
echo.

REM Test 1: Simple scene analysis
echo [Test 1] Analyzing current scene...
uv run main.py main --ai "Describe what you see in the camera view"
echo.

pause

REM Test 2: Portrait mode
echo [Test 2] Portrait mode setup...
uv run main.py main --ai "Set up for a portrait photo with blurry background"
echo.

pause

REM Test 3: Focus on subject
echo [Test 3] Intelligent focus...
uv run main.py main --ai "Focus on the main subject in the frame"
echo.

pause

REM Test 4: Low light scene
echo [Test 4] Low light optimization...
uv run main.py main --ai "The scene is too dark, adjust camera settings for better exposure"
echo.

pause

echo.
echo ====================================
echo Demo Complete!
echo ====================================
echo.
echo Try your own prompts:
echo   uv run main.py main --ai "your prompt here"
echo.
