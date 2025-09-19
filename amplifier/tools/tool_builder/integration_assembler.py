"""Integration assembly microtask for Tool Builder.

This module assembles generated modules into a complete working tool,
wiring up the interfaces and creating the final CLI entry point.
"""

from pathlib import Path
from typing import Any

from .exceptions import CCSDKRequiredError
from .exceptions import MicrotaskError


class IntegrationAssembler:
    """Assembles modules into a complete tool."""

    def __init__(self):
        """Initialize the assembler."""
        # Integration doesn't strictly need CC SDK but we check for consistency
        self._verify_sdk_available()

    def _verify_sdk_available(self):
        """Verify Claude Code SDK is available."""
        import importlib.util

        if importlib.util.find_spec("claude_code_sdk") is None:
            raise CCSDKRequiredError()

    async def assemble(
        self,
        tool_name: str,
        architecture: dict[str, Any],
        generated_modules: list[dict[str, Any]],
        output_dir: Path,
    ) -> dict[str, Any]:
        """Assemble modules into a complete tool.

        This microtask:
        - Creates the main CLI entry point
        - Wires up module dependencies
        - Creates Makefile integration
        - Sets up package structure

        Args:
            tool_name: Name of the tool being built
            architecture: Architecture specification
            generated_modules: List of generated module results
            output_dir: Tool output directory

        Returns:
            Assembly result with integration details
        """
        try:
            # Create main CLI entry point
            cli_file = await self._create_cli_entry(tool_name, architecture, output_dir)

            # Create __init__.py for package
            init_file = await self._create_package_init(tool_name, output_dir)

            # Create Makefile target
            makefile_entry = self._generate_makefile_target(tool_name)

            # Save Makefile snippet to a file for easy copying
            makefile_snippet = output_dir / "Makefile.snippet"
            makefile_snippet.write_text(makefile_entry)

            # Create basic README
            readme_file = await self._create_readme(tool_name, architecture, output_dir)

            # Try to append to main Makefile if requested
            auto_added = await self._try_add_to_makefile(tool_name, makefile_entry)

            return {
                "status": "success",
                "cli_file": str(cli_file),
                "init_file": str(init_file),
                "readme_file": str(readme_file),
                "makefile_target": makefile_entry,
                "makefile_snippet_file": str(makefile_snippet),
                "auto_added_to_makefile": auto_added,
                "summary": f"Tool '{tool_name}' assembled successfully",
                "next_steps": self._generate_next_steps(tool_name, auto_added),
            }

        except Exception as e:
            raise MicrotaskError(f"Integration assembly failed: {str(e)}")

    async def _create_cli_entry(
        self,
        tool_name: str,
        architecture: dict[str, Any],
        output_dir: Path,
    ) -> Path:
        """Create the main CLI entry point."""

        # Check if this is a directory processor
        cli_type = architecture.get("cli_type", "file_processor")

        if cli_type == "directory_processor":
            # Generate directory-based CLI
            return await self._create_directory_cli(tool_name, architecture, output_dir)
        # Generate file-based CLI (default)
        return await self._create_file_cli(tool_name, architecture, output_dir)

    async def _create_directory_cli(
        self,
        tool_name: str,
        architecture: dict[str, Any],
        output_dir: Path,
    ) -> Path:
        """Create a CLI that processes directories."""

        cli_content = f'''#!/usr/bin/env python3
"""CLI entry point for {tool_name} tool.

This module processes directories of content.
"""

import sys
import asyncio
from pathlib import Path

# Add the parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

import click

# Dynamic import of core module's exported function
try:
    from . import core
    # Find the main callable
    if hasattr(core, '__all__') and core.__all__:
        func_name = core.__all__[0]
        core_process = getattr(core, func_name)
    else:
        for name in ['process', 'process_directory', 'process_content', 'main', 'run']:
            if hasattr(core, name):
                core_process = getattr(core, name)
                break
        else:
            for attr_name in dir(core):
                if not attr_name.startswith('_'):
                    attr = getattr(core, attr_name)
                    if callable(attr):
                        core_process = attr
                        break
            else:
                raise ImportError("No callable function found in core module")
except ImportError:
    import core
    if hasattr(core, '__all__') and core.__all__:
        func_name = core.__all__[0]
        core_process = getattr(core, func_name)
    else:
        for name in ['process', 'process_directory', 'process_content', 'main', 'run']:
            if hasattr(core, name):
                core_process = getattr(core, name)
                break
        else:
            for attr_name in dir(core):
                if not attr_name.startswith('_'):
                    attr = getattr(core, attr_name)
                    if callable(attr):
                        core_process = attr
                        break
            else:
                raise ImportError("No callable function found in core module")


@click.group()
def cli():
    """{tool_name.replace("_", " ").title()} - Amplifier CLI Tool

    {architecture.get("entry_point", "Tool for processing directories")}
    """


@cli.command(name='run')
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_dir', type=click.Path())
@click.option('--max-files', '-m', default=5, help='Maximum number of files to process')
def run(source_dir: str, output_dir: str, max_files: int) -> None:
    """Process a directory of content."""
    import asyncio
    import inspect

    click.echo(f"Processing directory {{source_dir}}...")
    click.echo(f"Output will be written to {{output_dir}}")
    click.echo(f"Processing up to {{max_files}} files")

    # Handle different function signatures
    if inspect.iscoroutinefunction(core_process):
        result = asyncio.run(core_process(source_dir, output_dir, max_files))
    else:
        result = core_process(source_dir, output_dir, max_files)

    if isinstance(result, dict):
        click.echo("\nProcessing complete!")
        for key, value in result.items():
            click.echo(f"{{key}}: {{value}}")
    else:
        click.echo(result)


if __name__ == "__main__":
    cli()
'''

        cli_file = output_dir / "cli.py"
        cli_file.write_text(cli_content)
        cli_file.chmod(0o755)
        return cli_file

    async def _create_file_cli(
        self,
        tool_name: str,
        architecture: dict[str, Any],
        output_dir: Path,
    ) -> Path:
        """Create the original file-based CLI."""

        cli_content = f'''#!/usr/bin/env python3
"""CLI entry point for {tool_name} tool.

This module can be run directly or as a package module.
"""

import sys
import asyncio
from pathlib import Path

# Add the parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

import click

# Dynamic import of core module's exported function
# The module generator may create different function names
try:
    # Try package import first
    from . import core

    # Find the main callable - check __all__ first, then common names
    if hasattr(core, '__all__') and core.__all__:
        # Use the first exported function
        func_name = core.__all__[0]
        core_process = getattr(core, func_name)
    else:
        # Try common function names in order of preference
        for name in ['process', 'process_content', 'process_pipeline', 'main', 'run', 'execute']:
            if hasattr(core, name):
                core_process = getattr(core, name)
                break
        else:
            # Try to find any callable
            for attr_name in dir(core):
                if not attr_name.startswith('_'):
                    attr = getattr(core, attr_name)
                    if callable(attr):
                        core_process = attr
                        break
            else:
                raise ImportError("No callable function found in core module")
except ImportError:
    # Fallback for direct execution
    import core

    # Same dynamic discovery for direct import
    if hasattr(core, '__all__') and core.__all__:
        func_name = core.__all__[0]
        core_process = getattr(core, func_name)
    else:
        for name in ['process', 'process_content', 'process_pipeline', 'main', 'run', 'execute']:
            if hasattr(core, name):
                core_process = getattr(core, name)
                break
        else:
            for attr_name in dir(core):
                if not attr_name.startswith('_'):
                    attr = getattr(core, attr_name)
                    if callable(attr):
                        core_process = attr
                        break
            else:
                raise ImportError("No callable function found in core module")


@click.group()
def cli():
    """{tool_name.replace("_", " ").title()} - Amplifier CLI Tool

    {architecture.get("entry_point", "Tool for processing data")}
    """


# Create a proper Click command wrapper for async functions
@cli.command(name='process')
@click.argument('source_dir', type=click.Path(exists=True), required=False)
@click.argument('output_dir', type=click.Path(), required=False)
@click.option('--input', '-i', 'input_file', type=click.Path(exists=True), help='Input file path')
@click.option('--output', '-o', 'output_file', type=click.Path(), help='Output file path')
@click.option('--max-files', '-m', default=5, help='Maximum number of files to process')
def process_command(source_dir=None, output_dir=None, input_file=None, output_file=None, max_files=5):
    """Process data using the core module."""
    import asyncio
    import inspect

    # Handle different function signatures
    if inspect.iscoroutinefunction(core_process):
        # Async function - use asyncio.run
        if source_dir and output_dir:
            result = asyncio.run(core_process(source_dir, output_dir, max_files))
        elif input_file:
            result = asyncio.run(core_process(input_file, output_file))
        else:
            result = asyncio.run(core_process())
    else:
        # Sync function or Click command
        if source_dir and output_dir:
            result = core_process(source_dir, output_dir, max_files)
        elif input_file:
            result = core_process(input_file, output_file)
        else:
            result = core_process()

    if isinstance(result, dict):
        click.echo("\\nProcessing complete!")
        for key, value in result.items():
            click.echo(f"{{{{key}}}}: {{{{value}}}}")
    else:
        click.echo(result)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path")
def run(input_file: str, output: str | None) -> None:
    """Run the {tool_name} tool using the actual generated module."""
    import importlib
    import sys
    from pathlib import Path

    # Import the actual generated core module
    try:
        # Try to import the generated core module dynamically
        from .core import main as core_module
    except ImportError:
        try:
            # Fallback to direct import for testing
            from core import main as core_module
        except ImportError:
            # Try importing from core directly (if main.py exports at package level)
            try:
                from . import core as core_module
            except ImportError:
                try:
                    import core as core_module
                except ImportError:
                    click.echo("Error: Could not import the generated core module.")
                    click.echo("Make sure the module was generated correctly.")
                    sys.exit(1)

    # Find the main callable function dynamically
    core_process_impl = None

    # Check common function names
    for name in ['process', 'process_content', 'process_pipeline', 'main', 'run', 'execute']:
        if hasattr(core_module, name):
            core_process_impl = getattr(core_module, name)
            break

    if not core_process_impl:
        # Try to find any callable
        for attr_name in dir(core_module):
            if not attr_name.startswith('_'):
                attr = getattr(core_module, attr_name)
                if callable(attr):
                    core_process_impl = attr
                    break

    if not core_process_impl:
        click.echo("Error: No callable function found in the generated core module.")
        sys.exit(1)

    # Read the input file
    click.echo(f"Processing {{input_file}}...")
    with open(input_file) as f:
        data = f.read()

    # Use the actual generated module's process function
    # Handle both sync and async functions
    import inspect

    try:
        if inspect.iscoroutinefunction(core_process_impl):
            # Async function - use asyncio.run
            import asyncio
            result = asyncio.run(core_process_impl(data))
        else:
            # Sync function or Click command
            result = core_process_impl(data)
    except TypeError:
        # Module might expect different arguments
        # Try calling with Click's context if it's a Click command
        from click.testing import CliRunner
        runner = CliRunner()
        result_obj = runner.invoke(core_process_impl, [input_file])
        result = result_obj.output if result_obj.exit_code == 0 else f"Error: {{result_obj.output}}"
    except Exception as e:
        result = f"Error processing with generated module: {{str(e)}}"

    # Write output
    if output:
        with open(output, "w") as f:
            f.write(str(result))
        click.echo(f"Output written to {{output}}")
    else:
        click.echo(result)


if __name__ == "__main__":
    cli()
'''

        cli_file = output_dir / "cli.py"
        cli_file.write_text(cli_content)
        # Make the CLI file executable
        cli_file.chmod(0o755)
        return cli_file

    async def _create_package_init(self, tool_name: str, output_dir: Path) -> Path:
        """Create package __init__.py."""
        init_content = f'''"""{tool_name} - Amplifier CLI Tool."""

__version__ = "0.1.0"

from .cli import cli

__all__ = ["cli"]
'''

        init_file = output_dir / "__init__.py"
        init_file.write_text(init_content)
        return init_file

    async def _create_readme(
        self,
        tool_name: str,
        architecture: dict[str, Any],
        output_dir: Path,
    ) -> Path:
        """Create basic README."""
        readme_content = f"""# {tool_name.replace("_", " ").title()}

## Description

{architecture.get("entry_point", "Amplifier CLI tool for data processing")}

## Usage

### Via Make (after adding to Makefile)
```bash
make {tool_name} ARGS="run input.txt -o output.txt"
```

### Direct execution
```bash
cd ~/.amplifier/generated_tools/{tool_name}
python cli.py run input.txt -o output.txt
```

### Adding to main project Makefile
```bash
cat Makefile.snippet >> ../../Makefile
```

## Architecture

### Modules

"""

        for module in architecture.get("modules", []):
            readme_content += f"- **{module.get('name')}**: {module.get('purpose')}\n"

        readme_content += f"""

### Data Flow

{architecture.get("data_flow", "Input → Processing → Output")}

## Testing

```bash
pytest amplifier/tools/{tool_name}/
```

## Generated by Amplifier Tool Builder

This tool was generated using the Amplifier Tool Builder, demonstrating:
- Modular "bricks and studs" architecture
- Claude Code SDK integration
- Microtask decomposition
- Automated tool generation
"""

        readme_file = output_dir / "README.md"
        readme_file.write_text(readme_content)
        return readme_file

    async def _try_add_to_makefile(self, tool_name: str, makefile_entry: str) -> bool:
        """Try to automatically add the target to the main Makefile.

        Returns True if successfully added, False otherwise.
        """
        import os

        # Check if AUTO_ADD_TO_MAKEFILE env var is set
        if not os.environ.get("AUTO_ADD_TO_MAKEFILE"):
            return False

        try:
            # Find the main project Makefile
            # Look for it in common locations
            makefile_paths = [
                Path.cwd() / "Makefile",
                Path.home() / "repos" / "amplifier-cli-tools" / "Makefile",
                Path.home() / "amplifier" / "Makefile",
            ]

            makefile_path = None
            for path in makefile_paths:
                if path.exists():
                    makefile_path = path
                    break

            if not makefile_path:
                return False

            # Check if the target already exists
            makefile_content = makefile_path.read_text()
            if f"{tool_name}:" in makefile_content:
                # Target already exists, don't duplicate
                return False

            # Find a good place to insert (after the last tool entry or at the end)
            # Look for the "# Generated tools" section or append at the end
            if "# Generated tools" in makefile_content:
                # Insert after the generated tools section
                lines = makefile_content.split("\n")
                insert_index = None
                for i, line in enumerate(lines):
                    if "# Generated tools" in line:
                        # Find the next empty line or next section
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() == "" or lines[j].startswith("#"):
                                insert_index = j
                                break
                        if insert_index is None:
                            insert_index = len(lines)
                        break

                if insert_index:
                    lines.insert(insert_index, makefile_entry.rstrip())
                    makefile_path.write_text("\n".join(lines))
                    return True
            else:
                # Append at the end with a new section
                with open(makefile_path, "a") as f:
                    f.write("\n# Generated tools\n")
                    f.write(makefile_entry)
                return True

        except Exception:
            # Silently fail if we can't add to Makefile
            return False

        return False

    def _generate_next_steps(self, tool_name: str, auto_added: bool) -> list[str]:
        """Generate next steps based on what was accomplished."""
        steps = []

        if auto_added:
            steps.append("✅ Makefile target automatically added!")
        else:
            steps.append(f"Add to Makefile: cat ~/.amplifier/generated_tools/{tool_name}/Makefile.snippet >> Makefile")
            steps.append("Tip: Set AUTO_ADD_TO_MAKEFILE=1 to auto-add targets")

        steps.extend(
            [
                f"Test the tool: make {tool_name} ARGS='--help'",
                f"Run directly: cd ~/.amplifier/generated_tools/{tool_name} && python cli.py --help",
                f"Run tests: cd ~/.amplifier/generated_tools/{tool_name} && pytest",
                "Move to project if satisfied: cp -r ~/.amplifier/generated_tools/{tool_name} amplifier/tools/",
            ]
        )

        return steps

    def _generate_makefile_target(self, tool_name: str) -> str:
        """Generate Makefile target entry."""
        # Generate the target that works from the main project directory
        # Tools are in ~/.amplifier/generated_tools/{tool-name}/
        tool_path = f"~/.amplifier/generated_tools/{tool_name}"

        return f"""
# Generated tool: {tool_name}
{tool_name}: ## Run the {tool_name.replace("_", " ").replace("-", " ").title()} tool
\t@cd {tool_path} && python cli.py $(ARGS)
"""
