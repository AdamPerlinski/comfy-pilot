"""ComfyUI tool definitions for agent function calling.

Provides tools that let LLMs query ComfyUI's node registry, available
models, and current workflow on-demand instead of stuffing everything
into the system prompt.
"""

import json
from typing import List, Optional

from .tools import ToolDefinition, ToolParameter, ToolRegistry

# Keep a module-level reference so tool closures can access it
_node_registry = None
_system_monitor = None


def setup_tools(node_registry, system_monitor=None) -> List[ToolDefinition]:
    """Create and register ComfyUI tools.

    Args:
        node_registry: A NodeRegistry instance (from validation.node_registry)
        system_monitor: Optional SystemMonitor class for model listing

    Returns:
        List of registered ToolDefinition objects.
    """
    global _node_registry, _system_monitor
    _node_registry = node_registry
    _system_monitor = system_monitor

    tools = [
        _make_get_node_types(),
        _make_get_node_info(),
        _make_get_available_models(),
        _make_get_current_workflow(),
    ]

    ToolRegistry.clear()
    for tool in tools:
        ToolRegistry.register(tool)

    return tools


# ---------------------------------------------------------------------------
# Tool: get_node_types
# ---------------------------------------------------------------------------

def _make_get_node_types() -> ToolDefinition:
    async def handler(search: str = "", category: str = "", limit: int = 50) -> str:
        if not _node_registry or not _node_registry.is_loaded:
            await _node_registry.fetch()
        if not _node_registry or not _node_registry.is_loaded:
            return json.dumps({"error": "Node registry not available. Is ComfyUI running?"})

        all_types = _node_registry.get_all_class_types()
        results = []

        for ct in all_types:
            node = _node_registry.get_node(ct)
            if not node:
                continue
            if search and search.lower() not in ct.lower() and search.lower() not in (node.display_name or "").lower():
                continue
            if category and category.lower() not in (node.category or "").lower():
                continue
            results.append({
                "class_type": ct,
                "display_name": node.display_name,
                "category": node.category,
                "outputs": node.output_types,
            })
            if len(results) >= limit:
                break

        return json.dumps({
            "total_available": len(all_types),
            "returned": len(results),
            "nodes": results,
        })

    return ToolDefinition(
        name="get_node_types",
        description="Search or browse installed ComfyUI node types. Use this to find which nodes are available before building a workflow. You can filter by name or category.",
        parameters=[
            ToolParameter(name="search", type="string",
                          description="Search term to filter nodes by class_type or display_name (case-insensitive). Leave empty to browse.",
                          required=False),
            ToolParameter(name="category", type="string",
                          description="Filter by category (e.g. 'sampling', 'loaders', 'conditioning'). Case-insensitive partial match.",
                          required=False),
            ToolParameter(name="limit", type="integer",
                          description="Maximum number of results to return (default 50).",
                          required=False),
        ],
        handler=handler,
    )


# ---------------------------------------------------------------------------
# Tool: get_node_info
# ---------------------------------------------------------------------------

def _make_get_node_info() -> ToolDefinition:
    async def handler(class_type: str) -> str:
        if not _node_registry or not _node_registry.is_loaded:
            await _node_registry.fetch()
        if not _node_registry or not _node_registry.is_loaded:
            return json.dumps({"error": "Node registry not available."})

        node = _node_registry.get_node(class_type)
        if not node:
            suggestions = _node_registry.suggest_similar(class_type)
            return json.dumps({
                "error": f"Node '{class_type}' not found.",
                "suggestions": suggestions,
            })

        required_inputs = {}
        for name, inp in node.inputs_required.items():
            entry = {"type": inp.type, "required": True}
            if inp.default is not None:
                entry["default"] = inp.default
            if inp.min_val is not None:
                entry["min"] = inp.min_val
            if inp.max_val is not None:
                entry["max"] = inp.max_val
            if inp.options:
                entry["options"] = inp.options[:30]  # cap long combo lists
            required_inputs[name] = entry

        optional_inputs = {}
        for name, inp in node.inputs_optional.items():
            entry = {"type": inp.type, "required": False}
            if inp.default is not None:
                entry["default"] = inp.default
            if inp.min_val is not None:
                entry["min"] = inp.min_val
            if inp.max_val is not None:
                entry["max"] = inp.max_val
            if inp.options:
                entry["options"] = inp.options[:30]
            optional_inputs[name] = entry

        return json.dumps({
            "class_type": node.class_type,
            "display_name": node.display_name,
            "category": node.category,
            "description": node.description,
            "inputs_required": required_inputs,
            "inputs_optional": optional_inputs,
            "output_types": node.output_types,
            "output_names": node.output_names,
        })

    return ToolDefinition(
        name="get_node_info",
        description="Get full input/output specification for a specific ComfyUI node type. Use this to check exact parameter names, types, defaults, and valid ranges before creating or modifying a workflow.",
        parameters=[
            ToolParameter(name="class_type", type="string",
                          description="The exact class_type of the node (e.g. 'KSampler', 'CheckpointLoaderSimple').",
                          required=True),
        ],
        handler=handler,
    )


# ---------------------------------------------------------------------------
# Tool: get_available_models
# ---------------------------------------------------------------------------

def _make_get_available_models() -> ToolDefinition:
    async def handler(model_type: str = "checkpoints") -> str:
        if _system_monitor is None:
            return json.dumps({"error": "SystemMonitor not available."})

        try:
            models = await _system_monitor.get_available_models()
        except Exception as e:
            return json.dumps({"error": f"Failed to fetch models: {e}"})

        type_map = {
            "checkpoints": "checkpoints",
            "loras": "loras",
            "vae": "vae",
            "controlnets": "controlnets",
            "upscale_models": "upscale_models",
            "embeddings": "embeddings",
        }
        key = type_map.get(model_type.lower(), model_type.lower())
        found = models.get(key, [])

        return json.dumps({
            "model_type": model_type,
            "count": len(found),
            "models": found,
            "available_types": list(models.keys()),
        })

    return ToolDefinition(
        name="get_available_models",
        description="List models available in the user's ComfyUI installation. Returns checkpoints, LoRAs, VAEs, ControlNets, etc.",
        parameters=[
            ToolParameter(name="model_type", type="string",
                          description="Type of model to list: 'checkpoints', 'loras', 'vae', 'controlnets', 'upscale_models', 'embeddings'.",
                          required=False,
                          enum=["checkpoints", "loras", "vae", "controlnets", "upscale_models", "embeddings"]),
        ],
        handler=handler,
    )


# ---------------------------------------------------------------------------
# Tool: get_current_workflow
# ---------------------------------------------------------------------------

# The current workflow is injected by the controller before each chat turn
_current_workflow = None


def set_current_workflow(workflow: Optional[dict]) -> None:
    """Called by the controller to make the current workflow available to tools."""
    global _current_workflow
    _current_workflow = workflow


def _make_get_current_workflow() -> ToolDefinition:
    async def handler() -> str:
        if not _current_workflow:
            return json.dumps({"error": "No workflow is currently loaded in ComfyUI."})

        nodes = _current_workflow if isinstance(_current_workflow, dict) else {}
        summary = []
        for node_id, node_data in nodes.items():
            ct = node_data.get("class_type", "Unknown")
            title = (node_data.get("_meta") or {}).get("title", ct)
            summary.append({
                "id": node_id,
                "class_type": ct,
                "title": title,
            })

        return json.dumps({
            "node_count": len(nodes),
            "nodes": summary,
            "workflow": _current_workflow,
        })

    return ToolDefinition(
        name="get_current_workflow",
        description="Get the user's current ComfyUI workflow. Returns all nodes with their IDs, types, and full configuration. Use this to understand the existing workflow before suggesting modifications.",
        parameters=[],
        handler=handler,
    )
