"""
Three.js Video Generator with QA Feedback Loop

Generates Three.js animated visualizations and exports them as videos
matching the pipeline specs (1080p, 24fps, MP4)
"""

import os
import base64
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import json

try:
    import google.generativeai as genai
except ImportError:
    print("Error: google-generativeai not installed. Run: pip install google-generativeai")
    exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: pip install playwright && playwright install")
    exit(1)


def safe_print(*args, **kwargs):
    """Safely print messages, handling closed file errors"""
    try:
        print(*args, **kwargs)
    except (IOError, OSError, ValueError):
        pass


class ThreeJSVideoGenerator:
    """Generate Three.js animations and export as video files"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3-pro-preview",
        width: int = 1920,
        height: int = 1080,
        fps: int = 24
    ):
        """
        Initialize the generator

        Args:
            api_key: Gemini API key
            model_name: Gemini model to use
            width: Video width in pixels (default: 1920)
            height: Video height in pixels (default: 1080)
            fps: Frames per second (default: 24)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable"
            )

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

        # Video specs
        self.width = width
        self.height = height
        self.fps = fps

        # Output directory
        self.output_dir = Path("temp/threejs_videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_initial_code(self, prompt: str, duration: float) -> str:
        """
        Generate initial Three.js code with animation

        Args:
            prompt: Description of the desired 3D animated scene
            duration: Duration in seconds

        Returns:
            Complete HTML file with embedded Three.js code
        """
        system_prompt = f"""You are an expert Three.js developer creating ANIMATED visualizations. Generate a complete, self-contained HTML file
with embedded Three.js code based on the user's description. The code should:

1. Include Three.js from CDN (use importmap with 'three' module)
2. Create a full-screen canvas with proper responsive sizing
3. Include proper camera, renderer, and scene setup
4. Add appropriate lighting for the scene
5. CREATE A SMOOTH ANIMATION that lasts approximately {duration} seconds
6. Use requestAnimationFrame for the animation loop
7. Include camera movements, object rotations, or transitions as appropriate
8. Make the animation loop seamlessly or have a clear beginning/end
9. Use modern Three.js patterns (ES6+ modules from CDN)
10. Include clear comments

CRITICAL REQUIREMENTS FOR ANIMATION:
- The animation should be SMOOTH and CONTINUOUS
- Use time-based animation (performance.now() or similar) for consistency
- Camera movements should be smooth and purposeful
- Include easing functions for natural motion
- The scene should be visually engaging throughout the duration

VISUAL QUALITY:
- Use appropriate materials (MeshStandardMaterial, MeshPhysicalMaterial)
- Add proper lighting (ambient + directional/point lights)
- Consider using shadows if appropriate
- Use colors that create visual contrast
- Add depth and perspective

Return ONLY the complete HTML code, no explanations. The HTML should be production-ready and visually stunning.
"""

        response = self.model.generate_content(
            f"{system_prompt}\n\nUser request: {prompt}\nDuration: {duration} seconds"
        )

        code = response.text.strip()

        # Extract code from markdown code blocks if present
        if "```html" in code:
            code = code.split("```html")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        return code

    def render_preview_screenshot(self, html_code: str, scene_number: int, wait_time: float = 3.0) -> Path:
        """
        Render a single preview screenshot for QA feedback

        Args:
            html_code: HTML code to render
            scene_number: Scene number for naming
            wait_time: Time to wait before screenshot (seconds)

        Returns:
            Path to screenshot file
        """
        # Save HTML file
        html_path = self.output_dir / f"scene_{scene_number}_preview.html"
        with open(html_path, 'w') as f:
            f.write(html_code)

        # Capture screenshot using Playwright
        screenshot_path = self.output_dir / f"scene_{scene_number}_preview.png"

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": self.width, "height": self.height})

            # Load the HTML file
            page.goto(f"file://{html_path.absolute()}")

            # Wait for Three.js to initialize and render
            time.sleep(wait_time)

            # Take screenshot
            page.screenshot(path=screenshot_path)
            browser.close()

        safe_print(f"    📸 Preview screenshot saved: {screenshot_path.name}")
        return screenshot_path

    def render_preview_screenshots_multiframe(
        self,
        html_code: str,
        scene_number: int,
        duration: float,
        iteration: int = 0
    ) -> list[Path]:
        """
        Render multiple preview screenshots at different time points (start, middle, end)
        to catch timing and animation speed issues

        Args:
            html_code: HTML code to render
            scene_number: Scene number for naming
            duration: Total animation duration in seconds
            iteration: Current iteration number for naming

        Returns:
            List of paths to screenshot files [start, middle, end]
        """
        # Save HTML file
        html_path = self.output_dir / f"scene_{scene_number}_preview_iter{iteration}.html"
        with open(html_path, 'w') as f:
            f.write(html_code)

        # Calculate time points: start (1s for init), middle, end
        # Add 1 second buffer for WebGL initialization
        time_points = [
            ("start", 1.0),  # Just after initialization
            ("middle", 1.0 + duration / 2),  # Middle of animation
            ("end", 1.0 + duration * 0.9)  # Near end (90% through)
        ]

        screenshot_paths = []

        safe_print(f"    📸 Capturing {len(time_points)} preview screenshots (start/middle/end)...")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": self.width, "height": self.height})

            # Load the HTML file
            page.goto(f"file://{html_path.absolute()}")

            for label, wait_time in time_points:
                # Wait until the desired time point
                time.sleep(wait_time if label == "start" else (wait_time - sum(t for _, t in time_points[:time_points.index((label, wait_time))])))

                # Take screenshot
                screenshot_path = self.output_dir / f"scene_{scene_number}_preview_{label}_iter{iteration}.png"
                page.screenshot(path=screenshot_path)
                screenshot_paths.append(screenshot_path)
                safe_print(f"       ✓ {label.capitalize()} frame captured ({wait_time:.1f}s)")

            browser.close()

        return screenshot_paths

    def analyze_screenshot(self, screenshot_path: Path, original_prompt: str) -> Dict[str, Any]:
        """
        Analyze screenshot against original intent and provide feedback

        Args:
            screenshot_path: Path to screenshot
            original_prompt: Original user prompt

        Returns:
            Dict with 'satisfactory' bool and 'feedback' string
        """
        # Read and encode screenshot
        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        analysis_prompt = f"""You are a QA engineer reviewing a Three.js animated visualization for a documentary video.

Original Request: {original_prompt}

The screenshot shows a frame from the animation. Analyze it and determine if it matches the intent. Consider:
1. Does it contain the requested 3D elements?
2. Is the composition visually appealing and clear?
3. Are colors, lighting, and materials appropriate for a documentary?
4. Does it look professional and polished?
5. Will it effectively communicate the concept when animated?

Respond in JSON format:
{{
    "satisfactory": true/false,
    "feedback": "Detailed feedback on what's good and what needs improvement",
    "suggestions": "Specific code changes needed (if not satisfactory)"
}}
"""

        # Create message with image
        response = self.model.generate_content([
            analysis_prompt,
            {
                "mime_type": "image/png",
                "data": image_data
            }
        ])

        result_text = response.text.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            result = {
                "satisfactory": False,
                "feedback": result_text,
                "suggestions": "Unable to parse structured feedback"
            }

        return result

    def analyze_screenshots_multiframe(
        self,
        screenshot_paths: list[Path],
        original_prompt: str,
        duration: float
    ) -> Dict[str, Any]:
        """
        Analyze multiple screenshots (start/middle/end) to check animation timing and progression

        Args:
            screenshot_paths: List of paths to screenshots [start, middle, end]
            original_prompt: Original user prompt
            duration: Expected duration in seconds

        Returns:
            Dict with 'satisfactory' bool and 'feedback' string
        """
        # Read and encode all screenshots
        images = []
        for i, path in enumerate(screenshot_paths):
            with open(path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                images.append({
                    "mime_type": "image/png",
                    "data": image_data
                })

        labels = ["START", "MIDDLE", "END"]

        analysis_prompt = f"""You are a QA engineer reviewing a Three.js animated visualization for a documentary video.

Original Request: {original_prompt}
Expected Duration: {duration} seconds

You are shown THREE screenshots taken at different time points:
1. START - Beginning of the animation (after initialization)
2. MIDDLE - Halfway through the animation
3. END - Near the end of the animation (90% complete)

Analyze these screenshots and determine if the animation progression is appropriate. CRITICAL CHECKS:

TIMING & PACING:
- Is the animation progressing at a reasonable pace?
- Does it appear to be running too fast or too slow?
- Are transitions smooth and gradual between frames?
- Is the camera movement/zoom speed appropriate?

VISUAL PROGRESSION:
- Does each frame show clear progression from start to end?
- Are the 3D elements, camera angles, and positions changing appropriately?
- Does the animation tell a clear visual story across these frames?

QUALITY:
- Are colors, lighting, and materials consistent and appropriate?
- Does it look professional throughout?
- Are all requested 3D elements visible and well-composed?

**IMPORTANT**: If the animation appears to complete too quickly (e.g., major changes between start and middle, but little change between middle and end), flag it as TOO FAST.
If the scenes look nearly identical across all three frames, it may be TOO SLOW or STATIC.

Respond in JSON format:
{{
    "satisfactory": true/false,
    "feedback": "Detailed feedback on timing, pacing, and visual progression",
    "suggestions": "Specific code changes needed to fix timing/animation issues (if not satisfactory)",
    "timing_issues": "Description of any timing/speed problems detected"
}}
"""

        # Create message with all images
        message_parts = [analysis_prompt]
        for i, img in enumerate(images):
            message_parts.append(f"\n--- {labels[i]} FRAME ---")
            message_parts.append(img)

        response = self.model.generate_content(message_parts)
        result_text = response.text.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            result = {
                "satisfactory": False,
                "feedback": result_text,
                "suggestions": "Unable to parse structured feedback",
                "timing_issues": "JSON parsing failed"
            }

        return result

    def refine_code(self, current_code: str, feedback: Dict[str, Any], original_prompt: str, duration: float) -> str:
        """
        Refine code based on feedback

        Args:
            current_code: Current HTML/JS code
            feedback: Feedback from analysis
            original_prompt: Original user prompt
            duration: Duration in seconds

        Returns:
            Refined HTML code
        """
        refinement_prompt = f"""You are refining a Three.js animated visualization based on QA feedback.

Original Request: {original_prompt}
Duration: {duration} seconds

Current Code:
{current_code}

QA Feedback:
{feedback['feedback']}

Suggestions:
{feedback.get('suggestions', 'N/A')}

Generate an improved version of the code that addresses the feedback.
Maintain the animation duration and smoothness.
Return ONLY the complete updated HTML code, no explanations.
"""

        response = self.model.generate_content(refinement_prompt)
        code = response.text.strip()

        # Extract code from markdown code blocks if present
        if "```html" in code:
            code = code.split("```html")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        return code

    def capture_frame_sequence(self, html_code: str, duration: float, scene_number: int) -> Path:
        """
        Capture a sequence of frames from the animation

        Args:
            html_code: HTML code to render
            duration: Duration in seconds
            scene_number: Scene number for naming

        Returns:
            Path to directory containing frames
        """
        # Calculate total frames
        total_frames = int(duration * self.fps)

        # Create frames directory
        frames_dir = self.output_dir / f"scene_{scene_number}_frames"
        frames_dir.mkdir(exist_ok=True)

        safe_print(f"    🎞️  Capturing {total_frames} frames at {self.fps}fps...")

        # Save HTML file
        html_path = self.output_dir / f"scene_{scene_number}_final.html"
        with open(html_path, 'w') as f:
            f.write(html_code)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": self.width, "height": self.height})

            # Load the HTML file
            page.goto(f"file://{html_path.absolute()}")

            # Wait for Three.js to initialize
            time.sleep(2)

            # Capture frames
            frame_time = 1.0 / self.fps  # Time between frames in seconds

            for frame_num in range(total_frames):
                # Take screenshot
                frame_path = frames_dir / f"frame_{frame_num:04d}.png"
                page.screenshot(path=frame_path)

                # Wait for next frame
                time.sleep(frame_time)

                # Progress indicator every 10 frames
                if (frame_num + 1) % 10 == 0 or frame_num == total_frames - 1:
                    safe_print(f"       Captured {frame_num + 1}/{total_frames} frames...")

            browser.close()

        safe_print(f"    ✅ All {total_frames} frames captured")
        return frames_dir

    def convert_frames_to_video(self, frames_dir: Path, output_path: Path) -> bool:
        """
        Convert frame sequence to MP4 video using FFmpeg

        Args:
            frames_dir: Directory containing frame_XXXX.png files
            output_path: Output video path

        Returns:
            True if successful
        """
        safe_print(f"    🎬 Converting frames to video...")

        # FFmpeg command to create video from frames
        # Match Seedance specs: 1080p, 24fps, H.264, yuv420p
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-framerate", str(self.fps),
            "-i", str(frames_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",  # High quality (lower = better, 18 is visually lossless)
            "-preset", "medium",
            "-vf", f"scale={self.width}:{self.height}",
            str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            safe_print(f"    ✅ Video created: {output_path.name}")
            return True
        except subprocess.CalledProcessError as e:
            safe_print(f"    ❌ FFmpeg error: {e.stderr}")
            return False

    def generate_video_with_feedback(
        self,
        description: str,
        duration: float,
        scene_number: int,
        output_dir: Optional[Path] = None,
        max_iterations: int = 5
    ) -> str:
        """
        Generate a Three.js video with QA feedback loop

        Args:
            description: Visual description of the scene
            duration: Duration in seconds
            scene_number: Scene number
            output_dir: Output directory for final video (default: temp/threejs_videos)
            max_iterations: Maximum refinement iterations

        Returns:
            Path to generated video file
        """
        output_dir = output_dir or self.output_dir
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        safe_print(f"    🎨 Generating Three.js animation: '{description[:50]}...'")

        # Generate initial code
        current_code = self.generate_initial_code(description, duration)

        # Feedback loop with multi-frame preview (start/middle/end screenshots)
        for iteration in range(max_iterations):
            safe_print(f"    🔄 QA Iteration {iteration + 1}/{max_iterations}")

            # Render preview screenshots at multiple time points
            screenshot_paths = self.render_preview_screenshots_multiframe(
                current_code, scene_number, duration, iteration
            )

            # Analyze screenshots for timing and progression issues
            safe_print("       🔍 Analyzing animation timing and progression...")
            analysis = self.analyze_screenshots_multiframe(screenshot_paths, description, duration)

            # Show feedback with timing issues if present
            feedback_msg = analysis['feedback'][:80]
            if 'timing_issues' in analysis and analysis['timing_issues']:
                feedback_msg += f" | Timing: {analysis['timing_issues'][:40]}"

            safe_print(f"       {'✅' if analysis['satisfactory'] else '❌'} {feedback_msg}...")

            if analysis['satisfactory']:
                safe_print(f"    ✅ QA approved in {iteration + 1} iteration(s)")
                break

            if iteration < max_iterations - 1:
                # Refine code based on feedback
                safe_print("       🔧 Refining code to fix timing/animation issues...")
                current_code = self.refine_code(current_code, analysis, description, duration)
            else:
                safe_print(f"    ⚠️  Max iterations reached, proceeding with current version")

        # Capture full frame sequence
        frames_dir = self.capture_frame_sequence(current_code, duration, scene_number)

        # Convert to video
        video_path = output_dir / f"scene_{scene_number}.mp4"
        success = self.convert_frames_to_video(frames_dir, video_path)

        if not success:
            raise RuntimeError(f"Failed to create video for scene {scene_number}")

        return str(video_path)


def main():
    """Test the Three.js video generator"""

    test_description = "Animated cross-section of Earth showing the layers: crust, mantle, outer core, and inner core. Camera slowly rotates around the sphere as it transitions from full sphere to cutaway view, with each layer labeled by color - brown crust, orange mantle, yellow outer core, red inner core."
    test_duration = 6

    safe_print("Three.js Video Generator Test")
    safe_print("=" * 60)
    safe_print(f"Description: {test_description}")
    safe_print(f"Duration: {test_duration}s")
    safe_print(f"Specs: 1920x1080, 24fps, MP4")
    safe_print()

    try:
        generator = ThreeJSVideoGenerator()
        video_path = generator.generate_video_with_feedback(
            description=test_description,
            duration=test_duration,
            scene_number=999,
            max_iterations=3
        )

        safe_print()
        safe_print("=" * 60)
        safe_print("✅ SUCCESS!")
        safe_print(f"Video saved to: {video_path}")
        safe_print("=" * 60)

    except Exception as e:
        safe_print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
