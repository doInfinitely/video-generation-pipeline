"""Video generation worker using Replicate API."""

import base64
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import settings


class ReplicateVideoGenerator:
    """Client for video generation via Replicate."""

    def __init__(self):
        if not settings.replicate_api_token:
            raise ValueError("Replicate API token not configured")
        
        try:
            import replicate
            self.replicate = replicate
            # Set the API token
            import os
            os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token
        except ImportError:
            raise ValueError(
                "Replicate package not installed. Install with: pip install replicate"
            )
        
        self.model = settings.replicate_model

    async def generate_video(
        self,
        prompt: str,
        first_frame: Optional[bytes] = None,
        duration_seconds: float = 6.0,
    ) -> bytes:
        """
        Generate a video using Replicate API.

        Args:
            prompt: Text prompt describing the video
            first_frame: Optional first frame as PNG bytes for continuity
            duration_seconds: Duration of the video (default 6s)

        Returns:
            Video bytes (MP4 format)
        """
        logger.info(f"Generating video with Replicate API (duration: {duration_seconds}s)")
        logger.debug(f"Model: {self.model}")
        logger.debug(f"Prompt: {prompt[:200]}...")

        try:
            # Prepare input parameters
            input_params = {
                "prompt": prompt,
            }

            # Add first frame if provided (convert to data URL)
            if first_frame:
                first_frame_b64 = base64.b64encode(first_frame).decode("utf-8")
                input_params["first_frame_image"] = f"data:image/png;base64,{first_frame_b64}"
                logger.debug("Including first frame for continuity")

            # Run the model
            logger.info("Starting Replicate prediction...")
            logger.debug(f"Input params: {input_params}")
            
            try:
                output = self.replicate.run(
                    self.model,
                    input=input_params
                )
            except Exception as model_error:
                logger.error(f"Model error: {model_error}")
                logger.error(f"Model: {self.model}")
                logger.error(f"Input params: {input_params}")
                raise

            # Handle different output formats
            if isinstance(output, str):
                # Output is a URL - download it
                logger.info(f"Downloading video from: {output}")
                import httpx
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(output)
                    response.raise_for_status()
                    video_bytes = response.content
            elif isinstance(output, list) and len(output) > 0:
                # Output is a list of URLs - take the first one
                video_url = output[0]
                logger.info(f"Downloading video from: {video_url}")
                import httpx
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(video_url)
                    response.raise_for_status()
                    video_bytes = response.content
            elif isinstance(output, bytes):
                # Output is already bytes
                video_bytes = output
            elif hasattr(output, 'read'):
                # Output is a file-like object (FileOutput)
                logger.info(f"Reading video from FileOutput object")
                video_bytes = output.read()
                logger.info(f"Read {len(video_bytes)} bytes from FileOutput")
            elif hasattr(output, 'url'):
                # FileOutput object with URL attribute
                video_url = str(output.url) if hasattr(output.url, '__str__') else output.url
                logger.info(f"Downloading video from FileOutput.url: {video_url}")
                import httpx
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(video_url)
                    response.raise_for_status()
                    video_bytes = response.content
            else:
                raise ValueError(f"Unexpected output format from Replicate: {type(output)}")

            logger.success(f"Generated video ({len(video_bytes)} bytes)")
            return video_bytes

        except Exception as e:
            logger.error(f"Failed to generate video with Replicate: {e}")
            logger.exception("Full traceback:")
            raise

    async def generate_video_chunk(
        self,
        chunk_prompt: str,
        chunk_index: int,
        first_frame: Optional[bytes] = None,
    ) -> bytes:
        """
        Generate a video for a specific chunk.

        Args:
            chunk_prompt: The built prompt for this chunk
            chunk_index: Index of this chunk (for logging)
            first_frame: Optional first frame from previous chunk

        Returns:
            Video bytes
        """
        logger.info(f"Generating chunk {chunk_index} with Replicate")
        
        video_bytes = await self.generate_video(
            prompt=chunk_prompt,
            first_frame=first_frame,
            duration_seconds=settings.video_duration_seconds,
        )
        
        logger.success(f"Completed chunk {chunk_index}")
        return video_bytes

