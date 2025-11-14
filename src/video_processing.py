"""Video post-processing utilities for frame extraction and concatenation."""

import subprocess
from pathlib import Path
from typing import List

import ffmpeg
from loguru import logger

from .config import settings


def extract_last_frame(video_path: Path) -> bytes:
    """
    Extract the last frame from a video as PNG bytes.

    Args:
        video_path: Path to the video file

    Returns:
        PNG image bytes of the last frame
    """
    logger.debug(f"Extracting last frame from {video_path}")
    
    try:
        # Use ffmpeg to extract the last frame
        # -sseof -0.04 seeks to 0.04 seconds before the end
        output_path = video_path.parent / f"{video_path.stem}_last_frame.png"
        
        (
            ffmpeg
            .input(str(video_path), sseof=-0.04)
            .output(str(output_path), vframes=1, format='image2', vcodec='png')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        
        # Read the frame bytes
        with open(output_path, "rb") as f:
            frame_bytes = f.read()
        
        # Clean up the temporary file
        output_path.unlink()
        
        logger.success(f"Extracted last frame ({len(frame_bytes)} bytes)")
        return frame_bytes
    
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error extracting frame: {e.stderr.decode()}")
        raise
    except Exception as e:
        logger.error(f"Failed to extract last frame: {e}")
        raise


def concatenate_videos(video_paths: List[Path], output_path: Path) -> Path:
    """
    Concatenate multiple video files into a single video.

    Args:
        video_paths: List of paths to video files to concatenate
        output_path: Path for the output concatenated video

    Returns:
        Path to the concatenated video
    """
    logger.info(f"Concatenating {len(video_paths)} videos")
    
    if not video_paths:
        raise ValueError("No video paths provided for concatenation")
    
    if len(video_paths) == 1:
        # If only one video, just copy it
        logger.info("Only one video, copying instead of concatenating")
        import shutil
        shutil.copy(video_paths[0], output_path)
        return output_path
    
    try:
        # Create a temporary file list for ffmpeg concat
        concat_file = output_path.parent / "concat_list.txt"
        
        with open(concat_file, "w") as f:
            for video_path in video_paths:
                # Write the absolute path and escape special characters
                f.write(f"file '{video_path.absolute()}'\n")
        
        # Use ffmpeg concat demuxer
        logger.debug(f"Concatenating with concat file: {concat_file}")
        
        (
            ffmpeg
            .input(str(concat_file), format='concat', safe=0)
            .output(str(output_path), c='copy')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        
        # Clean up the concat file
        concat_file.unlink()
        
        logger.success(f"Concatenated video saved to {output_path}")
        return output_path
    
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error during concatenation: {e.stderr.decode()}")
        raise
    except Exception as e:
        logger.error(f"Failed to concatenate videos: {e}")
        raise


def save_video_bytes(video_bytes: bytes, output_path: Path) -> Path:
    """
    Save video bytes to a file.

    Args:
        video_bytes: Video data as bytes
        output_path: Path to save the video

    Returns:
        Path to the saved video
    """
    logger.debug(f"Saving video to {output_path} ({len(video_bytes)} bytes)")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "wb") as f:
        f.write(video_bytes)
    
    logger.success(f"Saved video to {output_path}")
    return output_path


def get_video_info(video_path: Path) -> dict:
    """
    Get information about a video file.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary with video information (duration, fps, resolution, etc.)
    """
    try:
        probe = ffmpeg.probe(str(video_path))
        video_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
            None
        )
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        info = {
            "duration": float(probe['format']['duration']),
            "fps": eval(video_stream['r_frame_rate']),
            "width": video_stream['width'],
            "height": video_stream['height'],
            "codec": video_stream['codec_name'],
        }
        
        return info
    
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        raise

