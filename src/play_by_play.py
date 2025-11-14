"""Play-by-play agent for generating video storyboards using LLMs."""

import json
from typing import Optional

from loguru import logger

from .config import settings
from .models import Storyboard


SYSTEM_PROMPT = """You are a "video storyboard AI" for an educational video generator that uses a 6-second video model. Given a user's request, you must output a timeline of keyframe prompts that visually explain the concept over time.

Output JSON with:
* duration_ms: total duration in milliseconds
* fps: assumed frame rate (default 24)
* global_style: description of visual style and subject appearance
* keyframes: an object mapping time in ms (as strings) to a short, vivid visual description of what is on screen at that moment (no dialogue, visual actions only).

The keyframes should be monotonically increasing timestamps. Be specific and vivid in your descriptions.
Each keyframe description should be a complete visual snapshot that the video model can understand independently.

Only output valid JSON. Do not include any explanations or markdown code blocks."""


class PlayByPlayAgent:
    """Agent for generating play-by-play storyboards from user prompts."""

    def __init__(self):
        self.provider = settings.llm_provider
        
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.model = settings.llm_model
            except ImportError:
                raise ValueError(
                    "OpenAI package not installed. Install with: pip install openai"
                )
        elif self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=settings.anthropic_api_key)
                self.model = settings.llm_model
            except ImportError:
                raise ValueError(
                    "Anthropic package not installed. Install with: pip install anthropic"
                )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_storyboard(
        self,
        user_prompt: str,
        duration_hint_seconds: Optional[int] = None,
        style_preference: Optional[str] = None,
    ) -> Storyboard:
        """
        Generate a storyboard from a user prompt.

        Args:
            user_prompt: User's description of the video to generate
            duration_hint_seconds: Optional hint for desired video duration
            style_preference: Optional style preference

        Returns:
            Storyboard object with keyframes and metadata
        """
        logger.info(f"Generating storyboard for prompt: {user_prompt}")

        # Build the user message
        user_message = user_prompt
        if duration_hint_seconds:
            user_message += f"\n\nTarget duration: approximately {duration_hint_seconds} seconds."
        if style_preference:
            user_message += f"\n\nStyle preference: {style_preference}"

        try:
            if self.provider == "openai":
                storyboard_json = self._generate_openai(user_message)
            else:  # anthropic
                storyboard_json = self._generate_anthropic(user_message)

            # Parse and validate the storyboard
            storyboard = Storyboard.model_validate_json(storyboard_json)
            logger.success(
                f"Generated storyboard with {len(storyboard.keyframes)} keyframes, "
                f"duration: {storyboard.duration_ms}ms"
            )
            return storyboard

        except Exception as e:
            logger.error(f"Failed to generate storyboard: {e}")
            raise

    def _generate_openai(self, user_message: str) -> str:
        """Generate storyboard using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    def _generate_anthropic(self, user_message: str) -> str:
        """Generate storyboard using Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message},
            ],
        )
        
        # Extract the JSON from the response
        content = response.content[0].text
        
        # Try to extract JSON if it's wrapped in markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        return content

