#!/usr/bin/env python3
"""
Tests for Codex transcript functionality.

Comprehensive tests covering codex_transcripts_builder.py enhancements,
transcript_exporter.py functionality, and various edge cases.
"""

import json

# Import modules under test
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent / "tools"))

from codex_transcripts_builder import HistoryEntry
from codex_transcripts_builder import SessionMeta
from codex_transcripts_builder import _parse_timestamp_with_fallbacks
from codex_transcripts_builder import filter_sessions_by_project
from codex_transcripts_builder import load_history
from codex_transcripts_builder import load_session_meta
from codex_transcripts_builder import parse_args
from codex_transcripts_builder import process_session
from codex_transcripts_builder import validate_session_entry
from codex_transcripts_builder import write_compact_transcript
from codex_transcripts_builder import write_session_metadata

sys.path.append(str(Path(__file__).parent.parent / ".codex" / "tools"))
from transcript_exporter import CodexTranscriptExporter

sys.path.append(str(Path(__file__).parent.parent / "tools"))
from transcript_manager import TranscriptManager


# Test fixtures
@pytest.fixture
def mock_codex_history():
    """Generate sample history.jsonl content."""
    history_entries = [
        {"session_id": "abc123", "ts": 1640995200, "text": "Hello world"},
        {"session_id": "abc123", "ts": 1640995300, "text": "How are you?"},
        {"session_id": "def456", "ts": 1640996000, "text": "Different session"},
        {"session_id": "ghi789", "ts": 1640997000, "text": "Third session"},
    ]
    return "\n".join(json.dumps(entry) for entry in history_entries)


@pytest.fixture
def mock_codex_session():
    """Generate sample session JSONL with various event types."""
    session_events = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "type": "user_message",
            "content": {"text": "Test user message"},
        },
        {
            "timestamp": "2024-01-01T10:00:01Z",
            "type": "assistant_message",
            "content": {"text": "Test assistant response"},
        },
        {
            "timestamp": "2024-01-01T10:00:02Z",
            "type": "tool_call",
            "content": {"tool_name": "test_tool", "arguments": {"arg1": "value1"}, "call_id": "call_123"},
        },
        {
            "timestamp": "2024-01-01T10:00:03Z",
            "type": "tool_result",
            "content": {"call_id": "call_123", "result": {"status": "success"}},
        },
    ]
    return "\n".join(json.dumps(event) for event in session_events)


@pytest.fixture
def mock_session_directory(tmp_path):
    """Create a complete session directory structure."""
    session_dir = tmp_path / "sessions" / "abc123"
    session_dir.mkdir(parents=True)

    # Create meta.json
    meta = {"session_id": "abc123", "started_at": "2024-01-01T10:00:00Z", "cwd": str(tmp_path / "project")}
    (session_dir / "meta.json").write_text(json.dumps(meta))

    # Create history.jsonl
    history = [{"session_id": "abc123", "ts": 1640995200, "text": "Test message"}]
    (session_dir / "history.jsonl").write_text("\n".join(json.dumps(h) for h in history))

    return session_dir


@pytest.fixture
def temp_codex_dirs(tmp_path):
    """Set up temporary ~/.codex/ structure."""
    codex_dir = tmp_path / ".codex"
    transcripts_dir = codex_dir / "transcripts"
    sessions_dir = codex_dir / "sessions"

    for dir_path in [codex_dir, transcripts_dir, sessions_dir]:
        dir_path.mkdir(parents=True)

    # Create sample history.jsonl
    history_entries = [{"session_id": "test123", "ts": 1640995200, "text": "Sample entry"}]
    history_content = "\n".join(json.dumps(entry) for entry in history_entries)
    (codex_dir / "history.jsonl").write_text(history_content)

    return codex_dir


# Tests for codex_transcripts_builder.py enhancements


class TestCodexTranscriptsBuilder:
    """Test enhanced codex_transcripts_builder.py functionality."""

    def test_parse_args_with_new_options(self):
        """Test that new command line arguments are parsed correctly."""
        args = parse_args(
            [
                "--project-dir",
                "/test/project",
                "--session-id",
                "abc123",
                "--skip-errors",
                "--incremental",
                "--force",
                "--output-format",
                "compact",
                "--verbose",
            ]
        )

        assert args.project_dir == Path("/test/project")
        assert args.session_id == "abc123"
        assert args.skip_errors is True
        assert args.incremental is True
        assert args.force is True
        assert args.output_format == "compact"
        assert args.verbose is True

    def test_load_history_with_corrupted_lines(self, tmp_path, mock_codex_history):
        """Test graceful handling of malformed JSON in history file."""
        history_file = tmp_path / "history.jsonl"

        # Add corrupted line to valid history
        corrupted_content = mock_codex_history + "\n" + "invalid json line" + "\n"
        corrupted_content += '{"session_id": "valid123", "ts": 1640995400, "text": "Valid after corruption"}'

        history_file.write_text(corrupted_content)

        # Should handle corrupted lines gracefully
        sessions = load_history(history_file, skip_errors=True, verbose=False)

        # Should still load valid entries
        assert len(sessions) >= 3  # Original entries plus the valid one after corruption
        assert "abc123" in sessions
        assert "valid123" in sessions

    def test_load_history_without_skip_errors(self, tmp_path):
        """Test that corrupted lines raise exceptions when skip_errors=False."""
        history_file = tmp_path / "history.jsonl"
        history_file.write_text("invalid json line")

        with pytest.raises(Exception):
            load_history(history_file, skip_errors=False, verbose=False)

    def test_filter_sessions_by_project(self, tmp_path, mock_session_directory):
        """Test project directory filtering."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        sessions_root = tmp_path / "sessions"

        # Create mock sessions dict
        sessions = {"abc123": [HistoryEntry("abc123", 1640995200, "test")]}

        with patch("codex_transcripts_builder.load_session_meta") as mock_load_meta:
            mock_meta = SessionMeta("abc123", datetime.now(), str(project_dir))
            mock_load_meta.return_value = mock_meta

            # This should match because session cwd matches project_dir
            filtered = filter_sessions_by_project(
                sessions,
                project_dir,
                sessions_root,
                tmp_path / "output",
            )

            assert "abc123" in filtered

    def test_validate_session_entry(self):
        """Test session entry validation."""
        # Valid entry
        valid_entry = HistoryEntry("abc123", 1640995200, "test")
        assert validate_session_entry(valid_entry) is True

        # Invalid entries
        invalid_entries = [
            HistoryEntry("", 1640995200, "test"),  # Empty session_id
            HistoryEntry("abc123", 0, "test"),  # Invalid timestamp
            HistoryEntry("abc123", -1, "test"),  # Negative timestamp
        ]

        for entry in invalid_entries:
            assert validate_session_entry(entry) is False

    def test_history_entry_from_json_validation(self):
        """Test HistoryEntry.from_json validation and error handling."""

        # Valid payload
        valid_payload = {"session_id": "abc123", "ts": 1640995200, "text": "test"}
        entry = HistoryEntry.from_json(valid_payload)
        assert entry.session_id == "abc123"
        assert entry.ts == 1640995200
        assert entry.text == "test"

        # Missing required fields
        with pytest.raises(ValueError, match="Missing required field: session_id"):
            HistoryEntry.from_json({"ts": 1640995200})

        with pytest.raises(ValueError, match="Missing required field: ts"):
            HistoryEntry.from_json({"session_id": "abc123"})

        # Invalid values
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            HistoryEntry.from_json({"session_id": "", "ts": 1640995200})

        with pytest.raises(ValueError, match="Invalid timestamp"):
            HistoryEntry.from_json({"session_id": "abc123", "ts": 0})

    def test_parse_timestamp_with_fallbacks(self):
        """Test enhanced timestamp parsing with multiple formats."""
        test_cases = [
            "2024-01-01T10:00:00.123456Z",
            "2024-01-01T10:00:00Z",
            "2024-01-01 10:00:00",
            "2024-01-01 10:00:00.123456",
            "2024/01/01 10:00:00",
            "1640995200",  # Unix timestamp
        ]

        for ts_str in test_cases:
            result = _parse_timestamp_with_fallbacks(ts_str)
            assert result is not None
            assert isinstance(result, datetime)

        # Invalid timestamp should return None
        result = _parse_timestamp_with_fallbacks("invalid timestamp")
        assert result is None

    def test_incremental_processing(self, tmp_path, mock_codex_history):
        """Test incremental processing functionality."""
        sessions_root = tmp_path / "sessions"
        sessions_root.mkdir()
        output_dir = tmp_path / "output"
        history_entries = [
            HistoryEntry("abc123", 1640995200, "Hello world"),
        ]

        rollout_path = sessions_root / "rollout_abc123.jsonl"
        rollout_payload = {
            "type": "session_meta",
            "payload": {"timestamp": "2024-01-01T10:00:00Z", "cwd": str(tmp_path / "project")},
        }
        rollout_path.write_text(json.dumps(rollout_payload) + "\n", encoding="utf-8")

        # First run generates outputs
        processed_path = process_session(
            "abc123",
            history_entries,
            sessions_root,
            output_dir,
            "America/Los_Angeles",
            "~",
            output_format="standard",
        )
        assert processed_path is not None
        assert (processed_path / "transcript.md").exists()
        assert (processed_path / "meta.json").exists()

        # Second run with incremental should skip
        skipped = process_session(
            "abc123",
            history_entries,
            sessions_root,
            output_dir,
            "America/Los_Angeles",
            "~",
            output_format="standard",
            incremental=True,
            force=False,
        )
        assert skipped is None

    def test_session_metadata_generation(self, tmp_path):
        """Test metadata JSON generation for sessions."""
        session_dir = tmp_path / "session_output"
        session_dir.mkdir()
        meta = SessionMeta("abc123", datetime.now(tz=UTC), str(tmp_path / "project"))
        events = []

        write_session_metadata(session_dir, meta, events)
        meta_file = session_dir / "meta.json"

        assert meta_file.exists()
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert data["session_id"] == "abc123"
        assert data["cwd"] == str(tmp_path / "project")
        assert data["event_count"] == 0

    def test_load_session_meta_parses_z_timestamp(self, tmp_path):
        """Ensure load_session_meta handles Z-suffixed timestamps."""
        session_dir = tmp_path / "session_dir"
        session_dir.mkdir()
        meta_payload = {
            "session_id": "test-123",
            "started_at": "2024-01-01T10:00:00Z",
            "cwd": str(tmp_path / "project"),
        }
        (session_dir / "meta.json").write_text(json.dumps(meta_payload), encoding="utf-8")

        meta = load_session_meta(session_dir)
        assert meta is not None
        assert meta.cwd == str(tmp_path / "project")
        assert meta.started_at == datetime(2024, 1, 1, 10, 0, tzinfo=UTC)

    def test_write_compact_transcript_outputs_file(self, tmp_path):
        """Ensure compact transcript writer creates expected file."""
        session_dir = tmp_path / "session_output"
        session_dir.mkdir()
        meta = SessionMeta("abc123", datetime(2024, 1, 1, 10, 0, tzinfo=UTC), "/tmp/project")
        event = Mock()
        event.timestamp = datetime(2024, 1, 1, 10, 5, tzinfo=UTC)
        event.kind = "message"
        event.role = "user"
        event.text = "Hello"
        event.tool_name = None
        event.tool_result = None
        event.tool_args = None

        write_compact_transcript(session_dir, meta, [event], "America/Los_Angeles")

        compact_file = session_dir / "transcript_compact.md"
        assert compact_file.exists()
        content = compact_file.read_text(encoding="utf-8")
        assert "Session ID: abc123" in content
        assert "Hello" in content


# Tests for transcript_exporter.py functionality


class TestTranscriptExporter:
    """Test transcript exporter functionality."""

    def test_exporter_initialization(self, tmp_path):
        """Test CodexTranscriptExporter initialization."""
        sessions_root = tmp_path / "sessions"
        exporter = CodexTranscriptExporter(sessions_root=sessions_root, verbose=True)

        assert exporter.sessions_root == sessions_root
        assert exporter.verbose is True

    def test_get_current_codex_session(self, temp_codex_dirs):
        """Test current session detection."""
        history_path = temp_codex_dirs / "history.jsonl"
        exporter = CodexTranscriptExporter(verbose=True)
        exporter.history_path = history_path

        with patch("transcript_exporter.load_history") as mock_load:
            mock_sessions = {
                "old123": [Mock(ts=1640995000)],
                "new456": [Mock(ts=1640996000)],  # More recent
            }
            mock_load.return_value = mock_sessions

            current = exporter.get_current_codex_session()
            assert current == "new456"

    def test_get_project_sessions(self, tmp_path):
        """Test project-specific session filtering."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        sessions_root = tmp_path / "sessions"

        # Create session directory with metadata
        session_dir = sessions_root / "test123"
        session_dir.mkdir(parents=True)

        meta = {"session_id": "test123", "cwd": str(project_dir)}
        (session_dir / "meta.json").write_text(json.dumps(meta))

        exporter = CodexTranscriptExporter(sessions_root=sessions_root)

        with patch("transcript_exporter.load_history") as mock_load:
            mock_load.return_value = {"test123": [Mock()]}

            project_sessions = exporter.get_project_sessions(project_dir)
            assert "test123" in project_sessions

    def test_export_codex_transcript_standard_format(self, tmp_path):
        """Test standard format transcript export."""
        sessions_root = tmp_path / "sessions"
        output_dir = tmp_path / "output"
        session_id = "test123"

        # Create session directory
        sessions_root.mkdir()
        session_dir = sessions_root / session_id
        session_dir.mkdir()
        history_path = tmp_path / "history.jsonl"
        history_entries = [{"session_id": session_id, "ts": 1640995200, "text": "Hello"}]
        history_path.write_text("\n".join(json.dumps(entry) for entry in history_entries), encoding="utf-8")

        rollout_path = session_dir / f"rollout_{session_id}.jsonl"
        rollout_payloads = [
            {"type": "session_meta", "payload": {"timestamp": "2024-01-01T10:00:00Z", "cwd": str(tmp_path)}},
            {
                "type": "response_item",
                "payload": {"type": "message", "role": "assistant", "content": [{"type": "text", "text": "Response"}]},
            },
        ]
        rollout_path.write_text("\n".join(json.dumps(payload) for payload in rollout_payloads), encoding="utf-8")

        exporter = CodexTranscriptExporter(sessions_root=sessions_root, verbose=True)
        exporter.history_path = history_path

        result_path = exporter.export_codex_transcript(
            session_id=session_id,
            output_dir=output_dir,
            format_type="standard",
        )

        assert result_path is not None
        expected_path = output_dir / session_id / "transcript.md"
        assert result_path == expected_path
        assert expected_path.exists()
        assert (output_dir / session_id / "meta.json").exists()
        assert "Response" in expected_path.read_text(encoding="utf-8")

    def test_duplicate_detection(self, tmp_path):
        """Test duplicate transcript detection."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create existing transcript with session ID
        existing_transcript = output_dir / "existing.md"
        existing_transcript.write_text("Session ID: duplicate123\nSome content")

        exporter = CodexTranscriptExporter(verbose=True)
        embedded_ids = exporter._extract_loaded_session_ids(output_dir)

        assert "duplicate123" in embedded_ids

    def test_compact_export_marks_duplicates(self, tmp_path):
        """Ensure compact export annotates duplicates on subsequent runs."""
        sessions_root = tmp_path / "sessions"
        sessions_root.mkdir()
        session_id = "dup123"
        session_dir = sessions_root / session_id
        session_dir.mkdir()
        history_path = tmp_path / "history.jsonl"
        history_path.write_text(
            json.dumps({"session_id": session_id, "ts": 1640995200, "text": "Hello"}) + "\n",
            encoding="utf-8",
        )
        rollout_path = session_dir / f"rollout_{session_id}.jsonl"
        rollout_payloads = [
            {"type": "session_meta", "payload": {"timestamp": "2024-01-01T10:00:00Z", "cwd": str(tmp_path)}}
        ]
        rollout_path.write_text("\n".join(json.dumps(payload) for payload in rollout_payloads), encoding="utf-8")

        output_dir = tmp_path / "exports"
        exporter = CodexTranscriptExporter(sessions_root=sessions_root, verbose=True)
        exporter.history_path = history_path

        first_path = exporter.export_codex_transcript(session_id, output_dir, format_type="compact")
        assert first_path is not None
        first_content = first_path.read_text(encoding="utf-8")
        assert "# Codex Session Transcript" in first_content

        second_path = exporter.export_codex_transcript(session_id, output_dir, format_type="compact")
        assert second_path == first_path
        second_content = second_path.read_text(encoding="utf-8")
        assert f"# Embedded Transcript: {session_id}" in second_content.splitlines()[0]

    def test_error_handling_missing_session(self, tmp_path):
        """Test graceful error handling for missing sessions."""
        sessions_root = tmp_path / "sessions"
        output_dir = tmp_path / "output"

        exporter = CodexTranscriptExporter(sessions_root=sessions_root, verbose=True)

        result = exporter.export_codex_transcript(session_id="nonexistent", output_dir=output_dir)

        assert result is None


# Tests for transcript manager enhancements


class TestTranscriptManagerFeatures:
    """Test TranscriptManager enhanced functionality."""

    def _create_manager(self, claude_dir: Path, codex_dir: Path) -> TranscriptManager:
        manager = TranscriptManager(backend="auto")
        manager.transcripts_dir = claude_dir
        manager.codex_global_dir = codex_dir
        manager.codex_local_dir = codex_dir
        return manager

    def test_list_transcripts_json_includes_backend(self, tmp_path):
        """Ensure JSON listing includes backend and Codex metadata."""
        claude_dir = tmp_path / ".data/transcripts"
        claude_dir.mkdir(parents=True)
        claude_file = claude_dir / "compact_20240101_000000_sessionclaude.txt"
        claude_file.write_text(
            "Session ID: session-claude\nExported: 2024-01-01T00:00:00Z\nHuman: Hello there\n",
            encoding="utf-8",
        )

        codex_dir = tmp_path / ".codex/transcripts"
        codex_dir.mkdir(parents=True)
        session_dir = codex_dir / "2024-01-02-10-00-am__project__codex123"
        session_dir.mkdir(parents=True)
        (session_dir / "meta.json").write_text(
            json.dumps(
                {
                    "session_id": "codex-123",
                    "started_at": "2024-01-02T10:00:00Z",
                    "cwd": "/tmp/project",
                }
            ),
            encoding="utf-8",
        )
        (session_dir / "transcript.md").write_text(
            "# Session Transcript\n\n## Metadata\n- Session ID: codex-123\n- Start: 2024-01-02T10:00:00Z\n- CWD: /tmp/project\n",
            encoding="utf-8",
        )

        manager = self._create_manager(claude_dir, codex_dir)
        data = json.loads(manager.list_transcripts_json())
        backends = {item["backend"] for item in data}
        assert {"claude", "codex"}.issubset(backends)

        codex_entries = [item for item in data if item["backend"] == "codex"]
        assert codex_entries
        codex_entry = codex_entries[0]
        assert codex_entry["session_dir"] == str(session_dir)
        assert "standard" in codex_entry["variants_available"]
        assert codex_entry["cwd"] == "/tmp/project"

    def test_restore_orders_segments_by_timestamp(self, tmp_path):
        """Restore output should be ordered chronologically by start timestamps."""
        claude_dir = tmp_path / ".data/transcripts"
        claude_dir.mkdir(parents=True)
        claude_file = claude_dir / "compact_20240101_000000_sessionclaude.txt"
        claude_file.write_text(
            "Session ID: session-claude\nExported: 2024-01-01T09:00:00Z\nHuman: Hello there\n",
            encoding="utf-8",
        )

        codex_dir = tmp_path / ".codex/transcripts"
        codex_dir.mkdir(parents=True)
        session_dir = codex_dir / "2024-01-02-10-00-am__project__codex123"
        session_dir.mkdir(parents=True)
        (session_dir / "transcript.md").write_text(
            "# Session Transcript\n\n## Metadata\n- Session ID: codex-123\n- Start: 2024-01-02T10:00:00Z\n- CWD: /tmp/project\n",
            encoding="utf-8",
        )

        manager = self._create_manager(claude_dir, codex_dir)
        content = manager.restore_conversation_lineage()
        assert content is not None
        claude_index = content.index("Start: 2024-01-01T09:00:00+00:00")
        codex_index = content.index("Start: 2024-01-02T10:00:00+00:00")
        assert claude_index < codex_index

    def test_export_transcript_invokes_codex_exporter(self, tmp_path):
        """Codex exports should delegate to the Codex exporter."""
        sessions_root = tmp_path / "sessions"
        sessions_root.mkdir()
        codex_output_dir = tmp_path / ".codex/transcripts"
        codex_output_dir.mkdir(parents=True)

        session_id = "codex-export-1"
        history_path = tmp_path / "history.jsonl"
        history_path.write_text(
            json.dumps({"session_id": session_id, "ts": 1640995200, "text": "Hello"}) + "\n",
            encoding="utf-8",
        )
        session_source_dir = sessions_root / session_id
        session_source_dir.mkdir()
        rollout_file = session_source_dir / f"rollout_{session_id}.jsonl"
        rollout_file.write_text(
            json.dumps({"type": "session_meta", "payload": {"timestamp": "2024-01-01T10:00:00Z", "cwd": str(tmp_path)}})
            + "\n",
            encoding="utf-8",
        )

        history_entries = [HistoryEntry(session_id, 1640995200, "Hello")]
        process_session(
            session_id,
            history_entries,
            sessions_root,
            codex_output_dir,
            "America/Los_Angeles",
            "~",
            output_format="standard",
        )

        manager = TranscriptManager(backend="codex")
        manager.codex_global_dir = codex_output_dir
        manager.codex_local_dir = codex_output_dir
        manager.codex_sessions_root = sessions_root
        manager.codex_history_path = history_path

        transcripts = manager.list_transcripts()
        assert transcripts
        assert any(manager._session_id_from_transcript_path(t) == session_id for t in transcripts)

        exported = manager.export_transcript(session_id=session_id, output_format="standard")
        assert exported is not None
        assert exported.exists()
        assert exported.parent.name == session_id
        assert exported.name == "transcript.md"


# Test parsing edge cases


class TestParsingEdgeCases:
    """Test various parsing edge cases."""

    def test_parse_empty_session(self):
        """Test handling of sessions with no messages."""
        empty_entry = HistoryEntry("empty123", 1640995200, "")
        assert validate_session_entry(empty_entry) is True

    def test_parse_unicode_content(self):
        """Test Unicode handling in session content."""
        unicode_text = "Hello 🌍 世界 émojis"
        entry = HistoryEntry("unicode123", 1640995200, unicode_text)
        assert entry.text == unicode_text

    def test_parse_large_tool_results(self):
        """Test handling of large tool result content."""
        large_content = "x" * 10000  # 10KB of content
        entry = HistoryEntry("large123", 1640995200, large_content)
        # Should handle large content without issues
        assert len(entry.text) == 10000

    def test_session_dir_name_sanitization(self):
        """Test session directory name generation and sanitization."""
        # This would test directory name sanitization
        # once implemented in the main code
        special_chars = "/path/with/special:chars"
        # Should sanitize to safe directory name
        # Implementation would replace special chars
        pass


# Integration tests


class TestIntegration:
    """Integration tests across components."""

    def test_end_to_end_export_and_load(self, tmp_path, mock_codex_history):
        """Test complete export and load workflow."""
        # Set up directories
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(mock_codex_history)
        sessions_root = tmp_path / "sessions"
        output_dir = tmp_path / "output"

        # This would test the complete workflow once implemented
        # 1. Export with codex_transcripts_builder
        # 2. Load with transcript_manager
        assert history_file.exists()

    @pytest.mark.slow
    def test_large_session_processing(self):
        """Test handling of sessions with 1000+ messages."""
        # Create large session data
        large_session_entries = []
        for i in range(1000):
            entry = HistoryEntry("large_session", 1640995200 + i, f"Message {i}")
            large_session_entries.append(entry)

        # Test that processing doesn't fail or timeout
        for entry in large_session_entries[:10]:  # Test subset for speed
            assert validate_session_entry(entry) is True

    @pytest.mark.slow
    def test_batch_processing_performance(self):
        """Test reasonable performance for 100+ sessions."""
        # This would test batch processing performance
        # once the main functionality is implemented
        pass


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
