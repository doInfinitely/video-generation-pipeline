"""Main orchestration logic for the video generation pipeline."""

import uuid
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import settings
from .models import VideoGenerationRequest, Storyboard
from .play_by_play import PlayByPlayAgent
from .chunker import chunk_keyframes
from .prompt_builder import build_chunk_prompt, build_context_summary
from .video_generator import MinimaxVideoGenerator
from .video_processing import (
    extract_last_frame,
    concatenate_videos,
    save_video_bytes,
)


class VideoOrchestrator:
    """Orchestrates the entire video generation pipeline."""

    def __init__(self):
        self.play_by_play_agent = PlayByPlayAgent()
        self.video_generator = MinimaxVideoGenerator()

    async def generate_video(
        self,
        request: VideoGenerationRequest,
        job_id: Optional[str] = None,
    ) -> Path:
        """
        Generate a complete video from a user prompt.

        This is the main orchestration method that:
        1. Generates a storyboard using the play-by-play agent
        2. Chunks the storyboard into 6-second segments
        3. Generates video for each chunk, chaining frames
        4. Concatenates all chunks into a final video

        Args:
            request: Video generation request with user prompt
            job_id: Optional job ID for tracking (generated if not provided)

        Returns:
            Path to the generated video file
        """
        if job_id is None:
            job_id = str(uuid.uuid4())

        logger.info(f"Starting video generation job {job_id}")
        logger.info(f"User prompt: {request.user_prompt}")

        try:
            # Step 1: Generate play-by-play storyboard
            logger.info("Step 1: Generating storyboard...")
            storyboard = self.play_by_play_agent.generate_storyboard(
                user_prompt=request.user_prompt,
                duration_hint_seconds=request.duration_hint_seconds,
                style_preference=request.style_preference,
            )

            # Step 2: Chunk keyframes into 6-second segments
            logger.info("Step 2: Chunking keyframes...")
            chunks = chunk_keyframes(storyboard)
            logger.info(f"Created {len(chunks)} chunks")

            # Step 3: Generate video for each chunk
            logger.info("Step 3: Generating video chunks...")
            previous_last_frame: Optional[bytes] = None
            generated_clips: list[Path] = []

            # Handle reference image for first chunk
            if request.reference_image:
                import base64
                previous_last_frame = base64.b64decode(request.reference_image)
                logger.info("Using provided reference image for first chunk")

            for chunk in chunks:
                # Build the prompt for this chunk
                previous_context = None
                if chunk.chunk_index > 0:
                    previous_context = build_context_summary(chunks[chunk.chunk_index - 1])

                chunk_prompt = build_chunk_prompt(
                    user_prompt=request.user_prompt,
                    global_style=storyboard.global_style,
                    chunk=chunk,
                    previous_context=previous_context,
                )

                logger.info(f"Generating chunk {chunk.chunk_index + 1}/{len(chunks)}")

                # Generate the video chunk
                video_bytes = await self.video_generator.generate_video_chunk(
                    chunk_prompt=chunk_prompt,
                    chunk_index=chunk.chunk_index,
                    first_frame=previous_last_frame,
                )

                # Save the chunk
                clip_path = settings.temp_storage_path / f"{job_id}_chunk_{chunk.chunk_index}.mp4"
                save_video_bytes(video_bytes, clip_path)
                generated_clips.append(clip_path)

                # Extract last frame for next chunk
                if chunk.chunk_index < len(chunks) - 1:
                    previous_last_frame = extract_last_frame(clip_path)

            # Step 4: Concatenate all chunks
            logger.info("Step 4: Concatenating chunks...")
            final_video_path = settings.video_storage_path / f"{job_id}_final.mp4"
            concatenate_videos(generated_clips, final_video_path)

            # Clean up temporary chunk files
            logger.info("Cleaning up temporary files...")
            for clip_path in generated_clips:
                clip_path.unlink()

            logger.success(f"Video generation completed: {final_video_path}")
            return final_video_path

        except Exception as e:
            logger.error(f"Video generation failed for job {job_id}: {e}")
            raise


async def generate_video_for_prompt(
    user_prompt: str,
    reference_image: Optional[bytes] = None,
    duration_hint_seconds: Optional[int] = None,
    style_preference: Optional[str] = None,
) -> Path:
    """
    Convenience function to generate a video from a prompt.

    Args:
        user_prompt: User's description of the video
        reference_image: Optional reference/subject image bytes
        duration_hint_seconds: Optional desired duration
        style_preference: Optional style preference

    Returns:
        Path to the generated video
    """
    import base64

    # Convert reference image to base64 if provided
    reference_image_b64 = None
    if reference_image:
        reference_image_b64 = base64.b64encode(reference_image).decode("utf-8")

    request = VideoGenerationRequest(
        user_prompt=user_prompt,
        reference_image=reference_image_b64,
        duration_hint_seconds=duration_hint_seconds,
        style_preference=style_preference,
    )

    orchestrator = VideoOrchestrator()
    return await orchestrator.generate_video(request)

