from .templates import WorkflowTemplates
from .manipulator import WorkflowManipulator

# Import knowledge patterns if available
try:
    from ..knowledge.workflow_patterns import WorkflowPatterns
    __all__ = ["WorkflowTemplates", "WorkflowManipulator", "WorkflowPatterns"]
except ImportError:
    __all__ = ["WorkflowTemplates", "WorkflowManipulator"]
