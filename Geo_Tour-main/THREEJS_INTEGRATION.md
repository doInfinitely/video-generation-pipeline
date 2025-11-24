# Three.js 3D Visualization Integration

## Overview

The video generation pipeline now automatically mixes traditional AI-generated videos with animated Three.js 3D visualizations for enhanced educational content.

## What's New

### Automatic Scene Type Detection
The AI scene planner now intelligently determines which scenes benefit from 3D visualizations:

**3D Visualizations (🎨) are used for:**
- Geological cross-sections (Earth's layers, tectonic plates)
- Animated processes (erosion, plate movement, water cycles)
- Abstract scientific concepts
- Data visualizations
- Impossible camera angles

**Traditional Video (🎥) is used for:**
- Real-world landscapes and environments
- Natural phenomena (weather, water, sky)
- Establishing shots
- Anything filmable in reality

### Technical Specifications
- **Resolution:** 1920x1080 (1080p)
- **Frame Rate:** 24 fps
- **Format:** H.264 MP4 (matching Seedance specs)
- **Quality:** CRF 18 (visually lossless)
- **QA Loop:** 5 iterations with Gemini visual feedback

## Setup

### 1. Install Dependencies

```bash
pip install google-generativeai playwright
playwright install chromium
```

### 2. Add API Key

Add to your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Or use:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

Get your API key at: https://aistudio.google.com/app/apikey

### 3. Verify Installation

```bash
# Test the scene planner
python scene_planner_ENHANCED.py

# Test the Three.js generator
python threejs_video_generator.py
```

## Using in the App

### Streamlit App Features

1. **API Key Status**
   - Check sidebar → "🔑 API Keys Status"
   - Gemini key shows "🎨 Enables 3D visualizations with Three.js"

2. **Scene Type Display**
   - Results tab shows 🎥 for video scenes, 🎨 for 3D visualizations
   - Each scene displays its type explicitly

3. **Example Prompts**
   - "🌏 Earth's Layers 🎨" - Perfect for demonstrating 3D viz
   - Marked with 🎨 icon to indicate 3D visualization support

### Running the App

```bash
streamlit run app.py
```

## Architecture

```
User Prompt
    ↓
Scene Planner (Enhanced with scene_type)
    ↓
Mix of scene types:
    - 60% traditional video (🎥)
    - 40% 3D visualizations (🎨)
    ↓
Video Generator (routes by type)
    ↓
    ├─→ video → Replicate API (Seedance) → MP4
    └─→ 3d_visualization → Three.js → Frames → FFmpeg → MP4
    ↓
Video Assembler (unchanged)
    ↓
Final video with mixed content types
```

## Files Modified

| File | Changes |
|------|---------|
| `scene_planner_ENHANCED.py` | Added scene_type field, intelligent routing logic |
| `video_generator.py` | Added scene type routing, Three.js integration |
| `threejs_video_generator.py` | **NEW** - Frame capture & video export |
| `app.py` | UI updates for scene types, Gemini key status |
| `requirements.txt` | Added google-generativeai, playwright |

## Example Output

A typical 5-scene video on "Earth's Layers" might generate:

1. 🎥 Aerial view of Earth from space (video)
2. 🎨 Animated cross-section showing crust/mantle/core (3D viz)
3. 🎥 Close-up of rock layers in canyon (video)
4. 🎨 Tectonic plate movement animation (3D viz)
5. 🎥 Volcanic landscape finale (video)

## Troubleshooting

### "Three.js generator not available"
- Install: `pip install google-generativeai playwright`
- Run: `playwright install chromium`

### "Gemini API key required"
- Set `GEMINI_API_KEY` in `.env` file
- Or set `GOOGLE_API_KEY`

### FFmpeg errors
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check frames were captured: `temp/threejs_videos/scene_N_frames/`

### No 3D visualizations generated
- Check Gemini API key is valid
- Verify prompt benefits from 3D (use Earth layers example)
- Check logs for "3d_visualization" scene type

## Performance Notes

- 3D visualizations take ~2-3x longer than regular video scenes
- QA feedback loop adds ~30 seconds per scene
- Frame capture time: ~5-10 seconds per second of video
- Total: ~2-3 minutes per 6-second 3D scene

## Benefits

✅ **Better Explanations:** Complex concepts become clearer with 3D
✅ **Automatic Selection:** AI chooses best visualization method
✅ **Quality Assured:** Visual QA loop ensures accuracy
✅ **Consistent Output:** All MP4s match pipeline specs
✅ **Seamless Integration:** Works with existing video assembler

## Next Steps

1. Run the app: `streamlit run app.py`
2. Try "Earth's Layers" example
3. Watch for 🎨 icons in scene breakdown
4. Check output video for mixed content

## Support

For issues or questions:
- Check `/temp/threejs_videos/` for debug output
- Review FFmpeg logs in terminal
- Verify all dependencies installed
- Test with `python threejs_video_generator.py`

---

**Ready to create stunning educational videos with mixed 3D visualizations!** 🎬✨
