"""Progress bar module for beautiful terminal progress tracking.

This module provides various progress tracking utilities using Rich,
designed as self-contained "bricks" that integrate with OutputManager.

Contract:
    Inputs: Task descriptions, total counts, current progress values
    Outputs: Visual progress indicators in terminal
    Side Effects: Terminal output, automatic cleanup on context exit
    Dependencies: Rich library, OutputManager from core.output
"""

from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rich.progress import BarColumn
from rich.progress import DownloadColumn
from rich.progress import MofNCompleteColumn
from rich.progress import Progress
from rich.progress import ProgressColumn
from rich.progress import SpinnerColumn
from rich.progress import TaskID
from rich.progress import TextColumn
from rich.progress import TimeElapsedColumn
from rich.progress import TimeRemainingColumn
from rich.progress import TransferSpeedColumn

from amplifier.cli.core.output import get_output_manager


class ProgressTracker:
    """Main progress tracking interface for the CLI.

    Provides context managers for different types of progress indicators,
    all integrated with the OutputManager for consistent styling.
    """

    def __init__(self, quiet: bool = False):
        """Initialize the progress tracker.

        Args:
            quiet: If True, suppress all progress output
        """
        self.quiet = quiet
        self.output = get_output_manager(quiet=quiet)

    @contextmanager
    def progress_bar(
        self,
        description: str = "Processing",
        total: int | None = None,
        auto_refresh: bool = True,
    ) -> Iterator[Progress]:
        """Context manager for a standard progress bar.

        Args:
            description: Description of the task
            total: Total number of steps (None for indeterminate)
            auto_refresh: Whether to auto-refresh the display

        Yields:
            Progress object with a single task added

        Example:
            >>> tracker = ProgressTracker()
            >>> with tracker.progress_bar("Processing files", total=100) as progress:
            ...     task = progress.tasks[0].id
            ...     for i in range(100):
            ...         # Do work
            ...         progress.update(task, advance=1)
        """
        if self.quiet:
            # Create minimal progress object for quiet mode
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                console=self.output.console,
                transient=True,
                auto_refresh=False,  # No output in quiet mode
            )
        else:
            columns: list[ProgressColumn] = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ]

            if total is not None:
                # Add bar and percentage for determinate progress
                columns.extend(
                    [
                        BarColumn(),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                        TextColumn("•"),
                        MofNCompleteColumn(),
                        TextColumn("•"),
                        TimeRemainingColumn(),
                    ]
                )
            else:
                # Just elapsed time for indeterminate progress
                columns.extend(
                    [
                        TimeElapsedColumn(),
                    ]
                )

            progress = Progress(
                *columns,
                console=self.output.console,
                transient=True,
                auto_refresh=auto_refresh,
            )

        with progress:
            # Add the main task
            progress.add_task(description, total=total)
            yield progress

    @contextmanager
    def download_progress(
        self,
        description: str = "Downloading",
        total_size: int | None = None,
    ) -> Iterator[tuple[Progress, TaskID]]:
        """Context manager for download progress with transfer speed.

        Args:
            description: Description of the download
            total_size: Total size in bytes (None for unknown size)

        Yields:
            Tuple of (Progress object, TaskID) for updating

        Example:
            >>> tracker = ProgressTracker()
            >>> with tracker.download_progress("data.zip", total_size=1024*1024) as (progress, task_id):
            ...     for chunk in download_chunks():
            ...         # Process chunk
            ...         progress.update(task_id, advance=len(chunk))
        """
        if self.quiet:
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                console=self.output.console,
                transient=True,
                auto_refresh=False,
            )
        else:
            columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TextColumn("•"),
                TransferSpeedColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
            ]

            if total_size is not None:
                columns.insert(-1, TimeRemainingColumn())

            progress = Progress(
                *columns,
                console=self.output.console,
                transient=True,
            )

        with progress:
            task_id = progress.add_task(description, total=total_size)
            yield progress, task_id

    @contextmanager
    def processing_progress(
        self,
        items: list[Any],
        description: str = "Processing items",
    ) -> Iterator[Callable[[Any], None]]:
        """Context manager for processing a list of items.

        Args:
            items: List of items to process
            description: Description of the processing task

        Yields:
            Update function to call after processing each item

        Example:
            >>> tracker = ProgressTracker()
            >>> files = ["file1.txt", "file2.txt", "file3.txt"]
            >>> with tracker.processing_progress(files, "Processing files") as update:
            ...     for file in files:
            ...         # Process file
            ...         process_file(file)
            ...         update(file)
        """
        total = len(items)

        if self.quiet:
            # No-op update function for quiet mode
            def update_func(item: Any) -> None:
                pass  # Intentionally empty - suppresses output in quiet mode

            yield update_func
        else:
            with self.progress_bar(description, total=total) as progress:
                task_id = progress.tasks[0].id
                current_index = 0

                def update_func(item: Any) -> None:
                    nonlocal current_index
                    # Update description with current item
                    item_str = str(item)
                    if len(item_str) > 50:
                        item_str = item_str[:47] + "..."
                    progress.update(task_id, description=f"{description}: {item_str}", advance=1)
                    current_index += 1

                yield update_func

    @contextmanager
    def spinner(
        self,
        message: str = "Working",
        style: str = "dots",
    ) -> Iterator[None]:
        """Context manager for an indeterminate spinner.

        Args:
            message: Message to display with spinner
            style: Spinner style (dots, line, arc, etc.)

        Example:
            >>> tracker = ProgressTracker()
            >>> with tracker.spinner("Connecting to server"):
            ...     # Do work that takes unknown time
            ...     connect_to_server()
        """
        if self.quiet:
            yield
        else:
            with self.output.spinner(message):
                yield

    def multi_progress(
        self,
        tasks: list[tuple[str, int | None]],
    ) -> Progress:
        """Create a multi-task progress display.

        Args:
            tasks: List of (description, total) tuples for each task

        Returns:
            Progress object with all tasks added

        Example:
            >>> tracker = ProgressTracker()
            >>> tasks = [("Download", 1000), ("Process", 100), ("Upload", None)]
            >>> progress = tracker.multi_progress(tasks)
            >>> with progress:
            ...     # Update individual tasks by ID
            ...     progress.update(task_ids[0], advance=100)
        """
        if self.quiet:
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                console=self.output.console,
                transient=True,
                auto_refresh=False,
            )
        else:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.output.console,
                transient=True,
            )

        # Add all tasks
        for description, total in tasks:
            progress.add_task(description, total=total)

        return progress


# Convenience functions for quick access
_tracker: ProgressTracker | None = None


def get_progress_tracker(quiet: bool = False) -> ProgressTracker:
    """Get or create the global progress tracker.

    Args:
        quiet: If True, suppress all progress output

    Returns:
        The global ProgressTracker instance
    """
    global _tracker
    if _tracker is None or _tracker.quiet != quiet:
        _tracker = ProgressTracker(quiet=quiet)
    return _tracker


@contextmanager
def progress_bar(
    description: str = "Processing",
    total: int | None = None,
    quiet: bool = False,
) -> Iterator[Progress]:
    """Quick access to progress bar context manager.

    Args:
        description: Description of the task
        total: Total number of steps
        quiet: If True, suppress output

    Yields:
        Progress object with task added
    """
    tracker = get_progress_tracker(quiet=quiet)
    with tracker.progress_bar(description, total) as progress:
        yield progress


@contextmanager
def download_progress(
    description: str = "Downloading",
    total_size: int | None = None,
    quiet: bool = False,
) -> Iterator[tuple[Progress, TaskID]]:
    """Quick access to download progress context manager.

    Args:
        description: Description of the download
        total_size: Total size in bytes
        quiet: If True, suppress output

    Yields:
        Tuple of (Progress object, TaskID)
    """
    tracker = get_progress_tracker(quiet=quiet)
    with tracker.download_progress(description, total_size) as result:
        yield result


@contextmanager
def processing_progress(
    items: list[Any],
    description: str = "Processing items",
    quiet: bool = False,
) -> Iterator[Callable[[Any], None]]:
    """Quick access to processing progress context manager.

    Args:
        items: List of items to process
        description: Description of the task
        quiet: If True, suppress output

    Yields:
        Update function to call after each item
    """
    tracker = get_progress_tracker(quiet=quiet)
    with tracker.processing_progress(items, description) as update:
        yield update


@contextmanager
def spinner(
    message: str = "Working",
    quiet: bool = False,
) -> Iterator[None]:
    """Quick access to spinner context manager.

    Args:
        message: Message to display
        quiet: If True, suppress output

    Example:
        >>> with spinner("Loading data"):
        ...     load_large_dataset()
    """
    tracker = get_progress_tracker(quiet=quiet)
    with tracker.spinner(message):
        yield
