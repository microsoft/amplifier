"""Main CLI entry point for amplifier principles and knowledge commands."""

import click

from amplifier.cli.commands.knowledge import knowledge
from amplifier.cli.commands.principles import principles


@click.group()
def cli():
    """Amplifier CLI - AI-First Principles and Knowledge Management."""
    pass


# Register commands
cli.add_command(principles)
cli.add_command(knowledge)


if __name__ == "__main__":
    cli()
