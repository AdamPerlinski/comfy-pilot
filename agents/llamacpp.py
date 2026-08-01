"""llama.cpp (llama-server) agent backend."""

import asyncio
import json
import os
from typing import AsyncIterator, List, Optional

import aiohttp

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class LlamaCppBackend(AgentBackend):
    """llama.cpp backend using llama-server's OpenAI-compatible HTTP API.

    llama-server must be running (default: http://localhost:11434).
    Override with the LLAMACPP_BASE_URL environment variable.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.environ.get(
            "LLAMACPP_BASE_URL", "http://localhost:11434"
        )).rstrip("/")
        self._cached_models: Optional[List[str]] = None

    @property
    def name(self) -> str:
        return "llamacpp"

    @property
    def display_name(self) -> str:
        return "llama.cpp (Local)"

    @property
    def supported_models(self) -> List[str]:
        if self._cached_models:
            return self._cached_models
        return ["default"]

    async def is_available(self) -> bool:
        """Check if llama-server is running and accessible.

        Uses /v1/models, which both identifies the server and yields the
        model list. Ollama also serves /v1/models, so verify it is really
        llama-server via the /props endpoint (llama.cpp-specific).
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/props",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status != 200:
                        return False
                async with session.get(
                    f"{self.base_url}/v1/models",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._cached_models = [
                            m["id"] for m in data.get("data", [])
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
        """Send messages to llama-server and stream responses."""
        config = config or AgentConfig()

        chat_messages = []
        system_prompt = config.system_prompt or self.get_default_system_prompt()
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            chat_messages.append({"role": msg.role, "content": msg.content})

        model = config.model
        if not model:
            model = self._cached_models[0] if self._cached_models else "default"

        payload = {
            "model": model,
            "messages": chat_messages,
            "stream": True,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        yield f"Error from llama.cpp: {error_text}"
                        return

                    # OpenAI-style SSE: lines of "data: {json}", ending "data: [DONE]"
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if not line.startswith("data: "):
                            continue
                        data_str = line[len("data: "):]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        choices = data.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        # Thinking models stream reasoning_content first;
                        # only surface the final answer content.
                        content = delta.get("content")
                        if content:
                            yield content

        except aiohttp.ClientError as e:
            yield f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            yield "Request timed out"


# Auto-register this backend
AgentRegistry.register(LlamaCppBackend)
