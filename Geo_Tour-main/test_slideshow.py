"""
Test the new nano-banana-pro slideshow feature for 3D visualizations
"""
from video_generator import VideoGenerator
from pathlib import Path

def test_slideshow():
    """Test slideshow generation with Grand Canyon cross-section prompt"""

    # The test prompt from the user
    test_description = "Macro detail shot of An animated cross-section of the Earth's crust showing layers, with the camera slowly descending to focus on the Vishnu Basement Rocks. The layers are labeled, and textures of dark metamorphic and igneous rocks are highlighted., backlit with rim lighting, revealing geological layers and deep time, with clear foreground, mid-ground, and background layers, staged for gentle tracking shot. stunning visual spectacle, 16:9 cinematic composition"

    test_duration = 6  # 6 seconds
    test_scene_number = 999

    print("="*80)
    print("Testing nano-banana-pro Slideshow Feature")
    print("="*80)
    print(f"Description: {test_description[:80]}...")
    print(f"Duration: {test_duration}s")
    print(f"Output: temp/scene_{test_scene_number}.mp4")
    print("="*80)
    print()

    try:
        # Initialize video generator
        generator = VideoGenerator()

        # Generate slideshow video (internally uses _generate_3d_visualization)
        output_dir = Path("temp")
        output_dir.mkdir(exist_ok=True)

        video_path = generator._generate_3d_visualization(
            description=test_description,
            duration=test_duration,
            scene_number=test_scene_number,
            output_dir=output_dir
        )

        print()
        print("="*80)
        print("✅ SUCCESS!")
        print(f"Slideshow video saved to: {video_path}")
        print("="*80)

    except Exception as e:
        print()
        print("="*80)
        print(f"❌ Error: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_slideshow()
