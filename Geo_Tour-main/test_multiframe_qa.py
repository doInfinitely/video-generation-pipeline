"""
Test script for the multi-frame video QA process

This script tests the improved QA system that takes multiple screenshots
(start, middle, end) to catch timing and animation speed issues.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from threejs_video_generator import ThreeJSVideoGenerator


def test_multiframe_qa():
    """Test the multi-frame QA process with a simple animation"""

    print("=" * 70)
    print("MULTI-FRAME QA TEST")
    print("=" * 70)
    print()
    print("This test will:")
    print("  1. Generate a Three.js animation")
    print("  2. Take screenshots at START, MIDDLE, and END")
    print("  3. Analyze timing and pacing issues")
    print("  4. Iterate until the animation is correctly paced")
    print()
    print("=" * 70)
    print()

    # Test case: An animation that might be prone to timing issues
    test_description = """
Macro detail shot of An animated cross-section of the Earth's crust showing layers, with the camera slowly descending to focus on the Vishnu Basement Rocks. The layers are labeled, and textures of dark metamorphic and igneous rocks are highlighted., backlit with rim lighting, revealing geological layers and deep time, with clear foreground, mid-ground, and background layers, staged for gentle tracking shot. stunning visual spectacle, 16:9 cinematic composition
    """.strip()

    test_duration = 5  # 5 second animation

    print(f"Test Description: {test_description}")
    print(f"Expected Duration: {test_duration}s")
    print()

    try:
        # Initialize generator
        print("Initializing ThreeJSVideoGenerator...")
        generator = ThreeJSVideoGenerator(
            width=1920,
            height=1080,
            fps=24
        )
        print("✓ Generator initialized")
        print()

        # Test just the QA process (without full video rendering)
        print("Starting multi-frame QA test...")
        print()

        # Generate initial code
        print("🎨 Generating initial Three.js code...")
        html_code = generator.generate_initial_code(test_description, test_duration)
        print("✓ Initial code generated")
        print()

        # Test the multi-frame screenshot capture
        print("📸 Testing multi-frame screenshot capture...")
        screenshot_paths = generator.render_preview_screenshots_multiframe(
            html_code=html_code,
            scene_number=999,
            duration=test_duration,
            iteration=0
        )

        print(f"✓ Captured {len(screenshot_paths)} screenshots:")
        for path in screenshot_paths:
            print(f"  - {path.name}")
        print()

        # Test the multi-frame analysis
        print("🔍 Testing multi-frame analysis...")
        analysis = generator.analyze_screenshots_multiframe(
            screenshot_paths=screenshot_paths,
            original_prompt=test_description,
            duration=test_duration
        )

        print("✓ Analysis complete")
        print()
        print("Analysis Results:")
        print(f"  Satisfactory: {'✅ YES' if analysis['satisfactory'] else '❌ NO'}")
        print(f"  Feedback: {analysis['feedback']}")
        if 'timing_issues' in analysis and analysis['timing_issues']:
            print(f"  Timing Issues: {analysis['timing_issues']}")
        if 'suggestions' in analysis and analysis['suggestions']:
            print(f"  Suggestions: {analysis['suggestions']}")
        print()

        # If not satisfactory, test refinement
        if not analysis['satisfactory']:
            print("🔧 Animation needs refinement. Testing code refinement...")
            refined_code = generator.refine_code(
                current_code=html_code,
                feedback=analysis,
                original_prompt=test_description,
                duration=test_duration
            )
            print("✓ Code refined")
            print()

            # Capture screenshots of refined version
            print("📸 Capturing screenshots of refined version...")
            refined_screenshots = generator.render_preview_screenshots_multiframe(
                html_code=refined_code,
                scene_number=999,
                duration=test_duration,
                iteration=1
            )
            print(f"✓ Captured {len(refined_screenshots)} screenshots")
            print()

            # Analyze refined version
            print("🔍 Analyzing refined version...")
            refined_analysis = generator.analyze_screenshots_multiframe(
                screenshot_paths=refined_screenshots,
                original_prompt=test_description,
                duration=test_duration
            )

            print("✓ Refined analysis complete")
            print()
            print("Refined Analysis Results:")
            print(f"  Satisfactory: {'✅ YES' if refined_analysis['satisfactory'] else '❌ NO'}")
            print(f"  Feedback: {refined_analysis['feedback']}")
            if 'timing_issues' in refined_analysis and refined_analysis['timing_issues']:
                print(f"  Timing Issues: {refined_analysis['timing_issues']}")
            print()

        print("=" * 70)
        print("✅ MULTI-FRAME QA TEST COMPLETE")
        print("=" * 70)
        print()
        print("Screenshots saved to:", generator.output_dir)
        print()
        print("You can review the screenshots to verify:")
        print("  1. START frame shows beginning of animation")
        print("  2. MIDDLE frame shows halfway progression")
        print("  3. END frame shows near-complete animation")
        print("  4. Progression is smooth and appropriately paced")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_video_generation():
    """Test the full video generation with multi-frame QA"""

    print()
    print("=" * 70)
    print("FULL VIDEO GENERATION TEST WITH MULTI-FRAME QA")
    print("=" * 70)
    print()

    test_description = "A slowly rotating Earth with realistic continents and atmosphere glow, camera gradually zooms out to reveal the planet in space with stars in the background"
    test_duration = 4

    print(f"Description: {test_description}")
    print(f"Duration: {test_duration}s")
    print()

    try:
        generator = ThreeJSVideoGenerator()

        video_path = generator.generate_video_with_feedback(
            description=test_description,
            duration=test_duration,
            scene_number=998,
            max_iterations=3
        )

        print()
        print("=" * 70)
        print("✅ FULL VIDEO TEST COMPLETE")
        print("=" * 70)
        print(f"Video saved to: {video_path}")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run QA tests"""

    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║       MULTI-FRAME VIDEO QA TESTING SUITE                         ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    print("This test suite validates the improved QA process that uses")
    print("multiple screenshots to catch animation timing and pacing issues.")
    print()

    # Check for API key
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
        print()
        print("Please set your API key:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print()
        return

    # Check for command-line argument or default to test 1
    choice = "1"
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        # Try to get interactive input if possible, otherwise default
        try:
            print("Available tests:")
            print("  1. Quick QA Test - Test multi-frame screenshot and analysis only")
            print("  2. Full Video Test - Generate complete video with multi-frame QA")
            print("  3. Both Tests")
            print()
            choice = input("Select test (1-3) [1]: ").strip() or "1"
            print()
        except (EOFError, KeyboardInterrupt):
            # Non-interactive mode, use default
            print("Running in non-interactive mode, defaulting to Quick QA Test (1)")
            print()
            choice = "1"

    if choice == "1":
        test_multiframe_qa()
    elif choice == "2":
        test_full_video_generation()
    elif choice == "3":
        if test_multiframe_qa():
            test_full_video_generation()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
