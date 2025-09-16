"""Tests for the Amplifier Tool Builder."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from amplifier.tools.tool_builder.exceptions import CCSDKRequiredError
from amplifier.tools.tool_builder.exceptions import SessionError
from amplifier.tools.tool_builder.exceptions import ValidationError
from amplifier.tools.tool_builder.microtask_orchestrator import MicrotaskOrchestrator
from amplifier.tools.tool_builder.microtask_orchestrator import PipelineStage
from amplifier.tools.tool_builder.session_manager import SessionManager
from amplifier.tools.tool_builder.session_manager import ToolBuilderSession


class TestSessionManager:
    """Test session management functionality."""

    def test_create_session(self):
        """Test creating a new session."""
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(Path, "home", return_value=Path(tmpdir)):
            manager = SessionManager()
            session = manager.create_session("test-tool", "Test description")

            assert session.tool_name == "test-tool"
            assert session.description == "Test description"
            assert session.current_stage == "initializing"
            assert len(session.completed_stages) == 0
            assert len(session.id) == 8  # Short ID

    def test_save_and_load_session(self):
        """Test saving and loading a session."""
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(Path, "home", return_value=Path(tmpdir)):
            manager = SessionManager()

            # Create and save session
            session = manager.create_session("test-tool", "Test description")
            session.update_stage("requirements_analysis")
            session.add_metadata("test_key", "test_value")

            # Load session
            loaded = manager.load_session(session.id)

            assert loaded.tool_name == "test-tool"
            assert loaded.current_stage == "requirements_analysis"
            assert loaded.completed_stages == ["initializing"]
            assert loaded.metadata["test_key"] == "test_value"

    def test_list_sessions(self):
        """Test listing all sessions."""
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(Path, "home", return_value=Path(tmpdir)):
            manager = SessionManager()

            # Create multiple sessions
            manager.create_session("tool1", "Description 1")
            manager.create_session("tool2", "Description 2")

            sessions = manager.list_sessions()

            assert len(sessions) == 2
            assert sessions[0].tool_name == "tool2"  # Newest first
            assert sessions[1].tool_name == "tool1"

    def test_session_not_found(self):
        """Test loading non-existent session."""
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(Path, "home", return_value=Path(tmpdir)):
            manager = SessionManager()

            with pytest.raises(SessionError, match="Session not found"):
                manager.load_session("nonexistent")


class TestMicrotaskOrchestrator:
    """Test microtask orchestration."""

    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """Test basic pipeline execution."""
        orchestrator = MicrotaskOrchestrator()

        # Create a mock session
        session = MagicMock(spec=ToolBuilderSession)
        session.update_stage = MagicMock()
        session.save = MagicMock()
        session.generated_modules = []
        session.requirements = None
        session.architecture = None
        session.quality_checks = []
        session.add_metadata = MagicMock()

        # Execute pipeline
        context = await orchestrator.execute_pipeline(session)

        assert context.session == session
        assert len(context.accumulated_results) > 0

        # Verify stages were updated
        assert session.update_stage.called

    @pytest.mark.asyncio
    async def test_pipeline_interruption(self):
        """Test pipeline interruption handling."""
        orchestrator = MicrotaskOrchestrator()

        # Create a mock session
        session = MagicMock(spec=ToolBuilderSession)
        session.update_stage = MagicMock()
        session.add_metadata = MagicMock()
        session.save = MagicMock()

        # Mock a handler that sets interruption
        async def interrupting_handler(context):
            context.interruption_requested = True
            return {"status": "interrupted"}

        orchestrator.stage_handlers[PipelineStage.REQUIREMENTS_ANALYSIS] = interrupting_handler

        # Execute pipeline
        context = await orchestrator.execute_pipeline(session)

        assert context.interruption_requested
        assert session.add_metadata.called_with("interrupted_at", "requirements_analysis")

    def test_stage_progress(self):
        """Test getting stage progress."""
        orchestrator = MicrotaskOrchestrator()

        # Create a mock session
        session = MagicMock(spec=ToolBuilderSession)
        session.completed_stages = ["initializing", "requirements_analysis"]
        session.current_stage = "architecture_design"

        progress = orchestrator.get_stage_progress(session)

        assert progress["completed_stages"] == ["initializing", "requirements_analysis"]
        assert progress["current_stage"] == "architecture_design"
        assert progress["progress_percentage"] == 33  # 2 out of 6 stages
        assert not progress["is_completed"]


class TestRequirementsAnalyzer:
    """Test requirements analysis functionality."""

    def test_cc_sdk_required(self):
        """Test that CC SDK is required."""
        with patch("importlib.util.find_spec", return_value=None):
            from amplifier.tools.tool_builder.requirements_analyzer import RequirementsAnalyzer

            with pytest.raises(CCSDKRequiredError):
                RequirementsAnalyzer()

    @pytest.mark.asyncio
    async def test_parse_requirements_json(self):
        """Test parsing requirements from JSON response."""
        from amplifier.tools.tool_builder.requirements_analyzer import RequirementsAnalyzer

        # Mock CC SDK availability
        with patch("importlib.util.find_spec", return_value=MagicMock()):
            analyzer = RequirementsAnalyzer()

            # Test valid JSON response
            response = json.dumps(
                {
                    "core_functionality": "Test functionality",
                    "inputs": ["input1", "input2"],
                    "outputs": ["output1"],
                    "complexity": "simple",
                    "key_features": ["feature1"],
                }
            )

            result = analyzer._parse_requirements(response)

            assert result["core_functionality"] == "Test functionality"
            assert result["inputs"] == ["input1", "input2"]
            assert result["complexity"] == "simple"

    @pytest.mark.asyncio
    async def test_parse_requirements_with_markdown(self):
        """Test parsing requirements wrapped in markdown."""
        from amplifier.tools.tool_builder.requirements_analyzer import RequirementsAnalyzer

        with patch("importlib.util.find_spec", return_value=MagicMock()):
            analyzer = RequirementsAnalyzer()

            # Test markdown-wrapped response
            response = """```json
{
    "core_functionality": "Test",
    "inputs": [],
    "outputs": [],
    "complexity": "simple",
    "key_features": []
}
```"""

            result = analyzer._parse_requirements(response)

            assert result["core_functionality"] == "Test"
            assert result["complexity"] == "simple"


class TestCLIValidation:
    """Test CLI validation functions."""

    def test_validate_tool_name(self):
        """Test tool name validation."""
        from amplifier.tools.tool_builder.cli import _validate_tool_name

        # Valid names
        _validate_tool_name("my-tool")
        _validate_tool_name("my_tool")
        _validate_tool_name("tool123")

        # Invalid names
        with pytest.raises(ValidationError, match="cannot be empty"):
            _validate_tool_name("")

        with pytest.raises(ValidationError, match="cannot start with a number"):
            _validate_tool_name("123tool")

        with pytest.raises(ValidationError, match="only letters, numbers"):
            _validate_tool_name("my tool!")  # Space and exclamation

    def test_check_cc_sdk_available(self):
        """Test CC SDK availability check."""
        from amplifier.tools.tool_builder.cli import _check_cc_sdk_available

        # Mock claude not found
        with (
            patch("shutil.which", return_value=None),
            patch.object(Path, "exists", return_value=False),
            pytest.raises(CCSDKRequiredError),
        ):
            _check_cc_sdk_available()
