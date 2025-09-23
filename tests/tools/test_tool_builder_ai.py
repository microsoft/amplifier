"""Tests for the AI-first Tool Builder architecture."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from amplifier.tools.tool_builder import StateManager
from amplifier.tools.tool_builder import ToolBuilderPipeline
from amplifier.tools.tool_builder import ToolBuilderState


class TestToolBuilderState:
    """Test state management for tool builder."""

    def test_create_state(self):
        """Test creating a new tool builder state."""
        state = ToolBuilderState(tool_name="test-tool", description="Test tool description")

        assert state.tool_name == "test-tool"
        assert state.description == "Test tool description"
        assert state.current_stage is None
        assert len(state.completed_stages) == 0
        assert state.get_resume_point() == "requirements"

    def test_mark_stage_complete(self):
        """Test marking stages as complete."""
        state = ToolBuilderState(tool_name="test-tool", description="Test description")

        # Mark requirements complete
        state.mark_stage_complete("requirements", {"data": "test"})
        assert "requirements" in state.completed_stages
        assert state.stage_outputs["requirements"] == {"data": "test"}
        assert state.get_resume_point() == "analysis"

        # Mark analysis complete
        state.mark_stage_complete("analysis", {"analysis": "data"})
        assert state.get_resume_point() == "generation"

    def test_save_and_load_state(self):
        """Test saving and loading state from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_state.json"

            # Create and save state
            state = ToolBuilderState(tool_name="test-tool", description="Test description")
            state.mark_stage_complete("requirements", {"test": "data"})
            state.save(filepath)

            # Load state
            loaded = ToolBuilderState.load(filepath)
            assert loaded.tool_name == "test-tool"
            assert "requirements" in loaded.completed_stages
            assert loaded.stage_outputs["requirements"] == {"test": "data"}


class TestStateManager:
    """Test state manager functionality."""

    def test_create_and_load_state(self):
        """Test creating and loading state via manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(Path(tmpdir))

            # Create state
            state = manager.create_state("test-tool", "Test description")
            assert state.tool_name == "test-tool"

            # Load state
            loaded = manager.load_state("test-tool")
            assert loaded is not None
            assert loaded.tool_name == "test-tool"

    def test_list_incomplete_tools(self):
        """Test listing incomplete tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(Path(tmpdir))

            # Create incomplete tool
            state1 = manager.create_state("incomplete-tool", "Incomplete")
            state1.mark_stage_complete("requirements", {})
            manager.save_checkpoint(state1)

            # Create complete tool
            state2 = manager.create_state("complete-tool", "Complete")
            for stage in ["requirements", "analysis", "generation", "validation"]:
                state2.mark_stage_complete(stage, {})
            manager.save_checkpoint(state2)

            # Check incomplete list
            incomplete = manager.list_incomplete_tools()
            assert "incomplete-tool" in incomplete
            assert "complete-tool" not in incomplete


class TestToolBuilderPipeline:
    """Test the main pipeline orchestrator."""

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ToolBuilderPipeline(state_dir=Path(tmpdir))

            assert pipeline.state_manager is not None
            assert pipeline.requirements_analyzer is not None
            assert pipeline.metacognitive_analyzer is not None
            assert pipeline.code_generator is not None
            assert pipeline.quality_validator is not None

    @pytest.mark.asyncio
    async def test_pipeline_with_mocked_stages(self):
        """Test pipeline execution with mocked AI stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ToolBuilderPipeline(state_dir=Path(tmpdir))

            # Mock all AI stages
            with (
                patch.object(
                    pipeline.requirements_analyzer,
                    "analyze",
                    return_value={"purpose": "test", "core_functionality": ["feature1"]},
                ),
                patch.object(
                    pipeline.metacognitive_analyzer,
                    "analyze",
                    return_value={"implementation_strategy": {"approach": "functional"}},
                ),
                patch.object(pipeline.code_generator, "generate", return_value={"tool.py": "# Generated code"}),
                patch.object(
                    pipeline.quality_validator, "validate", return_value={"overall_quality": "good", "issues": []}
                ),
            ):
                result = await pipeline.build_tool(
                    tool_name="test-tool", description="Test description", skip_validation=False
                )

                assert result["tool_name"] == "test-tool"
                assert "tool.py" in result["generated_code"]
                assert result["validation"]["overall_quality"] == "good"

    def test_get_tool_status(self):
        """Test getting tool build status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ToolBuilderPipeline(state_dir=Path(tmpdir))

            # Create a state
            state = pipeline.state_manager.create_state("test-tool", "Test")
            state.mark_stage_complete("requirements", {})
            pipeline.state_manager.save_checkpoint(state)

            # Get status
            status = pipeline.get_tool_status("test-tool")
            assert status is not None
            assert status["tool_name"] == "test-tool"
            assert "requirements" in status["completed_stages"]
            assert status["next_stage"] == "analysis"
