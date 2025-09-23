"""Tests for the Amplifier Tool Builder - AI-first architecture."""

# Import new AI-first architecture components
from amplifier.tools.tool_builder import StateManager
from amplifier.tools.tool_builder import ToolBuilderPipeline
from amplifier.tools.tool_builder import ToolBuilderState


class TestAIFirstArchitecture:
    """Test the new AI-first tool builder architecture."""

    def test_imports_work(self):
        """Test that new architecture components can be imported."""
        assert ToolBuilderPipeline is not None
        assert ToolBuilderState is not None
        assert StateManager is not None

    def test_state_creation(self):
        """Test basic state creation."""
        state = ToolBuilderState(tool_name="test-tool", description="Test description")
        assert state.tool_name == "test-tool"
        assert state.description == "Test description"

    def test_placeholder_for_legacy_tests(self):
        """Placeholder test confirming migration to AI-first architecture."""
        # Legacy tests have been replaced with test_tool_builder_ai.py
        # This file kept for backwards compatibility
        assert True
