"""
Tests for Claude session awareness functionality.
"""

import json
import os
import time
from unittest.mock import patch

import pytest

from amplifier.claude.session_awareness import SessionActivity
from amplifier.claude.session_awareness import SessionAwareness
from amplifier.claude.session_awareness import SessionInfo


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory for testing."""
    return tmp_path


@pytest.fixture
def session_awareness(temp_project_dir):
    """Create a SessionAwareness instance with a temporary directory."""
    return SessionAwareness(project_root=temp_project_dir)


class TestSessionActivity:
    """Tests for SessionActivity dataclass."""

    def test_create_activity(self):
        """Test creating a session activity."""
        activity = SessionActivity(
            session_id="test-session", timestamp=time.time(), action="Edit", details="Modified file.py"
        )
        assert activity.session_id == "test-session"
        assert activity.action == "Edit"
        assert activity.details == "Modified file.py"

    def test_activity_without_details(self):
        """Test creating activity without details."""
        activity = SessionActivity(session_id="test-session", timestamp=time.time(), action="Read")
        assert activity.details is None


class TestSessionInfo:
    """Tests for SessionInfo dataclass."""

    def test_create_session_info(self):
        """Test creating session info."""
        session = SessionInfo(session_id="test-session", pid=12345, started=time.time(), last_seen=time.time())
        assert session.session_id == "test-session"
        assert session.pid == 12345
        assert session.activities == []

    def test_is_stale(self):
        """Test stale session detection."""
        old_time = time.time() - 400  # More than 5 minutes ago
        session = SessionInfo(session_id="old-session", pid=12345, started=old_time, last_seen=old_time)
        assert session.is_stale is True

        recent_session = SessionInfo(session_id="recent-session", pid=54321, started=time.time(), last_seen=time.time())
        assert recent_session.is_stale is False


class TestSessionAwareness:
    """Tests for SessionAwareness class."""

    def test_initialization(self, session_awareness, temp_project_dir):
        """Test session awareness initialization."""
        assert session_awareness.project_root == temp_project_dir
        assert session_awareness.data_dir == temp_project_dir / ".data" / "session_awareness"
        assert session_awareness.data_dir.exists()

    def test_register_activity(self, session_awareness):
        """Test registering an activity."""
        session_awareness.register_activity("Test", "Running tests")

        # Check that session was saved
        assert session_awareness.sessions_file.exists()

        # Load and verify
        with open(session_awareness.sessions_file) as f:
            data = json.load(f)

        assert session_awareness.session_id in data
        session = data[session_awareness.session_id]
        assert len(session["activities"]) > 0
        assert session["activities"][-1]["action"] == "Test"

    def test_get_active_sessions(self, session_awareness):
        """Test getting active sessions."""
        # Register activities from multiple sessions
        session_awareness.register_activity("Session1", "Activity 1")

        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "session-2"}):
            sa2 = SessionAwareness(project_root=session_awareness.project_root)
            sa2.register_activity("Session2", "Activity 2")

        active = session_awareness.get_active_sessions()
        assert len(active) == 2
        session_ids = {s.session_id for s in active}
        assert session_awareness.session_id in session_ids
        assert "session-2" in session_ids

    def test_stale_session_cleanup(self, session_awareness):
        """Test that stale sessions are cleaned up."""
        # Create an old session
        old_sessions = {
            "stale-session": {
                "session_id": "stale-session",
                "pid": 99999,
                "started": time.time() - 600,
                "last_seen": time.time() - 600,  # 10 minutes ago
                "activities": [],
            }
        }

        # Save the old session
        with open(session_awareness.sessions_file, "w") as f:
            json.dump(old_sessions, f)

        # Register new activity (should clean up stale)
        session_awareness.register_activity("New", "Activity")

        # Check that stale session was removed
        with open(session_awareness.sessions_file) as f:
            data = json.load(f)

        assert "stale-session" not in data
        assert session_awareness.session_id in data

    def test_get_recent_activity(self, session_awareness):
        """Test getting recent activity."""
        # Register some activities
        for i in range(5):
            session_awareness.register_activity(f"Action{i}", f"Details {i}")
            time.sleep(0.01)  # Small delay to ensure different timestamps

        activities = session_awareness.get_recent_activity(3)
        assert len(activities) <= 3

        # Should be in reverse chronological order
        if len(activities) > 1:
            assert activities[0].timestamp >= activities[1].timestamp

    def test_get_status(self, session_awareness):
        """Test getting comprehensive status."""
        session_awareness.register_activity("Status Test", "Testing status")

        status = session_awareness.get_status()

        assert status["current_session"] == session_awareness.session_id
        assert status["active_sessions"] >= 1
        assert len(status["sessions"]) >= 1

        # Find our session in the list
        our_session = next(s for s in status["sessions"] if s["id"] == session_awareness.session_id)
        assert our_session["last_activity"] == "Status Test"

    def test_broadcast_message(self, session_awareness):
        """Test broadcasting a message."""
        session_awareness.broadcast_message("Test broadcast")

        # Should be recorded as an activity
        activities = session_awareness.get_recent_activity(1)
        assert len(activities) == 1
        assert activities[0].action == "Broadcast"
        assert activities[0].details == "Test broadcast"

    def test_activity_log_trimming(self, session_awareness, monkeypatch):
        """Test that activity log is trimmed to max size."""
        # Set a small max size for testing
        monkeypatch.setattr("amplifier.claude.session_awareness.MAX_ACTIVITY_LOG_SIZE", 5)

        # Write more activities than max
        for i in range(10):
            activity = SessionActivity(session_id=f"session-{i}", timestamp=time.time(), action=f"Action{i}")
            session_awareness._log_activity(activity)

        # Trigger trimming
        session_awareness._trim_activity_log()

        # Check that log was trimmed
        with open(session_awareness.activity_log) as f:
            lines = f.readlines()

        assert len(lines) == 5  # Should be trimmed to max

    @patch("amplifier.claude.session_awareness.logger")
    def test_error_handling(self, mock_logger, temp_project_dir):
        """Test error handling in various methods."""

        sa = SessionAwareness(project_root=temp_project_dir)

        # Test handling of corrupted sessions file
        sa.sessions_file.write_text("invalid json")
        sessions = sa._load_sessions()
        assert sessions == {}
        mock_logger.warning.assert_called()

        # Test handling of write errors
        sa.sessions_file.chmod(0o444)  # Read-only
        sa._save_sessions({"test": SessionInfo("test", 123, 0, 0)})
        mock_logger.error.assert_called()
