#!/usr/bin/env python3
"""CLI command for direct Aider interaction."""

import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("--message", "-m", help="Message/prompt for Aider")
@click.option("--model", default="claude-3-5-sonnet-20241022", help="Model to use")
@click.option(
    "--mode",
    type=click.Choice(["chat", "edit", "architect"]),
    default="edit",
    help="Aider mode: chat (discuss), edit (modify), architect (design)",
)
@click.option("--yes", "-y", is_flag=True, help="Auto-yes to prompts")
@click.option("--no-git", is_flag=True, help="Disable git integration")
@click.option("--zen", is_flag=True, help="Apply zen philosophy (ruthless simplification)")
def aider(files: tuple, message: str | None, model: str, mode: str, yes: bool, no_git: bool, zen: bool):
    """Launch Aider AI coding assistant with Amplifier presets.

    Examples:
        # Refactor a module with zen philosophy
        amplifier aider mymodule.py --zen -m "Simplify this module"

        # Chat about architecture
        amplifier aider --mode chat -m "How should I structure this feature?"

        # Edit multiple files
        amplifier aider file1.py file2.py -m "Add error handling"
    """
    # Check for .aider-venv
    venv_path = Path(".aider-venv/bin/aider")
    if not venv_path.exists():
        click.echo(
            "❌ Aider not found. Please run: python -m venv .aider-venv && .aider-venv/bin/pip install aider-chat"
        )
        sys.exit(1)

    # Build command
    cmd = [str(venv_path)]

    # Add model
    cmd.extend(["--model", model])

    # Add mode-specific options
    if mode == "architect":
        cmd.append("--architect")
    elif mode == "chat":
        cmd.append("--chat-mode")

    # Add flags
    if yes:
        cmd.append("--yes")
    if no_git:
        cmd.append("--no-git")
    else:
        cmd.append("--no-auto-commits")  # Safer default

    # Add message with zen philosophy if requested
    if message:
        if zen:
            zen_prompt = (
                """APPLY ZEN PHILOSOPHY:
- Ruthlessly simplify: remove all unnecessary complexity
- Every line must earn its place
- Prefer 10 obvious lines over 5 clever ones
- Delete first, refactor second, add third
- Make it work, make it right, make it gone

"""
                + message
            )
            cmd.extend(["--message", zen_prompt])
        else:
            cmd.extend(["--message", message])

    # Add files
    for file_path in files:
        cmd.append(str(file_path))

    # If no files and no message, launch interactive mode
    if not files and not message:
        click.echo("🤖 Launching Aider in interactive mode...")
        click.echo(f"   Model: {model}")
        if zen:
            click.echo("   Philosophy: Zen (ruthless simplification)")
        click.echo("")

    # Run Aider
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        click.echo("\n\n👋 Aider session ended.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error running Aider: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    aider()
