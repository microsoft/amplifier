"""CLI tool builder for CCSDK toolkit."""

from pathlib import Path

from .templates import CliTemplate


class CliBuilder:
    """Builder for creating CLI tools with Claude Code SDK.

    Provides methods to:
    - Generate CLI tool templates
    - Create tool scaffolding
    - Generate Makefile targets
    - Set up tool structure
    """

    def __init__(self, tools_dir: Path | None = None):
        """Initialize CLI builder.

        Args:
            tools_dir: Directory for tools. Defaults to ./tools
        """
        self.tools_dir = tools_dir or Path("tools")

    def create_template(
        self, name: str, description: str, template_type: str = "basic", output_dir: Path | None = None
    ) -> Path:
        """Create a new CLI tool from template.

        Args:
            name: Tool name (will be snake_cased)
            description: Tool description
            template_type: Template type (basic, analyzer, etc.)
            output_dir: Output directory (defaults to tools_dir)

        Returns:
            Path to created tool file
        """
        # Normalize name
        tool_name = name.replace("-", "_").lower()

        # Get output directory
        out_dir = output_dir or self.tools_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        # Get template
        template = CliTemplate.get_template(template_type)

        # Substitute values
        code = template.format(name=tool_name, description=description)

        # Write tool file
        tool_file = out_dir / f"{tool_name}.py"
        tool_file.write_text(code)

        # Make executable
        tool_file.chmod(0o755)

        return tool_file

    def create_makefile_target(self, name: str, append: bool = True) -> str:
        """Create Makefile target for tool.

        Args:
            name: Tool name
            append: If True, append to Makefile if it exists

        Returns:
            Makefile target content
        """
        target = CliTemplate.makefile_target(name)

        if append:
            makefile = Path("Makefile")
            if makefile.exists():
                content = makefile.read_text()
                if f".PHONY: {name}" not in content:
                    # Add before help target or at end
                    if "help:" in content:
                        parts = content.split("help:")
                        content = parts[0] + target + "\n\nhelp:" + parts[1]
                    else:
                        content += "\n" + target

                    makefile.write_text(content)

        return target

    def scaffold_tool(
        self, name: str, description: str, template_type: str = "basic", create_tests: bool = True
    ) -> dict:
        """Create complete tool scaffolding.

        Args:
            name: Tool name
            description: Tool description
            template_type: Template type
            create_tests: Whether to create test file

        Returns:
            Dict with paths to created files
        """
        created = {}

        # Create main tool
        created["tool"] = self.create_template(name, description, template_type)

        # Create test file if requested
        if create_tests:
            test_dir = Path("tests") / "tools"
            test_dir.mkdir(parents=True, exist_ok=True)

            test_file = test_dir / f"test_{name}.py"
            test_content = f'''"""Tests for {name} tool."""
import pytest
from pathlib import Path
from tools.{name} import process


@pytest.mark.asyncio
async def test_{name}_basic(tmp_path):
    """Test basic {name} functionality."""
    # Create test input
    input_file = tmp_path / "input.txt"
    input_file.write_text("test content")

    # Process
    result = await process(str(input_file), None)

    # Verify
    assert result
    assert len(result) > 0


def test_{name}_cli(runner):
    """Test {name} CLI interface."""
    from tools.{name} import main

    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "{description}" in result.output
'''
            test_file.write_text(test_content)
            created["test"] = test_file

        # Create Makefile target
        target = self.create_makefile_target(name)
        created["makefile"] = target

        return created

    def list_templates(self) -> list[str]:
        """List available templates.

        Returns:
            List of template names
        """
        return ["basic", "analyzer"]

    def get_template_description(self, template_type: str) -> str:
        """Get description of a template.

        Args:
            template_type: Template type

        Returns:
            Template description
        """
        descriptions = {
            "basic": "Basic CLI tool for processing files with Claude",
            "analyzer": "Code analysis tool with structured output",
        }
        return descriptions.get(template_type, "Unknown template")
