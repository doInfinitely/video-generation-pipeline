"""
Test the diagram scene type in scene planner
"""
from scene_planner_ENHANCED import ScenePlanner
import json

def test_diagram_plan():
    """Test scene planning with diagram scene type"""

    print("="*80)
    print("Testing Diagram Scene Type in Scene Planner")
    print("="*80)
    print()

    try:
        # Initialize scene planner
        planner = ScenePlanner(use_cinematic_enhancement=True)

        # Test script for Grand Canyon
        test_script = {
            "title": "The Formation of the Grand Canyon",
            "script": "The Grand Canyon formed over millions of years through the erosive power of the Colorado River. Layer by layer, the river cut through ancient rock formations, revealing a geological timeline spanning nearly two billion years. The canyon's distinctive red and orange layers tell the story of ancient seas, deserts, and shifting tectonic plates that shaped this magnificent landscape."
        }

        print("Generating scene plan with diagram scene type...")
        print(f"Title: {test_script['title']}")
        print(f"Script: {test_script['script'][:80]}...")
        print()

        # Create plan
        plan = planner.create_plan(test_script, target_scenes=5, scene_duration=6)

        print()
        print("="*80)
        print("SCENE PLAN OUTPUT")
        print("="*80)
        print(json.dumps(plan, indent=2))

        print()
        print("="*80)
        print("SCENE TYPE SUMMARY")
        print("="*80)
        for scene in plan["scenes"]:
            scene_type_icon = "🎥" if scene["scene_type"] == "video" else "📊"
            print(f"{scene_type_icon} Scene {scene['scene_number']}: {scene['scene_type']}")
            print(f"   Narration: {scene['narration'][:60]}...")
            print(f"   Visual: {scene['visual_description'][:80]}...")
            print()

        # Count diagram scenes
        diagram_count = sum(1 for s in plan["scenes"] if s["scene_type"] == "diagram")
        print(f"✅ SUCCESS! Generated {len(plan['scenes'])} scenes with {diagram_count} diagram scene(s)")

        if diagram_count == 0:
            print("⚠️  WARNING: No diagram scenes were generated!")

    except Exception as e:
        print()
        print("="*80)
        print(f"❌ Error: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_diagram_plan()
