# Quick Start Guide

Get the video generation pipeline running in 5 minutes!

## 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Install FFmpeg (if not already installed)
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
# sudo apt install ffmpeg
```

## 2. Configure API Keys

Create a `.env` file:

```bash
# Minimum required configuration
OPENAI_API_KEY=sk-your-key-here
MINIMAX_API_KEY=your-minimax-key-here

# Optional: Use Anthropic instead
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your-key-here
```

## 3. Start the Server

```bash
python main.py
```

The API will start on `http://localhost:8000`

## 4. Test It Out

### Option A: Use the Web API

Open another terminal and run:
```bash
python test_api.py
```

### Option B: Use the Python Interface

```bash
python example_usage.py
```

### Option C: Use cURL

```bash
# Generate a video
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "A bouncing ball animation",
    "duration_hint_seconds": 6
  }'

# Check status (use the job_id from above)
curl http://localhost:8000/status/YOUR_JOB_ID

# Download video when ready
curl http://localhost:8000/video/YOUR_JOB_ID -o video.mp4
```

## Example Prompts

Try these prompts to see what the system can do:

1. **Algorithm Visualization**
   ```
   Generate a video illustrating bubble sort on an array of 8 colorful bars of different heights, showing comparisons and swaps
   ```

2. **Science Education**
   ```
   Explain how a plant cell performs photosynthesis, showing chloroplasts, sunlight, water, and glucose production
   ```

3. **Simple Animation**
   ```
   A red cube rotating 360 degrees on a white background with soft lighting
   ```

4. **Step-by-Step Tutorial**
   ```
   Show how to tie a shoelace, step by step with clear hand movements and the lace changing color at each step
   ```

## Troubleshooting

**"No module named 'src'"**
- Make sure you're in the project root directory
- Try: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

**"OPENAI_API_KEY not configured"**
- Create a `.env` file with your API keys
- Check that the file is in the project root

**"FFmpeg not found"**
- Install FFmpeg (see step 1)
- Verify with: `ffmpeg -version`

**Video generation is slow**
- This is normal! Each 6-second chunk takes time to generate
- For an 18-second video, expect 3-5 minutes total

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the code in `src/` to understand the architecture
- Customize prompts and styles for your use case
- Add your own video generation models or LLM providers

