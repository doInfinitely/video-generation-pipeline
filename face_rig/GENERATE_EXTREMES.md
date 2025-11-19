# Generate Extreme Expressions

## Overview

The `generate_extreme_expressions.py` script generates "extreme" or "keyframe" versions of all expressions defined in `expressions.json`. These serve as anchor points for tweening and timeline generation.

## Features

✅ **Parallel execution** - Generate multiple expressions simultaneously
✅ **Skip existing** - Only generates missing files by default
✅ **Configurable workers** - Control API concurrency with `--max-workers`
✅ **Multiple poses** - Generate extremes for any pose in your config
✅ **Smart overwrite** - Use `--overwrite` to regenerate specific extremes

## Quick Start

```bash
export OPENAI_API_KEY=sk-...

python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image watercolor_boy_neutral_center.png \
  --pose center \
  --outdir frames/endpoints \
  --max-workers 6
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--config` | ✅ | - | Path to `expressions.json` |
| `--base-image` | ✅ | - | Neutral portrait as base reference |
| `--pose` | ❌ | `center` | Pose ID from config |
| `--outdir` | ✅ | - | Output directory for keyframes |
| `--size` | ❌ | `1024x1536` | Image dimensions |
| `--max-workers` | ❌ | `4` | Parallel OpenAI API calls |
| `--include-neutral` | ❌ | `false` | Generate neutral variant |
| `--overwrite` | ❌ | `false` | Overwrite existing files |

## Output Format

Files are saved as: `<expression_id>__<pose_id>.png`

Examples:
- `neutral__center.png`
- `speaking_ah__center.png`
- `happy_big__tilt_left_small.png`

## Usage Examples

### Generate all extremes for center pose (parallel)

```bash
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image base_neutral.png \
  --pose center \
  --outdir frames/endpoints \
  --max-workers 6
```

Output:
```
[i] Generating 8 expressions with 6 workers...
[✓] speaking_ah -> frames/endpoints/speaking_ah__center.png
[✓] speaking_ee -> frames/endpoints/speaking_ee__center.png
[✓] speaking_uw -> frames/endpoints/speaking_uw__center.png
[✓] happy_big -> frames/endpoints/happy_big__center.png
[✓] sad -> frames/endpoints/sad__center.png
[✓] surprised -> frames/endpoints/surprised__center.png
[✓] angry -> frames/endpoints/angry__center.png
[✓] thinking -> frames/endpoints/thinking__center.png
[i] Done. Success: 8, Failed: 0
```

### Generate for a different pose

```bash
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image base_neutral_tilt_left.png \
  --pose tilt_left_small \
  --outdir frames/endpoints \
  --max-workers 4
```

### Regenerate specific expressions

If you want to regenerate just a few:

```bash
# First, delete the ones you want to redo
rm frames/endpoints/speaking_ah__center.png
rm frames/endpoints/speaking_ee__center.png

# Then rerun (skips existing, generates missing)
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image base_neutral.png \
  --pose center \
  --outdir frames/endpoints \
  --max-workers 2
```

### Regenerate ALL with --overwrite

```bash
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image base_neutral.png \
  --pose center \
  --outdir frames/endpoints \
  --max-workers 6 \
  --overwrite
```

## Performance Tips

### Concurrency

- **Conservative**: `--max-workers 2-4` (safe, slower)
- **Aggressive**: `--max-workers 6-8` (faster, may hit rate limits)
- **Maximum**: `--max-workers 10+` (fastest, watch for API errors)

OpenAI's rate limits vary by account tier. Start conservatively and increase if stable.

### Batching Strategy

If you have many expressions (20+):

```bash
# Run in batches with high concurrency
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image base.png \
  --pose center \
  --outdir frames/endpoints \
  --max-workers 8
```

The script will automatically:
- Skip existing files
- Show progress for each completion
- Report final success/failure counts

## Integration with Timeline Generation

After generating extremes, use them as endpoints for `generate_sequence.py`:

```bash
# 1. Generate extremes (parallel)
python generate_extreme_expressions.py \
  --config expressions.json \
  --base-image neutral_center.png \
  --pose center \
  --outdir frames/endpoints \
  --max-workers 6

# 2. Generate tween sequence
python generate_sequence.py \
  --config expressions.json \
  --base-path neutral_to_speaking_ah \
  --pose center \
  --start-image frames/endpoints/neutral__center.png \
  --end-image frames/endpoints/speaking_ah__center.png \
  --outdir frames/neutral_to_speaking_ah__center \
  --max-depth 3
```

## Error Handling

The script handles errors gracefully:

```
[i] Generating 5 expressions with 4 workers...
[✓] speaking_ah -> frames/endpoints/speaking_ah__center.png
[!] Failed happy_big: 400 Client Error: Bad Request
[✓] speaking_ee -> frames/endpoints/speaking_ee__center.png
[✓] speaking_uw -> frames/endpoints/speaking_uw__center.png
[✓] sad -> frames/endpoints/sad__center.png
[i] Done. Success: 4, Failed: 1
```

Failed expressions can be regenerated individually:

```bash
rm frames/endpoints/happy_big__center.png
python generate_extreme_expressions.py ... # will only generate missing file
```

## Notes

- The script uses OpenAI's `gpt-image-1` edit endpoint
- Each expression is generated independently in parallel
- Base image should be neutral expression at the target pose
- Output images maintain the same style, character identity, and pose
- Only facial expression (mouth, eyes, brows) changes between extremes

