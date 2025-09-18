#!/usr/bin/env python3
"""
Code Complexity Analyzer

A CLI tool that uses Claude Code SDK to analyze code complexity and provide
suggestions for simplification. Demonstrates the CCSDK toolkit capabilities.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path when running as script
if __name__ == "__main__":
    # Get the project root (3 levels up from this script)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import click

from amplifier.ccsdk_toolkit import AgentDefinition
from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import LogFormat
from amplifier.ccsdk_toolkit import LogLevel
from amplifier.ccsdk_toolkit import SessionManager
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit import create_logger


@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--pattern", default="*.py", help="File pattern to analyze")
@click.option("--recursive", is_flag=True, help="Analyze recursively")
@click.option("--output", type=click.Path(), help="Save results to file")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.option("--resume", help="Resume previous session by ID")
@click.option("--agent", help="Path to custom agent definition")
@click.option("--limit", type=int, help="Process only N files (works with --resume to process next N)")
@click.option("--notify", is_flag=True, help="Enable desktop notifications for completion")
def main(
    target: str,
    pattern: str,
    recursive: bool,
    output: str | None,
    output_json: bool,
    verbose: bool,
    resume: str | None,
    agent: str | None,
    limit: int | None,
    notify: bool,
):
    """
    Analyze code complexity using Claude Code SDK.

    This tool examines code files and provides:
    - Complexity metrics
    - Simplification suggestions
    - Best practice recommendations
    """
    asyncio.run(
        analyze_complexity(
            Path(target),
            pattern,
            recursive,
            output,
            output_json,
            verbose,
            resume,
            agent,
            limit,
            notify,
        )
    )


async def analyze_complexity(
    target: Path,
    pattern: str,
    recursive: bool,
    output_path: str | None,
    output_json: bool,
    verbose: bool,
    resume_id: str | None,
    agent_path: str | None,
    limit: int | None,
    notify: bool,
):
    """Main analysis function"""
    import time

    start_time = time.time()

    # Set up logging
    log_format = LogFormat.JSON if output_json else LogFormat.RICH
    logger = create_logger(
        name="complexity_analyzer",
        level=LogLevel.DEBUG if verbose else LogLevel.INFO,
        format=log_format,
        output_file=Path(f"{output_path}.log") if output_path else None,
        enable_notifications=notify,
    )

    # Create session manager for persistence
    session_manager = SessionManager()

    # Load or create session
    if resume_id:
        session_state = session_manager.load_session(resume_id)
        if not session_state:
            logger.error(f"Session {resume_id} not found")
            raise click.ClickException(f"Cannot resume session {resume_id}")
        logger.info("Resumed session", session_id=resume_id)
    else:
        session_state = session_manager.create_session(
            name="complexity_analysis",
            tags=["analysis", "complexity"],
        )
        logger.info("Created new session", session_id=session_state.metadata.session_id)

    # Load agent configuration
    if agent_path:
        agent_def = AgentDefinition.from_file(Path(agent_path))
        logger.info(f"Loaded agent: {agent_def.name}")
    else:
        # Import ToolPermissions for agent configuration
        from amplifier.ccsdk_toolkit import ToolPermissions

        # Default complexity analyzer agent
        agent_def = AgentDefinition(
            name="complexity-analyzer",
            description="Expert at analyzing code complexity",
            system_prompt="""You are an expert code complexity analyzer following these principles:
- Ruthless simplicity: Always look for ways to reduce complexity
- Clear metrics: Provide specific complexity measurements
- Actionable advice: Give concrete simplification suggestions
- Best practices: Follow the implementation philosophy of minimal abstraction

Analyze the code for:
1. Cyclomatic complexity
2. Cognitive complexity
3. Nesting depth
4. Function length
5. Abstraction layers

Provide specific recommendations for simplification.""",
            tool_permissions=ToolPermissions(
                allowed=["Read", "Grep", "Glob"],
            ),
        )

    # Initialize tracking in session context if needed
    if "processed_files" not in session_state.context:
        session_state.context["processed_files"] = []
    if "total_files" not in session_state.context:
        session_state.context["total_files"] = 0

    # Convert to set for efficient operations
    processed_files_set = set(session_state.context["processed_files"])

    # Find files to analyze
    files_to_analyze = []
    if target.is_file():
        files_to_analyze = [target]
    else:
        glob_pattern = f"**/{pattern}" if recursive else pattern
        files_to_analyze = list(target.glob(glob_pattern))

    if not files_to_analyze:
        logger.warning("No files found matching pattern", pattern=pattern)
        return

    # Track total files for progress (only set on first run, not when resuming)
    if not resume_id:
        session_state.context["total_files"] = len(files_to_analyze)

    # Filter out already-processed files when resuming
    if processed_files_set:
        files_to_analyze = [f for f in files_to_analyze if str(f) not in processed_files_set]
        logger.info(f"Skipping {len(processed_files_set)} already-processed files")

    # Apply limit to remaining files
    if limit:
        files_to_analyze = files_to_analyze[:limit]
        logger.info(f"Limited to {len(files_to_analyze)} files (--limit={limit})")

    if not files_to_analyze:
        logger.info("All files have been processed or limit reached")
        return

    logger.info(f"Analyzing {len(files_to_analyze)} files (total: {session_state.context['total_files']})")

    # Start notification for analysis begin
    if notify:
        logger.stage_start("Analysis", f"Starting analysis of {len(files_to_analyze)} files")

    # Configure session
    options = SessionOptions(
        system_prompt=agent_def.system_prompt,
        max_turns=3,
    )

    # Add to session history
    session_state.add_message(
        "user",
        f"Analyzing {len(files_to_analyze)} files for complexity",
    )

    results = []

    try:
        async with ClaudeSession(options) as claude:
            logger.set_session(session_state.metadata.session_id)

            for i, file_path in enumerate(files_to_analyze, 1):
                # Calculate progress
                already_processed = len(session_state.context["processed_files"])
                current_progress = already_processed + i
                total = session_state.context["total_files"]

                logger.info(f"Analyzing [{current_progress}/{total}]: {file_path}")
                logger.increment_turn()

                # Build analysis prompt
                prompt = f"""Analyze the complexity of this code file: {file_path}

Please provide:
1. Overall complexity assessment (simple/moderate/complex)
2. Specific complexity metrics
3. Top 3 areas of highest complexity
4. Concrete suggestions for simplification
5. Example refactoring for the most complex section

Focus on actionable improvements following ruthless simplicity principles."""

                # Query Claude
                logger.log_query(prompt)
                response = await claude.query(prompt)

                if response.success:
                    result = {
                        "file": str(file_path),
                        "analysis": response.content,
                        "timestamp": session_state.metadata.updated_at,
                    }
                    results.append(result)

                    # Track as processed
                    if str(file_path) not in session_state.context["processed_files"]:
                        session_state.context["processed_files"].append(str(file_path))

                    # Log success
                    logger.info(
                        "Analysis complete",
                        file=str(file_path),
                        response_length=len(response.content),
                    )

                    # Add to session history
                    session_state.add_message("user", prompt)
                    session_state.add_message("assistant", response.content)
                else:
                    error_msg = response.error or "Unknown error"
                    logger.error(f"Analysis failed for {file_path}", error=Exception(error_msg))
                    results.append(
                        {
                            "file": str(file_path),
                            "error": error_msg,
                        }
                    )

                # Save session after each file
                session_manager.save_session(session_state)

    except Exception as e:
        logger.error("Analysis failed", error=e)
        # Send failure notification
        if notify:
            logger.task_complete(
                f"Code complexity analysis failed: {str(e)}", duration=time.time() - start_time, success=False
            )
        raise click.ClickException(str(e))

    # Calculate total duration
    total_duration = time.time() - start_time

    # Log session summary
    logger.log_session_end(
        session_id=session_state.metadata.session_id,
        duration_ms=int(total_duration * 1000),
        total_cost=0.0,  # Would track from responses
        turns_completed=len(files_to_analyze),
        status="completed",
    )

    # Send completion notification
    if notify:
        logger.task_complete(
            f"Code complexity analysis complete: {len(results)} files analyzed", duration=total_duration, success=True
        )

    # Output results
    if output_json:
        output_content = json.dumps(results, indent=2)
    else:
        output_content = format_results(results)

    if output_path:
        Path(output_path).write_text(output_content)
        logger.info(f"Results saved to {output_path}")
    else:
        print(output_content)


def format_results(results: list) -> str:
    """Format results for human-readable output"""
    output = []
    output.append("=" * 80)
    output.append("CODE COMPLEXITY ANALYSIS RESULTS")
    output.append("=" * 80)

    for i, result in enumerate(results, 1):
        output.append(f"\n[{i}] File: {result['file']}")
        output.append("-" * 40)

        if "error" in result:
            output.append(f"ERROR: {result['error']}")
        else:
            output.append(result["analysis"])

    output.append("\n" + "=" * 80)
    output.append(f"Analyzed {len(results)} files")

    return "\n".join(output)


if __name__ == "__main__":
    main()
