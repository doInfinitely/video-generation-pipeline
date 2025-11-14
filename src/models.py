"""Data models and schemas for the video generation pipeline."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class Storyboard(BaseModel):
    """Storyboard output from the play-by-play agent."""

    duration_ms: int = Field(..., description="Total duration in milliseconds")
    fps: int = Field(default=24, description="Frames per second")
    global_style: str = Field(..., description="Visual style and consistency description")
    keyframes: Dict[str, str] = Field(
        ...,
        description="Mapping of timestamp (ms as string) to visual description"
    )


class ChunkData(BaseModel):
    """Data for a single 6-second video chunk."""

    chunk_index: int = Field(..., description="Index of this chunk (0-based)")
    start_global_ms: int = Field(..., description="Start time in global timeline (ms)")
    end_global_ms: int = Field(..., description="End time in global timeline (ms)")
    keyframes: Dict[str, str] = Field(
        ...,
        description="Keyframes with local timestamps (0-based within this chunk)"
    )


class VideoGenerationRequest(BaseModel):
    """Request to generate a video from a user prompt."""

    user_prompt: str = Field(..., description="User's description of the video to generate")
    reference_image: Optional[str] = Field(
        None,
        description="Optional base64-encoded reference/subject image"
    )
    duration_hint_seconds: Optional[int] = Field(
        None,
        description="Optional hint for desired video duration"
    )
    style_preference: Optional[str] = Field(
        None,
        description="Optional style preference (e.g., '2D animation', 'realistic', etc.)"
    )


class VideoGenerationResponse(BaseModel):
    """Response from video generation."""

    job_id: str = Field(..., description="Unique identifier for this generation job")
    status: str = Field(..., description="Current status of the job")
    message: str = Field(..., description="Human-readable status message")


class VideoGenerationStatus(BaseModel):
    """Status of a video generation job."""

    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None


class ChunkPromptData(BaseModel):
    """Data for building a prompt for a video chunk."""

    user_prompt: str
    global_style: str
    chunk: ChunkData
    previous_context: Optional[str] = None

