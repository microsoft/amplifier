"""
Philosophy reviewer module.

Ensures suggestions align with target repository patterns and philosophy.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class PhilosophyReviewer:
    """Review opportunities for philosophical alignment."""

    async def review_philosophy(
        self, opportunities: list[dict[str, Any]], target_content: str, target_philosophy: str | None = None
    ) -> dict[str, Any]:
        """Review opportunities for alignment with target philosophy.

        Args:
            opportunities: Generated opportunities
            target_content: Target repository content
            target_philosophy: Optional explicit philosophy statement

        Returns:
            Review results with philosophy alignment assessment
        """
        logger.info("Reviewing opportunities for philosophical alignment...")

        philosophy_context = target_philosophy or "Infer from the codebase patterns"

        # Create isolated context for philosophy review
        prompt = f"""Review these proposed improvements for philosophical alignment.

TARGET REPOSITORY PHILOSOPHY:
{philosophy_context}

TARGET REPOSITORY CODE (to understand existing patterns):
{target_content[:30000]}

PROPOSED OPPORTUNITIES:
{self._format_opportunities(opportunities)}

Evaluate each opportunity against the target repository's:
1. Architectural patterns and principles
2. Code style and conventions
3. Complexity tolerance
4. Technology choices
5. Development philosophy

Consider:
- Would this fit naturally or feel foreign?
- Does it respect existing patterns or fight them?
- Is the complexity appropriate for this codebase?
- Does it align with apparent team values?

Return JSON with:
{{
    "philosophy_assessment": {{
        "detected_principles": ["principles observed in target repo"],
        "detected_patterns": ["architectural patterns in use"],
        "complexity_level": "simple|moderate|complex",
        "development_style": "description of style"
    }},
    "opportunity_alignments": [
        {{
            "opportunity_id": "opp_1",
            "alignment_score": 0.0-1.0,
            "fits_naturally": true/false,
            "conflicts": ["list of philosophical conflicts"],
            "adaptations_needed": ["how to better align with philosophy"],
            "recommendation": "accept|adapt|reconsider"
        }}
    ],
    "alignment_summary": {{
        "well_aligned": number,
        "needs_adaptation": number,
        "misaligned": number,
        "overall_fit": "excellent|good|fair|poor"
    }},
    "key_recommendations": ["strategic recommendations for alignment"]
}}"""

        options = SessionOptions(
            system_prompt="You are a software philosophy expert assessing cultural and architectural fit.",
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
                    logger.error("Could not complete philosophy review")
                    return self._default_review(len(opportunities))

                self._log_review_results(review)
                return review

        except Exception as e:
            logger.error(f"Philosophy review failed: {e}")
            return self._default_review(len(opportunities))

    def _format_opportunities(self, opportunities: list[dict]) -> str:
        """Format opportunities for review."""
        formatted = []
        for opp in opportunities[:10]:
            formatted.append(f"""
ID: {opp.get("id", "unknown")}
Title: {opp.get("title", "Unnamed")}
Category: {opp.get("category", "unknown")}
Complexity: {opp.get("implementation", {}).get("complexity", "unknown")}
Approach: {opp.get("implementation", {}).get("overview", "")}
""")
        return "\n---\n".join(formatted)

    def _log_review_results(self, review: dict[str, Any]) -> None:
        """Log philosophy review results."""
        logger.info("=" * 60)
        logger.info("PHILOSOPHY REVIEW COMPLETE")

        assessment = review.get("philosophy_assessment", {})
        logger.info("\n🎯 Detected Philosophy:")

        principles = assessment.get("detected_principles", [])
        if principles:
            logger.info("  Principles:")
            for principle in principles[:3]:
                logger.info(f"    • {principle}")

        logger.info(f"  Complexity Level: {assessment.get('complexity_level', 'unknown')}")
        logger.info(f"  Style: {assessment.get('development_style', 'not detected')}")

        summary = review.get("alignment_summary", {})
        logger.info("\n📊 Alignment Summary:")
        logger.info(f"  Well Aligned: {summary.get('well_aligned', 0)}")
        logger.info(f"  Needs Adaptation: {summary.get('needs_adaptation', 0)}")
        logger.info(f"  Misaligned: {summary.get('misaligned', 0)}")
        logger.info(f"  Overall Fit: {summary.get('overall_fit', 'unknown')}")

        recommendations = review.get("key_recommendations", [])
        if recommendations:
            logger.info("\n💡 Key Recommendations:")
            for rec in recommendations[:3]:
                logger.info(f"  • {rec}")

        logger.info("=" * 60)

    def _default_review(self, num_opportunities: int) -> dict[str, Any]:
        """Return default review on failure."""
        return {
            "philosophy_assessment": {
                "detected_principles": [],
                "detected_patterns": [],
                "complexity_level": "unknown",
                "development_style": "unknown",
            },
            "opportunity_alignments": [],
            "alignment_summary": {
                "well_aligned": num_opportunities,
                "needs_adaptation": 0,
                "misaligned": 0,
                "overall_fit": "unknown",
            },
            "key_recommendations": [],
        }
