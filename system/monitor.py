"""System monitoring utilities."""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional


class SystemMonitor:
    """Monitor system resources for ComfyUI operations."""

    @staticmethod
    async def get_gpu_info() -> Dict[str, Any]:
        """Get GPU information using nvidia-smi.

        Returns:
            Dict with GPU info:
            {
                "available": True/False,
                "gpus": [
                    {
                        "name": "NVIDIA GeForce RTX 4090",
                        "vram_total_mb": 24564,
                        "vram_used_mb": 1234,
                        "vram_free_mb": 23330,
                        "utilization_percent": 5
                    }
                ],
                "error": None or error string
            }
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10
            )

            if process.returncode != 0:
                return {
                    "available": False,
                    "gpus": [],
                    "error": stderr.decode().strip() or "nvidia-smi failed"
                }

            gpus = []
            for line in stdout.decode().strip().split('\n'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    gpus.append({
                        "name": parts[0],
                        "vram_total_mb": int(float(parts[1])),
                        "vram_used_mb": int(float(parts[2])),
                        "vram_free_mb": int(float(parts[3])),
                        "utilization_percent": int(float(parts[4]))
                    })

            return {
                "available": True,
                "gpus": gpus,
                "error": None
            }

        except FileNotFoundError:
            return {
                "available": False,
                "gpus": [],
                "error": "nvidia-smi not found (no NVIDIA GPU?)"
            }
        except asyncio.TimeoutError:
            return {
                "available": False,
                "gpus": [],
                "error": "nvidia-smi timed out"
            }
        except Exception as e:
            return {
                "available": False,
                "gpus": [],
                "error": str(e)
            }

    @staticmethod
    async def get_available_models(comfyui_path: Optional[str] = None) -> Dict[str, List[str]]:
        """Scan ComfyUI model directories.

        Args:
            comfyui_path: Path to ComfyUI installation. If None, tries to detect.

        Returns:
            Dict mapping model category to list of filenames:
            {
                "checkpoints": ["v1-5-pruned.safetensors", ...],
                "loras": [...],
                "vaes": [...],
                "controlnets": [...]
            }
        """
        if comfyui_path is None:
            # Try common locations
            candidates = [
                Path.home() / "ComfyUI",
                Path.home() / "comfy" / "ComfyUI",
                Path("/workspace/ComfyUI"),
                Path.cwd().parent,
                Path.cwd().parent.parent,
            ]
            for candidate in candidates:
                if (candidate / "models").exists():
                    comfyui_path = str(candidate)
                    break

        if comfyui_path is None:
            return {
                "checkpoints": [],
                "loras": [],
                "vaes": [],
                "controlnets": [],
                "upscale_models": [],
                "_error": "Could not find ComfyUI models directory"
            }

        model_dirs = {
            "checkpoints": "models/checkpoints",
            "loras": "models/loras",
            "vaes": "models/vae",
            "controlnets": "models/controlnet",
            "upscale_models": "models/upscale_models",
        }

        valid_extensions = {".safetensors", ".ckpt", ".pt", ".pth", ".bin"}

        results = {}
        base = Path(comfyui_path)

        for category, subdir in model_dirs.items():
            dir_path = base / subdir
            if dir_path.exists():
                results[category] = sorted([
                    f.name for f in dir_path.iterdir()
                    if f.is_file() and f.suffix.lower() in valid_extensions
                ])
            else:
                results[category] = []

        return results

    @staticmethod
    def get_system_summary() -> str:
        """Get a human-readable system summary for agents.

        Returns:
            String describing the system resources
        """
        import platform

        lines = [
            f"OS: {platform.system()} {platform.release()}",
            f"Python: {platform.python_version()}",
        ]

        # Try to get GPU info synchronously for summary
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.free", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        lines.append(f"GPU: {parts[0]}, {parts[1]}MB VRAM free")
        except Exception:
            lines.append("GPU: Unknown (nvidia-smi not available)")

        return "\n".join(lines)

    @staticmethod
    async def get_installed_custom_nodes(comfyui_path: Optional[str] = None) -> Dict[str, Any]:
        """Detect installed custom nodes in ComfyUI.

        Args:
            comfyui_path: Path to ComfyUI installation. If None, tries to detect.

        Returns:
            Dict with custom nodes info:
            {
                "found": True/False,
                "nodes": ["ComfyUI-Manager", "ComfyUI-AnimateDiff-Evolved", ...],
                "node_capabilities": {
                    "video": ["AnimateDiff", "WAN", ...],
                    "upscale": ["UltimateSDUpscale", ...],
                    ...
                }
            }
        """
        if comfyui_path is None:
            # Try common locations
            candidates = [
                Path.home() / "ComfyUI",
                Path.home() / "comfy" / "ComfyUI",
                Path("/workspace/ComfyUI"),
                Path.cwd().parent,
                Path.cwd().parent.parent,
            ]
            for candidate in candidates:
                if (candidate / "custom_nodes").exists():
                    comfyui_path = str(candidate)
                    break

        if comfyui_path is None:
            return {
                "found": False,
                "nodes": [],
                "node_capabilities": {},
                "_error": "Could not find ComfyUI custom_nodes directory"
            }

        custom_nodes_dir = Path(comfyui_path) / "custom_nodes"
        if not custom_nodes_dir.exists():
            return {
                "found": False,
                "nodes": [],
                "node_capabilities": {},
                "_error": "custom_nodes directory not found"
            }

        # Known node pack -> capability mapping
        capability_map = {
            # Video generation
            "ComfyUI-AnimateDiff-Evolved": "video",
            "ComfyUI-VideoHelperSuite": "video",
            "ComfyUI-WAN": "video",
            "ComfyUI-SVI": "video",
            "comfyui-mochi": "video",
            "ComfyUI-CogVideoX": "video",
            "ComfyUI-LTXVideo": "video",

            # Face/body processing
            "ComfyUI-Impact-Pack": "face",
            "comfyui-reactor-node": "face",
            "ComfyUI_IPAdapter_plus": "face",
            "ComfyUI_InstantID": "face",
            "ComfyUI-FaceAnalysis": "face",

            # Upscaling
            "ComfyUI_UltimateSDUpscale": "upscale",
            "ComfyUI-TiledDiffusion": "upscale",

            # ControlNet
            "comfyui_controlnet_aux": "controlnet",

            # Efficiency/utilities
            "efficiency-nodes-comfyui": "utility",
            "was-node-suite-comfyui": "utility",
            "rgthree-comfy": "utility",
            "ComfyUI-Custom-Scripts": "utility",
            "ComfyUI-Manager": "manager",
            "ComfyUI-KJNodes": "utility",
            "ComfyUI-Crystools": "utility",
            "ComfyUI-Easy-Use": "utility",

            # Advanced
            "ComfyUI-Advanced-ControlNet": "controlnet",
            "ComfyUI-Frame-Interpolation": "video",
        }

        installed_nodes = []
        capabilities = {
            "video": [],
            "face": [],
            "upscale": [],
            "controlnet": [],
            "utility": [],
            "manager": [],
        }

        # Scan custom_nodes directory
        for item in custom_nodes_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it looks like a node pack (has __init__.py or *.py files)
                has_py = any(item.glob("*.py")) or (item / "__init__.py").exists()
                if has_py:
                    installed_nodes.append(item.name)

                    # Check capabilities
                    for pack_name, capability in capability_map.items():
                        if pack_name.lower() in item.name.lower():
                            if item.name not in capabilities[capability]:
                                capabilities[capability].append(item.name)
                            break

        return {
            "found": True,
            "nodes": sorted(installed_nodes),
            "node_capabilities": {k: v for k, v in capabilities.items() if v},
            "total_count": len(installed_nodes)
        }

    @staticmethod
    async def get_full_system_context(comfyui_path: Optional[str] = None) -> Dict[str, Any]:
        """Get complete system context including GPU, models, and custom nodes.

        Returns:
            Dict with all system information for agent context
        """
        gpu_info = await SystemMonitor.get_gpu_info()
        models = await SystemMonitor.get_available_models(comfyui_path)
        custom_nodes = await SystemMonitor.get_installed_custom_nodes(comfyui_path)

        return {
            "gpu": gpu_info,
            "models": models,
            "custom_nodes": custom_nodes
        }
