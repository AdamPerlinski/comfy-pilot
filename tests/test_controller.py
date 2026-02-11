"""Tests for controller.py - _build_workflow_context and helpers.

The controller module uses relative imports that depend on ComfyUI's server,
so we test the workflow context builder via direct method binding.
"""

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_controller_stub():
    """Create a stub that has the controller's workflow context methods.

    We can't import the full controller due to ComfyUI server dependencies,
    so we extract and bind the methods we want to test.
    """
    # Read and exec just the methods we need
    ctrl_path = Path(__file__).resolve().parent.parent / "controller.py"
    source = ctrl_path.read_text()

    # Extract the _build_workflow_context method and all _extract_* helpers
    # by creating a minimal class that has them
    class StubController:
        pass

    stub = StubController()

    # We'll use the source directly - parse the method bodies from the class
    import re
    import textwrap

    # Find all methods from _build_workflow_context onward
    method_pattern = re.compile(
        r'^    def (_build_workflow_context|_extract_\w+)\(self.*?\n(?=    def |\n# |class |\Z)',
        re.MULTILINE | re.DOTALL,
    )
    matches = method_pattern.findall(source)

    # Simpler approach: just exec the relevant portion with typing imports
    namespace = {"List": list, "Dict": dict, "Any": object, "Optional": type(None), "Set": set}
    exec("from typing import Dict, Any, List, Optional, Set", namespace)

    for match in method_pattern.finditer(source):
        method_source = textwrap.dedent(match.group(0))
        # Remove 'self' calls by making it a module-level function with self param
        exec(method_source, namespace)

    # Bind methods to stub
    for name, obj in namespace.items():
        if callable(obj) and name.startswith("_"):
            setattr(stub, name, types.MethodType(obj, stub))

    return stub


# Build the stub once
try:
    _ctrl = _make_controller_stub()
    STUB_AVAILABLE = True
except Exception as e:
    STUB_AVAILABLE = False
    _stub_error = str(e)


def _build_wf_context(workflow, verbose=True):
    """Shortcut to call the stub's method."""
    return _ctrl._build_workflow_context(workflow, verbose=verbose)


pytestmark = pytest.mark.skipif(not STUB_AVAILABLE, reason="Could not create controller stub")


# ── _build_workflow_context ────────────────────────────────────────────


class TestBuildWorkflowContext:
    def test_empty_workflow(self):
        result = _build_wf_context({"nodes": [], "links": []})
        assert "Empty workflow" in result

    def test_no_nodes_key(self):
        result = _build_wf_context({})
        assert "Empty workflow" in result

    def test_summary_mode(self):
        wf = {
            "nodes": [
                {"type": "KSampler"},
                {"type": "CLIPTextEncode"},
                {"type": "CLIPTextEncode"},
                {"type": "SaveImage"},
            ],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=False)
        assert "4 nodes" in result
        assert "CLIPTextEncode(2)" in result
        assert "KSampler" in result
        assert "SaveImage" in result
        assert "Node details" not in result

    def test_detailed_mode_ksampler(self):
        wf = {
            "nodes": [
                {"id": 1, "type": "KSampler", "title": "KSampler",
                 "widgets_values": [42, 20, 7.0, "euler", "normal", 1.0]},
            ],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "Node count" in result
        assert "Node details" in result
        assert "seed: 42" in result
        assert "steps: 20" in result
        assert "cfg: 7.0" in result
        assert "sampler_name: euler" in result
        assert "scheduler: normal" in result
        assert "denoise: 1.0" in result

    def test_checkpoint_params(self):
        wf = {
            "nodes": [
                {"id": 1, "type": "CheckpointLoaderSimple", "title": "Load Checkpoint",
                 "widgets_values": ["model.safetensors"]},
            ],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "checkpoint: model.safetensors" in result

    def test_clip_params_truncation(self):
        long_prompt = "a" * 300
        wf = {
            "nodes": [{"id": 1, "type": "CLIPTextEncode", "widgets_values": [long_prompt]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "..." in result

    def test_latent_params(self):
        wf = {
            "nodes": [{"id": 1, "type": "EmptyLatentImage", "widgets_values": [1024, 768, 2]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "width: 1024" in result
        assert "height: 768" in result
        assert "batch_size: 2" in result

    def test_lora_params(self):
        wf = {
            "nodes": [{"id": 1, "type": "LoraLoader", "widgets_values": ["detail.safetensors", 0.8, 0.5]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "lora_name: detail.safetensors" in result
        assert "strength_model: 0.8" in result
        assert "strength_clip: 0.5" in result

    def test_controlnet_params(self):
        wf = {
            "nodes": [{"id": 1, "type": "ControlNetApply", "widgets_values": [0.9, 0.0, 1.0]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "strength: 0.9" in result

    def test_vae_tiled(self):
        wf = {
            "nodes": [{"id": 1, "type": "VAEDecodeTiled", "widgets_values": [512]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "tile_size: 512" in result

    def test_animatediff_params(self):
        wf = {
            "nodes": [{"id": 1, "type": "AnimateDiffLoader", "widgets_values": ["a", "b", "c"]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "AnimateDiff node" in result
        assert "3 parameters" in result

    def test_video_params(self):
        wf = {
            "nodes": [{"id": 1, "type": "VideoOutput", "widgets_values": [24, 30, "mp4", 1920, 1080]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "param_0: 24" in result

    def test_generic_node_few_widgets(self):
        wf = {
            "nodes": [{"id": 1, "type": "SomeCustomNode", "widgets_values": [1, 2]}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "widgets: [1, 2]" in result

    def test_generic_node_many_widgets_skipped(self):
        wf = {
            "nodes": [{"id": 1, "type": "BigNode", "widgets_values": list(range(10))}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "widgets:" not in result

    def test_node_without_widgets(self):
        wf = {
            "nodes": [{"id": 1, "type": "SimpleNode"}],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        # Listed in type summary but no detail line
        assert "SimpleNode" in result

    def test_connection_count(self):
        wf = {
            "nodes": [{"id": 1, "type": "A", "widgets_values": [1]}],
            "links": [[1], [2], [3]],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "Connection count**: 3" in result

    def test_nodes_grouped_by_type(self):
        wf = {
            "nodes": [
                {"id": 1, "type": "CLIPTextEncode", "widgets_values": ["pos"]},
                {"id": 2, "type": "CLIPTextEncode", "widgets_values": ["neg"]},
                {"id": 3, "type": "KSampler", "widgets_values": [1, 2, 3, "e", "n", 1]},
            ],
            "links": [],
        }
        result = _build_wf_context(wf, verbose=True)
        assert "CLIPTextEncode: 2" in result
        assert "KSampler: 1" in result
