"""
Cross-reference analysis commands for Veni AI.

/xref - Find references to a symbol across the codebase
"""

from typing import List, Optional

from rich.table import Table

from veni.commands.base import BaseCommand, console


class XrefCommand(BaseCommand):
    """Find cross-references to a symbol."""

    @property
    def name(self) -> str:
        return "/xref"

    @property
    def description(self) -> str:
        return "Find where a function, class, or variable is used across the codebase."

    @property
    def usage(self) -> str:
        return "/xref <symbol_name>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /xref <symbol_name>")
            return None

        symbol = " ".join(args)
        analyzer = getattr(self.bot, "crossref_analyzer", None)
        if not analyzer or not analyzer.indexer:
            self.show_warning(
                "Cross-reference analyzer not available. "
                "Indexing may still be in progress."
            )
            return None

        try:
            result = analyzer.analyze()
            if "error" in result:
                self.show_error(result["error"])
                return None

            # Find references to the symbol
            refs = analyzer.find_references(symbol)
            if not refs:
                console.print(f"[dim]No references found for '{symbol}'[/dim]")
                return None

            table = Table(title=f"References to '{symbol}'", box="ROUNDED")
            table.add_column("File", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Details", style="white")

            for ref in refs:
                table.add_row(
                    ref.get("file", "unknown"),
                    ref.get("type", "unknown"),
                    ref.get("details", ""),
                )

            console.print(table)
        except Exception as e:
            self.show_error(f"Cross-reference error: {e}")

        return None
