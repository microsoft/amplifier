"""Simple logger wrapper for amplifier utilities."""

from amplifier.ccsdk_toolkit.logger import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import create_logger as create_toolkit_logger


def get_logger(name: str) -> ToolkitLogger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        ToolkitLogger instance
    """
    return create_toolkit_logger(name=name)
