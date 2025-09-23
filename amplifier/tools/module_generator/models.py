"""Data models for the idea_synthesizer module."""

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class ProvenanceItem(BaseModel):
    """Tracks which summary inspired an idea."""

    summary_path: str = Field(..., description="Path to the summary file")
    summary_hash: str = Field(..., description="SHA256 hash of the summary content")


class IdeaRecord(BaseModel):
    """Complete data model for a synthesized idea."""

    id: str = Field(..., description="Stable slug based on title and content hash")
    title: str = Field(..., description="Title of the idea")
    summary: str = Field(..., description="1-3 paragraph summary of the idea")
    rationale: str = Field(..., description="Why this idea is non-trivial and new")
    novelty_score: float = Field(..., ge=0.0, le=1.0, description="Model-estimated novelty")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Estimated impact")
    effort_score: float = Field(..., ge=0.0, le=1.0, description="Estimated effort")
    tags: list[str] | None = Field(default=None, description="Optional tags")
    provenance: list[ProvenanceItem] = Field(..., min_length=1, description="Source summaries")
    source_refs: list[str] | None = Field(default=None, description="Original .md files")
    constraints: str | None = Field(default=None, description="Risks/assumptions")
    created_at: str = Field(..., description="RFC3339 timestamp")
    source_manifest_hash: str = Field(..., description="Hash of summary set considered")

    @field_validator("created_at")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Ensure timestamp is RFC3339 formatted."""
        try:
            # Parse and reformat to ensure RFC3339
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
            # If already valid RFC3339, return as-is
            return v

    @field_validator("provenance")
    @classmethod
    def validate_provenance(cls, v: list[ProvenanceItem]) -> list[ProvenanceItem]:
        """Ensure at least one provenance item exists."""
        if not v:
            raise ValueError("Every idea must have at least one provenance item")
        return v


class SynthesisRequest(BaseModel):
    """Request model for AI synthesis."""

    summaries: list[dict[str, str]] = Field(..., description="Compressed summaries")
    instruction: str = Field(..., description="Synthesis instruction")
    max_ideas: int = Field(default=5, description="Maximum ideas to generate")
    partition_id: str = Field(..., description="ID of this partition")


class SynthesisResponse(BaseModel):
    """Response model from AI synthesis."""

    ideas: list[IdeaRecord] = Field(..., description="Generated ideas")
    partition_id: str = Field(..., description="ID of the partition processed")
    token_usage: dict[str, int] | None = Field(default=None, description="Token usage stats")


class PartitionInfo(BaseModel):
    """Information about a summary partition."""

    partition_id: str = Field(..., description="Unique partition identifier")
    summary_paths: list[str] = Field(..., description="Paths in this partition")
    summary_count: int = Field(..., description="Number of summaries")
    estimated_tokens: int = Field(..., description="Estimated token count")


class SynthesisMetrics(BaseModel):
    """Metrics for a synthesis run."""

    run_id: str = Field(..., description="Run identifier")
    total_summaries: int = Field(..., description="Total summaries processed")
    total_partitions: int = Field(..., description="Number of partitions created")
    total_ideas_generated: int = Field(..., description="Ideas before deduplication")
    total_ideas_after_dedup: int = Field(..., description="Ideas after deduplication")
    duplicate_count: int = Field(..., description="Number of duplicates removed")
    total_duration_seconds: float = Field(..., description="Total processing time")
    partition_latencies: dict[str, float] = Field(..., description="Per-partition timing")
    total_tokens_used: int | None = Field(default=None, description="Total token usage")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    timestamp: str = Field(..., description="When metrics were recorded")


class SynthesisConfig(BaseModel):
    """Configuration for synthesis run."""

    summaries_dir: str = Field(..., description="Directory containing summaries")
    limit: int | None = Field(default=None, description="Max summaries to process")
    filters: dict[str, list[str]] | None = Field(default=None, description="Include/exclude patterns")
    run_id: str | None = Field(default=None, description="Execution ID")
    output_dir: str = Field(default="ideas", description="Output directory")
    log_dir: str = Field(default="logs/idea_synthesizer", description="Log directory")
    max_summaries_per_partition: int = Field(default=10, description="Max per partition")
    min_novelty_threshold: float = Field(default=0.3, description="Min novelty score")
    dedup_similarity_threshold: float = Field(default=0.85, description="Dedup threshold")
    max_retries: int = Field(default=2, description="Max synthesis retries")
    quarantine_dir: str = Field(default="ideas/_quarantine", description="Failed items dir")


class SummaryInfo(BaseModel):
    """Information about a loaded summary."""

    path: str = Field(..., description="File path")
    content_hash: str = Field(..., description="SHA256 hash of content")
    title: str = Field(..., description="Summary title")
    key_points: list[str] = Field(..., description="Key points extracted")
    word_count: int = Field(..., description="Approximate word count")


class SynthesisState(BaseModel):
    """State for resumable synthesis."""

    run_id: str = Field(..., description="Current run ID")
    source_manifest_hash: str = Field(..., description="Hash of input summaries")
    completed_partitions: list[str] = Field(default_factory=list, description="Finished partitions")
    generated_ideas: list[str] = Field(default_factory=list, description="Generated idea IDs")
    last_updated: str = Field(..., description="Last update timestamp")
    status: str = Field(default="in_progress", description="Current status")


# Error classes
class NoSummariesError(Exception):
    """Raised when no summaries are found."""

    pass


class ParseError(Exception):
    """Raised when summary parsing fails."""

    pass


class WriteError(Exception):
    """Raised when file writing fails."""

    pass
