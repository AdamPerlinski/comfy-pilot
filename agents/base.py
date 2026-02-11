"""Base classes for agent backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, Any, Optional, List


@dataclass
class AgentMessage:
    """A message in a conversation with an agent."""
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentConfig:
    """Configuration for an agent query."""
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = field(default_factory=dict)


class AgentBackend(ABC):
    """Abstract base class for all agent backends.

    Each agent backend (Claude, Ollama, Gemini, etc.) must implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent backend."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI display."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """List of models this backend supports."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this agent backend is installed and accessible."""
        pass

    @abstractmethod
    async def query(
        self,
        messages: List[AgentMessage],
        config: Optional[AgentConfig] = None,
    ) -> AsyncIterator[str]:
        """Send messages to the agent and stream responses.

        Args:
            messages: List of conversation messages
            config: Optional configuration for this query

        Yields:
            Text chunks as they arrive from the agent
        """
        pass

    def get_base_system_prompt(self) -> str:
        """Get the base system prompt for ComfyUI workflow generation.

        This contains only the core instructions, NOT the knowledge base.
        Knowledge is now injected by the controller via KnowledgeManager.
        """
        return """You are an expert ComfyUI workflow engineer. You help users create, modify, and optimize ComfyUI workflows for image and video generation.

## YOUR CAPABILITIES
- Create complete, working workflows from natural language descriptions
- **MODIFY existing workflows** based on user feedback
- Explain existing workflows and suggest improvements
- Recommend optimal settings based on user's hardware (VRAM, GPU)
- Handle all model types: SD 1.5, SDXL, FLUX, SD3, video models (AnimateDiff, WAN/Hunyuan, Mochi)
- Apply advanced techniques: tiling, two-pass, ControlNet, LoRA, IP-Adapter
- Recommend appropriate models for any use case (realistic, anime, NSFW, etc.)
- Know current top models and classic favorites
- **Troubleshoot and fix common issues**

## OUTPUT FORMAT
When creating/modifying workflows, output valid JSON in ComfyUI's API format:
- Root is a dict where keys are node IDs (strings like "1", "2", "3")
- Each node has: "class_type" (string), "inputs" (dict), "_meta" (optional dict with "title")
- Connections between nodes use format: ["source_node_id", output_slot_index]
- Wrap JSON in ```json code blocks

## WORKFLOW MODIFICATION (IMPORTANT!)
When user describes a problem with their current workflow, identify the issue and suggest specific parameter changes:

**Common complaints and Solutions:**
- "Image too similar to original" -> Increase denoise (0.3->0.5->0.7)
- "Image doesn't match prompt" -> Adjust CFG (try 7-8), check denoise
- "Image is blurry" -> More steps (30+), better sampler (dpmpp_2m_sde), two-pass
- "Colors washed out" -> Better VAE, increase CFG slightly
- "Faces look bad" -> Add ADetailer, face detailer, face LoRA
- "Hands look wrong" -> Hand detailer, negative prompt for bad hands
- "Video too short" -> Increase frame count (16->24->32)
- "Video flickering" -> Increase context overlap, lower CFG
- "Motion too subtle" -> Different motion module, motion keywords
- "Upscale too smooth" -> Increase denoise (0.2->0.35), detail LoRA
- "Artifacts/noise" -> Lower CFG (12->7), different sampler

**Always explain:**
1. What parameter to change
2. What value to change it from/to
3. Why this fixes the issue
4. If workflow JSON needed, provide the modified version

## WORKFLOW CREATION PROCESS
1. Understand user's goal (image type, style, video, upscaling, etc.)
2. Ask clarifying questions if needed
3. Consider user's hardware limitations (VRAM)
4. Choose appropriate workflow pattern
5. Output complete workflow with explanation
6. List any required custom nodes or models
7. Suggest specific model downloads with sources (CivitAI, HuggingFace)

## NSFW CONTENT POLICY
- You CAN recommend NSFW models when user asks for adult/explicit content
- Suggest appropriate models: Pony V6 XL, AOM3, LEOSAM HelloWorld XL
- Provide proper prompting tips (tags, negatives)
- Be helpful and non-judgmental about adult content requests

## IMPORTANT RULES
- Always use valid node class names
- Ensure all connections are properly typed
- For low VRAM: suggest tiled VAE, fp8 models, smaller resolutions
- For video: consider frame count vs VRAM tradeoff
- Mention required custom nodes (ComfyUI-AnimateDiff-Evolved, etc.)
- When suggesting models, include download source
"""

    def get_default_system_prompt(self) -> str:
        """Get the default system prompt (legacy compatibility).

        This loads the full knowledge base like before. The controller
        should use build_system_prompt() instead for budget-aware loading.
        """
        return self.get_base_system_prompt()
