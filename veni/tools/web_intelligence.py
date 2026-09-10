"""
Web Intelligence Tool for Veni AI.

Unified interface for all web capabilities:
- Multi-engine search
- Web scraping
- PDF extraction
- API access
- Archive lookup
"""

from typing import Any, Dict, List, Optional

from veni.tools.base import AITool
from veni.web_scraper import (
    APIClient,
    WebArchive,
    WebScraper,
    detect_urls,
)
from veni.web_search import MultiEngineSearch


class WebIntelligenceTool(AITool):
    """
    Unified web intelligence tool for Veni AI.

    Actions:
    - search: Multi-engine web search
    - scrape: Fetch and extract content from a URL
    - scrape_urls: Fetch multiple URLs at once
    - pdf: Extract text from a PDF URL
    - api: Call a REST API endpoint
    - archive: Find archived versions of a page
    - detect_urls: Find URLs in a block of text
    """

    def __init__(self, bot: Any):
        self.bot = bot
        self._search = MultiEngineSearch(cache=getattr(bot, "veni_cache", None))
        self._scraper = WebScraper(cache=getattr(bot, "veni_cache", None))
        self._api = APIClient(cache=getattr(bot, "veni_cache", None))
        self._archive = WebArchive(cache=getattr(bot, "veni_cache", None))

    @property
    def name(self) -> str:
        return "web_intelligence"

    @property
    def description(self) -> str:
        return (
            "Comprehensive web intelligence tool. "
            "Can search the web, scrape pages, extract PDFs, call APIs, "
            "and access web archives. "
            "Actions: search, scrape, scrape_urls, pdf, api, archive, detect_urls"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "search",
                        "scrape",
                        "scrape_urls",
                        "pdf",
                        "api",
                        "archive",
                        "detect_urls",
                    ],
                    "description": "The action to perform.",
                },
                "query": {
                    "type": "string",
                    "description": "Search query or URL (depends on action).",
                },
                "url": {
                    "type": "string",
                    "description": "URL for scrape/pdf actions.",
                },
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs for scrape_urls.",
                },
                "api_url": {
                    "type": "string",
                    "description": "API endpoint URL.",
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                    "description": "HTTP method for API calls.",
                    "default": "GET",
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers for API calls.",
                },
                "body": {
                    "type": "string",
                    "description": "Request body for POST/PUT.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max results for search.",
                    "default": 5,
                },
                "text": {
                    "type": "string",
                    "description": "Text to scan for URLs.",
                },
            },
            "required": ["action"],
        }

    def execute(
        self,
        action: str = "search",
        query: str = "",
        url: str = "",
        urls: Optional[List[str]] = None,
        api_url: str = "",
        method: str = "GET",
        headers: Optional[Dict] = None,
        body: str = "",
        max_results: int = 5,
        text: str = "",
        **kwargs: Any,
    ) -> str:
        """Execute a web intelligence action."""
        if action == "search":
            return self._search_web(query, max_results)
        elif action == "scrape":
            return self._scrape_page(url or query)
        elif action == "scrape_urls":
            return self._scrape_multiple(urls or [])
        elif action == "pdf":
            return self._extract_pdf(url or query)
        elif action == "api":
            return self._call_api(api_url, method, headers, body)
        elif action == "archive":
            return self._lookup_archive(url or query)
        elif action == "detect_urls":
            return self._find_urls(text)
        else:
            return f"Unknown action: {action}"

    def _search_web(self, query: str, max_results: int) -> str:
        """Search the web using multiple engines."""
        if not query:
            return "Error: query is required for search."
        results = self._search.search(query, max_results=max_results)
        if not results:
            return f"No results found for '{query}'."
        output = f"Search results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r.title}\n"
            output += f"   URL: {r.url}\n"
            output += f"   {r.snippet[:200]}\n\n"
        return output

    def _scrape_page(self, url: str) -> str:
        """Scrape a single web page."""
        if not url:
            return "Error: URL is required for scrape."
        result = self._scraper.scrape_page(url)
        if not result:
            return f"Failed to scrape: {url}"
        output = f"Scraped: {url}\n"
        output += f"Title: {result.title or 'Untitled'}\n\n"
        output += result.text[:3000]
        return output

    def _scrape_multiple(self, urls: List[str]) -> str:
        """Scrape multiple URLs."""
        if not urls:
            return "Error: URLs list is required for scrape_urls."
        results = []
        for url in urls:
            r = self._scraper.scrape_page(url)
            if r:
                results.append(f"- {url}: {r.title or 'Untitled'}")
        if not results:
            return "No URLs scraped successfully."
        return "Scraped URLs:\n" + "\n".join(results)

    def _extract_pdf(self, url: str) -> str:
        """Extract text from a PDF."""
        if not url:
            return "Error: URL is required for pdf."
        result = self._scraper.extract_pdf(url)
        if not result:
            return f"Failed to extract PDF: {url}"
        output = f"PDF: {url}\n"
        output += f"Title: {result.title or 'Untitled PDF'}\n\n"
        output += result.text[:3000]
        return output

    def _call_api(
        self, url: str, method: str, headers: Optional[Dict], body: str
    ) -> str:
        """Call a REST API."""
        if not url:
            return "Error: api_url is required for api action."
        result = self._api.call_api(url, method, headers, body)
        return f"API Response ({method} {url}):\n{result[:3000]}"

    def _lookup_archive(self, url: str) -> str:
        """Look up archived versions of a URL."""
        if not url:
            return "Error: URL is required for archive."
        result = self._archive.get_availability(url)
        return f"Archive info for {url}:\n{str(result)[:2000]}"

    def _find_urls(self, text: str) -> str:
        """Find URLs in text."""
        if not text:
            return "Error: text is required for detect_urls."
        urls = detect_urls(text)
        if not urls:
            return "No URLs found in the provided text."
        return f"Found {len(urls)} URL(s):\n" + "\n".join(f"- {u}" for u in urls)
