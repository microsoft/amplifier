"""
CLI tool builder and template generator for CCSDK toolkit.

Provides templates and scaffolding for creating new CLI tools
that leverage the Claude Code SDK.
"""

import shutil
import textwrap
from enum import Enum
from pathlib import Path
from typing import Optional

import click
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import Template


class CliTemplate(str, Enum):
    """Available CLI templates"""

    BASIC = "basic"
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    ORCHESTRATOR = "orchestrator"


class CliBuilder:
    """
    CLI tool builder and template generator.

    Creates scaffolding for new CCSDK-powered CLI tools.
    """

    def __init__(self, tools_dir: Path | None = None):
        """
        Initialize CLI builder.

        Args:
            tools_dir: Directory to create tools in (defaults to current directory)
        """
        self.tools_dir = tools_dir or Path.cwd()
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        # Template directory (packaged with toolkit)
        self.template_dir = Path(__file__).parent / "templates"
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_templates()

    def _create_default_templates(self):
        """Create default templates if they don't exist"""
        # Basic template
        basic_template = self.template_dir / "basic.py.j2"
        basic_template.write_text(
            textwrap.dedent(
                '''
                #!/usr/bin/env python3
                """
                {{ description }}

                Created with CCSDK Toolkit
                """

                import asyncio
                import json
                from pathlib import Path

                import click
                from amplifier.ccsdk_toolkit import (
                    ClaudeSession,
                    SessionOptions,
                    ToolkitLogger,
                    LogLevel,
                    LogFormat,
                )


                @click.command()
                @click.argument("input_text")
                @click.option("--max-turns", default=1, help="Maximum conversation turns")
                @click.option("--verbose", is_flag=True, help="Enable verbose logging")
                @click.option("--output", type=click.Path(), help="Output file path")
                def main(input_text: str, max_turns: int, verbose: bool, output: Optional[str]):
                    """{{ description }}"""
                    asyncio.run(process(input_text, max_turns, verbose, output))


                async def process(input_text: str, max_turns: int, verbose: bool, output: Optional[str]):
                    """Process the input with Claude"""
                    # Set up logging
                    log_level = LogLevel.DEBUG if verbose else LogLevel.INFO
                    logger = ToolkitLogger(name="{{ name }}", level=log_level)

                    # Configure session
                    options = SessionOptions(
                        system_prompt="{{ system_prompt }}",
                        max_turns=max_turns,
                    )

                    try:
                        async with ClaudeSession(options) as session:
                            logger.info("Starting query", input=input_text[:100])

                            response = await session.query(input_text)

                            if response.success:
                                logger.info("Query successful")

                                # Output result
                                if output:
                                    Path(output).write_text(response.content)
                                    logger.info(f"Result saved to {output}")
                                else:
                                    print(response.content)
                            else:
                                logger.error("Query failed", error=Exception(response.error))
                                click.echo(f"Error: {response.error}", err=True)

                    except Exception as e:
                        logger.error("Unexpected error", error=e)
                        click.echo(f"Error: {e}", err=True)
                        raise click.ClickException(str(e))


                if __name__ == "__main__":
                    main()
                '''
            ).strip()
        )

        # Analyzer template
        analyzer_template = self.template_dir / "analyzer.py.j2"
        analyzer_template.write_text(
            textwrap.dedent(
                '''
                #!/usr/bin/env python3
                """
                {{ description }}

                Analyzes files or directories using Claude Code SDK.
                """

                import asyncio
                import json
                from pathlib import Path
                from typing import List, Dict, Any

                import click
                from amplifier.ccsdk_toolkit import (
                    ClaudeSession,
                    SessionOptions,
                    AgentDefinition,
                    ToolkitLogger,
                    LogLevel,
                )


                @click.command()
                @click.argument("target", type=click.Path(exists=True))
                @click.option("--pattern", default="*", help="File pattern to analyze")
                @click.option("--recursive", is_flag=True, help="Analyze recursively")
                @click.option("--output-format", type=click.Choice(["json", "text"]), default="text")
                @click.option("--verbose", is_flag=True, help="Enable verbose logging")
                def main(target: str, pattern: str, recursive: bool, output_format: str, verbose: bool):
                    """{{ description }}"""
                    asyncio.run(analyze(Path(target), pattern, recursive, output_format, verbose))


                async def analyze(
                    target: Path,
                    pattern: str,
                    recursive: bool,
                    output_format: str,
                    verbose: bool
                ):
                    """Analyze the target path"""
                    # Set up logging
                    log_level = LogLevel.DEBUG if verbose else LogLevel.INFO
                    logger = ToolkitLogger(name="{{ name }}", level=log_level)

                    # Find files to analyze
                    if target.is_file():
                        files = [target]
                    else:
                        glob_pattern = f"**/{pattern}" if recursive else pattern
                        files = list(target.glob(glob_pattern))

                    logger.info(f"Found {len(files)} files to analyze")

                    # Configure session with analyzer agent
                    agent = AgentDefinition(
                        name="analyzer",
                        description="Code analysis expert",
                        system_prompt="{{ system_prompt }}",
                        tools=["Read", "Grep", "Glob"],
                    )

                    options = SessionOptions(
                        system_prompt=agent.system_prompt,
                        max_turns=3,
                    )

                    results = []

                    try:
                        async with ClaudeSession(options) as session:
                            for file_path in files:
                                logger.info(f"Analyzing {file_path}")

                                prompt = f"Analyze the file at {file_path}"
                                response = await session.query(prompt)

                                if response.success:
                                    results.append({
                                        "file": str(file_path),
                                        "analysis": response.content
                                    })
                                else:
                                    logger.error(f"Failed to analyze {file_path}",
                                               error=Exception(response.error))
                                    results.append({
                                        "file": str(file_path),
                                        "error": response.error
                                    })

                    except Exception as e:
                        logger.error("Analysis failed", error=e)
                        raise click.ClickException(str(e))

                    # Output results
                    if output_format == "json":
                        print(json.dumps(results, indent=2))
                    else:
                        for result in results:
                            print(f"\\nFile: {result['file']}")
                            print("-" * 50)
                            if "analysis" in result:
                                print(result["analysis"])
                            else:
                                print(f"Error: {result['error']}")


                if __name__ == "__main__":
                    main()
                '''
            ).strip()
        )

        # Makefile template
        makefile_template = self.template_dir / "Makefile.j2"
        makefile_template.write_text(
            textwrap.dedent(
                """
                # {{ name }} Makefile
                # Generated by CCSDK Toolkit

                .PHONY: install run test clean help

                help: ## Show this help message
                \t@echo "Available targets:"
                \t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\\n", $$1, $$2}'

                install: ## Install dependencies
                \tuv add claude-code-sdk click
                \tnpm install -g @anthropic-ai/claude-code

                run: ## Run the tool
                \tpython {{ name }}.py $(ARGS)

                test: ## Run tests
                \tpython -m pytest tests/

                clean: ## Clean generated files
                \trm -rf __pycache__ .pytest_cache
                \tfind . -type f -name "*.pyc" -delete

                # Convenience targets
                {{ name }}: ## Run with arguments (e.g., make {{ name }} ARGS="--help")
                \tpython {{ name }}.py $(ARGS)
                """
            ).strip()
        )

    def create_tool(
        self,
        name: str,
        description: str = "CCSDK-powered CLI tool",
        template: CliTemplate = CliTemplate.BASIC,
        system_prompt: str | None = None,
    ) -> Path:
        """
        Create a new CLI tool from template.

        Args:
            name: Tool name (used for filename and command)
            description: Tool description
            template: Template to use
            system_prompt: System prompt for Claude

        Returns:
            Path to the created tool directory
        """
        # Sanitize name
        safe_name = name.lower().replace(" ", "_").replace("-", "_")

        # Create tool directory
        tool_dir = self.tools_dir / safe_name
        tool_dir.mkdir(parents=True, exist_ok=True)

        # Default system prompt if not provided
        if not system_prompt:
            system_prompt = f"You are a helpful assistant for {description}"

        # Load and render template
        env = Environment(loader=FileSystemLoader(self.template_dir))

        # Render main script
        script_template = env.get_template(f"{template.value}.py.j2")
        script_content = script_template.render(
            name=safe_name,
            description=description,
            system_prompt=system_prompt,
        )

        script_path = tool_dir / f"{safe_name}.py"
        script_path.write_text(script_content)
        script_path.chmod(0o755)  # Make executable

        # Render Makefile
        if (self.template_dir / "Makefile.j2").exists():
            makefile_template = env.get_template("Makefile.j2")
            makefile_content = makefile_template.render(name=safe_name)
            (tool_dir / "Makefile").write_text(makefile_content)

        # Create basic README
        readme_content = f"""# {name}

{description}

## Installation

```bash
make install
```

## Usage

```bash
make run ARGS="--help"
# or
python {safe_name}.py --help
```

## Configuration

Edit `{safe_name}.py` to customize:
- System prompt
- Agent configuration
- Tool permissions
- Output format

Created with CCSDK Toolkit
"""
        (tool_dir / "README.md").write_text(readme_content)

        return tool_dir

    def create_template(
        self,
        name: str,
        description: str = "CCSDK-powered CLI tool",
        template_type: str = "basic",
    ) -> Path:
        """
        Create a new CLI tool from template (convenience method).

        Args:
            name: Tool name
            description: Tool description
            template_type: Template type as string

        Returns:
            Path to created tool directory
        """
        try:
            template = CliTemplate(template_type)
        except ValueError:
            template = CliTemplate.BASIC

        return self.create_tool(name, description, template)

    def list_templates(self) -> list[str]:
        """
        List available templates.

        Returns:
            List of template names
        """
        return [t.value for t in CliTemplate]

    def get_template_description(self, template_name: str) -> str:
        """
        Get description of a template.

        Args:
            template_name: Template name

        Returns:
            Template description
        """
        descriptions = {
            CliTemplate.BASIC: "Simple single-purpose tool",
            CliTemplate.ANALYZER: "File/directory analysis tool",
            CliTemplate.GENERATOR: "Code/content generation tool",
            CliTemplate.ORCHESTRATOR: "Multi-agent orchestration tool",
        }

        try:
            template = CliTemplate(template_name)
            return descriptions.get(template, "Unknown template")
        except ValueError:
            return f"Unknown template: {template_name}"

    def create_makefile_target(self, tool_name: str, makefile_path: Path | None = None) -> None:
        """
        Add a make target for the tool to a Makefile.

        Args:
            tool_name: Name of the tool
            makefile_path: Path to Makefile (defaults to ./Makefile)
        """
        makefile_path = makefile_path or Path("Makefile")

        safe_name = tool_name.lower().replace(" ", "_").replace("-", "_")

        target = f"""
# CCSDK Tool: {tool_name}
{safe_name}: ## Run {tool_name} tool
\tpython amplifier/ccsdk_toolkit/examples/{safe_name}/{safe_name}.py $(ARGS)
"""

        # Append to Makefile
        if makefile_path.exists():
            content = makefile_path.read_text()
            if f"{safe_name}:" not in content:
                makefile_path.write_text(content + target)


__all__ = [
    "CliBuilder",
    "CliTemplate",
]
