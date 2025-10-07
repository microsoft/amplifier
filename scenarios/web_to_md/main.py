"""Main CLI entry point for web_to_md tool."""

import logging
import sys
from pathlib import Path

import click

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .converter import html_to_markdown
from .enhancer import enhance_markdown
from .fetcher import fetch_page
from .image_handler import process_images
from .indexer import generate_index
from .organizer import get_domain_dir
from .organizer import save_page
from .state import WebToMdState
from .validator import validate_content

# Try to import amplifier utilities
try:
    from amplifier.ccsdk_toolkit import ToolkitLogger  # type: ignore
    from amplifier.config.paths import paths  # type: ignore

    logger = ToolkitLogger(name="web_to_md")
    AMPLIFIER_AVAILABLE = True
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    AMPLIFIER_AVAILABLE = False
    paths = None  # type: ignore


def process_url(url: str, output_dir: Path, state: WebToMdState) -> bool:
    """Process a single URL.

    Args:
        url: URL to process
        output_dir: Output directory for files
        state: State manager

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing: {url}")
        logger.info(f"{'=' * 60}")

        # Step 1: Fetch HTML and metadata
        logger.info("Step 1/7: Fetching page...")
        html, metadata = fetch_page(url)

        # Step 2: Convert to markdown
        logger.info("Step 2/7: Converting to markdown...")
        markdown = html_to_markdown(html, url)

        # Step 2.5: Validate content (check for paywalls/auth walls)
        logger.info("Step 2.5/7: Validating content...")
        validation_result = validate_content(html, markdown, url)
        if not validation_result.is_valid:
            logger.error(f"✗ Content validation failed: {validation_result.reason}")
            logger.error("  This page appears to be behind a paywall or requires authentication.")
            logger.error(f"  Detected pattern: {validation_result.detected_pattern}")
            state.mark_failed(url, f"Content validation failed: {validation_result.reason}")
            return False

        # Step 3: Process images
        logger.info("Step 3/7: Processing images...")
        domain_dir = get_domain_dir(url, output_dir)
        image_mappings = process_images(html, url, domain_dir)

        # Step 4: Enhance markdown with AI
        logger.info("Step 4/7: Enhancing markdown...")
        # Add metadata for enhancement
        metadata["title"] = extract_title_from_markdown(markdown)
        enhanced_markdown = enhance_markdown(markdown, metadata)

        # Step 5: Update image references
        if image_mappings:
            logger.info("Step 5/7: Updating image references...")
            for original_url, local_path in image_mappings:
                # Convert to relative path from markdown file location
                relative_path = f"images/{local_path.name}"
                enhanced_markdown = enhanced_markdown.replace(original_url, relative_path)
        else:
            logger.info("Step 5/7: No images to update")

        # Step 6: Save the page
        logger.info("Step 6/7: Saving page...")
        saved_path = save_page(url, enhanced_markdown, output_dir)

        # Step 7: Mark as processed
        logger.info("Step 7/7: Updating state...")
        state.mark_processed(url)

        logger.info(f"✓ Successfully saved to: {saved_path}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to process {url}: {e}")
        state.mark_failed(url, str(e))
        return False


def extract_title_from_markdown(markdown: str) -> str:
    """Extract title from markdown content.

    Args:
        markdown: Markdown content

    Returns:
        Title string or "Untitled"
    """
    lines = markdown.split("\n")
    for line in lines[:10]:  # Check first 10 lines
        if line.startswith("# "):
            return line[2:].strip()
    return "Untitled"


@click.command()
@click.option("--url", "-u", multiple=True, required=True, help="URL(s) to convert")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output directory")
@click.option("--resume", is_flag=True, help="Resume from saved state")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(url: tuple, output: Path | None, resume: bool, verbose: bool):
    """Convert web pages to markdown with AI enhancement.

    Examples:
        web_to_md --url https://example.com
        web_to_md --url https://example.com --url https://another.com
        web_to_md --url https://example.com --output ./my-sites
        web_to_md --url https://example.com --resume
    """
    # Set up logging
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine output directory
    if output:
        output_dir = output
    else:
        # Use amplifier paths if available, otherwise fall back to manual config
        if AMPLIFIER_AVAILABLE and paths is not None:
            # Use first content directory + sites subdirectory
            if paths.content_dirs:
                output_dir = paths.content_dirs[0] / "sites"
            else:
                output_dir = Path.cwd() / "sites"
        else:
            # Fallback: use current directory
            output_dir = Path.cwd() / "sites"

    logger.info(f"Output directory: {output_dir}")

    # Initialize state - store in data directory if available
    if AMPLIFIER_AVAILABLE and paths is not None:
        state_dir = paths.data_dir / "web_to_md"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "state.json"
    else:
        state_file = output_dir / ".web_to_md_state.json"

    state = WebToMdState(state_file)

    # Process URLs
    urls_to_process = list(url)
    processed_count = 0
    failed_count = 0
    skipped_count = 0

    for url_item in urls_to_process:
        # Check if already processed (for resume)
        if resume and state.is_processed(url_item):
            logger.info(f"Skipping (already processed): {url_item}")
            skipped_count += 1
            continue

        # Process the URL
        if process_url(url_item, output_dir, state):
            processed_count += 1
        else:
            failed_count += 1

    # Generate index
    if processed_count > 0 or (resume and state.processed_urls):
        logger.info("\nGenerating index...")
        index_content = generate_index(output_dir)
        index_path = output_dir / "index.md"

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

        logger.info(f"Index saved to: {index_path}")

    # Final statistics
    logger.info(f"\n{'=' * 60}")
    logger.info("Summary:")
    logger.info(f"  Processed: {processed_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Skipped: {skipped_count}")

    stats = state.get_stats()
    logger.info(f"  Total in state: {stats['total']} ({stats['processed']} successful, {stats['failed']} failed)")
    logger.info(f"{'=' * 60}")

    # Exit with error code if any failures
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
