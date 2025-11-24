"""
Scene planning module - breaks scripts into visual scenes
ENHANCED with automatic cinematic prompting
"""

from openai import OpenAI
import json
from config import OPENAI_API_KEY, OPENAI_MODEL, SCENE_MAX_TOKENS, TARGET_SCENES
from system_prompts import CinematicSystemPrompts

# ADDED: Import cinematic enhancer
from cinematic_enhancer import CinematicEnhancer

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (IOError, OSError, ValueError):
        pass

class ScenePlanner:
    def __init__(self, api_key=None, use_cinematic_enhancement=True):
        """
        Initialize scene planner

        Args:
            api_key: OpenAI API key
            use_cinematic_enhancement: If True, automatically enhance visual 
                                      descriptions with cinematic vocabulary
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=self.api_key)

        # ADDED: Cinematic enhancement
        self.use_cinematic_enhancement = use_cinematic_enhancement
        self.cinematic_enhancer = CinematicEnhancer() if use_cinematic_enhancement else None

    def create_plan(self, script_data, target_scenes=None, scene_duration=None):
        """
        Create a scene-by-scene plan from script

        Args:
            script_data (dict): Script with title and narration
            target_scenes (int): Number of scenes to create
            scene_duration (int): Duration per scene in seconds

        Returns:
            dict: Scene plan with visual descriptions and timing
        """
        safe_print("🎬 Creating scene plan...")

        ts = target_scenes or TARGET_SCENES
        sd = scene_duration or 6
        if sd > 12:
            sd = 12

        prompt = f"""Break this video script into {ts} scenes with detailed visual descriptions.

Title: {script_data['title']}
Script: {script_data['script']}

IMPORTANT: You must include a MIX of scene types:
- "video": Traditional AI-generated video footage (real-world scenes, landscapes, nature, etc.)
- "diagram": Labeled matplotlib diagrams with simple animations (best for: cross-sections, geological layers, scientific diagrams, data visualizations, educational illustrations)

WHEN TO USE DIAGRAMS:
✓ Geological cross-sections (Earth's layers, tectonic plates, fault lines) with labels
✓ Scientific diagrams that need labels and annotations
✓ Abstract scientific concepts that need visual representation with text labels
✓ Data visualizations, charts, or comparative diagrams
✓ Educational illustrations that benefit from labeled components

WHEN TO USE VIDEO:
✓ Real-world landscapes and environments
✓ Natural phenomena (weather, water, sky)
✓ Establishing shots and context scenes
✓ Anything that could be filmed in the real world

REQUIREMENT: Include AT LEAST one diagram scene in the plan (preferably 1-2 out of {ts} scenes).

Return ONLY a JSON object with this structure:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "scene_type": "video",
      "narration": "portion of script for this scene",
      "visual_description": "detailed description of visuals to generate - be specific about what should be shown",
      "duration": {sd}
    }},
    {{
      "scene_number": 2,
      "scene_type": "diagram",
      "narration": "portion of script for this scene",
      "visual_description": "detailed description of labeled diagram to generate - specify what should be shown, what labels are needed, and what simple animation should occur (e.g., highlighting different layers, zooming in, fading elements)",
      "duration": {sd}
    }}
  ]
}}

Each scene should be {sd} seconds. Visual descriptions should be detailed and suitable for generation.
For diagrams, include: what should be shown, what labels are needed, and what simple animation should occur.
DO NOT include any text outside the JSON."""

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=SCENE_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": CinematicSystemPrompts.get_scene_planning_prompt()},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            # Parse response
            plan_text = response.choices[0].message.content.strip()
            scene_plan = json.loads(plan_text)

            # Validate structure
            if "scenes" not in scene_plan or not scene_plan["scenes"]:
                raise ValueError("Invalid scene plan structure")

            for scene in scene_plan["scenes"]:
                required_fields = ["scene_number", "scene_type", "narration", "visual_description", "duration"]
                if not all(field in scene for field in required_fields):
                    raise ValueError(f"Scene missing required fields: {scene}")

                # Validate scene_type
                if scene["scene_type"] not in ["video", "diagram"]:
                    raise ValueError(f"Invalid scene_type: {scene['scene_type']}. Must be 'video' or 'diagram'")

                try:
                    scene["duration"] = sd
                except Exception:
                    pass

            # Count scene types
            video_count = sum(1 for s in scene_plan["scenes"] if s["scene_type"] == "video")
            diagram_count = sum(1 for s in scene_plan["scenes"] if s["scene_type"] == "diagram")
            safe_print(f"✅ Created {len(scene_plan['scenes'])} scenes ({video_count} video, {diagram_count} diagram)")

            # ADDED: Apply cinematic enhancement
            if self.use_cinematic_enhancement and self.cinematic_enhancer:
                safe_print("🎥 Enhancing scenes with cinematic prompting...")
                scene_plan = self.cinematic_enhancer.enhance_scene_plan(
                    scene_plan, 
                    original_user_prompt=script_data.get('title', '')
                )
                safe_print("✅ Cinematic enhancement applied to all scenes")

            return scene_plan

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse scene plan: {e}")
        except Exception as e:
            raise RuntimeError(f"Scene planning failed: {e}")


if __name__ == "__main__":
    # Test the enhanced scene planner with scene types
    planner = ScenePlanner(use_cinematic_enhancement=True)

    test_script = {
        "title": "The Formation of the Grand Canyon",
        "script": "The Grand Canyon formed over millions of years through the erosive power of the Colorado River. Layer by layer, the river cut through ancient rock formations, revealing a geological timeline spanning nearly two billion years. The canyon's distinctive red and orange layers tell the story of ancient seas, deserts, and shifting tectonic plates that shaped this magnificent landscape."
    }

    plan = planner.create_plan(test_script, target_scenes=5)

    print("\n" + "="*80)
    print("ENHANCED SCENE PLAN OUTPUT WITH SCENE TYPES")
    print("="*80)
    print(json.dumps(plan, indent=2))

    print("\n" + "="*80)
    print("SCENE TYPE SUMMARY")
    print("="*80)
    for scene in plan["scenes"]:
        scene_type_icon = "🎥" if scene["scene_type"] == "video" else "📊"
        print(f"{scene_type_icon} Scene {scene['scene_number']}: {scene['scene_type']}")
        print(f"   Narration: {scene['narration'][:60]}...")
        print(f"   Visual: {scene['visual_description'][:80]}...")
        print()
