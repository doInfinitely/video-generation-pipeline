"""
Test matplotlib diagram generation using descriptions from the actual plan generation
"""
from video_generator import VideoGenerator
from pathlib import Path

def test_diagram_scene_2():
    """Test Scene 2 - Cross-section diagram"""

    # This is the actual description from the plan generation test (Scene 2)
    test_description = "A cross-section diagram of the Grand Canyon showing distinct rock layers with labels for each era, such as Precambrian, Paleozoic, and Mesozoic. Simple animation highlights each layer sequentially, emphasizing the change over time."

    test_duration = 6
    test_scene_number = 2

    print("="*80)
    print("Testing Diagram Scene 2: Cross-Section with Layer Highlighting")
    print("="*80)
    print(f"Description: {test_description}")
    print(f"Duration: {test_duration}s")
    print(f"Output: temp/scene_{test_scene_number}.mp4")
    print("="*80)
    print()

    try:
        generator = VideoGenerator()
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
        print(f"Diagram video saved to: {video_path}")
        print("="*80)

    except Exception as e:
        print()
        print("="*80)
        print(f"❌ Error: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()

def test_diagram_scene_5():
    """Test Scene 5 - Tectonic plates diagram"""

    # This is the actual description from the plan generation test (Scene 5)
    test_description = "Diagram illustrating the movement of tectonic plates with labeled arrows indicating direction and force. Simple animation shows the plates shifting over time, contributing to the uplift and erosion that formed the canyon."

    test_duration = 6
    test_scene_number = 5

    print("="*80)
    print("Testing Diagram Scene 5: Tectonic Plates Movement")
    print("="*80)
    print(f"Description: {test_description}")
    print(f"Duration: {test_duration}s")
    print(f"Output: temp/scene_{test_scene_number}.mp4")
    print("="*80)
    print()

    try:
        generator = VideoGenerator()
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
        print(f"Diagram video saved to: {video_path}")
        print("="*80)

    except Exception as e:
        print()
        print("="*80)
        print(f"❌ Error: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING DIAGRAM GENERATION FROM ACTUAL PLAN")
    print("="*80 + "\n")

    # Test the cross-section diagram (Scene 2)
    test_diagram_scene_2()

    print("\n\n")

    # Test the tectonic plates diagram (Scene 5)
    test_diagram_scene_5()
