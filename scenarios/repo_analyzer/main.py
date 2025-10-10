#!/usr/bin/env python3
"""
Repository Analyzer - Main Entry Point

Analyzes repositories for improvement opportunities using comparative analysis.
"""

import asyncio
import sys
from pathlib import Path

import click

from amplifier.utils.logger import get_logger

from .pipeline_orchestrator import PipelineOrchestrator
from .state import StateManager

logger = get_logger(__name__)


@click.command()
@click.option(
    "--source",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Path to source/reference repository",
)
@click.option(
    "--target",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Path to target repository to improve",
)
@click.option("--request", type=str, required=True, help="Analysis request (what to look for)")
@click.option("--focus", type=str, multiple=True, help="Specific areas to focus on (can be used multiple times)")
@click.option("--include", type=str, multiple=True, help="File patterns to include (e.g., '*.py', 'src/**/*.js')")
@click.option("--exclude", type=str, multiple=True, help="File patterns to exclude (e.g., 'test/**', '*.min.js')")
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for results (default: auto-generated in session dir)",
)
@click.option("--resume", is_flag=True, help="Resume from saved state")
@click.option("--reset", is_flag=True, help="Reset state and start fresh")
@click.option("--max-iterations", type=int, default=3, help="Maximum feedback iterations (default: 3)")
@click.option("--skip-review", is_flag=True, help="Skip the markdown review step")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(
    source: Path,
    target: Path,
    request: str,
    focus: tuple[str],
    include: tuple[str],
    exclude: tuple[str],
    output: Path | None,
    resume: bool,
    reset: bool,
    max_iterations: int,
    skip_review: bool,
    verbose: bool,
):
    """Repository Analyzer - Find improvement opportunities through comparative analysis.

    This tool analyzes a target repository by comparing it to a source/reference
    repository, identifying patterns and opportunities for improvement.

    Example:
        python -m scenarios.repo_analyzer \\
            --source ./reference-repo \\
            --target ./my-repo \\
            --request "Find architectural improvements and missing features"
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Determine session directory
    session_dir = None
    if resume:
        # Find most recent session for resume
        base_dir = Path(".data/repo_analyzer")
        if base_dir.exists():
            sessions = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
            if sessions:
                session_dir = sessions[0]
                logger.info(f"Resuming session: {session_dir.name}")

    # Create state manager
    state_manager = StateManager(session_dir)

    # Handle reset
    if reset:
        state_manager.reset()
        logger.info("State reset - starting fresh")

    # Set max iterations
    state_manager.state.max_iterations = max_iterations

    # Check for resume
    if resume and state_manager.state_file.exists() and not reset:
        logger.info("Resuming from saved state")
        # Use saved paths if not provided
        if state_manager.state.source_path:
            source = Path(state_manager.state.source_path)
        if state_manager.state.target_path:
            target = Path(state_manager.state.target_path)
        if state_manager.state.analysis_request:
            request = state_manager.state.analysis_request
        if state_manager.state.focus_areas:
            focus = tuple(state_manager.state.focus_areas)  # type: ignore

    # Set output path
    if output:
        state_manager.state.output_path = str(output)

    # Create and run pipeline
    pipeline = PipelineOrchestrator(state_manager)

    logger.info("🚀 Starting Repository Analyzer")
    logger.info(f"  Session: {state_manager.session_dir}")
    logger.info(f"  Source: {source.name}")
    logger.info(f"  Target: {target.name}")
    logger.info(f"  Request: {request[:100]}...")
    if focus:
        logger.info(f"  Focus areas: {', '.join(focus)}")
    if include:
        logger.info(f"  Include patterns: {', '.join(include)}")
    if exclude:
        logger.info(f"  Exclude patterns: {', '.join(exclude)}")
    logger.info(f"  Max iterations: {max_iterations}")

    success = asyncio.run(
        pipeline.run(
            source_path=source,
            target_path=target,
            analysis_request=request,
            focus_areas=list(focus) if focus else None,
            include_patterns=list(include) if include else None,
            exclude_patterns=list(exclude) if exclude else None,
            skip_review=skip_review,
        )
    )

    if success:
        logger.info("\n✨ Repository analysis complete!")
        output_file = state_manager.get_output_file()
        logger.info(f"📄 Results saved to: {output_file}")
        return 0

    logger.error("\n❌ Repository analysis failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
