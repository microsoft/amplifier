"""
Completions command for Amplifier CLI v3.

This command generates shell completion scripts for bash, zsh, and fish shells.

Contract:
    - Command: completions [bash|zsh|fish]
    - Generates completion scripts for specified shell
    - Provides installation instructions
"""

import click

from amplifier.cli.core.completions import get_shell_completion_script
from amplifier.cli.core.completions import install_completion_instructions
from amplifier.cli.core.decorators import handle_errors
from amplifier.cli.core.decorators import log_command
from amplifier.cli.core.output import get_output_manager


@click.command()
@click.argument(
    "shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    required=False,
)
@click.option(
    "--install-instructions",
    is_flag=True,
    help="Show installation instructions instead of the script",
)
@handle_errors()
@log_command("completions")
@click.pass_context
def cmd(ctx: click.Context, shell: str | None, install_instructions: bool) -> None:
    """Generate shell completion scripts.

    This command generates shell completion scripts that enable tab completion
    for amplifier commands, options, and arguments in your shell.

    If no shell is specified, shows installation instructions for all shells.

    \b
    Examples:
        amplifier completions bash > ~/.amplifier_completion.bash
        amplifier completions zsh > ~/.zsh/completions/_amplifier
        amplifier completions fish > ~/.config/fish/completions/amplifier.fish
        amplifier completions --install-instructions
    """
    output = ctx.obj.get("output", get_output_manager())

    if not shell:
        # Show instructions for all shells
        output.info("📋 Shell Completion Support")
        output.info("")
        output.info("Amplifier supports tab completion for bash, zsh, and fish shells.")
        output.info("")

        for shell_type in ["bash", "zsh", "fish"]:
            output.success(f"[{shell_type.upper()}]")
            instructions = install_completion_instructions(shell_type)
            for line in instructions.split("\n"):
                if line.strip():
                    output.info(line)
            output.info("")

        output.info("For more information, run: amplifier completions <shell> --install-instructions")
        return

    if install_instructions:
        # Show installation instructions for specific shell
        instructions = install_completion_instructions(shell)
        output.info(instructions)
    else:
        # Generate and output the completion script
        script = get_shell_completion_script(shell)
        click.echo(script, nl=False)  # No newline at end for cleaner output
