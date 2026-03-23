"""Ollama agent backend."""

import asyncio
import json
import uuid
from typing import AsyncIterator, List, Optional, Union

import aiohttp

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry
from .tools import ToolCall, ToolDefinition


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

    @property
    def supports_tool_calling(self) -> bool:
        return True

    @staticmethod
    def _tools_to_ollama(tools: List[ToolDefinition]) -> List[dict]:
        """Convert ToolDefinitions to Ollama's tools format."""
        result = []
        for tool in tools:
            properties = {}
            required = []
            for param in tool.parameters:
                prop = {"type": param.type, "description": param.description}
                if param.enum:
                    prop["enum"] = param.enum
                properties[param.name] = prop
                if param.required:
                    required.append(param.name)
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            })
        return result

    def _build_ollama_messages(
        self, messages: List[AgentMessage], system_prompt: str
    ) -> List[dict]:
        """Convert AgentMessages to Ollama message format."""
        ollama_messages = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            if msg.role == "tool":
                ollama_messages.append({
                    "role": "tool",
                    "content": msg.content,
                })
            elif msg.role == "assistant" and msg.tool_calls:
                # Assistant message with tool calls
                tool_calls = []
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    })
                entry = {"role": "assistant", "tool_calls": tool_calls}
                if msg.content:
                    entry["content"] = msg.content
                ollama_messages.append(entry)
            else:
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        return ollama_messages

    async def query_with_tools(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> AsyncIterator[Union[str, ToolCall]]:
        """Query Ollama with native tool/function calling support."""
        if not tools:
            async for chunk in self.query(messages, config):
                yield chunk
            return

        config = config or AgentConfig()
        model = config.model or (self._cached_models[0] if self._cached_models else "llama3.2")
        system_prompt = config.system_prompt or self.get_default_system_prompt()

        ollama_messages = self._build_ollama_messages(messages, system_prompt)
        ollama_tools = self._tools_to_ollama(tools)

        payload = {
            "model": model,
            "messages": ollama_messages,
            "tools": ollama_tools,
            "stream": False,  # Non-streaming for tool calls
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        yield f"Error from Ollama: {error_text}"
                        return

                    data = await response.json()
                    msg = data.get("message", {})

                    # Yield text content if present
                    content = msg.get("content", "")
                    if content:
                        yield content

                    # Yield tool calls if present
                    for tc in msg.get("tool_calls", []):
                        func = tc.get("function", {})
                        args = func.get("arguments", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                args = {}
                        yield ToolCall(
                            id=str(uuid.uuid4()),
                            name=func.get("name", ""),
                            arguments=args,
                        )

        except aiohttp.ClientError as e:
            yield f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            yield "Request timed out"


# Auto-register this backend
AgentRegistry.register(OllamaBackend)
