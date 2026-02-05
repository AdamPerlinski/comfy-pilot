"""Prompt generator node using AI agents."""

import asyncio
from typing import Tuple

from ..agents import AgentRegistry, AgentMessage, AgentConfig


class AgenticPromptGenerator:
    """ComfyUI node that generates or enhances prompts using AI agents.

    Input a simple description and get a detailed, optimized prompt
    suitable for image generation.
    """

    CATEGORY = "comfy-pilot"
    FUNCTION = "generate"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")

    @classmethod
    def INPUT_TYPES(cls):
        # Get available agents
        agents = list(AgentRegistry.get_all().keys()) or ["ollama"]

        return {
            "required": {
                "description": ("STRING", {
                    "multiline": True,
                    "default": "A beautiful landscape"
                }),
                "agent": (agents, {"default": agents[0] if agents else "ollama"}),
                "style": ([
                    "photorealistic",
                    "artistic",
                    "anime",
                    "digital art",
                    "oil painting",
                    "watercolor",
                    "sketch",
                    "3d render",
                    "none"
                ], {"default": "photorealistic"}),
            },
            "optional": {
                "additional_instructions": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
            }
        }

    def generate(
        self,
        description: str,
        agent: str,
        style: str,
        additional_instructions: str = ""
    ) -> Tuple[str, str]:
        """Generate positive and negative prompts from a description.

        Args:
            description: Simple description of desired image
            agent: Which AI agent to use
            style: Art style to apply
            additional_instructions: Extra instructions for the agent

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._generate_async(
                    description, agent, style, additional_instructions
                )
            )
        finally:
            loop.close()

    async def _generate_async(
        self,
        description: str,
        agent_name: str,
        style: str,
        additional_instructions: str
    ) -> Tuple[str, str]:
        """Async implementation of prompt generation."""

        agent = AgentRegistry.get(agent_name)
        if not agent or not await agent.is_available():
            # Fallback: return enhanced version of input
            positive = f"{description}, {style}, high quality, detailed"
            negative = "blurry, low quality, distorted"
            return (positive, negative)

        # Build the prompt for the agent
        system_prompt = """You are a prompt engineer for Stable Diffusion and FLUX image generation models.

Your task is to convert simple descriptions into optimized prompts.

Rules:
1. Output ONLY two lines:
   - Line 1: The positive prompt (what to include)
   - Line 2: The negative prompt (what to avoid)
2. Do not include any other text, explanations, or formatting
3. Use comma-separated tags and descriptors
4. Include quality boosters like "masterpiece, best quality, highly detailed"
5. The negative prompt should include common issues to avoid

Example output:
masterpiece, best quality, a serene mountain lake at sunset, golden hour lighting, reflection on water, pine trees, snow-capped peaks, photorealistic, 8k, highly detailed
blurry, low quality, distorted, watermark, signature, text, ugly, deformed, disfigured"""

        style_instruction = f"Apply a {style} style." if style != "none" else ""
        extra = f"\nAdditional requirements: {additional_instructions}" if additional_instructions else ""

        message = f"Create prompts for: {description}\n{style_instruction}{extra}"

        messages = [AgentMessage(role="user", content=message)]
        config = AgentConfig(
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500
        )

        # Collect full response
        response = ""
        async for chunk in agent.query(messages, config):
            response += chunk

        # Parse response into positive and negative
        lines = [l.strip() for l in response.strip().split('\n') if l.strip()]

        if len(lines) >= 2:
            positive = lines[0]
            negative = lines[1]
        elif len(lines) == 1:
            positive = lines[0]
            negative = "blurry, low quality, distorted, watermark"
        else:
            # Fallback
            positive = f"{description}, {style}, high quality, detailed, masterpiece"
            negative = "blurry, low quality, distorted, watermark"

        return (positive, negative)
