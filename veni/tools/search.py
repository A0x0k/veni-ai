"""
Web Search tool for Veni AI.

Uses MultiEngineSearch for multi-engine search capabilities.
"""

from typing import Any, Dict

from veni.tools.base import AITool


class SearchTool(AITool):
    """Tool for searching the web using multiple engines."""

    def __init__(self, bot: Any):
        self.bot = bot
        self._multi_search = None

    def _get_search(self):
        """Lazy-load MultiEngineSearch."""
        if self._multi_search is None:
            from veni.web_search import MultiEngineSearch

            cache = getattr(self.bot, "veni_cache", None)
            self._multi_search = MultiEngineSearch(cache=cache)
        return self._multi_search

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for up-to-date information on any topic."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5).",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, query: str, max_results: int = 5) -> str:
        """Search the web and return formatted results."""
        try:
            search = self._get_search()
            results = search.search(query, max_results=max_results)
        except Exception as e:
            return f"Search failed: {e}"

        if not results:
            return "No results found."

        formatted = f"Web Search Results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            formatted += f"{i}. {r.title}\n"
            formatted += f"Source: {r.url}\n"
            formatted += f"Content: {r.snippet[:300]}\n\n"

        formatted += (
            "Use the above information to provide a detailed, up-to-date answer."
        )
        return formatted
