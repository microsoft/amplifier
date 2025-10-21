"""CLI utility functions for user interaction."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def print_section_header(title: str) -> None:
    """Print styled section header.

    Args:
        title: Section title
    """
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
    console.print()


def print_progress(message: str) -> None:
    """Print progress message.

    Args:
        message: Progress message
    """
    console.print(f"[dim]→ {message}[/dim]")


def get_user_input(prompt: str) -> str:
    """Get user input with styled prompt.

    Args:
        prompt: Prompt message

    Returns:
        User input string
    """
    return Prompt.ask(f"[yellow]{prompt}[/yellow]")


def print_error(message: str) -> None:
    """Print error message.

    Args:
        message: Error message
    """
    console.print(f"[bold red]✗ Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print success message.

    Args:
        message: Success message
    """
    console.print(f"[bold green]✓ {message}[/bold green]")


def print_info(message: str) -> None:
    """Print informational message.

    Args:
        message: Info message
    """
    console.print(f"[blue]ℹ {message}[/blue]")
