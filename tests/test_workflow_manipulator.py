"""Tests for workflow/manipulator.py - WorkflowManipulator."""

import json
import sys

import pytest

_wm_mod = sys.modules["workflow_manipulator"]
WorkflowManipulator = _wm_mod.WorkflowManipulator


# ── Construction ───────────────────────────────────────────────────────


class TestConstruction:
    def test_empty(self):
        m = WorkflowManipulator()
        assert m.workflow == {}

    def test_from_existing(self):
        wf = {"1": {"class_type": "A", "inputs": {}}}
        m = WorkflowManipulator(wf)
        assert m.workflow == wf
        # Should be a copy
        wf["2"] = {"class_type": "B", "inputs": {}}
        assert "2" not in m.workflow

    def test_next_id_calculation(self):
        m = WorkflowManipulator({"3": {}, "7": {}, "1": {}})
        assert m._next_node_id == 8

    def test_next_id_empty(self):
        m = WorkflowManipulator()
        assert m._next_node_id == 1


# ── add_node ───────────────────────────────────────────────────────────


class TestAddNode:
    def test_add_basic(self):
        m = WorkflowManipulator()
        nid = m.add_node("KSampler", {"seed": 42})
        assert nid == "1"
        assert m.workflow["1"]["class_type"] == "KSampler"
        assert m.workflow["1"]["inputs"]["seed"] == 42
        assert m.workflow["1"]["_meta"]["title"] == "KSampler"

    def test_add_with_title(self):
        m = WorkflowManipulator()
        nid = m.add_node("CLIPTextEncode", {"text": "a cat"}, title="Positive Prompt")
        assert m.workflow[nid]["_meta"]["title"] == "Positive Prompt"

    def test_add_sequential_ids(self):
        m = WorkflowManipulator()
        n1 = m.add_node("A", {})
        n2 = m.add_node("B", {})
        n3 = m.add_node("C", {})
        assert (n1, n2, n3) == ("1", "2", "3")


# ── remove_node ────────────────────────────────────────────────────────


class TestRemoveNode:
    def test_remove_existing(self):
        m = WorkflowManipulator({"1": {"class_type": "A", "inputs": {}}})
        assert m.remove_node("1") is True
        assert "1" not in m.workflow

    def test_remove_nonexistent(self):
        m = WorkflowManipulator()
        assert m.remove_node("99") is False

    def test_remove_cleans_references(self):
        m = WorkflowManipulator({
            "1": {"class_type": "A", "inputs": {}},
            "2": {"class_type": "B", "inputs": {"model": ["1", 0], "other": "keep"}},
        })
        m.remove_node("1")
        # Reference to node "1" should be removed
        assert "model" not in m.workflow["2"]["inputs"]
        # Non-reference input should remain
        assert m.workflow["2"]["inputs"]["other"] == "keep"


# ── connect_nodes ──────────────────────────────────────────────────────


class TestConnectNodes:
    def test_connect(self):
        m = WorkflowManipulator({
            "1": {"class_type": "A", "inputs": {}},
            "2": {"class_type": "B", "inputs": {}},
        })
        assert m.connect_nodes("1", 0, "2", "model") is True
        assert m.workflow["2"]["inputs"]["model"] == ["1", 0]

    def test_connect_target_not_found(self):
        m = WorkflowManipulator({"1": {"class_type": "A", "inputs": {}}})
        assert m.connect_nodes("1", 0, "99", "model") is False


# ── modify_input ───────────────────────────────────────────────────────


class TestModifyInput:
    def test_modify(self):
        m = WorkflowManipulator({
            "1": {"class_type": "KSampler", "inputs": {"steps": 20}},
        })
        assert m.modify_input("1", "steps", 30) is True
        assert m.workflow["1"]["inputs"]["steps"] == 30

    def test_modify_nonexistent_node(self):
        m = WorkflowManipulator()
        assert m.modify_input("99", "x", 1) is False


# ── get_nodes_by_type / get_node ───────────────────────────────────────


class TestLookups:
    def test_get_nodes_by_type(self):
        m = WorkflowManipulator({
            "1": {"class_type": "CLIPTextEncode", "inputs": {}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {}},
            "3": {"class_type": "KSampler", "inputs": {}},
        })
        found = m.get_nodes_by_type("CLIPTextEncode")
        assert set(found) == {"1", "2"}

    def test_get_nodes_by_type_none(self):
        m = WorkflowManipulator({"1": {"class_type": "A", "inputs": {}}})
        assert m.get_nodes_by_type("Z") == []

    def test_get_node(self):
        m = WorkflowManipulator({"1": {"class_type": "A", "inputs": {"x": 1}}})
        node = m.get_node("1")
        assert node["class_type"] == "A"

    def test_get_node_not_found(self):
        m = WorkflowManipulator()
        assert m.get_node("99") is None


# ── JSON serialization ─────────────────────────────────────────────────


class TestJson:
    def test_to_json(self):
        m = WorkflowManipulator({"1": {"class_type": "A", "inputs": {}}})
        j = m.to_json()
        assert json.loads(j) == {"1": {"class_type": "A", "inputs": {}}}

    def test_from_json(self):
        m = WorkflowManipulator()
        m.from_json('{"5": {"class_type": "B", "inputs": {"x": 1}}}')
        assert m.workflow["5"]["class_type"] == "B"
        assert m._next_node_id == 6


# ── extract_workflow_from_response ─────────────────────────────────────


class TestExtractWorkflow:
    def test_json_code_block(self):
        response = 'Here is the workflow:\n```json\n{"1": {"class_type": "KSampler", "inputs": {}}}\n```'
        result = WorkflowManipulator.extract_workflow_from_response(response)
        assert result is not None
        assert result["1"]["class_type"] == "KSampler"

    def test_plain_code_block(self):
        response = 'Workflow:\n```\n{"1": {"class_type": "A", "inputs": {}}}\n```'
        result = WorkflowManipulator.extract_workflow_from_response(response)
        assert result is not None

    def test_no_code_block_raw_json(self):
        response = '{"1": {"class_type": "A", "inputs": {}}}'
        result = WorkflowManipulator.extract_workflow_from_response(response)
        assert result is not None

    def test_no_workflow_in_response(self):
        response = "I think you should increase the denoise to 0.7."
        result = WorkflowManipulator.extract_workflow_from_response(response)
        assert result is None

    def test_json_but_not_workflow(self):
        response = '```json\n{"name": "not a workflow"}\n```'
        result = WorkflowManipulator.extract_workflow_from_response(response)
        assert result is None  # no class_type

    def test_invalid_json(self):
        response = '```json\n{invalid json}\n```'
        result = WorkflowManipulator.extract_workflow_from_response(response)
        assert result is None

    def test_multiple_code_blocks_picks_workflow(self):
        response = (
            "Here's some config:\n```json\n{\"key\": \"val\"}\n```\n\n"
            "And the workflow:\n```json\n{\"1\": {\"class_type\": \"A\", \"inputs\": {}}}\n```"
        )
        result = WorkflowManipulator.extract_workflow_from_response(response)
        assert result is not None
        assert "1" in result


# ── validate ───────────────────────────────────────────────────────────


class TestManipulatorValidate:
    def test_valid_workflow(self, simple_valid_workflow):
        m = WorkflowManipulator(simple_valid_workflow)
        valid, errors = m.validate()
        assert valid is True
        assert errors == []

    def test_missing_class_type(self):
        m = WorkflowManipulator({"1": {"inputs": {}}})
        valid, errors = m.validate()
        assert valid is False
        assert any("class_type" in e for e in errors)

    def test_missing_inputs(self):
        m = WorkflowManipulator({"1": {"class_type": "A"}})
        valid, errors = m.validate()
        assert valid is False
        assert any("inputs" in e for e in errors)

    def test_broken_link(self):
        m = WorkflowManipulator({
            "1": {"class_type": "A", "inputs": {"model": ["99", 0]}},
        })
        valid, errors = m.validate()
        assert valid is False
        assert any("99" in e for e in errors)
