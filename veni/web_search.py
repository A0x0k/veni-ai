"""
Multi-Engine Web Search for Veni AI.

Searches across multiple engines and merges results:
- DuckDuckGo (default, no API key)
- Brave Search (API key recommended)
- Bing Search (API key)
- Google Scholar (academic papers)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None  # type: ignore

try:
    import requests
except ImportError:
    requests = None  # type: ignore


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str
    source: str  # "duckduckgo", "brave", "bing", "scholar"
    score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }


class MultiEngineSearch:
    """
    Search across multiple engines and merge results.

    Usage:
        search = MultiEngineSearch()
        results = search.search("python async await", engines=["ddg", "brave"])
    """

    def __init__(self, cache: Any = None):
        self._cache = cache
        self._engines = {
            "ddg": self._search_ddg,
            "brave": self._search_brave,
            "bing": self._search_bing,
            "scholar": self._search_scholar,
        }
        self._api_keys: Dict[str, str] = {}

    def set_api_key(self, engine: str, key: str):
        """Set API key for a search engine."""
        self._api_keys[engine] = key

    def search(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        max_results: int = 10,
        region: str = "wt-wt",
        time_range: str = "",
    ) -> List[SearchResult]:
        """
        Search across multiple engines.

        Args:
            query: Search query
            engines: List of engines to use (default: ["ddg"])
            max_results: Max results per engine
            region: Region code (ddg only)
            time_range: Time filter (d/w/m/y)

        Returns:
            Merged and deduplicated results
        """
        if engines is None:
            engines = ["ddg"]

        # Check cache
        cache_key = f"search:{query}:{','.join(engines)}:{max_results}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                return cached

        all_results: List[SearchResult] = []

        for engine in engines:
            search_func = self._engines.get(engine)
            if search_func is None:
                continue

            try:
                results = search_func(query, max_results, region, time_range)
                all_results.extend(results)
            except Exception as exc:
                logger.debug("Search engine %s failed: %s", engine, exc)

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)

        # Cache results
        if self._cache:
            self._cache.set(cache_key, unique_results, ttl=1800)

        return unique_results[: max_results * len(engines)]

    def _search_ddg(
        self,
        query: str,
        max_results: int,
        region: str,
        time_range: str,
    ) -> List[SearchResult]:
        """Search DuckDuckGo."""
        if DDGS is None:
            return []

        results = []
        kwargs = {"keywords": query, "max_results": max_results}
        if region:
            kwargs["region"] = region
        if time_range:
            kwargs["timelimit"] = time_range

        with DDGS() as ddgs:
            for r in ddgs.text(**kwargs):
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source="duckduckgo",
                    )
                )

        return results

    def _search_brave(
        self,
        query: str,
        max_results: int,
        region: str,
        time_range: str,
    ) -> List[SearchResult]:
        """Search Brave Search API."""
        if requests is None:
            return []

        api_key = self._api_keys.get("brave")
        if not api_key:
            return []

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": query,
            "count": min(max_results, 20),
        }
        if time_range:
            params["freshness"] = time_range

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("web", {}).get("results", []):
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("description", ""),
                    source="brave",
                )
            )

        return results

    def _search_bing(
        self,
        query: str,
        max_results: int,
        region: str,
        time_range: str,
    ) -> List[SearchResult]:
        """Search Bing Web Search API."""
        if requests is None:
            return []

        api_key = self._api_keys.get("bing")
        if not api_key:
            return []

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {"q": query, "count": min(max_results, 50)}
        if time_range:
            params["freshness"] = time_range

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("webPages", {}).get("value", []):
            results.append(
                SearchResult(
                    title=r.get("name", ""),
                    url=r.get("url", ""),
                    snippet=r.get("snippet", ""),
                    source="bing",
                )
            )

        return results

    def _search_scholar(
        self,
        query: str,
        max_results: int,
        region: str,
        time_range: str,
    ) -> List[SearchResult]:
        """Search Google Scholar via scraping."""
        if requests is None:
            return []

        url = f"https://scholar.google.com/scholar?q={quote(query)}&num={max_results}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as exc:
            logger.debug("Google Scholar request failed: %s", exc)
            return []

        # Simple HTML parsing for scholar results
        results = []
        html = resp.text

        import re

        titles = re.findall(
            r'<h3[^>]*class="[^"]*gs_rt[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            re.DOTALL,
        )
        snippets = re.findall(
            r'<div[^>]*class="[^"]*gs_rs[^"]*"[^>]*>(.*?)</div>',
            html,
            re.DOTALL,
        )

        for i, (href, title_html) in enumerate(titles[:max_results]):
            # Clean title HTML
            title = re.sub(r"<[^>]+>", "", title_html).strip()
            snippet = ""
            if i < len(snippets):
                snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()

            results.append(
                SearchResult(
                    title=title,
                    url=href,
                    snippet=snippet[:300],
                    source="scholar",
                )
            )

        return results

    def compare_engines(
        self, query: str, max_results: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """Search all available engines and compare results."""
        comparison = {}
        for engine in self._engines:
            try:
                results = self.search(query, engines=[engine], max_results=max_results)
                comparison[engine] = results
            except Exception as exc:
                logger.debug("Engine comparison failed for %s: %s", engine, exc)
                comparison[engine] = []
        return comparison
