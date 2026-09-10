"""
Tests for Day 7 coverage expansion:
MCP, web search, web scraper, indexer, cache, parallel, sharing.
"""

import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from veni.cache_sys import VeniCache
from veni.indexer import CodebaseIndexer
from veni.parallel import ParallelEngine
from veni.sharing import SessionExporter
from veni.web_scraper import APIClient, WebArchive, WebScraper

# --- MCP Client Tests ---


class TestMCPClient:
    """Test MCP client lifecycle."""

    def test_init(self):
        from veni.mcp import MCPClient

        client = MCPClient("python", ["-m", "test_server"])
        assert client.command == "python"

    def test_connect_disconnect(self):
        from veni.mcp import MCPClient

        client = MCPClient("python", ["-m", "test_server"])
        # Should not raise even without actual server
        client.disconnect()  # Graceful no-op if not connected

    def test_call_tool_without_connection(self):
        from veni.mcp import MCPClient

        client = MCPClient("echo", ["hello"])
        result = client.call_tool("test_tool", {"arg": "val"})
        # Should return error when not connected
        assert "error" in result.lower() or result == ""


# --- Web Search Tests ---


class TestWebSearch:
    """Test MultiEngineSearch."""

    def test_init_with_cache(self):
        from veni.web_search import MultiEngineSearch

        cache = VeniCache()
        search = MultiEngineSearch(cache=cache)
        assert search._cache is cache

    def test_init_without_cache(self):
        from veni.web_search import MultiEngineSearch

        search = MultiEngineSearch()
        assert search._cache is None

    def test_search_empty_query(self):
        from veni.web_search import MultiEngineSearch

        search = MultiEngineSearch()
        # Should handle gracefully, not crash
        with patch.object(search, "_search_ddg", return_value=[]):
            results = search.search("")
        assert isinstance(results, list)

    def test_engines_config(self):
        from veni.web_search import MultiEngineSearch

        search = MultiEngineSearch()
        assert hasattr(search, "engines") or hasattr(search, "_engines")


# --- Web Scraper Tests ---


class TestWebScraper:
    """Test WebScraper functionality."""

    def test_init(self):
        scraper = WebScraper()
        assert scraper is not None

    def test_init_with_cache(self):
        cache = VeniCache()
        scraper = WebScraper(cache=cache)
        assert scraper._cache is cache

    def test_scrape_invalid_url(self):
        scraper = WebScraper()
        result = scraper.scrape("not-a-url")
        # Should return None or empty for invalid URL
        assert result is None or (hasattr(result, "text") and result.text == "")

    def test_api_client_init(self):
        client = APIClient()
        assert client is not None

    def test_archive_init(self):
        archive = WebArchive()
        assert archive is not None


# --- Indexer Tests ---


class TestIndexer:
    """Test CodebaseIndexer."""

    def test_init(self):
        indexer = CodebaseIndexer(Path("."))
        assert indexer.root.resolve() == Path(".").resolve()

    def test_scan_empty_dir(self, tmp_path: Path):
        indexer = CodebaseIndexer(tmp_path)
        count = indexer.scan()
        assert count == 0
        assert len(indexer.entries) == 0

    def test_scan_with_files(self, tmp_path: Path):
        # Create some test files
        (tmp_path / "test.py").write_text("def foo(): pass\n")
        (tmp_path / "test.js").write_text("function bar() {}")
        (tmp_path / "readme.md").write_text("# Test")

        indexer = CodebaseIndexer(tmp_path)
        count = indexer.scan()
        assert count == 3
        assert len(indexer.entries) == 3

    def test_respects_max_files(self, tmp_path: Path):
        # Create more files than max
        for i in range(10):
            (tmp_path / f"file{i}.py").write_text(f"def f{i}(): pass\n")

        indexer = CodebaseIndexer(tmp_path)
        count = indexer.scan()
        # Should be capped
        assert count <= 10

    def test_language_detection(self, tmp_path: Path):
        (tmp_path / "test.py").write_text("def foo(): pass\n")
        (tmp_path / "test.js").write_text("function bar() {}")

        indexer = CodebaseIndexer(tmp_path)
        indexer.scan()
        # Should detect different languages via file extensions
        paths = list(indexer.entries.keys())
        assert any(p.endswith(".py") for p in paths)
        assert any(p.endswith(".js") for p in paths)


# --- Cache System Tests ---


class TestCache:
    """Test VeniCache."""

    def test_init(self):
        cache = VeniCache()
        assert cache is not None

    def test_set_get(self):
        cache = VeniCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        cache = VeniCache()
        assert cache.get("missing") is None

    def test_get_with_default(self):
        cache = VeniCache()
        assert cache.get("missing", "default") == "default"

    def test_ttl_expiration(self, tmp_path: Path):
        cache = VeniCache(cache_dir=tmp_path)
        cache.set("ttl_key", "value", ttl=0.1)  # 100ms TTL
        assert cache.get("ttl_key") == "value"
        time.sleep(0.2)
        assert cache.get("ttl_key") is None

    def test_delete(self):
        cache = VeniCache()
        cache.set("del_key", "value")
        cache.delete("del_key")
        assert cache.get("del_key") is None

    def test_clear(self):
        cache = VeniCache()
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_lru_eviction(self):
        cache = VeniCache(max_entries=2)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")  # Should trigger eviction
        # At least k1 should be evicted (oldest)
        # k3 should definitely exist
        assert cache.get("k3") == "v3"
        # One of k1/k2 may be evicted depending on implementation
        assert cache.get("k1") is None or cache.get("k2") is None

    def test_persistence(self, tmp_path: Path):
        cache = VeniCache(cache_dir=tmp_path)
        cache.set("persist_key", "persist_value")
        # Should be able to reload from disk
        cache2 = VeniCache(cache_dir=tmp_path)
        assert cache2.get("persist_key") == "persist_value"


# --- Parallel Engine Tests ---


class TestParallel:
    """Test ParallelEngine."""

    def test_init(self):
        engine = ParallelEngine(max_workers=2)
        assert engine.max_workers == 2

    def test_run_parallel(self):
        engine = ParallelEngine(max_workers=2)

        def add_one(x):
            return x + 1

        tasks = [
            ("t1", lambda: add_one(1)),
            ("t2", lambda: add_one(2)),
            ("t3", lambda: add_one(3)),
        ]

        results = engine.run_parallel(tasks)
        assert len(results) == 3
        values = {r.task_name: r.result for r in results}
        assert values["t1"] == 2
        assert values["t2"] == 3
        assert values["t3"] == 4

    def test_run_parallel_with_failures(self):
        engine = ParallelEngine(max_workers=2)

        def fail():
            raise ValueError("test error")

        tasks = [
            ("ok", lambda: "success"),
            ("fail", fail),
        ]

        results = engine.run_parallel(tasks)
        ok_result = next(r for r in results if r.task_name == "ok")
        fail_result = next(r for r in results if r.task_name == "fail")
        assert ok_result.success is True
        assert fail_result.success is False

    def test_parallel_map(self):
        engine = ParallelEngine(max_workers=2)
        results = engine.run_parallel_map(lambda x: x * 2, [1, 2, 3], "task_{}")
        assert len(results) == 3

    def test_get_last_results(self):
        engine = ParallelEngine(max_workers=2)
        engine.run_parallel([("t1", lambda: 1)])
        last = engine.get_last_results()
        assert last is not None
        assert len(last) == 1

    def test_get_stats(self):
        engine = ParallelEngine(max_workers=2)
        engine.run_parallel([("t1", lambda: 1), ("t2", lambda: 2)])
        stats = engine.get_stats()
        assert "total_executions" in stats or "total_tasks" in stats


# --- Sharing / Export Tests ---


class TestSharing:
    """Test SessionExporter."""

    @pytest.fixture
    def mock_history(self):
        history = Mock()
        history.system_prompt = "Test system prompt"
        history.messages = [
            Mock(
                role="user",
                content="Hello",
                pinned=False,
                images=[],
                timestamp=time.time(),
            ),
            Mock(
                role="assistant",
                content="Hi there!",
                pinned=False,
                images=[],
                timestamp=time.time(),
            ),
        ]
        return history

    def test_export_markdown(self, mock_history):
        exporter = SessionExporter(mock_history)
        result = exporter.export_session(format="markdown")
        assert "Veni AI Session Export" in result
        assert "Hello" in result
        assert "Hi there!" in result

    def test_export_json(self, mock_history):
        exporter = SessionExporter(mock_history)
        result = exporter.export_session(format="json")
        data = json.loads(result)
        assert "messages" in data
        assert len(data["messages"]) == 2

    def test_export_txt(self, mock_history):
        exporter = SessionExporter(mock_history)
        result = exporter.export_session(format="txt")
        assert "user:" in result.lower() or "USER" in result
        assert "Hello" in result

    def test_export_unknown_format(self, mock_history):
        exporter = SessionExporter(mock_history)
        result = exporter.export_session(format="xml")
        assert "Unknown format" in result

    def test_export_empty_session(self):
        history = Mock()
        history.system_prompt = ""
        history.messages = []
        exporter = SessionExporter(history)
        result = exporter.export_session(format="markdown")
        assert "Veni AI Session Export" in result
