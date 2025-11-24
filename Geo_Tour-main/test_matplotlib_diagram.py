"""
Test the matplotlib diagram generation feature
"""
from video_generator import VideoGenerator
from pathlib import Path

def test_matplotlib_diagram():
    """Test matplotlib diagram generation with labeled diagram and animation"""

    # Test description for a labeled geological diagram
    test_description = """Create a labeled cross-section diagram of the Earth's crust showing geological layers of the Grand Canyon.
    Include labels for: Kaibab Limestone (top layer), Toroweap Formation, Coconino Sandstone, Hermit Shale, Supai Group,
    Redwall Limestone, Muav Limestone, Bright Angel Shale, Tapeats Sandstone, and Vishnu Basement Rocks (bottom layer).
    Animate by slowly highlighting each layer from top to bottom, with each layer briefly glowing or changing opacity as it's highlighted.
    Use earthy colors: browns, reds, oranges, and grays to represent different rock types."""

    test_duration = 6  # 6 seconds
    test_scene_number = 998

    print("="*80)
    print("Testing Matplotlib Diagram Generation with gemini-3-pro-preview")
    print("="*80)
    print(f"Description: {test_description[:80]}...")
    print(f"Duration: {test_duration}s")
    print(f"Output: temp/scene_{test_scene_number}.mp4")
    print("="*80)
    print()

    try:
        # Initialize video generator
        generator = VideoGenerator()

        # Generate matplotlib diagram video
        output_dir = Path("temp")
        output_dir.mkdir(exist_ok=True)

        video_path = generator._generate_matplotlib_diagram(
            description=test_description,
            duration=test_duration,
            scene_number=test_scene_number,
            output_dir=output_dir
        )

        print()
        print("="*80)
        print("✅ SUCCESS!")
        print(f"Matplotlib diagram video saved to: {video_path}")
        print("="*80)

    except Exception as e:
        print()
        print("="*80)
        print(f"❌ Error: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_matplotlib_diagram()
