#!/usr/bin/env python3
"""Test script to verify blog post writer fixes."""

import asyncio
import sys
from pathlib import Path

from ai_working.blog_post_writer.source_reviewer.core import SourceReviewer
from ai_working.blog_post_writer.style_extractor.core import StyleExtractor
from ai_working.blog_post_writer.style_reviewer.core import StyleReviewer
from ai_working.blog_post_writer.user_feedback.core import UserFeedbackHandler
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


async def test_style_extractor():
    """Test style extractor with retry logic."""
    logger.info("\n=== Testing Style Extractor ===")
    extractor = StyleExtractor()

    # Create a test writings dir with sample content
    test_dir = Path("test_writings")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "sample.md").write_text("# Test Post\n\nThis is a test blog post with my writing style.")

    try:
        profile = await extractor.extract_style(test_dir)
        logger.info("✓ Style extraction succeeded")
        logger.info(f"  Tone: {profile.get('tone')}")
        logger.info(f"  Voice: {profile.get('voice')}")
        return True
    except Exception as e:
        logger.error(f"✗ Style extraction failed: {e}")
        return False


async def test_source_reviewer():
    """Test source reviewer with retry and proper logging."""
    logger.info("\n=== Testing Source Reviewer ===")
    reviewer = SourceReviewer()

    blog_draft = """
    # My Blog Post

    This blog talks about AI and machine learning concepts.
    We discuss neural networks and deep learning.
    """

    brain_dump = """
    # Brain Dump

    Ideas about AI:
    - Machine learning is powerful
    - Neural networks are complex
    - Deep learning requires lots of data
    - GPUs help training
    """

    try:
        review = await reviewer.review_sources(blog_draft, brain_dump)
        logger.info("✓ Source review succeeded")
        logger.info(f"  Accuracy: {review.get('accuracy_score')}")
        logger.info(f"  Needs revision: {review.get('needs_revision')}")
        logger.info(f"  Issues found: {len(review.get('issues', []))}")
        return True
    except Exception as e:
        logger.error(f"✗ Source review failed: {e}")
        return False


async def test_style_reviewer():
    """Test style reviewer with retry and proper logging."""
    logger.info("\n=== Testing Style Reviewer ===")
    reviewer = StyleReviewer()

    blog_draft = """
    # My Blog Post

    This is a casual blog post about tech stuff.
    I really think AI is super cool!
    """

    style_profile = {
        "tone": "formal",
        "voice": "active",
        "vocabulary_level": "advanced",
        "sentence_structure": "complex",
        "paragraph_length": "long",
        "common_phrases": ["therefore", "moreover", "consequently"],
        "writing_patterns": ["thesis-evidence-conclusion"],
        "examples": ["Therefore, we must consider the implications.", "Moreover, the evidence suggests..."],
    }

    try:
        review = await reviewer.review_style(blog_draft, style_profile)
        logger.info("✓ Style review succeeded")
        logger.info(f"  Consistency: {review.get('consistency_score')}")
        logger.info(f"  Needs revision: {review.get('needs_revision')}")
        logger.info(f"  Issues found: {len(review.get('issues', []))}")
        return True
    except Exception as e:
        logger.error(f"✗ Style review failed: {e}")
        return False


def test_user_feedback():
    """Test user feedback extraction from file."""
    logger.info("\n=== Testing User Feedback ===")
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

    The end.
    """)

    try:
        # Test the internal method that reads from file
        feedback_text = handler._read_feedback_from_file(test_file)
        parsed = handler.parse_feedback(feedback_text)

        logger.info("✓ Feedback extraction succeeded")
        logger.info(f"  Requests found: {len(parsed.specific_requests)}")
        for req in parsed.specific_requests:
            logger.info(f"    → {req}")

        test_file.unlink()  # Clean up
        return True
    except Exception as e:
        logger.error(f"✗ Feedback extraction failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("Testing Blog Post Writer Fixes")
    logger.info("=" * 60)

    results = []

    # Test each component
    results.append(await test_style_extractor())
    results.append(await test_source_reviewer())
    results.append(await test_style_reviewer())
    results.append(test_user_feedback())

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    passed = sum(results)
    total = len(results)

    if passed == total:
        logger.info(f"✅ All {total} tests passed!")
        return 0
    logger.error(f"❌ {total - passed} of {total} tests failed")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
