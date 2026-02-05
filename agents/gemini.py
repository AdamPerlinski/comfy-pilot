"""Gemini CLI agent backend.

Uses Google's Gemini CLI for AI interactions.
"""

import asyncio
import json
import shutil
from typing import AsyncIterator, List, Optional

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


class GeminiCLIBackend(AgentBackend):
    """Gemini CLI backend.

    Requires:
        - Gemini CLI installed (`gemini` command available)
        - Valid Google API key configured

    Install: https://github.com/google-gemini/gemini-cli
    """

    def __init__(self):
        self._cli_path: Optional[str] = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Gemini CLI"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]

    async def is_available(self) -> bool:
        """Check if Gemini CLI is installed and accessible."""
        try:
            self._cli_path = shutil.which("gemini")
            if not self._cli_path:
                return False

            process = await asyncio.create_subprocess_exec(
                "gemini", "--version",
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
        """Send messages to Gemini CLI and stream responses."""
        config = config or AgentConfig()

        # Build the prompt
        prompt_parts = []

        system_prompt = config.system_prompt or self.get_default_system_prompt()
        prompt_parts.append(system_prompt)

        # Add conversation
        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        full_prompt = "\n\n".join(prompt_parts)

        # Build command
        cmd = ["gemini"]

        # Add prompt flag (gemini CLI uses -p or --prompt)
        cmd.extend(["-p", full_prompt])

        # Add model if specified
        if config.model:
            cmd.extend(["--model", config.model])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Stream output
            buffer = ""
            while True:
                chunk = await process.stdout.read(100)
                if not chunk:
                    break

                text = chunk.decode("utf-8", errors="replace")
                buffer += text

                # Yield lines
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


class GeminiAPIBackend(AgentBackend):
    """Gemini API backend using HTTP requests.

    Alternative to CLI - uses Google's Generative AI API directly.
    Requires GOOGLE_API_KEY environment variable.
    """

    def __init__(self):
        self._api_key: Optional[str] = None

    @property
    def name(self) -> str:
        return "gemini_api"

    @property
    def display_name(self) -> str:
        return "Gemini API"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-pro-preview-05-06",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]

    async def is_available(self) -> bool:
        """Check if Gemini API is accessible."""
        import os
        self._api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        return self._api_key is not None

    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        """Send messages to Gemini API and stream responses."""
        import aiohttp

        config = config or AgentConfig()
        model = config.model or "gemini-2.0-flash"

        # Build contents for Gemini API
        contents = []

        system_prompt = config.system_prompt or self.get_default_system_prompt()

        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"

        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens,
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
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

                    # Stream response
                    buffer = ""
                    async for chunk in response.content:
                        if not chunk:
                            continue

                        buffer += chunk.decode("utf-8", errors="replace")

                        # Parse JSON chunks
                        while buffer:
                            try:
                                # Try to find complete JSON object
                                if buffer.startswith("["):
                                    buffer = buffer[1:]
                                if buffer.startswith(","):
                                    buffer = buffer[1:]
                                if buffer.startswith("]"):
                                    break

                                # Find end of JSON object
                                depth = 0
                                end_idx = -1
                                for i, c in enumerate(buffer):
                                    if c == "{":
                                        depth += 1
                                    elif c == "}":
                                        depth -= 1
                                        if depth == 0:
                                            end_idx = i + 1
                                            break

                                if end_idx == -1:
                                    break

                                obj_str = buffer[:end_idx]
                                buffer = buffer[end_idx:]

                                obj = json.loads(obj_str)
                                candidates = obj.get("candidates", [])
                                if candidates:
                                    content = candidates[0].get("content", {})
                                    parts = content.get("parts", [])
                                    for part in parts:
                                        text = part.get("text", "")
                                        if text:
                                            yield text

                            except json.JSONDecodeError:
                                break

        except aiohttp.ClientError as e:
            yield f"\n\nConnection error: {str(e)}"
        except asyncio.TimeoutError:
            yield "\n\nError: Request timed out"
        except Exception as e:
            yield f"\n\nError: {str(e)}"


# Auto-register backends
AgentRegistry.register(GeminiCLIBackend)
AgentRegistry.register(GeminiAPIBackend)
