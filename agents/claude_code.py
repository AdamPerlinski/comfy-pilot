"""Claude Code agent backend.

Uses the Claude Code CLI (claude) for agentic interactions.
Claude Code can execute code, read files, and perform complex tasks.
"""

import asyncio
import json
import shutil
from typing import AsyncIterator, List, Optional

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class ClaudeCodeBackend(AgentBackend):
    """Claude Code CLI backend.

    Requires:
        - Claude Code CLI installed (`claude` command available)
        - Valid Anthropic API key configured

    Claude Code is particularly powerful because it can:
        - Execute code and shell commands
        - Read and analyze files
        - Perform multi-step reasoning
    """

    def __init__(self):
        self._cli_path: Optional[str] = None

    @property
    def name(self) -> str:
        return "claude_code"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    @property
    def supported_models(self) -> List[str]:
        return [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-sonnet-20241022",
        ]

    async def is_available(self) -> bool:
        """Check if Claude Code CLI is installed and accessible."""
        try:
            # Check if claude CLI exists
            self._cli_path = shutil.which("claude")
            if not self._cli_path:
                return False

            # Try to run a simple command to verify it works
            process = await asyncio.create_subprocess_exec(
                "claude", "--version",
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
        """Send messages to Claude Code CLI and stream responses.

        Uses claude CLI in print mode (-p) for non-interactive use.
        """
        config = config or AgentConfig()

        # Build the prompt from messages
        prompt_parts = []

        # Add system prompt context
        system_prompt = config.system_prompt or self.get_default_system_prompt()
        prompt_parts.append(f"Context:\n{system_prompt}\n")

        # Add conversation history
        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        full_prompt = "\n\n".join(prompt_parts)

        # Build command
        cmd = [
            "claude",
            "-p", full_prompt,  # Print mode (non-interactive)
            "--output-format", "text",  # Plain text output
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

            # Stream stdout
            buffer = ""
            while True:
                chunk = await process.stdout.read(100)
                if not chunk:
                    break

                text = chunk.decode("utf-8", errors="replace")
                buffer += text

                # Yield complete lines or chunks
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    yield line + "\n"

                # Also yield partial content for responsiveness
                if len(buffer) > 50:
                    yield buffer
                    buffer = ""

            # Yield remaining buffer
            if buffer:
                yield buffer

            # Check for errors
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

    def get_default_system_prompt(self) -> str:
        """Extended system prompt leveraging Claude Code's capabilities."""
        base = super().get_default_system_prompt()
        return base + """

Additional capabilities as Claude Code:
- You can analyze complex requirements and break them down
- You understand ComfyUI's node system deeply
- When creating workflows, ensure all connections are valid
- Consider the user's hardware limitations (VRAM, GPU)
- Suggest optimizations for better performance

When outputting workflows:
1. Always use valid JSON in ComfyUI API format
2. Wrap JSON in ```json code blocks
3. Explain the workflow structure briefly
4. Mention any models or custom nodes required"""


# Auto-register this backend
AgentRegistry.register(ClaudeCodeBackend)
