"""Interactive playground for testing minimax/video-01 prompts.

This script lets you experiment with different prompts and starting frames
to understand what the model can actually do.
"""

import os
import asyncio
from pathlib import Path
from datetime import datetime
import base64

from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class MinimaxPlayground:
    """Interactive playground for video generation models."""
    
    # Categorized model list
    MODELS = {
        "Premium Text-to-Video": [
            "openai/sora-2",
            "openai/sora-2-pro",
            "google/veo-3.1",
            "google/veo-3.1-fast",
            "google/veo-3",
            "google/veo-3-fast",
            "google/veo-2",
            "minimax/hailuo-2.3",
            "minimax/hailuo-2.3-fast",
            "minimax/hailuo-02",
            "minimax/video-01",
            "minimax/video-01-director",
            "minimax/video-01-live",
        ],
        "Fast/Turbo Models": [
            "bytedance/seedance-1-pro-fast",
            "kwaivgi/kling-v2.5-turbo-pro",
            "wan-video/wan-2.5-t2v-fast",
            "wan-video/wan-2.2-t2v-fast",
        ],
        "High Quality T2V": [
            "bytedance/seedance-1-pro",
            "bytedance/seedance-1-lite",
            "pixverse/pixverse-v5",
            "pixverse/pixverse-v4.5",
            "pixverse/pixverse-v4",
            "kwaivgi/kling-v2.1-master",
            "kwaivgi/kling-v2.1",
            "kwaivgi/kling-v2.0",
            "kwaivgi/kling-v1.6-pro",
            "kwaivgi/kling-v1.6-standard",
            "luma/ray-2-720p",
            "luma/ray-2-540p",
            "luma/ray",
            "luma/ray-flash-2-720p",
            "luma/ray-flash-2-540p",
            "leonardoai/motion-2.0",
            "tencent/hunyuan-video",
            "genmoai/mochi-1",
        ],
        "Image-to-Video": [
            "wan-video/wan-2.5-i2v",
            "wan-video/wan-2.5-i2v-fast",
            "wan-video/wan-2.2-i2v-a14b",
            "wan-video/wan-2.2-i2v-fast",
            "wavespeedai/wan-2.1-i2v-720p",
            "wavespeedai/wan-2.1-i2v-480p",
            "ali-vilab/i2vgen-xl",
        ],
        "Budget/Classic Models": [
            "wan-video/wan-2.1-1.3b",
            "lightricks/ltx-video",
            "cuuupid/cogvideox-5b",
            "anotherjesse/zeroscope-v2-xl",
            "cjwbw/damo-text-to-video",
        ],
    }
    
    def __init__(self, default_model="minimax/video-01"):
        try:
            import replicate
            self.client = replicate.Client(api_token=os.environ.get("REPLICATE_API_TOKEN"))
            logger.success("Replicate client initialized")
        except ImportError:
            logger.error("Replicate not installed. Run: pip install replicate")
            exit(1)
        
        self.model = default_model
        self.output_dir = Path("playground_outputs")
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"Outputs will be saved to: {self.output_dir}")
        logger.info(f"Current model: {self.model}")
    
    async def generate_video(self, prompt: str, first_frame_path: str = None, model: str = None):
        """Generate a video with the given prompt and optional first frame."""
        if model is None:
            model = self.model
            
        logger.info("="*80)
        logger.info(f"Model: {model}")
        logger.info(f"Prompt: {prompt}")
        logger.info(f"First frame: {first_frame_path if first_frame_path else 'None'}")
        logger.info("="*80)
        
        # Prepare input
        input_params = {
            "prompt": prompt,
            "prompt_optimizer": True,  # Can toggle this
        }
        
        # Add first frame if provided
        if first_frame_path:
            frame_path = Path(first_frame_path)
            if frame_path.exists():
                logger.info(f"Loading first frame from: {frame_path}")
                with open(frame_path, "rb") as f:
                    frame_bytes = f.read()
                frame_b64 = base64.b64encode(frame_bytes).decode("utf-8")
                input_params["first_frame_image"] = f"data:image/png;base64,{frame_b64}"
            else:
                logger.warning(f"First frame not found: {frame_path}")
        
        try:
            logger.info("Starting generation... (this takes 1-2 minutes)")
            start_time = datetime.now()
            
            # Use predictions.create to get cost info
            prediction = self.client.predictions.create(
                model=model,
                input=input_params
            )
            
            # Wait for completion
            prediction.wait()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.success(f"Generation completed in {elapsed:.1f} seconds")
            
            # Extract cost information
            cost_info = self._extract_cost_info(prediction)
            if cost_info:
                logger.info(f"💰 Cost: ${cost_info['total_cost']:.4f}")
                logger.info(f"   Compute: ${cost_info['compute_cost']:.4f} ({cost_info['compute_time']:.1f}s)")
            
            output = prediction.output
            
            # Download and save
            video_bytes = await self._download_output(output)
            
            # Save with timestamp and model name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '_')).rstrip()
            safe_prompt = safe_prompt.replace(' ', '_')
            model_name = model.replace('/', '_')
            filename = f"{timestamp}_{model_name}_{safe_prompt}.mp4"
            output_path = self.output_dir / filename
            
            with open(output_path, "wb") as f:
                f.write(video_bytes)
            
            logger.success(f"Video saved: {output_path}")
            logger.info(f"Size: {len(video_bytes) / 1024 / 1024:.2f} MB")
            
            result = {
                "path": output_path,
                "size_mb": len(video_bytes) / 1024 / 1024,
                "elapsed_seconds": elapsed,
                "cost": cost_info,
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _extract_cost_info(self, prediction):
        """Extract cost information from prediction."""
        try:
            metrics = prediction.metrics
            if not metrics:
                return None
            
            # Replicate provides predict_time which is billable compute time
            compute_time = metrics.get('predict_time', 0)
            
            # Get model pricing (this would need to be looked up per model)
            # For now, we'll just show what's available
            cost_info = {
                'compute_time': compute_time,
                'compute_cost': 0,  # Would need model-specific pricing
                'total_cost': 0,
            }
            
            # If prediction has cost field directly
            if hasattr(prediction, 'cost') and prediction.cost:
                cost_info['total_cost'] = prediction.cost
                cost_info['compute_cost'] = prediction.cost
            
            return cost_info if cost_info['compute_time'] > 0 else None
            
        except Exception as e:
            logger.debug(f"Could not extract cost info: {e}")
            return None
    
    async def _download_output(self, output):
        """Download video from Replicate output."""
        if hasattr(output, 'read'):
            # FileOutput object
            return output.read()
        elif hasattr(output, 'url'):
            # Has URL attribute
            import httpx
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(str(output.url))
                response.raise_for_status()
                return response.content
        elif isinstance(output, str):
            # Direct URL
            import httpx
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(output)
                response.raise_for_status()
                return response.content
        else:
            raise ValueError(f"Unexpected output type: {type(output)}")
    
    def show_models(self):
        """Display available models by category."""
        print("\n" + "="*80)
        print("AVAILABLE VIDEO MODELS")
        print("="*80)
        
        for category, models in self.MODELS.items():
            print(f"\n{category}:")
            for i, model in enumerate(models, 1):
                marker = "👉" if model == self.model else "  "
                print(f"  {marker} {model}")
        
        print("\n" + "="*80)
        print(f"Current model: {self.model}")
        print("="*80)
    
    def select_model(self):
        """Interactive model selection."""
        self.show_models()
        
        print("\nEnter model name (or part of it) to switch:")
        model_input = input("> ").strip()
        
        if not model_input:
            return
        
        # Find matching models
        all_models = [m for models in self.MODELS.values() for m in models]
        matches = [m for m in all_models if model_input.lower() in m.lower()]
        
        if not matches:
            print(f"❌ No models found matching '{model_input}'")
        elif len(matches) == 1:
            self.model = matches[0]
            print(f"✅ Switched to: {self.model}")
        else:
            print(f"\n Multiple matches found:")
            for i, m in enumerate(matches, 1):
                print(f"  {i}. {m}")
            choice = input("\nSelect number: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    self.model = matches[idx]
                    print(f"✅ Switched to: {self.model}")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
    
    async def interactive_mode(self):
        """Run interactive prompt mode."""
        print("\n" + "="*80)
        print("VIDEO GENERATION PLAYGROUND")
        print("="*80)
        print("\nTest different prompts across multiple video models!")
        print("Commands: 'quit', 'examples', 'models', 'switch', 'parallel'\n")
        
        while True:
            print("\n" + "-"*80)
            prompt = input(f"\n[{self.model}]\nEnter your prompt: ").strip()
            
            if not prompt:
                continue
            
            if prompt.lower() == 'quit':
                print("Goodbye!")
                break
            
            if prompt.lower() == 'examples':
                self.show_examples()
                continue
            
            if prompt.lower() == 'models':
                self.show_models()
                continue
            
            if prompt.lower() == 'switch':
                self.select_model()
                continue
            
            if prompt.lower() == 'parallel':
                await self.parallel_test_interactive()
                continue
            
            # Ask about first frame
            first_frame = input("First frame image path (press Enter to skip): ").strip()
            if not first_frame:
                first_frame = None
            
            # Ask about prompt optimizer
            use_optimizer = input("Use prompt optimizer? [Y/n]: ").strip().lower()
            if use_optimizer in ['n', 'no']:
                logger.info("Prompt optimizer disabled for this generation")
            
            try:
                result = await self.generate_video(prompt, first_frame)
                cost = result.get('cost', {}).get('total_cost', 0) if result.get('cost') else 0
                cost_str = f"${cost:.4f}" if cost > 0 else "N/A"
                print(f"\n✅ Success! Check {self.output_dir} for the video")
                print(f"💰 Cost: {cost_str} | ⏱️ Time: {result['elapsed_seconds']:.1f}s | 📦 Size: {result['size_mb']:.1f}MB")
            except Exception as e:
                print(f"\n❌ Failed: {e}")
    
    def show_examples(self):
        """Show example prompts."""
        print("\n" + "="*80)
        print("EXAMPLE PROMPTS")
        print("="*80)
        
        examples = [
            ("Simple", "A red ball bounces on a white surface"),
            ("Detailed", "A red rubber ball with glossy surface bounces on a wooden table, "
                        "starting from the left, bouncing three times, each bounce getting lower"),
            ("Sorting (Simple)", "Colorful numbered cards arrange themselves from lowest to highest"),
            ("Sorting (Detailed)", "Five cards labeled 5, 2, 8, 1, 4 are shown in a row. "
                                 "The card labeled 1 moves to the first position, then 2 moves to second, "
                                 "then 4 moves to third, then 5 moves to fourth, then 8 stays in fifth"),
            ("Abstract", "Geometric shapes morph and transform, changing colors smoothly"),
            ("Educational", "A plant cell with labeled parts: nucleus, cell wall, chloroplasts, vacuole"),
            ("Sequential", "Step 1: Draw a circle. Step 2: Add two dots for eyes. "
                          "Step 3: Draw a smile. Step 4: Add ears"),
        ]
        
        for i, (category, example) in enumerate(examples, 1):
            print(f"\n{i}. {category}:")
            print(f"   {example}")
        
        print("\n" + "="*80)
        print("Try variations of these to see what works best!")
        print("="*80)
    
    async def parallel_test(self, prompt: str, models: list, first_frame_path: str = None):
        """Test same prompt across multiple models in parallel."""
        print(f"\n🚀 Running parallel test with {len(models)} models...")
        print(f"Prompt: {prompt}")
        print(f"Models: {', '.join(models)}\n")
        
        # Run all models concurrently
        tasks = []
        for model in models:
            task = self.generate_video(prompt, first_frame_path, model=model)
            tasks.append((model, task))
        
        results = []
        for model, task in tasks:
            try:
                result = await task
                results.append({
                    "model": model,
                    "success": True,
                    "output": str(result["path"]),
                    "cost": result.get("cost"),
                    "time": result.get("elapsed_seconds"),
                    "size_mb": result.get("size_mb"),
                })
                cost_str = f"${result['cost']['total_cost']:.4f}" if result.get("cost") and result["cost"].get("total_cost") else "N/A"
                print(f"✅ {model} - completed (💰 {cost_str}, ⏱️ {result['elapsed_seconds']:.1f}s)")
            except Exception as e:
                results.append({
                    "model": model,
                    "success": False,
                    "error": str(e)
                })
                print(f"❌ {model} - failed: {e}")
        
        # Summary
        print("\n" + "="*80)
        print("PARALLEL TEST RESULTS")
        print("="*80)
        success_count = sum(1 for r in results if r["success"])
        print(f"\nSuccess: {success_count}/{len(models)}")
        
        print("\nSuccessful:")
        total_cost = 0
        for r in results:
            if r["success"]:
                cost = r.get('cost', {}).get('total_cost', 0) if r.get('cost') else 0
                total_cost += cost
                cost_str = f"${cost:.4f}" if cost > 0 else "N/A"
                time_str = f"{r.get('time', 0):.1f}s"
                size_str = f"{r.get('size_mb', 0):.1f}MB"
                print(f"  ✅ {r['model']}")
                print(f"     → {r['output']}")
                print(f"     💰 {cost_str} | ⏱️ {time_str} | 📦 {size_str}")
        
        if total_cost > 0:
            print(f"\n💰 Total cost: ${total_cost:.4f}")
        
        print("\nFailed:")
        for r in results:
            if not r["success"]:
                print(f"  ❌ {r['model']}")
                print(f"     → {r['error']}")
        
        return results
    
    async def parallel_test_interactive(self):
        """Interactive parallel testing."""
        print("\n" + "="*80)
        print("PARALLEL MODEL COMPARISON")
        print("="*80)
        
        # Show suggested model groups
        print("\nSuggested model groups:")
        print("  1. Fast models (3 models)")
        print("  2. Premium models (5 models)")
        print("  3. Minimax family (4 models)")
        print("  4. Custom selection")
        
        choice = input("\nSelect group (1-4) or press Enter for fast models: ").strip()
        
        if choice == "2":
            models = ["openai/sora-2", "google/veo-3.1-fast", "minimax/hailuo-2.3-fast", 
                     "bytedance/seedance-1-pro-fast", "kwaivgi/kling-v2.5-turbo-pro"]
        elif choice == "3":
            models = ["minimax/video-01", "minimax/hailuo-2.3", "minimax/hailuo-2.3-fast", "minimax/video-01-live"]
        elif choice == "4":
            self.show_models()
            models_input = input("\nEnter model names (comma-separated): ").strip()
            models = [m.strip() for m in models_input.split(",") if m.strip()]
            if not models:
                print("❌ No models selected")
                return
        else:
            # Default: fast models
            models = ["minimax/hailuo-2.3-fast", "bytedance/seedance-1-pro-fast", "wan-video/wan-2.5-t2v-fast"]
        
        prompt = input("\nEnter prompt to test across all models: ").strip()
        if not prompt:
            print("❌ No prompt provided")
            return
        
        first_frame = input("First frame image path (press Enter to skip): ").strip()
        if not first_frame:
            first_frame = None
        
        await self.parallel_test(prompt, models, first_frame)
    
    async def batch_test(self, prompts: list):
        """Test multiple prompts in batch."""
        print(f"\n📋 Running batch test with {len(prompts)} prompts...")
        
        results = []
        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] Testing: {prompt[:60]}...")
            try:
                result = await self.generate_video(prompt)
                results.append({
                    "prompt": prompt,
                    "success": True,
                    "output": str(result["path"]),
                    "cost": result.get("cost"),
                    "time": result.get("elapsed_seconds"),
                })
            except Exception as e:
                results.append({
                    "prompt": prompt,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        print("\n" + "="*80)
        print("BATCH TEST RESULTS")
        print("="*80)
        success_count = sum(1 for r in results if r["success"])
        print(f"\nSuccess: {success_count}/{len(prompts)}")
        
        print("\nSuccessful:")
        total_cost = 0
        for r in results:
            if r["success"]:
                cost = r.get('cost', {}).get('total_cost', 0) if r.get('cost') else 0
                total_cost += cost
                cost_str = f"${cost:.4f}" if cost > 0 else "N/A"
                print(f"  ✅ {r['prompt'][:60]}")
                print(f"     → {r['output']} (💰 {cost_str})")
        
        if total_cost > 0:
            print(f"\n💰 Total cost: ${total_cost:.4f}")
        
        print("\nFailed:")
        for r in results:
            if not r["success"]:
                print(f"  ❌ {r['prompt'][:60]}")
                print(f"     → {r['error']}")


async def main():
    """Main entry point."""
    import sys
    
    # Check for model flag
    model = "minimax/video-01"
    args = sys.argv[1:]
    
    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model = args[idx + 1]
            args = args[:idx] + args[idx+2:]
    
    playground = MinimaxPlayground(default_model=model)
    
    if len(args) > 0:
        if args[0] == "batch":
            # Batch test mode
            test_prompts = [
                "A red ball bounces three times",
                "Numbers 5, 2, 8, 1, 4 arrange themselves in order: 1, 2, 4, 5, 8",
                "A card labeled 5 moves from first position to last position",
                "Three colored blocks stack themselves into a tower",
            ]
            await playground.batch_test(test_prompts)
        elif args[0] == "parallel":
            # Parallel test mode
            if len(args) > 1:
                prompt = " ".join(args[1:])
                # Default fast models
                models = ["minimax/hailuo-2.3-fast", "bytedance/seedance-1-pro-fast", "wan-video/wan-2.5-t2v-fast"]
                await playground.parallel_test(prompt, models)
            else:
                print("Usage: python minimax_playground.py parallel \"your prompt here\"")
        elif args[0] == "models":
            # Show models and exit
            playground.show_models()
        else:
            # Single prompt from command line
            prompt = " ".join(args)
            await playground.generate_video(prompt)
    else:
        # Interactive mode
        await playground.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())

