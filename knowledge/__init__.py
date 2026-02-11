"""ComfyUI knowledge base for agents.

The knowledge system uses markdown files with YAML frontmatter.
KnowledgeManager handles loading, indexing, and smart selection.

Legacy Python knowledge classes are kept for backwards compatibility
but the markdown files are the primary source.
"""

from .manager import KnowledgeManager, KnowledgeFile

# Legacy imports for backwards compatibility (used by workflow templates)
try:
    from .workflow_patterns import WorkflowPatterns
except ImportError:
    WorkflowPatterns = None

# Legacy classes - still importable but deprecated
try:
    from .comfyui_knowledge import ComfyUIKnowledge
    from .models_knowledge import ModelsKnowledge
    from .workflow_tuning import WorkflowTuning
    from .video_advanced import VideoAdvanced
    from .custom_nodes_guide import CustomNodesGuide
except ImportError:
    ComfyUIKnowledge = None
    ModelsKnowledge = None
    WorkflowTuning = None
    VideoAdvanced = None
    CustomNodesGuide = None

__all__ = [
    "KnowledgeManager",
    "KnowledgeFile",
    "WorkflowPatterns",
]
