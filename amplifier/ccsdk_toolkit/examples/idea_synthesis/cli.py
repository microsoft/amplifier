#!/usr/bin/env python3
"""
Idea Synthesis CLI Tool

Synthesizes insights from AI context documentation using a 4-stage pipeline:
1. Reader: Loads markdown files
2. Summarizer: Creates summaries using AI
3. Synthesizer: Finds cross-cutting themes
4. Expander: Expands themes with context
"""

import asyncio
import sys
import uuid
from datetime import UTC
from datetime import datetime
from pathlib import Path

# Add project root to path when running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import click
from rich.console import Console
from rich.panel import Panel

from amplifier.ccsdk_toolkit.defensive import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive import write_json_with_retry

from .models import CrossCuttingTheme
from .models import FileSummary
from .models import SynthesisState
from .stages import ExpanderStage
from .stages import ReaderStage
from .stages import SummarizerStage
from .stages import SynthesizerStage

# Import notification helper if available
try:
    from amplifier.utils.notifications import send_notification
except ImportError:
    send_notification = None


@click.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option("--pattern", default="*.md", help="File pattern to match (default: *.md)")
@click.option("--recursive", is_flag=True, default=True, help="Search recursively")
@click.option("--limit", type=int, help="Process only N files")
@click.option("--resume", help="Resume from previous session ID")
@click.option("--output", type=click.Path(path_type=Path), help="Output directory for results")
@click.option("--json-output", is_flag=True, help="Output results as JSON")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--notify", is_flag=True, help="Enable desktop notifications on completion")
def main(
    directory: Path,
    pattern: str,
    recursive: bool,
    limit: int | None,
    resume: str | None,
    output: Path | None,
    json_output: bool,
    verbose: bool,
    notify: bool,
):
    """
    Synthesize ideas from AI context documentation.

    This tool processes markdown files through a 4-stage pipeline to extract
    insights, find themes, and create actionable synthesis.

    Examples:

        # Process all markdown files in ai_context directory
        python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/

        # Process with limit and save results
        python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/ --limit 5 --output results/

        # Resume a previous session
        python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/ --resume abc123
    """
    asyncio.run(
        run_synthesis(
            directory=directory,
            pattern=pattern,
            recursive=recursive,
            limit=limit,
            resume_id=resume,
            output_dir=output,
            json_output=json_output,
            verbose=verbose,
            notify=notify,
        )
    )


async def run_synthesis(
    directory: Path,
    pattern: str,
    recursive: bool,
    limit: int | None,
    resume_id: str | None,
    output_dir: Path | None,
    json_output: bool,
    verbose: bool,
    notify: bool,
):
    """Main synthesis pipeline."""
    console = Console()
    start_time = asyncio.get_event_loop().time()

    # Create logger with notification support
    from amplifier.ccsdk_toolkit.logger.logger import ToolkitLogger

    logger = ToolkitLogger(output_format="text", enable_notifications=notify, source="idea-synthesis")

    # Setup output directory
    if not output_dir:
        output_dir = Path.cwd() / "idea_synthesis_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load or create session state
    state_file = output_dir / "synthesis_state.json"
    state = load_or_create_state(state_file, resume_id)

    if resume_id:
        console.print(f"[cyan]Resuming session: {state.session_id}[/cyan]")
        console.print(f"[cyan]Previous progress: {state.processed_files}/{state.total_files} files[/cyan]")
    else:
        console.print(f"[cyan]Starting new session: {state.session_id}[/cyan]")

    # Initialize stages
    reader = ReaderStage(console)
    summarizer = SummarizerStage(state_file, console)
    synthesizer = SynthesizerStage(state_file, console)
    expander = ExpanderStage(state_file, console)

    try:
        # Stage 1: Read files
        console.print("\n[bold cyan]Stage 1: Reading Files[/bold cyan]")
        logger.stage_start("Reader")

        # Count total files first
        total_files = reader.count_files(directory, pattern, recursive)
        state.total_files = total_files

        # Determine skip count for resume
        skip_count = len(state.summaries) if resume_id else 0

        # Read files
        source_files = list(
            reader.read_files(directory=directory, pattern=pattern, recursive=recursive, limit=limit, skip=skip_count)
        )

        console.print(f"[green]✓ Loaded {len(source_files)} files[/green]")
        logger.stage_complete("Reader", f"Loaded {len(source_files)} files")

        # Stage 2: Summarize files
        console.print("\n[bold cyan]Stage 2: Summarizing Files[/bold cyan]")
        logger.stage_start("Summarizer")
        summaries = await summarizer.summarize_files(source_files, state)
        console.print(f"[green]✓ Created {len(summaries)} new summaries[/green]")
        console.print(f"[green]✓ Total summaries: {len(state.summaries)}[/green]")
        logger.stage_complete("Summarizer", f"Created {len(summaries)} summaries", total=len(state.summaries))

        # Stage 3: Synthesize themes
        console.print("\n[bold cyan]Stage 3: Synthesizing Themes[/bold cyan]")
        logger.stage_start("Synthesizer")
        themes = await synthesizer.synthesize_themes(state.summaries, state)
        console.print(f"[green]✓ Identified {len(themes)} themes[/green]")
        logger.stage_complete("Synthesizer", f"Identified {len(themes)} themes")

        # Stage 4: Expand ideas
        console.print("\n[bold cyan]Stage 4: Expanding Ideas[/bold cyan]")
        logger.stage_start("Expander")
        expanded = await expander.expand_ideas(themes, state.summaries, source_files, state)
        console.print(f"[green]✓ Expanded {len(expanded)} ideas[/green]")
        logger.stage_complete("Expander", f"Expanded {len(expanded)} ideas")

        # Generate output
        console.print("\n[bold cyan]Generating Output[/bold cyan]")

        if json_output:
            output_file = output_dir / "synthesis_results.json"
            export_json_results(state, output_file)
            console.print(f"[green]✓ JSON results saved to {output_file}[/green]")
        else:
            # Display results in console
            display_results(state, console)

            # Also save markdown report
            report_file = output_dir / "synthesis_report.md"
            export_markdown_report(state, report_file)
            console.print(f"\n[green]✓ Markdown report saved to {report_file}[/green]")

        console.print(f"\n[bold green]✨ Synthesis complete! Session: {state.session_id}[/bold green]")

        # Send final completion notification
        total_time = asyncio.get_event_loop().time() - start_time
        logger.task_complete(
            f"Idea synthesis complete: {state.processed_files} files processed", duration=total_time, success=True
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted! Progress has been saved.[/yellow]")
        console.print(f"[yellow]Resume with: --resume {state.session_id}[/yellow]")
        logger.task_complete("Idea synthesis interrupted", success=False)
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        console.print(f"[yellow]Resume with: --resume {state.session_id}[/yellow]")
        logger.task_complete(f"Idea synthesis failed: {str(e)}", success=False)
        sys.exit(1)


def load_or_create_state(state_file: Path, resume_id: str | None) -> SynthesisState:
    """Load existing state or create new one."""
    if resume_id and state_file.exists():
        state_data = read_json_with_retry(state_file)
        if state_data and state_data.get("session_id") == resume_id:
            # Reconstruct state from saved data
            state = SynthesisState(
                session_id=state_data["session_id"],
                total_files=state_data.get("total_files", 0),
                processed_files=state_data.get("processed_files", 0),
                current_stage=state_data.get("current_stage", "reader"),
                metadata=state_data.get("metadata", {}),
            )

            # Restore summaries
            for s in state_data.get("summaries", []):
                state.summaries.append(
                    FileSummary(
                        file_path=Path(s["file_path"]),
                        key_points=s["key_points"],
                        main_ideas=s["main_ideas"],
                        important_quotes=s["important_quotes"],
                        metadata=s.get("metadata", {}),
                        timestamp=datetime.fromisoformat(s["timestamp"]),
                    )
                )

            # Restore themes
            for t in state_data.get("themes", []):
                state.themes.append(
                    CrossCuttingTheme(
                        theme=t["theme"],
                        description=t["description"],
                        supporting_points=t["supporting_points"],
                        source_files=[Path(f) for f in t["source_files"]],
                        confidence=t["confidence"],
                        metadata=t.get("metadata", {}),
                    )
                )

            return state

    # Create new state
    return SynthesisState(session_id=str(uuid.uuid4())[:8])


def display_results(state: SynthesisState, console: Console):
    """Display results in the console."""

    # Display themes
    if state.themes:
        console.print("\n[bold]Cross-Cutting Themes:[/bold]")
        for i, theme in enumerate(state.themes, 1):
            console.print(f"\n{i}. [bold cyan]{theme.theme}[/bold cyan]")
            console.print(f"   {theme.description}")
            console.print(f"   Confidence: {theme.confidence:.1%}")
            console.print(f"   Sources: {', '.join(f.name for f in theme.source_files[:5])}")

    # Display expanded ideas
    if state.expanded_ideas:
        console.print("\n[bold]Expanded Synthesis:[/bold]")
        for i, idea in enumerate(state.expanded_ideas, 1):
            panel = Panel(
                f"[bold]{idea.title}[/bold]\n\n{idea.synthesis}\n\n[bold]Action Items:[/bold]\n"
                + "\n".join(f"• {item}" for item in idea.action_items),
                title=f"Idea {i}",
                border_style="cyan",
            )
            console.print(panel)


def export_markdown_report(state: SynthesisState, output_file: Path):
    """Export results as markdown report."""
    lines = [
        "# Idea Synthesis Report",
        f"\n*Generated: {datetime.now(UTC).isoformat()}*",
        f"\n*Session: {state.session_id}*",
        f"\n*Files Processed: {state.processed_files}*",
        "\n---\n",
    ]

    # Add themes section
    if state.themes:
        lines.append("## Cross-Cutting Themes\n")
        for i, theme in enumerate(state.themes, 1):
            lines.append(f"### {i}. {theme.theme}")
            lines.append(f"\n{theme.description}")
            lines.append(f"\n**Confidence:** {theme.confidence:.1%}")
            lines.append("\n**Supporting Points:**")
            for point in theme.supporting_points[:5]:
                lines.append(f"- {point}")
            lines.append(f"\n**Source Documents:** {', '.join(f.name for f in theme.source_files[:10])}")
            lines.append("")

    # Add expanded ideas section
    if state.expanded_ideas:
        lines.append("\n## Expanded Synthesis\n")
        for idea in state.expanded_ideas:
            lines.append(f"### {idea.title}")
            lines.append(f"\n{idea.synthesis}")
            lines.append("\n**Action Items:**")
            for item in idea.action_items:
                lines.append(f"- {item}")
            if idea.supporting_quotes:
                lines.append("\n**Key Quotes:**")
                for path, quote in idea.supporting_quotes[:5]:
                    lines.append(f'- "{quote}" (*{path.name}*)')
            lines.append("")

    output_file.write_text("\n".join(lines))


def export_json_results(state: SynthesisState, output_file: Path):
    """Export results as JSON."""
    results = {
        "session_id": state.session_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "files_processed": state.processed_files,
        "themes": [
            {
                "theme": t.theme,
                "description": t.description,
                "confidence": t.confidence,
                "supporting_points": t.supporting_points,
                "source_files": [str(f) for f in t.source_files],
            }
            for t in state.themes
        ],
        "expanded_ideas": [
            {
                "title": e.title,
                "synthesis": e.synthesis,
                "action_items": e.action_items,
                "supporting_quotes": [[str(q[0]), q[1]] for q in e.supporting_quotes],
            }
            for e in state.expanded_ideas
        ],
    }

    write_json_with_retry(results, output_file)


if __name__ == "__main__":
    main()
