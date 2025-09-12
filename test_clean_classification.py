#!/usr/bin/env python3
"""Test that document classification has clean output"""

import asyncio
from contextlib import suppress

from amplifier.content_loader import ContentItem
from amplifier.knowledge_synthesis.resilient_miner import ResilientKnowledgeMiner


async def test_clean_classification():
    """Test that classification output is clean"""

    # Create a test article
    test_article = ContentItem(
        content_id="test-1",
        title="API Documentation",
        content="""
        # REST API

        ## GET /users
        Returns users list.

        ## POST /users
        Creates a new user.
        """,
        source_path="api.md",
        format="md",
    )

    # Initialize miner
    miner = ResilientKnowledgeMiner(use_focused_extractors=True)

    print("\n" + "=" * 60)
    print("TESTING CLEAN CLASSIFICATION OUTPUT")
    print("=" * 60 + "\n")
    print("Expected: Animated spinner during classification")
    print("Expected: Clean '├─ Document type: api_docs' after")
    print("Expected: NO 'Claude Code SDK verified' messages")
    print("=" * 60 + "\n")

    # Process the article (will stop after classification for demo)
    with suppress(asyncio.TimeoutError):
        # Run with timeout to just show classification
        await asyncio.wait_for(
            miner.process_article_with_logging(test_article, 1, 1),
            timeout=35,  # Enough time for classification
        )

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("Check output above is clean")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_clean_classification())
