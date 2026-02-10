"""Workflow validator that checks workflows against the node registry.

Performs 7 validation checks:
1. node_exists - class_type in registry
2. required_inputs - all required inputs present
3. link_validity - linked source nodes exist in workflow
4. output_slot_range - source slot index within node's output count
5. type_compatibility - output type matches input type
6. value_ranges - INT/FLOAT within min/max
7. combo_values - COMBO values in allowed options
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .node_registry import NodeRegistry


@dataclass
class ValidationIssue:
    """A single validation error or warning."""
    check: str       # e.g. "node_not_found", "required_input_missing"
    node_id: str
    message: str
    severity: str = "error"  # "error" or "warning"
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Result of validating a workflow."""
    valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)
    node_count: int = 0
    validated_against_registry: bool = False

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def format_for_agent(self) -> str:
        """Format validation errors for feeding back to the agent."""
        if not self.issues:
            return "VALIDATION PASSED: Workflow is valid."

        errors = self.errors
        warnings = self.warnings
        lines = []

        if errors:
            lines.append(f"VALIDATION ERRORS ({len(errors)} error{'s' if len(errors) != 1 else ''}):")
            for i, err in enumerate(errors, 1):
                line = f"{i}. [{err.check}] {err.message}"
                if err.suggestion:
                    line += f" - {err.suggestion}"
                lines.append(line)

        if warnings:
            lines.append(f"\nWARNINGS ({len(warnings)}):")
            for w in warnings:
                lines.append(f"  - [{w.check}] {w.message}")

        lines.append("\nFix ALL errors and provide corrected workflow JSON.")
        return "\n".join(lines)


class WorkflowValidator:
    """Validates ComfyUI workflows against the node registry."""

    def __init__(self, registry: NodeRegistry):
        self.registry = registry

    def validate(self, workflow: Dict[str, Any]) -> ValidationResult:
        """Run all validation checks on a workflow.

        Args:
            workflow: ComfyUI API-format workflow dict

        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult(
            node_count=len(workflow),
            validated_against_registry=self.registry.is_loaded,
        )

        if not workflow:
            result.issues.append(ValidationIssue(
                check="empty_workflow",
                node_id="",
                message="Workflow is empty",
            ))
            result.valid = False
            return result

        # Basic structural validation (always runs)
        self._check_structure(workflow, result)

        # Registry-based validation (only if registry is loaded)
        if self.registry.is_loaded:
            for node_id, node_data in workflow.items():
                if not isinstance(node_data, dict):
                    continue
                class_type = node_data.get("class_type", "")
                inputs = node_data.get("inputs", {})

                self._check_node_exists(node_id, class_type, result)
                self._check_required_inputs(node_id, class_type, inputs, result)
                self._check_link_validity(node_id, inputs, workflow, result)
                self._check_output_slot_range(node_id, inputs, workflow, result)
                self._check_type_compatibility(node_id, class_type, inputs, workflow, result)
                self._check_value_ranges(node_id, class_type, inputs, result)
                self._check_combo_values(node_id, class_type, inputs, result)

        result.valid = len(result.errors) == 0
        return result

    def _check_structure(self, workflow: Dict[str, Any], result: ValidationResult) -> None:
        """Check basic workflow structure."""
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                result.issues.append(ValidationIssue(
                    check="invalid_structure",
                    node_id=node_id,
                    message=f"Node {node_id!r} is not a dict",
                ))
                continue

            if "class_type" not in node_data:
                result.issues.append(ValidationIssue(
                    check="missing_class_type",
                    node_id=node_id,
                    message=f"Node {node_id!r} missing 'class_type'",
                ))

            if "inputs" not in node_data:
                result.issues.append(ValidationIssue(
                    check="missing_inputs",
                    node_id=node_id,
                    message=f"Node {node_id!r} missing 'inputs'",
                ))

    def _check_node_exists(self, node_id: str, class_type: str, result: ValidationResult) -> None:
        """Check 1: Does this node type exist?"""
        if not class_type:
            return

        if not self.registry.node_exists(class_type):
            similar = self.registry.suggest_similar(class_type)
            suggestion = f"Did you mean {similar[0]!r}?" if similar else ""
            result.issues.append(ValidationIssue(
                check="node_not_found",
                node_id=node_id,
                message=f"Node {node_id!r} uses unknown type {class_type!r}",
                suggestion=suggestion,
            ))

    def _check_required_inputs(
        self, node_id: str, class_type: str, inputs: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check 2: Are all required inputs present?"""
        node_def = self.registry.get_node(class_type)
        if not node_def:
            return

        for input_name, input_def in node_def.inputs_required.items():
            if input_name not in inputs:
                result.issues.append(ValidationIssue(
                    check="required_input_missing",
                    node_id=node_id,
                    message=f"Node {node_id!r} ({class_type}) missing required input {input_name!r}",
                ))

    def _check_link_validity(
        self, node_id: str, inputs: Dict[str, Any], workflow: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check 3: Do linked source nodes exist in the workflow?"""
        for input_name, value in inputs.items():
            if isinstance(value, list) and len(value) == 2:
                source_id = str(value[0])
                if source_id not in workflow:
                    result.issues.append(ValidationIssue(
                        check="link_invalid",
                        node_id=node_id,
                        message=f"Node {node_id!r} input {input_name!r} links to non-existent node {source_id!r}",
                    ))

    def _check_output_slot_range(
        self, node_id: str, inputs: Dict[str, Any], workflow: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check 4: Is the source slot index within the node's output count?"""
        for input_name, value in inputs.items():
            if isinstance(value, list) and len(value) == 2:
                source_id = str(value[0])
                slot_index = value[1]

                source_node = workflow.get(source_id)
                if not source_node:
                    continue  # Already caught by link_validity

                source_type = source_node.get("class_type", "")
                source_def = self.registry.get_node(source_type)
                if not source_def:
                    continue

                if isinstance(slot_index, int) and slot_index >= len(source_def.output_types):
                    result.issues.append(ValidationIssue(
                        check="output_slot_out_of_range",
                        node_id=node_id,
                        message=(
                            f"Node {node_id!r} input {input_name!r} uses slot {slot_index} "
                            f"from node {source_id!r} ({source_type}), "
                            f"but it only has {len(source_def.output_types)} output(s)"
                        ),
                    ))

    def _check_type_compatibility(
        self,
        node_id: str,
        class_type: str,
        inputs: Dict[str, Any],
        workflow: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check 5: Does the output type match the expected input type?"""
        node_def = self.registry.get_node(class_type)
        if not node_def:
            return

        for input_name, value in inputs.items():
            if not (isinstance(value, list) and len(value) == 2):
                continue

            source_id = str(value[0])
            slot_index = value[1]

            source_node = workflow.get(source_id)
            if not source_node:
                continue

            source_type = source_node.get("class_type", "")
            output_type = self.registry.get_output_type(source_type, slot_index)
            if not output_type:
                continue

            # Get expected input type
            type_info = self.registry.get_input_type(class_type, input_name)
            if not type_info:
                continue

            expected_type, _ = type_info

            # Wildcard compatibility: "*" matches anything
            if expected_type == "*" or output_type == "*":
                continue

            if output_type != expected_type:
                result.issues.append(ValidationIssue(
                    check="type_mismatch",
                    node_id=node_id,
                    message=(
                        f"Node {node_id!r} input {input_name!r} expects {expected_type!r} "
                        f"but receives {output_type!r} from node {source_id!r} slot {slot_index}"
                    ),
                    severity="warning",  # Some type mismatches work due to ComfyUI's flexibility
                ))

    def _check_value_ranges(
        self, node_id: str, class_type: str, inputs: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check 6: Are INT/FLOAT values within min/max?"""
        node_def = self.registry.get_node(class_type)
        if not node_def:
            return

        all_inputs = {**node_def.inputs_required, **node_def.inputs_optional}

        for input_name, value in inputs.items():
            # Skip connections
            if isinstance(value, list):
                continue

            input_def = all_inputs.get(input_name)
            if not input_def:
                continue

            if input_def.type in ("INT", "FLOAT") and isinstance(value, (int, float)):
                if input_def.min_val is not None and value < input_def.min_val:
                    result.issues.append(ValidationIssue(
                        check="value_out_of_range",
                        node_id=node_id,
                        message=(
                            f"Node {node_id!r} ({class_type}) {input_name}={value}, "
                            f"minimum is {input_def.min_val}"
                        ),
                        severity="warning",
                    ))
                if input_def.max_val is not None and value > input_def.max_val:
                    result.issues.append(ValidationIssue(
                        check="value_out_of_range",
                        node_id=node_id,
                        message=(
                            f"Node {node_id!r} ({class_type}) {input_name}={value}, "
                            f"maximum is {input_def.max_val}"
                        ),
                        severity="warning",
                    ))

    def _check_combo_values(
        self, node_id: str, class_type: str, inputs: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check 7: Are COMBO values in the allowed options?"""
        node_def = self.registry.get_node(class_type)
        if not node_def:
            return

        all_inputs = {**node_def.inputs_required, **node_def.inputs_optional}

        for input_name, value in inputs.items():
            # Skip connections
            if isinstance(value, list):
                continue

            input_def = all_inputs.get(input_name)
            if not input_def:
                continue

            if input_def.type == "COMBO" and input_def.options and isinstance(value, str):
                if value not in input_def.options:
                    # For file-based combos (checkpoints, loras), just warn
                    # since files may exist but not be in the cached list
                    severity = "warning"
                    result.issues.append(ValidationIssue(
                        check="invalid_combo_value",
                        node_id=node_id,
                        message=(
                            f"Node {node_id!r} ({class_type}) {input_name}={value!r} "
                            f"not in allowed values"
                        ),
                        severity=severity,
                    ))
