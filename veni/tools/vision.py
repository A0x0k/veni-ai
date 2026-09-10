"""
Vision Analysis Tool for Veni AI.

Allows the AI to "see" and analyze images:
- UI/Layout analysis
- Code snippet extraction from screenshots
- General image description
- Debugging visual issues
"""

import logging
from typing import Any, Dict, Optional

from veni.tools.base import AITool

logger = logging.getLogger("veni.tools.vision")


class VisionTool(AITool):
    """
    Tool for analyzing images using vision-capable AI models.
    """

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "analyze_vision"

    @property
    def description(self) -> str:
        return (
            "Analyze an image or screenshot. Provide a file path to an image, "
            "and I will describe its contents, analyze UI layout, or extract "
            "information from it using my vision capabilities."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file to analyze.",
                },
                "task": {
                    "type": "string",
                    "description": "Optional specific task (e.g., 'extract code', 'check UI layout').",
                }
            },
            "required": ["image_path"],
        }

    def execute(self, image_path: str, task: Optional[str] = None) -> str:
        """Execute vision analysis."""
        path = self.bot.resolve_workspace_path(image_path)
        if not path.exists():
            return f"Error: Image file not found at {image_path}"

        prompt = "Analyze this image."
        if task:
            prompt += f" Specific task: {task}"

        # Build multi-modal message
        messages = [
            {
                "role": "user",
                "content": prompt,
                "images": [str(path)]
            }
        ]

        try:
            # We use the AI client directly for a single-shot vision request
            # Note: The core loop already supports images, but this tool
            # provides a structured way for the AI to 'call' its own eyes.
            response = ""
            for chunk in self.bot.ai_client.chat(messages, stream=True):
                response += chunk

            return f"Vision Analysis for {path.name}:\n\n{response}"
        except Exception as e:
            logger.error("Vision analysis failed: %s", e)
            return f"Error analyzing image: {str(e)}"
