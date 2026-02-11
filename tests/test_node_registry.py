"""Tests for validation/node_registry.py - NodeRegistry and data classes."""

import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_nr_mod = sys.modules["validation_node_registry"]
InputDefinition = _nr_mod.InputDefinition
NodeDefinition = _nr_mod.NodeDefinition
NodeRegistry = _nr_mod.NodeRegistry

from helpers import make_populated_registry


# ── InputDefinition ────────────────────────────────────────────────────


class TestInputDefinition:
    def test_defaults(self):
        inp = InputDefinition(name="x", type="INT")
        assert inp.required is True
        assert inp.default is None
        assert inp.min_val is None
        assert inp.max_val is None
        assert inp.options is None

    def test_full_construction(self):
        inp = InputDefinition(
            name="steps", type="INT", required=True,
            default=20, min_val=1, max_val=10000, options=None,
        )
        assert inp.name == "steps"
        assert inp.min_val == 1
        assert inp.max_val == 10000

    def test_combo_options(self):
        inp = InputDefinition(
            name="sampler", type="COMBO",
            options=["euler", "heun", "dpm"],
        )
        assert inp.type == "COMBO"
        assert len(inp.options) == 3


# ── NodeDefinition ─────────────────────────────────────────────────────


class TestNodeDefinition:
    def test_defaults(self):
        nd = NodeDefinition(class_type="TestNode")
        assert nd.category == ""
        assert nd.inputs_required == {}
        assert nd.inputs_optional == {}
        assert nd.output_types == []

    def test_with_inputs_and_outputs(self):
        nd = NodeDefinition(
            class_type="KSampler",
            inputs_required={"model": InputDefinition(name="model", type="MODEL")},
            output_types=["LATENT"],
        )
        assert "model" in nd.inputs_required
        assert nd.output_types == ["LATENT"]


# ── NodeRegistry (populated, no HTTP) ──────────────────────────────────


class TestNodeRegistryLookups:
    def test_is_loaded(self):
        reg = make_populated_registry()
        assert reg.is_loaded is True

    def test_empty_registry_not_loaded(self):
        reg = NodeRegistry()
        assert reg.is_loaded is False

    def test_node_exists(self):
        reg = make_populated_registry()
        assert reg.node_exists("KSampler") is True
        assert reg.node_exists("CheckpointLoaderSimple") is True
        assert reg.node_exists("NonExistentNode") is False

    def test_get_node(self):
        reg = make_populated_registry()
        node = reg.get_node("KSampler")
        assert node is not None
        assert node.class_type == "KSampler"
        assert "model" in node.inputs_required
        assert "steps" in node.inputs_required

    def test_get_node_not_found(self):
        reg = make_populated_registry()
        assert reg.get_node("Bogus") is None

    def test_get_output_type(self):
        reg = make_populated_registry()
        assert reg.get_output_type("CheckpointLoaderSimple", 0) == "MODEL"
        assert reg.get_output_type("CheckpointLoaderSimple", 1) == "CLIP"
        assert reg.get_output_type("CheckpointLoaderSimple", 2) == "VAE"

    def test_get_output_type_out_of_range(self):
        reg = make_populated_registry()
        assert reg.get_output_type("CheckpointLoaderSimple", 99) is None

    def test_get_output_type_unknown_node(self):
        reg = make_populated_registry()
        assert reg.get_output_type("Bogus", 0) is None

    def test_get_all_class_types(self):
        reg = make_populated_registry()
        types = reg.get_all_class_types()
        assert "KSampler" in types
        assert "CheckpointLoaderSimple" in types
        assert "SaveImage" in types

    def test_suggest_similar(self):
        reg = make_populated_registry()
        # "KSamler" is close to "KSampler"
        suggestions = reg.suggest_similar("KSamler")
        assert "KSampler" in suggestions

    def test_suggest_similar_no_match(self):
        reg = make_populated_registry()
        suggestions = reg.suggest_similar("ZZZZZZZZZ")
        assert suggestions == []

    def test_get_input_type_required(self):
        reg = make_populated_registry()
        result = reg.get_input_type("KSampler", "model")
        assert result == ("MODEL", True)

    def test_get_input_type_optional(self):
        reg = make_populated_registry()
        result = reg.get_input_type("SaveImage", "filename_prefix")
        assert result == ("STRING", False)

    def test_get_input_type_not_found(self):
        reg = make_populated_registry()
        assert reg.get_input_type("KSampler", "bogus_input") is None
        assert reg.get_input_type("BogusNode", "x") is None


# ── _parse_node_info ───────────────────────────────────────────────────


class TestParseNodeInfo:
    def test_parses_basic_info(self):
        reg = NodeRegistry()
        info = {
            "category": "sampling",
            "display_name": "KSampler",
            "description": "A sampler",
            "output": ["LATENT"],
            "output_name": ["LATENT"],
            "input": {
                "required": {
                    "model": ["MODEL"],
                    "steps": ["INT", {"default": 20, "min": 1, "max": 10000}],
                },
                "optional": {
                    "tag": ["STRING"],
                },
            },
        }
        node = reg._parse_node_info("KSampler", info)

        assert node.class_type == "KSampler"
        assert node.category == "sampling"
        assert node.output_types == ["LATENT"]
        assert "model" in node.inputs_required
        assert node.inputs_required["model"].type == "MODEL"
        assert node.inputs_required["steps"].min_val == 1
        assert node.inputs_required["steps"].max_val == 10000
        assert "tag" in node.inputs_optional

    def test_parses_combo_input(self):
        reg = NodeRegistry()
        info = {
            "input": {
                "required": {
                    "sampler": [["euler", "heun", "dpm"]],
                },
            },
        }
        node = reg._parse_node_info("Test", info)
        assert node.inputs_required["sampler"].type == "COMBO"
        assert node.inputs_required["sampler"].options == ["euler", "heun", "dpm"]

    def test_parses_empty_input(self):
        reg = NodeRegistry()
        info = {"input": {}}
        node = reg._parse_node_info("Empty", info)
        assert node.inputs_required == {}
        assert node.inputs_optional == {}

    def test_handles_missing_fields(self):
        reg = NodeRegistry()
        node = reg._parse_node_info("Bare", {})
        assert node.class_type == "Bare"
        assert node.category == ""
        assert node.output_types == []


# ── _parse_input_spec ──────────────────────────────────────────────────


class TestParseInputSpec:
    def test_string_type(self):
        reg = NodeRegistry()
        inp = reg._parse_input_spec("x", ["MODEL"], True)
        assert inp.type == "MODEL"
        assert inp.required is True

    def test_list_type_combo(self):
        reg = NodeRegistry()
        inp = reg._parse_input_spec("s", [["a", "b", "c"]], True)
        assert inp.type == "COMBO"
        assert inp.options == ["a", "b", "c"]

    def test_with_constraints(self):
        reg = NodeRegistry()
        inp = reg._parse_input_spec("v", ["FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0}], False)
        assert inp.type == "FLOAT"
        assert inp.default == 1.0
        assert inp.min_val == 0.0
        assert inp.max_val == 10.0
        assert inp.required is False

    def test_empty_spec(self):
        reg = NodeRegistry()
        inp = reg._parse_input_spec("x", [], True)
        assert inp.type == "UNKNOWN"

    def test_non_list_spec(self):
        reg = NodeRegistry()
        inp = reg._parse_input_spec("x", "just a string", True)
        assert inp.type == "UNKNOWN"


# ── fetch (with mocking) ──────────────────────────────────────────────


class TestNodeRegistryFetch:
    @pytest.mark.asyncio
    async def test_fetch_uses_cache(self):
        reg = make_populated_registry()
        # Already fetched, should return True without HTTP
        result = await reg.fetch()
        assert result is True

    @pytest.mark.asyncio
    async def test_fetch_cache_expired(self):
        reg = make_populated_registry()
        reg._last_fetch = 0  # expired
        # Will try HTTP and fail (no server), but we test the flow
        result = await reg.fetch()
        assert result is False  # HTTP failed

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        reg = NodeRegistry()

        mock_data = {
            "TestNode": {
                "category": "test",
                "display_name": "Test",
                "output": ["IMAGE"],
                "output_name": ["IMAGE"],
                "input": {"required": {"x": ["INT", {"default": 1}]}},
            }
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await reg.fetch()

        assert result is True
        assert reg.is_loaded is True
        assert reg.node_exists("TestNode")
        assert reg.get_output_type("TestNode", 0) == "IMAGE"

    @pytest.mark.asyncio
    async def test_fetch_http_error(self):
        reg = NodeRegistry()

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await reg.fetch()

        assert result is False
        assert reg.is_loaded is False

    @pytest.mark.asyncio
    async def test_fetch_connection_error(self):
        reg = NodeRegistry()

        with patch("aiohttp.ClientSession") as mock_cls:
            mock_cls.side_effect = Exception("Connection refused")
            result = await reg.fetch()

        assert result is False
