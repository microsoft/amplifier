"""Simple decorators for CLI commands."""

import functools
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import TypeVar

import click

from .errors import AmplifierCLIError
from .errors import NotInitializedError
from .output import get_output_manager

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(show_traceback: bool = False) -> Callable[[F], F]:
    """Catch and display errors nicely.

    Args:
        show_traceback: If True, always show traceback (ignored, kept for compatibility)

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        @click.pass_context
        def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
            """Wrapper that handles errors gracefully."""
            output = get_output_manager(
                quiet=ctx.obj.get("quiet", False) if ctx.obj else False,
                debug=ctx.obj.get("debug", False) if ctx.obj else False,
            )

            try:
                return func(*args, **kwargs)
            except (AmplifierCLIError, click.ClickException) as e:
                output.error(str(e))
                sys.exit(1)
            except KeyboardInterrupt:
                output.warning("Operation cancelled by user")
                sys.exit(1)
            except Exception as e:
                output.error(f"Unexpected error: {e}")
                if output.debug:
                    import traceback

                    output.debug(traceback.format_exc())
                sys.exit(1)

        return wrapper  # type: ignore

    return decorator


def log_command(command_name: str) -> Callable[[F], F]:
    """Log command execution for debugging.

    Args:
        command_name: Name of the command being executed

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        @click.pass_context
        def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
            """Wrapper that logs command execution."""
            output = get_output_manager(
                quiet=ctx.obj.get("quiet", False) if ctx.obj else False,
                debug=ctx.obj.get("debug", False) if ctx.obj else False,
            )

            output.debug(f"Executing command: {command_name}")
            result = func(*args, **kwargs)
            output.debug(f"Command {command_name} completed")
            return result

        return wrapper  # type: ignore

    return decorator


def requires_init(func: F) -> F:
    """Ensure project is initialized before running command.

    Args:
        func: The function to wrap

    Returns:
        Wrapped function that validates initialization
    """

    @functools.wraps(func)
    @click.pass_context
    def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        """Wrapper that checks for project initialization."""
        if not Path(".claude").exists():
            raise NotInitializedError()
        return func(*args, **kwargs)

    return wrapper  # type: ignore
