"""Main CLI entry point for amplifier commands."""

import click

from amplifier.cli.commands.beast import beast
from amplifier.cli.commands.heal import heal
from amplifier.cli.commands.knowledge import knowledge
from amplifier.cli.commands.principles import principles


@click.group()
def cli():
    """Amplifier CLI - AI-powered development tools."""
    pass


# Register commands
cli.add_command(beast)
cli.add_command(heal)
cli.add_command(principles)
cli.add_command(knowledge)

# Register Claude real monitoring commands
try:
    from amplifier.claude.real_cli import real_claude_group

    cli.add_command(real_claude_group)
except ImportError:
    pass  # Claude monitoring not available


if __name__ == "__main__":
    cli()
