"""
Browser Automation Tool for Veni AI.

Uses Playwright to provide the AI with "eyes and hands" on the web:
- Navigation
- Clicking and typing
- Form submission
- Screenshot capture
- Content extraction
"""

import logging
from typing import Any, Dict, Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None  # type: ignore

from veni.tools.base import AITool

logger = logging.getLogger("veni.tools.browser")


class BrowserTool(AITool):
    """
    Tool for interactive browser automation.
    """

    def __init__(self, bot: Any):
        self.bot = bot
        self._playwright = None
        self._browser = None
        self._page = None

    @property
    def name(self) -> str:
        return "browser_automation"

    @property
    def description(self) -> str:
        return (
            "Interact with a web browser. Use this to navigate to URLs, "
            "click buttons, type text, submit forms, and extract content. "
            "Actions: 'navigate', 'click', 'type', 'extract', 'screenshot'."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "click", "type", "extract", "screenshot"],
                    "description": "The action to perform.",
                },
                "url": {
                    "type": "string",
                    "description": "URL for 'navigate' action.",
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for 'click' or 'type' actions.",
                },
                "text": {
                    "type": "string",
                    "description": "Text to type for 'type' action.",
                },
                "wait_for": {
                    "type": "string",
                    "description": "Optional CSS selector to wait for after action.",
                },
            },
            "required": ["action"],
        }

    def execute(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        wait_for: Optional[str] = None,
        visible: bool = False,
    ) -> str:
        """Execute browser automation actions."""
        if sync_playwright is None:
            return "Error: Playwright is not installed. Run 'pip install playwright && playwright install chromium'."

        try:
            if not self._browser:
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(headless=not visible)
                self._page = self._browser.new_page()

            if action == "navigate":
                if not url:
                    return "Error: URL is required for 'navigate' action."
                self._page.goto(url)
                if wait_for:
                    self._page.wait_for_selector(wait_for, timeout=5000)
                return f"Navigated to {url}. Title: {self._page.title()}"

            elif action == "click":
                if not selector:
                    return "Error: Selector is required for 'click' action."
                self._page.click(selector)
                if wait_for:
                    self._page.wait_for_selector(wait_for, timeout=5000)
                return f"Clicked element: {selector}"

            elif action == "type":
                if not selector or text is None:
                    return "Error: Selector and text are required for 'type' action."
                self._page.fill(selector, text)
                if wait_for:
                    self._page.wait_for_selector(wait_for, timeout=5000)
                return f"Typed text into {selector}"

            elif action == "extract":
                content = self._page.content()
                from veni.web_scraper import WebScraper
                scraper = WebScraper()
                clean_text = scraper.extract_from_text(content)
                return f"Content extracted from {self._page.url}:\n\n{clean_text[:5000]}"

            elif action == "screenshot":
                import time
                filename = f"screenshot_{int(time.time())}.png"
                path = self.bot.workspace_root / filename
                self._page.screenshot(path=str(path))
                return f"Screenshot saved to {filename}"

            else:
                return f"Error: Unknown action '{action}'"

        except Exception as e:
            logger.error("Browser automation error: %s", e)
            return f"Error during browser automation: {str(e)}"

    def cleanup(self):
        """Close the browser session."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
