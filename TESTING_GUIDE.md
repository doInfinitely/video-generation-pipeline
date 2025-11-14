# Testing Guide

This guide helps you test different parts of the video generation pipeline.

## Testing Without Minimax API Key

You can test the play-by-play storyboard generation without the Minimax API key.

### Setup

1. Create a `.env` file with just your LLM provider key:

```env
# For OpenAI
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai

# OR for Anthropic
ANTHROPIC_API_KEY=your-key-here
LLM_PROVIDER=anthropic
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Run Play-by-Play Test

```bash
python test_play_by_play.py
```

This will:
- ✅ Generate a storyboard using your LLM
- ✅ Show all keyframes with timestamps
- ✅ Demonstrate chunking into 6-second segments
- ✅ Save output to JSON for inspection
- ❌ Skip video generation (no Minimax key needed)

### Available Test Examples

1. **Quicksort Algorithm** - Complex multi-chunk visualization
2. **Simple Ball Animation** - Single 6-second chunk
3. **Photosynthesis Education** - Educational diagram style
4. **Custom Prompt** - Enter your own prompt

### Example Output

```
================================================================================
GENERATED STORYBOARD
================================================================================

Duration: 18000ms (18.0s)
FPS: 24

Global Style:
  Clean flat 2D animation, pale background, rounded rectangle cards

Keyframes (9 total):

  [  0.00s] A horizontal row of 12 cards labeled 0 to 11 in random order
  [  1.00s] The leftmost card is highlighted and rises above the row
  [  1.50s] The second card slides to compare with the pivot
  ...

================================================================================
CHUNKED STORYBOARD (6-second segments)
================================================================================

Chunk 1:
  Global time: 0-6000ms
  Duration: 6000ms
  Keyframes (4):
    [  0.00s] A horizontal row of 12 cards labeled 0 to 11 in random order
    [  1.00s] The leftmost card is highlighted and rises above the row
    ...
```

### Inspect JSON Output

The test creates JSON files with complete storyboard data:

```bash
cat test_quicksort_storyboard.json
```

This shows:
- Original prompt
- Complete storyboard with all keyframes
- Chunked version with local timestamps

## Testing With Minimax API Key

Once you have a Minimax API key, add it to your `.env`:

```env
MINIMAX_API_KEY=your-minimax-key-here
```

Then you can test full video generation:

### Full API Test

```bash
# Start the server in one terminal
python main.py

# Test in another terminal
python test_api.py
```

### Programmatic Test

```bash
python example_usage.py
```

## Testing Individual Components

### Test Configuration

```python
python -c "from src.config import settings; print(f'LLM: {settings.llm_provider}, Chunk: {settings.chunk_duration_ms}ms')"
```

### Test Play-by-Play Agent

```python
from src.play_by_play import PlayByPlayAgent

agent = PlayByPlayAgent()
storyboard = agent.generate_storyboard(
    user_prompt="A red ball bounces across the screen",
    duration_hint_seconds=6
)
print(storyboard.model_dump_json(indent=2))
```

### Test Chunker

```python
from src.play_by_play import PlayByPlayAgent
from src.chunker import chunk_keyframes

agent = PlayByPlayAgent()
storyboard = agent.generate_storyboard("A simple animation", 12)
chunks = chunk_keyframes(storyboard)
print(f"Created {len(chunks)} chunks")
```

### Test Prompt Builder

```python
from src.prompt_builder import build_chunk_prompt
from src.models import ChunkData

chunk = ChunkData(
    chunk_index=0,
    start_global_ms=0,
    end_global_ms=6000,
    keyframes={"0": "Scene starts", "3000": "Action happens"}
)

prompt = build_chunk_prompt(
    user_prompt="My video",
    global_style="2D animation",
    chunk=chunk
)
print(prompt)
```

## Common Issues

### "OPENAI_API_KEY not configured"

Create a `.env` file in the project root:
```bash
cp .env.example .env
# Edit .env and add your API key
```

### "No module named 'src'"

Make sure you're in the project root directory:
```bash
cd /Users/remy/Code/gauntlet_ai/video-generation-pipeline
python test_play_by_play.py
```

### Rate Limits

If you hit API rate limits, the test will fail. Wait a moment and try again with a simpler/shorter prompt.

## What Each Test Validates

| Test | Validates |
|------|-----------|
| `test_play_by_play.py` | LLM integration, storyboard generation, chunking |
| `test_api.py` | Full API flow, video generation, storage |
| `example_usage.py` | Programmatic interface, orchestrator |

## Next Steps After Testing

Once play-by-play generation works:

1. ✅ You know your LLM integration is working
2. ✅ You can see the storyboards that will drive video generation
3. ✅ You understand the chunking process
4. 🔜 Get Minimax API key to enable video generation
5. 🔜 Test full end-to-end video generation

The storyboards from `test_play_by_play.py` show exactly what prompts will be sent to the video generation model!

