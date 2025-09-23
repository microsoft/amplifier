"""
Rollback operations module for Amplifier CLI v3.

This module provides transaction-like operations with automatic rollback
capability for file operations during command execution.

Contract:
    - RollbackManager: Main rollback handler with context manager support
    - track_operation(): Record an operation for potential rollback
    - commit(): Finalize all operations (cleanup backups)
    - rollback(): Undo all tracked operations
    - Supports file creation, modification, and deletion
    - Integration with manifest updates
"""

import shutil
import tempfile
from contextlib import contextmanager
from contextlib import suppress
from enum import Enum
from pathlib import Path
from typing import Any

from amplifier.cli.core.errors import AmplifierCLIError
from amplifier.cli.core.manifest import load_manifest
from amplifier.cli.core.manifest import save_manifest
from amplifier.cli.core.output import get_output_manager
from amplifier.cli.models import Manifest


class OperationType(Enum):
    """Types of operations that can be rolled back."""

    CREATE = "create"  # File was created
    MODIFY = "modify"  # File was modified
    DELETE = "delete"  # File was deleted
    MANIFEST_UPDATE = "manifest_update"  # Manifest was updated


class FileOperation:
    """Represents a file operation that can be rolled back."""

    def __init__(
        self,
        operation_type: OperationType,
        path: Path,
        backup_path: Path | None = None,
        original_data: Any = None,
    ):
        """Initialize a file operation.

        Args:
            operation_type: Type of operation
            path: Path to the file
            backup_path: Path to backup file (for modify/delete operations)
            original_data: Original data (for manifest operations)
        """
        self.operation_type = operation_type
        self.path = path
        self.backup_path = backup_path
        self.original_data = original_data


class RollbackError(AmplifierCLIError):
    """Raised when rollback operations fail."""

    def __init__(self, message: str, failed_operations: list[str] | None = None):
        """Initialize the rollback error.

        Args:
            message: Error message
            failed_operations: List of operations that failed to rollback
        """
        hint = "Some operations could not be rolled back. Manual cleanup may be required."
        if failed_operations:
            hint += f"\nFailed operations: {', '.join(failed_operations)}"
        super().__init__(message, hint=hint)
        self.failed_operations = failed_operations


class RollbackManager:
    """Manages rollback operations for transactional file handling.

    This class provides transaction-like semantics for file operations,
    allowing automatic rollback on failure.

    Example:
        >>> with RollbackManager() as rm:
        ...     rm.track_create(Path("new_file.txt"))
        ...     # Write to new_file.txt
        ...     rm.track_modify(Path("existing.txt"))
        ...     # Modify existing.txt
        ...     # If exception occurs here, all operations are rolled back
        ...     rm.commit()  # Success - cleanup backups
    """

    def __init__(self, verbose: bool = False):
        """Initialize the rollback manager.

        Args:
            verbose: Whether to print verbose output during operations
        """
        self.operations: list[FileOperation] = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="amplifier_rollback_"))
        self.verbose = verbose
        self._committed = False
        self._rolled_back = False
        self.output = get_output_manager(debug=verbose)

    def track_create(self, path: Path) -> None:
        """Track a file creation for potential rollback.

        Args:
            path: Path to the created file
        """
        if self.verbose:
            self.output.debug(f"Tracking creation of {path}")
        self.operations.append(FileOperation(OperationType.CREATE, path))

    def track_modify(self, path: Path) -> Path:
        """Track a file modification for potential rollback.

        Creates a backup of the file before modification.

        Args:
            path: Path to the file being modified

        Returns:
            Path to the backup file (for reference)
        """
        if not path.exists():
            raise ValueError(f"Cannot track modification of non-existent file: {path}")

        # Create backup
        backup_path = self.temp_dir / f"{path.name}.{len(self.operations)}.bak"
        shutil.copy2(path, backup_path)

        if self.verbose:
            self.output.debug(f"Backing up {path} before modification")

        self.operations.append(FileOperation(OperationType.MODIFY, path, backup_path))
        return backup_path

    def track_delete(self, path: Path) -> Path:
        """Track a file deletion for potential rollback.

        Creates a backup of the file before deletion.

        Args:
            path: Path to the file being deleted

        Returns:
            Path to the backup file (for reference)
        """
        if not path.exists():
            raise ValueError(f"Cannot track deletion of non-existent file: {path}")

        # Create backup
        backup_path = self.temp_dir / f"{path.name}.{len(self.operations)}.deleted"
        if path.is_dir():
            shutil.copytree(path, backup_path)
        else:
            shutil.copy2(path, backup_path)

        if self.verbose:
            self.output.debug(f"Backing up {path} before deletion")

        self.operations.append(FileOperation(OperationType.DELETE, path, backup_path))
        return backup_path

    def track_manifest_update(self) -> None:
        """Track a manifest update for potential rollback.

        Saves the current manifest state before modifications.
        """
        try:
            current_manifest = load_manifest()
            # Store as JSON string to avoid reference issues
            original_data = current_manifest.model_dump(mode="json")

            if self.verbose:
                self.output.debug("Backing up manifest before update")

            self.operations.append(
                FileOperation(
                    OperationType.MANIFEST_UPDATE, Path(".amplifier/manifest.json"), original_data=original_data
                )
            )
        except Exception as e:
            # If we can't load the manifest, we can't track it
            if self.verbose:
                self.output.warning(f"Could not backup manifest: {e}")

    def commit(self) -> None:
        """Commit all operations and cleanup backups.

        This should be called when all operations have succeeded.
        """
        if self._committed:
            return

        if self.verbose:
            self.output.success("Committing transaction (cleaning up backups)")

        # Clean up temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        self._committed = True

    def rollback(self) -> None:
        """Rollback all tracked operations.

        Attempts to undo all operations in reverse order.
        Raises RollbackError if any rollback operation fails.
        """
        if self._rolled_back or self._committed:
            return

        self.output.warning("Rolling back operations...")
        failed_operations = []

        # Process operations in reverse order
        for operation in reversed(self.operations):
            try:
                self._rollback_operation(operation)
            except Exception as e:
                failed_operations.append(f"{operation.operation_type.value} on {operation.path}: {e}")
                if self.verbose:
                    self.output.error(f"Failed to rollback {operation.operation_type.value} on {operation.path}: {e}")

        # Clean up temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        self._rolled_back = True

        if failed_operations:
            raise RollbackError("Some operations could not be rolled back", failed_operations)
        self.output.success("Successfully rolled back all operations")

    def _rollback_operation(self, operation: FileOperation) -> None:
        """Rollback a single operation.

        Args:
            operation: The operation to rollback
        """
        if operation.operation_type == OperationType.CREATE:
            # Delete the created file
            if operation.path.exists():
                if operation.path.is_dir():
                    shutil.rmtree(operation.path)
                else:
                    operation.path.unlink()
                if self.verbose:
                    self.output.debug(f"Removed created file: {operation.path}")

        elif operation.operation_type == OperationType.MODIFY:
            # Restore the original file
            if operation.backup_path and operation.backup_path.exists():
                shutil.copy2(operation.backup_path, operation.path)
                if self.verbose:
                    self.output.debug(f"Restored modified file: {operation.path}")

        elif operation.operation_type == OperationType.DELETE:
            # Restore the deleted file
            if operation.backup_path and operation.backup_path.exists():
                if operation.backup_path.is_dir():
                    shutil.copytree(operation.backup_path, operation.path)
                else:
                    shutil.copy2(operation.backup_path, operation.path)
                if self.verbose:
                    self.output.debug(f"Restored deleted file: {operation.path}")

        elif operation.operation_type == OperationType.MANIFEST_UPDATE and operation.original_data:
            # Restore the original manifest
            manifest = Manifest(**operation.original_data)
            save_manifest(manifest)
            if self.verbose:
                self.output.debug("Restored original manifest")

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager.

        If an exception occurred, rollback operations.
        Otherwise, commit them.
        """
        if exc_type is not None:
            # An exception occurred, rollback
            with suppress(RollbackError):
                # Log but don't suppress the original exception
                self.rollback()
        else:
            # No exception, commit
            self.commit()

        # Don't suppress the original exception
        return False


@contextmanager
def transactional_operation(verbose: bool = False):
    """Context manager for transactional file operations.

    This is a convenience wrapper around RollbackManager.

    Args:
        verbose: Whether to print verbose output

    Yields:
        RollbackManager instance for tracking operations

    Example:
        >>> with transactional_operation() as transaction:
        ...     transaction.track_create(Path("new_file.txt"))
        ...     # Write to new_file.txt
        ...     # If exception occurs, new_file.txt will be deleted
    """
    manager = RollbackManager(verbose=verbose)
    try:
        yield manager
        manager.commit()
    except Exception:
        manager.rollback()
        raise
    finally:
        # Ensure cleanup even if rollback fails
        if manager.temp_dir.exists():
            shutil.rmtree(manager.temp_dir, ignore_errors=True)


def track_operation(operation_type: str, path: Path, manager: RollbackManager) -> None:
    """Convenience function to track an operation.

    Args:
        operation_type: Type of operation ("create", "modify", "delete")
        path: Path to the file
        manager: RollbackManager instance
    """
    if operation_type == "create":
        manager.track_create(path)
    elif operation_type == "modify":
        manager.track_modify(path)
    elif operation_type == "delete":
        manager.track_delete(path)
    else:
        raise ValueError(f"Unknown operation type: {operation_type}")
