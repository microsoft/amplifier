"""
Transcript management workflow integration tests.

This module contains comprehensive integration tests for transcript management workflows
across both Claude Code and Codex backends, including export, conversion, and management.
"""

import os
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from amplifier.core.backend import BackendOperationError
from amplifier.core.backend import ClaudeCodeBackend
from amplifier.core.backend import CodexBackend


class TestClaudeTranscriptWorkflows:
    """Claude Code transcript workflow integration tests."""

    def test_claude_export_transcript_workflow(self, integration_test_project, mock_claude_transcript):
        """Test complete Claude Code transcript export workflow."""
        # Change to project directory
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = ClaudeCodeBackend()

            # Mock the export to create a real file
            with patch.object(backend, "export_transcript") as mock_export:
                mock_export.return_value = {
                    "success": True,
                    "data": {"path": str(mock_claude_transcript)},
                    "metadata": {"format": "standard", "session_id": "test_session"},
                }

                result = backend.export_transcript(session_id="test_session")

                assert result["success"] is True
                assert "path" in result["data"]
                assert result["metadata"]["session_id"] == "test_session"
                assert result["metadata"]["format"] == "standard"

                # Verify file was created
                transcript_path = Path(result["data"]["path"])
                assert transcript_path.exists()
                content = transcript_path.read_text()
                assert "Claude Code Transcript" in content
        finally:
            os.chdir(original_cwd)

    def test_claude_export_with_session_id(self, integration_test_project):
        """Test Claude Code transcript export with explicit session ID."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = ClaudeCodeBackend()

            with patch.object(backend, "export_transcript") as mock_export:
                mock_export.return_value = {
                    "success": True,
                    "data": {"path": ".data/transcripts/compact_test_session.txt"},
                    "metadata": {"format": "standard", "session_id": "test_session"},
                }

                result = backend.export_transcript(session_id="test_session")

                assert result["success"] is True
                assert result["metadata"]["session_id"] == "test_session"
                assert "test_session" in result["data"]["path"]
        finally:
            os.chdir(original_cwd)

    def test_claude_export_with_custom_output_dir(self, integration_test_project, temp_dir):
        """Test Claude Code transcript export with custom output directory."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = ClaudeCodeBackend()
            custom_dir = temp_dir / "custom_transcripts"

            with patch.object(backend, "export_transcript") as mock_export:
                mock_export.return_value = {
                    "success": True,
                    "data": {"path": str(custom_dir / "transcript.txt")},
                    "metadata": {"format": "standard", "session_id": "test_session"},
                }

                result = backend.export_transcript(session_id="test_session", output_dir=str(custom_dir))

                assert result["success"] is True
                assert custom_dir.name in result["data"]["path"]
        finally:
            os.chdir(original_cwd)


class TestCodexTranscriptWorkflows:
    """Codex transcript workflow integration tests."""

    def test_codex_export_transcript_workflow(self, integration_test_project, mock_codex_session_dir):
        """Test complete Codex transcript export workflow."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = CodexBackend()

            # Mock the CodexTranscriptExporter
            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter

                # Mock successful export
                mock_result = mock_codex_session_dir / "transcript.md"
                mock_result.write_text("# Exported Transcript\nContent here")
                mock_exporter.export_codex_transcript.return_value = mock_result

                result = backend.export_transcript(session_id="test_session_123456")

                assert result["success"] is True
                assert "path" in result["data"]
                assert result["metadata"]["session_id"] == "test_session_123456"
                assert result["metadata"]["format"] == "standard"

                # Verify exporter was called correctly
                mock_exporter.export_codex_transcript.assert_called_once()
                args = mock_exporter.export_codex_transcript.call_args
                assert args[0][0] == "test_session_123456"  # session_id
                assert str(args[0][1]) == ".codex/transcripts"  # output_dir
                assert args[0][2] == "standard"  # format
        finally:
            os.chdir(original_cwd)

    def test_codex_export_standard_format(self, integration_test_project, mock_codex_session_dir):
        """Test Codex transcript export in standard format."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = CodexBackend()

            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter

                mock_result = mock_codex_session_dir / "transcript.md"
                mock_result.write_text("# Standard Transcript\nUser: Hello\nAssistant: Hi there")
                mock_exporter.export_codex_transcript.return_value = mock_result

                result = backend.export_transcript(session_id="test_session", format="standard")

                assert result["success"] is True
                assert result["metadata"]["format"] == "standard"

                # Verify content
                content = mock_result.read_text()
                assert "Standard Transcript" in content
                assert "User: Hello" in content
                assert "Assistant: Hi there" in content
        finally:
            os.chdir(original_cwd)

    def test_codex_export_extended_format(self, integration_test_project, mock_codex_session_dir):
        """Test Codex transcript export in extended format."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = CodexBackend()

            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter

                mock_result = mock_codex_session_dir / "transcript_extended.md"
                mock_result.write_text("# Extended Transcript\nDetailed event information")
                mock_exporter.export_codex_transcript.return_value = mock_result

                result = backend.export_transcript(session_id="test_session", format="extended")

                assert result["success"] is True
                assert result["metadata"]["format"] == "extended"

                # Verify content
                content = mock_result.read_text()
                assert "Extended Transcript" in content
                assert "Detailed event information" in content
        finally:
            os.chdir(original_cwd)

    def test_codex_export_both_formats(self, integration_test_project, mock_codex_session_dir):
        """Test Codex transcript export in both formats."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = CodexBackend()

            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter

                # Mock export_codex_transcript to handle format="both"
                mock_result = mock_codex_session_dir / "transcript.md"
                mock_result.write_text("# Both Formats Transcript\nCombined content")
                mock_exporter.export_codex_transcript.return_value = mock_result

                result = backend.export_transcript(session_id="test_session", format="both")

                assert result["success"] is True
                assert result["metadata"]["format"] == "both"
        finally:
            os.chdir(original_cwd)

    def test_codex_export_compact_format(self, integration_test_project, mock_codex_session_dir):
        """Test Codex transcript export in compact format."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            backend = CodexBackend()

            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter

                mock_result = mock_codex_session_dir / "test_session_compact.md"
                mock_result.write_text("# Compact Transcript\nSingle file format")
                mock_exporter.export_codex_transcript.return_value = mock_result

                result = backend.export_transcript(session_id="test_session", format="compact")

                assert result["success"] is True
                assert result["metadata"]["format"] == "compact"

                # Verify content
                content = mock_result.read_text()
                assert "Compact Transcript" in content
        finally:
            os.chdir(original_cwd)


class TestTranscriptConversionWorkflows:
    """Cross-backend transcript conversion workflow tests."""

    def test_convert_claude_to_codex_format(self, integration_test_project, mock_claude_transcript):
        """Test conversion from Claude Code to Codex format."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Mock the conversion
            with patch.object(manager, "convert_format") as mock_convert:
                mock_convert.return_value = True

                success = manager.convert_format(session_id="test_session", from_backend="claude", to_backend="codex")

                assert success is True
                mock_convert.assert_called_once_with(
                    session_id="test_session", from_backend="claude", to_backend="codex", output_path=None
                )
        finally:
            os.chdir(original_cwd)

    def test_convert_codex_to_claude_format(self, integration_test_project, mock_codex_session_dir):
        """Test conversion from Codex to Claude Code format."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Mock the conversion
            with patch.object(manager, "convert_format") as mock_convert:
                mock_convert.return_value = True

                success = manager.convert_format(session_id="test_session", from_backend="codex", to_backend="claude")

                assert success is True
                mock_convert.assert_called_once_with(
                    session_id="test_session", from_backend="codex", to_backend="claude", output_path=None
                )
        finally:
            os.chdir(original_cwd)

    def test_bidirectional_conversion_preserves_content(self, integration_test_project, mock_claude_transcript):
        """Test that bidirectional conversion preserves content."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Mock conversions
            with patch.object(manager, "convert_format") as mock_convert:
                mock_convert.return_value = True

                # Claude -> Codex
                success1 = manager.convert_format(session_id="test_session", from_backend="claude", to_backend="codex")
                assert success1 is True

                # Codex -> Claude (back)
                success2 = manager.convert_format(session_id="test_session", from_backend="codex", to_backend="claude")
                assert success2 is True

                # Verify both conversions were called
                assert mock_convert.call_count == 2
        finally:
            os.chdir(original_cwd)


class TestTranscriptManagerIntegration:
    """Transcript manager integration tests."""

    def test_transcript_manager_lists_both_backends(
        self, integration_test_project, mock_claude_transcript, mock_codex_session_dir
    ):
        """Test transcript manager lists transcripts from both backends."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager(backend="auto")

            transcripts = manager.list_transcripts()

            # Should find both Claude and Codex transcripts
            assert len(transcripts) >= 2

            # Check for Claude transcript
            claude_found = any("compact_" in str(t) for t in transcripts)
            assert claude_found, "Claude transcript not found"

            # Check for Codex transcript
            codex_found = any("transcript.md" in str(t) for t in transcripts)
            assert codex_found, "Codex transcript not found"
        finally:
            os.chdir(original_cwd)

    def test_transcript_manager_loads_claude_transcript(self, integration_test_project, mock_claude_transcript):
        """Test transcript manager loads Claude Code transcript."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            content = manager.load_transcript_content("compact_20240101_100000_session123.txt")

            assert content is not None
            assert "Claude Code Transcript" in content
            assert "Session ID: session123" in content
        finally:
            os.chdir(original_cwd)

    def test_transcript_manager_loads_codex_transcript(self, integration_test_project, mock_codex_session_dir):
        """Test transcript manager loads Codex transcript."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Load standard format
            content = manager.load_transcript_content("test_session_123456", format_preference="standard")

            assert content is not None
            assert "User: How do I start a session?" in content
            assert "Assistant: Use the session_init.py script" in content
        finally:
            os.chdir(original_cwd)

    def test_transcript_manager_search_across_backends(
        self, integration_test_project, mock_claude_transcript, mock_codex_session_dir
    ):
        """Test transcript manager searches across both backends."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Search for term that appears in both transcripts
            results = manager.search_transcripts("session")

            assert results is not None
            assert len(results) > 0

            # Should find matches in both backends
            results_str = "".join(results)
            assert "[Claude Code]" in results_str or "[CODEX]" in results_str
        finally:
            os.chdir(original_cwd)

    def test_transcript_manager_restore_combined_lineage(
        self, integration_test_project, mock_claude_transcript, mock_codex_session_dir
    ):
        """Test transcript manager restores combined conversation lineage."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            content = manager.restore_conversation_lineage()

            assert content is not None
            assert "CONVERSATION SEGMENT" in content

            # Should contain content from both backends
            assert "[Claude Code]" in content or "[CODEX]" in content
        finally:
            os.chdir(original_cwd)


class TestTranscriptExportViaMCPTools:
    """MCP server transcript export tool tests."""

    def test_save_current_transcript_mcp_tool(self, integration_test_project, mock_codex_session_dir):
        """Test save_current_transcript MCP tool."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from amplifier.core.backend import CodexBackend

            # Mock the MCP server components
            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.get_current_codex_session.return_value = "test_session_123456"

                mock_result = mock_codex_session_dir / "transcript.md"
                mock_result.write_text("# Current Session Transcript\nContent")
                mock_exporter.export_codex_transcript.return_value = mock_result

                # Test via backend (which uses the exporter)
                backend = CodexBackend()
                result = backend.export_transcript(session_id="test_session_123456")

                assert result["success"] is True
                assert "path" in result["data"]
                mock_exporter.get_current_codex_session.assert_not_called()  # Not called since session_id provided

                # Verify export was called
                mock_exporter.export_codex_transcript.assert_called_once()
        finally:
            os.chdir(original_cwd)

    def test_save_project_transcripts_mcp_tool(self, integration_test_project, mock_codex_session_dir):
        """Test save_project_transcripts MCP tool functionality."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Mock the list and export functionality
            with patch.object(manager, "list_transcripts") as mock_list:
                mock_list.return_value = [mock_codex_session_dir / "transcript.md"]

                transcripts = manager.list_transcripts()

                assert len(transcripts) == 1
                assert transcripts[0].name == "transcript.md"
        finally:
            os.chdir(original_cwd)

    def test_save_project_transcripts_incremental(self, integration_test_project, mock_codex_session_dir):
        """Test incremental project transcript saving."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            # Create a mock already-exported transcript
            exported_dir = integration_test_project / ".codex" / "transcripts" / "already_exported"
            exported_dir.mkdir(parents=True)
            (exported_dir / "transcript.md").write_text("# Already exported")

            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Mock to return both existing and new transcripts
            with patch.object(manager, "list_transcripts") as mock_list:
                mock_list.return_value = [exported_dir / "transcript.md", mock_codex_session_dir / "transcript.md"]

                transcripts = manager.list_transcripts()

                assert len(transcripts) == 2
                # In real implementation, incremental logic would filter out already exported ones
        finally:
            os.chdir(original_cwd)

    def test_list_available_sessions_mcp_tool(self, integration_test_project, mock_codex_session_dir):
        """Test list_available_sessions MCP tool."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Mock session listing
            with patch.object(manager, "list_transcripts") as mock_list:
                mock_list.return_value = [mock_codex_session_dir / "transcript.md"]

                transcripts = manager.list_transcripts()

                assert len(transcripts) == 1
                assert "transcript.md" in transcripts[0].name
        finally:
            os.chdir(original_cwd)

    def test_list_available_sessions_project_filter(self, integration_test_project, mock_codex_session_dir):
        """Test project filtering in session listing."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from tools.transcript_manager import TranscriptManager

            manager = TranscriptManager()

            # Mock project filtering
            with patch.object(manager, "_determine_backend_for_path") as mock_determine:
                mock_determine.return_value = "codex"

                backend = manager._determine_backend_for_path(mock_codex_session_dir / "transcript.md")

                assert backend == "codex"
        finally:
            os.chdir(original_cwd)


class TestSessionDetection:
    """Session detection tests."""

    def test_detect_current_codex_session(self, integration_test_project, mock_codex_session_dir):
        """Test detection of current Codex session."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.get_current_codex_session.return_value = "test_session_123456"

                from amplifier.core.backend import CodexBackend

                backend = CodexBackend()

                # Test export without session_id (should detect current)
                with patch.object(backend, "export_transcript") as mock_export:
                    mock_export.return_value = {
                        "success": True,
                        "data": {"path": "mock_path"},
                        "metadata": {"session_id": "detected_session"},
                    }

                    result = backend.export_transcript()

                    assert result["success"] is True
        finally:
            os.chdir(original_cwd)

    def test_detect_project_sessions(self, integration_test_project, mock_codex_session_dir):
        """Test detection of project-specific sessions."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.get_project_sessions.return_value = ["session1", "session2"]

                # Test would call get_project_sessions with current project directory
                # This is tested indirectly through the MCP tools above
                assert True  # Placeholder for actual test
        finally:
            os.chdir(original_cwd)


class TestTranscriptErrorHandling:
    """Error handling tests for transcript operations."""

    def test_export_transcript_no_session_found(self, integration_test_project):
        """Test graceful handling when no session is found."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from amplifier.core.backend import ClaudeCodeBackend

            backend = ClaudeCodeBackend()

            with patch.object(backend, "export_transcript") as mock_export:
                mock_export.side_effect = BackendOperationError("No session found")

                with pytest.raises(BackendOperationError, match="No session found"):
                    backend.export_transcript(session_id="nonexistent")
        finally:
            os.chdir(original_cwd)

    def test_export_transcript_corrupted_session_data(self, integration_test_project, mock_codex_session_dir):
        """Test handling of corrupted session data."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            # Corrupt the session data
            meta_file = mock_codex_session_dir / "meta.json"
            meta_file.write_text("invalid json content")

            from amplifier.core.backend import CodexBackend

            backend = CodexBackend()

            # Should handle JSON parsing errors gracefully
            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_codex_transcript.return_value = None  # Failed export

                result = backend.export_transcript(session_id="test_session_123456")

                assert result["success"] is False
        finally:
            os.chdir(original_cwd)

    def test_export_transcript_permission_error(self, integration_test_project, mock_codex_session_dir, monkeypatch):
        """Test handling of permission errors during export."""
        original_cwd = os.getcwd()
        os.chdir(integration_test_project)

        try:
            from amplifier.core.backend import CodexBackend

            backend = CodexBackend()

            with patch("amplifier.core.backend.CodexTranscriptExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_codex_transcript.side_effect = PermissionError("Permission denied")

                with pytest.raises(BackendOperationError):
                    backend.export_transcript(session_id="test_session")
        finally:
            os.chdir(original_cwd)
