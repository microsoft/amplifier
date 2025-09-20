"""Tests for rollback functionality."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from amplifier.cli.core.rollback import RollbackError
from amplifier.cli.core.rollback import RollbackManager
from amplifier.cli.core.rollback import transactional_operation
from amplifier.cli.models import Manifest


class TestRollbackManager:
    """Test the RollbackManager class."""

    def test_track_create_and_rollback(self, tmp_path):
        """Test tracking file creation and rolling it back."""
        test_file = tmp_path / "test_file.txt"

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            manager = RollbackManager(verbose=True)

            # Create a file and track it
            test_file.write_text("test content")
            manager.track_create(test_file)

            assert test_file.exists()

            # Rollback should delete the file
            manager.rollback()
            assert not test_file.exists()

    def test_track_modify_and_rollback(self, tmp_path):
        """Test tracking file modification and rolling it back."""
        test_file = tmp_path / "test_file.txt"
        original_content = "original content"

        # Create file with original content
        test_file.write_text(original_content)

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            manager = RollbackManager()

            # Track modification
            backup_path = manager.track_modify(test_file)
            assert backup_path.exists()

            # Modify the file
            test_file.write_text("modified content")

            # Rollback should restore original content
            manager.rollback()
            assert test_file.read_text() == original_content

    def test_track_delete_and_rollback(self, tmp_path):
        """Test tracking file deletion and rolling it back."""
        test_file = tmp_path / "test_file.txt"
        original_content = "original content"

        # Create file
        test_file.write_text(original_content)

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            manager = RollbackManager()

            # Track deletion
            backup_path = manager.track_delete(test_file)
            assert backup_path.exists()

            # Delete the file
            test_file.unlink()
            assert not test_file.exists()

            # Rollback should restore the file
            manager.rollback()
            assert test_file.exists()
            assert test_file.read_text() == original_content

    def test_track_delete_directory_and_rollback(self, tmp_path):
        """Test tracking directory deletion and rolling it back."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        test_file = test_dir / "test_file.txt"
        test_file.write_text("content")

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            manager = RollbackManager()

            # Track deletion of directory
            backup_path = manager.track_delete(test_dir)
            assert backup_path.exists()

            # Delete the directory
            import shutil

            shutil.rmtree(test_dir)
            assert not test_dir.exists()

            # Rollback should restore the directory and its contents
            manager.rollback()
            assert test_dir.exists()
            assert test_file.exists()
            assert test_file.read_text() == "content"

    def test_commit_cleans_up_backups(self, tmp_path):
        """Test that commit cleans up backup files."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("original")

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            manager = RollbackManager()

            # Track a modification
            manager.track_modify(test_file)

            # Temp directory should exist
            assert manager.temp_dir.exists()

            # Commit should clean up
            manager.commit()
            assert not manager.temp_dir.exists()

    def test_context_manager_rollback_on_exception(self, tmp_path):
        """Test context manager rolls back on exception."""
        test_file = tmp_path / "test_file.txt"

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            try:
                with RollbackManager() as manager:
                    # Create a file and track it
                    test_file.write_text("test content")
                    manager.track_create(test_file)

                    assert test_file.exists()

                    # Simulate an error
                    raise ValueError("Test error")
            except ValueError:
                pass

            # File should be rolled back
            assert not test_file.exists()

    def test_context_manager_commit_on_success(self, tmp_path):
        """Test context manager commits on success."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("original")

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            with RollbackManager() as manager:
                # Track a modification
                backup_path = manager.track_modify(test_file)

                # Modify the file
                test_file.write_text("modified")

                # Backup should exist during operation
                assert backup_path.exists()

            # After successful exit, backup should be cleaned up
            assert not backup_path.parent.exists()
            # Modified content should remain
            assert test_file.read_text() == "modified"

    def test_manifest_rollback(self, tmp_path):
        """Test manifest update rollback."""
        with (
            patch("amplifier.cli.core.rollback.get_output_manager") as mock_output,
            patch("amplifier.cli.core.rollback.load_manifest") as mock_load,
            patch("amplifier.cli.core.rollback.save_manifest") as mock_save,
        ):
            mock_output.return_value = MagicMock()

            # Create a mock manifest
            original_manifest = Manifest()
            original_manifest.metadata.project_name = "original"
            mock_load.return_value = original_manifest

            manager = RollbackManager()

            # Track manifest update
            manager.track_manifest_update()

            # Simulate manifest change
            modified_manifest = Manifest()
            modified_manifest.metadata.project_name = "modified"

            # Rollback should restore original
            manager.rollback()

            # Verify save was called with original manifest data
            mock_save.assert_called_once()
            saved_manifest = mock_save.call_args[0][0]
            assert saved_manifest.metadata.project_name == "original"

    def test_multiple_operations_rollback(self, tmp_path):
        """Test rolling back multiple operations in correct order."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"

        # Create file2 with original content
        file2.write_text("original")

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            manager = RollbackManager()

            # Track multiple operations
            file1.write_text("created")
            manager.track_create(file1)

            manager.track_modify(file2)
            file2.write_text("modified")

            file3.write_text("to delete")
            manager.track_delete(file3)
            file3.unlink()

            # Rollback should undo all operations
            manager.rollback()

            # Check results
            assert not file1.exists()  # Created file should be deleted
            assert file2.read_text() == "original"  # Modified file should be restored
            assert file3.exists()  # Deleted file should be restored
            assert file3.read_text() == "to delete"

    def test_transactional_operation_helper(self, tmp_path):
        """Test the transactional_operation context manager."""
        test_file = tmp_path / "test_file.txt"

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            try:
                with transactional_operation() as transaction:
                    test_file.write_text("test")
                    transaction.track_create(test_file)

                    assert test_file.exists()
                    raise RuntimeError("Test error")
            except RuntimeError:
                pass

            # File should be rolled back
            assert not test_file.exists()

    def test_rollback_error_handling(self, tmp_path):
        """Test handling of rollback errors."""
        test_file = tmp_path / "test_file.txt"

        with patch("amplifier.cli.core.rollback.get_output_manager") as mock_output:
            mock_output.return_value = MagicMock()

            manager = RollbackManager()

            # Create a file and track it for deletion
            test_file.write_text("test")
            manager.track_create(test_file)

            # Make the file unremovable by changing permissions on parent dir
            # This is tricky to test portably, so we'll mock the rollback operation
            with patch.object(manager, "_rollback_operation", side_effect=Exception("Permission denied")):
                # Rollback should raise RollbackError
                with pytest.raises(RollbackError) as exc_info:
                    manager.rollback()

                assert "Some operations could not be rolled back" in str(exc_info.value)
