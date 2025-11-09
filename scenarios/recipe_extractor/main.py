"""CLI interface and orchestration for recipe extraction."""

import logging
import sys
from pathlib import Path

import click

from scenarios.recipe_extractor.converter import convert_to_metric
from scenarios.recipe_extractor.fetcher import fetch_recipe
from scenarios.recipe_extractor.markdown_writer import create_slug
from scenarios.recipe_extractor.markdown_writer import generate_markdown
from scenarios.recipe_extractor.state import RecipeExtractorState

# Try to import amplifier utilities (graceful fallback if not available)
try:
    from amplifier.utils.toolkit_logger import ToolkitLogger

    logger = ToolkitLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

try:
    from amplifier.config.paths import paths

    AMPLIFIER_AVAILABLE = True
except ImportError:
    AMPLIFIER_AVAILABLE = False


def process_url(url: str, output_dir: Path, state: RecipeExtractorState) -> bool:
    """Process a single recipe URL.

    Args:
        url: Recipe URL to process
        output_dir: Directory to save markdown files
        state: State manager

    Returns:
        True if successful, False otherwise
    """
    logger.info("")
    logger.info(f"Processing: {url}")
    logger.info("=" * 60)

    try:
        # Step 1: Fetching
        logger.info("Step 1/5: Fetching recipe...")
        recipe = fetch_recipe(url)

        # Step 2: Converting units
        logger.info("Step 2/5: Converting units to metric...")
        converted_ingredients = []
        for ingredient in recipe.ingredients:
            converted = convert_to_metric(ingredient)
            converted_ingredients.append(converted)

        # Update recipe with converted ingredients
        recipe.ingredients = converted_ingredients

        # Step 3: Scaling is handled by markdown writer (generates 1x, 2x, 3x sections)
        logger.info("Step 3/5: Preparing scaled ingredient sections...")

        # Step 4: Formatting markdown
        logger.info("Step 4/5: Formatting markdown...")
        markdown = generate_markdown(recipe)

        # Step 5: Saving file
        logger.info("Step 5/5: Saving file...")
        slug = create_slug(recipe.title)
        output_file = output_dir / f"{slug}.md"

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write markdown file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        # Mark as processed in state
        state.mark_processed(url)

        logger.info(f"✓ Successfully saved to: {output_file}")
        return True

    except ValueError as e:
        # Expected errors (unsupported site, fetch failure, etc.)
        logger.error(f"✗ Failed: {str(e)}")
        state.mark_failed(url, str(e))
        return False

    except Exception as e:
        # Unexpected errors
        logger.error(f"✗ Unexpected error: {str(e)}")
        state.mark_failed(url, f"Unexpected error: {str(e)}")
        return False


@click.command()
@click.option(
    "--url",
    "-u",
    multiple=True,
    required=True,
    help="Recipe URL(s) to extract",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory (default: auto-detect or ./recipes)",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from saved state (skip already-processed URLs)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose logging",
)
def main(
    url: tuple[str, ...],
    output: Path | None,
    resume: bool,
    verbose: bool,
) -> None:
    """Extract recipes from websites to markdown files.

    Examples:

        recipe_extractor --url https://example.com/recipe

        recipe_extractor --url https://site1.com/r1 --url https://site2.com/r2

        recipe_extractor --url https://example.com/recipe --output ./my-recipes

        recipe_extractor --url https://example.com/recipe --resume
    """
    # Set up logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        if hasattr(logger, "setLevel"):
            logger.setLevel(logging.DEBUG)

    # Determine output directory
    if output is not None:
        output_dir = output
    elif AMPLIFIER_AVAILABLE:
        # Use amplifier's content directory
        content_dirs = paths.content_dirs
        if content_dirs:
            output_dir = content_dirs[0] / "recipes"
        else:
            output_dir = Path.cwd() / "recipes"
    else:
        # Default to current directory
        output_dir = Path.cwd() / "recipes"

    logger.info("🍳 Recipe Extractor")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"URLs to process: {len(url)}")

    # Initialize state manager
    if AMPLIFIER_AVAILABLE:
        state_file = paths.data_dir / "recipe_extractor" / "state.json"
    else:
        state_file = Path.home() / ".local" / "share" / "amplifier" / "data" / "recipe_extractor" / "state.json"

    state = RecipeExtractorState(state_file)
    logger.info(f"State file: {state_file}")

    # Track results
    processed_count = 0
    failed_count = 0
    skipped_count = 0

    # Process each URL
    for recipe_url in url:
        # Check if already processed (if --resume flag set)
        if resume and state.is_processed(recipe_url):
            logger.info(f"⊘ Skipping (already processed): {recipe_url}")
            skipped_count += 1
            continue

        # Process the URL
        success = process_url(recipe_url, output_dir, state)

        if success:
            processed_count += 1
        else:
            failed_count += 1

    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info(f"  ✓ Processed: {processed_count}")
    if failed_count > 0:
        logger.info(f"  ✗ Failed: {failed_count}")
    if skipped_count > 0:
        logger.info(f"  ⊘ Skipped: {skipped_count} (already processed)")
    logger.info("=" * 60)

    # Exit with error code if any failures
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
