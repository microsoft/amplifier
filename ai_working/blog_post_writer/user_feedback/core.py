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


class ParsedFeedback(BaseModel):
    """Parsed user feedback with directives."""

    has_feedback: bool = Field(description="Whether user provided feedback")
    is_approved: bool = Field(description="Whether user approved the draft")
    general_comments: list[str] = Field(default_factory=list, description="General feedback")
    specific_requests: list[str] = Field(default_factory=list, description="[Bracket] requests")
    continue_iteration: bool = Field(description="Whether to continue iterating")


class UserFeedbackHandler:
    """Handles user interaction and feedback parsing."""

    def _read_feedback_from_file(self, file_path: Path) -> str:
        """Read the edited draft file and extract bracketed feedback.

        Args:
            file_path: Path to the draft file

        Returns:
            String containing all bracketed feedback
        """
        try:
            if not file_path.exists():
                logger.warning(f"Draft file not found: {file_path}")
                return ""

            content = file_path.read_text()

            # Extract all [bracketed] comments
            bracket_pattern = r"\[([^\]]+)\]"
            matches = re.findall(bracket_pattern, content)

            if matches:
                logger.info(f"Found {len(matches)} bracketed comments in file")
                # Return as bracketed items so parse_feedback can process them
                return "\n".join(f"[{match}]" for match in matches)
            logger.info("No bracketed comments found in file")
            return ""

        except Exception as e:
            logger.error(f"Error reading draft file: {e}")
            return ""

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
        feedback_text = self._read_feedback_from_file(draft_file_path)

        # Parse feedback
        parsed = self.parse_feedback(feedback_text)
        self._log_parsed_feedback(parsed)

        return parsed.model_dump()

    def parse_feedback(self, feedback_text: str) -> ParsedFeedback:
        """Parse user feedback text.

        Args:
            feedback_text: Raw feedback from user

        Returns:
            Structured feedback
        """
        if not feedback_text:
            logger.info("No user feedback provided")
            return ParsedFeedback(
                has_feedback=False,
                is_approved=False,
                general_comments=[],
                specific_requests=[],
                continue_iteration=False,
            )

        # Check for approval
        lower_text = feedback_text.lower()
        is_approved = "approve" in lower_text or "approved" in lower_text or "looks good" in lower_text

        # Check for skip
        if "skip" in lower_text:
            logger.info("User skipped review")
            return ParsedFeedback(
                has_feedback=False,
                is_approved=False,
                general_comments=[],
                specific_requests=[],
                continue_iteration=True,  # Continue without user input
            )

        # Extract [bracket] requests
        bracket_pattern = r"\[([^\]]+)\]"
        specific_requests = re.findall(bracket_pattern, feedback_text)

        # Remove bracket content from general feedback
        general_text = re.sub(bracket_pattern, "", feedback_text).strip()

        # Split general feedback into comments
        general_comments = []
        if general_text:
            # Split by sentences or line breaks
            for line in general_text.split("\n"):
                line = line.strip()
                if line and line.lower() not in ["approve", "approved", "skip"]:
                    general_comments.append(line)

        return ParsedFeedback(
            has_feedback=True,
            is_approved=is_approved,
            general_comments=general_comments,
            specific_requests=specific_requests,
            continue_iteration=not is_approved,  # Continue if not approved
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
                for req in feedback.specific_requests[:3]:
                    logger.info(f"    [→] {req}")
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
        requests = []

        # Add specific bracket requests first (high priority)
        if parsed_feedback.get("specific_requests"):
            requests.extend(parsed_feedback["specific_requests"])

        # Add general comments
        if parsed_feedback.get("general_comments"):
            requests.extend(parsed_feedback["general_comments"])

        return {
            "user_requests": requests,
            "source_issues": [],  # Will be filled by source reviewer
            "style_issues": [],  # Will be filled by style reviewer
        }
