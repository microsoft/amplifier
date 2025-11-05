"""CLI interface for the tips synthesizer tool."""

import asyncio
import sys
from pathlib import Path

import click

from amplifier.ccsdk_toolkit import ToolkitLogger

from .synthesizer import TipsSynthesizer

logger = ToolkitLogger("tips_synthesizer_cli")


@click.command()
@click.option(
    "--input-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory containing markdown files with tips",
)
@click.option(
    "--output-file",
    required=True,
    type=click.Path(path_type=Path),
    help="Output file path for synthesized tips document",
)
@click.option(
    "--temp-dir",
    type=click.Path(path_type=Path),
    help="Temporary directory for intermediate files (default: .data/tips_synthesizer/<session>)",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from saved state if available",
)
@click.option(
    "--max-iterations",
    default=3,
    type=int,
    help="Maximum review iterations (default: 3)",
)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Enable human review checkpoints (default: enabled)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed progress",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview what would be processed without actually running",
)
def main(
    input_dir: Path,
    output_file: Path,
    temp_dir: Path | None,
    resume: bool,
    max_iterations: int,
    interactive: bool,
    verbose: bool,
    dry_run: bool,
) -> int:
    """Synthesize tips from markdown files into a cohesive document.

    This tool extracts tips and tricks from multiple markdown files and
    synthesizes them into a well-organized, cohesive document using an
    iterative writer-reviewer feedback loop.

    Example:
        python -m scenarios.tips_synthesizer \\
            --input-dir ./my_tips/ \\
            --output-file ./synthesized_tips.md \\
            --verbose
    """
    # Configure logging
    if verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    # Input validation - check for minimum files
    files = list(input_dir.glob("**/*.md"))
    if len(files) < 2:
        logger.error(f"Need at least 2 markdown files, found {len(files)} in {input_dir}")
        if len(files) == 1:
            logger.error(f"  Found: {files[0].name}")
        return 1

    # Show what will be processed
    logger.info(f"📚 Found {len(files)} markdown files to synthesize:")
    for file in files[:5]:
        logger.info(f"  • {file.relative_to(input_dir)}")
    if len(files) > 5:
        logger.info(f"  ... and {len(files) - 5} more files")

    if dry_run:
        logger.info("\n🔍 Dry run mode - no actual processing")
        logger.info("Would process the following stages:")
        logger.info("  1. Extract tips from each file")
        logger.info("  2. Create individual note files")
        logger.info("  3. Synthesize into unified document")
        logger.info("  4. Review and refine with feedback loop")
        return 0

    # Create synthesizer instance
    synthesizer = TipsSynthesizer(
        input_dir=input_dir,
        output_file=output_file,
        temp_dir=temp_dir,
        max_iterations=max_iterations,
        resume=resume,
        interactive=interactive,
    )

    # Run the synthesis pipeline
    logger.info("\n🚀 Starting Tips Synthesis Pipeline")
    logger.info(f"  Session: {synthesizer.session_dir}")
    logger.info(f"  Output: {output_file}")
    logger.info(f"  Max iterations: {max_iterations}")
    logger.info(f"  Interactive mode: {'enabled' if interactive else 'disabled'}")

    try:
        success = asyncio.run(synthesizer.run())

        if success:
            logger.info("\n✨ Tips synthesis complete!")
            logger.info(f"📄 Output saved to: {output_file}")
            return 0
        # Check if we hit max iterations without approval
        if synthesizer.session.context.get("review_iteration", 0) >= max_iterations:
            logger.info("\n⏸️ Reached max iterations without approval.")
            logger.info("  Run with --resume to continue refinement")
            return 0  # Not a failure, just incomplete
        logger.error("\n❌ Tips synthesis failed")
        return 1

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Synthesis interrupted - progress saved, use --resume to continue")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
