#!/usr/bin/env python3
"""
Tests for unified transcript manager.

Comprehensive tests covering transcript_manager.py backend abstraction,
dual-backend support, and unified interface functionality.
"""

# Import module under test
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent / "tools"))

from transcript_manager import TranscriptManager

# Test fixtures


@pytest.fixture
def mock_claude_transcript():
    """Generate sample Claude Code transcript content."""
    return """# Claude Code Transcript

Export time: 2024-01-01 10:00:00
Session ID: claude-session-123
Working directory: /test/project

[USER]: Hello, how can you help me?

[ASSISTANT]: I can help you with various tasks including code analysis, writing, and problem-solving.

[TOOL USE: file_reader]
{
  "path": "test.py"
}

[TOOL RESULT]
def hello():
    print("Hello world")

[ASSISTANT]: I can see you have a simple Python function that prints "Hello world".
"""


@pytest.fixture
def mock_codex_transcript():
    """Generate sample Codex transcript content."""
    return """# Codex Session Transcript

**Session ID:** codex-session-456
**Started:** 2024-01-01T10:00:00Z
**Working Directory:** /test/project
**Exported:** 2024-01-01T11:00:00Z

---

## Conversation

- **User** · 2024-01-01 10:00:00
  Hello, how can you help me?

- **Assistant** · 2024-01-01 10:00:01
  I can help you with various tasks including code analysis, writing, and problem-solving.

- **Tool Call (file_reader)** · 2024-01-01 10:00:02
  ```json
  {
    "path": "test.py"
  }
  ```

- **Tool Result** · 2024-01-01 10:00:03
  ```python
  def hello():
      print("Hello world")
  ```

- **Assistant** · 2024-01-01 10:00:04
  I can see you have a simple Python function that prints "Hello world".
"""


@pytest.fixture
def mock_dual_backend_setup(tmp_path):
    """Set up mock environment with both Claude Code and Codex transcripts."""
    # Claude Code setup
    claude_dir = tmp_path / ".claude"
    claude_transcripts = tmp_path / ".data" / "transcripts"
    claude_transcripts.mkdir(parents=True)
    claude_dir.mkdir()

    # Create Claude Code transcript
    claude_transcript = claude_transcripts / "compact_20240101_100000_claude-session-123.txt"
    claude_transcript.write_text("Claude Code transcript content")

    # Create current_session file
    (claude_dir / "current_session").write_text("claude-session-123")

    # Codex setup
    codex_dir = tmp_path / ".codex"
    codex_global = tmp_path / ".codex_global" / "transcripts"
    codex_local = tmp_path / ".codex" / "transcripts"

    for dir_path in [codex_dir, codex_global, codex_local]:
        dir_path.mkdir(parents=True)

    # Create Codex session directory
    codex_session_dir = codex_global / "2024-01-01-10-00-AM__test-project__codex456"
    codex_session_dir.mkdir(parents=True)
    (codex_session_dir / "transcript.md").write_text("Codex transcript content")

    return {
        "tmp_path": tmp_path,
        "claude_transcripts": claude_transcripts,
        "codex_global": codex_global,
        "codex_local": codex_local,
        "codex_session_dir": codex_session_dir,
    }


@pytest.fixture
def transcript_manager_instance(tmp_path):
    """Create TranscriptManager instance with temporary directories."""
    with patch.object(TranscriptManager, "__init__", lambda x, backend="auto": None):
        manager = TranscriptManager.__new__(TranscriptManager)
        manager.backend = "auto"
        manager.data_dir = tmp_path / ".data"
        manager.transcripts_dir = manager.data_dir / "transcripts"
        manager.codex_global_dir = tmp_path / ".codex_global" / "transcripts"
        manager.codex_local_dir = tmp_path / ".codex" / "transcripts"
        return manager


# Test backend detection


class TestBackendDetection:
    """Test backend detection functionality."""

    def test_detect_backend_claude_only(self, tmp_path):
        """Test Claude Code backend detection."""
        # Create Claude Code structure
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".data" / "transcripts").mkdir(parents=True)

        with patch("transcript_manager.Path.cwd", return_value=tmp_path):
            manager = TranscriptManager(backend="auto")
            # When only Claude exists, should detect claude or auto
            assert manager.backend in ["claude", "auto"]

    def test_detect_backend_codex_only(self, tmp_path):
        """Test Codex backend detection."""
        # Create Codex structure only
        (tmp_path / ".codex").mkdir()

        with patch("transcript_manager.Path.cwd", return_value=tmp_path):
            manager = TranscriptManager(backend="auto")
            # When only Codex exists, should detect codex
            assert manager.backend == "codex"

    def test_detect_backend_both(self, mock_dual_backend_setup):
        """Test auto-detection with both backends present."""
        tmp_path = mock_dual_backend_setup["tmp_path"]

        with patch("transcript_manager.Path.cwd", return_value=tmp_path):
            manager = TranscriptManager(backend="auto")
            # When both exist, should use auto to support both
            assert manager.backend == "auto"

    def test_detect_backend_neither(self, tmp_path):
        """Test graceful handling when neither backend is present."""
        # Empty directory
        with patch("transcript_manager.Path.cwd", return_value=tmp_path):
            manager = TranscriptManager(backend="auto")
            # Should default to claude when neither is detected
            assert manager.backend == "claude"


# Test Claude Code functionality (backward compatibility)


class TestClaudeFunctionality:
    """Test Claude Code functionality to ensure backward compatibility."""

    def test_list_claude_transcripts(self, tmp_path):
        """Test Claude Code transcript listing."""
        # Set up Claude Code transcripts
        transcripts_dir = tmp_path / ".data" / "transcripts"
        transcripts_dir.mkdir(parents=True)

        # Create sample transcript files
        transcript1 = transcripts_dir / "compact_20240101_100000_session1.txt"
        transcript2 = transcripts_dir / "compact_20240101_110000_session2.txt"
        transcript1.write_text("Transcript 1")
        transcript2.write_text("Transcript 2")

        manager = TranscriptManager(backend="claude")
        manager.transcripts_dir = transcripts_dir

        claude_transcripts = manager._list_claude_transcripts()
        assert len(claude_transcripts) == 2
        assert transcript1 in claude_transcripts
        assert transcript2 in claude_transcripts

    def test_load_claude_transcript(self, tmp_path, mock_claude_transcript):
        """Test loading Claude Code transcript content."""
        transcripts_dir = tmp_path / ".data" / "transcripts"
        transcripts_dir.mkdir(parents=True)

        transcript_file = transcripts_dir / "compact_20240101_100000_claude-session-123.txt"
        transcript_file.write_text(mock_claude_transcript)

        manager = TranscriptManager(backend="claude")
        manager.transcripts_dir = transcripts_dir

        # Test loading by session ID
        content = manager.load_transcript_content("claude-session-123")
        assert content == mock_claude_transcript

        # Test loading by filename
        content = manager.load_transcript_content(transcript_file.name)
        assert content == mock_claude_transcript

    def test_search_claude_transcripts(self, tmp_path, mock_claude_transcript):
        """Test searching in Claude Code transcripts."""
        transcripts_dir = tmp_path / ".data" / "transcripts"
        transcripts_dir.mkdir(parents=True)

        transcript_file = transcripts_dir / "compact_20240101_100000_session.txt"
        transcript_file.write_text(mock_claude_transcript)

        manager = TranscriptManager(backend="claude")
        manager.transcripts_dir = transcripts_dir

        # This test assumes search_transcripts method exists
        # Would need to implement the actual search functionality
        pass


# Test Codex functionality


class TestCodexFunctionality:
    """Test Codex-specific functionality."""

    def test_list_codex_transcripts(self, tmp_path):
        """Test Codex transcript directory listing."""
        # Set up Codex transcript structure
        codex_global = tmp_path / ".codex_global" / "transcripts"
        session_dir1 = codex_global / "2024-01-01-10-00-AM__project__session1"
        session_dir2 = codex_global / "2024-01-01-11-00-AM__project__session2"

        for session_dir in [session_dir1, session_dir2]:
            session_dir.mkdir(parents=True)
            (session_dir / "transcript.md").write_text("Sample transcript")

        manager = TranscriptManager(backend="codex")
        manager.codex_global_dir = codex_global
        manager.codex_local_dir = tmp_path / "nonexistent"  # Won't exist

        codex_transcripts = manager._list_codex_transcripts()
        assert len(codex_transcripts) == 2

        # Should find transcript.md files
        transcript_paths = [t.name for t in codex_transcripts]
        assert all(name == "transcript.md" for name in transcript_paths)

    def test_load_codex_transcript_standard(self, tmp_path, mock_codex_transcript):
        """Test loading Codex transcript.md files."""
        codex_global = tmp_path / ".codex_global" / "transcripts"
        session_dir = codex_global / "2024-01-01-10-00-AM__project__codex456"
        session_dir.mkdir(parents=True)

        transcript_file = session_dir / "transcript.md"
        transcript_file.write_text(mock_codex_transcript)

        manager = TranscriptManager(backend="codex")
        manager.codex_global_dir = codex_global
        manager.codex_local_dir = tmp_path / "nonexistent"

        # Test loading by session ID
        content = manager.load_transcript_content("codex456")
        assert content == mock_codex_transcript

    def test_load_codex_transcript_extended(self, tmp_path):
        """Test loading Codex transcript_extended.md files."""
        codex_global = tmp_path / ".codex_global" / "transcripts"
        session_dir = codex_global / "2024-01-01-10-00-AM__project__session"
        session_dir.mkdir(parents=True)

        # Only create extended transcript (no standard)
        extended_content = "Extended transcript content"
        (session_dir / "transcript_extended.md").write_text(extended_content)

        manager = TranscriptManager(backend="codex")
        manager.codex_global_dir = codex_global
        manager.codex_local_dir = tmp_path / "nonexistent"

        codex_transcripts = manager._list_codex_transcripts()
        assert len(codex_transcripts) == 1
        assert codex_transcripts[0].name == "transcript_extended.md"

    def test_extract_codex_session_id(self, transcript_manager_instance):
        """Test session ID extraction from Codex directory names."""
        manager = transcript_manager_instance

        # Create mock session directory path
        session_path = Path("2024-01-01-10-00-AM__test-project__abc123def")

        session_id = manager._extract_codex_session_id(session_path)
        assert session_id == "abc123def"

        # Test with insufficient parts
        invalid_path = Path("invalid-format")
        session_id = manager._extract_codex_session_id(invalid_path)
        assert session_id is None


# Test unified functionality


class TestUnifiedFunctionality:
    """Test unified cross-backend functionality."""

    def test_list_transcripts_both_backends(self, mock_dual_backend_setup):
        """Test combined transcript listing from both backends."""
        setup = mock_dual_backend_setup
        tmp_path = setup["tmp_path"]

        with patch("transcript_manager.Path.cwd", return_value=tmp_path):
            manager = TranscriptManager(backend="auto")
            manager.transcripts_dir = setup["claude_transcripts"]
            manager.codex_global_dir = setup["codex_global"]
            manager.codex_local_dir = setup["codex_local"]

            all_transcripts = manager.list_transcripts()

            # Should find transcripts from both backends
            assert len(all_transcripts) >= 2  # At least one from each backend

    def test_backend_filtering(self, mock_dual_backend_setup):
        """Test backend parameter filtering."""
        setup = mock_dual_backend_setup
        tmp_path = setup["tmp_path"]

        # Test Claude-only filtering
        with patch("transcript_manager.Path.cwd", return_value=tmp_path):
            claude_manager = TranscriptManager(backend="claude")
            claude_manager.transcripts_dir = setup["claude_transcripts"]

            claude_transcripts = claude_manager.list_transcripts()
            # Should only include Claude Code transcripts
            assert all(".txt" in str(t) for t in claude_transcripts)

        # Test Codex-only filtering
        with patch("transcript_manager.Path.cwd", return_value=tmp_path):
            codex_manager = TranscriptManager(backend="codex")
            codex_manager.codex_global_dir = setup["codex_global"]
            codex_manager.codex_local_dir = setup["codex_local"]

            codex_transcripts = codex_manager.list_transcripts()
            # Should only include Codex transcripts
            assert all(".md" in str(t) for t in codex_transcripts)


# Test session ID handling


class TestSessionIdHandling:
    """Test session ID normalization and matching."""

    def test_normalize_session_id(self, transcript_manager_instance):
        """Test session ID normalization."""
        manager = transcript_manager_instance

        # Test various session ID formats
        test_cases = [
            ("ABC123-DEF456", "abc123def456"),
            ("abc123def456", "abc123def456"),
            ("ABC-123-DEF-456", "abc123def456"),
            ("a1b2c3d4-e5f6-7890-abcd-ef1234567890", "a1b2c3d4e5f678901234ef1234567890"),
        ]

        for input_id, expected in test_cases:
            result = manager._normalize_session_id(input_id)
            assert result == expected

    def test_fuzzy_session_id_matching(self, tmp_path):
        """Test prefix matching for session IDs."""
        # This would test fuzzy matching functionality
        # once implemented in the main code
        pass


# Test error handling


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_load_nonexistent_transcript(self, transcript_manager_instance):
        """Test error handling for missing transcripts."""
        manager = transcript_manager_instance

        content = manager.load_transcript_content("nonexistent-session")
        assert content is None

    def test_invalid_backend_parameter(self):
        """Test validation of backend parameter."""
        manager = TranscriptManager(backend="invalid")
        # Should default to auto for invalid backend
        assert manager.backend == "auto"

    def test_restore_empty_directory(self, tmp_path):
        """Test handling of no transcripts."""
        empty_transcripts = tmp_path / ".data" / "transcripts"
        empty_transcripts.mkdir(parents=True)

        manager = TranscriptManager(backend="claude")
        manager.transcripts_dir = empty_transcripts

        result = manager.restore_conversation_lineage()
        assert result is None


# Test JSON output


class TestJsonOutput:
    """Test JSON output functionality."""

    def test_list_transcripts_json_combined(self, mock_dual_backend_setup):
        """Test combined JSON output with backend information."""
        # This would test the list_transcripts_json method
        # once implemented in the main code
        pass


# Integration tests


class TestIntegration:
    """Integration tests with other components."""

    def test_manager_with_real_codex_builder(self):
        """Test integration with codex_transcripts_builder.py."""
        # This would test integration once the builder is enhanced
        pass

    def test_manager_with_transcript_exporter(self):
        """Test integration with transcript_exporter.py."""
        # This would test integration once the exporter is complete
        pass


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
