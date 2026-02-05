"""ComfyUI nodes for comfy-pilot.

These nodes can be used directly in ComfyUI workflows for
prompt generation, image analysis, and other AI-powered tasks.
"""

from .prompt_generator import AgenticPromptGenerator

NODE_CLASS_MAPPINGS = {
    "AgenticPromptGenerator": AgenticPromptGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AgenticPromptGenerator": "Agentic Prompt Generator",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
