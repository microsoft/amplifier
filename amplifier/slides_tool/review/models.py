"""
Data models for the presentation review system.

This module defines the data structures used by the review and auto-improvement
functionality. These models serve as the contract between the review components.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_serializer


class SlideIssue(BaseModel):
    """Represents an issue found in a specific slide."""

    slide_index: int = Field(description="Index of the slide with the issue (0-based)")
    issue_type: Literal["content", "formatting", "visual", "readability", "consistency"] = Field(
        description="Category of the issue"
    )
    severity: Literal["critical", "major", "minor", "suggestion"] = Field(description="Severity level of the issue")
    description: str = Field(description="Detailed description of the issue")
    suggestion: str | None = Field(None, description="Suggested fix for the issue")
    location: str | None = Field(None, description="Specific location in slide (e.g., 'title', 'bullet 2')")


class ReviewResult(BaseModel):
    """Result of a presentation review analysis."""

    model_config = ConfigDict()

    overall_score: float = Field(ge=0, le=10, description="Overall quality score (0-10)")
    issues: list[SlideIssue] = Field(default_factory=list, description="List of issues found")
    strengths: list[str] = Field(default_factory=list, description="Positive aspects of the presentation")
    general_feedback: str | None = Field(None, description="General feedback about the presentation")
    needs_revision: bool = Field(description="Whether the presentation needs revision")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the review was conducted")

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime, _info):
        """Serialize datetime to ISO format."""
        return timestamp.isoformat()

    def get_critical_issues(self) -> list[SlideIssue]:
        """Get only critical issues."""
        return [issue for issue in self.issues if issue.severity == "critical"]

    def get_issues_by_slide(self, slide_index: int) -> list[SlideIssue]:
        """Get all issues for a specific slide."""
        return [issue for issue in self.issues if issue.slide_index == slide_index]

    def to_feedback_text(self) -> str:
        """Convert review result to feedback text for revision."""
        feedback_parts = []

        # Add general feedback if present
        if self.general_feedback:
            feedback_parts.append(self.general_feedback)

        # Group issues by slide for clearer feedback
        issues_by_slide = {}
        for issue in self.issues:
            if issue.slide_index not in issues_by_slide:
                issues_by_slide[issue.slide_index] = []
            issues_by_slide[issue.slide_index].append(issue)

        # Format issues as feedback
        if issues_by_slide:
            feedback_parts.append("\nSpecific issues to address:")
            for slide_idx in sorted(issues_by_slide.keys()):
                slide_issues = issues_by_slide[slide_idx]
                feedback_parts.append(f"\nSlide {slide_idx + 1}:")
                for issue in slide_issues:
                    severity_marker = "!" if issue.severity in ["critical", "major"] else "-"
                    feedback_parts.append(f"  {severity_marker} {issue.description}")
                    if issue.suggestion:
                        feedback_parts.append(f"    Suggestion: {issue.suggestion}")

        return "\n".join(feedback_parts)


class ReviewRequest(BaseModel):
    """Request structure for presentation review."""

    presentation_file: str = Field(description="Path to presentation file (HTML or PNG)")
    review_type: Literal["visual", "content", "comprehensive"] = Field(
        "comprehensive", description="Type of review to perform"
    )
    focus_areas: list[str] | None = Field(
        None, description="Specific areas to focus on (e.g., 'readability', 'consistency')"
    )
    strict_mode: bool = Field(False, description="Whether to be strict in evaluation (more issues reported)")


class RevisionIteration(BaseModel):
    """Represents one iteration of the revision process."""

    model_config = ConfigDict()

    iteration: int = Field(description="Iteration number (1-based)")
    review_result: ReviewResult = Field(description="Review result for this iteration")
    revision_applied: bool = Field(description="Whether a revision was applied")
    presentation_file: str | None = Field(None, description="Path to revised presentation")
    improvement_delta: float | None = Field(None, description="Score improvement from previous iteration")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this iteration was completed")

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime, _info):
        """Serialize datetime to ISO format."""
        return timestamp.isoformat()


class AutoImproveRequest(BaseModel):
    """Request structure for auto-improvement process."""

    presentation_file: str = Field(description="Path to initial presentation file")
    max_iterations: int = Field(3, ge=1, le=10, description="Maximum improvement iterations")
    target_score: float = Field(8.0, ge=0, le=10, description="Target quality score to achieve")
    review_type: Literal["visual", "content", "comprehensive"] = Field(
        "comprehensive", description="Type of review to use"
    )
    output_dir: str | None = Field(None, description="Output directory for iterations")
    export_formats: list[Literal["html", "png", "gif"]] = Field(
        default_factory=lambda: ["html", "png"], description="Export formats for each iteration"
    )


class AutoImproveResult(BaseModel):
    """Result of the auto-improvement process."""

    success: bool = Field(description="Whether auto-improvement succeeded")
    iterations: list[RevisionIteration] = Field(default_factory=list, description="List of revision iterations")
    final_score: float | None = Field(None, description="Final quality score achieved")
    final_presentation_file: str | None = Field(None, description="Path to final presentation")
    total_time: float = Field(description="Total time taken in seconds")
    stopped_reason: Literal["target_reached", "max_iterations", "no_improvement", "error"] | None = Field(
        None, description="Reason for stopping the improvement process"
    )
    error: str | None = Field(None, description="Error message if failed")
