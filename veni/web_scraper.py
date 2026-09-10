"""
Web Scraping & Content Extraction for Veni AI.

Capabilities:
- Full page scraping with boilerplate removal
- PDF text extraction
- REST API client
- Web Archive (Wayback Machine) access
- Smart URL detection and auto-fetch
- Rate limiting and caching
"""

import io
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore


# Common boilerplate selectors to remove
BOILERPLATE_SELECTORS = [
    "nav",
    "footer",
    "header",
    "aside",
    ".sidebar",
    ".ad",
    ".ads",
    ".advertisement",
    ".cookie-banner",
    ".cookie-consent",
    "#cookie-banner",
    ".social-share",
    ".comments",
    ".newsletter-signup",
    ".popup",
    ".modal",
    ".overlay",
    ".breadcrumb",
    ".pagination",
    "script",
    "style",
    "noscript",
    "iframe",
]

# Content-rich HTML tags (in order of importance)
CONTENT_TAGS = ["article", "main", "section", "div"]


@dataclass
class ScrapedContent:
    """Content extracted from a web page."""

    url: str
    title: str
    text: str
    html: str = ""
    links: List[str] = None
    images: List[str] = None
    metadata: Dict[str, str] = None
    word_count: int = 0
    fetch_time: float = 0.0

    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.images is None:
            self.images = []
        if self.metadata is None:
            self.metadata = {}

    def summary(self, max_chars: int = 500) -> str:
        """Get a summary of the content."""
        parts = [f"# {self.title}", f"\nSource: {self.url}\n"]
        if self.word_count:
            parts.append(f"({self.word_count} words)\n")
        parts.append(self.text[:max_chars])
        if len(self.text) > max_chars:
            parts.append("...")
        return "\n".join(parts)


class WebScraper:
    """
    Advanced web scraper with content extraction.

    Features:
    - Boilerplate removal
    - Readability-style content extraction
    - PDF parsing
    - Metadata extraction
    """

    def __init__(self, cache: Any = None, rate_limit: float = 0.5):
        self._cache = cache
        self._rate_limit = rate_limit
        self._last_request: Dict[str, float] = {}
        self._session = requests.Session() if requests else None
        if self._session:
            self._session.headers.update(
                {
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; VeniAI/1.0; "
                        "+https://github.com/neoastra303/Veni-AI)"
                    )
                }
            )

    def scrape(
        self,
        url: str,
        extract_links: bool = True,
        extract_images: bool = False,
        max_length: int = 10000,
    ) -> Optional[ScrapedContent]:
        """
        Scrape a web page and extract clean content.

        Args:
            url: URL to scrape
            extract_links: Whether to extract links
            extract_images: Whether to extract images
            max_length: Maximum text length

        Returns:
            ScrapedContent or None on failure
        """
        if not self._session:
            return None

        # Check cache
        cache_key = f"scrape:{url}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                return cached

        # Rate limiting
        domain = urlparse(url).netloc
        self._wait_for_rate_limit(domain)

        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception:
            return None

        # Check if it's a PDF
        content_type = resp.headers.get("Content-Type", "")
        if "pdf" in content_type.lower():
            return self._extract_pdf(resp.content, url)

        return self._extract_html(
            resp.text, url, extract_links, extract_images, max_length
        )

    def scrape_multiple(
        self,
        urls: List[str],
        max_length: int = 10000,
    ) -> List[ScrapedContent]:
        """Scrape multiple URLs."""
        results = []
        for url in urls:
            content = self.scrape(url, max_length=max_length)
            if content:
                results.append(content)
        return results

    def extract_from_text(self, text: str) -> str:
        """Extract clean text from HTML string."""
        if BeautifulSoup is None:
            # Fallback: strip all HTML tags
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = re.sub(r"\s+", " ", clean).strip()
            return clean

        soup = BeautifulSoup(text, "html.parser")

        # Remove boilerplate
        for selector in BOILERPLATE_SELECTORS:
            if selector.startswith("."):
                for elem in soup.find_all(class_=selector[1:]):
                    elem.decompose()
            elif selector.startswith("#"):
                elem = soup.find(id=selector[1:])
                if elem:
                    elem.decompose()
            else:
                for elem in soup.find_all(selector):
                    elem.decompose()

        return soup.get_text(separator="\n", strip=True)

    # --- PDF Extraction ---

    def _extract_pdf(self, pdf_content: bytes, url: str) -> Optional[ScrapedContent]:
        """Extract text from a PDF."""
        if PdfReader is None:
            return None

        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            text_parts = []

            for page in reader.pages:
                text_parts.append(page.extract_text() or "")

            text = "\n\n".join(text_parts)

            return ScrapedContent(
                url=url,
                title=f"PDF: {urlparse(url).path.split('/')[-1]}",
                text=text[:50000],
                word_count=len(text.split()),
                fetch_time=time.time(),
            )
        except Exception:
            return None

    # --- HTML Extraction ---

    def _extract_html(
        self,
        html: str,
        url: str,
        extract_links: bool,
        extract_images: bool,
        max_length: int,
    ) -> Optional[ScrapedContent]:
        """Extract clean content from HTML."""
        if BeautifulSoup is None:
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return ScrapedContent(
                url=url,
                title=urlparse(url).path.split("/")[-1] or url,
                text=text[:max_length],
                word_count=len(text.split()),
                fetch_time=time.time(),
            )

        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", title)

        # Extract metadata
        metadata = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        # Find main content
        main_content = self._find_main_content(soup)

        # Remove boilerplate from main content
        for selector in BOILERPLATE_SELECTORS:
            if selector.startswith("."):
                for elem in main_content.find_all(class_=selector[1:]):
                    elem.decompose()
            elif selector.startswith("#"):
                elem = main_content.find(id=selector[1:])
                if elem:
                    elem.decompose()
            else:
                for elem in main_content.find_all(selector):
                    elem.decompose()

        # Extract text
        text = main_content.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        # Extract links
        links = []
        if extract_links:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("http://", "https://")):
                    links.append(href)

        # Extract images
        images = []
        if extract_images:
            for img in soup.find_all("img", src=True):
                images.append(img["src"])

        return ScrapedContent(
            url=url,
            title=title,
            text=text[:max_length],
            links=links[:50],
            images=images[:20],
            metadata=metadata,
            word_count=len(text.split()),
            fetch_time=time.time(),
        )

    def _find_main_content(self, soup: BeautifulSoup) -> Any:
        """Find the main content area of a page."""
        # Try semantic HTML5 tags first
        for tag in ["article", "main"]:
            elem = soup.find(tag)
            if elem and len(elem.get_text(strip=True)) > 100:
                return elem

        # Try content-rich divs
        for tag in CONTENT_TAGS:
            for elem in soup.find_all(tag):
                text_len = len(elem.get_text(strip=True))
                if text_len > 200:
                    return elem

        # Fallback to body
        if soup.body:
            return soup.body
        return soup

    # --- Rate Limiting ---

    def _wait_for_rate_limit(self, domain: str):
        """Wait if we've made a recent request to this domain."""
        if not self._rate_limit:
            return

        last = self._last_request.get(domain, 0)
        elapsed = time.time() - last
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)

        self._last_request[domain] = time.time()


# --- REST API Client ---


class APIClient:
    """Simple REST API client for structured data."""

    def __init__(self, cache: Any = None):
        self._cache = cache
        self._session = requests.Session() if requests else None
        if self._session:
            self._session.headers.update({"Accept": "application/json"})

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Make a GET request."""
        if not self._session:
            return None

        cache_key = f"api:get:{url}:{json.dumps(params or {})}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                return cached

        try:
            resp = self._session.get(
                url, params=params, headers=headers, timeout=timeout
            )
            resp.raise_for_status()
            data = resp.json()

            if self._cache:
                self._cache.set(cache_key, data, ttl=300)

            return data
        except Exception:
            return None

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Make a POST request."""
        if not self._session:
            return None

        try:
            resp = self._session.post(url, json=data, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None


# --- Wayback Machine Access ---


class WebArchive:
    """Access the Wayback Machine for historical web pages."""

    def __init__(self, cache: Any = None):
        self._cache = cache
        self._session = requests.Session() if requests else None
        if self._session:
            self._session.headers.update(
                {"User-Agent": ("Mozilla/5.0 (compatible; VeniAI/1.0)")}
            )

    def get_snapshot(self, url: str, timestamp: str = "") -> Optional[str]:
        """Get a Wayback Machine snapshot URL."""
        if not self._session:
            return None

        cache_key = f"wayback:{url}:{timestamp}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                return cached

        base = "https://archive.org/wayback/available"
        params = {"url": url}
        if timestamp:
            params["timestamp"] = timestamp

        try:
            resp = self._session.get(base, params=params, timeout=10)
            data = resp.json()
            snapshot = data.get("archived_snapshots", {}).get("closest", {})
            snapshot_url = snapshot.get("url", "")

            if self._cache and snapshot_url:
                self._cache.set(cache_key, snapshot_url, ttl=3600)

            return snapshot_url
        except Exception:
            return None

    def search(self, url: str, limit: int = 5) -> List[Dict[str, str]]:
        """Search for archived versions of a URL."""
        if not self._session:
            return []

        cdx_url = "https://web.archive.org/cdx/search/cdx"
        params = {
            "url": url,
            "output": "json",
            "fl": "timestamp,original,statuscode,mimetype",
            "collapse": "timestamp:4",
            "limit": limit,
        }

        try:
            resp = self._session.get(cdx_url, params=params, timeout=10)
            data = resp.json()

            # First row is headers
            if len(data) < 2:
                return []

            headers = data[0]
            results = []
            for row in data[1:]:
                entry = dict(zip(headers, row))
                entry["wayback_url"] = (
                    f"https://web.archive.org/web/{entry['timestamp']}/{url}"
                )
                results.append(entry)

            return results
        except Exception:
            return []


# --- URL Detection ---


def detect_urls(text: str) -> List[str]:
    """Detect URLs in text."""
    url_pattern = r'https?://[^\s<>"\')\]]+'
    return re.findall(url_pattern, text)


def is_valid_url(text: str) -> bool:
    """Check if text is a valid URL."""
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except Exception:
        return False
