"""Basic tests for repo_analyzer tool."""

from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    from scenarios.repo_analyzer import analysis_engine
    from scenarios.repo_analyzer import completeness_reviewer
    from scenarios.repo_analyzer import grounding_reviewer
    from scenarios.repo_analyzer import human_review_interface
    from scenarios.repo_analyzer import opportunity_generator
    from scenarios.repo_analyzer import philosophy_reviewer
    from scenarios.repo_analyzer import pipeline_orchestrator
    from scenarios.repo_analyzer import repo_processor
    from scenarios.repo_analyzer import state

    # Check main classes exist
    assert hasattr(repo_processor, "RepoProcessor")
    assert hasattr(analysis_engine, "AnalysisEngine")
    assert hasattr(opportunity_generator, "OpportunityGenerator")
    assert hasattr(grounding_reviewer, "GroundingReviewer")
    assert hasattr(philosophy_reviewer, "PhilosophyReviewer")
    assert hasattr(completeness_reviewer, "CompletenessReviewer")
    assert hasattr(human_review_interface, "HumanReviewInterface")
    assert hasattr(pipeline_orchestrator, "PipelineOrchestrator")
    assert hasattr(state, "StateManager")


def test_state_manager():
    """Test state management basics."""
    import tempfile

    from scenarios.repo_analyzer.state import StateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        state_mgr = StateManager(Path(tmpdir) / "test_session")

        # Check initial state
        assert state_mgr.state.stage == "initialized"
        assert state_mgr.state.iteration == 0

        # Test state updates
        state_mgr.update_stage("processing")
        assert state_mgr.state.stage == "processing"

        # Test iteration
        assert state_mgr.increment_iteration()
        assert state_mgr.state.iteration == 1


if __name__ == "__main__":
    test_imports()
    test_state_manager()
    print("✅ Basic tests pass!")
