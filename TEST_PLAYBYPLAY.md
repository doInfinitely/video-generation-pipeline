# Test Play-by-Play Generation (No Minimax Required)

Quick guide to test storyboard generation without the Minimax API key.

## Quick Start (3 steps)

### 1. Setup

```bash
# Run the setup script
./setup_for_testing.sh

# OR manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Add Your LLM API Key

Create or edit `.env`:

```env
# For OpenAI (recommended)
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai

# OR for Anthropic
ANTHROPIC_API_KEY=your-key-here  
LLM_PROVIDER=anthropic
```

### 3. Run Test

```bash
python test_play_by_play.py
```

## What You'll See

The test will:

1. **Generate a storyboard** - The LLM creates a detailed timeline with keyframes
2. **Display keyframes** - Shows what happens at each timestamp
3. **Show chunks** - Demonstrates how it splits into 6-second segments
4. **Save JSON** - Creates a file you can inspect

Example output:

```
================================================================================
GENERATED STORYBOARD
================================================================================

Duration: 18000ms (18.0s)
FPS: 24

Global Style:
  Clean flat 2D animation, pale background, each number in a rounded rectangle card

Keyframes (9 total):

  [  0.00s] A horizontal row of 12 cards labeled 0 to 11 in random order
  [  1.00s] The leftmost card is highlighted, rises above the row
  [  1.50s] The second card slides to compare with the pivot
  [  2.00s] The third card moves past the pivot to show it is greater
  [  4.00s] The pivot card glides to the correct sorted position
  [  6.00s] Zoom into the left subarray for next partition
  [  8.00s] Left subarray processes with new pivot
  [ 12.00s] Sorting repeats on smaller subarrays
  [ 16.00s] Full array now sorted from 0 to 11, cards glowing

================================================================================
CHUNKED STORYBOARD (6-second segments)
================================================================================

Chunk 1:
  Global time: 0-6000ms
  Duration: 6000ms
  Keyframes (6):
    [  0.00s] A horizontal row of 12 cards labeled 0 to 11 in random order
    [  1.00s] The leftmost card is highlighted, rises above the row
    ...

Chunk 2:
  Global time: 6000-12000ms
  Duration: 6000ms
  Keyframes (2):
    [  0.00s] Zoom into the left subarray for next partition
    [  2.00s] Left subarray processes with new pivot

Chunk 3:
  Global time: 12000-18000ms
  Duration: 6000ms
  Keyframes (2):
    [  0.00s] Sorting repeats on smaller subarrays
    [  4.00s] Full array now sorted from 0 to 11, cards glowing
```

## Test Options

When you run `python test_play_by_play.py`, you can choose:

1. **Quicksort Algorithm** - The example from the brainstorm (18 seconds, 3 chunks)
2. **Simple Ball Animation** - Quick test (6 seconds, 1 chunk)
3. **Photosynthesis Education** - Science education example (12 seconds, 2 chunks)
4. **Custom Prompt** - Enter your own prompt interactively

## What This Tests

✅ LLM API integration (OpenAI or Anthropic)  
✅ Storyboard generation with keyframes  
✅ Keyframe chunking into 6-second segments  
✅ Prompt building for video generation  
✅ JSON export of storyboards  

❌ Video generation (requires Minimax API key)  
❌ Frame extraction  
❌ Video concatenation  

## Example JSON Output

The test creates `test_quicksort_storyboard.json`:

```json
{
  "prompt": "Generate a video illustrating quicksort...",
  "storyboard": {
    "duration_ms": 18000,
    "fps": 24,
    "global_style": "Clean flat 2D animation...",
    "keyframes": {
      "0": "A horizontal row of 12 cards...",
      "1000": "The leftmost card is highlighted...",
      ...
    }
  },
  "chunks": [
    {
      "chunk_index": 0,
      "start_global_ms": 0,
      "end_global_ms": 6000,
      "keyframes": {
        "0": "A horizontal row of 12 cards...",
        "1000": "The leftmost card is highlighted...",
        ...
      }
    },
    ...
  ]
}
```

## Understanding the Output

### Storyboard Structure

- **duration_ms**: Total video length in milliseconds
- **fps**: Frame rate (usually 24)
- **global_style**: Consistent visual style applied to all chunks
- **keyframes**: Dictionary mapping time → visual description

### Chunks

Each chunk represents a 6-second video segment:
- **chunk_index**: Position in sequence (0, 1, 2, ...)
- **start_global_ms/end_global_ms**: Position in full timeline
- **keyframes**: Same keyframes but with LOCAL timestamps (0-6000ms)

This is exactly what gets sent to the video generation model!

## Try Your Own Prompts

Run with option 4 (Custom Prompt) and try:

- "A tree growing from a seed through all four seasons"
- "Binary search algorithm on a sorted array"
- "Water cycle: evaporation, condensation, precipitation"
- "DNA replication showing the double helix unzipping"

## Next Steps

Once you're happy with the storyboard generation:

1. ✅ You know the LLM integration works
2. ✅ You can see what prompts will be sent to video generation
3. ✅ You understand the chunking process
4. 🔜 Get a Minimax API key
5. 🔜 Test full video generation with `python test_api.py`

## Troubleshooting

**"OPENAI_API_KEY not configured"**
- Make sure `.env` file exists in the project root
- Check that you've added your API key to `.env`

**"Rate limit exceeded"**
- You're making too many requests
- Wait a minute and try again
- Use a shorter duration_hint_seconds

**Storyboard looks weird**
- The LLM output can vary
- Try adjusting your prompt to be more specific
- Specify a clear style_preference

**Want to use Claude instead of GPT-4?**
```env
ANTHROPIC_API_KEY=your-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
```

