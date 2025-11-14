"""FastAPI application for the video generation service."""

import uuid
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import settings
from .models import (
    VideoGenerationRequest,
    VideoGenerationResponse,
    VideoGenerationStatus,
)
from .orchestrator import VideoOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="Video Generation Pipeline",
    description="AI-powered video generation using play-by-play storyboarding",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (use Redis/database in production)
jobs: Dict[str, VideoGenerationStatus] = {}

# Orchestrator instance
orchestrator = VideoOrchestrator()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Video Generation Pipeline",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Generate a video from a user prompt.

    This endpoint starts the video generation process in the background
    and returns a job ID that can be used to check status and retrieve
    the final video.
    """
    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    # Initialize job status
    jobs[job_id] = VideoGenerationStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
    )

    # Start video generation in background
    background_tasks.add_task(
        _generate_video_background,
        job_id=job_id,
        request=request,
    )

    logger.info(f"Created video generation job {job_id}")

    return VideoGenerationResponse(
        job_id=job_id,
        status="pending",
        message=f"Video generation started. Use /status/{job_id} to check progress.",
    )


@app.get("/status/{job_id}", response_model=VideoGenerationStatus)
async def get_job_status(job_id: str):
    """Get the status of a video generation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]


@app.get("/video/{job_id}")
async def get_video(job_id: str):
    """Download the generated video."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready. Current status: {job.status}",
        )

    if not job.video_url:
        raise HTTPException(status_code=500, detail="Video URL not available")

    # The video_url is actually a local path in this implementation
    video_path = Path(job.video_url)

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"generated_video_{job_id}.mp4",
    )


async def _generate_video_background(job_id: str, request: VideoGenerationRequest):
    """Background task to generate a video."""
    try:
        # Update status to processing
        jobs[job_id].status = "processing"
        jobs[job_id].progress = 0.1

        logger.info(f"Starting video generation for job {job_id}")

        # Generate the video
        video_path = await orchestrator.generate_video(request, job_id=job_id)

        # Update status to completed
        jobs[job_id].status = "completed"
        jobs[job_id].progress = 1.0
        jobs[job_id].video_url = str(video_path)

        logger.success(f"Video generation completed for job {job_id}")

    except Exception as e:
        logger.error(f"Video generation failed for job {job_id}: {e}")
        jobs[job_id].status = "failed"
        jobs[job_id].error_message = str(e)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )

