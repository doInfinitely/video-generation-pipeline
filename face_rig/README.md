# Watercolor Face Rig Pipeline

Complete pipeline for generating animated facial expression sequences using OpenAI's `gpt-image-1` model.

## 🎯 Quick Start

```bash
export OPENAI_API_KEY=sk-...
cd face_rig

# 1. Generate extreme expressions at center pose (5-10 min)
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image watercolor_boy_greenscreen.png \
  --pose center \
  --outdir frames/endpoints \
  --include-neutral \
  --max-workers 6

# 2. Generate all head tilts (5-10 min)
python generate_head_tilts.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --base-neutral watercolor_boy_greenscreen.png \
  --source-pose center \
  --max-workers 6

# 3. Generate expression tween sequences (10-20 min)
python generate_all_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --max-depth 2 \
  --max-workers 6

# 4. Generate neutral pose sequences (5-10 min)
python generate_neutral_pose_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --source-pose center \
  --max-depth 2 \
  --max-workers 6

# 5. Start backend server
uvicorn server:app --reload --port 8000

# 6. Start sequence editor UI (in another terminal)
cd watercolor-rig
npm run dev

# 7. Start character player (optional, in another terminal)
cd character-player
npm install
npm run dev
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [COMPLETE_WORKFLOW.md](./COMPLETE_WORKFLOW.md) | Full end-to-end workflow guide |
| [GENERATE_EXTREMES.md](./GENERATE_EXTREMES.md) | Generate extreme expression keyframes |
| [GENERATE_HEAD_TILTS.md](./GENERATE_HEAD_TILTS.md) | Multiply expressions across head poses |
| [GENERATE_SEQUENCES.md](./GENERATE_SEQUENCES.md) | Generate expression sequences recursively |
| [GENERATE_POSE_SEQUENCES.md](./GENERATE_POSE_SEQUENCES.md) | Generate neutral pose transitions |

## 🧩 Pipeline Components

### 1. Expression Generation (`generate_extreme_expressions.py`)

**Purpose:** Generate keyframe expressions at a single pose

**Input:**
- Base neutral portrait
- `expressions.json` config

**Output:**
- `frames/endpoints/<expr_id>__<pose>.png`

**Example:**
```bash
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image watercolor_boy_greenscreen.png \
  --pose center \
  --max-workers 6
```

**Result:**
```
frames/endpoints/
├── neutral__center.png
├── speaking_ah__center.png
├── speaking_ee__center.png
├── speaking_uw__center.png
├── happy_soft__center.png
└── ...
```

### 2. Head Tilt Generation (`generate_head_tilts.py`)

**Purpose:** Multiply **each extreme expression** across all head poses

**Input:**
- **All extreme expressions** at source pose (e.g., `speaking_ah__center.png`, `speaking_ee__center.png`, etc.)
- `expressions.json["poses"]` array

**Output:**
- Full expression × pose matrix

**Example:**
```bash
python generate_head_tilts.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --base-neutral watercolor_boy_greenscreen.png \
  --source-pose center \
  --max-workers 6
```

**Result:**
```
frames/endpoints/
├── neutral__center.png
├── neutral__tilt_left_small.png
├── neutral__tilt_right_small.png
├── neutral__nod_up_small.png
├── neutral__nod_down_small.png
├── speaking_ah__center.png
├── speaking_ah__tilt_left_small.png
└── ...
```

### 3. Sequence Generation (`generate_all_sequences.py`)

**Purpose:** Generate interpolated tween sequences

**Input:**
- Expression × pose matrix from `frames/endpoints/`
- `expressions.json["base_paths"]` defining transitions

**Output:**
- Tween sequences with manifests

**Example:**
```bash
python generate_all_sequences.py \
  --config expressions.json \
  --max-depth 2 \
  --max-workers 6
```

**Result:**
```
frames/sequences/
├── neutral_to_speaking_ah__center/
│   ├── 000.png  (t=0.0)
│   ├── 025.png  (t=0.25)
│   ├── 050.png  (t=0.5)
│   ├── 075.png  (t=0.75)
│   ├── 100.png  (t=1.0)
│   └── manifest.json
├── neutral_to_speaking_ah__tilt_left_small/
│   └── ...
└── ...
```

### 4. Backend API (`server.py`)

**Purpose:** Serve sequences and provide regeneration API

**Features:**
- Auto-discovers sequences
- Serves frame images
- Provides `/timeline/{path_id}/regenerate` endpoint
- Anchor-based regeneration

**Usage:**
```bash
uvicorn server:app --reload --port 8000
```

### 5. React Sequence Editor (`watercolor-rig`)

**Purpose:** Preview and refine sequences

**Features:**
- Timeline viewer
- Playback controls
- Single-frame regeneration
- Range regeneration with recursive binary subdivision

**Usage:**
```bash
cd watercolor-rig
npm run dev  # Opens at http://localhost:5174
```

### 6. Character Player (`character-player`)

**Purpose:** Interactive state machine for testing character animations

**Features:**
- Click buttons to change expression/pose
- Automatic routing between states (detours via neutral when needed)
- Resting blink behavior when idle
- Visual state display

**Usage:**
```bash
cd character-player
npm install
npm run dev  # Opens at http://localhost:5175
```

**State Space:**
- **Expressions:** neutral, happy_soft, happy_big, speaking_ah, surprised_ah, speaking_ee, speaking_uw, oh_round, concerned, blink_closed
- **Poses:** center, tilt_left_small, tilt_right_small, nod_up_small, nod_down_small

**Routing Logic:**
- Same pose + direct path → play that sequence
- Same pose + no direct path → detour via neutral
- Different pose → route via neutral pose transition

## 🎨 Expression × Pose Matrix

The pipeline generates a full matrix of combinations:

| Expression | center | tilt_left | tilt_right | nod_up | nod_down |
|------------|--------|-----------|------------|--------|----------|
| neutral | ✓ | ✓ | ✓ | ✓ | ✓ |
| speaking_ah | ✓ | ✓ | ✓ | ✓ | ✓ |
| speaking_ee | ✓ | ✓ | ✓ | ✓ | ✓ |
| speaking_uw | ✓ | ✓ | ✓ | ✓ | ✓ |
| happy_soft | ✓ | ✓ | ✓ | ✓ | ✓ |
| happy_big | ✓ | ✓ | ✓ | ✓ | ✓ |
| concerned | ✓ | ✓ | ✓ | ✓ | ✓ |
| blink_closed | ✓ | ✓ | ✓ | ✓ | ✓ |

**Then**, for each base_path (e.g., `neutral_to_speaking_ah`) × each pose:
- Full tween sequence with 3-15 frames (depending on `max_depth`)

## 🔄 Recursive Binary Subdivision

Sequences are generated using recursive midpoint refinement:

```
max_depth=1:  0.0 ────────── 0.5 ────────── 1.0
                        (1 tween)

max_depth=2:  0.0 ── 0.25 ── 0.5 ── 0.75 ── 1.0
                      (3 tweens)

max_depth=3:  0.0─0.125─0.25─0.375─0.5─0.625─0.75─0.875─1.0
                          (7 tweens)
```

**Formula:** `2^max_depth - 1` tweens

**Generation order:**
1. Depth 1: Generate midpoint (0.5)
2. Depth 2: Generate quarters (0.25, 0.75)
3. Depth 3: Generate eighths (0.125, 0.375, 0.625, 0.875)

All frames at each depth are generated **in parallel**.

## 📁 Directory Structure

```
face_rig/
├── expressions.json              # Config: expressions, poses, base_paths
├── watercolor_boy_greenscreen.png  # Base neutral portrait
│
├── generate_extreme_expressions.py  # Step 1: Generate extremes
├── generate_head_tilts.py          # Step 2: Generate head tilts
├── generate_all_sequences.py       # Step 3: Generate sequences
├── generate_sequence.py            # Helper: Single sequence generation
│
├── server.py                       # FastAPI backend
│
├── frames/
│   ├── endpoints/                  # Extreme expressions
│   │   ├── neutral__center.png
│   │   ├── speaking_ah__center.png
│   │   └── ...
│   └── sequences/                  # Tween sequences
│       ├── neutral_to_speaking_ah__center/
│       │   ├── 000.png
│       │   ├── 025.png
│       │   ├── 050.png
│       │   ├── 075.png
│       │   ├── 100.png
│       │   └── manifest.json
│       └── ...
│
├── watercolor-rig/                 # React sequence editor
│   ├── src/
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   └── TimelineViewer.tsx
│   │   └── index.css
│   └── package.json
│
└── character-player/               # React character state machine
    ├── src/
    │   ├── api.ts
    │   ├── App.tsx
    │   ├── transitionGraph.ts
    │   ├── main.tsx
    │   └── index.css
    └── package.json
```

## ⚙️ Configuration

### expressions.json

```json
{
  "axes": {
    "mouth": ["neutral", "smile_soft", "smile_big", "ah", "ee", "uw", "frown"],
    "eyes": ["neutral", "wide", "squint", "blink_closed"],
    "brows": ["neutral", "raise", "furrow"]
  },
  "poses": [
    "center",
    "tilt_left_small",
    "tilt_right_small",
    "nod_down_small",
    "nod_up_small"
  ],
  "expressions": {
    "neutral": { "mouth": "neutral", "eyes": "neutral", "brows": "neutral" },
    "speaking_ah": { "mouth": "ah", "eyes": "neutral", "brows": "neutral" },
    "speaking_ee": { "mouth": "ee", "eyes": "neutral", "brows": "neutral" },
    "speaking_uw": { "mouth": "uw", "eyes": "neutral", "brows": "neutral" },
    "happy_soft": { "mouth": "smile_soft", "eyes": "squint", "brows": "neutral" },
    "happy_big": { "mouth": "smile_big", "eyes": "squint", "brows": "raise" },
    "concerned": { "mouth": "frown", "eyes": "squint", "brows": "furrow" },
    "blink_closed": { "mouth": "neutral", "eyes": "blink_closed", "brows": "neutral" }
  },
  "base_paths": [
    { "id": "neutral_to_speaking_ah", "start": "neutral", "end": "speaking_ah" },
    { "id": "neutral_to_speaking_ee", "start": "neutral", "end": "speaking_ee" },
    { "id": "neutral_to_speaking_uw", "start": "neutral", "end": "speaking_uw" },
    { "id": "neutral_to_happy_soft", "start": "neutral", "end": "happy_soft" },
    { "id": "happy_soft_to_happy_big", "start": "happy_soft", "end": "happy_big" },
    { "id": "neutral_to_concerned", "start": "neutral", "end": "concerned" },
    { "id": "neutral_to_blink", "start": "neutral", "end": "blink_closed" }
  ]
}
```

## 💰 Cost Estimation

**For 8 expressions × 5 poses:**
- Step 1: 8 extremes at center (including neutral) = 8 calls × $0.10 = **$0.80**
- Step 2: 8 × 4 head tilts = 32 calls × $0.10 = **$3.20**
- Step 3: 7 base_paths × 5 poses × 3 tweens = 105 calls × $0.10 = **$10.50**
- Step 4: 4 pose sequences × 3 tweens = 12 calls × $0.10 = **$1.20**
- **Total: ~$15.70**

**Denser sequences (`max_depth=3`):**
- Step 3: 7 × 5 × 7 = 245 calls = **$24.50**
- Step 4: 4 × 7 = 28 calls = **$2.80**
- **Total: ~$31.30**

## 🛠️ Development

### Backend hot reload
```bash
cd face_rig
uvicorn server:app --reload --port 8000
```

### Frontend hot reload
```bash
cd face_rig/watercolor-rig
npm run dev
```

### Regenerate single sequence
```bash
python generate_sequence.py \
  --config expressions.json \
  --base-path neutral_to_speaking_ah \
  --pose center \
  --start-image frames/endpoints/neutral__center.png \
  --end-image frames/endpoints/speaking_ah__center.png \
  --outdir frames/sequences/neutral_to_speaking_ah__center \
  --max-depth 2
```

## 🚀 Production Deployment

1. **Generate all assets offline**
2. **Deploy static frames + manifests**
3. **Deploy backend API** (optional; can serve statically)
4. **Deploy React UI**

The regeneration endpoints are optional for production—you can pre-generate everything and just serve static files.

## 📖 Next Steps

1. Read [COMPLETE_WORKFLOW.md](./COMPLETE_WORKFLOW.md) for detailed walkthrough
2. Review [expressions.json](./expressions.json) configuration
3. Run the 4-step generation pipeline
4. Preview in `watercolor-rig` sequence editor and refine as needed
5. Test state machine behavior in `character-player`
6. Export production sequences

## 🐛 Troubleshooting

### "The api_key client option must be set"
```bash
export OPENAI_API_KEY=sk-...
```

### "Missing source pose for expr 'X'"
Generate extreme expressions first:
```bash
python generate_extreme_expressions.py --pose center
```

### "No sequences to generate"
Check that `frames/endpoints/` has matching pairs defined in `base_paths`.

### UI not updating after regeneration
Images are cached. The UI appends `?v=timestamp` to bust cache, but you may need to hard-refresh browser.

### Frames look inconsistent
Try:
- Higher resolution (`--size 1024x1536`)
- More specific prompts in description tables
- Regenerate with different anchors in UI

---

**Made with 🎨 by the Gauntlet AI team**

