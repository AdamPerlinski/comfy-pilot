"""Tests for validation/validator.py - WorkflowValidator with all 7 checks."""

import sys

import pytest

_vv_mod = sys.modules["validation_validator"]
ValidationIssue = _vv_mod.ValidationIssue
ValidationResult = _vv_mod.ValidationResult
WorkflowValidator = _vv_mod.WorkflowValidator

_nr_mod = sys.modules["validation_node_registry"]
NodeRegistry = _nr_mod.NodeRegistry

from helpers import make_populated_registry


# ── ValidationIssue / ValidationResult ─────────────────────────────────


class TestValidationResult:
    def test_empty_result_is_valid(self):
        r = ValidationResult()
        assert r.valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_errors_property(self):
        r = ValidationResult(issues=[
            ValidationIssue(check="a", node_id="1", message="err1", severity="error"),
            ValidationIssue(check="b", node_id="2", message="warn1", severity="warning"),
            ValidationIssue(check="c", node_id="3", message="err2", severity="error"),
        ])
        assert len(r.errors) == 2
        assert len(r.warnings) == 1

    def test_format_for_agent_no_issues(self):
        r = ValidationResult()
        text = r.format_for_agent()
        assert "PASSED" in text

    def test_format_for_agent_with_errors(self):
        r = ValidationResult(issues=[
            ValidationIssue(check="node_not_found", node_id="1", message="bad node",
                            suggestion="Did you mean X?"),
        ])
        text = r.format_for_agent()
        assert "VALIDATION ERRORS" in text
        assert "bad node" in text
        assert "Did you mean X?" in text
        assert "Fix ALL errors" in text

    def test_format_for_agent_with_warnings(self):
        r = ValidationResult(issues=[
            ValidationIssue(check="type_mismatch", node_id="1", message="type warning",
                            severity="warning"),
        ])
        text = r.format_for_agent()
        assert "WARNINGS" in text
        assert "type warning" in text

    def test_format_for_agent_errors_and_warnings(self):
        r = ValidationResult(issues=[
            ValidationIssue(check="e", node_id="1", message="error msg", severity="error"),
            ValidationIssue(check="w", node_id="2", message="warn msg", severity="warning"),
        ])
        text = r.format_for_agent()
        assert "VALIDATION ERRORS (1 error)" in text
        assert "WARNINGS (1)" in text

    def test_format_pluralization(self):
        r = ValidationResult(issues=[
            ValidationIssue(check="a", node_id="1", message="e1", severity="error"),
            ValidationIssue(check="b", node_id="2", message="e2", severity="error"),
        ])
        text = r.format_for_agent()
        assert "2 errors" in text


# ── WorkflowValidator: Empty/Structural ────────────────────────────────


class TestValidatorStructural:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_empty_workflow(self):
        result = self.validator.validate({})
        assert result.valid is False
        assert result.node_count == 0
        assert any(i.check == "empty_workflow" for i in result.issues)

    def test_node_not_dict(self):
        result = self.validator.validate({"1": "not a dict"})
        assert any(i.check == "invalid_structure" for i in result.issues)

    def test_missing_class_type(self):
        result = self.validator.validate({"1": {"inputs": {}}})
        assert any(i.check == "missing_class_type" for i in result.issues)

    def test_missing_inputs(self):
        result = self.validator.validate({"1": {"class_type": "KSampler"}})
        assert any(i.check == "missing_inputs" for i in result.issues)


# ── Check 1: node_exists ──────────────────────────────────────────────


class TestCheckNodeExists:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_valid_node_passes(self):
        wf = {
            "1": {"class_type": "KSampler", "inputs": {
                "model": ["2", 0], "positive": ["3", 0], "negative": ["4", 0],
                "latent_image": ["5", 0], "seed": 42, "steps": 20, "cfg": 7.0,
                "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
            }},
        }
        result = self.validator.validate(wf)
        assert not any(i.check == "node_not_found" for i in result.issues)

    def test_unknown_node_fails(self):
        wf = {"1": {"class_type": "FakeNode", "inputs": {}}}
        result = self.validator.validate(wf)
        errors = [i for i in result.issues if i.check == "node_not_found"]
        assert len(errors) == 1
        assert "FakeNode" in errors[0].message

    def test_typo_suggests_correction(self):
        wf = {"1": {"class_type": "KSamler", "inputs": {}}}
        result = self.validator.validate(wf)
        errors = [i for i in result.issues if i.check == "node_not_found"]
        assert len(errors) == 1
        assert "KSampler" in errors[0].suggestion


# ── Check 2: required_inputs ──────────────────────────────────────────


class TestCheckRequiredInputs:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_all_required_present(self):
        wf = {
            "1": {"class_type": "EmptyLatentImage", "inputs": {
                "width": 512, "height": 512, "batch_size": 1,
            }},
        }
        result = self.validator.validate(wf)
        assert not any(i.check == "required_input_missing" for i in result.issues)

    def test_missing_required_input(self):
        wf = {
            "1": {"class_type": "CLIPTextEncode", "inputs": {
                "text": "hello",
                # "clip" is missing
            }},
        }
        result = self.validator.validate(wf)
        errors = [i for i in result.issues if i.check == "required_input_missing"]
        assert len(errors) == 1
        assert "clip" in errors[0].message


# ── Check 3: link_validity ────────────────────────────────────────────


class TestCheckLinkValidity:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_valid_link(self):
        wf = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "hi", "clip": ["1", 1]}},
        }
        result = self.validator.validate(wf)
        assert not any(i.check == "link_invalid" for i in result.issues)

    def test_link_to_nonexistent_node(self):
        wf = {
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "hi", "clip": ["99", 0]}},
        }
        result = self.validator.validate(wf)
        errors = [i for i in result.issues if i.check == "link_invalid"]
        assert len(errors) == 1
        assert "99" in errors[0].message


# ── Check 4: output_slot_range ────────────────────────────────────────


class TestCheckOutputSlotRange:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_valid_slot(self):
        wf = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
            "2": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["1", 2]}},
            "3": {"class_type": "KSampler", "inputs": {
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                "latent_image": ["6", 0], "seed": 1, "steps": 20, "cfg": 7.0,
                "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
            }},
            "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "a", "clip": ["1", 1]}},
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["1", 1]}},
            "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1}},
        }
        result = self.validator.validate(wf)
        assert not any(i.check == "output_slot_out_of_range" for i in result.issues)

    def test_slot_out_of_range(self):
        wf = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
            # CheckpointLoaderSimple has 3 outputs (0,1,2). Slot 5 is invalid.
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a", "clip": ["1", 5]}},
        }
        result = self.validator.validate(wf)
        errors = [i for i in result.issues if i.check == "output_slot_out_of_range"]
        assert len(errors) == 1
        assert "slot 5" in errors[0].message


# ── Check 5: type_compatibility ───────────────────────────────────────


class TestCheckTypeCompatibility:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_compatible_types(self):
        wf = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
            # CLIPTextEncode expects CLIP on input "clip", slot 1 of CheckpointLoader = CLIP
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a", "clip": ["1", 1]}},
        }
        result = self.validator.validate(wf)
        type_issues = [i for i in result.issues if i.check == "type_mismatch"]
        assert len(type_issues) == 0

    def test_incompatible_types(self):
        wf = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
            # CLIPTextEncode expects CLIP on "clip", but slot 0 = MODEL (wrong)
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a", "clip": ["1", 0]}},
        }
        result = self.validator.validate(wf)
        type_issues = [i for i in result.issues if i.check == "type_mismatch"]
        assert len(type_issues) == 1
        assert "MODEL" in type_issues[0].message
        assert "CLIP" in type_issues[0].message
        assert type_issues[0].severity == "warning"


# ── Check 6: value_ranges ────────────────────────────────────────────


class TestCheckValueRanges:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_values_in_range(self):
        wf = {
            "1": {"class_type": "EmptyLatentImage", "inputs": {
                "width": 512, "height": 512, "batch_size": 1,
            }},
        }
        result = self.validator.validate(wf)
        range_issues = [i for i in result.issues if i.check == "value_out_of_range"]
        assert len(range_issues) == 0

    def test_value_below_min(self):
        wf = {
            "1": {"class_type": "EmptyLatentImage", "inputs": {
                "width": 4, "height": 512, "batch_size": 1,  # min is 16
            }},
        }
        result = self.validator.validate(wf)
        range_issues = [i for i in result.issues if i.check == "value_out_of_range"]
        assert len(range_issues) == 1
        assert "width" in range_issues[0].message
        assert "minimum" in range_issues[0].message

    def test_value_above_max(self):
        wf = {
            "1": {"class_type": "EmptyLatentImage", "inputs": {
                "width": 512, "height": 512, "batch_size": 99999,  # max is 4096
            }},
        }
        result = self.validator.validate(wf)
        range_issues = [i for i in result.issues if i.check == "value_out_of_range"]
        assert len(range_issues) == 1
        assert "batch_size" in range_issues[0].message
        assert "maximum" in range_issues[0].message

    def test_skips_connections(self):
        """Values that are links (lists) should be skipped for range checking."""
        wf = {
            "1": {"class_type": "KSampler", "inputs": {
                "model": ["2", 0],  # link, not a value
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": 42, "steps": 20, "cfg": 7.0,
                "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
            }},
        }
        result = self.validator.validate(wf)
        # Should not error on the link values
        range_issues = [i for i in result.issues if i.check == "value_out_of_range"]
        assert len(range_issues) == 0


# ── Check 7: combo_values ────────────────────────────────────────────


class TestCheckComboValues:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_valid_combo(self):
        wf = {
            "1": {"class_type": "KSampler", "inputs": {
                "model": ["2", 0], "positive": ["3", 0], "negative": ["4", 0],
                "latent_image": ["5", 0], "seed": 42, "steps": 20, "cfg": 7.0,
                "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
            }},
        }
        result = self.validator.validate(wf)
        combo_issues = [i for i in result.issues if i.check == "invalid_combo_value"]
        assert len(combo_issues) == 0

    def test_invalid_combo(self):
        wf = {
            "1": {"class_type": "KSampler", "inputs": {
                "model": ["2", 0], "positive": ["3", 0], "negative": ["4", 0],
                "latent_image": ["5", 0], "seed": 42, "steps": 20, "cfg": 7.0,
                "sampler_name": "nonexistent_sampler",
                "scheduler": "normal", "denoise": 1.0,
            }},
        }
        result = self.validator.validate(wf)
        combo_issues = [i for i in result.issues if i.check == "invalid_combo_value"]
        assert len(combo_issues) == 1
        assert "sampler_name" in combo_issues[0].message
        assert combo_issues[0].severity == "warning"


# ── Full valid workflow ──────────────────────────────────────────────


class TestFullWorkflowValidation:
    def setup_method(self):
        self.registry = make_populated_registry()
        self.validator = WorkflowValidator(self.registry)

    def test_valid_workflow_passes(self, simple_valid_workflow):
        result = self.validator.validate(simple_valid_workflow)
        # Should have no errors (warnings are OK)
        assert result.valid is True, f"Errors: {[i.message for i in result.errors]}"
        assert result.node_count == 7
        assert result.validated_against_registry is True

    def test_without_registry(self, simple_valid_workflow):
        """Without registry loaded, only structural checks run."""
        empty_reg = NodeRegistry()
        validator = WorkflowValidator(empty_reg)
        result = validator.validate(simple_valid_workflow)
        # Should still pass structural checks
        assert result.valid is True
        assert result.validated_against_registry is False

    def test_multiple_errors(self):
        """A workflow with several different errors."""
        wf = {
            "1": {"class_type": "FakeNode", "inputs": {}},  # unknown type
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "hi"}},  # missing "clip"
            "3": {"inputs": {}},  # missing class_type
            "4": "not a dict",  # invalid structure
        }
        result = self.validator.validate(wf)
        assert result.valid is False

        checks = {i.check for i in result.issues}
        assert "node_not_found" in checks
        assert "required_input_missing" in checks
        assert "missing_class_type" in checks
        assert "invalid_structure" in checks
