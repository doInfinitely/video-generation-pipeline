"""Test script for the video generation API."""

import time
import requests
from loguru import logger


API_BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    logger.info("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    response.raise_for_status()
    logger.success(f"Health check: {response.json()}")


def test_video_generation():
    """Test video generation workflow."""
    logger.info("Testing video generation...")
    
    # Submit a video generation request
    request_data = {
        "user_prompt": "A simple animation of a red cube rotating 360 degrees on a white background",
        "duration_hint_seconds": 6,
        "style_preference": "Simple 3D animation",
    }
    
    logger.info("Submitting video generation request...")
    response = requests.post(f"{API_BASE_URL}/generate", json=request_data)
    response.raise_for_status()
    
    result = response.json()
    job_id = result["job_id"]
    logger.success(f"Job created: {job_id}")
    
    # Poll for status
    logger.info("Polling for job status...")
    max_attempts = 60  # 5 minutes with 5-second intervals
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}")
        response.raise_for_status()
        
        status = response.json()
        logger.info(f"Status: {status['status']}, Progress: {status['progress']:.1%}")
        
        if status["status"] == "completed":
            logger.success("Video generation completed!")
            
            # Download the video
            logger.info("Downloading video...")
            response = requests.get(f"{API_BASE_URL}/video/{job_id}")
            response.raise_for_status()
            
            output_path = f"test_video_{job_id}.mp4"
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.success(f"Video saved to: {output_path}")
            return output_path
        
        elif status["status"] == "failed":
            logger.error(f"Video generation failed: {status.get('error_message')}")
            return None
        
        time.sleep(5)
        attempt += 1
    
    logger.error("Timed out waiting for video generation")
    return None


def main():
    """Run API tests."""
    try:
        test_health_check()
        test_video_generation()
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to API. Make sure the server is running.")
        logger.info("Start the server with: python main.py")
    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    main()

