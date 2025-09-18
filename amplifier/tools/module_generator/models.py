"""Data models for module specifications

This module defines the Pydantic models used to represent module specifications
after parsing from markdown.
"""

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ContractSpec(BaseModel):
    """Parsed contract specification from markdown"""

    module_name: str = Field(description="Module name (e.g., idea_synthesizer)")
    purpose: str = Field(description="Module's primary purpose")
    inputs: dict[str, str] = Field(default_factory=dict, description="Input specifications")
    outputs: dict[str, str] = Field(default_factory=dict, description="Output specifications")
    side_effects: list[str] = Field(default_factory=list, description="Side effects")
    dependencies: list[str] = Field(default_factory=list, description="Required dependencies")
    public_interface: list[str] = Field(default_factory=list, description="Public API exports")
    invariants: list[str] = Field(default_factory=list, description="Module invariants")
    error_handling: dict[str, str] = Field(default_factory=dict, description="Error types and handling")
    performance_specs: dict[str, str] = Field(default_factory=dict, description="Performance requirements")


class ImplementationSpec(BaseModel):
    """Parsed implementation specification from markdown"""

    module_name: str = Field(description="Module name matching contract")
    architecture: str = Field(description="Architecture overview")
    key_algorithms: list[str] = Field(default_factory=list, description="Key algorithm descriptions")
    data_models: dict[str, str] = Field(default_factory=dict, description="Data model definitions")
    processing_flow: list[str] = Field(default_factory=list, description="Processing pipeline steps")
    testing_strategy: str = Field(default="", description="Testing approach")
    error_handling_details: str = Field(default="", description="Detailed error handling")
    performance_optimizations: list[str] = Field(default_factory=list, description="Performance optimizations")
    security_considerations: list[str] = Field(default_factory=list, description="Security considerations")


class GenerationPlan(BaseModel):
    """Plan for what will be generated"""

    module_path: str = Field(description="Where module will be created")
    files_to_create: list[str] = Field(default_factory=list, description="List of files to generate")
    estimated_loc: int = Field(default=0, description="Estimated lines of code")
    key_components: list[str] = Field(default_factory=list, description="Main components")
    risks: list[str] = Field(default_factory=list, description="Identified risks")
    approach: str = Field(default="", description="Implementation approach")


class TestSpec(BaseModel):
    """Specification for a test file"""

    filename: str = Field(description="Test filename (e.g., test_parser.py)")
    description: str = Field(description="What the test validates")
    test_cases: list[str] = Field(default_factory=list, description="List of test case descriptions")


class FileSpec(BaseModel):
    """Specification for a single module file"""

    filename: str = Field(description="Filename (e.g., parser.py)")
    purpose: str = Field(description="What this file does")
    public_interface: list[str] = Field(default_factory=list, description="Public functions/classes")
    dependencies: list[str] = Field(default_factory=list, description="Internal dependencies")
    implementation_notes: str | None = Field(default=None, description="Additional implementation guidance")


class ModuleSpec(BaseModel):
    """Complete specification for a module"""

    name: str = Field(description="Module name (e.g., module_generator)")
    path: str = Field(description="Module path (e.g., amplifier/tools/module_generator)")
    purpose: str = Field(description="Module's primary purpose")

    # Core components
    files: list[FileSpec] = Field(default_factory=list, description="Implementation files")
    tests: list[TestSpec] = Field(default_factory=list, description="Test specifications")

    # Contract definition
    inputs: dict[str, str] = Field(default_factory=dict, description="Input contract")
    outputs: dict[str, str] = Field(default_factory=dict, description="Output contract")
    side_effects: list[str] = Field(default_factory=list, description="Side effects")

    # Dependencies
    external_deps: list[str] = Field(default_factory=list, description="External package dependencies")
    internal_deps: list[str] = Field(default_factory=list, description="Internal module dependencies")

    # Configuration
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration requirements")

    # Additional metadata
    performance: str | None = Field(default=None, description="Performance characteristics")
    error_handling: str | None = Field(default=None, description="Error handling approach")
    examples: list[str] = Field(default_factory=list, description="Usage examples")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "module_generator",
                "path": "amplifier/tools/module_generator",
                "purpose": "Generate complete modules from specifications",
                "files": [
                    {
                        "filename": "parser.py",
                        "purpose": "Parse markdown specifications",
                        "public_interface": ["SpecificationParser"],
                        "dependencies": ["models.py"],
                    }
                ],
                "tests": [
                    {
                        "filename": "test_parser.py",
                        "description": "Test specification parsing",
                        "test_cases": ["Parse valid spec", "Handle invalid format"],
                    }
                ],
                "inputs": {"spec_file": "Path to markdown specification"},
                "outputs": {"module": "Generated module directory"},
                "external_deps": ["pydantic", "click"],
            }
        }
