# Video Generation Pipeline

An AI-powered video generation pipeline that creates educational and explanatory videos using play-by-play storyboarding and the Minimax video-01 model.

## Overview

This system takes a text prompt (e.g., "Generate a video illustrating quicksort") and produces a complete video by:

1. **Play-by-Play Generation**: Using an LLM (OpenAI GPT-4 or Anthropic Claude) to generate a structured timeline of keyframes
2. **Chunking**: Splitting the timeline into 6-second segments (matching Minimax video-01's output)
3. **Video Generation**: Generating each chunk with Minimax video-01, chaining the last frame as the first frame of the next chunk
4. **Concatenation**: Stitching all chunks together into a final video

## Architecture

```
User Prompt → Play-by-Play Agent (LLM) → Chunker → Video Generator (Minimax) → Video Processing → Final Video
```

### Components

- **FastAPI Backend**: REST API for video generation requests
- **Play-by-Play Agent**: LLM integration for storyboard generation
- **Chunker**: Splits keyframes into 6-second segments
- **Video Generator**: Interfaces with Minimax video-01 API
- **Video Processing**: FFmpeg-based frame extraction and concatenation

## Installation

### Prerequisites

- Python 3.9+
- FFmpeg (for video processing)
- Redis (optional, for production task queuing)

### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Install Python Dependencies

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
# LLM Provider Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4-turbo-preview  # or claude-3-opus-20240229

# Minimax API Configuration
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_API_URL=https://api.minimax.chat/v1/video_generation

# Video Settings
DEFAULT_FPS=24
CHUNK_DURATION_MS=6000
VIDEO_DURATION_SECONDS=6

# Storage Configuration
VIDEO_STORAGE_PATH=./storage/videos
TEMP_STORAGE_PATH=./storage/temp

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

## Usage

### Start the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### Generate Video

```bash
POST /generate
```

Request body:
```json
{
  "user_prompt": "Generate a video illustrating quicksort on an array of numbers",
  "duration_hint_seconds": 18,
  "style_preference": "Clean 2D animation",
  "reference_image": null
}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Video generation started. Use /status/{job_id} to check progress."
}
```

#### Check Status

```bash
GET /status/{job_id}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 0.5,
  "current_chunk": 2,
  "total_chunks": 3,
  "video_url": null,
  "error_message": null
}
```

#### Download Video

```bash
GET /video/{job_id}
```

Returns the generated MP4 video file.

### Programmatic Usage

```python
import asyncio
from src.orchestrator import generate_video_for_prompt

async def main():
    video_path = await generate_video_for_prompt(
        user_prompt="Explain how a binary search tree works",
        duration_hint_seconds=12,
        style_preference="Educational diagram style"
    )
    print(f"Video saved to: {video_path}")

asyncio.run(main())
```

### Example Scripts

Run the included examples:

```bash
# Interactive example selector
python example_usage.py

# API test script
python test_api.py
```

## Project Structure

```
video-generation-pipeline/
├── src/
│   ├── __init__.py
│   ├── api.py                 # FastAPI application
│   ├── orchestrator.py        # Main orchestration logic
│   ├── play_by_play.py        # LLM integration for storyboards
│   ├── chunker.py             # Keyframe chunking
│   ├── prompt_builder.py      # Prompt construction for video gen
│   ├── video_generator.py     # Minimax API client
│   ├── video_processing.py    # FFmpeg utilities
│   ├── models.py              # Pydantic data models
│   └── config.py              # Configuration management
├── storage/
│   ├── videos/                # Final generated videos
│   └── temp/                  # Temporary chunk files
├── main.py                    # API entry point
├── example_usage.py           # Usage examples
├── test_api.py               # API tests
├── requirements.txt           # Python dependencies
├── brainstorm.md             # Original design document
└── README.md                 # This file
```

## How It Works

### 1. Play-by-Play Generation

The LLM receives your prompt and generates a structured JSON storyboard:

```json
{
  "duration_ms": 18000,
  "fps": 24,
  "global_style": "Clean flat 2D animation, colorful cards",
  "keyframes": {
    "0": "A horizontal row of 12 cards labeled 0 to 11 in random order",
    "1000": "The leftmost card is highlighted and rises above the row",
    "1500": "The second card slides to compare with the pivot",
    ...
  }
}
```

### 2. Chunking

The timeline is split into 6-second chunks, with keyframe timestamps adjusted to be relative to each chunk's start:

```
Chunk 0: 0-5999ms (keyframes: 0, 1000, 1500, 2000, ...)
Chunk 1: 6000-11999ms (keyframes: 0, 2000, 4000, ...)
Chunk 2: 12000-17999ms (keyframes: 0, 1000, ...)
```

### 3. Video Generation

For each chunk:
1. Build a detailed text prompt from the keyframes
2. Call Minimax video-01 API with:
   - The text prompt
   - The last frame from the previous chunk (for continuity)
3. Receive a 6-second video clip
4. Extract the last frame for the next chunk

### 4. Concatenation

All chunks are concatenated using FFmpeg into a single seamless video.

## Development

### Running Tests

```bash
pytest
```

### Adding New LLM Providers

Extend `src/play_by_play.py` with additional provider logic.

### Customizing Video Generation

Modify `src/video_generator.py` to adjust Minimax API parameters or switch to alternative video generation APIs.

## Future Enhancements

- **Audio & Narration**: Generate voiceover scripts and TTS audio aligned with keyframes
- **Subtitles**: Automatic subtitle generation synced to narration
- **Task Queue**: Celery + Redis for distributed processing
- **Frontend**: Web UI for easier interaction
- **Cloud Storage**: S3/GCS integration for video storage
- **Advanced Prompting**: Fine-tuned prompt templates for different video styles

## Troubleshooting

### FFmpeg Not Found

Ensure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

### API Key Errors

Verify your `.env` file has valid API keys for your chosen LLM provider and Minimax.

### Video Generation Timeout

Adjust the timeout in `src/video_generator.py` if generation takes longer than expected.

## License

MIT License - See LICENSE file for details

## Credits

Design concept from the brainstorm document. Implementation uses:
- FastAPI for the REST API
- OpenAI/Anthropic for play-by-play generation
- Minimax video-01 for video generation
- FFmpeg for video processing

