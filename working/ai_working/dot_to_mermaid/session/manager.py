"""
Session manager for tracking conversion progress.
"""

import logging
from pathlib import Path

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry

from ..models import ConversionResult
from ..models import SessionState

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversion session state for resume capability."""

    def __init__(self, session_file: Path | None = None):
        """Initialize session manager.

        Args:
            session_file: Path to session state file (default: dot_conversion_session.json)
        """
        self.session_file = session_file or Path("dot_conversion_session.json")
        self.state = self._load_state()

    def _load_state(self) -> SessionState:
        """Load existing session state or create new."""
        if self.session_file.exists():
            try:
                data = read_json_with_retry(self.session_file)
                logger.info(f"Resuming session: {len(data['processed_files'])} files already processed")
                return SessionState(
                    processed_files=data.get("processed_files", []),
                    results=[ConversionResult(**r) for r in data.get("results", [])],
                    failed_files=[(f[0], f[1]) for f in data.get("failed_files", [])],
                    total_files=data.get("total_files", 0),
                    current_file=data.get("current_file"),
                )
            except Exception as e:
                logger.warning(f"Could not load session state: {e}")

        return SessionState(processed_files=[], results=[], failed_files=[], total_files=0, current_file=None)

    def _save_state(self):
        """Save current state to disk."""
        try:
            data = {
                "processed_files": self.state.processed_files,
                "results": [
                    {
                        "source_file": str(r.source_file),
                        "mermaid_content": r.mermaid_content,
                        "conversion_method": r.conversion_method,
                        "warnings": r.warnings,
                        "success": r.success,
                    }
                    for r in self.state.results
                ],
                "failed_files": self.state.failed_files,
                "total_files": self.state.total_files,
                "current_file": self.state.current_file,
            }
            write_json_with_retry(data, self.session_file)
            logger.debug(f"Session state saved: {len(self.state.processed_files)}/{self.state.total_files} processed")
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")

    def is_processed(self, file_path: Path) -> bool:
        """Check if a file has already been processed.

        Args:
            file_path: Path to check

        Returns:
            True if file was already processed
        """
        return str(file_path) in self.state.processed_files

    def start_file(self, file_path: Path):
        """Mark a file as being processed.

        Args:
            file_path: File being started
        """
        self.state.current_file = str(file_path)
        self._save_state()

    def complete_file(self, result: ConversionResult):
        """Mark a file as successfully processed.

        Args:
            result: Conversion result to store
        """
        file_str = str(result.source_file)
        if file_str not in self.state.processed_files:
            self.state.processed_files.append(file_str)
        self.state.results.append(result)
        self.state.current_file = None
        self._save_state()

        # Log progress
        progress = len(self.state.processed_files)
        total = self.state.total_files
        percent = (progress / total * 100) if total > 0 else 0
        logger.info(f"Progress: {progress}/{total} ({percent:.1f}%)")

    def fail_file(self, file_path: Path, error: str):
        """Mark a file as failed.

        Args:
            file_path: File that failed
            error: Error message
        """
        file_str = str(file_path)
        if file_str not in self.state.processed_files:
            self.state.processed_files.append(file_str)
        self.state.failed_files.append((file_str, error))
        self.state.current_file = None
        self._save_state()
        logger.error(f"Failed to convert {file_path.name}: {error}")

    def set_total_files(self, count: int):
        """Set the total number of files to process.

        Args:
            count: Total file count
        """
        self.state.total_files = count
        self._save_state()

    def get_results(self) -> list[ConversionResult]:
        """Get all successful conversion results.

        Returns:
            List of conversion results
        """
        return self.state.results

    def get_failed(self) -> list[tuple[str, str]]:
        """Get all failed files.

        Returns:
            List of (file_path, error_message) tuples
        """
        return self.state.failed_files

    def get_summary(self) -> dict:
        """Get session summary statistics.

        Returns:
            Summary dictionary
        """
        successful = len([r for r in self.state.results if r.success])
        failed = len(self.state.failed_files)

        return {
            "total_files": self.state.total_files,
            "processed": len(self.state.processed_files),
            "successful": successful,
            "failed": failed,
            "completion_percent": (len(self.state.processed_files) / self.state.total_files * 100)
            if self.state.total_files > 0
            else 0,
        }

    def clear(self):
        """Clear session state and delete session file."""
        self.state = SessionState(processed_files=[], results=[], failed_files=[], total_files=0, current_file=None)
        if self.session_file.exists():
            self.session_file.unlink()
        logger.info("Session cleared")
