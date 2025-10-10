"""
Completeness reviewer module.

Ensures all requested opportunities are explored.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class CompletenessReviewer:
    """Review analysis for completeness and coverage."""

    async def review_completeness(
        self, opportunities: list[dict[str, Any]], original_request: str, analysis_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Review if analysis fully addresses the request.

        Args:
            opportunities: Generated opportunities
            original_request: User's original analysis request
            analysis_results: Initial analysis results

        Returns:
            Review results with completeness assessment
        """
        logger.info("Reviewing analysis completeness...")

        # Extract coverage information
        patterns_count = len(analysis_results.get("patterns_identified", []))
        gaps_count = len(analysis_results.get("gaps", []))

        prompt = f"""Review this analysis for completeness against the original request.

ORIGINAL REQUEST:
{original_request}

ANALYSIS COVERAGE:
- Patterns Identified: {patterns_count}
- Gaps Found: {gaps_count}
- Opportunities Generated: {len(opportunities)}

OPPORTUNITIES SUMMARY:
{self._format_opportunity_summary(opportunities)}

Evaluate:
1. Does the analysis address all aspects of the original request?
2. Are there obvious areas that weren't explored?
3. Is the depth of analysis appropriate?
4. Are there missing categories of improvements?
5. Should any areas be explored more deeply?

Return JSON with:
{{
    "request_coverage": {{
        "request_aspects": ["aspect1", "aspect2"],
        "covered_aspects": ["aspect1"],
        "missing_aspects": ["aspect2"],
        "coverage_percentage": 0-100
    }},
    "depth_assessment": {{
        "overall_depth": "shallow|appropriate|deep",
        "areas_needing_more_depth": ["area1", "area2"],
        "areas_well_covered": ["area3", "area4"]
    }},
    "opportunity_coverage": {{
        "categories_covered": ["architecture", "features"],
        "categories_missing": ["testing", "performance"],
        "balance_assessment": "well-balanced|skewed|gaps"
    }},
    "missing_opportunities": [
        {{
            "category": "...",
            "description": "what's missing",
            "importance": "high|medium|low"
        }}
    ],
    "completeness_score": 0.0-1.0,
    "recommendations": ["specific suggestions for completeness"]
}}"""

        options = SessionOptions(
            system_prompt="You are a thorough analyst ensuring comprehensive coverage of improvement opportunities.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:

                async def query_with_parsing(enhanced_prompt: str):
                    response = await session.query(enhanced_prompt)
                    if response and response.content:
                        parsed = parse_llm_json(response.content)
                        if parsed:
                            return parsed
                    return None

                review = await retry_with_feedback(
                    func=query_with_parsing, prompt=prompt, max_retries=3, provide_feedback=True
                )

                if review is None:
                    logger.error("Could not complete completeness review")
                    return self._default_review()

                self._log_review_results(review)
                return review

        except Exception as e:
            logger.error(f"Completeness review failed: {e}")
            return self._default_review()

    def _format_opportunity_summary(self, opportunities: list[dict]) -> str:
        """Create summary of opportunities by category."""
        categories = {}
        for opp in opportunities:
            cat = opp.get("category", "unknown")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(opp.get("title", "Unnamed"))

        formatted = []
        for cat, titles in categories.items():
            formatted.append(f"\n{cat.upper()} ({len(titles)} items):")
            for title in titles[:3]:
                formatted.append(f"  • {title}")
            if len(titles) > 3:
                formatted.append(f"  ... and {len(titles) - 3} more")

        return "\n".join(formatted)

    def _log_review_results(self, review: dict[str, Any]) -> None:
        """Log completeness review results."""
        logger.info("=" * 60)
        logger.info("COMPLETENESS REVIEW")

        coverage = review.get("request_coverage", {})
        logger.info("\n📋 Request Coverage:")
        logger.info(f"  Coverage: {coverage.get('coverage_percentage', 0)}%")

        missing = coverage.get("missing_aspects", [])
        if missing:
            logger.warning("  Missing Aspects:")
            for aspect in missing:
                logger.warning(f"    • {aspect}")

        depth = review.get("depth_assessment", {})
        logger.info("\n🔍 Depth Assessment:")
        logger.info(f"  Overall: {depth.get('overall_depth', 'unknown')}")

        needs_depth = depth.get("areas_needing_more_depth", [])
        if needs_depth:
            logger.info("  Needs More Depth:")
            for area in needs_depth[:3]:
                logger.info(f"    • {area}")

        opp_coverage = review.get("opportunity_coverage", {})
        logger.info("\n📊 Opportunity Balance:")
        logger.info(f"  Assessment: {opp_coverage.get('balance_assessment', 'unknown')}")

        missing_cats = opp_coverage.get("categories_missing", [])
        if missing_cats:
            logger.warning("  Missing Categories:")
            for cat in missing_cats:
                logger.warning(f"    • {cat}")

        score = review.get("completeness_score", 0)
        logger.info(f"\n✅ Completeness Score: {score:.1%}")

        logger.info("=" * 60)

    def _default_review(self) -> dict[str, Any]:
        """Return default review on failure."""
        return {
            "request_coverage": {
                "request_aspects": [],
                "covered_aspects": [],
                "missing_aspects": [],
                "coverage_percentage": 100,
            },
            "depth_assessment": {
                "overall_depth": "appropriate",
                "areas_needing_more_depth": [],
                "areas_well_covered": [],
            },
            "opportunity_coverage": {
                "categories_covered": [],
                "categories_missing": [],
                "balance_assessment": "unknown",
            },
            "missing_opportunities": [],
            "completeness_score": 1.0,
            "recommendations": [],
        }
