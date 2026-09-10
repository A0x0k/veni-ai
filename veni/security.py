"""
Security and data protection utilities for Veni AI.
"""

import re
from typing import List, Pattern


class Redactor:
    """Handles redaction of sensitive information from text."""

    PATTERNS: List[Pattern] = [
        # OpenAI API Keys
        re.compile(r"sk-[a-zA-Z0-9]{48}"),
        # Anthropic API Keys
        re.compile(r"sk-ant-sid01-[a-zA-Z0-9\-_]{90,100}"),
        re.compile(r"sk-ant-[a-zA-Z0-9]{50,}"),
        # Google/Gemini API Keys
        re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
        # Generic Bearer Tokens
        re.compile(r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", re.IGNORECASE),
        # AWS Access Key ID
        re.compile(r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])"),
        # AWS Secret Access Key
        re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"),
        # GitHub Personal Access Token
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        # Common Emails
        re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
        # IPv4 Addresses
        re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    ]

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def redact(self, text: str) -> str:
        """Replace sensitive patterns with [REDACTED]."""
        if not self.enabled or not text:
            return text

        redacted_text = text
        for pattern in self.PATTERNS:
            redacted_text = pattern.sub("[REDACTED]", redacted_text)

        return redacted_text


# Global redactor instance
redactor = Redactor()
