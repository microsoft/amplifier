"""Command-line interface for session monitoring and token tracking."""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

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

WORKSPACES_DIR = Path(".codex/workspaces")
DAEMON_PID_FILE = Path(".codex/session_monitor.pid")
DEFAULT_TOML_CONFIG = Path(".codex/config.toml")
LEGACY_JSON_CONFIG = Path(".codex/session_monitor_config.json")


def resolve_workspace_name(workspace: str | None) -> str:
    """Return a sanitized workspace identifier."""
    return workspace or Path.cwd().name


def _read_pid(pid_file: Path) -> int | None:
    """Read a PID from disk, returning None if unavailable."""
    try:
        return int(pid_file.read_text().strip())
    except FileNotFoundError:
        return None
    except ValueError:
        logger.debug("Invalid PID file contents at %s", pid_file)
        return None


def _is_process_alive(pid: int | None) -> bool:
    """Check whether a PID represents a running process."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but may belong to another user; treat as alive.
        return True
    return True


def _ensure_session_pid(workspace: str, override_pid: int | None = None) -> int:
    """Resolve the current session PID, optionally using an override."""
    if override_pid is not None:
        pid = override_pid
    else:
        pid_file = WORKSPACES_DIR / workspace / "session.pid"
        pid = _read_pid(pid_file)
        if pid is None:
            raise click.ClickException(
                f"Session PID file not found or invalid for workspace '{workspace}'. "
                "Pass --pid explicitly or ensure session.pid exists."
            )
    if not _is_process_alive(pid):
        raise click.ClickException(
            f"Process {pid} is not running. Restart the session or provide an updated --pid value."
        )
    return pid


def _parse_toml_config(path: Path, require_section: bool) -> MonitorConfig | None:
    """Load MonitorConfig from a TOML file."""
    if not path.exists():
        return None

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError) as exc:
        logger.error("Failed to read TOML config at %s: %s", path, exc)
        return None

    section: dict[str, Any] | None = None
    if isinstance(data, dict):
        if "session_monitor" in data and isinstance(data["session_monitor"], dict):
            section = data["session_monitor"]
        elif not require_section:
            section = data  # Treat entire file as config

    if not section:
        return None

    return MonitorConfig(**section)


def _parse_json_config(path: Path) -> MonitorConfig | None:
    """Load MonitorConfig from a legacy JSON file."""
    if not path.exists():
        return None

    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read legacy JSON config at %s: %s", path, exc)
        return None

    if not isinstance(data, dict):
        return None

    return MonitorConfig(**data)


def load_monitor_config(config_override: str | None = None) -> tuple[MonitorConfig, str]:
    """Load monitor configuration with override/legacy fallbacks."""
    if config_override:
        override_path = Path(config_override)
        config = None
        if override_path.suffix.lower() == ".json":
            config = _parse_json_config(override_path)
        elif override_path.suffix.lower() in {".toml", ".tml"}:
            config = _parse_toml_config(override_path, require_section=False)
        else:
            raise click.BadParameter("Config override must be a .json or .toml file.", param_hint="--config")

        if not config:
            raise click.ClickException(f"Unable to load config from {override_path}")
        return config, str(override_path)

    config = _parse_toml_config(DEFAULT_TOML_CONFIG, require_section=True)
    if config:
        return config, f"{DEFAULT_TOML_CONFIG}[session_monitor]"

    config = _parse_json_config(LEGACY_JSON_CONFIG)
    if config:
        return config, str(LEGACY_JSON_CONFIG)

    return MonitorConfig(), "defaults"


@click.group()
def cli():
    """Session monitor for token usage tracking and graceful termination."""
    pass


@cli.command("start")
@click.option(
    "--config",
    "config_override",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Override session monitor config file (.toml or .json)",
)
@click.option("--workspace", help="Workspace identifier (auto-detect from cwd if not provided)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def start(config_override: Path | None, workspace: str | None, verbose: bool):
    """Launch the session monitor daemon as a detached background process."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    resolved_workspace = resolve_workspace_name(workspace)
    config_path_str = str(config_override) if config_override else None
    monitor_config, source = load_monitor_config(config_path_str)
    logger.info("Using monitor config from %s (workspace dir: %s)", source, monitor_config.workspace_base_dir)
    monitor_config.workspace_base_dir.mkdir(parents=True, exist_ok=True)

    existing_pid = _read_pid(DAEMON_PID_FILE)
    if _is_process_alive(existing_pid):
        click.echo(click.style(f"Daemon already running (PID: {existing_pid})", fg="yellow"))
        raise click.Abort()
    if existing_pid and DAEMON_PID_FILE.exists():
        logger.info("Removing stale daemon PID file at %s", DAEMON_PID_FILE)
        DAEMON_PID_FILE.unlink(missing_ok=True)

    cmd = [sys.executable, "-m", "amplifier.session_monitor.cli", "_run_daemon"]
    if config_path_str:
        cmd.extend(["--config-path", config_path_str])

    logger.info("Starting session monitor daemon for workspace context: %s", resolved_workspace)
    try:
        process = subprocess.Popen(cmd, start_new_session=True)
    except OSError as exc:
        raise click.ClickException(f"Failed to spawn daemon process: {exc}") from exc

    DAEMON_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    DAEMON_PID_FILE.write_text(str(process.pid))
    click.echo(click.style(f"✓ Session monitor daemon started (PID: {process.pid})", fg="green"))
    click.echo(f"Config source: {source}")


@cli.command("_run_daemon", hidden=True)
@click.option(
    "--config-path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=False,
    help="Internal use: override config file for daemon process.",
)
def run_daemon(config_path: Path | None):
    """Internal entry point that runs the daemon event loop."""
    config_path_str = str(config_path) if config_path else None
    monitor_config, source = load_monitor_config(config_path_str)
    logger.info("Session monitor daemon booting with config source: %s", source)

    try:
        daemon = SessionMonitorDaemon(monitor_config)
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    except Exception as exc:  # pragma: no cover - surfaced via logs
        logger.error("Failed to run daemon: %s", exc)
        raise click.Abort() from exc


@cli.command("stop")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def stop(verbose: bool):
    """Stop the session monitor daemon gracefully."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    pid = _read_pid(DAEMON_PID_FILE)
    if pid is None:
        logger.error("Daemon PID file not found. Is the daemon running?")
        raise click.Abort()

    if not _is_process_alive(pid):
        click.echo(click.style("Daemon PID file exists but process not found", fg="yellow"))
        DAEMON_PID_FILE.unlink(missing_ok=True)
        return

    logger.info("Stopping daemon (PID: %s)", pid)
    try:
        os.kill(pid, signal.SIGTERM)
    except PermissionError as exc:
        raise click.ClickException(f"Insufficient permissions to stop daemon ({exc})") from exc

    time.sleep(2)

    if _is_process_alive(pid):
        logger.warning("Daemon still running after SIGTERM, sending SIGKILL")
        os.kill(pid, signal.SIGKILL)

    DAEMON_PID_FILE.unlink(missing_ok=True)
    click.echo(click.style("✓ Daemon stopped successfully", fg="green"))


@cli.command("status")
@click.option("--workspace", help="Workspace identifier (auto-detect from cwd if not provided)")
@click.option("--clean", is_flag=True, help="Remove stale PID files")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def status(workspace: str | None, clean: bool, verbose: bool):
    """Show session monitor status and active sessions."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    workspace_name = resolve_workspace_name(workspace)

    pid = _read_pid(DAEMON_PID_FILE)
    if _is_process_alive(pid):
        click.echo(click.style(f"✓ Daemon running (PID: {pid})", fg="green"))
    elif pid is not None:
        click.echo(click.style("✗ Daemon PID file exists but process not found", fg="red"))
        if clean:
            DAEMON_PID_FILE.unlink(missing_ok=True)
            click.echo("Removed stale daemon PID file.")
    else:
        click.echo(click.style("✗ Daemon not running", fg="red"))

    # Check token usage
    tracker = TokenTracker()
    usage = tracker.get_current_usage(workspace_name)

    if usage.source == "no_files":
        click.echo(f"Token usage: No session files found for workspace '{workspace_name}'")
    else:
        color = "red" if usage.usage_pct >= 90 else "yellow" if usage.usage_pct >= 80 else "green"
        click.echo(
            click.style(
                f"Token usage: {usage.estimated_tokens:,} tokens ({usage.usage_pct:.1f}%) - {usage.source}", fg=color
            )
        )

    # Check for termination request
    request_file = WORKSPACES_DIR / workspace_name / "termination-request"
    if request_file.exists():
        click.echo(click.style(f"⚠ Termination request pending: {request_file}", fg="yellow"))
    else:
        click.echo("No termination requests pending")

    # Show active sessions
    workspace_dir = WORKSPACES_DIR / workspace_name
    if workspace_dir.exists():
        pid_file = workspace_dir / "session.pid"
        session_pid = _read_pid(pid_file)
        if _is_process_alive(session_pid):
            click.echo(f"Active session: PID {session_pid}")
        elif session_pid is not None:
            click.echo(click.style("Session PID file exists but process not found", fg="red"))
            if clean:
                pid_file.unlink(missing_ok=True)
                click.echo("Removed stale session PID file.")


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
@click.option("--pid", type=int, help="Session PID (defaults to workspace session.pid file)")
@click.option("--notify", is_flag=True, help="Send desktop notification")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def request_termination(
    reason: str,
    continuation_command: str,
    priority: str,
    phase: str | None,
    issue: str | None,
    workspace: str | None,
    pid: int | None,
    notify: bool,
    verbose: bool,
):
    """Create a termination request file for the current session."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Auto-detect workspace if not provided
    workspace_name = resolve_workspace_name(workspace)

    # Get current token usage
    tracker = TokenTracker()
    usage = tracker.get_current_usage(workspace_name)

    # Resolve the session PID
    target_pid = _ensure_session_pid(workspace_name, pid)

    # Create termination request
    request = TerminationRequest(
        reason=TerminationReason(reason),
        phase=phase,
        issue=issue,
        continuation_command=continuation_command,
        priority=TerminationPriority(priority),
        token_usage_pct=usage.usage_pct,
        pid=target_pid,
        workspace_id=workspace_name,
    )

    # Write to file
    workspace_dir = WORKSPACES_DIR / workspace_name
    workspace_dir.mkdir(parents=True, exist_ok=True)
    request_file = workspace_dir / "termination-request"

    with open(request_file, "w") as f:
        json.dump(request.model_dump(mode="json"), f, indent=2)

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

    workspace_name = resolve_workspace_name(workspace)

    tracker = TokenTracker()
    usage = tracker.get_current_usage(workspace_name)

    if usage.source == "no_files":
        click.echo(f"No session files found for workspace '{workspace_name}'")
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
@click.option("--clean", is_flag=True, help="Remove stale session PID files")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def list_sessions(clean: bool, verbose: bool):
    """List all monitored sessions with status."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not WORKSPACES_DIR.exists():
        click.echo("No workspaces found")
        return

    click.echo("Monitored Sessions:")
    click.echo("-" * 60)

    tracker = TokenTracker()

    for workspace_dir in WORKSPACES_DIR.iterdir():
        if not workspace_dir.is_dir():
            continue

        workspace = workspace_dir.name
        click.echo(f"Workspace: {workspace}")

        # Check for active session
        pid_file = workspace_dir / "session.pid"
        pid = _read_pid(pid_file)
        if _is_process_alive(pid):
            click.echo(f"  Session: PID {pid} (running)")
        elif pid is not None:
            click.echo(click.style("  Session: PID file exists but process not found", fg="red"))
            if clean:
                pid_file.unlink(missing_ok=True)
                click.echo("  Cleanup: removed stale session PID file.")
        else:
            click.echo("  Session: No active session")

        # Check for termination request
        request_file = workspace_dir / "termination-request"
        if request_file.exists():
            click.echo(click.style("  Status: Termination requested", fg="yellow"))
        else:
            click.echo("  Status: Active")

        # Show token usage
        usage = tracker.get_current_usage(workspace)
        if usage.source != "no_files":
            color = "red" if usage.usage_pct >= 90 else "yellow" if usage.usage_pct >= 80 else "green"
            click.echo(click.style(f"  Tokens: {usage.usage_pct:.1f}% ({usage.source})", fg=color))

        click.echo()


if __name__ == "__main__":
    cli()
