"""
Main CLI implementation for Amplifier using Click.

Provides commands for initializing projects, running modes, listing modules,
and entering interactive sessions.
"""

import asyncio
import sys

import click
from amplifier_core import Kernel as AmplifierKernel
from rich.console import Console
from rich.table import Table

from .config import ConfigurationError
from .config import init_config_dirs
from .config import list_available_modes
from .config import load_mode_manifest
from .config import load_user_config
from .config import save_mode_manifest

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", is_flag=True, help="Show version and exit")
def cli(ctx: click.Context, version: bool) -> None:
    """
    Amplifier - Modular AI-powered development assistant.

    Run without arguments to enter interactive mode, or use subcommands
    for specific actions.
    """
    if version:
        from . import __version__

        click.echo(f"Amplifier CLI v{__version__}")
        ctx.exit()

    if ctx.invoked_subcommand is None:
        # No subcommand, enter interactive mode
        ctx.invoke(interactive)


@cli.command()
@click.option("--mode", "-m", help="Mode to initialize (default: 'default')")
@click.option("--name", "-n", help="Name for the new mode (if creating custom)")
@click.option("--modules", multiple=True, help="Modules to include in custom mode")
@click.option("--from-mode", help="Base mode to extend from")
def init(mode: str | None, name: str | None, modules: tuple[str, ...], from_mode: str | None) -> None:
    """
    Initialize a project or mode configuration.

    Examples:
        amplifier init --mode development
        amplifier init --name mymode --modules amplifier_mod_llm_openai amplifier_mod_tool_ultra_think
        amplifier init --name extended --from-mode development --modules amplifier_mod_tool_blog_generator
    """
    try:
        # Initialize config directories if they don't exist
        init_config_dirs()

        if name:
            # Creating a new custom mode
            console.print(f"[cyan]Creating new mode: {name}[/cyan]")

            manifest = {"name": name, "description": f"Custom mode: {name}", "modules": []}

            # If extending from another mode, load its modules first
            if from_mode:
                base_manifest = load_mode_manifest(from_mode)
                manifest["modules"] = base_manifest.get("modules", [])
                console.print(f"[dim]Extending from mode: {from_mode}[/dim]")

            # Add specified modules (handle comma-separated)
            if modules:
                for module_spec in modules:
                    # Split comma-separated modules
                    module_list = [m.strip() for m in module_spec.split(",")]
                    for module in module_list:
                        if module and module not in manifest["modules"]:
                            manifest["modules"].append(module)

            # Save the new mode
            save_mode_manifest(name, manifest)
            console.print(f"[green]✓[/green] Mode '{name}' created successfully")
            console.print(f"[dim]Modules: {', '.join(manifest['modules']) or 'none'}[/dim]")
        else:
            # Initializing with existing mode
            mode_name = mode or "default"
            try:
                manifest = load_mode_manifest(mode_name)
                console.print(f"[green]✓[/green] Initialized with mode: {mode_name}")
                if manifest.get("description"):
                    console.print(f"[dim]{manifest['description']}[/dim]")
            except ConfigurationError as e:
                console.print(f"[red]Error:[/red] {e}")
                sys.exit(1)

    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("mode_or_command")
@click.argument("args", nargs=-1)
@click.option("--modules", "-m", multiple=True, help="Additional modules to load")
@click.option("--async", "async_mode", is_flag=True, help="Run in async mode")
def run(mode_or_command: str, args: tuple[str, ...], modules: tuple[str, ...], async_mode: bool) -> None:
    """
    Execute with a specific mode configuration or run a command/tool.

    Examples:
        amplifier run development
        amplifier run blog_generator "AI in Education"
        amplifier run ultra_think "quantum computing" --modules amplifier_mod_llm_claude
    """

    async def _run() -> None:
        kernel = AmplifierKernel()
        config = load_user_config()

        try:
            # Check if it's a mode name
            try:
                manifest = load_mode_manifest(mode_or_command)
                mode_modules = manifest.get("modules", [])
                console.print(f"[cyan]Loading mode: {mode_or_command}[/cyan]")
            except ConfigurationError:
                # Not a mode, might be a tool/command name
                mode_modules = []

            # Load modules from mode (handle comma-separated for backwards compatibility)
            if mode_modules:
                expanded_modules = []
                for module_spec in mode_modules:
                    # Split if comma-separated (for backwards compatibility)
                    if "," in module_spec:
                        expanded_modules.extend([m.strip() for m in module_spec.split(",") if m.strip()])
                    else:
                        expanded_modules.append(module_spec)
                await kernel.load_modules_by_name(expanded_modules)

            # Load additional modules specified on command line
            if modules:
                expanded_modules = []
                for module_spec in modules:
                    # Split comma-separated modules
                    if "," in module_spec:
                        expanded_modules.extend([m.strip() for m in module_spec.split(",") if m.strip()])
                    else:
                        expanded_modules.append(module_spec)
                await kernel.load_modules_by_name(expanded_modules)

            # Check if mode_or_command is a tool, or if first arg is a tool
            tool_to_run = None
            tool_args = args

            if mode_or_command in kernel.tools:
                # Direct tool invocation: amplifier run tool_name args
                tool_to_run = mode_or_command
                tool_args = args
            elif args and args[0] in kernel.tools:
                # Mode + tool invocation: amplifier run mode tool_name args
                tool_to_run = args[0]
                tool_args = args[1:]

            if tool_to_run:
                console.print(f"[cyan]Running tool: {tool_to_run}[/cyan]")
                # Convert args to input dict based on tool
                if tool_to_run == "ultra_think":
                    input_dict = {"topic": tool_args[0] if tool_args else ""}
                elif tool_to_run == "blog_generator":
                    input_dict = {"topic_or_outline": tool_args[0] if tool_args else ""}
                else:
                    # Generic fallback
                    if len(tool_args) == 1:
                        input_dict = {"input": tool_args[0]}
                    elif len(tool_args) > 1:
                        input_dict = {"inputs": tool_args}
                    else:
                        input_dict = {}

                result = await kernel.tools[tool_to_run].run(input=input_dict)
                console.print(result)
            elif not mode_modules:
                console.print(f"[yellow]Warning:[/yellow] '{mode_or_command}' is not a known mode or tool")
                console.print(
                    "[dim]Use 'amplifier list-modes' or 'amplifier list-modules' to see available options[/dim]"
                )
            else:
                # Mode loaded successfully, show what's available
                console.print(f"[green]✓[/green] Mode loaded successfully with {len(kernel.tools)} tools")
                if kernel.tools:
                    console.print("[dim]Available tools:[/dim]")
                    for tool_name in kernel.tools:
                        console.print(f"  • {tool_name}")
                    console.print("\n[dim]To use a tool, run: amplifier run {tool_name} \"your input\"[/dim]")
                if kernel.model_providers:
                    console.print("[dim]Available model providers:[/dim]")
                    for provider_name in kernel.model_providers:
                        console.print(f"  • {provider_name}")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    # Run the async function
    if async_mode:
        # For async mode, we might want to keep the event loop running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()
    else:
        asyncio.run(_run())


@cli.command("list-modules")
@click.option("--loaded", is_flag=True, help="Show only currently loaded modules")
def list_modules(loaded: bool) -> None:
    """Show available modules that can be loaded."""

    async def _list() -> None:
        kernel = AmplifierKernel()

        if loaded:
            # Show loaded modules
            console.print("[cyan]Currently loaded modules:[/cyan]")
            # This would need to be implemented in the kernel
            console.print("[dim]No modules loaded (feature not yet implemented)[/dim]")
        else:
            # Show available modules
            table = Table(title="Available Modules")
            table.add_column("Module Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Description", style="dim")

            # These would be discovered dynamically in a real implementation
            modules_info = [
                ("amplifier_mod_llm_openai", "LLM Provider", "OpenAI GPT model provider"),
                ("amplifier_mod_llm_claude", "LLM Provider", "Anthropic Claude model provider"),
                ("amplifier_mod_tool_ultra_think", "Tool", "Multi-step reasoning workflow"),
                ("amplifier_mod_tool_blog_generator", "Tool", "Blog post generation workflow"),
                ("amplifier_mod_philosophy", "Context", "Philosophy document injection"),
                ("amplifier_mod_agent_registry", "Agent", "Agent management and registry"),
            ]

            for name, module_type, description in modules_info:
                table.add_row(name, module_type, description)

            console.print(table)

    asyncio.run(_list())


@cli.command("list-modes")
@click.option("--verbose", "-v", is_flag=True, help="Show mode details including modules")
def list_modes(verbose: bool) -> None:
    """Show available mode configurations."""
    try:
        modes = list_available_modes()

        if not verbose:
            table = Table(title="Available Modes")
            table.add_column("Mode Name", style="cyan")
            table.add_column("Description", style="dim")

            for mode_name in modes:
                try:
                    manifest = load_mode_manifest(mode_name)
                    description = manifest.get("description", "No description")
                    table.add_row(mode_name, description)
                except ConfigurationError:
                    table.add_row(mode_name, "[red]Error loading manifest[/red]")

            console.print(table)
        else:
            for mode_name in modes:
                try:
                    manifest = load_mode_manifest(mode_name)
                    console.print(f"\n[cyan]{mode_name}[/cyan]")
                    console.print(f"  Description: {manifest.get('description', 'No description')}")
                    modules = manifest.get("modules", [])
                    if modules:
                        console.print("  Modules:")
                        for module in modules:
                            console.print(f"    - {module}")
                    else:
                        console.print("  [dim]No modules configured[/dim]")
                except ConfigurationError as e:
                    console.print(f"\n[cyan]{mode_name}[/cyan]")
                    console.print(f"  [red]Error loading manifest: {e}[/red]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--mode", "-m", default="default", help="Mode to use for the session")
def interactive(mode: str) -> None:
    """
    Enter interactive shell mode.

    This starts an interactive session where you can enter commands and
    queries that will be processed by the loaded agents and tools.
    """

    async def _interactive() -> None:
        kernel = AmplifierKernel()

        # Load the specified mode
        try:
            manifest = load_mode_manifest(mode)
            console.print(f"[cyan]Starting interactive mode: {mode}[/cyan]")
            if manifest.get("description"):
                console.print(f"[dim]{manifest['description']}[/dim]")

            # Load modules from mode
            mode_modules = manifest.get("modules", [])
            if mode_modules:
                console.print(f"[dim]Loading modules: {', '.join(mode_modules)}[/dim]")
                await kernel.load_modules_by_name(mode_modules)

        except ConfigurationError as e:
            console.print(f"[yellow]Warning:[/yellow] Could not load mode '{mode}': {e}")
            console.print("[dim]Continuing with default configuration[/dim]")

        console.print("\n[green]Amplifier interactive mode ready![/green]")
        console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")

        # Interactive loop
        while True:
            try:
                # Get user input
                user_input = console.input("[bold cyan]amp>[/bold cyan] ")

                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("[dim]Goodbye![/dim]")
                    break

                if user_input.lower() in ["help", "?"]:
                    console.print("\n[cyan]Available commands:[/cyan]")
                    console.print("  help, ?       - Show this help message")
                    console.print("  list-tools    - List available tools")
                    console.print("  list-agents   - List available agents")
                    console.print("  !<tool> <args> - Run a specific tool")
                    console.print("  exit, quit, q - Exit interactive mode")
                    console.print("\n[dim]Or just type a query to process it[/dim]\n")
                    continue

                if user_input == "list-tools":
                    if kernel.tools:
                        console.print("\n[cyan]Available tools:[/cyan]")
                        for tool_name in kernel.tools:
                            console.print(f"  - {tool_name}")
                    else:
                        console.print("[dim]No tools loaded[/dim]")
                    console.print()
                    continue

                if user_input == "list-agents":
                    if hasattr(kernel, "agent_registry") and kernel.agent_registry:
                        console.print("\n[cyan]Available agents:[/cyan]")
                        # This would list agents from the registry
                        console.print("[dim]Agent listing not yet implemented[/dim]")
                    else:
                        console.print("[dim]No agent registry loaded[/dim]")
                    console.print()
                    continue

                # Handle tool invocation with ! prefix
                if user_input.startswith("!"):
                    parts = user_input[1:].split(maxsplit=1)
                    if parts:
                        tool_name = parts[0]
                        tool_args = parts[1] if len(parts) > 1 else ""

                        if tool_name in kernel.tools:
                            console.print(f"[dim]Running tool: {tool_name}[/dim]")
                            # Convert string to appropriate dict based on tool
                            if tool_name == "ultra_think":
                                input_dict = {"topic": tool_args}
                            elif tool_name == "blog_generator":
                                input_dict = {"topic_or_outline": tool_args}
                            else:
                                # Generic fallback
                                input_dict = {"input": tool_args}
                            result = await kernel.tools[tool_name].run(input=input_dict)
                            console.print(result)
                        else:
                            console.print(f"[red]Unknown tool: {tool_name}[/red]")
                    console.print()
                    continue

                # Default: process as a general query
                # In a full implementation, this would route to an agent or tool
                console.print(f"[dim]Processing: {user_input}[/dim]")
                console.print("[yellow]Query processing not yet implemented[/yellow]")
                console.print()

            except KeyboardInterrupt:
                console.print("\n[dim]Use 'exit' to quit[/dim]")
                continue
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
                continue

    asyncio.run(_interactive())


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
