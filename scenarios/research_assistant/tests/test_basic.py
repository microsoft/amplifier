"""Basic tests for research assistant components."""

import pytest
from research_assistant.models import CredibilityLevel
from research_assistant.models import PreliminaryFindings
from research_assistant.models import ResearchContext
from research_assistant.models import ResearchDepth
from research_assistant.models import ResearchNote
from research_assistant.models import ResearchPhase
from research_assistant.models import ResearchSession
from research_assistant.models import ResearchType
from research_assistant.models import Source
from research_assistant.models import Theme


def test_research_context_creation() -> None:
    """Test creating a research context."""
    context = ResearchContext(
        question="What are the latest AI trends?",
        research_type=ResearchType.TECHNICAL,
        persona="AI researcher",
        depth=ResearchDepth.MODERATE,
        constraints=["Focus on 2024"],
    )

    assert context.question == "What are the latest AI trends?"
    assert context.research_type == ResearchType.TECHNICAL
    assert context.persona == "AI researcher"
    assert context.depth == ResearchDepth.MODERATE
    assert len(context.constraints) == 1


def test_research_context_to_dict() -> None:
    """Test serialization of research context."""
    context = ResearchContext(question="Test question", research_type=ResearchType.GENERAL, depth=ResearchDepth.QUICK)

    data = context.to_dict()

    assert data["question"] == "Test question"
    assert data["research_type"] == "general"
    assert data["depth"] == "quick"

    restored = ResearchContext.from_dict(data)
    assert restored.question == context.question
    assert restored.research_type == context.research_type


def test_source_creation() -> None:
    """Test creating a source."""
    source = Source(
        url="https://example.com",
        title="Test Article",
        content="Test content",
        credibility=CredibilityLevel.HIGH,
        credibility_reasoning="Well-established source",
    )

    assert source.url == "https://example.com"
    assert source.credibility == CredibilityLevel.HIGH
    assert not source.verified


def test_research_note_creation() -> None:
    """Test creating a research note."""
    note = ResearchNote(
        content="Key finding about AI",
        source_url="https://example.com",
        source_title="AI Article",
    )

    assert note.content == "Key finding about AI"
    assert not note.verified
    assert note.verification_notes is None


def test_theme_creation() -> None:
    """Test creating a theme."""
    theme = Theme(
        title="AI Safety",
        description="Research on AI alignment and safety",
        supporting_notes=["Note 1", "Note 2"],
        priority=8,
    )

    assert theme.title == "AI Safety"
    assert theme.priority == 8
    assert len(theme.supporting_notes) == 2
    assert not theme.user_approved


def test_preliminary_findings() -> None:
    """Test preliminary findings structure."""
    findings = PreliminaryFindings()

    source = Source(
        url="https://example.com",
        title="Test",
        content="Content",
        credibility=CredibilityLevel.MEDIUM,
        credibility_reasoning="Test source",
    )

    note = ResearchNote(content="Test note", source_url="https://example.com", source_title="Test")

    findings.sources.append(source)
    findings.notes.append(note)
    findings.search_queries_used.append("test query")

    assert len(findings.sources) == 1
    assert len(findings.notes) == 1
    assert len(findings.search_queries_used) == 1


def test_research_session_creation() -> None:
    """Test creating a research session."""
    session = ResearchSession.create_new("test_session")

    assert session.session_id == "test_session"
    assert session.phase == ResearchPhase.CLARIFICATION
    assert session.context is None
    assert session.preliminary_findings is None


def test_research_session_serialization(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Test session save and load."""
    from pathlib import Path

    workspace = Path(str(tmp_path))
    session = ResearchSession.create_new("test_session")
    session.context = ResearchContext(question="Test?", research_type=ResearchType.GENERAL, depth=ResearchDepth.QUICK)

    session.save(workspace)

    loaded = ResearchSession.load(workspace)

    assert loaded.session_id == session.session_id
    assert loaded.phase == session.phase
    assert loaded.context is not None
    assert loaded.context.question == "Test?"


@pytest.mark.asyncio
async def test_web_scraper_url_validation() -> None:
    """Test URL validation."""
    from research_assistant.components.web_scraper import WebScraper

    scraper = WebScraper()

    assert scraper.is_valid_url("https://example.com")
    assert scraper.is_valid_url("http://example.com")
    assert not scraper.is_valid_url("not-a-url")
    assert not scraper.is_valid_url("ftp://example.com")
