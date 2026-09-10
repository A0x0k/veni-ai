"""
Intelligent Caching System for Veni AI.

Caches expensive operations:
- Codebase indexing
- API lookups
- Analysis results
- File contents
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class CacheEntry:
    """A single cache entry."""

    def __init__(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.metadata = metadata or {}

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl

    @property
    def size_estimate(self) -> int:
        return len(str(self.value))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "ttl": self.ttl,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        entry = cls(
            key=data["key"],
            value=data["value"],
            ttl=data.get("ttl", 3600),
            metadata=data.get("metadata"),
        )
        entry.created_at = data.get("created_at", time.time())
        entry.access_count = data.get("access_count", 0)
        return entry


class VeniCache:
    """
    Intelligent caching system with:
    - TTL-based expiration
    - LRU eviction
    - File persistence
    - Size limits
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_size_mb: int = 50,
        max_entries: int = 1000,
    ):
        self.cache_dir = cache_dir or Path.home() / ".veni-chatbot" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries

        self._cache: Dict[str, CacheEntry] = {}
        self._file_cache: Path = self.cache_dir / "cache.json"
        self._load()

    def _load(self):
        """Load cache from disk."""
        if self._file_cache.exists():
            try:
                data = json.loads(self._file_cache.read_text(encoding="utf-8"))
                for entry_data in data.get("entries", []):
                    entry = CacheEntry.from_dict(entry_data)
                    if not entry.is_expired:
                        self._cache[entry.key] = entry
            except Exception:
                self._cache = {}

    def _save(self):
        """Save cache to disk."""
        try:
            data = {
                "entries": [
                    entry.to_dict()
                    for entry in self._cache.values()
                    if not entry.is_expired
                ]
            }
            self._file_cache.write_text(json.dumps(data), encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed to save cache: %s", exc)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a cached value."""
        entry = self._cache.get(key)
        if entry is None or entry.is_expired:
            if entry:
                del self._cache[key]
            return default

        entry.access_count += 1
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Set a cached value."""
        # Evict if needed
        if len(self._cache) >= self.max_entries:
            self._evict()

        entry = CacheEntry(key, value, ttl, metadata)
        self._cache[key] = entry
        self._save()
        # Very short TTLs are useful in tests and for transient provider data.
        # Start the in-memory TTL after persistence so slow disks do not expire
        # the value before the caller can read it once.
        entry.created_at = time.time()

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        if key in self._cache:
            del self._cache[key]
            self._save()
            return True
        return False

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._save()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(e.size_estimate for e in self._cache.values())
        expired = sum(1 for e in self._cache.values() if e.is_expired)
        return {
            "entries": len(self._cache),
            "expired": expired,
            "size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "max_entries": self.max_entries,
        }

    def _evict(self):
        """Evict least recently used entries."""
        # Remove expired first
        expired = [k for k, v in self._cache.items() if v.is_expired]
        for k in expired:
            del self._cache[k]

        # If still full, remove lowest access entries
        if len(self._cache) >= self.max_entries:
            sorted_entries = sorted(
                self._cache.items(), key=lambda x: x[1].access_count
            )
            to_remove = len(self._cache) - self.max_entries + 100
            for key, _ in sorted_entries[:to_remove]:
                del self._cache[key]

    @staticmethod
    def make_key(*args: Any, **kwargs: Any) -> str:
        """Generate a cache key from arguments."""
        key_parts = [str(a) for a in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "|".join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
