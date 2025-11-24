"""
Three.js Code Generator with QA Feedback Loop

This script demonstrates generating Three.js code using Google Gemini and iteratively
improving it based on screenshot feedback until the output matches the intended behavior.
"""

import os
import base64
import time
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


class ThreeJSGenerator:
    """Generate and refine Three.js code using Gemini with visual feedback"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3-pro-preview"):
        """Initialize the generator with Gemini API"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable"
            )

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.output_dir = Path("temp/threejs_tests")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_initial_code(self, prompt: str) -> str:
        """
        Generate initial Three.js code from a prompt

        Args:
            prompt: Description of the desired 3D scene

        Returns:
            Complete HTML file with embedded Three.js code
        """
        system_prompt = """You are an expert Three.js developer. Generate a complete, self-contained HTML file
with embedded Three.js code based on the user's description. The code should:

1. Include Three.js from CDN
2. Create a full-screen canvas with proper responsive sizing
3. Include proper camera, renderer, and scene setup
4. Add appropriate lighting
5. Implement animation loop if needed
6. Use modern Three.js patterns (ES6+ modules from CDN)
7. Include clear comments

Return ONLY the complete HTML code, no explanations. The HTML should be production-ready and visually appealing.
"""

        response = self.model.generate_content(
            f"{system_prompt}\n\nUser request: {prompt}"
        )

        code = response.text.strip()

        # Extract code from markdown code blocks if present
        if "```html" in code:
            code = code.split("```html")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        return code

    def render_and_screenshot(self, html_code: str, iteration: int) -> Path:
        """
        Render HTML in a browser and capture screenshot

        Args:
            html_code: HTML code to render
            iteration: Current iteration number

        Returns:
            Path to screenshot file
        """
        # Save HTML file
        html_path = self.output_dir / f"iteration_{iteration}.html"
        with open(html_path, 'w') as f:
            f.write(html_code)

        # Capture screenshot using Playwright
        screenshot_path = self.output_dir / f"screenshot_{iteration}.png"

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            # Load the HTML file
            page.goto(f"file://{html_path.absolute()}")

            # Wait for Three.js to initialize and render
            time.sleep(3)  # Give time for WebGL to render

            # Take screenshot
            page.screenshot(path=screenshot_path)
            browser.close()

        print(f"  📸 Screenshot saved: {screenshot_path.name}")
        return screenshot_path

    def analyze_screenshot(self, screenshot_path: Path, original_prompt: str, current_code: str) -> Dict[str, Any]:
        """
        Analyze screenshot against original intent and provide feedback

        Args:
            screenshot_path: Path to screenshot
            original_prompt: Original user prompt
            current_code: Current HTML/JS code

        Returns:
            Dict with 'satisfactory' bool and 'feedback' string
        """
        # Read and encode screenshot
        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        analysis_prompt = f"""You are a QA engineer reviewing a Three.js implementation.

Original Request: {original_prompt}

Current Code Summary:
- The implementation is rendered and shown in the screenshot

Analyze the screenshot and determine if it matches the original request. Consider:
1. Does it contain the requested 3D elements?
2. Is the composition visually appealing?
3. Are colors, lighting, and materials appropriate?
4. Does it meet the user's intent?

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

    def refine_code(self, current_code: str, feedback: Dict[str, Any], original_prompt: str) -> str:
        """
        Refine code based on feedback

        Args:
            current_code: Current HTML/JS code
            feedback: Feedback from analysis
            original_prompt: Original user prompt

        Returns:
            Refined HTML code
        """
        refinement_prompt = f"""You are refining a Three.js implementation based on QA feedback.

Original Request: {original_prompt}

Current Code:
{current_code}

QA Feedback:
{feedback['feedback']}

Suggestions:
{feedback.get('suggestions', 'N/A')}

Generate an improved version of the code that addresses the feedback.
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

    def generate_with_feedback_loop(
        self,
        prompt: str,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Generate Three.js code with iterative feedback loop

        Args:
            prompt: Description of desired 3D scene
            max_iterations: Maximum refinement iterations

        Returns:
            Dict with final code, screenshots, and iteration history
        """
        print(f"🚀 Starting Three.js generation for: '{prompt}'")
        print(f"📁 Output directory: {self.output_dir}")

        # Generate initial code
        print("\n🎨 Generating initial Three.js code...")
        current_code = self.generate_initial_code(prompt)

        iteration_history = []

        for i in range(max_iterations):
            print(f"\n🔄 Iteration {i + 1}/{max_iterations}")

            # Render and screenshot
            screenshot_path = self.render_and_screenshot(current_code, i + 1)

            # Analyze screenshot
            print("  🔍 Analyzing screenshot...")
            analysis = self.analyze_screenshot(screenshot_path, prompt, current_code)

            iteration_history.append({
                "iteration": i + 1,
                "screenshot": str(screenshot_path),
                "analysis": analysis
            })

            print(f"  📊 Satisfactory: {analysis['satisfactory']}")
            print(f"  💬 Feedback: {analysis['feedback'][:100]}...")

            if analysis['satisfactory']:
                print(f"\n✅ Success! Final output achieved in {i + 1} iterations")
                break

            if i < max_iterations - 1:
                # Refine code based on feedback
                print("  🔧 Refining code based on feedback...")
                current_code = self.refine_code(current_code, analysis, prompt)
            else:
                print(f"\n⚠️  Reached maximum iterations ({max_iterations})")

        # Save final code
        final_html_path = self.output_dir / "final_output.html"
        with open(final_html_path, 'w') as f:
            f.write(current_code)

        print(f"\n📄 Final HTML saved: {final_html_path}")

        return {
            "final_code": current_code,
            "final_html_path": str(final_html_path),
            "iterations": len(iteration_history),
            "history": iteration_history,
            "success": iteration_history[-1]["analysis"]["satisfactory"]
        }


def main():
    """Example usage of the Three.js generator"""

    # Example prompts to test
    test_prompts = [
        "A rotating blue cube with golden edges on a dark background",
        "A solar system with the sun and 3 planets orbiting around it",
        "An abstract particle system with colorful particles floating in space",
    ]

    # You can also get user input
    print("Three.js Generator with QA Feedback Loop")
    print("=" * 50)
    print("\nExample prompts:")
    for i, prompt in enumerate(test_prompts, 1):
        print(f"  {i}. {prompt}")

    choice = input(f"\nSelect a prompt (1-{len(test_prompts)}) or enter your own: ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(test_prompts):
        prompt = test_prompts[int(choice) - 1]
    else:
        prompt = choice

    # Initialize generator
    try:
        generator = ThreeJSGenerator()
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        return

    # Run generation with feedback loop
    result = generator.generate_with_feedback_loop(prompt, max_iterations=3)

    # Print summary
    print("\n" + "=" * 50)
    print("📊 Generation Summary")
    print("=" * 50)
    print(f"Prompt: {prompt}")
    print(f"Iterations: {result['iterations']}")
    print(f"Success: {'✅' if result['success'] else '❌'}")
    print(f"Final output: {result['final_html_path']}")
    print("\nOpen the final HTML file in your browser to view the result!")


if __name__ == "__main__":
    main()
