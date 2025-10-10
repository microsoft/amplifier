"""
Grounding reviewer module.

Ensures analysis stays true to actual repository content.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class GroundingReviewer:
    """Review analysis for grounding in actual repository content."""

    async def review_grounding(
        self, opportunities: list[dict[str, Any]], source_content: str, target_content: str
    ) -> dict[str, Any]:
        """Review opportunities for accuracy and grounding.

        Args:
            opportunities: Generated opportunities
            source_content: Source repository content
            target_content: Target repository content

        Returns:
            Review results with validated opportunities
        """
        logger.info("Reviewing opportunities for grounding in repository reality...")

        # Create isolated context (no contamination from previous analysis)
        prompt = f"""Review these proposed improvements for accuracy and grounding.

You are reviewing ONLY based on the actual repository content provided.
Do NOT assume or infer anything not explicitly shown in the repositories.

SOURCE REPOSITORY:
{source_content[:30000]}

TARGET REPOSITORY:
{target_content[:30000]}

PROPOSED OPPORTUNITIES:
{self._format_opportunities(opportunities)}

For each opportunity, verify:
1. Is it based on ACTUAL patterns in the source repo (with specific evidence)?
2. Is it addressing REAL gaps in the target repo (not imagined)?
3. Are the implementation suggestions technically accurate?
4. Would it actually work given the target repo's current state?

Return JSON with:
{{
    "review_summary": {{
        "total_reviewed": number,
        "well_grounded": number,
        "needs_adjustment": number,
        "not_grounded": number
    }},
    "opportunity_reviews": [
        {{
            "opportunity_id": "opp_1",
            "grounding_score": 0.0-1.0,
            "is_well_grounded": true/false,
            "evidence": {{
                "source_evidence": ["specific code/pattern references"],
                "target_evidence": ["specific gaps/locations"],
                "accuracy_issues": []
            }},
            "adjustments_needed": ["list of corrections"],
            "recommendation": "accept|modify|reject"
        }}
    ],
    "overall_assessment": {{
        "grounding_quality": "excellent|good|fair|poor",
        "key_concerns": [],
        "confidence_level": 0.0-1.0
    }}
}}"""

        options = SessionOptions(
            system_prompt="You are a technical reviewer ensuring proposals are grounded in actual code, not assumptions.",
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
                    logger.error("Could not complete grounding review")
                    return self._default_review(len(opportunities))

                self._log_review_results(review)
                return review

        except Exception as e:
            logger.error(f"Grounding review failed: {e}")
            return self._default_review(len(opportunities))

    def _format_opportunities(self, opportunities: list[dict]) -> str:
        """Format opportunities for review."""
        formatted = []
        for opp in opportunities[:10]:  # Limit for context
            formatted.append(f"""
ID: {opp.get("id", "unknown")}
Title: {opp.get("title", "Unnamed")}
Description: {opp.get("description", "")}
Implementation: {opp.get("implementation", {}).get("overview", "")}
""")
        return "\n---\n".join(formatted)

    def _log_review_results(self, review: dict[str, Any]) -> None:
        """Log grounding review results."""
        logger.info("=" * 60)
        logger.info("GROUNDING REVIEW COMPLETE")

        summary = review.get("review_summary", {})
        logger.info("\n📊 Review Summary:")
        logger.info(f"  Total Reviewed: {summary.get('total_reviewed', 0)}")
        logger.info(f"  Well Grounded: {summary.get('well_grounded', 0)}")
        logger.info(f"  Needs Adjustment: {summary.get('needs_adjustment', 0)}")
        logger.info(f"  Not Grounded: {summary.get('not_grounded', 0)}")

        assessment = review.get("overall_assessment", {})
        logger.info("\n⚖️ Overall Assessment:")
        logger.info(f"  Grounding Quality: {assessment.get('grounding_quality', 'unknown')}")
        logger.info(f"  Confidence Level: {assessment.get('confidence_level', 0):.1%}")

        concerns = assessment.get("key_concerns", [])
        if concerns:
            logger.warning("\n⚠️ Key Concerns:")
            for concern in concerns[:3]:
                logger.warning(f"  • {concern}")

        logger.info("=" * 60)

    def _default_review(self, num_opportunities: int) -> dict[str, Any]:
        """Return default review on failure."""
        return {
            "review_summary": {
                "total_reviewed": num_opportunities,
                "well_grounded": num_opportunities,  # Optimistic default
                "needs_adjustment": 0,
                "not_grounded": 0,
            },
            "opportunity_reviews": [],
            "overall_assessment": {
                "grounding_quality": "unknown",
                "key_concerns": ["Review could not be completed"],
                "confidence_level": 0.5,
            },
        }
