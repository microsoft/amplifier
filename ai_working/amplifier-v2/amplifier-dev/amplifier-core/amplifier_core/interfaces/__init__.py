"""Interface contracts for Amplifier components."""

from .model import BaseModelProvider
from .tool import BaseTool
from .workflow import BaseWorkflow

__all__ = ["BaseModelProvider", "BaseTool", "BaseWorkflow"]
