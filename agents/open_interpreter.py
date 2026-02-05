"""Open Interpreter agent backend.

Open Interpreter is an open-source code interpreter that runs locally.
"""

import asyncio
import shutil
from typing import AsyncIterator, List, Optional

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class OpenInterpreterBackend(AgentBackend):
    """Open Interpreter CLI backend.

    Open Interpreter lets LLMs run code locally. It's open-source
    and supports multiple providers including local models.

    Requires:
        - Open Interpreter installed (`interpreter` command)
        - API key or local model configured

    Install: pip install open-interpreter
    """

    def __init__(self):
        self._cli_path: Optional[str] = None

    @property
    def name(self) -> str:
        return "interpreter"

    @property
    def display_name(self) -> str:
        return "Open Interpreter"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4-turbo",
            "claude-3-5-sonnet",
            "claude-sonnet-4",
            "ollama/llama3.2",
            "ollama/codellama",
            "local",  # Local model
        ]

    async def is_available(self) -> bool:
        """Check if Open Interpreter is installed."""
        try:
            self._cli_path = shutil.which("interpreter")
            if not self._cli_path:
                return False

            process = await asyncio.create_subprocess_exec(
                "interpreter", "--version",
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
        """Send messages to Open Interpreter and stream responses."""
        config = config or AgentConfig()

        # Build prompt
        prompt_parts = []

        system_prompt = config.system_prompt or self.get_default_system_prompt()
        prompt_parts.append(system_prompt)

        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(msg.content)

        full_prompt = "\n\n".join(prompt_parts)

        # Open Interpreter command
        cmd = [
            "interpreter",
            "--fast",  # Fast mode, less verbose
            "-y",  # Auto-confirm code execution
        ]

        if config.model:
            if config.model.startswith("ollama/"):
                cmd.extend(["--local", "--model", config.model.replace("ollama/", "")])
            elif config.model == "local":
                cmd.append("--local")
            else:
                cmd.extend(["--model", config.model])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send prompt to stdin
            process.stdin.write(full_prompt.encode("utf-8"))
            process.stdin.write(b"\n")
            await process.stdin.drain()
            process.stdin.close()

            buffer = ""
            while True:
                chunk = await process.stdout.read(100)
                if not chunk:
                    break

                text = chunk.decode("utf-8", errors="replace")
                buffer += text

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    # Filter interpreter UI elements
                    if not line.startswith(("▌", "●", "Open Interpreter")):
                        yield line + "\n"

                if len(buffer) > 50:
                    yield buffer
                    buffer = ""

            if buffer:
                yield buffer

            await process.wait()

        except asyncio.TimeoutError:
            yield "\n\nError: Request timed out"
        except Exception as e:
            yield f"\n\nError: {str(e)}"


# Auto-register
AgentRegistry.register(OpenInterpreterBackend)
