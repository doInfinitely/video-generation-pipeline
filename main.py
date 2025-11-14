"""Main entry point for the video generation pipeline API."""

import uvicorn
from loguru import logger

from src.config import settings

if __name__ == "__main__":
    logger.info("Starting Video Generation Pipeline API...")
    logger.info(f"Configuration: {settings.llm_provider} LLM, {settings.chunk_duration_ms}ms chunks")
    
    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )

