"""
Base classes for Veni AI tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AITool(ABC):
    """Abstract base class for all AI-accessible tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does (used by AI)."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema representation of tool parameters."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with provided arguments."""
        pass

    def get_declaration(self) -> Dict[str, Any]:
        """Get the tool declaration for AI models."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Manages available tools for Veni AI."""

    def __init__(self, bot: Any):
        self.bot = bot
        self.tools: Dict[str, AITool] = {}

    def register(self, tool: AITool):
        """Register a new tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[AITool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[AITool]:
        """List all registered tools."""
        return list(self.tools.values())

    def get_declarations(self) -> List[Dict[str, Any]]:
        """Get declarations for all registered tools."""
        return [t.get_declaration() for t in self.tools.values()]
