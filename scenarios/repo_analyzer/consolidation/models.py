"""
Data structures for consolidation of chunk analysis results.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class ChunkReference:
    """Reference to a specific chunk and its relevance."""

    chunk_index: int
    start_line: int
    end_line: int
    relevance_score: float  # 0.0 to 1.0
    reason: str  # Why this chunk is relevant
    key_findings: list[str] = field(default_factory=list)


@dataclass
class ChunkAnalysis:
    """Analysis result for a chunk with expanded context."""

    primary_chunk_index: int
    context_indices: list[int]  # Indices of context chunks (±2)
    expanded_content: str  # Combined content of all chunks

    # Analysis results
    opportunities: list[dict[str, Any]] = field(default_factory=list)
    insights: list[dict[str, Any]] = field(default_factory=list)
    patterns: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    total_lines: int = 0
    analysis_focus: str | None = None  # Specific focus for re-analysis


@dataclass
class ConsolidatedResult:
    """Final consolidated analysis result combining all chunks."""

    # Core findings (deduplicated and merged)
    opportunities: list[dict[str, Any]] = field(default_factory=list)
    insights: list[dict[str, Any]] = field(default_factory=list)
    patterns: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)

    # Cross-cutting analysis
    cross_chunk_patterns: list[dict[str, Any]] = field(default_factory=list)
    system_level_insights: list[dict[str, Any]] = field(default_factory=list)

    # Chunk mapping
    chunk_references: list[ChunkReference] = field(default_factory=list)
    analyzed_chunks: list[ChunkAnalysis] = field(default_factory=list)

    # Summary statistics
    total_chunks_analyzed: int = 0
    chunks_with_findings: int = 0
    chunks_reanalyzed: int = 0
    unique_findings_count: int = 0

    # Processing metadata
    processing_time: float = 0.0
    llm_calls_made: int = 0

    def add_finding(self, finding_type: str, finding: dict[str, Any], chunk_ref: ChunkReference | None = None):
        """Add a finding to the appropriate category with deduplication."""

        # Get the appropriate list
        if finding_type == "opportunity":
            target_list = self.opportunities
        elif finding_type == "insight":
            target_list = self.insights
        elif finding_type == "pattern":
            target_list = self.patterns
        elif finding_type == "gap":
            target_list = self.gaps
        else:
            return  # Unknown type

        # Check for duplicates based on title/description
        finding_key = finding.get("title", "") + finding.get("description", "")
        for existing in target_list:
            existing_key = existing.get("title", "") + existing.get("description", "")
            if self._similarity_score(finding_key, existing_key) > 0.8:
                # Merge information if needed
                if chunk_ref and "chunk_refs" in existing:
                    existing["chunk_refs"].append(chunk_ref)
                return  # Skip duplicate

        # Add new finding
        if chunk_ref:
            finding["chunk_refs"] = [chunk_ref]
        target_list.append(finding)
        self.unique_findings_count += 1

    def _similarity_score(self, text1: str, text2: str) -> float:
        """Simple similarity score between two texts (0.0 to 1.0)."""
        if not text1 or not text2:
            return 0.0

        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Calculate Jaccard similarity
        if not words1 and not words2:
            return 1.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def get_high_priority_findings(self, min_priority: int = 7) -> dict[str, list[dict[str, Any]]]:
        """Get all findings with priority >= min_priority."""
        result = {"opportunities": [], "insights": [], "patterns": [], "gaps": []}

        for opp in self.opportunities:
            if opp.get("priority", 0) >= min_priority:
                result["opportunities"].append(opp)

        for insight in self.insights:
            if insight.get("priority", 0) >= min_priority:
                result["insights"].append(insight)

        for pattern in self.patterns:
            if pattern.get("priority", 0) >= min_priority:
                result["patterns"].append(pattern)

        for gap in self.gaps:
            if gap.get("priority", 0) >= min_priority:
                result["gaps"].append(gap)

        return result
