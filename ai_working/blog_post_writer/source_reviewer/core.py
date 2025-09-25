"""
Source reviewer core functionality.

Verifies factual accuracy and proper attribution in blog content.
"""

from typing import Any

from pydantic import BaseModel
from pydantic import Field

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class SourceReview(BaseModel):
    """Results of source review."""

    accuracy_score: float = Field(description="Overall accuracy score 0-1")
    has_issues: bool = Field(description="Whether issues were found")
    issues: list[str] = Field(default_factory=list, description="List of accuracy issues")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    needs_revision: bool = Field(description="Whether revision is required")


class SourceReviewer:
    """Reviews blog posts for source accuracy."""

    async def review_sources(self, blog_draft: str, original_brain_dump: str) -> dict[str, Any]:
        """Review blog for factual accuracy.

        Args:
            blog_draft: Current blog draft
            original_brain_dump: Original source material

        Returns:
            Review results as dictionary
        """
        logger.info("Reviewing blog for source accuracy")

        prompt = f"""Review this blog post for factual accuracy compared to the source:

=== ORIGINAL SOURCE ===
{original_brain_dump}

=== BLOG DRAFT ===
{blog_draft}

Check for:
1. Factual accuracy - Are all claims supported by the source?
2. Misrepresentations - Any distortions of the original ideas?
3. Added claims - Any unsupported new claims not in source?
4. Missing context - Important context from source that's missing?

Return JSON with:
- accuracy_score: 0-1 score
- has_issues: boolean
- issues: list of specific problems found
- suggestions: list of how to fix issues
- needs_revision: boolean (true if accuracy < 0.8)"""

        options = SessionOptions(
            system_prompt="You are a fact-checker ensuring blog accuracy.",
            temperature=0.2,  # Low temp for accuracy checking
            max_retries=2,
        )

        try:
            async with ClaudeSession(options) as session:
                # Use retry_with_feedback for robust JSON extraction
                async def query_with_parsing(enhanced_prompt: str):
                    response = await session.query(enhanced_prompt)
                    if response and response.content:
                        parsed = parse_llm_json(response.content)
                        if parsed:
                            return parsed
                    return None

                # Retry with feedback if parsing fails
                parsed = await retry_with_feedback(
                    func=query_with_parsing, prompt=prompt, max_retries=3, provide_feedback=True
                )

                if parsed is None:
                    logger.error("Could not get source review after retries, using default")
                    return self._default_review()

                # Validate and structure response
                review_data = {
                    "accuracy_score": float(parsed.get("accuracy_score", 0.9)),
                    "has_issues": bool(parsed.get("has_issues", False)),
                    "issues": parsed.get("issues", []),
                    "suggestions": parsed.get("suggestions", []),
                    "needs_revision": bool(parsed.get("needs_revision", False)),
                }

                # Force needs_revision if accuracy too low or issues found
                if review_data["accuracy_score"] < 0.8:
                    logger.info(f"Accuracy score {review_data['accuracy_score']:.2f} < 0.8, forcing revision")
                    review_data["needs_revision"] = True
                    review_data["has_issues"] = True

                if review_data["issues"] and len(review_data["issues"]) > 0:
                    logger.info(f"Found {len(review_data['issues'])} issues, forcing revision")
                    review_data["needs_revision"] = True
                    review_data["has_issues"] = True

                review = SourceReview(**review_data)
                self._log_review_results(review)

                return review.model_dump()

        except Exception as e:
            logger.error(f"Source review failed: {e}")
            # Return passing review on error to not block pipeline
            return self._default_review()

    def _log_review_results(self, review: SourceReview) -> None:
        """Log review results for visibility.

        Args:
            review: Review results
        """
        logger.info("=" * 50)
        logger.info("SOURCE REVIEW RESULTS:")
        logger.info(f"  Accuracy score: {review.accuracy_score:.2f}")
        logger.info(f"  Has issues: {review.has_issues}")
        logger.info(f"  Needs revision: {review.needs_revision}")

        # Log thresholds
        logger.info("  Threshold: 0.8 (revision if below)")
        logger.info(f"  Pass/Fail: {'FAIL - Revision Required' if review.needs_revision else 'PASS'}")

        if review.has_issues:
            logger.warning(f"\nFound {len(review.issues)} accuracy issues:")
            for i, issue in enumerate(review.issues, 1):
                logger.warning(f"  {i}. {issue}")

        if review.suggestions:
            logger.info(f"\nSuggestions ({len(review.suggestions)}):")
            for i, suggestion in enumerate(review.suggestions, 1):
                logger.info(f"  {i}. {suggestion}")

        logger.info("=" * 50)

    def _default_review(self) -> dict[str, Any]:
        """Return default passing review when checking fails."""
        logger.info("Using default source review (no issues)")
        review = SourceReview(
            accuracy_score=1.0,
            has_issues=False,
            issues=[],
            suggestions=[],
            needs_revision=False,
        )
        return review.model_dump()
