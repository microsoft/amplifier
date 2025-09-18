"""
Tool Generator Agent

Generates complete amplifier CLI tools with proper structure, AI capabilities,
and all required patterns (incremental processing, resume, file I/O).
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from ..agent import execute_task


@dataclass
class ToolSpecification:
    """Specification for a tool to be generated."""

    name: str
    description: str
    version: str = "1.0.0"
    capabilities: Optional[List[str]] = None
    input_pattern: str = "*.md"  # Default for markdown files
    default_output_dir: str = "output"
    custom_options: Optional[List[Dict]] = None
    ai_system_prompt: Optional[str] = None
    ai_prompt_template: Optional[str] = None
    processes_batches: bool = False
    needs_persistence: bool = True
    module_name: Optional[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.custom_options is None:
            self.custom_options = []
        if self.module_name is None:
            # Convert tool name to valid module name
            self.module_name = self.name.lower().replace("-", "_").replace(" ", "_")


@dataclass
class GeneratedTool:
    """Represents a generated tool."""

    tool_name: str
    tool_path: str
    specification: ToolSpecification
    generated_at: str = ""
    files_created: Optional[List[str]] = None
    status: str = "pending"  # pending, generated, failed
    error: Optional[str] = None

    def __post_init__(self):
        if self.files_created is None:
            self.files_created = []


class ToolGeneratorAgent:
    """Agent specialized in generating complete CLI tools."""

    def __init__(self, workspace: Optional[Path] = None):
        """Initialize the tool generator.

        Args:
            workspace: Optional workspace directory for generated tools
        """
        self.agent_type = "tool_generator"
        self.workspace = workspace or Path("amplifier_workspace")
        self.tools_dir = self.workspace / "tools"
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def _generate_validation_code(self) -> str:
        """Generate validation functions for AI responses.

        Returns:
            Python code string with validation functions
        """
        validation_code = '''# Validation utilities
GARBAGE_PATTERNS = [
    "I'll analyze", "I'll help", "Let me", "I cannot",
    "As an AI", "I'm going to", "I will", "Here's", "Here is",
    "I've", "I have", "I'm", "I am", "I understand"
]

def validate_ai_response(response: str, item_name: str) -> tuple[bool, str, dict]:
    """Validate AI response and return (is_valid, error_msg, parsed_data).

    Args:
        response: Raw response from AI
        item_name: Name of item being processed (for error messages)

    Returns:
        Tuple of (is_valid, error_message, parsed_data)
    """
    # Check response exists
    if not response or len(response.strip()) < 50:
        return False, "Response too short or empty", {}

    # Check for garbage patterns indicating AI preamble
    lower_response = response.lower()
    for pattern in GARBAGE_PATTERNS:
        if lower_response.startswith(pattern.lower()):
            return False, f"AI returned preamble instead of data: '{pattern}...'", {}

    # Try to parse as JSON if expected
    try:
        # Clean markdown formatting if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove trailing ```

        cleaned = cleaned.strip()

        # Attempt JSON parsing
        data = json.loads(cleaned)

        # Check data has actual content
        if isinstance(data, dict) and not data:
            return False, "Empty dictionary returned", {}
        if isinstance(data, list) and not data:
            return False, "Empty list returned", {}

        return True, "", data

    except json.JSONDecodeError:
        # If not JSON, check it's meaningful text content
        if len(response.strip()) > 100:
            # Seems like substantial text content
            return True, "", {"content": response.strip()}
        return False, "Could not parse response as JSON and content too short", {}


def validate_processing_result(result: dict, required_fields: list = None) -> tuple[bool, str]:
    """Validate a processing result has expected structure.

    Args:
        result: Result dictionary to validate
        required_fields: Optional list of required field names

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(result, dict):
        return False, f"Result is not a dictionary: {type(result)}"

    # Check for error fields indicating failure
    if "error" in result:
        return False, f"Processing failed with error: {result.get('error')}"

    # Check required fields if specified
    if required_fields:
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Check result has some content
    content_fields = [k for k in result.keys() if k not in ["source", "id", "timestamp"]]
    if not content_fields:
        return False, "Result has no content fields beyond metadata"

    return True, ""'''
        return validation_code

    def _generate_test_harness(self, spec: ToolSpecification) -> str:
        """Generate comprehensive test harness for the tool.

        Args:
            spec: Tool specification

        Returns:
            Python test code string
        """
        test_code = f'''"""Comprehensive tests for {spec.name}."""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import cli, validate_ai_response, validate_processing_result


class TestValidation:
    """Test validation functions."""

    def test_validate_ai_response_catches_garbage(self):
        """Test that validation catches AI preambles and garbage."""
        garbage_responses = [
            "I'll analyze this for you",
            "Let me help you with that",
            "I cannot process this",
            "As an AI, I can help",
            "Here's what I found:",
            "",  # Empty
            "   ",  # Whitespace only
            "Short",  # Too short
            "{{}}",  # Empty JSON object
            "[]",  # Empty JSON array
        ]

        for response in garbage_responses:
            is_valid, error, _ = validate_ai_response(response, "test_item")
            assert not is_valid, f"Should have caught garbage: {{response!r}}, but got: {{error}}"

    def test_validate_ai_response_accepts_valid_json(self):
        """Test validation accepts valid JSON responses."""
        valid_responses = [
            json.dumps({{"result": "test", "data": [1, 2, 3]}}),
            json.dumps({{"key": "value"}}),
            '```json\\n{{"wrapped": "in markdown"}}\\n```',
            json.dumps([{{"item": 1}}, {{"item": 2}}]),
        ]

        for response in valid_responses:
            is_valid, error, data = validate_ai_response(response, "test_item")
            assert is_valid, f"Should accept valid JSON: {{response!r}}, error: {{error}}"
            assert data, "Should return parsed data"

    def test_validate_ai_response_handles_text_content(self):
        """Test validation handles substantial text content."""
        text_response = "This is a substantial text response that contains meaningful content. " * 3
        is_valid, error, data = validate_ai_response(text_response, "test_item")
        assert is_valid, f"Should accept substantial text: {{error}}"
        assert "content" in data, "Should wrap text in content field"
        assert data["content"] == text_response.strip()

    def test_validate_processing_result(self):
        """Test result validation."""
        # Test valid results
        valid_result = {{"data": "test", "source": "file.txt"}}
        is_valid, error = validate_processing_result(valid_result)
        assert is_valid, f"Should accept valid result: {{error}}"

        # Test with required fields
        is_valid, error = validate_processing_result(valid_result, ["data", "source"])
        assert is_valid, "Should have required fields"

        # Test missing required fields
        is_valid, error = validate_processing_result(valid_result, ["missing_field"])
        assert not is_valid, "Should detect missing required field"
        assert "missing_field" in error.lower()

        # Test error results
        error_result = {{"error": "Processing failed", "source": "file.txt"}}
        is_valid, error = validate_processing_result(error_result)
        assert not is_valid, "Should reject error results"
        assert "Processing failed" in error

        # Test empty results
        empty_result = {{"source": "file.txt"}}  # Only metadata
        is_valid, error = validate_processing_result(empty_result)
        assert not is_valid, "Should reject empty results"
        assert "no content" in error.lower()


class TestCLI:
    """Test CLI functionality."""

    def test_cli_help(self):
        """Test that CLI help works."""
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "{spec.name}" in result.output

    def test_version_command(self):
        """Test version command."""
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "v{spec.version}" in result.output

    def test_status_command_no_output(self):
        """Test status command when no output exists."""
        from click.testing import CliRunner
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])
            assert "No output directory found" in result.output

    @pytest.mark.asyncio
    async def test_process_with_validation(self, tmp_path):
        """Test processing with validation."""
        # Create test input
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        test_file = input_dir / "test.md"
        test_file.write_text("Test content for processing")

        output_dir = tmp_path / "output"

        from click.testing import CliRunner
        runner = CliRunner()

        # Mock the AI processing to return garbage
        with patch('cli.process_item_with_ai') as mock_process:
            mock_process.return_value = {{"error": "validation_failed", "message": "AI returned preamble"}}

            result = runner.invoke(cli, [
                "process",
                "--input", str(input_dir),
                "--output", str(output_dir)
            ])

            # Check that validation error is handled
            assert "validation_failed" in str(result.output) or result.exit_code != 0


class TestIntegration:
    """Integration tests for the full pipeline."""

    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, tmp_path):
        """Test complete processing pipeline."""
        # Create test input
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test content")

        # Test with valid mock response
        mock_response = json.dumps({{"processed": True, "result": "test"}})

        with patch('cli.ClaudeSDKClient') if 'ai_integration' in {spec.capabilities or []} else patch('cli.process_item'):
            # Run processing
            from cli import process_async, get_items_to_process

            items = get_items_to_process(input_file.parent)
            assert len(items) == 1, "Should find one item to process"

            # Verify item structure
            item = items[0]
            assert "path" in item
            assert "name" in item
            assert Path(item["path"]).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])'''

        return test_code

    def determine_components(self, spec: ToolSpecification) -> List[str]:
        """Determine which components to include based on specification.

        Args:
            spec: Tool specification

        Returns:
            List of component names to include
        """
        components = []

        # Always need file I/O
        components.append("file_io")

        # Check for AI capabilities
        if spec.capabilities and "ai_processing" in spec.capabilities:
            components.append("ai_integration")
            components.append("async_processing")

        # Check for batch processing
        if spec.processes_batches:
            components.append("incremental_processor")
            components.append("async_processing")

        return components

    async def analyze_requirements(self, description: str) -> ToolSpecification:
        """Analyze requirements to create tool specification.

        Args:
            description: Natural language description of the tool

        Returns:
            ToolSpecification object
        """
        prompt = """
Analyze this tool description and create a specification.

TOOL DESCRIPTION:
{description}

Determine:
1. Tool name (kebab-case)
2. Short description (one line)
3. What capabilities it needs (choose from: ai_processing, batch_processing, file_io, web_api, data_transformation)
4. Does it process batches of items? (true/false)
5. Does it need AI integration? (true/false)
6. Input file pattern (e.g., "*.md", "*.json", "*.py")
7. Any custom command-line options needed

Return ONLY valid JSON in this format:
{{
    "name": "tool-name",
    "description": "Short description",
    "capabilities": ["ai_processing", "batch_processing"],
    "processes_batches": true,
    "needs_ai": true,
    "input_pattern": "*.md",
    "custom_options": [
        {{
            "name": "max-items",
            "default": 5,
            "help": "Maximum items to process"
        }}
    ],
    "ai_system_prompt": "You are a helpful assistant that...",
    "ai_prompt_template": "Process the following content..."
}}
"""

        context = {"description": description}
        response = await execute_task(prompt, context, timeout=60)

        try:
            data = json.loads(response)

            # Create specification
            spec = ToolSpecification(
                name=data.get("name", "unnamed-tool"),
                description=data.get("description", "Generated tool"),
                capabilities=data.get("capabilities", []),
                processes_batches=data.get("processes_batches", False),
                input_pattern=data.get("input_pattern", "*.md"),
                custom_options=data.get("custom_options", []),
                ai_system_prompt=data.get("ai_system_prompt"),
                ai_prompt_template=data.get("ai_prompt_template"),
            )

            return spec

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse tool specification: {e}")

    def generate_tool_files(self, spec: ToolSpecification) -> GeneratedTool:
        """Generate all files for a complete tool.

        Args:
            spec: Tool specification

        Returns:
            GeneratedTool object with status
        """
        # Ensure module_name is set (it should be from __post_init__)
        if spec.module_name is None:
            spec.module_name = spec.name.lower().replace("-", "_").replace(" ", "_")

        tool_dir = self.tools_dir / spec.module_name
        tool_dir.mkdir(parents=True, exist_ok=True)

        generated_tool = GeneratedTool(
            tool_name=spec.name, tool_path=str(tool_dir), specification=spec, generated_at=datetime.now().isoformat()
        )

        try:
            # Determine components
            components = self.determine_components(spec)

            # Generate validation code
            validation_code = self._generate_validation_code()

            # Generate CLI file
            cli_template = self.env.get_template("cli_base.py.j2")

            # Properly escape strings for Python code using json.dumps
            ai_system_prompt = spec.ai_system_prompt or "You are a helpful assistant."
            ai_prompt_template = spec.ai_prompt_template or "Process the following content:"

            # Use json.dumps to properly escape strings for Python
            ai_system_prompt = json.dumps(ai_system_prompt)
            ai_prompt_template = json.dumps(ai_prompt_template)

            cli_content = cli_template.render(
                tool_name=spec.name,
                tool_description=spec.description,
                tool_version=spec.version,
                components=components,
                custom_options=spec.custom_options,
                default_output_dir=spec.default_output_dir,
                input_pattern=spec.input_pattern,
                ai_system_prompt=ai_system_prompt,
                ai_prompt_template=ai_prompt_template,
                validation_code=validation_code,  # Add validation code
            )

            cli_file = tool_dir / "cli.py"
            cli_file.write_text(cli_content)
            if generated_tool.files_created is not None:
                generated_tool.files_created.append(str(cli_file))

            # Generate __init__.py
            init_content = f'''"""
{spec.name} - {spec.description}

Generated by Amplifier Microtask Pipeline
"""

__version__ = "{spec.version}"
'''
            init_file = tool_dir / "__init__.py"
            init_file.write_text(init_content)
            if generated_tool.files_created is not None:
                generated_tool.files_created.append(str(init_file))

            # Generate Makefile
            makefile_template = self.env.get_template("Makefile.j2")
            makefile_content = makefile_template.render(
                tool_name=spec.name,
                tool_description=spec.description,
                module_name=f"amplifier_workspace.tools.{spec.module_name}",
            )

            makefile = tool_dir / "Makefile"
            makefile.write_text(makefile_content)
            if generated_tool.files_created is not None:
                generated_tool.files_created.append(str(makefile))

            # Generate README
            readme_content = f"""# {spec.name}

{spec.description}

## Installation

This tool was generated by the Amplifier Microtask Pipeline and is ready to use.

## Usage

### Basic Usage

```bash
# Show help
python -m amplifier_workspace.tools.{spec.module_name}.cli --help

# Process files
python -m amplifier_workspace.tools.{spec.module_name}.cli process --input <input_path> --output <output_path>
```

### Using Make

```bash
# From the tool directory
cd {tool_dir}

# Show available commands
make help

# Process files
make process INPUT=<input_path> OUTPUT=<output_path>
```

## Features

- ✅ CLI interface with Click
{"- ✅ AI integration with Claude SDK" if "ai_integration" in components else ""}
{"- ✅ Incremental processing with resume capability" if "incremental_processor" in components else ""}
{"- ✅ Batch processing support" if spec.processes_batches else ""}
- ✅ Robust file I/O with retry logic

## Configuration

The tool accepts the following options:

- `--input`: Input file or directory (required)
- `--output`: Output directory (default: {spec.default_output_dir})
{"".join(f"- `--{opt['name']}`: {opt['help']} (default: {opt['default']})" for opt in (spec.custom_options or []))}

## Generated Files

Results are saved to the output directory as JSON files with full metadata.
"""

            readme_file = tool_dir / "README.md"
            readme_file.write_text(readme_content)
            if generated_tool.files_created is not None:
                generated_tool.files_created.append(str(readme_file))

            # Create tests directory
            tests_dir = tool_dir / "tests"
            tests_dir.mkdir(exist_ok=True)

            # Generate comprehensive test file
            test_content = self._generate_test_harness(spec)

            test_file = tests_dir / "test_cli.py"
            test_file.write_text(test_content)
            if generated_tool.files_created is not None:
                generated_tool.files_created.append(str(test_file))

            # Update status
            generated_tool.status = "generated"

        except Exception as e:
            generated_tool.status = "failed"
            generated_tool.error = str(e)

        return generated_tool

    async def generate_tool_from_description(self, description: str) -> GeneratedTool:
        """Generate a complete tool from a natural language description.

        Args:
            description: Natural language description of desired tool

        Returns:
            GeneratedTool object with all files created
        """
        # Analyze requirements
        spec = await self.analyze_requirements(description)

        # Generate tool files
        generated_tool = self.generate_tool_files(spec)

        return generated_tool

    def get_tool_status(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a generated tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Status dictionary or None if not found
        """
        # Convert to module name
        module_name = tool_name.lower().replace("-", "_").replace(" ", "_")
        tool_dir = self.tools_dir / module_name

        if not tool_dir.exists():
            return None

        status = {"name": tool_name, "path": str(tool_dir), "exists": True, "files": []}

        # List files in tool directory
        for file_path in tool_dir.rglob("*"):
            if file_path.is_file():
                status["files"].append(str(file_path.relative_to(tool_dir)))

        return status
