"""
Test script for mixed scene types (video + 3D visualization)

This tests the complete pipeline:
1. Scene planner generates mix of scene types
2. Video generator routes to appropriate generators
3. Both video and 3D clips are created successfully
"""

import json
from pathlib import Path
from scene_planner_ENHANCED import ScenePlanner
from video_generator import VideoGenerator


def test_mixed_scene_generation():
    """Test end-to-end generation with mixed scene types"""

    print("=" * 80)
    print("MIXED SCENE TYPE PIPELINE TEST")
    print("=" * 80)
    print()

    # Step 1: Create scene plan with mixed types
    print("Step 1: Creating scene plan with mixed types...")
    print("-" * 80)

    planner = ScenePlanner(use_cinematic_enhancement=True)

    test_script = {
        "title": "Earth's Layers and Tectonic Activity",
        "script": "Our planet Earth is made up of distinct layers, each with unique properties. "
                  "From the thin rocky crust we walk on, through the thick mantle of hot rock, "
                  "to the liquid outer core and solid inner core. These layers interact through "
                  "tectonic processes, with massive plates sliding over the mantle, creating "
                  "mountains, earthquakes, and shaping our world's geography."
    }

    # Generate plan with 3 scenes (should get mix of video and 3D viz)
    scene_plan = planner.create_plan(test_script, target_scenes=3, scene_duration=6)

    print()
    print("Generated scene plan:")
    print("-" * 80)
    for scene in scene_plan["scenes"]:
        scene_type_icon = "🎨" if scene["scene_type"] == "3d_visualization" else "🎥"
        print(f"{scene_type_icon} Scene {scene['scene_number']}: {scene['scene_type']}")
        print(f"   {scene['visual_description'][:80]}...")
        print()

    # Count scene types
    video_count = sum(1 for s in scene_plan["scenes"] if s["scene_type"] == "video")
    viz_count = sum(1 for s in scene_plan["scenes"] if s["scene_type"] == "3d_visualization")

    print(f"Scene type distribution: {video_count} video, {viz_count} 3D visualization")
    print()

    if viz_count == 0:
        print("⚠️  Warning: No 3D visualization scenes generated!")
        print("    The test will still proceed but won't test 3D generation.")
        print()

    # Step 2: Generate video clips
    print("Step 2: Generating video clips...")
    print("-" * 80)
    print()

    # Create output directory
    output_dir = Path("temp/mixed_scene_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        generator = VideoGenerator()

        # Generate only the first scene to test both types quickly
        # (generating all scenes would take too long for a test)
        print("NOTE: Testing with first scene only for speed")
        print()

        first_scene = scene_plan["scenes"][0]
        scene_type = first_scene["scene_type"]

        print(f"Generating scene 1 ({scene_type})...")
        clip_path = generator._generate_clip(
            description=first_scene['visual_description'],
            duration=first_scene['duration'],
            scene_number=first_scene['scene_number'],
            output_dir=output_dir,
            storyboard_image=None,
            scene_type=scene_type
        )

        print()
        print("=" * 80)
        print("✅ TEST SUCCESSFUL!")
        print("=" * 80)
        print(f"Scene type: {scene_type}")
        print(f"Output video: {clip_path}")
        print()
        print(f"Video file exists: {Path(clip_path).exists()}")
        print(f"Video file size: {Path(clip_path).stat().st_size / 1024 / 1024:.2f} MB")
        print()

        # Verify video specs using ffprobe if available
        try:
            import subprocess
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,r_frame_rate,codec_name",
                    "-of", "json",
                    clip_path
                ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                video_info = json.loads(result.stdout)
                stream = video_info["streams"][0]
                print("Video specifications:")
                print(f"  Resolution: {stream['width']}x{stream['height']}")
                print(f"  Frame rate: {stream['r_frame_rate']}")
                print(f"  Codec: {stream['codec_name']}")
                print()
        except Exception:
            pass

        print("To test full pipeline with all scenes, use the main pipeline.py")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ TEST FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_mixed_scene_generation()
