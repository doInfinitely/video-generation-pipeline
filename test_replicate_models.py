"""Test script to check available Replicate video models and their parameters."""

import os
from loguru import logger

# Set up environment
from dotenv import load_dotenv
load_dotenv()

try:
    import replicate
    client = replicate.Client(api_token=os.environ.get("REPLICATE_API_TOKEN"))
    logger.info("Replicate client initialized")
except ImportError:
    logger.error("Replicate package not installed. Run: pip install replicate")
    exit(1)
except Exception as e:
    logger.error(f"Failed to initialize Replicate: {e}")
    exit(1)


def test_model(model_name: str):
    """Test if a model exists and show its schema."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing model: {model_name}")
    logger.info(f"{'='*80}")
    
    try:
        # Try to get the model
        model = client.models.get(model_name)
        logger.success(f"✅ Model found: {model_name}")
        
        # Get the latest version
        if hasattr(model, 'latest_version') and model.latest_version:
            version = model.latest_version
            logger.info(f"Latest version: {version.id}")
            
            # Show input schema
            if hasattr(version, 'openapi_schema'):
                schema = version.openapi_schema
                if 'components' in schema and 'schemas' in schema['components']:
                    input_schema = schema['components']['schemas'].get('Input', {})
                    properties = input_schema.get('properties', {})
                    
                    logger.info("\nInput parameters:")
                    for param_name, param_info in properties.items():
                        param_type = param_info.get('type', 'unknown')
                        description = param_info.get('description', 'No description')
                        default = param_info.get('default', 'None')
                        logger.info(f"  - {param_name} ({param_type}): {description}")
                        if default != 'None':
                            logger.info(f"    Default: {default}")
        else:
            logger.warning("Could not get version info")
            
    except Exception as e:
        logger.error(f"❌ Model not found or error: {e}")


def list_popular_video_models():
    """List some popular video generation models on Replicate."""
    logger.info("\n" + "="*80)
    logger.info("Popular Video Generation Models on Replicate")
    logger.info("="*80 + "\n")
    
    # Known video generation models
    models = [
        "minimax/video-01",
        "stability-ai/stable-video-diffusion",
        "anotherjesse/zeroscope-v2-xl",
        "cjwbw/damo-text-to-video",
        "deforum/deforum_stable_diffusion",
    ]
    
    for model in models:
        test_model(model)


def test_simple_generation():
    """Try a simple video generation test."""
    logger.info("\n" + "="*80)
    logger.info("Testing Simple Video Generation")
    logger.info("="*80 + "\n")
    
    # Try with a model that's known to work
    test_models = [
        ("anotherjesse/zeroscope-v2-xl", {"prompt": "A ball bouncing"}),
        ("stability-ai/stable-video-diffusion", {"image": "https://replicate.delivery/pbxt/JvVcVYKAjNXc6J5ZPlJZR9JI8RmPo8cHBdLTSRIlS6yp9LZk/rocket.png"}),
    ]
    
    for model_name, input_params in test_models:
        try:
            logger.info(f"\nTrying {model_name}...")
            logger.info(f"Input: {input_params}")
            
            output = client.run(model_name, input=input_params)
            logger.success(f"✅ {model_name} works!")
            logger.info(f"Output type: {type(output)}")
            logger.info(f"Output: {output}")
            break  # If one works, we're good
            
        except Exception as e:
            logger.error(f"❌ {model_name} failed: {e}")


if __name__ == "__main__":
    import sys
    
    logger.info("Replicate Model Testing Tool")
    logger.info("This will help identify working video models and their parameters\n")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "test" and len(sys.argv) > 2:
            test_model(sys.argv[2])
        elif sys.argv[1] == "generate":
            test_simple_generation()
        else:
            list_popular_video_models()
    else:
        # Default: list popular models
        list_popular_video_models()

