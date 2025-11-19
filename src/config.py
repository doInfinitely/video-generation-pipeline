"""Configuration management for the video generation pipeline."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = "gpt-4-turbo-preview"  # or claude-3-opus-20240229

    # Video Generation API Configuration
    video_provider: Literal["minimax", "replicate"] = "replicate"
    
    # Minimax API Configuration
    minimax_api_key: str = ""
    minimax_api_url: str = "https://api.minimax.chat/v1/video_generation"
    
    # Replicate API Configuration
    replicate_api_token: str = ""
    replicate_model: str = "minimax/video-01"  # or other video models on Replicate
    use_simple_prompts: bool = True  # Use simplified prompts for video models

    # Video Settings
    default_fps: int = 24
    chunk_duration_ms: int = 6000
    video_duration_seconds: int = 6

    # Storage Configuration
    video_storage_path: Path = Path("./storage/videos")
    temp_storage_path: Path = Path("./storage/temp")

    # Redis Configuration (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure storage directories exist
        self.video_storage_path.mkdir(parents=True, exist_ok=True)
        self.temp_storage_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

