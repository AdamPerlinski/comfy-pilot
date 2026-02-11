"""Tests for agents/base.py and agents/registry.py."""

import sys

import pytest

_ab_mod = sys.modules["agents_base"]
AgentBackend = _ab_mod.AgentBackend
AgentMessage = _ab_mod.AgentMessage
AgentConfig = _ab_mod.AgentConfig

_ar_mod = sys.modules["agents_registry"]
AgentRegistry = _ar_mod.AgentRegistry

from helpers import MockAgentBackend


# ── AgentMessage / AgentConfig ─────────────────────────────────────────


class TestAgentMessage:
    def test_basic(self):
        msg = AgentMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.metadata is None

    def test_with_metadata(self):
        msg = AgentMessage(role="assistant", content="hi", metadata={"key": "val"})
        assert msg.metadata == {"key": "val"}


class TestAgentConfig:
    def test_defaults(self):
        cfg = AgentConfig()
        assert cfg.model is None
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 4096
        assert cfg.system_prompt is None
        assert cfg.additional_params == {}

    def test_custom(self):
        cfg = AgentConfig(model="llama3.2", temperature=0.5, max_tokens=2048)
        assert cfg.model == "llama3.2"
        assert cfg.temperature == 0.5


# ── AgentBackend (via MockAgentBackend) ────────────────────────────────


class TestAgentBackend:
    def test_properties(self):
        agent = MockAgentBackend(name="test", display_name="Test Agent", models=["m1", "m2"])
        assert agent.name == "test"
        assert agent.display_name == "Test Agent"
        assert agent.supported_models == ["m1", "m2"]

    @pytest.mark.asyncio
    async def test_is_available(self):
        agent = MockAgentBackend(available=True)
        assert await agent.is_available() is True

        agent2 = MockAgentBackend(available=False)
        assert await agent2.is_available() is False

    @pytest.mark.asyncio
    async def test_query(self):
        agent = MockAgentBackend()
        agent.set_response(["chunk1", "chunk2"])

        chunks = []
        async for c in agent.query([AgentMessage(role="user", content="hi")]):
            chunks.append(c)

        assert chunks == ["chunk1", "chunk2"]
        assert agent._last_messages[0].content == "hi"

    def test_get_base_system_prompt(self):
        agent = MockAgentBackend()
        prompt = agent.get_base_system_prompt()
        assert "ComfyUI" in prompt
        assert "workflow" in prompt.lower()

    def test_get_default_system_prompt_is_base(self):
        agent = MockAgentBackend()
        assert agent.get_default_system_prompt() == agent.get_base_system_prompt()


# ── AgentRegistry ──────────────────────────────────────────────────────


class TestAgentRegistry:
    def setup_method(self):
        """Clear registry before each test to avoid cross-contamination."""
        AgentRegistry.clear()

    def teardown_method(self):
        AgentRegistry.clear()

    def test_register_and_get(self):
        AgentRegistry.register(MockAgentBackend)
        agent = AgentRegistry.get("mock")
        assert agent is not None
        assert agent.name == "mock"

    def test_get_nonexistent(self):
        assert AgentRegistry.get("nonexistent") is None

    def test_list_all(self):
        AgentRegistry.register(MockAgentBackend)
        names = AgentRegistry.list_all()
        assert "mock" in names

    def test_get_all(self):
        AgentRegistry.register(MockAgentBackend)
        all_agents = AgentRegistry.get_all()
        assert "mock" in all_agents
        assert all_agents["mock"].name == "mock"

    def test_clear(self):
        AgentRegistry.register(MockAgentBackend)
        assert AgentRegistry.get("mock") is not None
        AgentRegistry.clear()
        assert AgentRegistry.get("mock") is None
        assert AgentRegistry.list_all() == []

    @pytest.mark.asyncio
    async def test_get_available_agents(self):
        AgentRegistry.register(MockAgentBackend)
        result = await AgentRegistry.get_available_agents()

        assert "mock" in result
        assert result["mock"]["available"] is True
        assert result["mock"]["display_name"] == "Mock Agent"
        assert result["mock"]["models"] == ["mock-model-1"]

    @pytest.mark.asyncio
    async def test_get_available_agents_unavailable(self):
        class UnavailableAgent(MockAgentBackend):
            def __init__(self):
                super().__init__(name="offline", display_name="Offline", available=False)

        AgentRegistry.register(UnavailableAgent)
        result = await AgentRegistry.get_available_agents()

        assert "offline" in result
        assert result["offline"]["available"] is False
        assert result["offline"]["models"] == []
