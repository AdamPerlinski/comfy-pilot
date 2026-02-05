"""Ollama agent backend."""

import asyncio
import json
from typing import AsyncIterator, List, Optional

import aiohttp

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class OllamaBackend(AgentBackend):
    """Ollama backend using the local HTTP API.

    Ollama must be running locally (default: http://localhost:11434).
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._cached_models: Optional[List[str]] = None

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        return "Ollama (Local)"

    @property
    def supported_models(self) -> List[str]:
        """Return cached models or default list."""
        if self._cached_models:
            return self._cached_models
        return ["llama3.2", "llama3.1", "qwen2.5", "deepseek-r1", "mistral"]

    async def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._cached_models = [
                            m["name"] for m in data.get("models", [])
                        ]
                        return True
                    return False
        except Exception:
            return False

    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        """Send messages to Ollama and stream responses."""
        config = config or AgentConfig()

        # Build message list for Ollama API
        ollama_messages = []

        # Add system prompt if provided
        system_prompt = config.system_prompt or self.get_default_system_prompt()
        if system_prompt:
            ollama_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add conversation messages
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Determine model
        model = config.model
        if not model:
            # Try to use first available model
            if self._cached_models:
                model = self._cached_models[0]
            else:
                model = "llama3.2"

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        yield f"Error from Ollama: {error_text}"
                        return

                    async for line in response.content:
                        if not line:
                            continue
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "message" in data:
                                content = data["message"].get("content", "")
                                if content:
                                    yield content
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except aiohttp.ClientError as e:
            yield f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            yield "Request timed out"


# Auto-register this backend
AgentRegistry.register(OllamaBackend)
