"""Competitive analysis tool for comparing two entities.

Multi-stage pipeline architecture:
1. Research: Web research and data gathering
2. Analysis: Apply analytical frameworks (Porter's Five Forces, SWOT)
3. Format: Generate audience-specific reports

Usage:
    # CLI
    python -m ai_working.competitive_analysis "Entity1" "Entity2"

    # Programmatic
    from ai_working.competitive_analysis import run_research_async, run_analysis_async, run_format_async
"""

from .models import AnalysisResult
from .models import CompanyResearch
from .models import ResearchResult
from .stages.analysis import run_analysis_async
from .stages.format import run_format_async
from .stages.research import run_research_async

__all__ = [
    "CompanyResearch",
    "ResearchResult",
    "AnalysisResult",
    "run_research_async",
    "run_analysis_async",
    "run_format_async",
]
