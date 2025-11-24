"""
Generate a detailed scene plan for Grand Canyon formation with Earth's layers
"""
import json
from scene_planner_ENHANCED import ScenePlanner

# Create planner with cinematic enhancement
planner = ScenePlanner(use_cinematic_enhancement=True)

# Custom script focusing on Earth's layers and Grand Canyon formation
script = {
    "title": "Formation of the Grand Canyon: A Journey Through Earth's Layers",
    "script": """
    Deep beneath our feet lies a story billions of years in the making. The Grand Canyon
    is not just a magnificent gorge - it's a window into Earth's ancient past, revealing
    the very layers that make up our planet.

    At the deepest level lie the Vishnu Basement Rocks, nearly 2 billion years old,
    formed from the crystallized roots of ancient mountains. These dark metamorphic and
    igneous rocks represent Earth's primordial crust.

    Above them, the Grand Canyon Supergroup tells of ancient seas and river deltas from
    1.2 billion to 740 million years ago. These tilted layers capture a time when continents
    were still assembling.

    The horizontal Paleozoic layers - the Tapeats Sandstone, Bright Angel Shale, and
    Redwall Limestone - record ancient oceans advancing and retreating over 500 million
    years. Each colorful band is a chapter in Earth's history book.

    Then came the Colorado River, carving downward over 6 million years, aided by the
    uplift of the Colorado Plateau. Layer by layer, the river exposed this geological
    masterpiece, creating one of nature's most spectacular cross-sections of Earth's crust.
    """
}

# Generate plan with 6 scenes for more detail
print("🎬 Generating detailed Grand Canyon + Earth's Layers scene plan...")
print("=" * 80)
plan = planner.create_plan(script, target_scenes=6, scene_duration=6)

# Display the plan
print("\n" + "=" * 80)
print("COMPLETE SCENE PLAN: GRAND CANYON & EARTH'S LAYERS")
print("=" * 80)
print(json.dumps(plan, indent=2))

# Summary
print("\n" + "=" * 80)
print("SCENE BREAKDOWN SUMMARY")
print("=" * 80)

video_scenes = []
viz_scenes = []

for scene in plan["scenes"]:
    scene_type_icon = "🎥" if scene["scene_type"] == "video" else "🎨"
    scene_type_label = "VIDEO" if scene["scene_type"] == "video" else "3D VISUALIZATION"

    print(f"\n{scene_type_icon} SCENE {scene['scene_number']} [{scene_type_label}] ({scene['duration']}s)")
    print(f"   Narration: {scene['narration']}")
    print(f"   Visual: {scene['visual_description'][:120]}...")

    if scene["scene_type"] == "video":
        video_scenes.append(scene['scene_number'])
    else:
        viz_scenes.append(scene['scene_number'])

print("\n" + "=" * 80)
print(f"📊 TOTAL: {len(plan['scenes'])} scenes")
print(f"   🎥 Video scenes: {len(video_scenes)} - {video_scenes}")
print(f"   🎨 3D visualization scenes: {len(viz_scenes)} - {viz_scenes}")
print("=" * 80)

# Save to file
output_file = "grand_canyon_scene_plan.json"
with open(output_file, 'w') as f:
    json.dump(plan, f, indent=2)

print(f"\n✅ Scene plan saved to: {output_file}")
print("\nℹ️  You can now use this plan in the Streamlit app to generate the full video!")
