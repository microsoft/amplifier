"""Human feedback collection for tips synthesis."""

import asyncio
import re
from pathlib import Path

from amplifier.ccsdk_toolkit import ToolkitLogger

logger = ToolkitLogger("user_feedback")


async def get_user_feedback_async(draft_path: Path) -> tuple[str, str | None]:
    """
    Pause for human review of draft document.

    Args:
        draft_path: Path to the draft document

    Returns:
        (mode, feedback) where mode is 'done', 'approve', or 'skip'
        feedback contains extracted [bracketed comments] with context
    """
    # Show draft location
    print("\n" + "=" * 60)
    print("HUMAN REVIEW CHECKPOINT")
    print("=" * 60)
    print(f"\n📄 Draft synthesized: {draft_path}")
    print("\nReview the draft and provide feedback:")
    print("  • Add [bracketed comments] inline for specific issues")
    print("    Example: 'This section [needs more detail about the implementation]'")
    print("  • Type 'done' when ready to continue with feedback")
    print("  • Type 'approve' to accept as-is")
    print("  • Type 'skip' to continue without feedback")
    print("-" * 60)

    # Use asyncio-compatible input
    loop = asyncio.get_event_loop()
    user_input = await loop.run_in_executor(None, input, "Your choice: ")
    user_input = user_input.strip().lower()

    if user_input in ["approve", "approved"]:
        logger.info("✅ User approved draft")
        return "approve", None

    if user_input == "skip":
        logger.info("⏭️ User skipped review")
        return "skip", None

    # User said 'done' - read the file for bracketed comments
    logger.info("📝 Reading user feedback from file")
    feedback, comment_count = await _extract_bracketed_feedback(draft_path)

    if feedback:
        logger.info(f"📋 Found {comment_count} bracketed {'comment' if comment_count == 1 else 'comments'}")
    else:
        logger.info("ℹ️ No bracketed comments found")

    return "done", feedback


async def _extract_bracketed_feedback(file_path: Path) -> tuple[str | None, int]:
    """
    Extract bracketed feedback with context from file.

    Args:
        file_path: Path to the draft file with user comments

    Returns:
        Tuple of (formatted feedback string with context, count of comments)
    """
    try:
        if not file_path.exists():
            logger.warning(f"Draft file not found: {file_path}")
            return None, 0

        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        feedback_items = []
        bracket_pattern = r"\[([^\]]+)\]"
        comment_count = 0

        for line_num, line in enumerate(lines):
            matches = re.findall(bracket_pattern, line)
            for match in matches:
                comment_count += 1
                # Capture context (3 lines before/after)
                context_lines = 3

                start_idx = max(0, line_num - context_lines)
                end_idx = min(len(lines), line_num + context_lines + 1)

                context_before = lines[start_idx:line_num]
                context_after = lines[line_num + 1 : end_idx]

                # Format feedback with context
                feedback_text = []
                feedback_text.append(f"\n### Feedback at line {line_num + 1}:")
                feedback_text.append(f"**Issue**: {match}")

                if context_before:
                    feedback_text.append("\n**Context before**:")
                    for ctx_line in context_before:
                        if ctx_line.strip():
                            feedback_text.append(f"> {ctx_line}")

                feedback_text.append(f"\n**Current line**: {line}")

                if context_after:
                    feedback_text.append("\n**Context after**:")
                    for ctx_line in context_after:
                        if ctx_line.strip():
                            feedback_text.append(f"> {ctx_line}")

                feedback_items.append("\n".join(feedback_text))

        if feedback_items:
            return "\n\n".join(feedback_items), comment_count
        return None, 0

    except Exception as e:
        logger.error(f"Error reading draft file: {e}")
        return None, 0


def get_user_feedback_sync(draft_path: Path) -> tuple[str, str | None]:
    """
    Synchronous wrapper for get_user_feedback_async.

    Useful for calling from non-async contexts.
    """
    return asyncio.run(get_user_feedback_async(draft_path))
