# LUMIX Tether - Agentic Mode Quick Reference

## What's Possible with LLM + Camera Control

### Natural Language Commands

Simply describe what you want in plain English:

```bash
# Simple commands
uv run main.py --ai "take a photo"
uv run main.py --ai "focus on the person"
uv run main.py --ai "make the background blurry"

# Technical requests
uv run main.py --ai "analyze the exposure and suggest settings"
uv run main.py --ai "what camera mode should I use for this scene?"
```

### Photography Modes

**Portrait Mode**
```bash
uv run main.py --ai "Set up for a portrait with shallow depth of field, focus on eyes"
```
The AI will:
- Analyze the scene to detect people/faces
- Suggest wide aperture (f/1.4-f/2.8) for background blur
- Provide specific focus coordinates for the subject's face
- Execute focus and optionally take the photo

**Landscape Mode**
```bash
uv run main.py --ai "Configure for landscape photography with deep depth of field"
```
The AI will:
- Suggest narrow aperture (f/8-f/16) for everything in focus
- Recommend focus distance for maximum sharpness
- Suggest tripod use for stability

**Low Light/Night**
```bash
uv run main.py --ai "It's too dark in here, optimize for low light"
```
The AI will:
- Suggest higher ISO settings
- Recommend slower shutter speeds
- Advise on tripod usage
- Warn about potential camera shake

### Advanced Workflows

**HDR Photography**
```bash
uv run main.py --ai "Set up for HDR: take 3 bracketed exposures (-2, 0, +2 EV)"
```

**Focus Stacking**
```bash
uv run main.py --ai "Prepare for focus stacking: 5 shots from near to far focus"
```

**Event Photography**
```bash
uv run main.py --ai "Event mode: fast shutter (1/250+), continuous autofocus, ready for action"
```

**Product Photography**
```bash
uv run main.py --ai "Product shot mode: clean background, even lighting, focus on product"
```

### Voice Control Integration

For hands-free operation, combine with speech-to-text:

```python
# voice_control.py (example)
import speech_recognition as sr

def listen_and_execute():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        command = recognizer.recognize_google(audio)

        # Execute the command
        os.system(f"uv run main.py --ai \"{command}\"")
```

Then you can say:
- "take a photo"
- "focus on the person"
- "make it brighter"
- "switch to video mode"

### Grid 3 AAC Integration

For users with limited mobility, natural language commands make camera control accessible:

**Grid 3 Cell Examples:**

1. **Simple Photo Cell**
   - Program: `lumix-launcher.bat`
   - Arguments: `--ai "take a photo"`

2. **Portrait Setup Cell**
   - Program: `lumix-launcher.bat`
   - Arguments: `--ai "set up portrait mode and take the photo when ready"`

3. **Voice Cell (with speech-to-text)**
   - Program: `voice_to_lumix.bat`
   - This would capture voice and convert to command

### Creating a Launcher Batch File

**lumix-launcher.bat:**
```batch
@echo off
REM Set your API key here
set OPENAI_API_KEY=sk-proj-your-actual-key-here

REM Launch the command
uv run main.py %*
```

**Usage in Grid 3:**
- Program: `C:\path\to\lumix-launcher.bat`
- Arguments: `--ai "take a photo of the person in the center"`

### API Key Security

**Important Security Notes:**

1. **Never commit API keys** to version control
2. **Use environment variables** instead of hardcoding
3. **Rotate keys regularly** for production use
4. **Set spending limits** on your OpenAI account

**Setting your API key:**

```batch
# Temporary (current session only)
set OPENAI_API_KEY=sk-proj-b4LKRqTOqt9qHdyKdVWku6LkNk5CUkHq

# Permanent (user environment variable)
setx OPENAI_API_KEY "sk-proj-b4LKRqTOqt9qHdyKdVWku6LkNk5CUkHq"

# For the current project only (create .env file)
echo OPENAI_API_KEY=sk-proj-b4LKRqTOqt9qHdyKdVWku6LkNk5CUkHq > .env
```

### Cost Considerations

**GPT-4o Vision Pricing (approximate):**
- Input: ~$0.005 per image (1280x720)
- Output: ~$0.015 per 1K tokens
- Typical agentic command: ~$0.02-0.05 per use

**To minimize costs:**
1. Use deterministic commands (`--action`, `--layout`) when possible
2. Reserve agentic mode for complex decisions
3. Cache scene analysis and reuse settings

### Testing Without Costs

You can test the basic functionality without API costs:

```bash
# These don't use AI - completely free
uv run main.py --action shutter
uv run main.py --layout grid
uv run main.py --action af-on
```

### Example Sessions

**Session 1: Portrait Photography**
```bash
# 1. Set up workspace
uv run main.py --layout focus

# 2. Get AI recommendations
uv run main.py --ai "I'm taking portraits, what settings should I use?"

# 3. Execute specific AI command
uv run main.py --ai "Focus on the subject's left eye and take a portrait with blurry background"
```

**Session 2: Product Photography**
```bash
# 1. Clean workspace
uv run main.py --layout grid

# 2. Analyze lighting
uv run main.py --ai "Analyze the product lighting and suggest improvements"

# 3. Capture
uv run main.py --ai "Take a product photo with white background and sharp focus"
```

**Session 3: Event Coverage**
```bash
# 1. Quick setup
uv run main.py --ai "Event mode: fast shutter 1/500, ISO 800, continuous autofocus"

# 2. Capture moments as they happen
uv run main.py --action shutter

# 3. Adjust when needed
uv run main.py --ai "It's getting darker, adjust for evening indoor lighting"
```

### Troubleshooting AI Commands

**AI doesn't focus correctly:**
- Try being more specific: "focus on the person's face at center of frame"
- Use relative positions: "focus on the subject in the lower third"
- Manual focus: `uv run main.py --action af-on` (centers on Live View)

**AI suggests but doesn't execute:**
- Add explicit action: "focus on center and take the photo"
- Some suggestions are informational only
- Use combination: first AI analysis, then deterministic commands

**Slow response:**
- Vision analysis takes 2-5 seconds
- Network connectivity affects speed
- Consider using deterministic actions for time-sensitive shots

### Future Enhancements

What's possible with this platform:

- **Face Recognition**: Auto-detect and track faces
- **Smile Detection**: Capture when subjects smile
- **Composition Rules**: Rule of thirds, golden ratio guidance
- **Color Grading**: Suggest white balance adjustments
- **Multi-Camera**: Control multiple GH5M2 cameras simultaneously
- **Live Streaming**: Integrate with streaming platforms
- **Remote Trigger**: Web-based camera trigger via phone
- **Voice Memos**: Attach voice notes to each photo
