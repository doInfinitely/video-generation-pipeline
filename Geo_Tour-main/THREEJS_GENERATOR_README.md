# Three.js Generator with QA Feedback Loop

This module demonstrates automated Three.js code generation using Google Gemini with a visual quality assurance feedback loop.

## How It Works

1. **Initial Generation**: Gemini generates complete Three.js code based on a text prompt
2. **Rendering**: The code is rendered in a headless browser (Chromium via Playwright)
3. **Screenshot Capture**: A screenshot of the rendered 3D scene is captured
4. **Visual QA**: The screenshot is sent back to Gemini for analysis against the original intent
5. **Iterative Refinement**: If not satisfactory, Gemini refines the code based on visual feedback
6. **Loop**: Steps 2-5 repeat until the output matches the intended behavior (or max iterations reached)

## Setup

### 1. Install Dependencies

Dependencies are already installed if you ran the main requirements.txt:

```bash
venv/bin/pip install google-generativeai playwright
venv/bin/playwright install chromium
```

### 2. Set Up Gemini API Key

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

Set the environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
# or
export GOOGLE_API_KEY="your-api-key-here"
```

Or add it to your `.env` file:

```
GEMINI_API_KEY=your-api-key-here
```

## Usage

### Run the Test Script

```bash
venv/bin/python threejs_generator_test.py
```

The script will:
- Prompt you to select or enter a 3D scene description
- Generate Three.js code iteratively with visual feedback
- Save HTML files and screenshots to `temp/threejs_tests/`
- Display progress and feedback for each iteration

### Example Prompts

- "A rotating blue cube with golden edges on a dark background"
- "A solar system with the sun and 3 planets orbiting around it"
- "An abstract particle system with colorful particles floating in space"
- "A 3D Earth globe with realistic textures rotating slowly"

### Output

The script generates:
- `iteration_N.html` - HTML/JS code for each iteration
- `screenshot_N.png` - Screenshot of each iteration
- `final_output.html` - Final approved version

## Integration with Video Pipeline

This feedback loop will be integrated into the main video generation pipeline to enable a new video type:

### Planned Integration

```python
from threejs_generator import ThreeJSGenerator

# In video_generator.py or new threejs_video_generator.py
class ThreeJSVideoGenerator:
    def __init__(self):
        self.generator = ThreeJSGenerator()

    def generate_clip(self, scene_description, duration):
        # Generate Three.js code with QA feedback
        result = self.generator.generate_with_feedback_loop(
            prompt=scene_description,
            max_iterations=3
        )

        # Render to video frames (using headless browser)
        # frames = self.render_to_frames(result['final_code'], duration)

        # Assemble frames into video
        # video_path = self.frames_to_video(frames)

        return video_path
```

### Next Steps for Integration

1. Add frame-by-frame rendering capability (capture animation frames)
2. Convert frames to video using FFmpeg or similar
3. Add to video type options in the main pipeline
4. Integrate with scene planner for multi-scene 3D content
5. Add camera movement and scene transitions

## Architecture

```
User Prompt
    ↓
Gemini: Generate Three.js Code
    ↓
Playwright: Render in Browser
    ↓
Screenshot Capture
    ↓
Gemini: Analyze Screenshot vs. Intent
    ↓
Satisfactory? ──No──→ Gemini: Refine Code ──→ Loop
    ↓
   Yes
    ↓
Final HTML Output
```

## API Reference

### `ThreeJSGenerator`

Main class for generating and refining Three.js code.

**Methods:**

- `generate_initial_code(prompt: str) -> str`
  - Generates initial HTML/JS code from prompt

- `render_and_screenshot(html_code: str, iteration: int) -> Path`
  - Renders code and captures screenshot

- `analyze_screenshot(screenshot_path: Path, original_prompt: str, current_code: str) -> Dict`
  - Analyzes screenshot against original intent

- `refine_code(current_code: str, feedback: Dict, original_prompt: str) -> str`
  - Refines code based on feedback

- `generate_with_feedback_loop(prompt: str, max_iterations: int = 5) -> Dict`
  - Main method: runs complete generation with QA loop

## Configuration

You can customize the generator:

```python
generator = ThreeJSGenerator(
    api_key="your-key",  # Optional, reads from env
    model_name="gemini-2.0-flash-exp"  # Gemini model to use
)

result = generator.generate_with_feedback_loop(
    prompt="your 3D scene description",
    max_iterations=5  # Maximum refinement iterations
)
```

## Troubleshooting

**Issue**: "Gemini API key required"
- Make sure `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set

**Issue**: "playwright not installed"
- Run: `venv/bin/pip install playwright && venv/bin/playwright install chromium`

**Issue**: Screenshot is black/blank
- The wait time (3 seconds) may be too short for complex scenes
- Increase the sleep time in `render_and_screenshot()` method

**Issue**: Gemini keeps refining without satisfaction
- The prompt may be too vague or ambiguous
- Try more specific prompts with clear visual requirements
- Check the feedback in the iteration history to see what's being requested

## Future Enhancements

- [ ] Add video recording capability (not just screenshots)
- [ ] Support for custom Three.js libraries and shaders
- [ ] Multiple camera angles/views
- [ ] Physics simulation integration
- [ ] Interactive controls in final output
- [ ] Style transfer for consistent art direction
- [ ] Performance optimization analysis
