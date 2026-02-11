"""Test helpers: pre-built registries and mock objects."""

import sys
from typing import AsyncIterator, List, Optional

_nr_mod = sys.modules["validation_node_registry"]
NodeRegistry = _nr_mod.NodeRegistry
NodeDefinition = _nr_mod.NodeDefinition
InputDefinition = _nr_mod.InputDefinition

_ab_mod = sys.modules["agents_base"]
AgentBackend = _ab_mod.AgentBackend
AgentMessage = _ab_mod.AgentMessage
AgentConfig = _ab_mod.AgentConfig


def make_populated_registry() -> NodeRegistry:
    """Build a NodeRegistry with realistic test node definitions (no HTTP needed)."""
    registry = NodeRegistry()
    registry._fetched = True
    registry._last_fetch = 9999999999  # far future so cache never expires

    registry._nodes = {
        "CheckpointLoaderSimple": NodeDefinition(
            class_type="CheckpointLoaderSimple",
            category="loaders",
            display_name="Load Checkpoint",
            inputs_required={
                "ckpt_name": InputDefinition(
                    name="ckpt_name", type="COMBO", required=True,
                    options=["model.safetensors", "sd_xl_base.safetensors"],
                ),
            },
            output_types=["MODEL", "CLIP", "VAE"],
            output_names=["MODEL", "CLIP", "VAE"],
        ),
        "CLIPTextEncode": NodeDefinition(
            class_type="CLIPTextEncode",
            category="conditioning",
            display_name="CLIP Text Encode",
            inputs_required={
                "text": InputDefinition(name="text", type="STRING", required=True),
                "clip": InputDefinition(name="clip", type="CLIP", required=True),
            },
            output_types=["CONDITIONING"],
            output_names=["CONDITIONING"],
        ),
        "EmptyLatentImage": NodeDefinition(
            class_type="EmptyLatentImage",
            category="latent",
            display_name="Empty Latent Image",
            inputs_required={
                "width": InputDefinition(
                    name="width", type="INT", required=True,
                    default=512, min_val=16, max_val=16384,
                ),
                "height": InputDefinition(
                    name="height", type="INT", required=True,
                    default=512, min_val=16, max_val=16384,
                ),
                "batch_size": InputDefinition(
                    name="batch_size", type="INT", required=True,
                    default=1, min_val=1, max_val=4096,
                ),
            },
            output_types=["LATENT"],
            output_names=["LATENT"],
        ),
        "KSampler": NodeDefinition(
            class_type="KSampler",
            category="sampling",
            display_name="KSampler",
            inputs_required={
                "model": InputDefinition(name="model", type="MODEL", required=True),
                "positive": InputDefinition(name="positive", type="CONDITIONING", required=True),
                "negative": InputDefinition(name="negative", type="CONDITIONING", required=True),
                "latent_image": InputDefinition(name="latent_image", type="LATENT", required=True),
                "seed": InputDefinition(
                    name="seed", type="INT", required=True,
                    default=0, min_val=0, max_val=0xffffffffffffffff,
                ),
                "steps": InputDefinition(
                    name="steps", type="INT", required=True,
                    default=20, min_val=1, max_val=10000,
                ),
                "cfg": InputDefinition(
                    name="cfg", type="FLOAT", required=True,
                    default=8.0, min_val=0.0, max_val=100.0,
                ),
                "sampler_name": InputDefinition(
                    name="sampler_name", type="COMBO", required=True,
                    options=["euler", "euler_ancestral", "heun", "dpm_2",
                             "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_sde"],
                ),
                "scheduler": InputDefinition(
                    name="scheduler", type="COMBO", required=True,
                    options=["normal", "karras", "exponential", "sgm_uniform"],
                ),
                "denoise": InputDefinition(
                    name="denoise", type="FLOAT", required=True,
                    default=1.0, min_val=0.0, max_val=1.0,
                ),
            },
            output_types=["LATENT"],
            output_names=["LATENT"],
        ),
        "VAEDecode": NodeDefinition(
            class_type="VAEDecode",
            category="latent",
            display_name="VAE Decode",
            inputs_required={
                "samples": InputDefinition(name="samples", type="LATENT", required=True),
                "vae": InputDefinition(name="vae", type="VAE", required=True),
            },
            output_types=["IMAGE"],
            output_names=["IMAGE"],
        ),
        "SaveImage": NodeDefinition(
            class_type="SaveImage",
            category="image",
            display_name="Save Image",
            inputs_required={
                "images": InputDefinition(name="images", type="IMAGE", required=True),
            },
            inputs_optional={
                "filename_prefix": InputDefinition(
                    name="filename_prefix", type="STRING", required=False,
                    default="ComfyUI",
                ),
            },
            output_types=[],
            output_names=[],
        ),
        "LoraLoader": NodeDefinition(
            class_type="LoraLoader",
            category="loaders",
            display_name="Load LoRA",
            inputs_required={
                "model": InputDefinition(name="model", type="MODEL", required=True),
                "clip": InputDefinition(name="clip", type="CLIP", required=True),
                "lora_name": InputDefinition(
                    name="lora_name", type="COMBO", required=True,
                    options=["detail.safetensors", "style.safetensors"],
                ),
                "strength_model": InputDefinition(
                    name="strength_model", type="FLOAT", required=True,
                    default=1.0, min_val=-20.0, max_val=20.0,
                ),
                "strength_clip": InputDefinition(
                    name="strength_clip", type="FLOAT", required=True,
                    default=1.0, min_val=-20.0, max_val=20.0,
                ),
            },
            output_types=["MODEL", "CLIP"],
            output_names=["MODEL", "CLIP"],
        ),
    }
    return registry


class MockAgentBackend(AgentBackend):
    """A mock agent backend for testing."""

    def __init__(self, name="mock", display_name="Mock Agent", models=None, available=True):
        self._name = name
        self._display_name = display_name
        self._models = models or ["mock-model-1"]
        self._available = available
        self._last_messages = None
        self._last_config = None
        self._response_chunks = ["Hello ", "from ", "mock!"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def supported_models(self) -> List[str]:
        return self._models

    async def is_available(self) -> bool:
        return self._available

    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        self._last_messages = messages
        self._last_config = config
        for chunk in self._response_chunks:
            yield chunk

    def set_response(self, chunks: List[str]):
        self._response_chunks = chunks
