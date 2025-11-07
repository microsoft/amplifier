"""Command-line interface for session monitoring and token tracking."""

import asyncio
import json
import logging
import os
from pathlib import Path

import click

from .daemon import SessionMonitorDaemon
from .models import MonitorConfig
from .models import TerminationPriority
from .models import TerminationReason
from .models import TerminationRequest
from .token_tracker import TokenTracker

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Session monitor for token usage tracking and graceful termination."""
    pass


@cli.command("start")
@click.option(
    "--config", type=click.Path(exists=True), default=".codex/session_monitor_config.json", help="Path to config file"
)
@click.option("--workspace", help="Workspace identifier (auto-detect from cwd if not provided)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def start(config: str, workspace: str | None, verbose: bool):
    """Start the session monitor daemon in background."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load or create config
    config_path = Path(config)
    if config_path.exists():
        with open(config_path) as f:
            config_data = json.load(f)
        monitor_config = MonitorConfig(**config_data)
    else:
        monitor_config = MonitorConfig()
        # Save default config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(monitor_config.model_dump(), f, indent=2)

    # Auto-detect workspace if not provided
    if not workspace:
        workspace = Path.cwd().name

    logger.info(f"Starting session monitor daemon for workspace: {workspace}")

    try:
        daemon = SessionMonitorDaemon(monitor_config)
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")
        raise click.Abort()


@cli.command("stop")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def stop(verbose: bool):
    """Stop the session monitor daemon gracefully."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    pid_file = Path(".codex/session_monitor.pid")
    if not pid_file.exists():
        logger.error("Daemon PID file not found. Is the daemon running?")
        raise click.Abort()

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())

        logger.info(f"Stopping daemon (PID: {pid})")
        os.kill(pid, 15)  # SIGTERM

        # Wait for graceful shutdown
        import time

        time.sleep(2)

        # Check if still running
        try:
            os.kill(pid, 0)
            logger.warning("Daemon still running, sending SIGKILL")
            os.kill(pid, 9)  # SIGKILL
        except OSError:
            pass  # Process has exited

        # Remove PID file
        pid_file.unlink()
        logger.info("Daemon stopped successfully")

    except Exception as e:
        logger.error(f"Failed to stop daemon: {e}")
        raise click.Abort()


@cli.command("status")
@click.option("--workspace", help="Workspace identifier (auto-detect from cwd if not provided)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def status(workspace: str | None, verbose: bool):
    """Show session monitor status and active sessions."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Auto-detect workspace if not provided
    if not workspace:
        workspace = Path.cwd().name

    pid_file = Path(".codex/session_monitor.pid")
    daemon_running = pid_file.exists()

    if daemon_running:
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists
            click.echo(click.style(f"✓ Daemon running (PID: {pid})", fg="green"))
        except OSError:
            click.echo(click.style("✗ Daemon PID file exists but process not found", fg="red"))
            daemon_running = False
    else:
        click.echo(click.style("✗ Daemon not running", fg="red"))

    # Check token usage
    tracker = TokenTracker()
    usage = tracker.get_current_usage(workspace)

    if usage.source == "no_files":
        click.echo(f"Token usage: No session files found for workspace '{workspace}'")
    else:
        color = "red" if usage.usage_pct >= 90 else "yellow" if usage.usage_pct >= 80 else "green"
        click.echo(
            click.style(
                f"Token usage: {usage.estimated_tokens:,} tokens ({usage.usage_pct:.1f}%) - {usage.source}", fg=color
            )
        )

    # Check for termination request
    request_file = Path(".codex/workspaces") / workspace / "termination-request"
    if request_file.exists():
        click.echo(click.style(f"⚠ Termination request pending: {request_file}", fg="yellow"))
    else:
        click.echo("No termination requests pending")

    # Show active sessions
    workspace_dir = Path(".codex/workspaces") / workspace
    if workspace_dir.exists():
        pid_file = workspace_dir / "session.pid"
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    session_pid = int(f.read().strip())
                os.kill(session_pid, 0)  # Check if exists
                click.echo(f"Active session: PID {session_pid}")
            except OSError:
                click.echo(click.style("Session PID file exists but process not found", fg="red"))


@cli.command("request-termination")
@click.option(
    "--reason",
    required=True,
    type=click.Choice(["token_limit_approaching", "phase_complete", "error", "manual"]),
    help="Reason for termination request",
)
@click.option("--continuation-command", required=True, help="Command to restart the session")
@click.option(
    "--priority", type=click.Choice(["immediate", "graceful"]), default="graceful", help="Termination priority"
)
@click.option("--phase", help="Current workflow phase")
@click.option("--issue", help="Specific issue description")
@click.option("--workspace", help="Workspace identifier (auto-detect from cwd if not provided)")
@click.option("--notify", is_flag=True, help="Send desktop notification")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def request_termination(
    reason: str,
    continuation_command: str,
    priority: str,
    phase: str | None,
    issue: str | None,
    workspace: str | None,
    notify: bool,
    verbose: bool,
):
    """Create a termination request file for the current session."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Auto-detect workspace if not provided
    if not workspace:
        workspace = Path.cwd().name

    # Get current token usage
    tracker = TokenTracker()
    usage = tracker.get_current_usage(workspace)

    # Get current process ID (assume this is the session process)
    pid = os.getpid()

    # Create termination request
    request = TerminationRequest(
        reason=TerminationReason(reason),
        phase=phase,
        issue=issue,
        continuation_command=continuation_command,
        priority=TerminationPriority(priority),
        token_usage_pct=usage.usage_pct,
        pid=pid,
        workspace_id=workspace,
    )

    # Write to file
    workspace_dir = Path(".codex/workspaces") / workspace
    workspace_dir.mkdir(parents=True, exist_ok=True)
    request_file = workspace_dir / "termination-request"

    with open(request_file, "w") as f:
        json.dump(request.model_dump(), f, indent=2)

    click.echo(click.style(f"✓ Termination request created: {request_file}", fg="green"))
    click.echo(f"  Reason: {reason}")
    click.echo(f"  Priority: {priority}")
    click.echo(f"  Token usage: {usage.usage_pct:.1f}%")
    click.echo(f"  Continuation: {continuation_command}")

    # Send notification if requested
    if notify:
        try:
            from amplifier.utils.notifications import send_notification

            send_notification(
                title="Session Monitor",
                message=f"Termination requested: {reason} ({usage.usage_pct:.1f}% tokens)",
                cwd=os.getcwd(),
            )
        except ImportError:
            logger.debug("Notifications not available")


@cli.command("check-tokens")
@click.option("--workspace", help="Workspace identifier (auto-detect from cwd if not provided)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def check_tokens(workspace: str | None, verbose: bool):
    """Check current token usage for a workspace."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Auto-detect workspace if not provided
    if not workspace:
        workspace = Path.cwd().name

    tracker = TokenTracker()
    usage = tracker.get_current_usage(workspace)

    if usage.source == "no_files":
        click.echo(f"No session files found for workspace '{workspace}'")
        return

    # Determine status and color
    if usage.usage_pct >= 90:
        status = "CRITICAL"
        color = "red"
        symbol = "🔴"
    elif usage.usage_pct >= 80:
        status = "WARNING"
        color = "yellow"
        symbol = "🟡"
    else:
        status = "OK"
        color = "green"
        symbol = "🟢"

    click.echo(click.style(f"{symbol} Token Status: {status}", fg=color))
    click.echo(f"Estimated tokens: {usage.estimated_tokens:,}")
    click.echo(f"Usage percentage: {usage.usage_pct:.1f}%")
    click.echo(f"Source: {usage.source}")


@cli.command("list-sessions")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def list_sessions(verbose: bool):
    """List all monitored sessions with status."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    workspaces_dir = Path(".codex/workspaces")
    if not workspaces_dir.exists():
        click.echo("No workspaces found")
        return

    click.echo("Monitored Sessions:")
    click.echo("-" * 60)

    for workspace_dir in workspaces_dir.iterdir():
        if not workspace_dir.is_dir():
            continue

        workspace = workspace_dir.name
        click.echo(f"Workspace: {workspace}")

        # Check for active session
        pid_file = workspace_dir / "session.pid"
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)  # Check if exists
                click.echo(f"  Session: PID {pid} (running)")
            except OSError:
                click.echo(click.style("  Session: PID file exists but process not found", fg="red"))
        else:
            click.echo("  Session: No active session")

        # Check for termination request
        request_file = workspace_dir / "termination-request"
        if request_file.exists():
            click.echo(click.style("  Status: Termination requested", fg="yellow"))
        else:
            click.echo("  Status: Active")

        # Show token usage
        tracker = TokenTracker()
        usage = tracker.get_current_usage(workspace)
        if usage.source != "no_files":
            color = "red" if usage.usage_pct >= 90 else "yellow" if usage.usage_pct >= 80 else "green"
            click.echo(click.style(f"  Tokens: {usage.usage_pct:.1f}% ({usage.source})", fg=color))

        click.echo()


if __name__ == "__main__":
    cli()
