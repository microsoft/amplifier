#!/usr/bin/env python
"""Command-line interface for the amplifier microtask system.

This module provides the CLI for managing and executing microtask pipelines.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from . import orchestrator
from . import session as session_module


@click.group()
def cli():
    """Amplifier Microtask System - Execute complex tasks through simple microtasks."""
    pass


@cli.command()
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
def init(workspace: str):
    """Initialize a new amplifier workspace."""
    workspace_path = Path(workspace).resolve()

    try:
        # Create workspace directory structure
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "sessions").mkdir(exist_ok=True)
        (workspace_path / "tasks").mkdir(exist_ok=True)
        (workspace_path / "results").mkdir(exist_ok=True)

        # Create a sample task file
        sample_task = {
            "name": "example_pipeline",
            "description": "Example pipeline showing basic structure",
            "tasks": [
                {"id": "task1", "type": "process", "config": {"action": "example", "message": "Hello from task 1"}},
                {
                    "id": "task2",
                    "type": "process",
                    "config": {"action": "example", "message": "Hello from task 2"},
                    "dependencies": ["task1"],
                },
            ],
        }

        sample_file = workspace_path / "tasks" / "example.json"
        with open(sample_file, "w") as f:
            json.dump(sample_task, f, indent=2)

        click.echo(f"✅ Workspace initialized at: {workspace_path}")
        click.echo(f"📝 Sample task file created: {sample_file}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Edit task files in: {workspace_path / 'tasks'}")
        click.echo(f"  2. Run a task: amplifier run {sample_file}")

    except Exception as e:
        click.echo(f"❌ Failed to initialize workspace: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("task_file", type=click.Path(exists=True))
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
@click.option(
    "--parallel",
    default=3,
    help="Maximum parallel tasks",
    type=int,
)
def run(task_file: str, workspace: str, parallel: int):
    """Execute a pipeline from a task file."""
    workspace_path = Path(workspace).resolve()
    task_path = Path(task_file).resolve()

    # Ensure workspace exists
    if not workspace_path.exists():
        click.echo("❌ Workspace not found. Run 'amplifier init' first.", err=True)
        sys.exit(1)

    try:
        # Load task definition
        with open(task_path) as f:
            task_def = json.load(f)

        click.echo(f"📋 Loading pipeline: {task_def.get('name', 'unnamed')}")
        if description := task_def.get("description"):
            click.echo(f"   {description}")

        # Create session
        sess = session_module.create_session(workspace_path)
        sess.data["name"] = task_def.get("name", "pipeline")
        sess.data["task_file"] = str(task_path)
        sess.data["tasks"] = []
        session_module.save_checkpoint(sess)
        session_id = sess.id

        click.echo(f"🆔 Session ID: {session_id}")

        # Create tasks from definition
        pipeline_tasks = []

        # Parse and execute tasks
        tasks = task_def.get("tasks", [])
        if not tasks:
            click.echo("⚠️  No tasks defined in pipeline", err=True)
            sys.exit(1)

        click.echo(f"🚀 Executing {len(tasks)} tasks...")

        # Execute pipeline with progress updates
        with click.progressbar(
            length=len(tasks),
            label="Progress",
            show_percent=True,
            show_pos=True,
        ) as bar:
            completed = 0

            # Simple task execution (real implementation would be async)
            for task in tasks:
                task_id = task.get("id", f"task_{completed}")
                task_type = task.get("type", "process")
                config = task.get("config", {})

                click.echo(f"\n  ▶️  Running: {task_id} ({task_type})")

                # Create task object
                task_obj = orchestrator.Task(
                    id=task_id,
                    prompt=config.get("message", "Process task"),
                    context_keys=task.get("dependencies", []),
                    save_key=task_id,
                )
                pipeline_tasks.append(task_obj)

                # Mark as completed for demo
                session_module.add_completed_task(sess, task_id)
                click.echo(f"  ✅ Completed: {task_id}")

                completed += 1
                bar.update(1)

        # Update session status
        session_module.update_session_status(sess, "completed")

        click.echo("\n✨ Pipeline completed successfully!")
        click.echo(f"📂 Results saved in: {workspace_path / 'results' / session_id}")

    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON in task file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Pipeline execution failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("session_id")
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
def resume(session_id: str, workspace: str):
    """Resume an interrupted session."""
    workspace_path = Path(workspace).resolve()

    try:
        sess = session_module.load_session(session_id, workspace_path)

        if not sess:
            click.echo(f"❌ Session not found: {session_id}", err=True)
            sys.exit(1)

        click.echo(f"📋 Resuming session: {sess.id}")
        click.echo(f"   Status: {sess.status}")
        click.echo(f"   Created: {sess.created_at}")

        # Resume logic would go here
        # orchestrator = MicrotaskOrchestrator(workspace_path=workspace_path)

        # Get incomplete tasks (checking which tasks are not in completed list)
        all_tasks = sess.data.get("tasks", [])
        incomplete_tasks = [t for t in all_tasks if t not in sess.completed_tasks]

        if not incomplete_tasks:
            click.echo("✅ Session already completed or no tasks to resume")
            return

        click.echo(f"🔄 Resuming {len(incomplete_tasks)} incomplete tasks...")

        # Execute remaining tasks
        for task_id in incomplete_tasks:
            click.echo(f"  ▶️  Resuming: {task_id}")
            # Mark as completed for demo
            session_module.add_completed_task(sess, task_id)
            click.echo(f"  ✅ Completed: {task_id}")

        session_module.update_session_status(sess, "completed")
        click.echo("✨ Session resumed and completed successfully!")

    except Exception as e:
        click.echo(f"❌ Failed to resume session: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("session_id", required=False)
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
def status(session_id: Optional[str], workspace: str):
    """Show session status and progress."""
    workspace_path = Path(workspace).resolve()

    try:
        if session_id:
            # Show specific session status
            sess = session_module.load_session(session_id, workspace_path)
            if not sess:
                click.echo(f"❌ Session not found: {session_id}", err=True)
                sys.exit(1)

            click.echo(f"\n📊 Session Status: {session_id}")
            click.echo(f"{'=' * 50}")
            click.echo(f"ID:         {sess.id}")
            click.echo(f"Status:     {sess.status}")
            click.echo(f"Stage:      {sess.current_stage}")
            click.echo(f"Created:    {sess.created_at}")

            if sess.data:
                click.echo("\nData:")
                for key, value in sess.data.items():
                    if key != "tasks":  # Don't show tasks here
                        click.echo(f"  {key}: {value}")

            if sess.completed_tasks:
                click.echo("\nTasks:")
                total_tasks = len(sess.data.get("tasks", []))
                completed = len(sess.completed_tasks)
                click.echo(f"  Total:     {total_tasks if total_tasks else 'N/A'}")
                click.echo(f"  Completed: {completed}")
                if total_tasks:
                    click.echo(f"  Progress:  {completed / total_tasks * 100:.1f}%")
        else:
            # Show recent sessions
            sessions = session_module.list_sessions(workspace_path)
            sessions = sessions[:5]  # Limit to 5
            if not sessions:
                click.echo("No sessions found. Run 'amplifier run' to create one.")
                return

            click.echo("\n📊 Recent Sessions")
            click.echo(f"{'=' * 70}")
            click.echo(f"{'ID':<15} {'Stage':<20} {'Status':<12} {'Created':<20}")
            click.echo(f"{'-' * 70}")

            for sess_info in sessions:
                sid = sess_info.id[:12] + "..."
                stage = (
                    sess_info.current_stage[:17] + "..."
                    if len(sess_info.current_stage) > 20
                    else sess_info.current_stage
                )
                status = sess_info.status
                created = str(sess_info.created_at)[:19]
                click.echo(f"{sid:<15} {stage:<20} {status:<12} {created:<20}")

            click.echo("\n💡 Use 'amplifier status <session-id>' for details")

    except Exception as e:
        click.echo(f"❌ Failed to get status: {e}", err=True)
        sys.exit(1)


@cli.command(name="list")
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
@click.option(
    "--limit",
    default=10,
    help="Number of sessions to show",
    type=int,
)
@click.option(
    "--status",
    help="Filter by status",
    type=click.Choice(["pending", "running", "completed", "failed"]),
)
def list_sessions(workspace: str, limit: int, status: Optional[str]):
    """List all sessions."""
    workspace_path = Path(workspace).resolve()

    try:
        all_sessions = session_module.list_sessions(workspace_path)

        # Filter by status if provided
        if status:
            sessions = [s for s in all_sessions if s.status == status]
        else:
            sessions = all_sessions

        # Apply limit
        sessions = sessions[:limit]

        if not sessions:
            if status:
                click.echo(f"No sessions found with status: {status}")
            else:
                click.echo("No sessions found. Run 'amplifier run' to create one.")
            return

        click.echo(f"\n📋 Sessions{f' (status={status})' if status else ''}")
        click.echo(f"{'=' * 80}")
        click.echo(f"{'ID':<36} {'Stage':<20} {'Status':<12} {'Created':<20}")
        click.echo(f"{'-' * 80}")

        for sess_info in sessions:
            sid = sess_info.id
            stage = (
                sess_info.current_stage[:17] + "..." if len(sess_info.current_stage) > 20 else sess_info.current_stage
            )
            sess_status = sess_info.status
            created = str(sess_info.created_at)[:19]

            # Color code status
            if sess_status == "completed":
                status_display = click.style(sess_status, fg="green")
            elif sess_status == "failed":
                status_display = click.style(sess_status, fg="red")
            elif sess_status == "running":
                status_display = click.style(sess_status, fg="yellow")
            else:
                status_display = sess_status

            click.echo(f"{sid:<36} {stage:<20} {status_display:<12} {created:<20}")

        click.echo(f"\n📊 Showing {len(sessions)} of {len(all_sessions)} total sessions")

    except Exception as e:
        click.echo(f"❌ Failed to list sessions: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
def demo(workspace: str):
    """Run a real AI demo pipeline that actually uses Claude SDK."""
    import json
    from pathlib import Path
    from .agent import check_sdk_available, SDKNotAvailableError

    # Check SDK availability upfront
    if not check_sdk_available():
        click.echo("\n❌ ERROR: Claude SDK is not available!", err=True)
        click.echo("\nThe demo requires the Claude SDK to be installed.", err=True)
        click.echo("\nPlease install the required dependencies:", err=True)
        click.echo("\n  1. Install Python SDK:", err=True)
        click.echo("     pip install claude-code-sdk", err=True)
        click.echo("\n  2. Install Claude CLI globally:", err=True)
        click.echo("     npm install -g @anthropic-ai/claude-code", err=True)
        click.echo("\n  3. Set your API key:", err=True)
        click.echo("     export ANTHROPIC_API_KEY='sk-ant-...'", err=True)
        click.echo("\n  4. Verify installation:", err=True)
        click.echo("     which claude  # Should show the path to claude CLI", err=True)
        click.echo()
        sys.exit(1)

    workspace_path = Path(workspace).resolve()
    demo_file = Path(__file__).parent / "examples" / "demo_pipeline.json"

    if not demo_file.exists():
        click.echo("❌ Demo pipeline file not found", err=True)
        sys.exit(1)

    with open(demo_file) as f:
        pipeline_config = json.load(f)

    click.echo("✅ Claude SDK detected - ready to run AI tasks")
    click.echo()
    click.echo("🚀 Running real AI demo pipeline...")
    click.echo(f"   Pipeline: {pipeline_config['name']}")
    click.echo(f"   Description: {pipeline_config['description']}")
    click.echo()

    # Create session with initial data
    sess = session_module.create_session(workspace_path)
    sess.data.update(pipeline_config.get("initial_data", {}))

    # Convert JSON tasks to Task objects
    tasks = []
    for task_data in pipeline_config["tasks"]:
        task = orchestrator.Task(
            id=task_data["id"],
            prompt=task_data["prompt"],
            context_keys=task_data.get("context_keys", []),
            save_key=task_data["save_key"],
            required=task_data.get("required", True),
            timeout=task_data.get("timeout", 120),
        )
        tasks.append(task)

    click.echo(f"🆔 Session ID: {sess.id[:8]}...")
    click.echo(f"📋 Tasks to execute: {len(tasks)}")
    click.echo()

    # Run the pipeline
    try:
        orchestrator.run_pipeline_sync(sess, tasks)

        click.echo("\n✨ Pipeline completed successfully!")
        click.echo("\n📊 Results:")
        for key, value in sess.data.items():
            if key not in pipeline_config.get("initial_data", {}):
                click.echo(f"\n   {key}:")
                click.echo(f"   {'-' * 40}")
                click.echo(f"   {value}")

    except orchestrator.PipelineError as e:
        # Check if this is an SDK availability issue
        error_msg = str(e)
        if "SDK not available" in error_msg or "SDKNotAvailableError" in error_msg:
            click.echo("\n❌ SDK Error: Claude SDK is required but not available!", err=True)
            click.echo("\nPlease install the Claude SDK as shown above.", err=True)
            sys.exit(1)
        else:
            click.echo(f"\n⚠️ Pipeline partially completed: {e}", err=True)
            click.echo("\n📊 Partial results:")
            for key, value in e.partial_results.items():
                click.echo(f"   {key}: {value}")
            sys.exit(1)
    except SDKNotAvailableError as e:
        click.echo(f"\n❌ SDK Error: {e}", err=True)
        click.echo("\nThe Claude SDK is required to run this demo.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Pipeline failed: {e}", err=True)
        # Provide more context for common errors
        if "TimeoutError" in str(e) or "timed out" in str(e):
            click.echo("\nThis may indicate the Claude SDK is not properly configured.", err=True)
            click.echo("Please verify your installation and API key.", err=True)
        sys.exit(1)


@cli.command()
@click.argument("description")
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
def develop(workspace: str, description: str):
    """Run full development pipeline: Requirements → Design → Implementation."""
    from pathlib import Path
    from .stages import PipelineExecutor, create_full_development_pipeline
    from .agent import check_sdk_available

    # Check SDK availability upfront
    if not check_sdk_available():
        click.echo("\n❌ ERROR: Claude SDK is required for the development pipeline!", err=True)
        click.echo("\nPlease install the required dependencies:", err=True)
        click.echo("  1. pip install claude-code-sdk", err=True)
        click.echo("  2. npm install -g @anthropic-ai/claude-code", err=True)
        click.echo("  3. export ANTHROPIC_API_KEY='sk-ant-...'", err=True)
        sys.exit(1)

    workspace_path = Path(workspace).resolve()

    # Ensure workspace exists
    if not workspace_path.exists():
        click.echo("🔧 Initializing workspace...")
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "sessions").mkdir(exist_ok=True)
        (workspace_path / "stages").mkdir(exist_ok=True)
        (workspace_path / "pipelines").mkdir(exist_ok=True)

    click.echo("\n🚀 Starting Full Development Pipeline")
    click.echo("\n📝 Project Description:")
    click.echo(f"   {description}\n")

    try:
        # Create and execute pipeline
        pipeline = create_full_development_pipeline(description, workspace_path)
        executor = PipelineExecutor(workspace_path)

        # The executor returns results with the session ID embedded
        # We need to capture the session from the executor
        results = executor.execute_pipeline(pipeline)

        # Extract session ID from the pipeline results file path
        # The executor saves results to pipelines/<session_id>_results.json
        import json

        results_files = list((workspace_path / "pipelines").glob("*_results.json"))
        if results_files:
            # Get the most recent results file
            latest_result = max(results_files, key=lambda p: p.stat().st_mtime)
            with open(latest_result) as f:
                result_data = json.load(f)
                session_id = result_data.get("session_id", "unknown")
        else:
            session_id = "unknown"

        # Report final status
        successful = sum(1 for r in results.values() if r["status"] == "success")
        if successful == len(results):
            click.echo("\n✅ All stages completed successfully!")

            # Load the session data to get tool info
            session_file = workspace_path / "sessions" / f"{session_id}.json"
            if session_file.exists():
                with open(session_file) as f:
                    session_data = json.load(f)

                # Check for new tool generation format
                if "generated_tool_info" in session_data:
                    tool_info_str = session_data["generated_tool_info"]
                    if isinstance(tool_info_str, str):
                        try:
                            tool_info = json.loads(tool_info_str)
                            if tool_info.get("status") == "generated":
                                click.echo("\n🛠️  Generated Tool:")
                                click.echo(f"   Name: {tool_info['tool_name']}")
                                click.echo(f"   Location: {tool_info['tool_path']}")
                                click.echo("\n📁 Files Created:")
                                for file_path in tool_info.get("files_created", []):
                                    # Show just the filename
                                    filename = Path(file_path).name
                                    click.echo(f"   - {filename}")

                                # Show how to use the tool
                                tool_path = Path(tool_info["tool_path"])
                                click.echo("\n💡 To use your generated tool:")
                                click.echo(f"   cd {tool_path}")
                                click.echo("   make help               # See available commands")
                                click.echo("   make run                # Run the tool")
                                click.echo(f"   python -m amplifier_workspace.tools.{tool_path.name}.cli --help")
                        except json.JSONDecodeError:
                            pass

            # Fallback to old format if no tool info found
            else:
                # Show where the generated files are
                if "code_generation" in results and results["code_generation"]["status"] == "success":
                    click.echo("\n📁 Generated Files:")
                    code_dir = workspace_path / "generated" / session_id
                    if code_dir.exists():
                        click.echo(f"   Code: {code_dir}")
                        # List the generated files
                        for file in sorted(code_dir.glob("*.py")):
                            click.echo(f"     - {file.name}")

                if "test_generation" in results and results["test_generation"]["status"] == "success":
                    test_dir = workspace_path / "tests" / session_id
                    if test_dir.exists():
                        click.echo(f"   Tests: {test_dir}")
                        # List the test files
                        for file in sorted(test_dir.glob("*.py")):
                            click.echo(f"     - {file.name}")

                click.echo("\n💡 To run the tests:")
                click.echo(f"   cd {workspace_path}")
                click.echo(f"   pytest tests/{session_id}/")
        else:
            click.echo("\n⚠️  Some stages failed or were skipped.")
            click.echo("   Check the pipeline results for details.")

    except Exception as e:
        click.echo(f"\n❌ Pipeline failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--workspace",
    default="./amplifier_workspace",
    help="Workspace directory path",
    type=click.Path(),
)
def example(workspace: str):
    """Run a simple example pipeline without a task file (simulated)."""
    workspace_path = Path(workspace).resolve()

    # Ensure workspace exists
    if not workspace_path.exists():
        click.echo("🔧 Workspace not found, initializing...")
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "sessions").mkdir(exist_ok=True)
        (workspace_path / "results").mkdir(exist_ok=True)

    try:
        click.echo("🎯 Running example pipeline...")
        click.echo("   This demonstrates a simple 3-task pipeline\n")

        # Create session
        sess = session_module.create_session(workspace_path)
        sess.data["name"] = "example_demo"
        sess.data["type"] = "example"
        session_module.save_checkpoint(sess)
        session_id = sess.id

        click.echo(f"🆔 Session ID: {session_id[:8]}...")

        # No orchestrator needed for example

        # Define example tasks
        example_tasks = [
            {"id": "fetch_data", "name": "Fetching sample data", "duration": 1},
            {"id": "process_data", "name": "Processing data", "duration": 2},
            {"id": "save_results", "name": "Saving results", "duration": 1},
        ]

        click.echo("🚀 Executing tasks...\n")

        # Execute each task with visual feedback
        for i, task in enumerate(example_tasks, 1):
            click.echo(f"[{i}/{len(example_tasks)}] {task['name']}...")

            # Simulate task execution with progress bar
            with click.progressbar(
                length=task["duration"] * 10,
                label=f"    {task['id']}",
                show_percent=False,
                width=30,
            ) as bar:
                import time

                for _ in range(task["duration"] * 10):
                    time.sleep(0.1)
                    bar.update(1)

            click.echo(f"    ✅ {task['id']} completed\n")

        # Update session
        session_module.update_session_status(sess, "completed")

        click.echo("✨ Example pipeline completed successfully!")
        click.echo(f"📂 Results would be saved in: {workspace_path / 'results' / session_id}")
        click.echo("\n💡 To run your own pipeline:")
        click.echo("   1. Create a task JSON file")
        click.echo("   2. Run: amplifier run <your-task-file.json>")

    except Exception as e:
        click.echo(f"❌ Example failed: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
