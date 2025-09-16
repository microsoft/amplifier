"""CLI interface for the Amplifier Tool Builder.

This module provides the command-line interface for creating new Amplifier CLI tools
with AI assistance. It demonstrates advanced Claude Code SDK patterns.
"""

import asyncio
import sys
from pathlib import Path

import click

from .exceptions import CCSDKRequiredError
from .exceptions import MicrotaskError
from .exceptions import SessionError
from .exceptions import ValidationError
from .microtask_orchestrator import MicrotaskOrchestrator
from .microtask_orchestrator import PipelineStage
from .session_manager import SessionManager


@click.group()
def tool_builder():
    """Build new Amplifier CLI tools with AI assistance.

    The Tool Builder uses advanced Claude Code SDK patterns to generate
    working CLI tools in minutes instead of days.
    """


@tool_builder.command()
@click.argument("name")
@click.argument("description")
@click.option("--output-dir", default="./amplifier/tools", help="Output directory for generated tool")
@click.option("--template", help="Base template to use (e.g., 'processor', 'generator')")
@click.option("--session-id", help="Resume from existing session")
@click.option("--auto-add-makefile", is_flag=True, help="Automatically add target to main Makefile")
def create(
    name: str, description: str, output_dir: str, template: str | None, session_id: str | None, auto_add_makefile: bool
):
    """Create a new Amplifier CLI tool.

    NAME: Tool name (e.g., 'content-analyzer')
    DESCRIPTION: What the tool does (e.g., 'Analyzes markdown content for patterns')
    """
    try:
        # Set environment variable if auto-add is requested
        import os

        if auto_add_makefile:
            os.environ["AUTO_ADD_TO_MAKEFILE"] = "1"
        asyncio.run(_create_tool_async(name, description, output_dir, template, session_id))
    except CCSDKRequiredError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n⚠ Interrupted - session saved for resumption", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@tool_builder.command()
@click.argument("session_id")
def resume(session_id: str):
    """Resume an interrupted tool creation session.

    SESSION_ID: ID of the session to resume (shown when interrupted)
    """
    try:
        asyncio.run(_resume_tool_async(session_id))
    except CCSDKRequiredError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except SessionError as e:
        click.echo(f"❌ Session error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@tool_builder.command()
def list_sessions():
    """List all available tool creation sessions."""
    try:
        manager = SessionManager()
        sessions = manager.list_sessions()

        if not sessions:
            click.echo("No sessions found.")
            return

        click.echo("Available sessions:")
        click.echo("━" * 60)

        for session in sessions:
            status_color = "green" if session.current_stage == "completed" else "yellow"
            click.echo(
                f"  {click.style(session.id, bold=True)} - "
                f"{session.tool_name} "
                f"[{click.style(session.current_stage, fg=status_color)}]"
            )
            click.echo(f"    Created: {session.created_at}")
            click.echo(f"    Description: {session.description[:60]}...")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error listing sessions: {e}", err=True)
        sys.exit(1)


async def _create_tool_async(
    name: str, description: str, output_dir: str, template: str | None, session_id: str | None
):
    """Async implementation of tool creation."""
    # Validate inputs
    _validate_tool_name(name)

    # Check CC SDK availability first - fail fast if not available
    _check_cc_sdk_available()

    # Create or load session
    manager = SessionManager()

    if session_id:
        session = manager.load_session(session_id)
        click.echo(f"📂 Resuming session: {session_id}")
    else:
        session = manager.create_session(name, description)
        session.output_dir = output_dir
        session.template = template
        click.echo("🚀 Starting new tool creation")
        click.echo(f"   Session ID: {session.id}")
        click.echo(f"   Tool: {name}")
        click.echo(f"   Output: {output_dir}/{name}")

    # Create orchestrator and run pipeline
    orchestrator = MicrotaskOrchestrator()

    try:
        click.echo("\n🔧 Running tool generation pipeline...\n")

        # Show progress
        def show_stage_progress(stage_name: str):
            stage_names = {
                "requirements_analysis": "📋 Analyzing requirements...",
                "architecture_design": "🏗️ Designing architecture...",
                "module_generation": "⚙️ Generating modules...",
                "integration_assembly": "🔗 Assembling components...",
                "quality_verification": "✔️ Running quality checks...",
                "final_polish": "✨ Applying final polish...",
            }
            if stage_name in stage_names:
                click.echo(stage_names[stage_name])

        # Run the pipeline (will use CC SDK for actual generation)
        context = await orchestrator.execute_pipeline(session)

        # Report results for each completed stage
        for stage, result in context.accumulated_results.items():
            show_stage_progress(stage.value)
            if result.success:
                click.echo(f"   ✅ {stage.value.replace('_', ' ').title()} complete")
            else:
                click.echo(f"   ⚠️ {stage.value.replace('_', ' ').title()}: {result.error}")
            click.echo()

        # Check if completed
        if session.current_stage == PipelineStage.COMPLETED.value:
            click.echo("\n🎉 Tool generation complete!")
            # Get actual output path from session results
            actual_path = Path.home() / ".amplifier" / "generated_tools" / name
            click.echo(f"   Location: {actual_path}")

            # Check if we have integration results with makefile info
            integration_result = None
            if hasattr(context, "accumulated_results"):
                for stage, result in context.accumulated_results.items():
                    if stage == PipelineStage.INTEGRATION_ASSEMBLY and result.success:
                        integration_result = result.data
                        break

            click.echo("\n📝 Next steps:")

            if integration_result and "next_steps" in integration_result:
                for i, step in enumerate(integration_result["next_steps"], 1):
                    click.echo(f"   {i}. {step}")
            else:
                # Fallback to generic instructions
                click.echo(f"   1. Add to Makefile: cat {actual_path}/Makefile.snippet >> Makefile")
                click.echo(f"   2. Test the tool: make {name} ARGS='--help'")
                click.echo(f"   3. Run directly: cd {actual_path} && python cli.py --help")
                click.echo(f"   4. Run tests: cd {actual_path} && pytest")
                click.echo(f"   5. Move to project if satisfied: cp -r {actual_path} amplifier/tools/")

            # Show the actual make command prominently
            click.echo("\n✨ Quick test after adding to Makefile:")
            click.echo(click.style(f"   make {name} ARGS='--help'", fg="green", bold=True))
        else:
            click.echo(f"\n⚠️ Pipeline stopped at stage: {session.current_stage}")
            click.echo(f'   Resume with: make tool-builder ARGS="resume {session.id}"')

    except MicrotaskError as e:
        click.echo(f"\n❌ Pipeline error: {e}", err=True)
        click.echo(f'   Session saved. Resume with: make tool-builder ARGS="resume {session.id}"')
        session.save()
        raise
    except CCSDKRequiredError as e:
        click.echo(f"\n❌ {e}", err=True)
        raise
    except KeyboardInterrupt:
        click.echo(f"\n⚠️ Interrupted at stage: {session.current_stage}")
        click.echo(f'   Session saved. Resume with: make tool-builder ARGS="resume {session.id}"')
        session.save()
        raise
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        session.save()
        raise

    # Save final session state
    session.save()
    click.echo(f"\n✅ Session saved: {session.id}")


async def _resume_tool_async(session_id: str):
    """Resume an interrupted session."""
    # Check CC SDK availability first
    _check_cc_sdk_available()

    # Load session
    manager = SessionManager()
    session = manager.load_session(session_id)

    click.echo(f"📂 Resuming session: {session_id}")
    click.echo(f"   Tool: {session.tool_name}")
    click.echo(f"   Current Stage: {session.current_stage}")
    if session.completed_stages:
        click.echo(f"   Completed: {', '.join(session.completed_stages)}")

    # Create orchestrator and resume pipeline
    orchestrator = MicrotaskOrchestrator()

    # Determine where to resume from
    if session.current_stage == PipelineStage.COMPLETED.value:
        click.echo("\n✅ Tool generation already complete!")
        actual_path = Path.home() / ".amplifier" / "generated_tools" / session.tool_name
        click.echo(f"   Location: {actual_path}")
        return

    # Map current stage to PipelineStage enum
    try:
        current_stage = PipelineStage(session.current_stage)
    except ValueError:
        current_stage = PipelineStage.REQUIREMENTS_ANALYSIS

    click.echo(f"\n🔄 Resuming from stage: {current_stage.value.replace('_', ' ').title()}\n")

    try:
        # Resume pipeline execution
        context = await orchestrator.execute_pipeline(session, start_from=current_stage)

        # Show results
        for stage, result in context.accumulated_results.items():
            if result.success:
                click.echo(f"✅ {stage.value.replace('_', ' ').title()} complete")
            else:
                click.echo(f"⚠️ {stage.value.replace('_', ' ').title()}: {result.error}")

        if session.current_stage == PipelineStage.COMPLETED.value:
            click.echo("\n🎉 Tool generation complete!")
            actual_path = Path.home() / ".amplifier" / "generated_tools" / session.tool_name
            click.echo(f"   Location: {actual_path}")

            click.echo("\n📝 Next steps:")
            click.echo(f"   1. Add to Makefile: cat {actual_path}/Makefile.snippet >> Makefile")
            click.echo(f"   2. Test the tool: make {session.tool_name} ARGS='--help'")
            click.echo(f"   3. Run directly: cd {actual_path} && python cli.py --help")

            # Show the actual make command prominently
            click.echo("\n✨ Quick test after adding to Makefile:")
            click.echo(click.style(f"   make {session.tool_name} ARGS='--help'", fg="green", bold=True))
        else:
            click.echo(f"\n⚠️ Pipeline stopped at: {session.current_stage}")

    except Exception as e:
        click.echo(f"\n❌ Error during resume: {e}", err=True)
        session.save()
        raise

    session.save()


def _validate_tool_name(name: str):
    """Validate tool name follows conventions."""
    if not name:
        raise ValidationError("Tool name cannot be empty")

    if not name.replace("-", "").replace("_", "").isalnum():
        raise ValidationError("Tool name must contain only letters, numbers, hyphens, and underscores")

    if name[0].isdigit():
        raise ValidationError("Tool name cannot start with a number")


def _check_cc_sdk_available():
    """Check if Claude Code SDK is available - no fallbacks!"""
    import shutil
    import subprocess

    # Check for claude CLI
    claude_path = shutil.which("claude")

    if not claude_path:
        # Try to find it in common locations
        known_locations = [
            Path.home() / ".local/share/reflex/bun/bin/claude",
            Path.home() / ".npm-global/bin/claude",
            Path("/usr/local/bin/claude"),
        ]

        for location in known_locations:
            if location.exists() and location.is_file():
                claude_path = str(location)
                break

    if not claude_path:
        raise CCSDKRequiredError()

    # Verify it's executable
    try:
        result = subprocess.run([claude_path, "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise CCSDKRequiredError()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        raise CCSDKRequiredError()


if __name__ == "__main__":
    tool_builder()
