"""
Repository processor module using repomix.

Handles repository acquisition and preparation using npx repomix@latest.
"""

import asyncio
import re
import subprocess
import tempfile
from pathlib import Path

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class RepoProcessor:
    """Process repositories into analyzable format using repomix."""

    def __init__(self):
        """Initialize repository processor."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="repo_analyzer_"))
        logger.debug(f"Created temp directory: {self.temp_dir}")

    def _validate_pattern(self, pattern: str) -> str:
        """Validate and sanitize a file pattern.

        Args:
            pattern: File pattern to validate

        Returns:
            Sanitized pattern

        Raises:
            ValueError: If pattern contains dangerous characters
        """
        # Only allow safe glob patterns
        # Allow: alphanumeric, /, *, ?, [, ], {, }, -, _, ., comma
        safe_pattern = re.compile(r"^[\w\-_./\*\?\[\]\{\},]+$")

        if not safe_pattern.match(pattern):
            raise ValueError(f"Invalid pattern contains unsafe characters: {pattern}")

        # Prevent directory traversal
        if ".." in pattern:
            raise ValueError(f"Pattern cannot contain directory traversal: {pattern}")

        # Prevent absolute paths
        if pattern.startswith("/"):
            raise ValueError(f"Pattern cannot be absolute path: {pattern}")

        return pattern

    async def process_repository(
        self,
        repo_path: Path,
        output_name: str,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> Path:
        """Process repository using repomix.

        Args:
            repo_path: Path to repository to analyze
            output_name: Name for output file (without extension)
            include_patterns: Optional glob patterns to include
            exclude_patterns: Optional glob patterns to exclude

        Returns:
            Path to the generated repomix output file
        """
        output_file = self.temp_dir / f"{output_name}.xml"

        # Build repomix command
        cmd = ["npx", "repomix@latest", "--output", str(output_file), "--style", "xml"]

        # Add include patterns (with validation)
        if include_patterns:
            for pattern in include_patterns:
                validated_pattern = self._validate_pattern(pattern)
                cmd.extend(["--include", validated_pattern])

        # Add exclude patterns (with validation)
        if exclude_patterns:
            for pattern in exclude_patterns:
                validated_pattern = self._validate_pattern(pattern)
                cmd.extend(["--ignore", validated_pattern])

        # Add repository path
        cmd.append(str(repo_path))

        logger.info(f"Processing repository: {repo_path.name}")
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            # Run repomix in background thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: subprocess.run(cmd, capture_output=True, text=True, check=True)
            )

            if result.stdout:
                logger.debug(f"Repomix output: {result.stdout}")

            if output_file.exists():
                logger.info(f"✅ Repository processed: {output_file.name} ({output_file.stat().st_size:,} bytes)")
                return output_file
            raise FileNotFoundError(f"Repomix did not create output file: {output_file}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Repomix failed: {e}")
            if e.stderr:
                logger.error(f"Error output: {e.stderr}")
            raise RuntimeError(f"Failed to process repository: {e}")
        except Exception as e:
            logger.error(f"Repository processing failed: {e}")
            raise

    async def process_both_repos(
        self,
        source_path: Path,
        target_path: Path,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> tuple[Path, Path]:
        """Process both source and target repositories.

        Args:
            source_path: Path to source repository
            target_path: Path to target repository
            include_patterns: Optional glob patterns to include
            exclude_patterns: Optional glob patterns to exclude

        Returns:
            Tuple of (source_file, target_file) paths
        """
        logger.info("Processing both repositories...")

        # Process both repos in parallel
        source_task = self.process_repository(source_path, "source_repo", include_patterns, exclude_patterns)
        target_task = self.process_repository(target_path, "target_repo", include_patterns, exclude_patterns)

        source_file, target_file = await asyncio.gather(source_task, target_task)

        logger.info("✅ Both repositories processed successfully")
        return source_file, target_file

    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil

            shutil.rmtree(self.temp_dir)
            logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Could not clean up temp directory: {e}")
