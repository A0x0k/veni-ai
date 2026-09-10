"""
Repo map tool for Veni AI.

Allows the AI to get an overview of the codebase structure,
search for symbols, and find relevant files.
"""

from typing import Any, Dict

from veni.tools.base import AITool


class RepoMapTool(AITool):
    """Tool for getting an overview of the codebase."""

    def __init__(self, bot: Any):
        self.bot = bot

    @property
    def name(self) -> str:
        return "repo_map"

    @property
    def description(self) -> str:
        return (
            "Get a map of the repository structure including files, "
            "classes, functions, and their locations. "
            "Use this before editing to understand the codebase layout. "
            "Call with no arguments for the full map, or with 'search' "
            "to find specific symbols."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["map", "search"],
                    "description": (
                        "'map' for full repo map, 'search' to find symbols"
                    ),
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Symbol or filename to search for "
                        "(only used with action='search')"
                    ),
                },
            },
            "required": ["action"],
        }

    def execute(self, **kwargs: Any) -> str:
        """Get repo map or search for symbols."""
        action_raw = kwargs.get("action", "map")
        query_raw = kwargs.get("query", "")
        action = action_raw if isinstance(action_raw, str) else "map"
        query = query_raw if isinstance(query_raw, str) else ""
        indexer = self.bot.codebase_indexer
        if indexer is None:
            return "Error: Codebase indexer not initialized."

        if action == "search" and query:
            # Search for symbols
            entries = indexer.search_symbol(query)
            if not entries:
                # Fall back to file search
                files = indexer.search_files(query)
                if files:
                    return f"Files matching '{query}':\n" + "\n".join(
                        f"  - {f}" for f in files
                    )
                return f"No files or symbols matching '{query}'."

            result = []
            for entry in entries:
                result.append(f"## {entry.path} ({entry.line_count} lines)")
                for sym in entry.symbols:
                    if query.lower() in sym.name.lower():
                        result.append(f"  - {sym.kind}: {sym.name} (line {sym.line})")
            return "\n".join(result) if result else "No matches found."

        # Default: full repo map
        return indexer.get_repo_map()
