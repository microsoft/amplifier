#!/usr/bin/env python3
"""
Command-line interface for AI-first tool builder.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from amplifier.tools.tool_builder import ToolBuilderPipeline


def setup_logging(verbose: bool = False):
    """Configure logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")


async def build_tool(args):
    """Build a new tool."""
    # Use output_dir as tools_dir if specified, otherwise use default
    tools_dir = Path(args.output_dir) if args.output_dir else None
    pipeline = ToolBuilderPipeline(state_dir=args.state_dir, tools_dir=tools_dir)

    try:
        result = await pipeline.build_tool(
            tool_name=args.name, description=args.description, resume=args.resume, skip_validation=args.skip_validation
        )

        # Files are now automatically saved by the integration stage
        integration_results = result.get("integration_results", {})
        if integration_results.get("saved_files"):
            print(f"\n✓ Tool files saved to: {integration_results.get('tool_dir')}")
            for filepath in integration_results["saved_files"]:
                print(f"  - {Path(filepath).name}")
        elif args.output_dir:
            # Legacy: save if integration stage didn't run
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            for filename, content in result.get("generated_code", {}).items():
                if isinstance(content, str):
                    filepath = output_dir / filename
                    filepath.write_text(content)
                    print(f"✓ Saved {filename} to {filepath}")

        # Show validation results if available
        if result.get("validation"):
            validation = result["validation"]
            print(f"\n{'=' * 60}")
            print("Validation Results")
            print("=" * 60)
            print(f"Overall Quality: {validation.get('overall_quality', 'unknown')}")

            if validation.get("issues"):
                print("\nIssues Found:")
                for issue in validation["issues"]:
                    print(f"  [{issue.get('severity', 'unknown')}] {issue.get('description', '')}")

            if validation.get("recommendations"):
                print("\nRecommendations:")
                for rec in validation["recommendations"]:
                    print(f"  - {rec}")

        # Show metrics
        metrics = result.get("metrics", {})
        print(f"\n✓ Tool '{args.name}' built successfully")
        print(f"  AI calls: {metrics.get('total_ai_calls', 0)}")
        print(f"  Tokens used: {metrics.get('total_tokens', 0)}")
        print(f"  Stages completed: {metrics.get('stages_completed', 0)}")

    except Exception as e:
        logging.error(f"Failed to build tool: {e}")
        return 1

    return 0


async def resume_builds(args):
    """Resume incomplete tool builds."""
    pipeline = ToolBuilderPipeline(state_dir=args.state_dir)

    incomplete = pipeline.state_manager.list_incomplete_tools()
    if not incomplete:
        print("No incomplete tool builds found.")
        return 0

    print(f"Found {len(incomplete)} incomplete tool(s):")
    for tool_name in incomplete:
        print(f"  - {tool_name}")

    if not args.yes and input("\nResume all? [y/N]: ").lower() != "y":
        return 0

    results = await pipeline.resume_incomplete_tools()

    success_count = sum(1 for r in results.values() if "error" not in r)
    print(f"\nResumed {success_count}/{len(results)} tools successfully")

    for tool_name, result in results.items():
        if "error" in result:
            print(f"  ✗ {tool_name}: {result['error']}")
        else:
            print(f"  ✓ {tool_name}")

    return 0 if success_count == len(results) else 1


async def show_status(args):
    """Show status of a tool build."""
    pipeline = ToolBuilderPipeline(state_dir=args.state_dir)

    status = pipeline.get_tool_status(args.name)
    if not status:
        print(f"No build found for tool '{args.name}'")
        return 1

    print(f"Tool: {status['tool_name']}")
    print(f"Current Stage: {status.get('current_stage', 'None')}")
    print(f"Next Stage: {status.get('next_stage', 'Complete')}")

    if status.get("completed_stages"):
        print("\nCompleted Stages:")
        for stage in status["completed_stages"]:
            print(f"  ✓ {stage}")

    if status.get("failed_attempts"):
        print("\nFailed Attempts:")
        for stage, errors in status["failed_attempts"].items():
            print(f"  ✗ {stage}: {len(errors)} attempt(s)")

    metrics = status.get("metrics", {})
    if metrics:
        print("\nMetrics:")
        print(f"  AI calls: {metrics.get('ai_calls', 0)}")
        print(f"  Tokens used: {metrics.get('tokens_used', 0)}")

    return 0


async def cleanup_completed(args):
    """Clean up completed tool build states."""
    pipeline = ToolBuilderPipeline(state_dir=args.state_dir)

    cleaned = pipeline.cleanup_completed()
    print(f"Cleaned up {cleaned} completed tool state(s)")
    return 0


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AI-first tool builder for Claude Code tools")

    # Global options
    parser.add_argument(
        "--state-dir", type=Path, help="Directory for state files (default: ~/.amplifier/tool_builder_state)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build a new tool")
    build_parser.add_argument("name", help="Name of the tool")
    build_parser.add_argument("description", help="Description of what the tool should do")
    build_parser.add_argument("--resume", action="store_true", help="Resume from previous run")
    build_parser.add_argument("--skip-validation", action="store_true", help="Skip validation stage")
    build_parser.add_argument(
        "--output-dir", "-o", help="Directory to save generated files (default: amplifier/tools/<tool_name>)"
    )

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume incomplete builds")
    resume_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show build status")
    status_parser.add_argument("name", help="Name of the tool")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up completed builds")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    setup_logging(args.verbose)

    # Route to appropriate handler
    handlers = {"build": build_tool, "resume": resume_builds, "status": show_status, "cleanup": cleanup_completed}

    handler = handlers.get(args.command)
    if handler:
        return await handler(args)
    parser.print_help()
    return 1


def cli_main():
    """Synchronous CLI entry point."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    cli_main()
