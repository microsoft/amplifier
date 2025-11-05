"""Data models for claim validation"""

import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))
from pydantic import BaseModel
from pydantic import Field


class ClaimValidation(BaseModel):
    """Validation result for a single claim"""

    claim: str = Field(..., description="The claim being validated")
    supports: bool = Field(default=False, description="Whether the claim is supported by memories")
    contradicts: bool = Field(default=False, description="Whether the claim contradicts memories")
    confidence: float = Field(default=0.0, description="Confidence score 0-1")
    supporting_memory: Any | None = Field(default=None, description="Memory that supports the claim")
    conflicting_memory: Any | None = Field(default=None, description="Memory that contradicts the claim")
    evidence: list[str] = Field(default_factory=list, description="Evidence text from memories")
    verdict: str = Field(default="unknown", description="Verdict: supported, contradicted, or unknown")


class ValidationResult(BaseModel):
    """Overall validation result for text containing multiple claims"""

    text: str = Field(..., description="Original text that was validated")
    claims: list[ClaimValidation] = Field(default_factory=list, description="Individual claim validations")
    has_contradictions: bool = Field(default=False, description="Whether any claims contradict memories")
    overall_confidence: float = Field(default=0.0, description="Average confidence across all claims")
