"""
AI-first tool builder for Claude Code tools.

This module provides an AI-powered pipeline for generating Claude Code tools
from natural language descriptions, using pure AI intelligence for understanding
and generation while using code only for orchestration and state management.
"""

from .pipeline import ToolBuilderPipeline
from .stages import CodeGenerator
from .stages import MetacognitiveAnalyzer
from .stages import QualityValidator
from .stages import RequirementsAnalyzer
from .state import StateManager
from .state import ToolBuilderState

__all__ = [
    "ToolBuilderPipeline",
    "ToolBuilderState",
    "StateManager",
    "RequirementsAnalyzer",
    "MetacognitiveAnalyzer",
    "CodeGenerator",
    "QualityValidator",
]

__version__ = "2.0.0"  # AI-first architecture
