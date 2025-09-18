"""Module Generator - Generate Amplifier modules from specifications

This tool generates complete, working modules from markdown specifications
using the Claude Code SDK.
"""

from .cli import generate_command
from .generator import ModuleGenerator
from .models import FileSpec
from .models import ModuleSpec
from .models import TestSpec
from .parser import SpecificationParser

__all__ = ["ModuleSpec", "FileSpec", "TestSpec", "SpecificationParser", "ModuleGenerator", "generate_command"]
