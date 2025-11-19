# Setup with Replicate

Since you have a Replicate API key, you can now test the full video generation pipeline!

## ⚠️ Security Note

You shared your API key in the conversation. Consider rotating it after testing:
- Go to https://replicate.com/account/api-tokens
- Delete the old token and create a new one

## Quick Setup

### 1. Install Replicate Package

```bash
pip install replicate --break-system-packages
```

### 2. Configure Environment

Copy the Replicate configuration:

```bash
cp .env.replicate .env
```

Then edit `.env` and add your OpenAI key:

```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

The Replicate key is already configured in the file.

### 3. Test Play-by-Play First

Before testing video generation, verify play-by-play works:

```bash
python test_play_by_play.py
```

Select option 2 (Simple Ball Animation) for a quick test.

### 4. Test Full Video Generation

Once play-by-play works, test the full pipeline:

```bash
python example_usage.py
```

Select option 2 (Simple Ball Animation) - this will generate just 6 seconds (1 chunk) so it's faster.

## How It Works with Replicate

The system now supports two video generation backends:

- **Minimax Direct API** - If you had a direct Minimax key
- **Replicate** - Uses Replicate's hosted Minimax video-01 model ✅ (You have this!)

Your `.env` file controls which one is used:

```env
VIDEO_PROVIDER=replicate  # or "minimax"
```

## Available Models on Replicate

You can try different video models by changing `REPLICATE_MODEL` in `.env`:

```env
# Minimax video-01 (default)
REPLICATE_MODEL=minimax/video-01

# Other models you might want to try:
# REPLICATE_MODEL=stability-ai/stable-video-diffusion
# REPLICATE_MODEL=anotherjesse/zeroscope-v2-xl
```

## Expected Behavior

### Play-by-Play Test (Fast)
- ⏱️ Takes 10-30 seconds
- ✅ Shows generated storyboard with keyframes
- ✅ Shows chunks
- 💰 Costs: ~$0.01 (LLM API call)

### Full Video Generation (Slower)
- ⏱️ Takes 2-5 minutes per 6-second chunk
- ✅ Generates actual MP4 video
- 💰 Costs: Varies by model (check Replicate pricing)

## Troubleshooting

### "Replicate package not installed"

```bash
pip install replicate --break-system-packages
```

### "REPLICATE_API_TOKEN not set"

Make sure your `.env` file has:
```env
REPLICATE_API_TOKEN=your-replicate-token-here
```

### Model not found

Check available models at https://replicate.com/collections/video-generation

### Video generation takes forever

This is normal! Video generation is computationally expensive:
- 6 seconds of video ≈ 2-5 minutes to generate
- 18 seconds of video (3 chunks) ≈ 6-15 minutes total

Start with the simple ball animation (option 2) which is just one 6-second chunk.

## Cost Estimates

Approximate costs per video generation:

| Component | Cost per call |
|-----------|---------------|
| Play-by-Play (GPT-4) | ~$0.01-0.05 |
| Video Gen (Minimax on Replicate) | Check Replicate pricing |
| Total for 6s video | Variable |

Always check current pricing at:
- OpenAI: https://openai.com/pricing
- Replicate: https://replicate.com/pricing

## Next Steps

1. ✅ Test play-by-play generation
2. ✅ Test full video generation with simple prompt
3. ✅ Try the quicksort example
4. 🎨 Experiment with different prompts and styles
5. 🔊 Add audio/narration (future enhancement)

Enjoy creating AI-generated videos! 🎬

