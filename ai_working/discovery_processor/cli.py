#!/usr/bin/env python3
"""
Discovery Content Processor CLI

Processes content items (images, documents, URLs, canvas drawings) for the Discovery canvas.
Features:
  - Multi-processor routing (image, URL, document, canvas)
  - Progress tracking with resume capability
  - Batch processing with incremental saves
  - Claude Vision API integration for image analysis
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Optional
from uuid import uuid4

import click

from .models import ContentItem, ContentType, ProcessorConfig
from .processors import CanvasDrawingProcessor, DocumentProcessor, ImageProcessor, URLProcessor
from .session import SessionManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def detect_content_type(file_path: Path) -> Tuple[ContentType, Optional[str]]:
    """Detect content type from file path.

    Args:
        file_path: Path to content file

    Returns:
        Tuple of (ContentType, mime_type)
    """
    import mimetypes

    mime_type, _ = mimetypes.guess_type(str(file_path))

    if not mime_type:
        return ContentType.UNKNOWN, None

    if mime_type.startswith("image/"):
        return ContentType.IMAGE, mime_type
    elif mime_type in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
    ]:
        return ContentType.DOCUMENT, mime_type
    else:
        return ContentType.UNKNOWN, mime_type


async def process_single_item(item: ContentItem, config: ProcessorConfig, session: SessionManager):
    """Process a single content item.

    Args:
        item: Content item to process
        config: Processor configuration
        session: Session manager for progress tracking
    """
    # Check if already processed
    if session.is_processed(item.id):
        logger.info(f"⏭️  Skipping (already processed): {item.file_name}")
        return

    # Mark as started
    session.start_item(item.id)

    # Route to appropriate processor
    processors = [
        ImageProcessor(config),
        URLProcessor(config),
        DocumentProcessor(config),
        CanvasDrawingProcessor(config),
    ]

    processor = None
    for p in processors:
        if await p.can_process(item):
            processor = p
            break

    if not processor:
        session.fail_item(item.id, f"No processor found for content type: {item.type}")
        return

    # Process the item
    logger.info(f"🔄 Processing: {item.file_name} ({item.type.value})")
    result = await processor.process(item, config)

    # Save result
    if result.status.value == "completed":
        session.complete_item(result)
        logger.info(f"✅ Completed: {item.file_name}")
    else:
        session.fail_item(item.id, result.error_message or "Unknown error")


@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("discovery_output"),
    help="Output directory for processing results",
)
@click.option(
    "--session-file",
    "-s",
    type=click.Path(path_type=Path),
    default=Path("discovery_session.json"),
    help="Session file for progress tracking (default: discovery_session.json)",
)
@click.option("--session-id", help="Resume existing session by ID")
@click.option("--clear-session", is_flag=True, help="Clear existing session and start fresh")
@click.option("--pattern", "-p", default="**/*", help="Glob pattern for finding files (default: **/*)")
@click.option("--vision-api/--no-vision-api", default=True, help="Enable/disable Claude Vision API")
@click.option("--timeout", "-t", default=300, help="Processing timeout in seconds (default: 300)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(
    input_path: Path,
    output: Path,
    session_file: Path,
    session_id: Optional[str],
    clear_session: bool,
    pattern: str,
    vision_api: bool,
    timeout: int,
    verbose: bool,
):
    """Process content items for Discovery canvas.

    INPUT_PATH can be:
    - A single file (image, PDF, etc.)
    - A directory containing files to process
    - A URL (must start with http:// or https://)

    Examples:
        # Process a single image
        python -m ai_working.discovery_processor.cli image.png

        # Process all files in a directory
        python -m ai_working.discovery_processor.cli ./uploads/

        # Process with custom output directory
        python -m ai_working.discovery_processor.cli ./uploads/ --output ./results/

        # Resume previous session
        python -m ai_working.discovery_processor.cli ./uploads/ --session-id abc-123
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Setup configuration
    config = ProcessorConfig(
        use_vision_api=vision_api,
        timeout_seconds=timeout,
        output_dir=output,
        session_file=session_file,
    )

    # Setup session manager
    session = SessionManager(session_file=session_file, session_id=session_id)

    if clear_session:
        session.clear()
        logger.info("Session cleared")

    # Collect content items
    items = []

    # Check if input is a URL
    input_str = str(input_path)
    if input_str.startswith(("http://", "https://")):
        # Single URL
        items.append(
            ContentItem(
                id=str(uuid4()),
                type=ContentType.URL,
                source_path=input_str,
                file_name=input_str,
                mime_type="text/html",
            )
        )
    elif input_path.is_file():
        # Single file
        content_type, mime_type = detect_content_type(input_path)
        items.append(
            ContentItem(
                id=str(uuid4()),
                type=content_type,
                source_path=str(input_path.absolute()),
                file_name=input_path.name,
                mime_type=mime_type,
                size_bytes=input_path.stat().st_size,
            )
        )
    elif input_path.is_dir():
        # Directory - find all matching files
        for file_path in input_path.glob(pattern):
            if file_path.is_file():
                content_type, mime_type = detect_content_type(file_path)
                if content_type != ContentType.UNKNOWN:
                    items.append(
                        ContentItem(
                            id=str(uuid4()),
                            type=content_type,
                            source_path=str(file_path.absolute()),
                            file_name=file_path.name,
                            mime_type=mime_type,
                            size_bytes=file_path.stat().st_size,
                        )
                    )

    if not items:
        logger.error("No processable content items found")
        sys.exit(1)

    # Setup session with total count
    session.set_total_items(len(items))
    logger.info(f"📦 Found {len(items)} items to process")

    # Process all items
    async def process_all():
        for item in items:
            await process_single_item(item, config, session)

    asyncio.run(process_all())

    # Print summary
    summary = session.get_summary()
    logger.info("\n" + "=" * 50)
    logger.info("Processing Complete")
    logger.info("=" * 50)
    logger.info(f"Total items: {summary['total_items']}")
    logger.info(f"Successful: {summary['successful']} ✅")
    logger.info(f"Failed: {summary['failed']} ❌")
    logger.info(f"Completion: {summary['completion_percent']:.1f}%")
    logger.info("=" * 50)

    # Exit with error if any failures
    if summary["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
