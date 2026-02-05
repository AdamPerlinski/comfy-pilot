"""Kilo Code agent backend.

Kilo Code is an open-source fork of Claude Code with additional features.
Uses the `kilo` CLI command.
"""

import asyncio
import shutil
from typing import AsyncIterator, List, Optional

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class KiloCodeBackend(AgentBackend):
    """Kilo Code CLI backend.

    Kilo Code is an open-source AI coding assistant, fork of Claude Code.

    Requires:
        - Kilo CLI installed (`kilo` command available)
        - API key configured (supports multiple providers)

    Install: https://github.com/kilocode/kilo
    """

    def __init__(self):
        self._cli_path: Optional[str] = None

    @property
    def name(self) -> str:
        return "kilo"

    @property
    def display_name(self) -> str:
        return "Kilo Code"

    @property
    def supported_models(self) -> List[str]:
        return [
            "claude-sonnet-4",
            "claude-opus-4",
            "gpt-4o",
            "gemini-2.5-pro",
            "deepseek-v3",
            "llama-3.3-70b",
        ]

    async def is_available(self) -> bool:
        """Check if Kilo CLI is installed."""
        try:
            self._cli_path = shutil.which("kilo")
            if not self._cli_path:
                return False

            process = await asyncio.create_subprocess_exec(
                "kilo", "--version",
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
        """Send messages to Kilo CLI and stream responses."""
        config = config or AgentConfig()

        # Build prompt
        prompt_parts = []

        system_prompt = config.system_prompt or self.get_default_system_prompt()
        prompt_parts.append(f"Context:\n{system_prompt}\n")

        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        full_prompt = "\n\n".join(prompt_parts)

        # Kilo CLI command (similar to claude CLI)
        cmd = [
            "kilo",
            "-p", full_prompt,
            "--output-format", "text",
        ]

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


# Auto-register
AgentRegistry.register(KiloCodeBackend)
