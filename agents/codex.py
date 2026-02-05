"""OpenAI Codex CLI agent backend.

Uses OpenAI's Codex CLI for agentic interactions.
"""

import asyncio
import json
import os
import shutil
from typing import AsyncIterator, List, Optional

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class CodexCLIBackend(AgentBackend):
    """OpenAI Codex CLI backend.

    Requires:
        - Codex CLI installed (`codex` command available)
        - Valid OpenAI API key configured

    Install: https://github.com/openai/codex
    """

    def __init__(self):
        self._cli_path: Optional[str] = None

    @property
    def name(self) -> str:
        return "codex"

    @property
    def display_name(self) -> str:
        return "OpenAI Codex"

    @property
    def supported_models(self) -> List[str]:
        return [
            "o3",
            "o4-mini",
            "gpt-4.1",
            "gpt-4.1-mini",
        ]

    async def is_available(self) -> bool:
        """Check if Codex CLI is installed and accessible."""
        try:
            self._cli_path = shutil.which("codex")
            if not self._cli_path:
                return False

            process = await asyncio.create_subprocess_exec(
                "codex", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10
            )

            return process.returncode == 0

        except (FileNotFoundError, asyncio.TimeoutError):
            return False
        except Exception:
            return False

    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        """Send messages to Codex CLI and stream responses."""
        config = config or AgentConfig()

        # Build prompt
        prompt_parts = []

        system_prompt = config.system_prompt or self.get_default_system_prompt()
        prompt_parts.append(system_prompt)

        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        full_prompt = "\n\n".join(prompt_parts)

        # Build command - codex uses -q for quiet/non-interactive mode
        cmd = [
            "codex",
            "-q", full_prompt,
            "--approval-mode", "full-auto",  # Non-interactive
        ]

        # Add model if specified
        if config.model:
            cmd.extend(["--model", config.model])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            buffer = ""
            while True:
                chunk = await process.stdout.read(100)
                if not chunk:
                    break

                text = chunk.decode("utf-8", errors="replace")
                buffer += text

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    yield line + "\n"

                if len(buffer) > 50:
                    yield buffer
                    buffer = ""

            if buffer:
                yield buffer

            await process.wait()
            if process.returncode != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode("utf-8", errors="replace")
                if error_msg:
                    yield f"\n\nError: {error_msg}"

        except asyncio.TimeoutError:
            yield "\n\nError: Request timed out"
        except Exception as e:
            yield f"\n\nError: {str(e)}"


class OpenAIAPIBackend(AgentBackend):
    """OpenAI API backend using HTTP requests.

    Direct API access without CLI. Requires OPENAI_API_KEY env var.
    """

    def __init__(self):
        self._api_key: Optional[str] = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI API"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1",
            "o1-mini",
        ]

    async def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        self._api_key = os.environ.get("OPENAI_API_KEY")
        return self._api_key is not None

    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        """Send messages to OpenAI API and stream responses."""
        import aiohttp

        config = config or AgentConfig()
        model = config.model or "gpt-4o"

        # Build messages for OpenAI API
        api_messages = []

        system_prompt = config.system_prompt or self.get_default_system_prompt()
        api_messages.append({
            "role": "system",
            "content": system_prompt
        })

        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": model,
            "messages": api_messages,
            "stream": True,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        yield f"Error: {response.status} - {error}"
                        return

                    # Stream SSE response
                    async for line in response.content:
                        if not line:
                            continue

                        line_str = line.decode("utf-8").strip()

                        if not line_str.startswith("data: "):
                            continue

                        data_str = line_str[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except aiohttp.ClientError as e:
            yield f"\n\nConnection error: {str(e)}"
        except asyncio.TimeoutError:
            yield "\n\nError: Request timed out"
        except Exception as e:
            yield f"\n\nError: {str(e)}"


# Auto-register backends
AgentRegistry.register(CodexCLIBackend)
AgentRegistry.register(OpenAIAPIBackend)
