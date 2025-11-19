# Watercolor Character Player

State machine player for the watercolor face animation rig.

## What It Does

This is an interactive **state machine tester** that lets you:
- Click buttons to change expression or pose
- Watch the system automatically route between states
- Enable "resting blink" for natural idle animations

## State Space

The character exists in a 2D state space:
- **Expression axis**: neutral, happy_soft, happy_big, speaking_ah, surprised_ah, speaking_ee, speaking_uw, oh_round, concerned, blink_closed
- **Pose axis**: center, tilt_left_small, tilt_right_small, nod_down_small, nod_up_small

**Current state**: `(expression, pose)` tuple

## Routing Logic

When you click to go from state A to state B:

**1. Same pose, direct path exists:**
```
neutral @ center → speaking_ah @ center
Uses: neutral_to_speaking_ah__center
```

**2. Same pose, no direct path:**
```
speaking_ah @ center → speaking_ee @ center
Detours: speaking_ah → neutral → speaking_ee (all at center)
```

**3. Different pose:**
```
speaking_ah @ center → speaking_ee @ tilt_left
Route: 
  1. speaking_ah @ center → neutral @ center
  2. neutral @ center → neutral @ tilt_left
  3. neutral @ tilt_left → speaking_ee @ tilt_left
```

**4. Non-center pose to non-center pose:**
```
concerned @ tilt_left → speaking_ah @ tilt_right
Route:
  1. concerned @ tilt_left → neutral @ tilt_left
  2. neutral @ tilt_left → neutral @ center (backward)
  3. neutral @ center → neutral @ tilt_right (forward)
  4. neutral @ tilt_right → speaking_ah @ tilt_right
```

**Key routing rules:**
- **Neutral is the expression hub** - all cross-pose transitions route through neutral expression first
- **Center is the pose hub** - pose sequences only exist between center and other poses
- Non-center to non-center pose transitions automatically route via center

## Setup

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

Open http://localhost:5175

## Requirements

- FastAPI backend running at `http://localhost:8000`
- Generated sequences in `frames/sequences/`
- Sequences must include:
  - Expression sequences: `{base_path}__{pose}` (e.g., `neutral_to_speaking_ah__center`)
  - Pose sequences: `neutral_{poseA}_to_neutral_{poseB}` (e.g., `neutral_center_to_neutral_tilt_left_small`)

## Features

### Expression Buttons
Click any expression to transition to it while keeping the current pose.

### Pose Buttons
Click any pose to transition to it while keeping the current expression (routes through neutral if needed).

### Resting Blink
When enabled and idle in neutral, the character will occasionally blink automatically:
- Waits 2-6 seconds
- Plays neutral → blink_closed → neutral
- Only triggers when not already transitioning

### Stop/Reset
Cancels the current transition and freezes on the current frame.

## State Machine Graph

```
Expression transitions (per pose):
  neutral ↔ happy_soft ↔ happy_big
  neutral ↔ speaking_ah ↔ surprised_ah
  neutral ↔ speaking_ee
  neutral ↔ speaking_uw
  neutral ↔ concerned
  neutral ↔ blink_closed

Pose transitions (neutral only):
  center ↔ tilt_left_small
  center ↔ tilt_right_small
  center ↔ nod_up_small
  center ↔ nod_down_small
```

**Bidirectional Playback:**
All sequences are bidirectional - they can be played forwards or backwards. This means:
- `neutral_to_speaking_ah` can go **neutral → speaking_ah** (forward) OR **speaking_ah → neutral** (backward)
- `neutral_center_to_neutral_tilt_left` can go **center → tilt_left** (forward) OR **tilt_left → center** (backward)
- You only need to generate each sequence once, and the player automatically reverses it when needed

All other transitions route through the graph (often via neutral).

## File Structure

```
character-player/
├── src/
│   ├── App.tsx              # Main UI component
│   ├── transitionGraph.ts   # State space & routing logic
│   ├── api.ts               # FastAPI client
│   ├── main.tsx             # Entry point
│   └── index.css            # Tailwind styles
├── package.json
├── vite.config.ts
└── README.md
```

## Extending

### Add New Expression Transition
1. Add to `expressions.json["base_paths"]` in the main face_rig
2. Generate sequences with `generate_all_sequences.py`
3. Update `BASE_PATHS` in `transitionGraph.ts`

### Add New Pose
1. Add to `expressions.json["poses"]`
2. Generate head tilts with `generate_head_tilts.py`
3. Generate pose sequences with `generate_neutral_pose_sequences.py`
4. Update `POSES` array in `App.tsx`

### Debug Routing
Add a dev overlay showing the planned route before playing it:
```tsx
const route = planRoute(currentState, targetState);
console.log("Route:", route.map(s => s.pathId));
```

## Tips

- Start at `neutral @ center` (the default)
- Try expressions first to see direct transitions
- Then try poses to see neutral routing
- Enable resting blink and go idle to see autonomous behavior
- Use Stop/Reset if a transition gets stuck

## Next Steps

- Add audio sync (lip sync to phonemes)
- Add emotion blending (mix expressions)
- Add physics (head bob, breathing)
- Export to sprite sheet for game engines

---

**Made with 🎨 by the Gauntlet AI team**

