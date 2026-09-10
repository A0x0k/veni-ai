"""
Image Generation Tool for Veni AI.

Allows the AI to generate high-quality images from text descriptions.
Primary engine: OpenAI DALL-E 3.
"""

import logging
import os
import requests
from pathlib import Path
from typing import Any, Dict, Optional

from veni.tools.base import AITool
from veni.config import config

logger = logging.getLogger("veni.tools.image_gen")


class ImageGenTool(AITool):
    """
    Tool for generating images from text prompts.
    """

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "generate_image"

    @property
    def description(self) -> str:
        return (
            "Generate an image from a text description. Use this to create "
            "visual content, logos, or illustrations. Provide a detailed prompt."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "A detailed description of the image to generate.",
                },
                "size": {
                    "type": "string",
                    "enum": ["256x256", "512x512", "1024x1024"],
                    "default": "1024x1024",
                    "description": "The dimensions of the generated image.",
                }
            },
            "required": ["prompt"],
        }

    def execute(self, prompt: str, size: str = "1024x1024") -> str:
        """Execute image generation via OpenAI API."""
        api_key = config.get("api_keys.openai") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OpenAI API key is missing. Image generation requires an OpenAI key."

        self.bot.show_warning(f"🎨 Generating image for: '{prompt[:50]}...'")
        
        try:
            url = "https://api.openai.com/v1/images/generations"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": size
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            image_url = result['data'][0]['url']
            
            # Download the image to workspace
            import time
            filename = f"generated_{int(time.time())}.png"
            path = self.bot.workspace_root / filename
            
            img_data = requests.get(image_url).content
            path.write_bytes(img_data)
            
            return (
                f"✅ Image generated successfully!\n"
                f"Prompt: {prompt}\n"
                f"File saved to: {filename}\n"
                f"Remote URL: {image_url}"
            )
            
        except Exception as e:
            logger.error("Image generation failed: %s", e)
            return f"Error generating image: {str(e)}"
