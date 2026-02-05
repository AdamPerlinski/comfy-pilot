"""Agent registry for managing available backends."""

from typing import Dict, Type, Optional, List
import asyncio

from .base import AgentBackend


class AgentRegistry:
    """Central registry for all available agent backends.

    Usage:
        # Register a backend
        AgentRegistry.register(OllamaBackend)

        # Get available agents
        available = await AgentRegistry.get_available_agents()

        # Get a specific backend
        ollama = AgentRegistry.get("ollama")
    """

    _backends: Dict[str, Type[AgentBackend]] = {}
    _instances: Dict[str, AgentBackend] = {}

    @classmethod
    def register(cls, backend_class: Type[AgentBackend]) -> None:
        """Register a new agent backend."""
        instance = backend_class()
        cls._backends[instance.name] = backend_class
        cls._instances[instance.name] = instance

    @classmethod
    def get(cls, name: str) -> Optional[AgentBackend]:
        """Get an agent backend instance by name."""
        return cls._instances.get(name)

    @classmethod
    def list_all(cls) -> List[str]:
        """List all registered backend names."""
        return list(cls._backends.keys())

    @classmethod
    def get_all(cls) -> Dict[str, AgentBackend]:
        """Get all registered backend instances."""
        return cls._instances.copy()

    @classmethod
    async def get_available_agents(cls) -> Dict[str, Dict]:
        """Check which agents are currently available.

        Returns:
            Dict mapping agent name to availability info:
            {
                "ollama": {"available": True, "display_name": "Ollama", "models": [...]},
                "claude": {"available": False, "display_name": "Claude Code", "models": []}
            }
        """
        results = {}

        async def check_agent(name: str, instance: AgentBackend):
            try:
                available = await instance.is_available()
                models = instance.supported_models if available else []
                return name, {
                    "available": available,
                    "display_name": instance.display_name,
                    "models": models
                }
            except Exception as e:
                return name, {
                    "available": False,
                    "display_name": instance.display_name,
                    "models": [],
                    "error": str(e)
                }

        tasks = [
            check_agent(name, instance)
            for name, instance in cls._instances.items()
        ]

        for coro in asyncio.as_completed(tasks):
            name, info = await coro
            results[name] = info

        return results

    @classmethod
    def clear(cls) -> None:
        """Clear all registered backends (useful for testing)."""
        cls._backends.clear()
        cls._instances.clear()
