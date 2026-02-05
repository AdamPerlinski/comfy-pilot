"""Agent backends for comfy-pilot.

Each backend implements the AgentBackend interface and auto-registers
with the AgentRegistry on import.
"""

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry

# Import backends to trigger auto-registration
from . import ollama  # noqa: F401
from . import claude_code  # noqa: F401
from . import gemini  # noqa: F401
from . import codex  # noqa: F401
from . import kilo  # noqa: F401
from . import aider  # noqa: F401
from . import open_interpreter  # noqa: F401

__all__ = [
    "AgentBackend",
    "AgentMessage",
    "AgentConfig",
    "AgentRegistry",
]
