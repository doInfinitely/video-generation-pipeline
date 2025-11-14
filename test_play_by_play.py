"""Test script for play-by-play storyboard generation only."""

import asyncio
import json
from loguru import logger

from src.play_by_play import PlayByPlayAgent
from src.chunker import chunk_keyframes


def print_storyboard(storyboard):
    """Pretty print a storyboard."""
    print("\n" + "="*80)
    print("GENERATED STORYBOARD")
    print("="*80)
    print(f"\nDuration: {storyboard.duration_ms}ms ({storyboard.duration_ms/1000}s)")
    print(f"FPS: {storyboard.fps}")
    print(f"\nGlobal Style:")
    print(f"  {storyboard.global_style}")
    print(f"\nKeyframes ({len(storyboard.keyframes)} total):")
    
    # Sort keyframes by time
    sorted_keyframes = sorted(
        storyboard.keyframes.items(),
        key=lambda x: int(x[0])
    )
    
    for time_ms, description in sorted_keyframes:
        seconds = int(time_ms) / 1000
        print(f"\n  [{seconds:6.2f}s] {description}")
    
    print("\n" + "="*80)


def print_chunks(chunks):
    """Pretty print chunks."""
    print("\n" + "="*80)
    print("CHUNKED STORYBOARD (6-second segments)")
    print("="*80)
    
    for chunk in chunks:
        print(f"\nChunk {chunk.chunk_index + 1}:")
        print(f"  Global time: {chunk.start_global_ms}-{chunk.end_global_ms}ms")
        print(f"  Duration: {chunk.end_global_ms - chunk.start_global_ms}ms")
        print(f"  Keyframes ({len(chunk.keyframes)}):")
        
        # Sort keyframes by time
        sorted_keyframes = sorted(
            chunk.keyframes.items(),
            key=lambda x: int(x[0])
        )
        
        for time_ms, description in sorted_keyframes:
            seconds = int(time_ms) / 1000
            print(f"    [{seconds:6.2f}s] {description[:80]}...")
    
    print("\n" + "="*80)


def test_quicksort_example():
    """Test with the quicksort example from the brainstorm."""
    logger.info("Testing quicksort algorithm visualization...")
    
    agent = PlayByPlayAgent()
    
    prompt = """Generate a video illustrating quicksort on an array of twelve numbers 
from 0 to 11, showing partition around a pivot and recursive subarrays."""
    
    storyboard = agent.generate_storyboard(
        user_prompt=prompt,
        duration_hint_seconds=18,
        style_preference="Clean flat 2D animation, pale background, each number in a rounded rectangle card"
    )
    
    print_storyboard(storyboard)
    
    # Test chunking
    chunks = chunk_keyframes(storyboard)
    print_chunks(chunks)
    
    # Save to JSON for inspection
    output_data = {
        "prompt": prompt,
        "storyboard": storyboard.model_dump(),
        "chunks": [chunk.model_dump() for chunk in chunks]
    }
    
    with open("test_quicksort_storyboard.json", "w") as f:
        json.dump(output_data, f, indent=2)
    
    logger.success("Storyboard saved to test_quicksort_storyboard.json")


def test_simple_animation():
    """Test with a simple animation."""
    logger.info("Testing simple ball animation...")
    
    agent = PlayByPlayAgent()
    
    prompt = "A red ball bounces from left to right across the screen with a nice arc trajectory"
    
    storyboard = agent.generate_storyboard(
        user_prompt=prompt,
        duration_hint_seconds=6,
        style_preference="Simple 3D animation with soft lighting"
    )
    
    print_storyboard(storyboard)
    
    # Test chunking
    chunks = chunk_keyframes(storyboard)
    print_chunks(chunks)


def test_photosynthesis():
    """Test with an educational example."""
    logger.info("Testing photosynthesis education video...")
    
    agent = PlayByPlayAgent()
    
    prompt = """Explain the process of photosynthesis in plants. Show a plant leaf, 
sunlight rays hitting it, CO2 entering, water molecules moving up from roots, 
and glucose and oxygen being produced."""
    
    storyboard = agent.generate_storyboard(
        user_prompt=prompt,
        duration_hint_seconds=12,
        style_preference="Educational diagram style with clear labels and arrows"
    )
    
    print_storyboard(storyboard)
    
    # Test chunking
    chunks = chunk_keyframes(storyboard)
    print_chunks(chunks)


def test_custom_prompt():
    """Test with a custom prompt from user input."""
    print("\n" + "="*80)
    print("CUSTOM PROMPT TEST")
    print("="*80)
    
    prompt = input("\nEnter your video prompt: ").strip()
    if not prompt:
        print("No prompt provided, skipping.")
        return
    
    duration = input("Desired duration in seconds (press Enter for 12): ").strip()
    duration = int(duration) if duration else 12
    
    style = input("Style preference (press Enter for default): ").strip()
    style = style if style else None
    
    agent = PlayByPlayAgent()
    
    logger.info(f"Generating storyboard for: {prompt}")
    
    storyboard = agent.generate_storyboard(
        user_prompt=prompt,
        duration_hint_seconds=duration,
        style_preference=style
    )
    
    print_storyboard(storyboard)
    
    # Test chunking
    chunks = chunk_keyframes(storyboard)
    print_chunks(chunks)
    
    # Save to JSON
    output_file = "test_custom_storyboard.json"
    output_data = {
        "prompt": prompt,
        "duration_hint": duration,
        "style": style,
        "storyboard": storyboard.model_dump(),
        "chunks": [chunk.model_dump() for chunk in chunks]
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    logger.success(f"Storyboard saved to {output_file}")


def main():
    """Run play-by-play tests."""
    print("\n" + "="*80)
    print("PLAY-BY-PLAY STORYBOARD GENERATION TEST")
    print("="*80)
    print("\nThis will test the LLM-based storyboard generation without video generation.")
    print("Make sure you have OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file.")
    
    examples = {
        "1": ("Quicksort Algorithm", test_quicksort_example),
        "2": ("Simple Ball Animation", test_simple_animation),
        "3": ("Photosynthesis Education", test_photosynthesis),
        "4": ("Custom Prompt", test_custom_prompt),
    }
    
    print("\nAvailable tests:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    choice = input("\nSelect a test (1-4) or press Enter for quicksort: ").strip()
    if not choice:
        choice = "1"
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\nRunning: {name}\n")
        try:
            func()
            print("\n✅ Test completed successfully!")
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            print("\n❌ Make sure you have set up your .env file with API keys!")
            print("Create a .env file with:")
            print("  OPENAI_API_KEY=your-key-here")
            print("  # or")
            print("  ANTHROPIC_API_KEY=your-key-here")
            print("  LLM_PROVIDER=anthropic")
        except Exception as e:
            logger.error(f"Test failed: {e}")
            print(f"\n❌ Test failed: {e}")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()

