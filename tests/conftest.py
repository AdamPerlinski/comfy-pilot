"""Shared fixtures for comfy-pilot tests.

We import modules directly by path to avoid triggering the project's
__init__.py which depends on ComfyUI's server infrastructure.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_project_root = Path(__file__).resolve().parent.parent
_tests_dir = Path(__file__).resolve().parent

# Ensure the tests directory is on sys.path so helpers can be imported
if str(_tests_dir) not in sys.path:
    sys.path.insert(0, str(_tests_dir))


def _import_module_from_path(name: str, filepath: Path, package: str = None):
    """Import a Python module from an absolute path without triggering __init__.py."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    if package is not None:
        mod.__package__ = package
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Pre-import the modules tests need (avoids __init__.py chain)
def _setup_imports():
    """Set up isolated imports for test modules."""
    # agents.base (no problematic imports)
    _import_module_from_path("agents_base", _project_root / "agents" / "base.py")
    # agents.registry
    # It imports from .base, so we need to make that work
    agents_base = sys.modules["agents_base"]
    sys.modules["agents"] = type(sys)("agents")
    sys.modules["agents"].base = agents_base
    sys.modules["agents.base"] = agents_base

    _import_module_from_path("agents_registry", _project_root / "agents" / "registry.py", package="agents")
    agents_registry = sys.modules["agents_registry"]
    sys.modules["agents"].registry = agents_registry
    sys.modules["agents.registry"] = agents_registry

    # knowledge.manager
    _import_module_from_path("knowledge_manager", _project_root / "knowledge" / "manager.py")

    # validation.node_registry
    _import_module_from_path("validation_node_registry", _project_root / "validation" / "node_registry.py")
    val_nr = sys.modules["validation_node_registry"]
    sys.modules["validation"] = type(sys)("validation")
    sys.modules["validation"].node_registry = val_nr
    sys.modules["validation.node_registry"] = val_nr

    # validation.validator
    _import_module_from_path("validation_validator", _project_root / "validation" / "validator.py", package="validation")

    # workflow.manipulator
    _import_module_from_path("workflow_manipulator", _project_root / "workflow" / "manipulator.py")


_setup_imports()


@pytest.fixture
def tmp_knowledge_dir(tmp_path):
    kdir = tmp_path / "knowledge"
    kdir.mkdir()
    (kdir / "user").mkdir()
    return kdir


@pytest.fixture
def sample_md_with_frontmatter(tmp_knowledge_dir):
    path = tmp_knowledge_dir / "core_nodes.md"
    path.write_text(
        "---\n"
        "id: core_nodes\n"
        "title: Core ComfyUI Nodes\n"
        "keywords: [KSampler, checkpoint, VAEDecode]\n"
        "category: core\n"
        "priority: high\n"
        "---\n"
        "\n"
        "## Core Nodes\n"
        "\n"
        "KSampler is the main sampling node.\n"
    )
    return path


@pytest.fixture
def sample_md_no_frontmatter(tmp_knowledge_dir):
    path = tmp_knowledge_dir / "user_notes.md"
    path.write_text("Some plain user notes about workflows.\n")
    return path


@pytest.fixture
def populated_knowledge_dir(tmp_knowledge_dir):
    files = {
        "core_nodes.md": (
            "---\nid: core_nodes\ntitle: Core Nodes\n"
            "keywords: [KSampler, checkpoint, VAEDecode, CLIPTextEncode]\n"
            "category: core\npriority: high\n---\n\n"
            "Core node documentation content here.\n"
        ),
        "models.md": (
            "---\nid: models\ntitle: Models Guide\n"
            "keywords: [FLUX, SDXL, checkpoint, download, civitai]\n"
            "category: models\npriority: medium\n---\n\n"
            "Models documentation content here.\n"
        ),
        "video_advanced.md": (
            "---\nid: video_advanced\ntitle: Advanced Video\n"
            "keywords: [video, WAN, AnimateDiff, frames, motion]\n"
            "category: video\npriority: low\n---\n\n"
            "Video documentation that is a bit longer to test budgets. " + "x" * 5000 + "\n"
        ),
        "workflow_tuning.md": (
            "---\nid: workflow_tuning\ntitle: Tuning Guide\n"
            "keywords: [denoise, cfg, steps, sampler, blurry, artifact]\n"
            "category: tuning\npriority: medium\n---\n\n"
            "Tuning docs here.\n"
        ),
    }
    for name, content in files.items():
        (tmp_knowledge_dir / name).write_text(content)

    user_file = tmp_knowledge_dir / "user" / "my_tips.md"
    user_file.write_text("My personal tips about video workflows.\n")

    return tmp_knowledge_dir


@pytest.fixture
def simple_valid_workflow():
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a photo of a cat", "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0],
            "latent_image": ["4", 0], "seed": 42, "steps": 20, "cfg": 7.0,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
        }},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "comfy"}},
    }
