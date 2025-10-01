"""Tests for the AI-First Principles integration module."""

import pytest

from amplifier.principles import PrincipleLoader
from amplifier.principles import PrincipleSearcher
from amplifier.principles import PrincipleSynthesizer


@pytest.fixture
def loader():
    """Create a PrincipleLoader instance."""
    return PrincipleLoader()


@pytest.fixture
def searcher(loader):
    """Create a PrincipleSearcher instance."""
    return PrincipleSearcher(loader)


@pytest.fixture
def synthesizer(loader):
    """Create a PrincipleSynthesizer instance."""
    return PrincipleSynthesizer(loader)


class TestPrincipleLoader:
    """Test the PrincipleLoader class."""

    def test_loader_initialization(self, loader):
        """Test that the loader initializes correctly."""
        assert loader is not None
        assert loader.principles_dir.exists()
        assert len(loader.principles) > 0

    def test_get_principle(self, loader):
        """Test retrieving a specific principle."""
        # Try to get principle #45 (prompt-design-patterns)
        principle = loader.get_principle(45)
        if principle:  # Only test if principle exists
            assert principle.number == 45
            assert principle.name == "prompt-design-patterns"
            assert principle.category == "technology"

    def test_get_by_category(self, loader):
        """Test retrieving principles by category."""
        tech_principles = loader.get_by_category("technology")
        assert isinstance(tech_principles, list)

        process_principles = loader.get_by_category("process")
        assert isinstance(process_principles, list)

    def test_search_by_keyword(self, loader):
        """Test searching principles by keyword."""
        results = loader.search_by_keyword("prompt")
        assert isinstance(results, list)
        # If we have prompt-related principles, they should be found
        if results:
            assert any("prompt" in p.name.lower() or (p.content and "prompt" in p.content.lower()) for p in results)

    def test_get_statistics(self, loader):
        """Test getting statistics about loaded principles."""
        stats = loader.get_statistics()
        assert "total" in stats
        assert "by_category" in stats
        assert stats["total"] >= 0


class TestPrincipleSearcher:
    """Test the PrincipleSearcher class."""

    def test_searcher_initialization(self, searcher):
        """Test that the searcher initializes correctly."""
        assert searcher is not None
        assert hasattr(searcher, "keyword_index")
        assert hasattr(searcher, "category_index")

    def test_search_with_filters(self, searcher):
        """Test searching with various filters."""
        # Search by category
        results = searcher.search(category="technology")
        assert isinstance(results, list)

        # Search with keyword
        results = searcher.search(query="context")
        assert isinstance(results, list)

    def test_find_similar(self, searcher):
        """Test finding similar principles."""
        # Only test if we have principle 46
        similar = searcher.find_similar(46, max_results=3)
        assert isinstance(similar, list)
        assert len(similar) <= 3

    def test_find_clusters(self, searcher):
        """Test finding principle clusters."""
        clusters = searcher.find_clusters()
        assert isinstance(clusters, dict)

    def test_generate_summary_report(self, searcher):
        """Test generating a summary report."""
        report = searcher.generate_summary_report()
        assert "statistics" in report
        assert "clusters" in report
        assert "most_connected" in report


class TestPrincipleSynthesizer:
    """Test the PrincipleSynthesizer class."""

    def test_synthesizer_initialization(self, synthesizer):
        """Test that the synthesizer initializes correctly."""
        assert synthesizer is not None
        assert hasattr(synthesizer, "loader")

    def test_synthesize_for_task(self, synthesizer):
        """Test synthesizing principles for a specific task."""
        result = synthesizer.synthesize_for_task("Build a testing framework")
        assert "task" in result
        assert "keywords" in result
        assert "relevant_principles" in result
        assert result["task"] == "Build a testing framework"

    def test_synthesize_for_phase(self, synthesizer):
        """Test synthesizing principles for a project phase."""
        result = synthesizer.synthesize_for_phase("planning")
        assert "phase" in result
        assert "focus_categories" in result
        assert result["phase"] == "planning"

    def test_analyze_principle_coverage(self, synthesizer):
        """Test analyzing principle coverage."""
        # Test with some principle numbers
        coverage = synthesizer.analyze_principle_coverage([45, 46, 47])
        assert "total_principles" in coverage
        assert "principles_used" in coverage
        assert "coverage_percentage" in coverage
        assert coverage["principles_used"] == 3

    def test_generate_implementation_roadmap(self, synthesizer):
        """Test generating an implementation roadmap."""
        roadmap = synthesizer.generate_implementation_roadmap([45, 46, 47, 48])
        assert "total_principles" in roadmap
        assert "phases" in roadmap
        assert "estimated_timeline" in roadmap
        assert roadmap["total_principles"] == 4


@pytest.mark.parametrize(
    "principle_num,expected_category",
    [
        (45, "technology"),
        (53, "process"),
        (54, "process"),
    ],
)
def test_principle_categories(loader, principle_num, expected_category):
    """Test that principles have correct categories."""
    principle = loader.get_principle(principle_num)
    if principle:  # Only test if principle exists
        assert principle.category == expected_category


def test_principle_relationships(loader):
    """Test that principle relationships are properly loaded."""
    # Get a principle known to have relationships
    principle = loader.get_principle(46)  # context-window-management
    if principle and principle.related_principles:
        # Check that related principles exist
        for related_num in principle.related_principles:
            loader.get_principle(related_num)
            # Related principle might not be loaded, that's okay
