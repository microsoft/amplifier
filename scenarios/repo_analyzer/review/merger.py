"""
Feedback merger using AI.

Merges human feedback from markdown files back into JSON opportunities.
"""

import re
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.core import ClaudeSession
from amplifier.ccsdk_toolkit.core import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackMerger:
    """Merge human feedback into opportunities using AI."""

    async def merge_feedback(
        self, markdown_files: list[Path], original_opportunities: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Merge feedback from edited markdown files.

        Args:
            markdown_files: List of markdown file paths with feedback
            original_opportunities: Original opportunity dictionaries

        Returns:
            Tuple of (enhanced_opportunities, rejected_opportunities)
        """
        enhanced = []
        rejected = []

        # Create mapping of opportunities by index
        opp_map = dict(enumerate(original_opportunities, 1))

        for filepath in markdown_files:
            try:
                # Extract index from filename (e.g., "001-title.md")
                filename = filepath.name
                index = int(filename.split("-")[0])
                original = opp_map.get(index)

                if not original:
                    logger.warning(f"No original opportunity found for index {index}")
                    continue

                # Read markdown content
                content = filepath.read_text(encoding="utf-8")

                # Extract feedback section
                feedback = self._extract_feedback(content)

                if not feedback or feedback.strip() == "":
                    # No feedback provided, keep original
                    enhanced.append(original)
                    continue

                # Check for rejection
                if self._is_rejection(feedback):
                    logger.info(f"Opportunity {index} marked for rejection")
                    rejected.append({"index": index, "opportunity": original, "reason": feedback})
                    continue

                # Merge feedback using AI
                merged = await self._ai_merge(original, feedback, content)
                if merged:
                    enhanced.append(merged)
                else:
                    # Fallback to original if merge fails
                    logger.warning(f"Failed to merge feedback for opportunity {index}, using original")
                    enhanced.append(original)

            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
                # Keep original on error
                if index in opp_map:
                    enhanced.append(opp_map[index])

        logger.info(f"Processed {len(enhanced)} opportunities, {len(rejected)} rejected")
        return enhanced, rejected

    def _extract_feedback(self, markdown_content: str) -> str:
        """Extract feedback section from markdown."""
        # Look for content between FEEDBACK START and FEEDBACK END comments
        pattern = r"<!-- FEEDBACK START -->(.+?)<!-- FEEDBACK END -->"
        match = re.search(pattern, markdown_content, re.DOTALL)

        if match:
            feedback = match.group(1).strip()
            # Remove the default placeholder text if unchanged
            placeholder_lines = [
                "*[Please add your feedback here. You can:*",
                "- *Accept as-is*",
                "- *Suggest modifications*",
                "- *Mark for rejection with reason*",
                "- *Request more details*",
                "- *Adjust priority or effort estimates]*",
            ]

            for line in placeholder_lines:
                feedback = feedback.replace(line, "")

            return feedback.strip()

        return ""

    def _is_rejection(self, feedback: str) -> bool:
        """Check if feedback indicates rejection."""
        rejection_keywords = ["reject", "remove", "not applicable", "not relevant", "skip this", "don't implement"]
        feedback_lower = feedback.lower()
        return any(keyword in feedback_lower for keyword in rejection_keywords)

    async def _ai_merge(self, original: dict[str, Any], feedback: str, full_content: str) -> dict[str, Any] | None:
        """Use AI to intelligently merge feedback into opportunity."""
        prompt = f"""You are helping merge human feedback into a software improvement opportunity.

ORIGINAL OPPORTUNITY (JSON):
{original}

HUMAN FEEDBACK:
{feedback}

FULL REVIEWED DOCUMENT:
{full_content}

Please merge the human feedback into the opportunity JSON structure. The human may have:
- Adjusted priority, effort, or complexity estimates
- Modified the description or implementation approach
- Added or removed implementation steps
- Clarified benefits or risks
- Provided additional context or requirements

Return ONLY a valid JSON object with the merged opportunity. Preserve all original fields and structure, but update values based on the feedback. If the feedback suggests major changes, rewrite sections as needed while maintaining the JSON schema.

Important:
- Maintain the exact same JSON structure as the original
- All original fields must be present in the output
- Apply the human's feedback thoughtfully
- If feedback is vague, make reasonable interpretations
- Return ONLY the JSON object, no explanations"""

        try:
            options = SessionOptions(
                system_prompt="You are a precise JSON merger for software opportunities.", retry_attempts=2
            )

            async with ClaudeSession(options) as session:
                response = await session.query(prompt)

                if response.error:
                    logger.error(f"AI merge error: {response.error}")
                    return None

                if not response.content:
                    logger.error("Empty response from AI merge")
                    return None

                # Parse JSON from response
                parsed = parse_llm_json(response.content)

                # Ensure we got a dict (not a list)
                if isinstance(parsed, dict):
                    merged = parsed
                    # Ensure critical fields are preserved
                    if "title" not in merged and "title" in original:
                        merged["title"] = original["title"]
                    if "category" not in merged and "category" in original:
                        merged["category"] = original["category"]

                    # Add feedback tracking
                    merged["human_reviewed"] = True
                    merged["feedback_applied"] = feedback[:200] if len(feedback) > 200 else feedback

                    return merged

                logger.warning("Failed to parse merged JSON")
                return None

        except Exception as e:
            logger.error(f"AI merge failed: {e}")
            return None
