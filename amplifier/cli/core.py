"""Core CLI definitions for Amplifier."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import click

from amplifier.cli.commands import aider
from amplifier.cli.commands import heal


def _run_amplifier_launcher(extra_args: list[str]) -> None:
    """Delegate to the original amplifier launcher script."""

    script_path = Path(__file__).resolve().parents[2] / "amplifier-anywhere.sh"
    if not script_path.exists():
        raise click.ClickException("amplifier-anywhere.sh not found. Please reinstall Amplifier.")

    env = os.environ.copy()
    env.setdefault("ORIGINAL_PWD", os.getcwd())

    result = subprocess.call([str(script_path), *extra_args], env=env)
    raise SystemExit(result)


@click.group(
    invoke_without_command=True,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Amplifier CLI - AI-powered code improvement tools."""

    if ctx.invoked_subcommand is None:
        _run_amplifier_launcher(ctx.args)


cli.add_command(heal)
cli.add_command(aider)


__all__ = ["cli"]
