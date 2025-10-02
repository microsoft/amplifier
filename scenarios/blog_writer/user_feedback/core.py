"""
User feedback handling core functionality.

Parses user feedback and extracts actionable directives.
"""

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackItem(BaseModel):
    """A single feedback item with surrounding context."""

    comment: str = Field(description="The bracketed comment text")
    line_number: int = Field(description="Line number where comment appears")
    context_before: list[str] = Field(description="3-5 lines before comment")
    context_after: list[str] = Field(description="3-5 lines after comment")


class ParsedFeedback(BaseModel):
    """Parsed user feedback with directives."""

    has_feedback: bool = Field(description="Whether user provided feedback")
    is_approved: bool = Field(description="Whether user approved the draft")
    general_comments: list[str] = Field(default_factory=list, description="General feedback")
    specific_requests: list[FeedbackItem] = Field(default_factory=list, description="[Bracket] requests with context")
    continue_iteration: bool = Field(description="Whether to continue iterating")


class UserFeedbackHandler:
    """Handles user interaction and feedback parsing."""

    def _read_feedback_from_file(self, file_path: Path) -> list[FeedbackItem]:
        """Read the edited draft file and extract bracketed feedback with context.

        Args:
            file_path: Path to the draft file

        Returns:
            List of FeedbackItem objects with context
        """
        try:
            if not file_path.exists():
                logger.warning(f"Draft file not found: {file_path}")
                return []

            content = file_path.read_text()
            lines = content.split("\n")

            feedback_items = []
            bracket_pattern = r"\[([^\]]+)\]"

            for line_num, line in enumerate(lines):
                matches = re.findall(bracket_pattern, line)
                for match in matches:
                    # Capture context (4 lines before/after)
                    context_lines = 4

                    start_idx = max(0, line_num - context_lines)
                    end_idx = min(len(lines), line_num + context_lines + 1)

                    context_before = lines[start_idx:line_num]
                    context_after = lines[line_num + 1 : end_idx]

                    feedback_items.append(
                        FeedbackItem(
                            comment=match,
                            line_number=line_num + 1,  # 1-indexed for humans
                            context_before=context_before,
                            context_after=context_after,
                        )
                    )

            if feedback_items:
                logger.info(f"Found {len(feedback_items)} bracketed comments with context")
            else:
                logger.info("No bracketed comments found in file")

            return feedback_items

        except Exception as e:
            logger.error(f"Error reading draft file: {e}")
            return []

    def get_user_feedback(
        self, current_draft: str, iteration: int, draft_file_path: Path | None = None
    ) -> dict[str, Any]:
        """Get feedback from user on current draft.

        Args:
            current_draft: Current blog draft
            iteration: Current iteration number
            draft_file_path: Path to saved draft file (for reading user edits)

        Returns:
            Parsed feedback as dictionary
        """
        print("\n" + "=" * 60)
        print(f"ITERATION {iteration} - BLOG DRAFT REVIEW")
        print("=" * 60)

        # Determine draft file path if not provided
        if draft_file_path is None:
            draft_file_path = Path("data") / f"draft_iter_{iteration}.md"

        print(f"\nDraft saved to: {draft_file_path}")
        print("\n📝 INSTRUCTIONS:")
        print("  1. Open the draft file in your editor")
        print("  2. Add [bracketed comments] inline where you want changes")
        print("     Example: 'This paragraph [needs more detail about X]'")
        print("  3. Save the file")
        print("  4. Come back here and:")
        print("     • Type 'done' when you've added comments to the file")
        print("     • Type 'approve' to accept without changes")
        print("     • Type 'skip' to skip user review this iteration")
        print("-" * 60)

        # Wait for user signal
        user_input = input("Your choice: ").strip().lower()

        if user_input in ["approve", "approved"]:
            logger.info("User approved the draft")
            return ParsedFeedback(
                has_feedback=False,
                is_approved=True,
                general_comments=[],
                specific_requests=[],
                continue_iteration=False,
            ).model_dump()

        if user_input == "skip":
            logger.info("User skipped review")
            return ParsedFeedback(
                has_feedback=False,
                is_approved=False,
                general_comments=[],
                specific_requests=[],
                continue_iteration=True,
            ).model_dump()

        # User said 'done' or something else - read the file for bracketed comments
        feedback_items = self._read_feedback_from_file(draft_file_path)

        # Parse feedback
        parsed = self.parse_feedback(feedback_items)
        self._log_parsed_feedback(parsed)

        return parsed.model_dump()

    def parse_feedback(self, feedback_items: list[FeedbackItem]) -> ParsedFeedback:
        """Parse user feedback items.

        Args:
            feedback_items: List of FeedbackItem objects from file

        Returns:
            Structured feedback
        """
        if not feedback_items:
            logger.info("No user feedback provided")
            return ParsedFeedback(
                has_feedback=False,
                is_approved=False,
                general_comments=[],
                specific_requests=[],
                continue_iteration=False,
            )

        # Check if any comment indicates approval
        is_approved = any("approve" in item.comment.lower() for item in feedback_items)

        return ParsedFeedback(
            has_feedback=True,
            is_approved=is_approved,
            general_comments=[],
            specific_requests=feedback_items,
            continue_iteration=not is_approved,
        )

    def _log_parsed_feedback(self, feedback: ParsedFeedback) -> None:
        """Log parsed feedback for visibility.

        Args:
            feedback: Parsed feedback
        """
        if feedback.is_approved:
            logger.info("✓ User approved the draft!")
        elif feedback.has_feedback:
            logger.info("User provided feedback:")
            if feedback.specific_requests:
                logger.info(f"  Specific requests: {len(feedback.specific_requests)}")
                for item in feedback.specific_requests[:3]:
                    logger.info(f"    [→] {item.comment} (line {item.line_number})")
            if feedback.general_comments:
                logger.info(f"  General comments: {len(feedback.general_comments)}")
        else:
            logger.info("No feedback provided")

    def format_feedback_for_revision(self, parsed_feedback: dict[str, Any]) -> dict[str, Any]:
        """Format parsed feedback for blog revision.

        Args:
            parsed_feedback: Parsed feedback dictionary

        Returns:
            Formatted feedback for BlogWriter
        """
        formatted_requests = []

        # Add specific bracket requests with context
        if parsed_feedback.get("specific_requests"):
            for item in parsed_feedback["specific_requests"]:
                # Format with context for LLM
                context_str = []

                if item.get("context_before"):
                    context_str.append("Context before:")
                    context_str.extend(f"  {line}" for line in item["context_before"] if line.strip())
                    context_str.append("")

                context_str.append(f">>> USER FEEDBACK: [{item['comment']}]")
                context_str.append(f">>> (at line {item['line_number']})")
                context_str.append("")

                if item.get("context_after"):
                    context_str.append("Context after:")
                    context_str.extend(f"  {line}" for line in item["context_after"] if line.strip())

                formatted_requests.append("\n".join(context_str))

        # Add general comments
        if parsed_feedback.get("general_comments"):
            formatted_requests.extend(parsed_feedback["general_comments"])

        return {
            "user_requests": formatted_requests,
            "source_issues": [],  # Will be filled by source reviewer
            "style_issues": [],  # Will be filled by style reviewer
        }
