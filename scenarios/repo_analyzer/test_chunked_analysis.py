#!/usr/bin/env python3
"""Test the enhanced chunked analysis functionality."""

import asyncio

from amplifier.utils.logger import get_logger
from scenarios.repo_analyzer.analysis_engine.core import AnalysisEngine

logger = get_logger(__name__)


async def test_chunked_analysis():
    """Test the chunked analysis with sample content."""

    # Create sample repository content that will trigger chunking
    source_content = (
        """<repository>
<file path="src/main.py">
# Main application module
import sys
import os

class Application:
    def __init__(self):
        self.config = {}

    def run(self):
        print("Running application")
        return 0

if __name__ == "__main__":
    app = Application()
    sys.exit(app.run())
</file>
"""
        * 10
    )  # Repeat to create larger content

    target_content = (
        """<repository>
<file path="app.py">
# Simple script without structure
print("Hello world")
# Missing proper architecture
</file>
"""
        * 10
    )  # Repeat to create larger content

    # Create analysis engine
    engine = AnalysisEngine()

    # Test analysis request
    analysis_request = "Analyze the architectural patterns and suggest improvements"

    logger.info("=" * 60)
    logger.info("TESTING CHUNKED ANALYSIS")
    logger.info("=" * 60)

    logger.info(f"Source content size: {len(source_content):,} chars")
    logger.info(f"Target content size: {len(target_content):,} chars")

    # Run analysis (should automatically use chunking if content is large)
    result = await engine.analyze_repositories(
        source_content=source_content,
        target_content=target_content,
        analysis_request=analysis_request,
        focus_areas=["code organization", "architectural patterns"],
    )

    # Display results
    logger.info("\nAnalysis Results:")
    logger.info("-" * 40)

    if "summary" in result:
        summary = result["summary"]
        logger.info(f"Overall Assessment: {summary.get('overall_assessment', 'N/A')}")

        if "key_findings" in summary:
            logger.info(f"\nKey Findings ({len(summary['key_findings'])}):")
            for finding in summary["key_findings"][:3]:
                logger.info(f"  • {finding}")

    if "opportunities" in result:
        logger.info(f"\nOpportunities Found: {len(result['opportunities'])}")
        for i, opp in enumerate(result["opportunities"][:3], 1):
            logger.info(f"  {i}. {opp.get('title', 'Unnamed')}")

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    asyncio.run(test_chunked_analysis())
