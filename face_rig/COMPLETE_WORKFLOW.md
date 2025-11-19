# Complete Watercolor Rig Workflow

## Overview

This is the end-to-end workflow for generating a full library of animated facial expressions using the watercolor rig system.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Input Assets                        │
├─────────────────────────────────────────────────────────┤
│ • Base neutral portrait (watercolor_boy_neutral.png)   │
│ • expressions.json (defines expressions & base_paths)   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│        Step 1: Generate Extreme Expressions             │
│        (generate_extreme_expressions.py)                │
├─────────────────────────────────────────────────────────┤
│ Parallel generation of keyframe expressions at center: │
│ • neutral__center.png                                   │
│ • speaking_ah__center.png                               │
│ • speaking_ee__center.png                               │
│ • speaking_uw__center.png                               │
│ • ...                                                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│        Step 2: Generate Head Tilts                      │
│        (generate_head_tilts.py)                         │
├─────────────────────────────────────────────────────────┤
│ Multiply each expression across all poses:             │
│ • neutral__tilt_left_small.png                          │
│ • neutral__tilt_right_small.png                         │
│ • speaking_ah__nod_up_small.png                         │
│ • ... (expression × pose matrix)                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│        Step 3: Generate Expression Sequences            │
│        (generate_all_sequences.py)                      │
├─────────────────────────────────────────────────────────┤
│ Expression-to-expression transitions at all poses:     │
│ • neutral_to_speaking_ah__center/                       │
│ • neutral_to_speaking_ah__tilt_left_small/              │
│   - 000.png, 025.png, 050.png, 075.png, 100.png       │
│   - manifest.json                                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│        Step 4: Generate Pose Sequences                  │
│        (generate_neutral_pose_sequences.py)             │
├─────────────────────────────────────────────────────────┤
│ Pose-to-pose transitions for neutral expression:       │
│ • neutral_center_to_neutral_tilt_left_small/            │
│ • neutral_center_to_neutral_tilt_right_small/           │
│ • neutral_center_to_neutral_nod_up_small/               │
│   - Same structure: endpoints + midpoints + manifest    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│        Step 5: Refine with UI (watercolor-rig)          │
├─────────────────────────────────────────────────────────┤
│ • Preview sequences                                      │
│ • Regenerate janky frames (single or range)            │
│ • Recursive binary subdivision for quality             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│        Output: Production-Ready Sequences               │
├─────────────────────────────────────────────────────────┤
│ • Full interpolated sequences                           │
│ • manifest.json per sequence                            │
│ • Ready for animation playback                          │
└─────────────────────────────────────────────────────────┘
```

## Step-by-Step Guide

### Prerequisites

```bash
# Set up environment
export OPENAI_API_KEY=sk-...
cd face_rig

# Ensure you have:
# - expressions.json
# - Base neutral portrait
# - Python 3.8+
# - OpenAI Python SDK
# - Pillow
```

### Step 1: Generate Extreme Expressions at Center Pose (5-10 minutes)

Generate all extreme/keyframe expressions at the center pose:

```bash
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image watercolor_boy_greenscreen.png \
  --pose center \
  --outdir frames/endpoints \
  --include-neutral \
  --max-workers 24
```

**What it does:**
- Takes neutral portrait as input
- Generates **all extreme expressions** defined in config (speaking_ah, speaking_ee, happy_soft, etc.)
- **Includes neutral** (`--include-neutral`) so it's model-generated (matches style of other frames)
- Typically 8-15 expressions depending on your config
- All at `center` pose (easiest for consistent results)
- Runs in parallel for speed
- Outputs: `frames/endpoints/{expr_id}__center.png`

**Output example:**
```
[i] Generating 9 expressions with 24 workers...
[✓] neutral -> frames/endpoints/neutral__center.png
[✓] speaking_ah -> frames/endpoints/speaking_ah__center.png
[✓] speaking_ee -> frames/endpoints/speaking_ee__center.png
[✓] speaking_uw -> frames/endpoints/speaking_uw__center.png
[✓] happy_soft -> frames/endpoints/happy_soft__center.png
[✓] happy_big -> frames/endpoints/happy_big__center.png
...
[i] Done. Success: 9, Failed: 0
```

### Step 2: Generate All Head Tilts (5-10 minutes)

Multiply each expression across all head poses:

```bash
python generate_head_tilts.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --base-neutral watercolor_boy_greenscreen.png \
  --source-pose center \
  --max-workers 24
```

**What it does:**
- Takes **each extreme expression** from Step 1 (speaking_ah, speaking_ee, happy_soft, etc.) at `center` pose
- For **each expression**, generates it at all other poses:
  - `tilt_left_small`
  - `tilt_right_small`
  - `nod_up_small`
  - `nod_down_small`
- Preserves the facial expression (mouth, eyes, brows), only changes head orientation
- Runs in parallel for speed
- Creates full **expression × pose matrix** (every expression at every pose)

**Output example:**
```
[i] Generating 36 head-tilted endpoints with 24 workers...
[✓] neutral @ tilt_left_small -> neutral__tilt_left_small.png
[✓] neutral @ tilt_right_small -> neutral__tilt_right_small.png
[✓] speaking_ah @ tilt_left_small -> speaking_ah__tilt_left_small.png
[✓] speaking_ah @ nod_up_small -> speaking_ah__nod_up_small.png
[✓] speaking_ee @ tilt_right_small -> speaking_ee__tilt_right_small.png
[✓] happy_soft @ nod_down_small -> happy_soft__nod_down_small.png
...
[i] Done. Success: 36, Failed: 0
```

**Result:** Full expression × pose grid in `frames/endpoints/`:
```
neutral__center.png
neutral__tilt_left_small.png
neutral__tilt_right_small.png
neutral__nod_up_small.png
neutral__nod_down_small.png

speaking_ah__center.png
speaking_ah__tilt_left_small.png
speaking_ah__tilt_right_small.png
speaking_ah__nod_up_small.png
speaking_ah__nod_down_small.png

speaking_ee__center.png
speaking_ee__tilt_left_small.png
... (and so on for all 8 expressions)
```

### Step 3: Generate Expression Tween Sequences (10-20 minutes)

Auto-generate all expression-to-expression tween sequences:

```bash
python generate_all_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --max-depth 2 \
  --max-workers 24
```

**What it does:**
- Scans `frames/endpoints/` for all extreme expressions
- Pairs them according to `base_paths` in config
- Uses recursive binary subdivision to generate tweens:
  - **Depth 1**: 0.5
  - **Depth 2**: 0.25, 0.75
  - (`max_depth=2` gives 3 tweens total)
- Creates manifest.json for each sequence
- Runs in parallel at each depth level

**Output example:**
```
[i] Found poses in endpoints: ['center', 'tilt_left_small', 'tilt_right_small', 'nod_up_small', 'nod_down_small']
[i] Initialized 35 sequences with endpoints.

=== Refinement depth 1 ===
[i] Depth 1: 35 tween frames to generate.
[✓] neutral_to_speaking_ah__center t=0.500 -> 050.png
[✓] neutral_to_speaking_ah__tilt_left_small t=0.500 -> 050.png
...
[i] Depth 1 done. Success: 35, Failed: 0

=== Refinement depth 2 ===
[i] Depth 2: 70 tween frames to generate.
[✓] neutral_to_speaking_ah__center t=0.250 -> 025.png
[✓] neutral_to_speaking_ah__center t=0.750 -> 075.png
...
[i] Depth 2 done. Success: 70, Failed: 0

[i] Wrote manifest: frames/sequences/neutral_to_speaking_ah__center/manifest.json
```

**Directory structure after:**
```
frames/
  endpoints/
    neutral__center.png
    speaking_ah__center.png
    speaking_ee__center.png
    ...
  sequences/
    neutral_to_speaking_ah__center/
      000.png
      025.png
      050.png
      075.png
      100.png
      manifest.json
    neutral_to_speaking_ee__center/
      ...
```

### Step 4: Generate Neutral Pose Transition Sequences (5-10 minutes)

Generate pose-to-pose transitions for neutral expression:

```bash
python generate_neutral_pose_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --source-pose center \
  --max-depth 2 \
  --max-workers 24
```

**What it does:**
- Takes neutral expression at all poses
- Generates **pose-to-pose transitions** (center → tilt_left, center → nod_down, etc.)
- Uses same recursive binary subdivision as expression sequences
- Creates sequences like `neutral_center_to_neutral_tilt_left_small`

**Output example:**
```
[i] Initialized 4 neutral pose sequences.

=== Pose refinement depth 1 ===
[i] Depth 1: 4 pose tween frames to generate.
[✓] neutral_center_to_neutral_tilt_left_small t=0.500 -> 050.png
[✓] neutral_center_to_neutral_tilt_right_small t=0.500 -> 050.png
[✓] neutral_center_to_neutral_nod_up_small t=0.500 -> 050.png
[✓] neutral_center_to_neutral_nod_down_small t=0.500 -> 050.png
[i] Depth 1 done. Success: 4, Failed: 0

=== Pose refinement depth 2 ===
[i] Depth 2: 8 pose tween frames to generate.
[✓] neutral_center_to_neutral_tilt_left_small t=0.250 -> 025.png
[✓] neutral_center_to_neutral_tilt_left_small t=0.750 -> 075.png
...
[i] Depth 2 done. Success: 8, Failed: 0
```

**Result:** Pose transition sequences in `frames/sequences/`:
```
frames/sequences/
  neutral_center_to_neutral_tilt_left_small/
    000.png  # neutral at center
    025.png
    050.png
    075.png
    100.png  # neutral at tilt_left_small
    manifest.json
  neutral_center_to_neutral_tilt_right_small/
    ...
  neutral_center_to_neutral_nod_up_small/
    ...
  neutral_center_to_neutral_nod_down_small/
    ...
```

### Step 5: Start Backend Server

```bash
# Terminal 1: Start FastAPI backend
cd face_rig
uvicorn server:app --reload --port 8000
```

The server:
- Auto-discovers sequences in `frames/sequences/`
- Serves frame images
- Provides regeneration API
- Loads manifests automatically

### Step 6: Start React UI

```bash
# Terminal 2: Start React dev server
cd face_rig/watercolor-rig
npm run dev
```

Open **http://localhost:5174**

### Step 7: Refine Sequences (As Needed)

Use the UI to refine any problematic frames:

1. **Load a sequence** - Click in sidebar or type path_id
2. **Preview** - Hit Play to see the animation
3. **Identify issues** - Find janky or inconsistent frames
4. **Select range** - Click first frame, Shift+Click last frame
5. **Regenerate** - Hit "Regenerate range (recursive)"
6. **Review** - Play again to verify quality

**Regeneration strategies:**

| Issue | Solution |
|-------|----------|
| Single bad frame | Click "Regenerate" on that frame |
| Multiple adjacent bad frames | Select range → "Regenerate range (recursive)" |
| Entire sequence needs work | Regenerate from endpoints with `generate_sequence.py` |

## Configuration

### expressions.json Structure

```json
{
  "expressions": {
    "neutral": {
      "mouth": "neutral",
      "eyes": "neutral",
      "brows": "neutral"
    },
    "speaking_ah": {
      "mouth": "ah",
      "eyes": "neutral",
      "brows": "neutral"
    },
    "speaking_ee": {
      "mouth": "ee",
      "eyes": "neutral",
      "brows": "neutral"
    }
  },
  "base_paths": [
    {
      "id": "neutral_to_speaking_ah",
      "start": "neutral",
      "end": "speaking_ah"
    },
    {
      "id": "neutral_to_speaking_ee",
      "start": "neutral",
      "end": "speaking_ee"
    }
  ],
  "poses": ["center", "tilt_left_small", "tilt_right_small"]
}
```

## Performance Optimization

### Parallel Processing

All generation scripts support `--max-workers`:

| Workers | Speed | Risk |
|---------|-------|------|
| 2-4 | Conservative | Low rate limit risk |
| 6-12 | Balanced | Good for most cases |
| 16-24 | Aggressive | Recommended for production |
| 30+ | Very aggressive | May hit rate limits |

### Time Estimates

**For 9 expressions (including neutral) × 5 poses, 7 base_paths:**

| Step | Images | Sequential | Parallel (24 workers) |
|------|--------|-----------|----------------------|
| Step 1: Extremes at center | 9 | 9 × 30s = 4.5 min | ~30s |
| Step 2: Head tilts | 36 | 36 × 30s = 18 min | ~1.5 min |
| Step 3: Expression sequences (depth 2) | 105 | 105 × 30s = 52 min | ~3 min |
| Step 4: Pose sequences (depth 2) | 12 | 12 × 30s = 6 min | ~30s |
| **Total** | **162** | **~80 min** | **~6 min** |

With `max_depth=2`, you get 3 tweens per sequence (at t=0.25, 0.5, 0.75).

### Cost Optimization

**OpenAI pricing (gpt-image-1 edit):**
- ~$0.10 per image (approximate)
- 9 extremes + 36 head tilts + 105 expression tweens + 12 pose tweens = **162 images**
- **Total: ~$16.20 for complete rig**

**Breakdown:**
- Step 1 (extremes): 9 × $0.10 = **$0.90**
- Step 2 (head tilts): 36 × $0.10 = **$3.60**
- Step 3 (expression sequences): 105 × $0.10 = **$10.50**
- Step 4 (pose sequences): 12 × $0.10 = **$1.20**

**Tips:**
- Generate extremes and head tilts once, reuse for multiple sequence variations
- Use `--overwrite` sparingly
- Start with `max_depth=1` (1 tween per sequence), increase if needed
- For `max_depth=3`: 7 tweens per sequence = ~$35 total

## Troubleshooting

### Issue: "No sequences generated"

**Cause**: Missing endpoints or config mismatch

**Fix**:
```bash
# List available endpoints
ls frames/endpoints/

# Check they match expressions.json base_paths
# Ensure both start and end expressions exist
```

### Issue: Rate limit errors

**Cause**: Too many parallel requests

**Fix**:
```bash
# Reduce workers from 24 to a more conservative number
python generate_all_sequences.py --max-workers 12 ...

# Or very conservative
python generate_all_sequences.py --max-workers 4 ...
```

### Issue: Janky frames in UI

**Cause**: Poor interpolation between distant anchors

**Fix**:
1. Select the janky range
2. Ensure endpoints of range are good
3. Use "Regenerate range (recursive)"
4. Let binary subdivision create better intermediates

### Issue: Style drift across sequence

**Cause**: OpenAI model variance

**Fix**:
1. Regenerate extremes with more explicit prompts
2. Use fewer tweens initially
3. Refine specific frames in UI

## Advanced Usage

### Generate Dense Sequences

For very smooth animations, increase `max_depth`:

```bash
# Depth 3: 7 tweens per sequence (0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875)
python generate_all_sequences.py \
  --config expressions.json \
  --max-depth 3 \
  --max-workers 24

python generate_neutral_pose_sequences.py \
  --config expressions.json \
  --max-depth 3 \
  --max-workers 24
```

**Tween count by depth:**
- `max_depth=1`: 1 tween (0.5)
- `max_depth=2`: 3 tweens (0.25, 0.5, 0.75)
- `max_depth=3`: 7 tweens (every 0.125)
- `max_depth=4`: 15 tweens (every 0.0625)

### Complete Production Pipeline

Run all 4 steps in sequence:

```bash
#!/bin/bash
export OPENAI_API_KEY=sk-...

cd face_rig

echo "Step 1: Generating extreme expressions..."
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image watercolor_boy_greenscreen.png \
  --pose center \
  --outdir frames/endpoints \
  --include-neutral \
  --max-workers 24

echo "Step 2: Generating head tilts..."
python generate_head_tilts.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --base-neutral watercolor_boy_greenscreen.png \
  --source-pose center \
  --max-workers 24

echo "Step 3: Generating expression sequences..."
python generate_all_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --max-depth 2 \
  --max-workers 24

echo "Step 4: Generating pose sequences..."
python generate_neutral_pose_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --source-pose center \
  --max-depth 2 \
  --max-workers 24

echo "Done! Complete animation rig generated."
```

## Next Steps

After generating your sequence library:

1. **Export for Animation**
   - Sequences are ready for FFmpeg, After Effects, or game engines
   - Each frame is a standalone PNG

2. **Build UI Controls**
   - Create animation player
   - Blend between sequences
   - Add audio sync

3. **Optimize Assets**
   - Compress PNGs (pngquant, oxipng)
   - Create sprite sheets
   - Generate video files for web playback

4. **Scale Up**
   - Add more expressions
   - Generate for more poses
   - Create expression combinations

## Summary

✅ **Automated 4-step pipeline** - From single neutral portrait to full animation library  
✅ **Expression × Pose matrix** - Every expression at every pose automatically  
✅ **Parallel processing** - ~6 minutes total with 24 workers  
✅ **Quality control** - React UI for refinement and regeneration  
✅ **Production ready** - Organized sequences with manifests  
✅ **Cost effective** - ~$16.20 for complete rig with 162 generated images  
✅ **Subject-centric poses** - Unambiguous left/right definitions prevent confusion

**Complete rig includes:**
- 9 expressions (including neutral) × 5 poses = **45 endpoint images**
- 7 base_paths × 5 poses = **35 expression sequences**
- 4 pose transitions = **4 pose sequences**
- Each sequence with 3-15 tweens (depending on `max_depth`)
- = **39 complete animation sequences** ready for production! 🎨✨

