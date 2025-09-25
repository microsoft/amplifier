#!/usr/bin/env python3
"""Test just the user feedback extraction."""

from pathlib import Path

from ai_working.blog_post_writer.user_feedback.core import UserFeedbackHandler
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


def test_user_feedback():
    """Test user feedback extraction from file."""
    logger.info("=== Testing User Feedback Extraction ===")
    handler = UserFeedbackHandler()

    # Create test draft file with bracketed comments
    test_file = Path("test_draft.md")
    test_file.write_text("""
    # My Blog Post

    This is the introduction [needs more context about the topic].

    ## Main Section

    Here's the main content [add more examples here].

    [This section feels too technical, make it more accessible]

    ## Conclusion

    The end [should tie back to introduction].
    """)

    try:
        # Test the internal method that reads from file
        feedback_text = handler._read_feedback_from_file(test_file)
        logger.info(f"Extracted feedback text:\n{feedback_text}")

        parsed = handler.parse_feedback(feedback_text)

        logger.info("\n✓ Feedback extraction succeeded!")
        logger.info(f"  Total requests found: {len(parsed.specific_requests)}")
        logger.info("\n  Extracted feedback:")
        for i, req in enumerate(parsed.specific_requests, 1):
            logger.info(f"    {i}. {req}")

        test_file.unlink()  # Clean up
        return True
    except Exception as e:
        logger.error(f"✗ Feedback extraction failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_user_feedback()
    if success:
        logger.info("\n✅ User feedback fix verified!")
    else:
        logger.error("\n❌ User feedback fix failed!")
