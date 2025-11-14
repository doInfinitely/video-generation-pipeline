"""Build prompts for video generation from chunk data."""

from typing import Optional

from .models import ChunkData


def build_chunk_prompt(
    user_prompt: str,
    global_style: str,
    chunk: ChunkData,
    previous_context: Optional[str] = None,
) -> str:
    """
    Build a detailed text prompt for video generation from a chunk.

    Args:
        user_prompt: Original user prompt for context
        global_style: Global visual style description
        chunk: The chunk data with local keyframes
        previous_context: Optional summary of what happened in previous chunks

    Returns:
        A text prompt suitable for the video generation model
    """
    # Start with the global context
    prompt_parts = []
    
    # Add user context and style
    prompt_parts.append(f"Create a video for: {user_prompt}")
    prompt_parts.append(f"\nVisual style: {global_style}")
    
    # Add continuation context if this is not the first chunk
    if chunk.chunk_index > 0 and previous_context:
        prompt_parts.append(f"\nContinuation: {previous_context}")
    
    # Add the timeline for this specific 6-second segment
    prompt_parts.append(
        f"\n\nFor this {chunk.end_global_ms - chunk.start_global_ms}ms segment, "
        "follow this visual timeline (times in milliseconds from the start of this segment):"
    )
    
    # Sort keyframes by time and add them
    sorted_keyframes = sorted(
        chunk.keyframes.items(),
        key=lambda x: int(x[0])
    )
    
    for time_ms, description in sorted_keyframes:
        prompt_parts.append(f"\n* At {time_ms}ms: {description}")
    
    # Add instruction for smooth animation
    prompt_parts.append(
        "\n\nSmooth animation: Animate smoothly between these keyframe states "
        "with clear, readable motion. Maintain visual consistency with the "
        "established style and elements."
    )
    
    return "".join(prompt_parts)


def build_context_summary(chunk: ChunkData) -> str:
    """
    Build a summary of a chunk to use as context for the next chunk.

    Args:
        chunk: The chunk to summarize

    Returns:
        A brief summary string
    """
    # Get the last keyframe in this chunk as it represents the ending state
    if not chunk.keyframes:
        return "Previous segment completed."
    
    sorted_keyframes = sorted(
        chunk.keyframes.items(),
        key=lambda x: int(x[0])
    )
    
    # Use the last keyframe as the summary
    last_time, last_description = sorted_keyframes[-1]
    
    return f"The previous segment ended with: {last_description}"

