"""Tool/function calling infrastructure for comfy-pilot.

Defines a backend-agnostic tool system. Tools are registered once and
each agent backend translates them into its native format (Gemini
functionDeclarations, Ollama tools, etc.).
"""

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional


@dataclass
class ToolParameter:
    """A single parameter for a tool."""
    name: str
    type: str  # "string", "integer", "number", "boolean", "array"
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Any = None


@dataclass
class ToolDefinition:
    """A tool that can be called by an LLM."""
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable[..., Awaitable[str]]


@dataclass
class ToolCall:
    """A tool call request from the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Result of executing a tool."""
    call_id: str
    name: str
    content: str
    is_error: bool = False


class ToolRegistry:
    """Registry of available tools."""
    _tools: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool: ToolDefinition) -> None:
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> Optional[ToolDefinition]:
        return cls._tools.get(name)

    @classmethod
    def get_all(cls) -> List[ToolDefinition]:
        return list(cls._tools.values())

    @classmethod
    def clear(cls) -> None:
        cls._tools.clear()

    @classmethod
    async def execute(cls, call: ToolCall) -> ToolResult:
        """Execute a tool call and return the result."""
        tool = cls._tools.get(call.name)
        if not tool:
            return ToolResult(call.id, call.name, f"Unknown tool: {call.name}", is_error=True)
        try:
            result = await tool.handler(**call.arguments)
            return ToolResult(call.id, call.name, result)
        except Exception as e:
            return ToolResult(call.id, call.name, f"Error: {e}", is_error=True)
