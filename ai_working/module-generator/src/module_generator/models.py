"""Data models for the module generator."""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


@dataclass
class GeneratorContext:
    """Context for module generation containing all necessary information.

    This provides the unified interface for all generators to receive
    their input data and configuration.
    """

    name: str
    """The module name."""

    contract: dict[str, Any]
    """The full contract/specification for the module."""

    output_dir: Path | str
    """The directory to output generated files."""

    spec: dict[str, Any] | None = None
    """The implementation specification for the module."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for generation."""

    config: dict[str, Any] = field(default_factory=dict)
    """Generator-specific configuration."""

    def get_output_path(self, filename: str) -> Path:
        """Get the full path for an output file.

        Args:
            filename: The filename to generate

        Returns:
            Path: The full path to the output file
        """
        return Path(self.output_dir) / filename
