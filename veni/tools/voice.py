"""
Voice tool for Veni AI.
"""

from typing import Any, Dict

from veni.tools.base import AITool


class VoiceTool(AITool):
    """Tool for text-to-speech."""

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "speak"

    @property
    def description(self) -> str:
        return "Speak a message aloud using the text-to-speech engine."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to speak aloud."}
            },
            "required": ["text"],
        }

    def execute(self, text: str) -> str:
        """Speak the text using the bot's voice engine."""
        from veni.voice import VoiceEngine

        if self.bot.voice_engine is None:
            try:
                self.bot.voice_engine = VoiceEngine()
            except Exception as e:
                return f"Error initializing voice engine: {e}"

        try:
            self.bot.voice_engine.speak(text)
            return "Message spoken aloud."
        except Exception as e:
            return f"Error speaking message: {e}"
