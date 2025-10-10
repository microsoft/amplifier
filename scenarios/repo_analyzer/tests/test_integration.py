"""Integration tests for repo_analyzer pipeline."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scenarios.repo_analyzer.pipeline_orchestrator import PipelineOrchestrator
from scenarios.repo_analyzer.state import StateManager


@pytest.mark.asyncio
async def test_pipeline_basic_flow():
    """Test basic pipeline flow without actual LLM calls."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test repositories
        source_dir = Path(tmpdir) / "source_repo"
        target_dir = Path(tmpdir) / "target_repo"

        source_dir.mkdir()
        target_dir.mkdir()

        # Add minimal content
        (source_dir / "README.md").write_text("# Source Repository\n\nWell-designed patterns here.")
        (source_dir / "main.py").write_text("def main():\n    print('Source code')\n")

        (target_dir / "README.md").write_text("# Target Repository\n\nNeeds improvements.")
        (target_dir / "app.py").write_text("# Main application\npass\n")

        # Initialize pipeline with state
        session_dir = Path(tmpdir) / "session"
        state_mgr = StateManager(session_dir)
        pipeline = PipelineOrchestrator(state_mgr)

        # Mock the LLM-dependent methods
        with patch.object(pipeline.analysis_engine, "analyze_repositories") as mock_analyze:
            mock_analyze.return_value = {
                "patterns": ["Good error handling", "Clean architecture"],
                "gaps": ["Missing tests", "No documentation"],
            }

            with patch.object(pipeline.opportunity_generator, "generate_opportunities") as mock_generate:
                mock_generate.return_value = [
                    {
                        "title": "Add error handling",
                        "description": "Implement comprehensive error handling",
                        "impact": {"priority": "high"},
                        "category": "error_handling",
                    }
                ]

                with patch.object(pipeline.human_interface, "present_opportunities") as mock_human:
                    mock_human.return_value = {"approved": True}

                    # Mock the repo processor to skip actual repomix calls
                    async def mock_process_repo(repo_path, output_name, include_patterns=None, exclude_patterns=None):
                        output_file = pipeline.repo_processor.temp_dir / f"{output_name}.xml"
                        output_file.write_text(f"<repository>{output_name}</repository>")
                        return output_file

                    with patch.object(pipeline.repo_processor, "process_repository", mock_process_repo):
                        result = await pipeline.run(
                            source_path=source_dir, target_path=target_dir, analysis_request="Find improvements"
                        )

                        assert result is True
                        assert state_mgr.is_complete()


@pytest.mark.asyncio
async def test_state_persistence():
    """Test that state can be saved and resumed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session_dir = Path(tmpdir) / "session"

        # First session - partial completion
        state_mgr1 = StateManager(session_dir)
        state_mgr1.update_stage("repos_processed")
        state_mgr1.set_analysis_results({"test": "data"})
        state_mgr1.save()

        # Second session - resume
        state_mgr2 = StateManager(session_dir)
        assert state_mgr2.state.stage == "repos_processed"
        assert state_mgr2.state.analysis_results == {"test": "data"}


def test_feedback_loop_iteration():
    """Test iteration control and limits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_mgr = StateManager(Path(tmpdir) / "session")

        # Test iteration increments
        assert state_mgr.state.iteration == 0
        assert state_mgr.increment_iteration() is True
        assert state_mgr.state.iteration == 1

        # Test max iterations
        state_mgr.state.iteration = 3
        assert state_mgr.increment_iteration() is False  # Exceeds max


if __name__ == "__main__":
    asyncio.run(test_pipeline_basic_flow())
    asyncio.run(test_state_persistence())
    test_feedback_loop_iteration()
    print("✅ Integration tests pass!")
