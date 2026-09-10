"""
Codebase indexer for Veni AI.

Builds a lightweight index of the workspace:
- File tree respecting .gitignore
- Symbol extraction (imports, classes, functions) for key languages
- Compact repo map for AI context injection
- Persistent cache for instant startup
"""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    FileSystemEventHandler = object
    Observer = None

# Default ignore patterns (mirrors common .gitignore entries)
_DEFAULT_IGNORES = {
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".eggs",
    "*.egg-info",
    "dist",
    "build",
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "*.pyo",
}

# File extensions we can parse for symbols
_CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".rb",
    ".sh",
}

# Max files to index (performance guard)
_MAX_FILES = 2000


@dataclass
class Symbol:
    """A code symbol (function, class, import)."""

    name: str
    kind: str  # "function", "class", "import"
    line: int = 0


@dataclass
class FileEntry:
    """Indexed file with its symbols."""

    path: str
    symbols: List[Symbol] = field(default_factory=list)
    line_count: int = 0
    mtime: float = 0.0


class CodebaseIndexer:
    """Index a workspace directory for code awareness."""

    def __init__(self, root: Path, max_files: int = _MAX_FILES):
        self.root = root.resolve()
        self.max_files = max_files
        self.entries: Dict[str, FileEntry] = {}
        self._ignore_patterns: Set[str] = set(_DEFAULT_IGNORES)
        self.cache_path = self.root / ".veni_cache.json"
        self._load_gitignore()
        self._load_cache()

    def _load_cache(self):
        """Load entries from persistent cache."""
        if not self.cache_path.exists():
            return
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            for rel_str, entry_data in data.items():
                symbols = [Symbol(**s) for s in entry_data.get("symbols", [])]
                self.entries[rel_str] = FileEntry(
                    path=entry_data["path"],
                    symbols=symbols,
                    line_count=entry_data["line_count"],
                    mtime=entry_data.get("mtime", 0.0),
                )
        except Exception:
            pass

    def _save_cache(self):
        """Save current entries to persistent cache."""
        try:
            data = {}
            for rel_str, entry in self.entries.items():
                data[rel_str] = {
                    "path": entry.path,
                    "line_count": entry.line_count,
                    "mtime": entry.mtime,
                    "symbols": [asdict(s) for s in entry.symbols],
                }
            self.cache_path.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass

    def _load_gitignore(self):
        """Load patterns from .gitignore if it exists."""
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            return
        try:
            for line in gitignore.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Strip trailing slash for directory patterns
                pattern = line.rstrip("/")
                # Take the last component for matching
                if "/" in pattern:
                    pattern = pattern.split("/")[-1]
                if pattern:
                    self._ignore_patterns.add(pattern)
        except Exception:
            pass

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be skipped."""
        for part in path.parts:
            for pattern in self._ignore_patterns:
                if _fnmatch(part, pattern):
                    return True
        return False

    def scan(self) -> int:
        """Scan the workspace and build/update the index incrementally."""
        files_to_parse = []
        new_entries = {}
        current_paths = set()
        
        for root, dirs, files in os.walk(self.root):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]

            for fname in files:
                if len(current_paths) >= self.max_files:
                    break

                file_path = root_path / fname
                if self._should_ignore(file_path):
                    continue

                rel = file_path.relative_to(self.root)
                rel_str = str(rel).replace("\\", "/")
                current_paths.add(rel_str)

                mtime = file_path.stat().st_mtime
                
                # If in cache and not modified, reuse it
                if rel_str in self.entries and self.entries[rel_str].mtime == mtime:
                    new_entries[rel_str] = self.entries[rel_str]
                    continue

                # Check extension
                ext = file_path.suffix.lower()
                if ext not in _CODE_EXTENSIONS:
                    new_entries[rel_str] = FileEntry(path=rel_str, line_count=0, mtime=mtime)
                    continue

                files_to_parse.append((file_path, rel_str, mtime))

        # Parallel symbol parsing for new/modified files
        if files_to_parse:
            with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
                results = executor.map(lambda x: self._parse_file(x[0], x[1], x[2]), files_to_parse)
                for entry in results:
                    new_entries[entry.path] = entry

        self.entries = new_entries
        self._save_cache()
        return len(self.entries)

    def _parse_file(self, file_path: Path, rel_str: str, mtime: float = 0.0) -> FileEntry:
        """Extract symbols from a code file."""
        symbols: List[Symbol] = []
        line_count = 0
        ext = file_path.suffix.lower()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    line_count += 1
                    stripped = line.strip()

                    if ext == ".py":
                        self._parse_python(stripped, symbols, line_num)
                    elif ext in (".js", ".ts", ".tsx", ".jsx"):
                        self._parse_javascript(stripped, symbols, line_num)
                    elif ext == ".go":
                        self._parse_go(stripped, symbols, line_num)
                    elif ext in (".c", ".cpp", ".h"):
                        self._parse_c_family(stripped, symbols, line_num)
                    elif ext in (".rb",):
                        self._parse_ruby(stripped, symbols, line_num)
                    elif ext in (".rs",):
                        self._parse_rust(stripped, symbols, line_num)
                    elif ext in (".java",):
                        self._parse_java(stripped, symbols, line_num)
                    elif ext in (".sh",):
                        self._parse_shell(stripped, symbols, line_num)
        except Exception:
            pass

        return FileEntry(path=rel_str, symbols=symbols, line_count=line_count, mtime=mtime)

    # --- Language-specific parsers ---

    @staticmethod
    def _parse_python(line: str, symbols: list, line_num: int):
        if line.startswith(("import ", "from ")):
            name = line.split()[1].split(".")[0]
            symbols.append(Symbol(name=name, kind="import", line=line_num))
        elif line.startswith("def "):
            match = re.match(r"def\s+(\w+)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="function", line=line_num)
                )
        elif line.startswith("class "):
            match = re.match(r"class\s+(\w+)", line)
            if match:
                symbols.append(Symbol(name=match.group(1), kind="class", line=line_num))

    @staticmethod
    def _parse_javascript(line: str, symbols: list, line_num: int):
        if line.startswith(("import ", "export ")):
            name = line.split()[-1].split("/")[0].strip("'\"")
            symbols.append(Symbol(name=name, kind="import", line=line_num))
        elif re.match(r"(export\s+)?(async\s+)?function\s+\w+", line):
            match = re.search(r"function\s+(\w+)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="function", line=line_num)
                )
        elif re.match(r"(export\s+)?class\s+\w+", line):
            match = re.search(r"class\s+(\w+)", line)
            if match:
                symbols.append(Symbol(name=match.group(1), kind="class", line=line_num))

    @staticmethod
    def _parse_go(line: str, symbols: list, line_num: int):
        if line.startswith("import "):
            match = re.search(r'"([^"]+)"', line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="import", line=line_num)
                )
        elif re.match(r"func\s+", line):
            match = re.search(r"func\s+(\w+)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="function", line=line_num)
                )
        elif re.match(r"type\s+\w+\s+struct", line):
            match = re.search(r"type\s+(\w+)", line)
            if match:
                symbols.append(Symbol(name=match.group(1), kind="class", line=line_num))

    @staticmethod
    def _parse_c_family(line: str, symbols: list, line_num: int):
        if line.startswith("#include"):
            match = re.search(r'[<"]([^>"]+)[>"]', line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="import", line=line_num)
                )
        elif re.match(r"(\w+\s+)+\w+\s*\(", line):
            match = re.search(r"\b(\w+)\s*\(", line)
            if match and match.group(1) not in (
                "if",
                "while",
                "for",
                "switch",
                "return",
            ):
                symbols.append(
                    Symbol(name=match.group(1), kind="function", line=line_num)
                )

    @staticmethod
    def _parse_ruby(line: str, symbols: list, line_num: int):
        if line.startswith("def "):
            match = re.match(r"def\s+([\w.?!]+)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="function", line=line_num)
                )
        elif line.startswith("class "):
            match = re.match(r"class\s+(\w+)", line)
            if match:
                symbols.append(Symbol(name=match.group(1), kind="class", line=line_num))

    @staticmethod
    def _parse_rust(line: str, symbols: list, line_num: int):
        if line.startswith("use "):
            match = re.match(r"use\s+([\w:]+)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="import", line=line_num)
                )
        elif re.match(r"(pub\s+)?fn\s+", line):
            match = re.search(r"fn\s+(\w+)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="function", line=line_num)
                )
        elif re.match(r"(pub\s+)?struct\s+", line):
            match = re.search(r"struct\s+(\w+)", line)
            if match:
                symbols.append(Symbol(name=match.group(1), kind="class", line=line_num))

    @staticmethod
    def _parse_java(line: str, symbols: list, line_num: int):
        if line.startswith("import "):
            match = re.match(r"import\s+([\w.]+)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="import", line=line_num)
                )
        elif re.match(r"(public|private|protected)?\s*\w*\s*class\s+", line):
            match = re.search(r"class\s+(\w+)", line)
            if match:
                symbols.append(Symbol(name=match.group(1), kind="class", line=line_num))

    @staticmethod
    def _parse_shell(line: str, symbols: list, line_num: int):
        if re.match(r"\w+\s*\(\)\s*\{", line):
            match = re.match(r"(\w+)\s*\(\)", line)
            if match:
                symbols.append(
                    Symbol(name=match.group(1), kind="function", line=line_num)
                )

    # --- Public API ---

    def get_repo_map(self, max_symbols: int = 100) -> str:
        """Generate a compact repo map for AI context."""
        if not self.entries:
            self.scan()

        lines: List[str] = []
        lines.append(f"# Repository Map: {self.root.name}")
        lines.append(f"# Files indexed: {len(self.entries)}")
        lines.append("")

        # Group by directory
        tree: Dict[str, List[FileEntry]] = {}
        for entry in sorted(self.entries.values(), key=lambda e: e.path):
            parts = entry.path.rsplit("/", 1)
            if len(parts) == 2:
                tree.setdefault(parts[0], []).append(entry)
            else:
                tree.setdefault(".", []).append(entry)

        symbol_count = 0
        for dir_path, entries in sorted(tree.items()):
            lines.append(f"## {dir_path}/")
            for entry in entries:
                if entry.symbols:
                    # Only include files with symbols
                    symbol_lines = [s for s in entry.symbols if s.kind != "import"][
                        :10
                    ]  # Cap per file
                    if symbol_lines:
                        lines.append(f"  - {entry.path}")
                        for sym in symbol_lines:
                            if symbol_count >= max_symbols:
                                break
                            lines.append(f"    - {sym.kind}: {sym.name}")
                            symbol_count += 1
                    else:
                        lines.append(f"  - {entry.path}")
                else:
                    lines.append(f"  - {entry.path}")
            lines.append("")

        if symbol_count >= max_symbols:
            lines.append(f"# ... truncated at {max_symbols} symbols")

        return "\n".join(lines)

    def search_symbol(self, name: str) -> List[FileEntry]:
        """Find files containing a symbol by name."""
        results = []
        for entry in self.entries.values():
            for sym in entry.symbols:
                if name.lower() in sym.name.lower():
                    results.append(entry)
                    break
        return results

    def search_files(self, pattern: str) -> List[str]:
        """Find files matching a glob-like pattern."""
        results = []
        for path in sorted(self.entries.keys()):
            if pattern.lower() in path.lower():
                results.append(path)
        return results

    def index_semantically(self, memory_system):
        """Push indexed symbols and file summaries to semantic memory."""
        if not self.entries:
            self.scan()

        for entry in self.entries.values():
            if not entry.symbols:
                # Basic file entry
                memory_system.remember(
                    category="code_file",
                    content=f"File: {entry.path} ({entry.line_count} lines)",
                    weight=0.5
                )
                continue

            # Index symbols
            for sym in entry.symbols:
                if sym.kind == "import":
                    continue
                content = f"In {entry.path}: {sym.kind} '{sym.name}' on line {sym.line}"
                memory_system.remember(
                    category="code_symbol",
                    content=content,
                    weight=1.0
                )

    def start_watching(self):
        """Start watching for file changes."""
        if Observer is None:
            return None
        
        self.observer = Observer()
        handler = IndexerEventHandler(self)
        self.observer.schedule(handler, str(self.root), recursive=True)
        self.observer.start()
        return self.observer

    def stop_watching(self):
        """Stop watching for file changes."""
        if hasattr(self, "observer") and self.observer:
            self.observer.stop()
            self.observer.join()

class IndexerEventHandler(FileSystemEventHandler):
    """Handles file system events to update the index."""
    def __init__(self, indexer: CodebaseIndexer):
        self.indexer = indexer

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self.indexer._should_ignore(path):
            return
        
        try:
            rel = path.relative_to(self.indexer.root)
            rel_str = str(rel).replace("\\", "/")
            ext = path.suffix.lower()
            if ext in _CODE_EXTENSIONS:
                mtime = path.stat().st_mtime
                entry = self.indexer._parse_file(path, rel_str, mtime)
                self.indexer.entries[rel_str] = entry
        except Exception:
            pass

    def on_created(self, event):
        self.on_modified(event)

    def on_deleted(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        try:
            rel = path.relative_to(self.indexer.root)
            rel_str = str(rel).replace("\\", "/")
            if rel_str in self.indexer.entries:
                del self.indexer.entries[rel_str]
        except Exception:
            pass

def _fnmatch(name: str, pattern: str) -> bool:
    """Simple fnmatch-style matching with * and ? wildcards."""
    if pattern == name:
        return True
    if "*" in pattern:
        regex = "^" + pattern.replace("*", ".*").replace("?", ".") + "$"
        return bool(re.match(regex, name))
    return False
