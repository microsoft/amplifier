"""Rich output manager for beautiful CLI output."""

from collections.abc import Iterator
from contextlib import contextmanager

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.progress import TimeRemainingColumn
from rich.syntax import Syntax
from rich.table import Table


class OutputManager:
    """Handle all rich terminal output with consistent styling."""

    def __init__(self, quiet: bool = False, debug: bool = False):
        """Initialize the output manager.

        Args:
            quiet: If True, suppress non-essential output
            debug: If True, show debug information
        """
        self.console = Console()
        self.quiet = quiet
        self.debug_mode = debug
        self._error_count = 0
        self._warning_count = 0

    def success(self, message: str, detail: str | None = None) -> None:
        """Display a success message with green checkmark.

        Args:
            message: The success message to display
            detail: Optional additional detail to show
        """
        if not self.quiet:
            self.console.print(f"[green]✓[/green] {message}")
            if detail and self.debug_mode:
                self.console.print(f"  [dim]{detail}[/dim]")

    def error(self, message: str, detail: str | None = None) -> None:
        """Display an error message with red X.

        Args:
            message: The error message to display
            detail: Optional additional detail to show
        """
        self._error_count += 1
        self.console.print(f"[red]✗[/red] {message}")
        if detail:
            self.console.print(f"  [dim red]{detail}[/dim red]")

    def warning(self, message: str, detail: str | None = None) -> None:
        """Display a warning message with yellow warning sign.

        Args:
            message: The warning message to display
            detail: Optional additional detail to show
        """
        self._warning_count += 1
        if not self.quiet:
            self.console.print(f"[yellow]⚠️[/yellow]  {message}")
            if detail:
                self.console.print(f"  [dim yellow]{detail}[/dim yellow]")

    def info(self, message: str, emoji: str = "ℹ️") -> None:
        """Display an info message.

        Args:
            message: The info message to display
            emoji: Optional emoji to display before the message
        """
        if not self.quiet:
            self.console.print(f"{emoji} {message}")

    def debug(self, message: str) -> None:
        """Display a debug message if debug mode is enabled.

        Args:
            message: The debug message to display
        """
        if self.debug_mode:
            self.console.print(f"[dim cyan]DEBUG:[/dim cyan] {message}")

    @contextmanager
    def progress_context(self, description: str = "Processing...") -> Iterator[Progress]:
        """Context manager for progress bars.

        Args:
            description: Description of the operation

        Yields:
            Progress object to track progress
        """
        if self.quiet:
            # Create a no-op progress object for quiet mode
            progress = Progress(console=self.console, transient=True)
            try:
                yield progress
            finally:
                # Clean up is handled by Progress object
                progress.stop()
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.console,
                transient=True,
            ) as progress:
                yield progress

    @contextmanager
    def spinner(self, message: str = "Working...") -> Iterator[None]:
        """Context manager for a simple spinner.

        Args:
            message: Message to display with the spinner
        """
        if not self.quiet:
            with self.console.status(message):
                yield
        else:
            yield

    def create_table(self, title: str | None = None) -> Table:
        """Create a styled table.

        Args:
            title: Optional title for the table

        Returns:
            Rich Table object
        """
        table = Table(
            title=title,
            box=box.ROUNDED,
            title_style="bold cyan",
            header_style="bold",
            show_lines=False,
            pad_edge=True,
            padding=(0, 1),
        )
        return table

    def panel(self, content: str, title: str | None = None, style: str = "cyan", width: int | None = None) -> None:
        """Display content in a styled panel.

        Args:
            content: Content to display in the panel
            title: Optional title for the panel
            style: Style for the panel border
            width: Optional width for the panel
        """
        if not self.quiet:
            panel = Panel.fit(content, title=title, border_style=style, width=width, padding=(1, 2))
            self.console.print(panel)

    def section_header(self, title: str) -> None:
        """Display a section header.

        Args:
            title: Title of the section
        """
        if not self.quiet:
            self.console.print()
            self.console.rule(f"[bold cyan]{title}[/bold cyan]")
            self.console.print()

    def code(self, code: str, language: str = "python", theme: str = "monokai") -> None:
        """Display syntax-highlighted code.

        Args:
            code: Code to display
            language: Programming language for syntax highlighting
            theme: Color theme for syntax highlighting
        """
        if not self.quiet:
            syntax = Syntax(code, language, theme=theme)
            self.console.print(syntax)

    def print_summary(self) -> None:
        """Print a summary of errors and warnings."""
        if self._error_count > 0 or self._warning_count > 0:
            self.console.print()
            if self._error_count > 0:
                self.console.print(f"[red]✗ {self._error_count} error{'s' if self._error_count != 1 else ''}[/red]")
            if self._warning_count > 0:
                self.console.print(
                    f"[yellow]⚠️  {self._warning_count} warning{'s' if self._warning_count != 1 else ''}[/yellow]"
                )

    def prompt(self, message: str, default: str | None = None) -> str:
        """Prompt the user for input.

        Args:
            message: Prompt message
            default: Default value if user presses enter

        Returns:
            User input or default value
        """
        prompt_text = f"[cyan]?[/cyan] {message}"
        if default:
            prompt_text += f" [dim]({default})[/dim]"
        prompt_text += ": "

        result = self.console.input(prompt_text)
        return result if result else (default or "")

    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask the user for confirmation.

        Args:
            message: Confirmation message
            default: Default response if user presses enter

        Returns:
            True if confirmed, False otherwise
        """
        default_text = "Y/n" if default else "y/N"
        response = self.prompt(f"{message} [{default_text}]", "y" if default else "n")
        return response.lower() in ["y", "yes"]

    def list_items(self, items: list[str], title: str | None = None) -> None:
        """Display a list of items.

        Args:
            items: List of items to display
            title: Optional title for the list
        """
        if not self.quiet and items:
            if title:
                self.console.print(f"[bold]{title}:[/bold]")
            for item in items:
                self.console.print(f"  • {item}")

    def clear(self) -> None:
        """Clear the console screen."""
        self.console.clear()


# Singleton instance for global access
_output_manager: OutputManager | None = None


def get_output_manager(quiet: bool = False, debug: bool = False) -> OutputManager:
    """Get or create the global output manager instance.

    Args:
        quiet: If True, suppress non-essential output
        debug: If True, show debug information

    Returns:
        The global OutputManager instance
    """
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager(quiet=quiet, debug=debug)
    else:
        # Update settings if needed
        _output_manager.quiet = quiet
        _output_manager.debug_mode = debug
    return _output_manager
