"""Aider agent backend.

Aider is a popular AI pair programming tool that works in the terminal.
"""

import asyncio
import shutil
from typing import AsyncIterator, List, Optional

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class AiderBackend(AgentBackend):
    """Aider CLI backend.

    Aider is an AI pair programming tool - one of the most popular
    coding assistants with excellent code understanding.

    Requires:
        - Aider installed (`aider` command available)
        - API key for chosen provider (OpenAI, Anthropic, etc.)

    Install: pip install aider-chat
    """

    def __init__(self):
        self._cli_path: Optional[str] = None

    @property
    def name(self) -> str:
        return "aider"

    @property
    def display_name(self) -> str:
        return "Aider"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4o",
            "claude-3-5-sonnet",
            "claude-sonnet-4",
            "deepseek/deepseek-chat",
            "gemini/gemini-2.5-pro",
            "ollama/llama3.2",
        ]

    async def is_available(self) -> bool:
        """Check if Aider is installed."""
        try:
            self._cli_path = shutil.which("aider")
            if not self._cli_path:
                return False

            process = await asyncio.create_subprocess_exec(
                "aider", "--version",
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
        """Send messages to Aider and stream responses.

        Uses aider in message mode (--message) for non-interactive use.
        """
        config = config or AgentConfig()

        # Build the message
        prompt_parts = []

        system_prompt = config.system_prompt or self.get_default_system_prompt()
        prompt_parts.append(system_prompt)

        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        full_prompt = "\n\n".join(prompt_parts)

        # Aider command - use --message for single message mode
        cmd = [
            "aider",
            "--message", full_prompt,
            "--no-git",  # Don't require git repo
            "--no-auto-commits",  # Don't auto-commit
            "--yes",  # Auto-confirm
        ]

        if config.model:
            cmd.extend(["--model", config.model])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/tmp"  # Use temp dir to avoid git issues
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
                    # Filter out aider's UI noise
                    if not line.startswith(("Aider v", "Model:", "Git repo:", "───")):
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
                if error_msg and "error" in error_msg.lower():
                    yield f"\n\nError: {error_msg}"

        except asyncio.TimeoutError:
            yield "\n\nError: Request timed out"
        except Exception as e:
            yield f"\n\nError: {str(e)}"


# Auto-register
AgentRegistry.register(AiderBackend)
