"""Data models for research assistant."""

import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from pathlib import Path


class ResearchType(str, Enum):
    """Type of research being conducted."""

    PRICING = "pricing"
    PRODUCT_COMPARISON = "product_comparison"
    MARKET_ANALYSIS = "market_analysis"
    POSITIONING = "positioning"
    BRAND_STRATEGY = "brand_strategy"
    TECHNICAL = "technical"
    COMPETITIVE = "competitive"
    GENERAL = "general"


class ResearchDepth(str, Enum):
    """Depth of research to conduct."""

    QUICK = "quick"  # Quick overview, 5-10 sources
    MODERATE = "moderate"  # Standard research, 15-25 sources
    DEEP = "deep"  # Comprehensive analysis, 30+ sources


class ResearchPhase(str, Enum):
    """Current phase of the research workflow."""

    CLARIFICATION = "clarification"
    PRELIMINARY_RESEARCH = "preliminary_research"
    THEME_REFINEMENT = "theme_refinement"
    DEEP_RESEARCH = "deep_research"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"


class CredibilityLevel(str, Enum):
    """Credibility assessment for a source."""

    HIGH = "high"  # Authoritative, well-established sources
    MEDIUM = "medium"  # Reasonable credibility, needs verification
    LOW = "low"  # Questionable or unverified sources


@dataclass
class ResearchContext:
    """Context for the research question and parameters."""

    question: str
    research_type: ResearchType
    persona: str | None = None  # e.g., "product manager", "brand strategist"
    depth: ResearchDepth = ResearchDepth.MODERATE
    constraints: list[str] = field(default_factory=list)  # Additional constraints/focus areas
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchContext":
        """Create from dictionary."""
        return cls(
            question=data["question"],
            research_type=ResearchType(data["research_type"]),
            persona=data.get("persona"),
            depth=ResearchDepth(data["depth"]),
            constraints=data.get("constraints", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )

    def to_prompt_context(self) -> str:
        """Format as context for AI prompts."""
        lines = [
            f"Research Question: {self.question}",
            f"Research Type: {self.research_type.value}",
            f"Research Depth: {self.depth.value}",
        ]
        if self.persona:
            lines.append(f"Researcher Persona: {self.persona}")
        if self.constraints:
            lines.append(f"Constraints: {', '.join(self.constraints)}")
        return "\n".join(lines)


@dataclass
class Source:
    """A web source used in research."""

    url: str
    title: str
    content: str  # Extracted text content
    credibility: CredibilityLevel
    credibility_reasoning: str
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified: bool = False  # Whether facts have been verified

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        """Create from dictionary."""
        return cls(
            url=data["url"],
            title=data["title"],
            content=data["content"],
            credibility=CredibilityLevel(data["credibility"]),
            credibility_reasoning=data["credibility_reasoning"],
            scraped_at=data.get("scraped_at", datetime.now().isoformat()),
            verified=data.get("verified", False),
        )


@dataclass
class ResearchNote:
    """A note extracted from research sources."""

    content: str
    source_url: str
    source_title: str
    verified: bool = False
    verification_notes: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchNote":
        """Create from dictionary."""
        return cls(
            content=data["content"],
            source_url=data["source_url"],
            source_title=data["source_title"],
            verified=data.get("verified", False),
            verification_notes=data.get("verification_notes"),
        )


@dataclass
class Theme:
    """A theme extracted from research."""

    title: str
    description: str
    supporting_notes: list[str] = field(default_factory=list)
    priority: int = 0  # Higher = more important
    user_approved: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Theme":
        """Create from dictionary."""
        return cls(
            title=data["title"],
            description=data["description"],
            supporting_notes=data.get("supporting_notes", []),
            priority=data.get("priority", 0),
            user_approved=data.get("user_approved", False),
        )


@dataclass
class PreliminaryFindings:
    """Results from preliminary research phase."""

    sources: list[Source] = field(default_factory=list)
    notes: list[ResearchNote] = field(default_factory=list)
    search_queries_used: list[str] = field(default_factory=list)
    completed_at: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "sources": [s.to_dict() for s in self.sources],
            "notes": [n.to_dict() for n in self.notes],
            "search_queries_used": self.search_queries_used,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PreliminaryFindings":
        """Create from dictionary."""
        return cls(
            sources=[Source.from_dict(s) for s in data.get("sources", [])],
            notes=[ResearchNote.from_dict(n) for n in data.get("notes", [])],
            search_queries_used=data.get("search_queries_used", []),
            completed_at=data.get("completed_at"),
        )


@dataclass
class DeepResearchFindings:
    """Results from deep research phase."""

    sources: list[Source] = field(default_factory=list)
    notes: list[ResearchNote] = field(default_factory=list)
    themes_researched: list[str] = field(default_factory=list)
    completed_at: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "sources": [s.to_dict() for s in self.sources],
            "notes": [n.to_dict() for n in self.notes],
            "themes_researched": self.themes_researched,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeepResearchFindings":
        """Create from dictionary."""
        return cls(
            sources=[Source.from_dict(s) for s in data.get("sources", [])],
            notes=[ResearchNote.from_dict(n) for n in data.get("notes", [])],
            themes_researched=data.get("themes_researched", []),
            completed_at=data.get("completed_at"),
        )


@dataclass
class ResearchSession:
    """Complete research session state."""

    session_id: str
    phase: ResearchPhase
    context: ResearchContext | None = None
    preliminary_findings: PreliminaryFindings | None = None
    themes: list[Theme] = field(default_factory=list)
    deep_research: DeepResearchFindings | None = None
    report_draft: str | None = None
    final_report: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "context": self.context.to_dict() if self.context else None,
            "preliminary_findings": self.preliminary_findings.to_dict() if self.preliminary_findings else None,
            "themes": [t.to_dict() for t in self.themes],
            "deep_research": self.deep_research.to_dict() if self.deep_research else None,
            "report_draft": self.report_draft,
            "final_report": self.final_report,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchSession":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            phase=ResearchPhase(data["phase"]),
            context=ResearchContext.from_dict(data["context"]) if data.get("context") else None,
            preliminary_findings=(
                PreliminaryFindings.from_dict(data["preliminary_findings"])
                if data.get("preliminary_findings")
                else None
            ),
            themes=[Theme.from_dict(t) for t in data.get("themes", [])],
            deep_research=(
                DeepResearchFindings.from_dict(data["deep_research"]) if data.get("deep_research") else None
            ),
            report_draft=data.get("report_draft"),
            final_report=data.get("final_report"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

    def save(self, workspace_dir: Path) -> None:
        """Save session to disk."""
        session_file = workspace_dir / "session.json"
        self.updated_at = datetime.now().isoformat()
        with open(session_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, workspace_dir: Path) -> "ResearchSession":
        """Load session from disk."""
        session_file = workspace_dir / "session.json"
        with open(session_file) as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def create_new(cls, session_id: str) -> "ResearchSession":
        """Create a new research session."""
        return cls(session_id=session_id, phase=ResearchPhase.CLARIFICATION)
