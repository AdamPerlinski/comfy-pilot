"""Main controller for comfy-pilot.

Handles HTTP endpoints and coordinates agent communication,
knowledge selection, workflow validation, and auto-correction.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Set

from aiohttp import web

from .agents import AgentRegistry, AgentMessage, AgentConfig
from .agents.ollama import OllamaBackend  # noqa: F401 - registers itself
from .knowledge import KnowledgeManager
from .system import SystemMonitor
from .validation import NodeRegistry, WorkflowValidator
from .workflow import WorkflowManipulator

logger = logging.getLogger("comfy-pilot")

MAX_CORRECTION_RETRIES = 3


class ComfyPilotController:
    """Main controller handling HTTP routes and agent coordination."""

    def __init__(self):
        self.conversations: Dict[str, List[AgentMessage]] = {}
        self.knowledge_manager = KnowledgeManager()
        self.knowledge_manager.load_all()
        self.node_registry = NodeRegistry()
        self.validator = WorkflowValidator(self.node_registry)

    def setup_routes(self, routes: web.RouteTableDef) -> None:
        """Register HTTP routes with aiohttp."""

        @routes.get("/comfy-pilot/agents")
        async def get_agents(request: web.Request) -> web.Response:
            """Get list of available agents."""
            agents = await AgentRegistry.get_available_agents()
            return web.json_response(agents)

        @routes.get("/comfy-pilot/system")
        async def get_system_info(request: web.Request) -> web.Response:
            """Get system information (GPU, models, etc.)."""
            gpu_info = await SystemMonitor.get_gpu_info()
            return web.json_response(gpu_info)

        @routes.get("/comfy-pilot/models")
        async def get_models(request: web.Request) -> web.Response:
            """Get available ComfyUI models."""
            models = await SystemMonitor.get_available_models()
            return web.json_response(models)

        @routes.get("/comfy-pilot/custom-nodes")
        async def get_custom_nodes(request: web.Request) -> web.Response:
            """Get installed custom nodes information."""
            custom_nodes = await SystemMonitor.get_installed_custom_nodes()
            return web.json_response(custom_nodes)

        @routes.get("/comfy-pilot/knowledge-categories")
        async def get_knowledge_categories(request: web.Request) -> web.Response:
            """Get available knowledge categories for UI checkboxes."""
            categories = self.knowledge_manager.get_all_categories()
            return web.json_response(categories)

        @routes.get("/comfy-pilot/node-info")
        async def get_node_info(request: web.Request) -> web.Response:
            """Get available node types from the registry."""
            await self.node_registry.fetch()
            class_types = self.node_registry.get_all_class_types()
            return web.json_response({
                "loaded": self.node_registry.is_loaded,
                "node_count": len(class_types),
                "class_types": class_types[:200],  # Limit response size
            })

        @routes.post("/comfy-pilot/validate-workflow")
        async def validate_workflow(request: web.Request) -> web.Response:
            """Validate a workflow without applying it."""
            data = await request.json()
            workflow = data.get("workflow", {})

            # Try to fetch registry if not loaded
            await self.node_registry.fetch()

            result = self.validator.validate(workflow)
            return web.json_response({
                "valid": result.valid,
                "node_count": result.node_count,
                "validated_against_registry": result.validated_against_registry,
                "errors": [
                    {"check": i.check, "node_id": i.node_id,
                     "message": i.message, "suggestion": i.suggestion}
                    for i in result.errors
                ],
                "warnings": [
                    {"check": i.check, "node_id": i.node_id,
                     "message": i.message, "suggestion": i.suggestion}
                    for i in result.warnings
                ],
            })

        @routes.post("/comfy-pilot/chat")
        async def chat(request: web.Request) -> web.StreamResponse:
            """Chat with an agent (streaming response with auto-correction)."""
            data = await request.json()

            agent_name = data.get("agent", "ollama")
            message = data.get("message", "")
            history = data.get("history", [])
            current_workflow = data.get("current_workflow")
            selected_model = data.get("model")
            context_mode = data.get("context_mode", "standard")
            knowledge_categories = data.get("knowledge_categories")

            # Get the agent backend
            agent = AgentRegistry.get(agent_name)
            if not agent:
                return web.json_response(
                    {"error": f"Agent '{agent_name}' not found"},
                    status=404
                )

            # Check availability
            if not await agent.is_available():
                return web.json_response(
                    {"error": f"Agent '{agent_name}' is not available"},
                    status=503
                )

            # Build knowledge context
            categories_enabled = set(knowledge_categories) if knowledge_categories else None
            model_name = selected_model or ""
            knowledge_text = self.knowledge_manager.build_knowledge_text(
                message=message,
                agent_name=agent_name,
                model_name=model_name,
                context_mode=context_mode,
                categories_enabled=categories_enabled,
            )

            # Build system context
            system_context = await self._build_system_context()

            # Build workflow context
            workflow_context = ""
            if current_workflow:
                verbose = context_mode != "minimal"
                workflow_context = self._build_workflow_context(current_workflow, verbose=verbose)

            # Compose full system prompt
            base_prompt = agent.get_base_system_prompt()
            full_prompt = base_prompt
            if knowledge_text:
                full_prompt += "\n\n" + knowledge_text
            full_prompt += "\n\n" + system_context
            if workflow_context:
                full_prompt += "\n\n" + workflow_context

            # Build messages list
            messages = []
            for msg in history:
                messages.append(AgentMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                ))
            messages.append(AgentMessage(role="user", content=message))

            config = AgentConfig(
                model=selected_model,
                system_prompt=full_prompt,
            )

            # Try to ensure node registry is loaded for validation
            await self.node_registry.fetch()

            # Create streaming response
            response = web.StreamResponse(
                status=200,
                reason="OK",
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                }
            )
            await response.prepare(request)

            try:
                full_response = ""
                async for chunk in agent.query(messages, config):
                    full_response += chunk
                    await response.write(chunk.encode("utf-8"))

                # Auto-correction loop
                if self.node_registry.is_loaded:
                    workflow_json = WorkflowManipulator.extract_workflow_from_response(full_response)
                    if workflow_json:
                        result = self.validator.validate(workflow_json)
                        if not result.valid and result.errors:
                            await self._run_correction_loop(
                                agent, messages, config, full_response,
                                result, response
                            )

            except Exception as e:
                await response.write(f"\n\nError: {str(e)}".encode("utf-8"))

            await response.write_eof()
            return response

        @routes.post("/comfy-pilot/apply-workflow")
        async def apply_workflow(request: web.Request) -> web.Response:
            """Validate and prepare a workflow for application."""
            data = await request.json()
            workflow = data.get("workflow", {})

            # Basic structural validation
            manipulator = WorkflowManipulator(workflow)
            is_valid, errors = manipulator.validate()

            if not is_valid:
                return web.json_response({
                    "success": False,
                    "errors": errors
                }, status=400)

            # Registry-based validation if available
            await self.node_registry.fetch()
            if self.node_registry.is_loaded:
                result = self.validator.validate(workflow)
                if not result.valid:
                    return web.json_response({
                        "success": False,
                        "errors": [i.message for i in result.errors],
                        "warnings": [i.message for i in result.warnings],
                    }, status=400)

            return web.json_response({
                "success": True,
                "workflow": workflow,
                "node_count": len(workflow)
            })

    async def _run_correction_loop(
        self,
        agent,
        original_messages: List[AgentMessage],
        config: AgentConfig,
        last_response: str,
        validation_result,
        stream_response: web.StreamResponse,
    ) -> None:
        """Run the auto-correction loop when validation fails."""
        for attempt in range(1, MAX_CORRECTION_RETRIES + 1):
            # Stream correction notice
            notice = f"\n\n---\n**Validation found {len(validation_result.errors)} error(s). Correcting (attempt {attempt}/{MAX_CORRECTION_RETRIES})...**\n\n"
            await stream_response.write(notice.encode("utf-8"))

            # Build correction message
            error_text = validation_result.format_for_agent()
            correction_messages = list(original_messages)
            correction_messages.append(AgentMessage(role="assistant", content=last_response))
            correction_messages.append(AgentMessage(role="user", content=error_text))

            # Get corrected response
            corrected_response = ""
            async for chunk in agent.query(correction_messages, config):
                corrected_response += chunk
                await stream_response.write(chunk.encode("utf-8"))

            # Validate the correction
            workflow_json = WorkflowManipulator.extract_workflow_from_response(corrected_response)
            if not workflow_json:
                # No workflow in response - agent might have explained the fix
                break

            result = self.validator.validate(workflow_json)
            if result.valid or not result.errors:
                # Fixed!
                await stream_response.write(
                    "\n\n**Workflow validated successfully.**\n".encode("utf-8")
                )
                break

            # Still errors - continue loop
            last_response = corrected_response
            validation_result = result

        else:
            # Max retries exceeded
            remaining = validation_result.format_for_agent()
            await stream_response.write(
                f"\n\n**Auto-correction could not fix all errors after {MAX_CORRECTION_RETRIES} attempts.**\n{remaining}\n".encode("utf-8")
            )

    async def _build_system_context(self) -> str:
        """Build system context string for agents."""
        lines = ["## CURRENT SYSTEM STATUS"]

        # GPU info
        gpu_info = await SystemMonitor.get_gpu_info()
        if gpu_info.get("available") and gpu_info.get("gpus"):
            gpu = gpu_info["gpus"][0]
            lines.append(
                f"**GPU**: {gpu['name']}, "
                f"{gpu['vram_free_mb']}MB VRAM free of {gpu['vram_total_mb']}MB"
            )
            vram_free = gpu['vram_free_mb']
            if vram_free < 6000:
                lines.append("  -> Low VRAM: Recommend SD 1.5, fp8 models, tiled VAE")
            elif vram_free < 10000:
                lines.append("  -> Medium VRAM: SDXL OK, video with fewer frames")
            elif vram_free < 16000:
                lines.append("  -> Good VRAM: FLUX fp8 OK, most video workflows")
            else:
                lines.append("  -> High VRAM: All models supported")
        else:
            lines.append("**GPU**: Information unavailable")

        # Available models
        try:
            models = await SystemMonitor.get_available_models()
            if models.get("checkpoints"):
                lines.append(f"\n**Available checkpoints**: {', '.join(models['checkpoints'][:5])}")
                if len(models['checkpoints']) > 5:
                    lines.append(f"  ... and {len(models['checkpoints']) - 5} more")
            if models.get("loras"):
                lines.append(f"**LoRAs**: {len(models['loras'])} available")
            if models.get("controlnets"):
                lines.append(f"**ControlNets**: {', '.join(models['controlnets'][:3])}")
        except Exception:
            pass

        # Custom nodes info
        try:
            custom_nodes = await SystemMonitor.get_installed_custom_nodes()
            if custom_nodes.get("found"):
                lines.append(f"\n**Custom nodes installed**: {custom_nodes['total_count']} packs")

                capabilities = custom_nodes.get("node_capabilities", {})
                if capabilities.get("video"):
                    lines.append(f"  - Video: {', '.join(capabilities['video'])}")
                if capabilities.get("face"):
                    lines.append(f"  - Face processing: {', '.join(capabilities['face'])}")
                if capabilities.get("upscale"):
                    lines.append(f"  - Upscaling: {', '.join(capabilities['upscale'])}")
                if capabilities.get("controlnet"):
                    lines.append(f"  - ControlNet: {', '.join(capabilities['controlnet'])}")

                missing = []
                if not capabilities.get("video"):
                    missing.append("video generation (AnimateDiff/WAN)")
                if not capabilities.get("face"):
                    missing.append("face processing (Impact-Pack)")
                if not capabilities.get("controlnet"):
                    missing.append("ControlNet preprocessors")

                if missing:
                    lines.append(f"\n  **Missing for full capability**: {', '.join(missing)}")
                    lines.append("  -> Suggest installation if user needs these features")
        except Exception:
            pass

        return "\n".join(lines)

    def _build_workflow_context(self, workflow: Dict[str, Any], verbose: bool = True) -> str:
        """Build context string from the current workflow.

        Args:
            workflow: The current workflow dict
            verbose: If False, return only a summary (for small models)
        """
        nodes = workflow.get("nodes", [])
        links = workflow.get("links", [])

        if not nodes:
            return "## CURRENT WORKFLOW\n(Empty workflow)"

        # Summary mode for small models
        if not verbose:
            node_types = {}
            for node in nodes:
                t = node.get("type", "Unknown")
                node_types[t] = node_types.get(t, 0) + 1
            type_list = ", ".join(
                f"{t}({c})" if c > 1 else t
                for t, c in sorted(node_types.items())
            )
            return f"## CURRENT WORKFLOW ({len(nodes)} nodes): {type_list}"

        # Detailed mode
        lines = ["## CURRENT WORKFLOW (User's active workflow in ComfyUI)"]
        lines.append("The user has shared their current workflow. Analyze it to provide accurate modifications.")
        lines.append("")
        lines.append(f"**Node count**: {len(nodes)}")
        lines.append(f"**Connection count**: {len(links) if links else 0}")
        lines.append("")

        # Group nodes by type
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "Unknown")
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node)

        lines.append("**Nodes by type**:")
        for node_type, type_nodes in sorted(node_types.items()):
            lines.append(f"- {node_type}: {len(type_nodes)}")

        lines.append("")
        lines.append("**Node details**:")

        for node in nodes:
            node_type = node.get("type", "Unknown")
            node_id = node.get("id", "?")
            title = node.get("title", node_type)

            widgets = node.get("widgets_values", [])
            if widgets:
                lines.append(f"\n[{node_id}] {title} ({node_type}):")

                if "KSampler" in node_type:
                    self._extract_ksampler_params(lines, widgets, node)
                elif "EmptyLatentImage" in node_type:
                    self._extract_latent_params(lines, widgets)
                elif "CLIPTextEncode" in node_type or "CLIP" in node_type:
                    self._extract_clip_params(lines, widgets)
                elif "VAE" in node_type:
                    self._extract_vae_params(lines, widgets, node_type)
                elif "CheckpointLoader" in node_type:
                    self._extract_checkpoint_params(lines, widgets)
                elif "LoraLoader" in node_type:
                    self._extract_lora_params(lines, widgets)
                elif "ControlNet" in node_type:
                    self._extract_controlnet_params(lines, widgets)
                elif "Video" in node_type or "AnimateDiff" in node_type:
                    self._extract_video_params(lines, widgets, node_type)
                else:
                    if len(widgets) <= 5:
                        lines.append(f"  widgets: {widgets}")

        lines.append("")
        lines.append("When suggesting modifications, reference specific node IDs and parameter names.")
        lines.append("Provide the exact values to change (from -> to).")

        return "\n".join(lines)

    def _extract_ksampler_params(self, lines: List[str], widgets: List, node: Dict) -> None:
        param_names = ["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"]
        for i, name in enumerate(param_names):
            if i < len(widgets):
                lines.append(f"  {name}: {widgets[i]}")

    def _extract_latent_params(self, lines: List[str], widgets: List) -> None:
        param_names = ["width", "height", "batch_size"]
        for i, name in enumerate(param_names):
            if i < len(widgets):
                lines.append(f"  {name}: {widgets[i]}")

    def _extract_clip_params(self, lines: List[str], widgets: List) -> None:
        if widgets:
            text = str(widgets[0])
            if len(text) > 200:
                text = text[:200] + "..."
            lines.append(f"  prompt: \"{text}\"")

    def _extract_vae_params(self, lines: List[str], widgets: List, node_type: str) -> None:
        if "Tiled" in node_type and widgets:
            lines.append(f"  tile_size: {widgets[0] if widgets else 'default'}")

    def _extract_checkpoint_params(self, lines: List[str], widgets: List) -> None:
        if widgets:
            lines.append(f"  checkpoint: {widgets[0]}")

    def _extract_lora_params(self, lines: List[str], widgets: List) -> None:
        param_names = ["lora_name", "strength_model", "strength_clip"]
        for i, name in enumerate(param_names):
            if i < len(widgets):
                lines.append(f"  {name}: {widgets[i]}")

    def _extract_controlnet_params(self, lines: List[str], widgets: List) -> None:
        param_names = ["strength", "start_percent", "end_percent"]
        for i, name in enumerate(param_names):
            if i < len(widgets):
                lines.append(f"  {name}: {widgets[i]}")

    def _extract_video_params(self, lines: List[str], widgets: List, node_type: str) -> None:
        if "AnimateDiff" in node_type:
            lines.append(f"  (AnimateDiff node with {len(widgets)} parameters)")
        elif "Video" in node_type:
            for i, val in enumerate(widgets[:5]):
                lines.append(f"  param_{i}: {val}")


# Global controller instance
controller = ComfyPilotController()
