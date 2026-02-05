"""
comfy-pilot - AI copilot for ComfyUI

Create and modify ComfyUI workflows through natural language conversation
with Claude, Ollama, Gemini, and other AI agents.

Installation:
    Clone into ComfyUI/custom_nodes/comfy-pilot

Usage:
    1. Start ComfyUI
    2. Click "Pilot" button in the menu bar
    3. Select an agent and start chatting
"""

import logging

# Import nodes
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Web extension directory for frontend JS
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# Version info
__version__ = "0.1.0"
__author__ = "comfy-pilot contributors"

# Register routes with ComfyUI's PromptServer
try:
    from server import PromptServer
    from .controller import controller

    # Get the routes from PromptServer instance
    routes = PromptServer.instance.routes

    # Register our routes
    controller.setup_routes(routes)

    logging.info("[comfy-pilot] Routes registered successfully")
except Exception as e:
    logging.warning(f"[comfy-pilot] Could not register routes: {e}")
