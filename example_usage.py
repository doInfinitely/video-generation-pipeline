"""Example usage of the video generation pipeline."""

import asyncio
from pathlib import Path

from loguru import logger

from src.orchestrator import generate_video_for_prompt


async def example_quicksort_video():
    """Generate a video explaining quicksort algorithm."""
    logger.info("Generating quicksort explanation video...")
    
    prompt = """Generate a video illustrating quicksort on an array of twelve numbers 
    from 0 to 11, showing partition around a pivot and recursive subarrays. 
    Use clear 2D animation with colorful cards representing each number."""
    
    video_path = await generate_video_for_prompt(
        user_prompt=prompt,
        duration_hint_seconds=18,
        style_preference="Clean flat 2D animation, colorful cards",
    )
    
    logger.success(f"Video generated: {video_path}")
    return video_path


async def example_simple_animation():
    """Generate a simple animation video."""
    logger.info("Generating simple animation...")
    
    prompt = """Create an animation showing a ball bouncing across the screen from 
    left to right, with a nice arc trajectory and smooth motion."""
    
    video_path = await generate_video_for_prompt(
        user_prompt=prompt,
        duration_hint_seconds=6,
        style_preference="Simple 3D animation with soft lighting",
    )
    
    logger.success(f"Video generated: {video_path}")
    return video_path


async def example_educational_video():
    """Generate an educational video about photosynthesis."""
    logger.info("Generating educational video about photosynthesis...")
    
    prompt = """Explain the process of photosynthesis in plants. Show a plant leaf, 
    sunlight rays hitting it, CO2 entering, water molecules moving up from roots, 
    and glucose and oxygen being produced. Use diagrams and labels."""
    
    video_path = await generate_video_for_prompt(
        user_prompt=prompt,
        duration_hint_seconds=12,
        style_preference="Educational diagram style with clear labels",
    )
    
    logger.success(f"Video generated: {video_path}")
    return video_path


async def main():
    """Run example video generations."""
    logger.info("Starting video generation examples...")
    
    # Choose which example to run
    examples = {
        "1": ("Quicksort Algorithm", example_quicksort_video),
        "2": ("Simple Ball Animation", example_simple_animation),
        "3": ("Photosynthesis Education", example_educational_video),
    }
    
    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"{key}. {name}")
    
    choice = input("\nSelect an example (1-3) or press Enter for quicksort: ").strip()
    if not choice:
        choice = "1"
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\nGenerating: {name}")
        await func()
    else:
        print("Invalid choice, running quicksort example...")
        await example_quicksort_video()


if __name__ == "__main__":
    asyncio.run(main())

