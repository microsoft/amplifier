"""Core CLI module for amplifier."""

import click

from amplifier.cli.commands import heal


@click.group()
def cli():
    """Amplifier CLI - AI-powered code improvement tools."""
    pass


# Register commands
cli.add_command(heal.heal)
