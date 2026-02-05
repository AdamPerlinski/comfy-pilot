"""Workflow manipulation utilities."""

import json
import re
from typing import Dict, Any, List, Optional, Tuple


class WorkflowManipulator:
    """Manipulates ComfyUI workflow JSON.

    Works with the API format workflow JSON (not UI format).
    """

    def __init__(self, workflow: Optional[Dict[str, Any]] = None):
        """Initialize with an optional existing workflow.

        Args:
            workflow: Existing workflow dict, or None for empty workflow
        """
        self.workflow = workflow.copy() if workflow else {}
        self._next_node_id = self._calculate_next_id()

    def _calculate_next_id(self) -> int:
        """Calculate the next available node ID."""
        if not self.workflow:
            return 1
        try:
            return max(int(k) for k in self.workflow.keys()) + 1
        except ValueError:
            return 1

    def add_node(
        self,
        class_type: str,
        inputs: Dict[str, Any],
        title: Optional[str] = None,
    ) -> str:
        """Add a node to the workflow.

        Args:
            class_type: The node class type (e.g., "KSampler")
            inputs: Dict of input values
            title: Optional display title

        Returns:
            The new node's ID as a string
        """
        node_id = str(self._next_node_id)
        self._next_node_id += 1

        self.workflow[node_id] = {
            "class_type": class_type,
            "inputs": inputs,
            "_meta": {"title": title or class_type}
        }

        return node_id

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and clean up references to it.

        Args:
            node_id: ID of the node to remove

        Returns:
            True if node was removed, False if not found
        """
        if node_id not in self.workflow:
            return False

        del self.workflow[node_id]

        # Clean up references to this node in other nodes
        for other_id, node in self.workflow.items():
            inputs = node.get("inputs", {})
            for input_name, value in list(inputs.items()):
                if isinstance(value, list) and len(value) == 2:
                    if str(value[0]) == node_id:
                        del inputs[input_name]

        return True

    def connect_nodes(
        self,
        source_node_id: str,
        source_output_slot: int,
        target_node_id: str,
        target_input_name: str,
    ) -> bool:
        """Connect two nodes together.

        Args:
            source_node_id: ID of the source node
            source_output_slot: Output slot index on source node
            target_node_id: ID of the target node
            target_input_name: Input name on target node

        Returns:
            True if connection was made, False if target node not found
        """
        if target_node_id not in self.workflow:
            return False

        self.workflow[target_node_id]["inputs"][target_input_name] = [
            source_node_id,
            source_output_slot
        ]
        return True

    def modify_input(
        self,
        node_id: str,
        input_name: str,
        value: Any,
    ) -> bool:
        """Modify a specific input on a node.

        Args:
            node_id: ID of the node
            input_name: Name of the input to modify
            value: New value for the input

        Returns:
            True if modified, False if node not found
        """
        if node_id not in self.workflow:
            return False

        self.workflow[node_id]["inputs"][input_name] = value
        return True

    def get_nodes_by_type(self, class_type: str) -> List[str]:
        """Find all nodes of a specific type.

        Args:
            class_type: The node class type to search for

        Returns:
            List of node IDs matching the class type
        """
        return [
            node_id for node_id, node in self.workflow.items()
            if node.get("class_type") == class_type
        ]

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID.

        Args:
            node_id: ID of the node

        Returns:
            Node dict or None if not found
        """
        return self.workflow.get(node_id)

    def to_json(self, indent: int = 2) -> str:
        """Export workflow as JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation of the workflow
        """
        return json.dumps(self.workflow, indent=indent)

    def from_json(self, json_str: str) -> None:
        """Load workflow from JSON string.

        Args:
            json_str: JSON string to parse
        """
        self.workflow = json.loads(json_str)
        self._next_node_id = self._calculate_next_id()

    @staticmethod
    def extract_workflow_from_response(response: str) -> Optional[Dict[str, Any]]:
        """Extract workflow JSON from an agent's response.

        Looks for JSON blocks in markdown code fences.

        Args:
            response: The agent's full response text

        Returns:
            Parsed workflow dict, or None if not found
        """
        # Try to find JSON in code blocks
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    data = json.loads(match)
                    # Verify it looks like a workflow (has node-like structure)
                    if isinstance(data, dict) and any(
                        isinstance(v, dict) and "class_type" in v
                        for v in data.values()
                    ):
                        return data
                except json.JSONDecodeError:
                    continue

        # Try parsing the whole response as JSON
        try:
            data = json.loads(response)
            if isinstance(data, dict) and any(
                isinstance(v, dict) and "class_type" in v
                for v in data.values()
            ):
                return data
        except json.JSONDecodeError:
            pass

        return None

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the workflow structure.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        for node_id, node in self.workflow.items():
            # Check required fields
            if "class_type" not in node:
                errors.append(f"Node {node_id}: missing 'class_type'")

            if "inputs" not in node:
                errors.append(f"Node {node_id}: missing 'inputs'")
                continue

            # Check connections reference valid nodes
            for input_name, value in node.get("inputs", {}).items():
                if isinstance(value, list) and len(value) == 2:
                    source_id = str(value[0])
                    if source_id not in self.workflow:
                        errors.append(
                            f"Node {node_id}: input '{input_name}' references "
                            f"non-existent node '{source_id}'"
                        )

        return len(errors) == 0, errors
