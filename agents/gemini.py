"""Gemini agent backends for comfy-pilot.

Uses the official Google Gen AI SDK (google-genai) — the unified,
actively maintained library for Gemini Developer API and Vertex AI.

Install: pip install google-genai
Docs:    https://googleapis.github.io/python-genai/
"""

import asyncio
import os
import shutil
from typing import AsyncIterator, List, Optional

from .base import AgentBackend, AgentMessage, AgentConfig
from .registry import AgentRegistry


# ---------------------------------------------------------------------------
# Fallback model list used if dynamic fetching fails
# ---------------------------------------------------------------------------
_FALLBACK_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]

# Models that are NOT for text generation — excluded from the chat dropdown
_EXCLUDED_SUFFIXES = (
    "-image", "-image-preview", "-embedding", "-aqa",
    "-live", "-tts", "-vision", "-transcribe",
)
_EXCLUDED_PREFIXES = (
    "imagen-", "veo-", "text-embedding", "embedding-",
    "aqa", "learnlm",
)


def _is_chat_model(model_name: str) -> bool:
    """Return True if this model is suitable for chat/text generation."""
    name = model_name.lower()
    for suffix in _EXCLUDED_SUFFIXES:
        if name.endswith(suffix):
            return False
    for prefix in _EXCLUDED_PREFIXES:
        if name.startswith(prefix):
            return False
    return True


async def _fetch_dynamic_models(api_key: str) -> List[str]:
    """Fetch all generateContent-capable chat models from the Gemini API."""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        chat_models = []
        async for model in await client.aio.models.list():
            name = getattr(model, "name", "") or ""
            short_name = name.replace("models/", "")
            supported_methods = getattr(model, "supported_generation_methods", []) or []
            if "generateContent" not in supported_methods:
                continue
            if _is_chat_model(short_name):
                chat_models.append(short_name)
        if chat_models:
            print(f"[comfy-pilot] Gemini API: {len(chat_models)} chat models available")
            return chat_models
    except Exception as e:
        print(f"[comfy-pilot] Gemini model fetch failed, using fallback list: {e}")
    return _FALLBACK_MODELS


# ---------------------------------------------------------------------------
# Gemini CLI Backend (unchanged — kept for parity)
# ---------------------------------------------------------------------------

class GeminiCLIBackend(AgentBackend):
    """Gemini CLI backend.

    Requires:
        - Gemini CLI installed (``gemini`` command available)
        - Valid Google API key configured

    Install: https://github.com/google-gemini/gemini-cli
    """

    def __init__(self):
        self._cli_path: Optional[str] = None
        self._dynamic_models: Optional[List[str]] = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Gemini CLI"

    @property
    def supported_models(self) -> List[str]:
        return self._dynamic_models or _FALLBACK_MODELS

    async def is_available(self) -> bool:
        """Check if Gemini CLI is installed and accessible."""
        try:
            self._cli_path = shutil.which("gemini")
            if not self._cli_path:
                return False

            process = await asyncio.create_subprocess_exec(
                "gemini", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=10)
            if process.returncode != 0:
                return False

        except (FileNotFoundError, asyncio.TimeoutError):
            return False
        except Exception:
            return False

        # Opportunistically fetch the full model list if an API key is available
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                self._dynamic_models = await _fetch_dynamic_models(api_key)
            except Exception as e:
                print(f"[comfy-pilot] GeminiCLI: model fetch skipped: {e}")

        return True

    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        """Send messages to Gemini CLI and stream responses."""
        config = config or AgentConfig()

        prompt_parts = []
        system_prompt = config.system_prompt or self.get_default_system_prompt()
        prompt_parts.append(system_prompt)

        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        full_prompt = "\n\n".join(prompt_parts)
        cmd = ["gemini", "-p", full_prompt]
        if config.model:
            cmd.extend(["--model", config.model])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
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
                stderr_data = await process.stderr.read()
                error_msg = stderr_data.decode("utf-8", errors="replace")
                if error_msg:
                    yield f"\n\nError: {error_msg}"

        except asyncio.TimeoutError:
            yield "\n\nError: Request timed out"
        except Exception as e:
            yield f"\n\nError: {str(e)}"


# ---------------------------------------------------------------------------
# Gemini API Backend — rewritten with google-genai SDK
# ---------------------------------------------------------------------------

class GeminiAPIBackend(AgentBackend):
    """Gemini API backend using the official google-genai SDK.

    Requires:
        - ``pip install google-genai``
        - GOOGLE_API_KEY or GEMINI_API_KEY environment variable

    Models are fetched dynamically from the API so the dropdown always
    reflects what your key actually has access to.
    """

    def __init__(self):
        self._api_key: Optional[str] = None
        self._dynamic_models: Optional[List[str]] = None  # cached after first fetch

    @property
    def name(self) -> str:
        return "gemini_api"

    @property
    def display_name(self) -> str:
        return "Gemini API"

    @property
    def supported_models(self) -> List[str]:
        """Return cached dynamic models, or fallback list if not yet fetched."""
        if self._dynamic_models:
            return self._dynamic_models
        return _FALLBACK_MODELS

    async def is_available(self) -> bool:
        """Check if the google-genai SDK is installed and API key is set."""
        try:
            from google import genai  # noqa: F401
        except ImportError:
            print("[comfy-pilot] google-genai not installed. Run: pip install google-genai")
            return False

        self._api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            return False

        # Pre-fetch and cache the model list at availability check time
        try:
            self._dynamic_models = await _fetch_dynamic_models(self._api_key)
        except Exception as e:
            print(f"[comfy-pilot] Could not pre-fetch Gemini models: {e}")

        return True

    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from the Gemini API using google-genai SDK."""
        from google import genai
        from google.genai import types

        config = config or AgentConfig()
        model = config.model or "gemini-2.5-flash"
        system_prompt = config.system_prompt or self.get_default_system_prompt()

        # Re-read API key in case env changed since is_available()
        api_key = (
            self._api_key
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )
        if not api_key:
            yield "Error: No GOOGLE_API_KEY or GEMINI_API_KEY found in environment."
            return

        all_messages = list(messages)
        if not all_messages:
            yield "Error: No messages to send."
            return

        # Split into history (all but last) and the current user message
        last_message = all_messages[-1]
        prior_messages = all_messages[:-1]

        # Build conversation history in the format the SDK expects
        history = []
        for msg in prior_messages:
            role = "user" if msg.role == "user" else "model"
            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)],
                )
            )

        try:
            client = genai.Client(api_key=api_key)

            # Create async chat session with history and system prompt
            chat = client.aio.chats.create(
                model=model,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=config.temperature,
                    max_output_tokens=config.max_tokens,
                ),
                history=history,
            )

            # Stream the latest user message
            async for chunk in await chat.send_message_stream(last_message.content):
                text = chunk.text
                if text:
                    yield text

        except Exception as e:
            error_str = str(e)
            if "not found" in error_str.lower() or "404" in error_str:
                yield (
                    f"Error: Model '{model}' not found or not available for your API key.\n"
                    f"Try selecting a different model from the dropdown.\n"
                    f"Details: {error_str}"
                )
            else:
                yield f"Error: {error_str}"


# Auto-register backends
AgentRegistry.register(GeminiCLIBackend)
AgentRegistry.register(GeminiAPIBackend)