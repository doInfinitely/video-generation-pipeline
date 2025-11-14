"""Keyframe chunking logic for splitting storyboards into 6-second segments."""

from typing import List, Dict

from loguru import logger

from .config import settings
from .models import Storyboard, ChunkData


def chunk_keyframes(
    storyboard: Storyboard,
    chunk_ms: int = None,
) -> List[ChunkData]:
    """
    Split keyframes into chunks based on chunk duration.

    Args:
        storyboard: The complete storyboard with keyframes
        chunk_ms: Duration of each chunk in milliseconds (default from settings)

    Returns:
        List of ChunkData objects, each representing a 6-second segment
    """
    if chunk_ms is None:
        chunk_ms = settings.chunk_duration_ms

    keyframes = storyboard.keyframes
    duration_ms = storyboard.duration_ms

    logger.info(
        f"Chunking {len(keyframes)} keyframes over {duration_ms}ms "
        f"into {chunk_ms}ms segments"
    )

    # Convert keyframe times to integers and sort
    times = sorted(int(t) for t in keyframes.keys())
    max_time = duration_ms

    # Calculate number of chunks needed
    num_chunks = (max_time + chunk_ms - 1) // chunk_ms
    chunks: List[ChunkData] = []

    for i in range(num_chunks):
        start = i * chunk_ms
        end = min((i + 1) * chunk_ms, max_time)

        chunk_keyframes: Dict[str, str] = {}
        
        # Find all keyframes that fall within this chunk
        for t in times:
            if start <= t < end:
                local_t = t - start
                chunk_keyframes[str(local_t)] = keyframes[str(t)]

        # If no keyframe at exactly 0, synthesize one
        if "0" not in chunk_keyframes:
            # Option 1: Use the earliest keyframe in this chunk
            if chunk_keyframes:
                first_time = min(int(k) for k in chunk_keyframes.keys())
                chunk_keyframes["0"] = chunk_keyframes[str(first_time)]
            # Option 2: If this is not the first chunk and there are no keyframes,
            # we should use the last keyframe from the previous chunk as context
            elif i > 0:
                # Find the most recent keyframe before this chunk
                previous_times = [t for t in times if t < start]
                if previous_times:
                    last_previous = max(previous_times)
                    chunk_keyframes["0"] = keyframes[str(last_previous)]

        chunk = ChunkData(
            chunk_index=i,
            start_global_ms=start,
            end_global_ms=end,
            keyframes=chunk_keyframes,
        )
        chunks.append(chunk)

        logger.debug(
            f"Chunk {i}: {start}-{end}ms with {len(chunk_keyframes)} keyframes"
        )

    logger.success(f"Created {len(chunks)} chunks from storyboard")
    return chunks

