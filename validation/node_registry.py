"""Node registry that fetches and caches ComfyUI's node definitions.

Uses the /object_info endpoint to get all available node types
with their inputs, outputs, and constraints.
"""

import time
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Any, Dict, List, Optional, Tuple

import aiohttp


@dataclass
class InputDefinition:
    """Definition of a node input."""
    name: str
    type: str  # e.g. "MODEL", "CLIP", "INT", "FLOAT", "STRING", "COMBO"
    required: bool = True
    default: Any = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    options: Optional[List[str]] = None  # For COMBO type


@dataclass
class NodeDefinition:
    """Definition of a ComfyUI node type."""
    class_type: str
    category: str = ""
    display_name: str = ""
    description: str = ""
    inputs_required: Dict[str, InputDefinition] = field(default_factory=dict)
    inputs_optional: Dict[str, InputDefinition] = field(default_factory=dict)
    output_types: List[str] = field(default_factory=list)  # e.g. ["MODEL", "CLIP", "VAE"]
    output_names: List[str] = field(default_factory=list)


class NodeRegistry:
    """Registry of available ComfyUI node types.

    Fetches node definitions from the /object_info endpoint and caches them.
    """

    CACHE_TTL = 300  # 5 minutes

    def __init__(self, comfyui_url: str = "http://127.0.0.1:8188"):
        self.comfyui_url = comfyui_url
        self._nodes: Dict[str, NodeDefinition] = {}
        self._last_fetch: float = 0
        self._fetched = False

    async def fetch(self) -> bool:
        """Fetch node definitions from ComfyUI's /object_info endpoint.

        Returns True if successful, False otherwise.
        """
        now = time.time()
        if self._fetched and (now - self._last_fetch) < self.CACHE_TTL:
            return True

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.comfyui_url}/object_info",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        return False
                    data = await response.json()
        except Exception:
            return False

        self._nodes = {}
        for class_type, info in data.items():
            node_def = self._parse_node_info(class_type, info)
            self._nodes[class_type] = node_def

        self._last_fetch = now
        self._fetched = True
        return True

    def _parse_node_info(self, class_type: str, info: Dict[str, Any]) -> NodeDefinition:
        """Parse the /object_info response for a single node type."""
        node = NodeDefinition(
            class_type=class_type,
            category=info.get("category", ""),
            display_name=info.get("display_name", class_type),
            description=info.get("description", ""),
        )

        # Parse output types
        output_types = info.get("output", [])
        if isinstance(output_types, list):
            node.output_types = output_types

        output_names = info.get("output_name", [])
        if isinstance(output_names, list):
            node.output_names = output_names

        # Parse inputs
        input_info = info.get("input", {})

        for section, required in [("required", True), ("optional", False)]:
            section_data = input_info.get(section, {})
            if not isinstance(section_data, dict):
                continue

            for input_name, input_spec in section_data.items():
                input_def = self._parse_input_spec(input_name, input_spec, required)
                if required:
                    node.inputs_required[input_name] = input_def
                else:
                    node.inputs_optional[input_name] = input_def

        return node

    def _parse_input_spec(
        self, name: str, spec: Any, required: bool
    ) -> InputDefinition:
        """Parse a single input specification."""
        input_def = InputDefinition(name=name, type="UNKNOWN", required=required)

        if not isinstance(spec, (list, tuple)) or len(spec) == 0:
            return input_def

        type_info = spec[0]
        constraints = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}

        # Type can be a string like "MODEL", "CLIP", etc.
        # Or a list of strings for COMBO type
        if isinstance(type_info, str):
            input_def.type = type_info
        elif isinstance(type_info, list):
            input_def.type = "COMBO"
            input_def.options = type_info

        # Parse constraints
        if isinstance(constraints, dict):
            input_def.default = constraints.get("default")
            input_def.min_val = constraints.get("min")
            input_def.max_val = constraints.get("max")

        return input_def

    @property
    def is_loaded(self) -> bool:
        return self._fetched and len(self._nodes) > 0

    def node_exists(self, class_type: str) -> bool:
        """Check if a node type exists in the registry."""
        return class_type in self._nodes

    def get_node(self, class_type: str) -> Optional[NodeDefinition]:
        """Get a node definition by class type."""
        return self._nodes.get(class_type)

    def get_output_type(self, class_type: str, slot_index: int) -> Optional[str]:
        """Get the output type at a given slot index for a node type."""
        node = self._nodes.get(class_type)
        if node and 0 <= slot_index < len(node.output_types):
            return node.output_types[slot_index]
        return None

    def get_all_class_types(self) -> List[str]:
        """Get all registered class types (for fuzzy matching)."""
        return list(self._nodes.keys())

    def suggest_similar(self, class_type: str, n: int = 3) -> List[str]:
        """Find similar class type names using fuzzy matching."""
        return get_close_matches(class_type, self._nodes.keys(), n=n, cutoff=0.6)

    def get_input_type(self, class_type: str, input_name: str) -> Optional[Tuple[str, bool]]:
        """Get the expected type for a node input.

        Returns (type_string, is_required) or None if not found.
        """
        node = self._nodes.get(class_type)
        if not node:
            return None

        if input_name in node.inputs_required:
            return (node.inputs_required[input_name].type, True)
        if input_name in node.inputs_optional:
            return (node.inputs_optional[input_name].type, False)
        return None
