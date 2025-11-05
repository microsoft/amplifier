#!/usr/bin/env python3
"""
Tool: [TOOL_NAME]
Purpose: [ONE_LINE_PURPOSE]

Contract:
  Inputs: [EXPECTED_INPUTS]
  Outputs: [EXPECTED_OUTPUTS]
  Failures: [HOW_IT_FAILS]

Philosophy:
  - Ruthless simplicity: Direct solutions without abstractions
  - Fail fast and loud: Clear errors, no silent failures
  - Progress visibility: Show what's happening
  - Defensive by default: Handle LLM and file I/O edge cases
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

import click

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CORE LOGIC (This is the "brick" - self-contained functionality)
# ============================================================================


class ToolProcessor:
    """Core processing logic - can be regenerated from specification."""

    def __init__(self, session_file: Path | None = None):
        """Initialize processor with optional session persistence."""
        self.session_file = session_file or Path("tool_session.json")
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Load previous state for resume capability."""
        if self.session_file.exists():
            try:
                return read_json_with_retry(self.session_file)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        return {"processed": [], "results": []}

    def _save_state(self) -> None:
        """Save state after each item (incremental progress)."""
        try:
            write_json_with_retry(self.state, self.session_file)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    async def process_item(self, item: Path) -> dict[str, Any]:
        """Process a single item with AI assistance."""
        # Skip if already processed (resume capability)
        if str(item) in self.state["processed"]:
            logger.info(f"Skipping already processed: {item}")
            return {}

        # AI processing with defensive parsing
        options = SessionOptions(
            system_prompt="You are a helpful assistant.",
            retry_attempts=2,
        )

        async with ClaudeSession(options) as session:
            prompt = f"Analyze this item: {item.name}"
            response = await session.query(prompt)

            # Parse with defensive utilities
            parsed = parse_llm_json(response.content, default={})
            # Ensure we always return a dict
            result = parsed if isinstance(parsed, dict) else {"data": parsed}

        # Save progress immediately
        self.state["processed"].append(str(item))
        self.state["results"].append(result)
        self._save_state()

        return result

    def validate_inputs(self, items: list[Path], min_required: int = 1) -> bool:
        """Validate inputs before processing."""
        if not items:
            logger.error("No input items found")
            return False

        if len(items) < min_required:
            logger.error(f"Need at least {min_required} items, found {len(items)}")
            return False

        logger.info(f"Found {len(items)} items to process:")
        for item in items[:5]:  # Show first 5
            logger.info(f"  • {item.name}")
        if len(items) > 5:
            logger.info(f"  ... and {len(items) - 5} more")

        return True


# ============================================================================
# CLI INTERFACE (This is the "stud" - stable connection point)
# ============================================================================


@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--pattern",
    default="**/*.md",
    help="Glob pattern for file discovery (default: **/*.md)",
)
@click.option(
    "--min-files",
    default=1,
    type=int,
    help="Minimum files required (default: 1)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("output.json"),
    help="Output file path",
)
@click.option(
    "--resume",
    type=click.Path(path_type=Path),
    help="Resume from session file",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def main(
    input_path: Path,
    pattern: str,
    min_files: int,
    output: Path,
    resume: Path | None,
    verbose: bool,
):
    """[TOOL_NAME] - [ONE_LINE_PURPOSE]

    This tool processes files using AI assistance with automatic retry,
    progress tracking, and resume capability.
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")  # Access underlying logger

    # Find files (recursive by default)
    files = list(input_path.glob(pattern))

    # Create processor
    processor = ToolProcessor(session_file=resume)

    # Validate inputs (fail fast)
    if not processor.validate_inputs(files, min_files):
        sys.exit(1)

    # Process with progress visibility
    logger.info("Starting processing...")
    results = []

    async def process_all():
        for i, file in enumerate(files, 1):
            logger.info(f"[{i}/{len(files)}]: Processing {file.name}")
            try:
                result = await processor.process_item(file)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file}: {e}")
                # Continue on partial failure (graceful degradation)
                continue
        return results

    # Run async processing
    final_results = asyncio.run(process_all())

    # Save results
    write_json_with_retry({"results": final_results}, output)
    logger.info(f"✅ Processed {len(final_results)} items successfully")
    logger.info(f"📄 Results saved to: {output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
