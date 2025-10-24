"""Data models for competitive analysis pipeline.

This module defines the JSON contracts (the "studs") between pipeline stages.
Each model represents data passed between stages via JSON checkpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class CompanyResearch(BaseModel):
    """Research findings for a single company/product."""

    name: str = Field(description="Company or product name")
    findings: list[str] = Field(description="Key research findings")
    sources: list[str] = Field(description="Source URLs")


class ResearchResult(BaseModel):
    """Output from research stage (research.json)."""

    timestamp: str = Field(description="ISO 8601 timestamp")
    companies: list[CompanyResearch] = Field(description="Research for each entity")

    @classmethod
    def create(cls, companies: list[CompanyResearch]) -> "ResearchResult":
        """Create ResearchResult with current timestamp."""
        return cls(timestamp=datetime.now().isoformat(), companies=companies)


class FrameworkAnalysis(BaseModel):
    """Analysis result from a single framework.

    Structure is flexible - frameworks return different data shapes.
    """

    framework_name: str = Field(description="Framework that produced this analysis")
    analysis: dict[str, Any] = Field(description="Framework-specific analysis data")


class AnalysisResult(BaseModel):
    """Output from analysis stage (analysis.json)."""

    timestamp: str = Field(description="ISO 8601 timestamp")
    frameworks: dict[str, dict[str, Any]] = Field(description="Analysis results keyed by framework name")

    @classmethod
    def create(cls, frameworks: dict[str, dict[str, Any]]) -> "AnalysisResult":
        """Create AnalysisResult with current timestamp."""
        return cls(timestamp=datetime.now().isoformat(), frameworks=frameworks)


class SynthesisResult(BaseModel):
    """Output from synthesis stage (synthesis.json).

    Note: Deferred to Iteration 2.
    """

    timestamp: str = Field(description="ISO 8601 timestamp")
    key_insights: list[str] = Field(description="Cross-framework insights")
    recommendations: list[str] = Field(description="Strategic recommendations")

    @classmethod
    def create(cls, key_insights: list[str], recommendations: list[str]) -> "SynthesisResult":
        """Create SynthesisResult with current timestamp."""
        return cls(timestamp=datetime.now().isoformat(), key_insights=key_insights, recommendations=recommendations)
