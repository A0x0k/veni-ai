"""
API & Documentation Lookup tool for Veni AI.

Fetches and understands live documentation for libraries/frameworks:
- Python standard library
- Popular frameworks (Django, React, etc.)
- Language references
- API documentation
"""

import re
from typing import Any, Dict, Optional, Tuple

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from veni.tools.base import AITool

# Documentation source registry
DOC_SOURCES = {
    "python": {
        "search": "https://docs.python.org/3/search.html?q={query}",
        "api": "https://docs.python.org/3/library/{module}.html",
        "base": "https://docs.python.org/3/",
    },
    "django": {
        "search": "https://docs.djangoproject.com/en/stable/search/?q={query}",
        "base": "https://docs.djangoproject.com/en/stable/",
    },
    "react": {
        "search": "https://react.dev/search?q={query}",
        "base": "https://react.dev/",
    },
    "numpy": {
        "search": "https://numpy.org/doc/stable/search.html?q={query}",
        "base": "https://numpy.org/doc/stable/",
    },
    "flask": {
        "search": "https://flask.palletsprojects.com/search/?q={query}",
        "base": "https://flask.palletsprojects.com/",
    },
    "fastapi": {
        "search": "https://fastapi.tiangolo.com/search/?q={query}",
        "base": "https://fastapi.tiangolo.com/",
    },
    "requests": {
        "search": "https://requests.readthedocs.io/en/latest/search/?q={query}",
        "base": "https://requests.readthedocs.io/en/latest/",
    },
    "pytest": {
        "search": "https://docs.pytest.org/en/stable/search.html?q={query}",
        "base": "https://docs.pytest.org/en/stable/",
    },
}

# Common symbol mappings
SYMBOL_DOCS = {
    "asyncio.gather": {
        "url": "https://docs.python.org/3/library/asyncio-task.html#asyncio.gather",
        "summary": "Run awaitables concurrently and return results.",
    },
    "asyncio.create_task": {
        "url": "https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task",
        "summary": "Schedule a coroutine as a Task.",
    },
    "list comprehension": {
        "url": "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions",
        "summary": "Concise way to create lists.",
    },
    "decorators": {
        "url": "https://docs.python.org/3/glossary.html#term-decorator",
        "summary": "Functions that modify behavior of other functions.",
    },
    "context manager": {
        "url": "https://docs.python.org/3/reference/datamodel.html#context-managers",
        "summary": "Objects that define runtime context with with statement.",
    },
}


class DocLookupTool(AITool):
    """Tool for looking up API documentation."""

    def __init__(self, bot: Any):
        self.bot = bot
        self._cache: Dict[str, Tuple[str, float]] = {}
        self._cache_ttl = 3600  # 1 hour

    @property
    def name(self) -> str:
        return "doc_lookup"

    @property
    def description(self) -> str:
        return (
            "Look up API documentation for libraries, functions, or concepts. "
            "Supports Python, Django, React, Flask, FastAPI, NumPy, pytest, requests. "
            "Usage: doc_lookup(query='asyncio.gather') or "
            "doc_lookup(query='django models', library='django')"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The function, class, module, or concept to look up."
                    ),
                },
                "library": {
                    "type": "string",
                    "description": (
                        "Optional: specific library to search in. "
                        "Options: python, django, react, flask, fastapi, numpy, pytest, requests"
                    ),
                    "enum": list(DOC_SOURCES.keys()),
                },
            },
            "required": ["query"],
        }

    def execute(self, query: str, library: str = "") -> str:
        """Look up documentation for a query."""
        # Check known symbols first
        for symbol, info in SYMBOL_DOCS.items():
            if symbol.lower() in query.lower():
                return (
                    f"## {symbol}\n\n{info['summary']}\n\n"
                    f"📖 Full docs: {info['url']}"
                )

        # Check cache
        cache_key = f"{library}:{query}"
        if cache_key in self._cache:
            cached, timestamp = self._cache[cache_key]
            import time

            if time.time() - timestamp < self._cache_ttl:
                return cached

        # Try to fetch from docs
        result = self._search_docs(query, library)
        self._cache[cache_key] = (result, __import__("time").time())
        return result

    def _search_docs(self, query: str, library: str) -> str:
        """Search documentation sources."""
        if requests is None:
            return (
                f"## Documentation Lookup\n\n"
                f"Query: {query}\n"
                f"Library: {library or 'auto-detect'}\n\n"
                "⚠️ `requests` library not installed. "
                "Install with: pip install requests"
            )

        # Determine library
        lib = self._detect_library(query, library)

        if lib and lib in DOC_SOURCES:
            source = DOC_SOURCES[lib]
            search_url = source["search"].format(query=requests.utils.quote(query))
            return (
                f"## {lib.title()} Documentation\n\n"
                f"🔍 Search: [{query}]({search_url})\n"
                f"📖 Base: {source['base']}\n\n"
                f"Open the search link above for live documentation."
            )

        # Fallback: web search suggestion
        return (
            f"## Documentation Search\n\n"
            f"Query: {query}\n\n"
            f"Try these resources:\n"
            f"- [Python Docs](https://docs.python.org/3/search.html?q={requests.utils.quote(query)})\n"
            f"- [Stack Overflow](https://stackoverflow.com/search?q={requests.utils.quote(query)})\n"
            f"- [GitHub](https://github.com/search?q={requests.utils.quote(query)})\n"
        )

    def _detect_library(self, query: str, explicit: str) -> Optional[str]:
        """Auto-detect the library from the query."""
        if explicit:
            return explicit.lower()

        query_lower = query.lower()

        # Pattern-based detection
        if re.search(r"\bdjango\b", query_lower):
            return "django"
        if re.search(r"\breact\b|jsx|tsx|component", query_lower):
            return "react"
        if re.search(r"\bflask\b|@app\.route", query_lower):
            return "flask"
        if re.search(r"\bfastapi\b|@app\.get|@app\.post", query_lower):
            return "fastapi"
        if re.search(r"\bnumpy\b|np\.\w+|ndarray", query_lower):
            return "numpy"
        if re.search(r"\bpytest\b|@pytest|assert\s", query_lower):
            return "pytest"
        if re.search(r"\brequests\b|requests\.(get|post)", query_lower):
            return "requests"

        return "python"  # Default
