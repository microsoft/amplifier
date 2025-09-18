"""Module Generator CLI package.

Generates a new module from a contract + implementation spec
using Claude Code SDK with safe, resume-friendly steps.

Now includes:
- Import mapping system for correct package imports
- File generation verification
- Prompt enhancement for complete generation
- Auto-fixing of common issues
"""

from .import_mappings import PACKAGE_IMPORT_MAPPINGS
from .import_mappings import get_import_guidance
from .import_mappings import validate_imports_in_code
from .prompt_enhancement import analyze_contract
from .prompt_enhancement import enhance_generation_prompt
from .verification import FileGenerationPlan
from .verification import ModuleVerifier

__all__ = [
    "PACKAGE_IMPORT_MAPPINGS",
    "get_import_guidance",
    "validate_imports_in_code",
    "ModuleVerifier",
    "FileGenerationPlan",
    "enhance_generation_prompt",
    "analyze_contract",
]
