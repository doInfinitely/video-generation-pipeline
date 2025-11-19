# Generate All Sequences

## Overview

The `generate_all_sequences.py` script automatically generates tween sequences for all valid combinations of expressions and poses in your project. It discovers your extreme expressions, pairs them according to your config, and generates smooth tweens between them - all in parallel.

## Features

✅ **Auto-discovery** - Scans `frames/endpoints/` and pairs expressions automatically  
✅ **Parallel generation** - Generates multiple tweens simultaneously  
✅ **Manifest creation** - Auto-generates `manifest.json` for each sequence  
✅ **Smart skipping** - Only generates missing frames by default  
✅ **Multiple poses** - Handles all poses with available endpoints  
✅ **UI-ready output** - Creates sequences the React UI can load directly

## Quick Start

```bash
export OPENAI_API_KEY=sk-...

python generate_all_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --times 0.25,0.5,0.75 \
  --max-workers 6
```

## Output Structure

```
frames/sequences/
  neutral_to_speaking_ah__center/
    000.png              # Start (neutral)
    025.png              # Tween at t=0.25
    050.png              # Tween at t=0.50
    075.png              # Tween at t=0.75
    100.png              # End (speaking_ah)
    manifest.json        # Timeline metadata
    
  neutral_to_speaking_ee__center/
    000.png
    025.png
    050.png
    075.png
    100.png
    manifest.json
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--config` | ✅ | - | Path to `expressions.json` |
| `--endpoints-dir` | ❌ | `frames/endpoints` | Directory with extreme expressions |
| `--sequences-dir` | ❌ | `frames/sequences` | Output directory for sequences |
| `--max-depth` | ❌ | `2` | Recursive refinement depth (2 → 0.25, 0.5, 0.75) |
| `--size` | ❌ | `1024x1536` | Image dimensions |
| `--max-workers` | ❌ | `4` | Parallel OpenAI API calls |
| `--overwrite` | ❌ | `false` | Overwrite existing tween frames |

## How It Works

### 1. Discovery Phase

Scans `frames/endpoints/` for files like:
- `neutral__center.png`
- `speaking_ah__center.png`
- `speaking_ee__center.png`

Builds a map: `(expression_id, pose) -> filepath`

### 2. Pairing Phase

Uses `expressions.json` `base_paths` to find valid pairs:

```json
{
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
  ]
}
```

For each `(base_path, pose)` where **both endpoints exist**, creates a sequence.

### 3. Generation Phase (Recursive Binary Subdivision)

For each sequence:
1. **Creates directory**: `frames/sequences/{base_path_id}__{pose}/`
2. **Copies endpoints**: `000.png` (t=0.0) and `100.png` (t=1.0)
3. **Recursively generates midpoints**:
   - **Depth 1**: Generate midpoint between 0 and 1 → t=0.5 (`050.png`)
   - **Depth 2**: Generate midpoints of each segment:
     - Between 0 and 0.5 → t=0.25 (`025.png`)
     - Between 0.5 and 1 → t=0.75 (`075.png`)
   - **Depth 3** (if `max_depth=3`): Generate t=0.125, 0.375, 0.625, 0.875
4. **Writes manifest**: `manifest.json` with metadata

Each depth level generates **all midpoints in parallel** using `ThreadPoolExecutor`.

### 4. Manifest Creation

Each sequence gets a `manifest.json`:

```json
{
  "path_id": "neutral_to_speaking_ah__center",
  "expr_start": "neutral",
  "expr_end": "speaking_ah",
  "pose": "center",
  "frames": [
    {"t": 0.0, "file": "000.png"},
    {"t": 0.25, "file": "025.png"},
    {"t": 0.5, "file": "050.png"},
    {"t": 0.75, "file": "075.png"},
    {"t": 1.0, "file": "100.png"}
  ]
}
```

## Usage Examples

### Generate all sequences (default 3 tweens per sequence)

```bash
python generate_all_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --max-workers 6
```

### Generate with more tweens (denser interpolation)

```bash
python generate_all_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --max-depth 3 \
  --max-workers 8
```

This generates 7 tweens instead of 3:
- **Depth 1**: 0.5
- **Depth 2**: 0.25, 0.75
- **Depth 3**: 0.125, 0.375, 0.625, 0.875

### Generate coarse sequences (fewer tweens)

```bash
python generate_all_sequences.py \
  --config expressions.json \
  --max-depth 1 \
  --max-workers 4
```

This generates only 1 tween at t=0.5

### Regenerate everything

```bash
python generate_all_sequences.py \
  --config expressions.json \
  --overwrite \
  --max-workers 6
```

## Complete Workflow

### Step 1: Generate Extreme Expressions

```bash
# Generate all extreme expressions in parallel
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image neutral_center.png \
  --pose center \
  --outdir frames/endpoints \
  --max-workers 6
```

Output:
```
frames/endpoints/
  neutral__center.png
  speaking_ah__center.png
  speaking_ee__center.png
  speaking_uw__center.png
  ...
```

### Step 2: Generate All Sequences

```bash
# Auto-discover endpoints and generate sequences
python generate_all_sequences.py \
  --config expressions.json \
  --endpoints-dir frames/endpoints \
  --sequences-dir frames/sequences \
  --times 0.25,0.5,0.75 \
  --max-workers 6
```

Output:
```
[i] Found poses in endpoints: ['center']
[i] Will generate 12 tween frames across 4 sequences using 6 workers.
[✓] neutral_to_speaking_ah__center t=0.25 -> 025.png
[✓] neutral_to_speaking_ah__center t=0.50 -> 050.png
[✓] neutral_to_speaking_ee__center t=0.25 -> 025.png
[✓] neutral_to_speaking_ah__center t=0.75 -> 075.png
...
[i] Tween generation completed. Success: 12, Failed: 0
[i] Wrote manifest: frames/sequences/neutral_to_speaking_ah__center/manifest.json
[i] Wrote manifest: frames/sequences/neutral_to_speaking_ee__center/manifest.json
...
```

### Step 3: View in UI

Open the React UI and it automatically discovers the sequences:

```bash
# UI is already running at http://localhost:5174
# Sequences appear in the sidebar automatically
```

## Performance Tips

### Concurrency Tuning

- **Conservative** (2-4 workers): Safer for rate limits
- **Balanced** (6-8 workers): Good for most use cases
- **Aggressive** (10+ workers): Fast but may hit limits

### Optimizing Generation Time

**3 sequences × 3 tweens each = 9 frames:**

| Workers | Estimated Time |
|---------|----------------|
| 2 | ~4.5 minutes |
| 4 | ~2.5 minutes |
| 6 | ~1.5 minutes |
| 8 | ~1 minute |

### Smart Regeneration

Only regenerate what you need:

```bash
# First run - generates everything
python generate_all_sequences.py --config expressions.json --max-workers 6

# Later - only generates missing frames
python generate_all_sequences.py --config expressions.json --max-workers 6

# Force regenerate specific sequence
rm -rf frames/sequences/neutral_to_speaking_ah__center
python generate_all_sequences.py --config expressions.json --max-workers 6
```

## Integration with UI

The generated sequences work seamlessly with the watercolor-rig UI:

1. **Backend auto-discovers** sequences in `frames/sequences/`
2. **GET /timelines** returns all available sequences
3. **GET /timeline/{path_id}** loads the manifest
4. **Frames load** from `frames/sequences/{path_id}/{file}`

The UI can then:
- Load and preview sequences
- Play them back at variable FPS
- Regenerate individual frames using the recursive algorithm

## Troubleshooting

### No sequences generated

```
[i] No sequences to generate (no matching endpoint pairs).
```

**Solution**: Check that:
- Endpoints exist in `frames/endpoints/`
- Filenames match pattern: `{expr_id}__{pose}.png`
- Both start and end expressions exist for each base_path

### Some frames skipped

```
[i] Tween exists, skipping: neutral_to_speaking_ah__center t=0.50 -> 050.png
```

**Solution**: This is normal! Use `--overwrite` to regenerate.

### API errors during generation

```
[!] Failed neutral_to_speaking_ah__center t=0.50: 429 Too Many Requests
```

**Solution**: Reduce `--max-workers` or add retry logic.

## Notes

- Endpoints are copied, not symlinked, so sequences are self-contained
- Manifest files are overwritten on each run
- The script is idempotent - safe to run multiple times
- Times are rounded to nearest integer (e.g., t=0.25 → `025.png`)
- Uses OpenAI's `gpt-image-1` with two reference images for interpolation

