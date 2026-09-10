"""
Voice & Audio handling for Veni AI.

Uses lazy imports so the module loads even if
speech_recognition or pyttsx3 are not installed.
"""

import threading
from typing import Optional


class VoiceEngine:
    """Handles speech recognition and text-to-speech."""

    def __init__(self):
        # Lazy import speech_recognition
        try:
            import speech_recognition as sr
        except ImportError:
            raise RuntimeError(
                "speech_recognition is not installed. "
                "Install with: pip install SpeechRecognition"
            )

        # Lazy import pyttsx3
        try:
            import pyttsx3
        except ImportError:
            raise RuntimeError(
                "pyttsx3 is not installed. " "Install with: pip install pyttsx3"
            )

        self._sr = sr
        self._pyttsx3 = pyttsx3
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 170)  # Speed of speech
        self.is_listening = False
        self.microphone = sr.Microphone()

        # Configure microphone for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen_once(self) -> Optional[str]:
        """Listen for a single command."""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5)
            return self.recognizer.recognize_google(audio)
        except self._sr.WaitTimeoutError:
            print("Listening timed out.")
            return None
        except Exception as e:
            print(f"Voice recognition failed: {e}")
            return None

    def speak(self, text: str):
        """Speak text aloud."""
        # Clean text for TTS
        text = self._clean_text(text)
        threading.Thread(target=self.engine.say, args=(text,)).start()

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove code blocks and other noise for TTS."""
        import re

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "code block", text)
        # Remove inline code
        text = re.sub(r"`[^`]*`", "code", text)
        # Remove URLs
        text = re.sub(r"http\S+", "link", text)
        return text[:500]  # Limit length to avoid long monologues
