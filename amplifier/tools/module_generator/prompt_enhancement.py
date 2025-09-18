"""Prompt enhancement system for better module generation.

This module enhances prompts to ensure complete, correct module generation.
"""

from __future__ import annotations


def enhance_generation_prompt(
    base_prompt: str,
    contract_text: str,
    impl_text: str,
    module_name: str,
    module_dir_rel: str,
) -> str:
    """Enhance the generation prompt with comprehensive instructions.

    Args:
        base_prompt: Original prompt template
        contract_text: Module contract
        impl_text: Implementation spec
        module_name: Name of the module
        module_dir_rel: Relative path to module directory

    Returns:
        Enhanced prompt with detailed instructions
    """

    # Analyze contract to find required components
    contract_analysis = analyze_contract(contract_text)

    # Build file checklist based on contract
    file_checklist = build_file_checklist(contract_analysis, module_dir_rel)

    # Add completion verification instructions
    verification_instructions = build_verification_instructions(module_dir_rel)

    enhanced = f"""
🚀 MODULE GENERATION TASK - COMPLETE IMPLEMENTATION REQUIRED
===========================================================

Module: {module_name}
Target Directory: {module_dir_rel}/

YOUR MISSION: Generate a COMPLETE, WORKING module with ALL necessary files.
You have 50 turns available. Use them to ensure COMPLETENESS.

CRITICAL REQUIREMENTS:
=====================
1. Create ALL files mentioned in your plan
2. Implement ALL functions/classes from the contract
3. No placeholders, TODOs, or stubs - everything must work
4. Continue creating files until the module is complete
5. Verify imports work correctly

{file_checklist}

{verification_instructions}

WORKFLOW:
========
1. Create directory structure
2. Create __init__.py with proper exports
3. Create models.py (if data structures needed)
4. Create main implementation file(s)
5. Create utility files (if referenced)
6. Create error classes (if needed)
7. Create README.md
8. Create comprehensive tests
9. Verify all imports work
10. Run a quick test to ensure module loads

=== CONTRACT ===
{contract_text}

=== IMPLEMENTATION SPEC ===
{impl_text}

BEGIN IMPLEMENTATION NOW!
Create each file completely before moving to the next.
After each file, immediately create any files it imports.
Continue until ALL files are created and the module is complete.
"""

    return enhanced


def analyze_contract(contract_text: str) -> dict:
    """Analyze contract to extract required components.

    Args:
        contract_text: The module contract

    Returns:
        Dictionary of extracted components
    """
    components = {
        "functions": [],
        "classes": [],
        "exceptions": [],
        "data_models": [],
        "has_async": False,
        "imports_mentioned": [],
    }

    lines = contract_text.split("\n")
    for line in lines:
        # Detect functions
        if "def " in line or "async def " in line:
            if "async def " in line:
                components["has_async"] = True
            parts = line.split("def ")
            if len(parts) > 1:
                func_name = parts[-1].split("(")[0].strip()
                if func_name and not func_name.startswith("_"):
                    components["functions"].append(func_name)

        # Detect classes
        elif "class " in line:
            parts = line.split("class ")
            if len(parts) > 1:
                class_name = parts[-1].split(":")[0].split("(")[0].strip()
                if class_name:
                    if "Error" in class_name or "Exception" in class_name:
                        components["exceptions"].append(class_name)
                    elif any(x in class_name for x in ["Model", "Config", "Data", "Result"]):
                        components["data_models"].append(class_name)
                    else:
                        components["classes"].append(class_name)

        # Detect mentioned imports
        elif "from " in line or "import " in line:
            components["imports_mentioned"].append(line.strip())

    return components


def build_file_checklist(components: dict, module_dir_rel: str) -> str:
    """Build a detailed file checklist based on contract analysis.

    Args:
        components: Analyzed contract components
        module_dir_rel: Module directory relative path

    Returns:
        Formatted file checklist
    """
    checklist = ["FILE GENERATION CHECKLIST", "=" * 25, "YOU MUST CREATE THESE FILES:", ""]

    # Always required files
    checklist.append(f"✓ [ ] {module_dir_rel}/__init__.py")
    checklist.append("      - Import ALL public functions and classes")
    checklist.append("      - Define __all__ with all exports")
    checklist.append("")

    # Models file if needed
    if components["data_models"] or "pydantic" in str(components.get("imports_mentioned", [])):
        checklist.append(f"✓ [ ] {module_dir_rel}/models.py")
        checklist.append("      - All data models and configurations")
        for model in components["data_models"]:
            checklist.append(f"      - {model} class")
        checklist.append("")

    # Main implementation file
    impl_file = f"{module_dir_rel}/core.py"
    if "synthesizer" in module_dir_rel.lower():
        impl_file = f"{module_dir_rel}/synthesizer.py"
    elif "engine" in module_dir_rel.lower():
        impl_file = f"{module_dir_rel}/engine.py"

    checklist.append(f"✓ [ ] {impl_file}")
    checklist.append("      - Main implementation")
    for func in components["functions"]:
        checklist.append(f"      - {func}() function")
    for cls in components["classes"]:
        checklist.append(f"      - {cls} class")
    checklist.append("")

    # Utils file if complex
    if len(components["functions"]) > 5:
        checklist.append(f"✓ [ ] {module_dir_rel}/utils.py")
        checklist.append("      - Helper functions")
        checklist.append("      - Internal utilities")
        checklist.append("")

    # Errors file if exceptions
    if components["exceptions"]:
        checklist.append(f"✓ [ ] {module_dir_rel}/errors.py")
        for exc in components["exceptions"]:
            checklist.append(f"      - {exc} class")
        checklist.append("")

    # Documentation
    checklist.append(f"✓ [ ] {module_dir_rel}/README.md")
    checklist.append("      - Module overview")
    checklist.append("      - Usage examples")
    checklist.append("      - API documentation")
    checklist.append("")

    # Tests
    checklist.append(f"✓ [ ] {module_dir_rel}/tests/__init__.py")
    checklist.append(f"✓ [ ] {module_dir_rel}/tests/test_core.py (or test_*.py)")
    checklist.append("      - Test main functionality")
    checklist.append("      - Edge cases")
    checklist.append("")

    return "\n".join(checklist)


def build_verification_instructions(module_dir_rel: str) -> str:
    """Build verification instructions for the AI.

    Args:
        module_dir_rel: Module directory relative path

    Returns:
        Formatted verification instructions
    """
    return f"""
SELF-VERIFICATION STEPS:
=======================
After creating files, verify completeness:

1. Check all imports:
   - Run: python -c "import {module_dir_rel.replace("/", ".")}"
   - Fix any import errors

2. Check file references:
   - If any file imports from .utils, CREATE utils.py
   - If any file imports from .models, CREATE models.py
   - If any file imports from .errors, CREATE errors.py

3. Verify __init__.py exports:
   - Ensure all public functions/classes are imported
   - Ensure __all__ is defined with exports

4. Test basic functionality:
   - Try importing the module
   - Call at least one function to verify it works

COMMON MISTAKES TO AVOID:
========================
- Forgetting to create files that are imported
- Using wrong import syntax for packages (check import rules)
- Leaving placeholder code instead of implementations
- Not creating the tests directory
- Incomplete __init__.py exports
"""
