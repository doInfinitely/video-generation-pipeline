"""Video generation worker that interfaces with Minimax video-01 API."""

import base64
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from .config import settings


class MinimaxVideoGenerator:
    """Client for Minimax video-01 API."""

    def __init__(self):
        if not settings.minimax_api_key:
            raise ValueError("Minimax API key not configured")
        
        self.api_key = settings.minimax_api_key
        self.api_url = settings.minimax_api_url
        self.timeout = 300.0  # 5 minutes timeout for video generation

    async def generate_video(
        self,
        prompt: str,
        first_frame: Optional[bytes] = None,
        duration_seconds: float = 6.0,
    ) -> bytes:
        """
        Generate a video using Minimax video-01 API.

        Args:
            prompt: Text prompt describing the video
            first_frame: Optional first frame as PNG bytes for continuity
            duration_seconds: Duration of the video (default 6s)

        Returns:
            Video bytes (MP4 format)
        """
        logger.info(f"Generating video with Minimax API (duration: {duration_seconds}s)")
        logger.debug(f"Prompt: {prompt[:200]}...")

        # Prepare the request payload
        payload = {
            "prompt": prompt,
            "duration": duration_seconds,
            "model": "video-01",
        }

        # Add first frame if provided
        if first_frame:
            # Encode as base64
            first_frame_b64 = base64.b64encode(first_frame).decode("utf-8")
            payload["first_frame"] = first_frame_b64
            logger.debug("Including first frame for continuity")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                # Parse response
                result = response.json()
                
                # The API response format may vary - adjust based on actual API
                # This is a placeholder structure
                if "video_url" in result:
                    # Download the video from URL
                    video_response = await client.get(result["video_url"])
                    video_response.raise_for_status()
                    video_bytes = video_response.content
                elif "video_data" in result:
                    # Video is returned as base64
                    video_bytes = base64.b64decode(result["video_data"])
                else:
                    raise ValueError(f"Unexpected API response format: {result.keys()}")

                logger.success(f"Generated video ({len(video_bytes)} bytes)")
                return video_bytes

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Minimax API: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
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
        logger.info(f"Generating chunk {chunk_index}")
        
        video_bytes = await self.generate_video(
            prompt=chunk_prompt,
            first_frame=first_frame,
            duration_seconds=settings.video_duration_seconds,
        )
        
        logger.success(f"Completed chunk {chunk_index}")
        return video_bytes

