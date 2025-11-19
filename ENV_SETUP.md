# Environment Variable Quick Reference

## The Correct Variable Name

Use **`REPLICATE_API_TOKEN`** (not `REPLICATE_API_KEY`)

The Replicate SDK expects `REPLICATE_API_TOKEN`.

## Your `.env` File Should Look Like This:

```env
# LLM Provider
OPENAI_API_KEY=sk-your-openai-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Video Generation
VIDEO_PROVIDER=replicate

# Replicate (THIS IS THE CORRECT VARIABLE NAME)
REPLICATE_API_TOKEN=your-replicate-token-here
REPLICATE_MODEL=minimax/video-01

# Video Settings
DEFAULT_FPS=24
CHUNK_DURATION_MS=6000
VIDEO_DURATION_SECONDS=6

# Storage
VIDEO_STORAGE_PATH=./storage/videos
TEMP_STORAGE_PATH=./storage/temp

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

## Quick Setup Command:

```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-openai-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
VIDEO_PROVIDER=replicate
REPLICATE_API_TOKEN=your-replicate-token-here
REPLICATE_MODEL=minimax/video-01
DEFAULT_FPS=24
CHUNK_DURATION_MS=6000
VIDEO_DURATION_SECONDS=6
VIDEO_STORAGE_PATH=./storage/videos
TEMP_STORAGE_PATH=./storage/temp
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
EOF
```

Then edit the file to add your actual OpenAI key:
```bash
nano .env  # or use your preferred editor
```

## Summary

✅ **REPLICATE_API_TOKEN** - Correct  
❌ **REPLICATE_API_KEY** - Wrong (don't use this)

