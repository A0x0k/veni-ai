"""
Cross-Reference & Impact Analysis for Veni AI.

Understands code relationships:
- Import/usage tracking
- Dependency graphs
- Impact analysis before changes
- Call graph generation
"""

import ast
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


@dataclass
class SymbolReference:
    """A reference to a symbol in code."""

    symbol: str
    file_path: str
    line_number: int
    context: str  # The line of code
    ref_type: str  # "import", "call", "definition", "attribute"


@dataclass
class ImpactReport:
    """Impact analysis report for a proposed change."""

    target: str
    target_file: str
    direct_dependencies: List[str] = field(default_factory=list)
    indirect_dependencies: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high
    summary: str = ""


class CrossReferenceAnalyzer:
    """
    Analyzes cross-references and dependencies in the codebase.

    Builds a graph of:
    - Which files import which modules
    - Which functions call which functions
    - Which classes are used where
    """

    def __init__(self, indexer: Any):
        self.indexer = indexer
        self._import_graph: Dict[str, Set[str]] = defaultdict(set)
        self._usage_graph: Dict[str, Set[str]] = defaultdict(set)
        self._symbol_locations: Dict[str, List[str]] = defaultdict(list)
        self._analyzed: bool = False

    def analyze(self) -> Dict[str, Any]:
        """Run full cross-reference analysis."""
        if self.indexer is None:
            return {"error": "Indexer not set. Call analyzer.indexer = ... first."}
        if self._analyzed:
            return self._get_summary()

        self._import_graph.clear()
        self._usage_graph.clear()
        self._symbol_locations.clear()

        for entry in self.indexer.entries.values():
            file_path = entry.path
            ext = Path(file_path).suffix.lower()

            if ext == ".py":
                self._analyze_python_file(file_path, entry.symbols)
            elif ext in (".js", ".ts"):
                self._analyze_js_file(file_path, entry.symbols)

        self._analyzed = True
        return self._get_summary()

    def find_references(self, symbol: str) -> List[SymbolReference]:
        """Find all references to a symbol."""
        refs = []

        for entry in self.indexer.entries.values():
            file_path = entry.path
            try:
                full_path = self.indexer.root / file_path
                content = full_path.read_text(encoding="utf-8")
            except Exception as exc:
                logger.debug("Failed to read %s for reference search: %s", full_path, exc)
                continue

            for i, line in enumerate(content.splitlines(), 1):
                if symbol in line and not line.strip().startswith("#"):
                    ref_type = "usage"
                    if line.strip().startswith(("import", "from")):
                        ref_type = "import"
                    elif f"def {symbol}" in line or f"class {symbol}" in line:
                        ref_type = "definition"

                    refs.append(
                        SymbolReference(
                            symbol=symbol,
                            file_path=file_path,
                            line_number=i,
                            context=line.strip(),
                            ref_type=ref_type,
                        )
                    )

        return refs

    def analyze_impact(self, target: str, target_file: str) -> ImpactReport:
        """Analyze the impact of changing a symbol."""
        report = ImpactReport(target=target, target_file=target_file)

        # Find all references
        refs = self.find_references(target)

        for ref in refs:
            if ref.file_path == target_file:
                continue

            report.direct_dependencies.append(f"{ref.file_path}:{ref.line_number}")
            report.affected_files.append(ref.file_path)

            # Check if it's a test file
            if "test" in ref.file_path.lower():
                report.affected_tests.append(ref.file_path)

        report.direct_dependencies = list(set(report.direct_dependencies))
        report.affected_files = list(set(report.affected_files))
        report.affected_tests = list(set(report.affected_tests))

        # Determine risk level
        if len(report.affected_files) == 0:
            report.risk_level = "low"
        elif len(report.affected_files) <= 3:
            report.risk_level = "medium"
        else:
            report.risk_level = "high"

        report.summary = (
            f"Changing '{target}' in {target_file} affects "
            f"{len(report.affected_files)} file(s) "
            f"({len(report.affected_tests)} test file(s)). "
            f"Risk: {report.risk_level}."
        )

        return report

    def get_import_graph(self) -> Dict[str, List[str]]:
        """Get the import graph."""
        return {k: sorted(v) for k, v in self._import_graph.items()}

    def get_usage_graph(self) -> Dict[str, List[str]]:
        """Get the usage graph."""
        return {k: sorted(v) for k, v in self._usage_graph.items()}

    def find_unused_symbols(self) -> List[Dict[str, str]]:
        """Find symbols that are defined but never used."""
        unused = []

        for symbol, locations in self._symbol_locations.items():
            # If symbol is only defined once and never imported/used
            if len(locations) <= 1:
                # Check if it's used anywhere
                refs = self.find_references(symbol)
                non_defs = [r for r in refs if r.ref_type != "definition"]
                if not non_defs:
                    unused.append(
                        {
                            "symbol": symbol,
                            "file": locations[0] if locations else "unknown",
                        }
                    )

        return unused

    def _get_summary(self) -> Dict[str, Any]:
        return {
            "imports": len(self._import_graph),
            "usages": len(self._usage_graph),
            "symbols_tracked": len(self._symbol_locations),
            "analyzed_files": len(self.indexer.entries),
        }

    def _analyze_python_file(self, file_path: str, symbols: list):
        """Analyze imports and definitions in a Python file."""
        full_path = self.indexer.root / file_path
        try:
            tree = ast.parse(
                full_path.read_text(encoding="utf-8"),
                filename=file_path,
            )
        except Exception as exc:
            logger.debug("Failed to parse Python file %s: %s", file_path, exc)
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    self._import_graph[module].add(file_path)
                    self._symbol_locations[module].append(file_path)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    self._import_graph[module].add(file_path)
                    for alias in node.names:
                        self._symbol_locations[alias.name].append(file_path)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._symbol_locations[node.name].append(file_path)

            elif isinstance(node, ast.ClassDef):
                self._symbol_locations[node.name].append(file_path)

            elif isinstance(node, ast.Name):
                self._usage_graph[node.id].add(file_path)
                self._symbol_locations[node.id].append(file_path)

            elif isinstance(node, ast.Attribute):
                # Track method calls
                if isinstance(node.value, ast.Name):
                    key = f"{node.value.id}.{node.attr}"
                    self._usage_graph[key].add(file_path)

    def _analyze_js_file(self, file_path: str, symbols: list):
        """Analyze imports in JavaScript/TypeScript files."""
        full_path = self.indexer.root / file_path
        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed to read JS file %s: %s", file_path, exc)
            return

        # Import patterns
        import_patterns = [
            r"import\s+.*?\s+from\s+['\"](.+?)['\"]",
            r"require\s*\(\s*['\"](.+?)['\"]\s*\)",
            r"import\s+\*\s+as\s+\w+\s+from\s+['\"](.+?)['\"]",
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                module = match.group(1)
                self._import_graph[module].add(file_path)
