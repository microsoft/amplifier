#!/usr/bin/env python3
"""
DOT to Mermaid Converter CLI

Converts DOT graph files to Mermaid diagram format using deterministic pattern matching.
Features:
  - Progress tracking with resume capability
  - Batch processing with incremental saves
"""

import logging
import sys
from pathlib import Path

import click

from .converter import convert_deterministic
from .models import ConversionResult
from .parser import parse_dot_file
from .session import SessionManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def process_single_file(file_path: Path, output_dir: Path) -> ConversionResult:
    """Process a single DOT file.

    Args:
        file_path: Path to DOT file
        output_dir: Directory for output files

    Returns:
        ConversionResult object
    """
    try:
        # Parse DOT file
        logger.info(f"Parsing {file_path.name}")
        dot_graph = parse_dot_file(file_path)

        # Convert to Mermaid
        mermaid_content = convert_deterministic(dot_graph)

        # Save the output if successful
        if mermaid_content:
            output_file = output_dir / f"{file_path.stem}.mmd"
            output_file.write_text(mermaid_content, encoding="utf-8")
            logger.info(f"✅ Saved {output_file.name}")

            return ConversionResult(
                source_file=file_path,
                mermaid_content=mermaid_content,
                conversion_method="deterministic",
                warnings=[],
                success=True,
            )

        return ConversionResult(
            source_file=file_path,
            mermaid_content="",
            conversion_method="failed",
            warnings=["Conversion failed"],
            success=False,
        )

    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {e}")
        return ConversionResult(
            source_file=file_path, mermaid_content="", conversion_method="error", warnings=[str(e)], success=False
        )


@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("mermaid_output"),
    help="Output directory for Mermaid files",
)
@click.option("--pattern", "-p", default="**/*.dot", help="Glob pattern for finding DOT files (default: **/*.dot)")
@click.option(
    "--session-file",
    "-s",
    type=click.Path(path_type=Path),
    default=Path("dot_conversion_session.json"),
    help="Session file for progress tracking and resume (default: dot_conversion_session.json in current dir)",
)
@click.option("--clear-session", is_flag=True, help="Clear existing session and start fresh")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(
    input_path: Path,
    output: Path,
    pattern: str,
    session_file: Path,
    clear_session: bool,
    verbose: bool,
):
    """Convert DOT graph files to Mermaid diagram format.

    Uses deterministic pattern matching to convert Graphviz DOT files
    to Mermaid flowchart diagrams.

    Progress is saved after each file, allowing interrupted sessions
    to be resumed without reprocessing completed files.

    INPUT_PATH can be either a single DOT file or a directory of DOT files.

    Examples:
        # Convert all DOT files in a directory
        python cli.py /path/to/dot/files

        # Convert a single file
        python cli.py /path/to/file.dot

        # Use custom session file location
        python cli.py /path/to/dot/files --session-file /tmp/session.json
    """
    # Setup logging
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Find DOT files
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob(pattern))

    if not files:
        logger.error(f"No DOT files found matching pattern: {pattern}")
        sys.exit(1)

    logger.info(f"Found {len(files)} DOT files to process")

    # Initialize session manager
    session = SessionManager(session_file=session_file)

    if clear_session:
        session.clear()

    session.set_total_files(len(files))

    # Show what will be processed
    logger.info("Files to process:")
    for i, file in enumerate(files[:5], 1):
        status = "✓ Already processed" if session.is_processed(file) else "→ To process"
        logger.info(f"  {i}. {file.name} [{status}]")
    if len(files) > 5:
        logger.info(f"  ... and {len(files) - 5} more")

    # Process each file
    successful = 0
    failed = 0

    for i, file_path in enumerate(files, 1):
        # Skip if already processed
        if session.is_processed(file_path):
            logger.debug(f"Skipping already processed: {file_path.name}")
            continue

        # Process the file
        logger.info(f"[{i}/{len(files)}] Processing {file_path.name}")
        session.start_file(file_path)

        result = process_single_file(file_path, output)

        if result.success:
            session.complete_file(result)
            successful += 1
        else:
            error_msg = result.warnings[0] if result.warnings else "Unknown error"
            session.fail_file(file_path, error_msg)
            failed += 1

    # Display summary
    summary = session.get_summary()
    logger.info("")
    logger.info("=" * 60)
    logger.info("CONVERSION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files:        {summary['total_files']}")
    logger.info(f"Processed:          {summary['processed']}")
    logger.info(f"Successful:         {summary['successful']}")
    logger.info(f"Failed:             {summary['failed']}")
    logger.info(f"Completion:         {summary['completion_percent']:.1f}%")

    # Show failed files if any
    if session.get_failed():
        logger.info("")
        logger.info("Failed files:")
        for file_path, error in session.get_failed()[:10]:
            logger.error(f"  • {Path(file_path).name}: {error}")
        if len(session.get_failed()) > 10:
            logger.error(f"  ... and {len(session.get_failed()) - 10} more")

    logger.info("")
    logger.info(f"📁 Output directory: {output}")
    logger.info(f"💾 Session file: {session.session_file}")

    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
