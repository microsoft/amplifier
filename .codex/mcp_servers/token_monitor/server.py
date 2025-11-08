"""
Token Monitor MCP Server for Codex.
Provides programmatic access to token usage monitoring and session termination management.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Import FastMCP for server framework
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import base utilities using absolute imports
from base import MCPLogger
from base import error_response
from base import get_project_root as base_get_project_root
from base import setup_amplifier_path as base_setup_amplifier_path
from base import success_response

# Initialize FastMCP server
mcp = FastMCP("token_monitor")

# Initialize logger
logger = MCPLogger("token_monitor")
WORKSPACES_DIR = Path(".codex/workspaces")


def _package_override(name: str) -> Any:
    """Fetch attribute from the package namespace if present."""
    package_name = __package__
    if package_name is None:
        return None
    package = sys.modules.get(package_name)
    return getattr(package, name, None) if package else None


def _setup_amplifier(project_root: Path) -> bool:
    """Call setup_amplifier_path, allowing tests to override."""
    override = _package_override("setup_amplifier_path")
    func = override if callable(override) else base_setup_amplifier_path
    return bool(func(project_root))


def _project_root() -> Path:
    """Get the project root, allowing tests to override."""
    override = _package_override("get_project_root")
    func = override if callable(override) else base_get_project_root
    result = func()
    if not isinstance(result, Path):
        raise TypeError(f"Expected Path from get_project_root, got {type(result)}")
    return result


def _get_token_tracker_cls():
    """Return the TokenTracker class, honoring overrides."""
    override = _package_override("TokenTracker")
    if override is not None:
        return override

    from amplifier.session_monitor.token_tracker import TokenTracker

    return TokenTracker


def _get_monitor_config_cls():
    """Return the MonitorConfig class, honoring overrides."""
    override = _package_override("MonitorConfig")
    if override is not None:
        return override

    from amplifier.session_monitor.models import MonitorConfig

    return MonitorConfig


def _read_pid(pid_file: Path) -> int | None:
    """Read a PID from a file, returning None if unavailable."""
    try:
        return int(pid_file.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def _is_pid_active(pid: int | None) -> bool:
    """Check whether a PID represents a running process."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _workspace_dir(workspace_id: str) -> Path:
    """Return the workspace directory for a given workspace id."""
    return WORKSPACES_DIR / workspace_id


@mcp.tool()
async def health_check() -> dict[str, Any]:
    """
    Health check for the token monitor MCP server.

    Returns:
        Dictionary containing server metadata and module availability.
    """
    try:
        project_root = _project_root()
        modules_available = _setup_amplifier(project_root)
        response_data = {
            "server": "token_monitor",
            "project_root": str(project_root),
            "modules_available": modules_available,
        }
        return success_response(response_data)
    except Exception as exc:
        logger.exception("Error running token monitor health check")
        return error_response("Failed to run health check", {"error": str(exc)})


@mcp.tool()
async def get_token_usage(workspace_id: str) -> dict[str, Any]:
    """
    Get current token usage snapshot for a workspace.

    Args:
        workspace_id: Identifier for the workspace to check

    Returns:
        Dictionary containing token usage data and metadata
    """
    try:
        logger.info(f"Getting token usage for workspace: {workspace_id}")

        # Set up amplifier path
        project_root = _project_root()
        if not _setup_amplifier(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import token tracker
        try:
            tracker_cls = _get_token_tracker_cls()
        except ImportError as e:
            logger.error(f"Failed to import TokenTracker: {e}")
            return error_response("TokenTracker not available", {"import_error": str(e)})

        # Get token usage
        tracker = tracker_cls()
        usage = tracker.get_current_usage(workspace_id)

        # Build response
        response_data = {
            "workspace_id": workspace_id,
            "token_usage": {
                "estimated_tokens": usage.estimated_tokens,
                "usage_pct": usage.usage_pct,
                "source": usage.source,
                "timestamp": usage.timestamp.isoformat(),
            },
        }

        logger.info(f"Token usage retrieved: {usage.usage_pct:.1f}% from {usage.source}")
        return success_response(response_data)

    except Exception as e:
        logger.exception("Error getting token usage")
        return error_response("Failed to get token usage", {"error": str(e)})


@mcp.tool()
async def check_should_terminate(workspace_id: str) -> dict[str, Any]:
    """
    Check if a session should terminate based on token usage thresholds.

    Args:
        workspace_id: Identifier for the workspace to check

    Returns:
        Dictionary containing termination recommendation and reasoning
    """
    try:
        logger.info(f"Checking termination recommendation for workspace: {workspace_id}")

        # Set up amplifier path
        project_root = _project_root()
        if not _setup_amplifier(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import required modules
        try:
            tracker_cls = _get_token_tracker_cls()
            config_cls = _get_monitor_config_cls()
        except ImportError as e:
            logger.error(f"Failed to import session monitor modules: {e}")
            return error_response("Session monitor modules not available", {"import_error": str(e)})

        # Get token usage and check thresholds
        tracker = tracker_cls()
        config = config_cls()  # Use defaults, could be loaded from config file
        usage = tracker.get_current_usage(workspace_id)

        should_terminate, reason = tracker.should_terminate(usage, config)

        # Build response
        response_data = {
            "workspace_id": workspace_id,
            "should_terminate": should_terminate,
            "reason": reason,
            "token_usage": {
                "estimated_tokens": usage.estimated_tokens,
                "usage_pct": usage.usage_pct,
                "source": usage.source,
                "timestamp": usage.timestamp.isoformat(),
            },
            "thresholds": {
                "warning": config.token_warning_threshold,
                "critical": config.token_critical_threshold,
            },
        }

        logger.info(f"Termination check: {should_terminate} - {reason}")
        return success_response(response_data)

    except Exception as e:
        logger.exception("Error checking termination recommendation")
        return error_response("Failed to check termination recommendation", {"error": str(e)})


@mcp.tool()
async def request_termination(
    workspace_id: str, reason: str, continuation_command: str, priority: str = "graceful"
) -> dict[str, Any]:
    """
    Create a termination request file for programmatic session termination.

    Args:
        workspace_id: Identifier for the workspace
        reason: Reason for termination (token_limit_approaching, phase_complete, error, manual)
        continuation_command: Command to restart the session
        priority: Termination priority (immediate or graceful)

    Returns:
        Dictionary containing request creation status
    """
    try:
        logger.info(f"Creating termination request for workspace: {workspace_id}")

        # Set up amplifier path
        project_root = _project_root()
        if not _setup_amplifier(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import required modules
        try:
            from amplifier.session_monitor.models import TerminationPriority
            from amplifier.session_monitor.models import TerminationReason
            from amplifier.session_monitor.models import TerminationRequest
        except ImportError as e:
            logger.error(f"Failed to import session monitor modules: {e}")
            return error_response("Session monitor modules not available", {"import_error": str(e)})

        # Ensure session PID is available
        workspace_dir = _workspace_dir(workspace_id)
        session_pid_file = workspace_dir / "session.pid"
        session_pid = _read_pid(session_pid_file)
        if session_pid is None:
            return error_response(
                f"No session PID found for workspace '{workspace_id}'",
                {"pid_file": str(session_pid_file)},
            )
        if not _is_pid_active(session_pid):
            return error_response(
                f"Session PID {session_pid} is not running",
                {"pid_file": str(session_pid_file), "pid": session_pid},
            )

        # Get current token usage
        tracker_cls = _get_token_tracker_cls()
        tracker = tracker_cls()
        usage = tracker.get_current_usage(workspace_id)

        # Validate inputs
        try:
            termination_reason = TerminationReason(reason)
            termination_priority = TerminationPriority(priority)
        except ValueError as e:
            return error_response(
                f"Invalid reason or priority: {e}",
                {"valid_reasons": list(TerminationReason), "valid_priorities": list(TerminationPriority)},
            )

        # Create termination request
        request = TerminationRequest(
            reason=termination_reason,
            continuation_command=continuation_command,
            priority=termination_priority,
            token_usage_pct=usage.usage_pct,
            pid=session_pid,
            workspace_id=workspace_id,
        )

        # Write to file
        workspace_dir.mkdir(parents=True, exist_ok=True)
        request_file = workspace_dir / "termination-request"

        with open(request_file, "w") as f:
            json.dump(request.model_dump(mode="json"), f, indent=2)

        # Build response
        response_data: dict[str, Any] = {
            "workspace_id": workspace_id,
            "request_file": str(request_file),
            "reason": reason,
            "priority": priority,
            "token_usage_pct": usage.usage_pct,
            "pid": session_pid,
            "continuation_command": continuation_command,
        }

        logger.info(f"Termination request created: {request_file}")
        return success_response(response_data, {"created_at": request.timestamp.isoformat()})

    except Exception as e:
        logger.exception("Error creating termination request")
        return error_response("Failed to create termination request", {"error": str(e)})


@mcp.tool()
async def get_monitor_status() -> dict[str, Any]:
    """
    Get the current status of the session monitor daemon.

    Returns:
        Dictionary containing daemon status and active sessions
    """
    try:
        logger.info("Getting monitor daemon status")

        # Set up amplifier path
        project_root = _project_root()
        if not _setup_amplifier(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Check daemon status
        pid_file = Path(".codex/session_monitor.pid")
        daemon_running = False
        daemon_pid = _read_pid(pid_file)
        daemon_pid_stale = False

        if daemon_pid is not None:
            if _is_pid_active(daemon_pid):
                daemon_running = True
            else:
                daemon_pid_stale = True

        # Check active sessions
        active_sessions = []
        if WORKSPACES_DIR.exists():
            for workspace_dir in WORKSPACES_DIR.iterdir():
                if workspace_dir.is_dir():
                    workspace_id = workspace_dir.name
                    session_pid_file = workspace_dir / "session.pid"
                    termination_request = workspace_dir / "termination-request"

                    session_info: dict[str, str | int | bool] = {"workspace_id": workspace_id}

                    if session_pid_file.exists():
                        pid = _read_pid(session_pid_file)
                        if pid is not None:
                            session_info["session_pid"] = pid
                        if _is_pid_active(pid):
                            session_info["session_running"] = True
                        else:
                            session_info["session_running"] = False
                            session_info["stale_pid"] = pid is not None
                    else:
                        session_info["session_running"] = False

                    session_info["termination_pending"] = termination_request.exists()
                    active_sessions.append(session_info)

        # Build response
        response_data = {
            "daemon_running": daemon_running,
            "daemon_pid": daemon_pid,
            "daemon_pid_stale": daemon_pid_stale,
            "active_sessions": active_sessions,
            "workspaces_dir": str(WORKSPACES_DIR),
        }

        logger.info(
            f"Monitor status retrieved: daemon {'running' if daemon_running else 'stopped'}, {len(active_sessions)} sessions"
        )
        return success_response(response_data)

    except Exception as e:
        logger.exception("Error getting monitor status")
        return error_response("Failed to get monitor status", {"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting Token Monitor MCP Server")
    mcp.run()
