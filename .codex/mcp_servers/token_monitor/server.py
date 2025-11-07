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
from base import get_project_root
from base import setup_amplifier_path
from base import success_response

# Initialize FastMCP server
mcp = FastMCP("token_monitor")

# Initialize logger
logger = MCPLogger("token_monitor")


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
        project_root = get_project_root()
        if not setup_amplifier_path(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import token tracker
        try:
            from amplifier.session_monitor.token_tracker import TokenTracker
        except ImportError as e:
            logger.error(f"Failed to import TokenTracker: {e}")
            return error_response("TokenTracker not available", {"import_error": str(e)})

        # Get token usage
        tracker = TokenTracker()
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
        logger.exception("Error getting token usage", e)
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
        project_root = get_project_root()
        if not setup_amplifier_path(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import required modules
        try:
            from amplifier.session_monitor.models import MonitorConfig
            from amplifier.session_monitor.token_tracker import TokenTracker
        except ImportError as e:
            logger.error(f"Failed to import session monitor modules: {e}")
            return error_response("Session monitor modules not available", {"import_error": str(e)})

        # Get token usage and check thresholds
        tracker = TokenTracker()
        config = MonitorConfig()  # Use defaults, could be loaded from config file
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
        logger.exception("Error checking termination recommendation", e)
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
        project_root = get_project_root()
        if not setup_amplifier_path(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Import required modules
        try:
            from amplifier.session_monitor.models import TerminationPriority
            from amplifier.session_monitor.models import TerminationReason
            from amplifier.session_monitor.models import TerminationRequest
            from amplifier.session_monitor.token_tracker import TokenTracker
        except ImportError as e:
            logger.error(f"Failed to import session monitor modules: {e}")
            return error_response("Session monitor modules not available", {"import_error": str(e)})

        # Get current token usage
        tracker = TokenTracker()
        usage = tracker.get_current_usage(workspace_id)

        # Get current process ID (assume this is called from the session process)
        pid = os.getpid()

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
            pid=pid,
            workspace_id=workspace_id,
        )

        # Write to file
        workspace_dir = Path(".codex/workspaces") / workspace_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        request_file = workspace_dir / "termination-request"

        with open(request_file, "w") as f:
            json.dump(request.model_dump(), f, indent=2)

        # Build response
        response_data = {
            "workspace_id": workspace_id,
            "request_file": str(request_file),
            "reason": reason,
            "priority": priority,
            "token_usage_pct": usage.usage_pct,
            "pid": pid,
            "continuation_command": continuation_command,
        }

        logger.info(f"Termination request created: {request_file}")
        return success_response(response_data, {"created_at": request.timestamp.isoformat()})

    except Exception as e:
        logger.exception("Error creating termination request", e)
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
        project_root = get_project_root()
        if not setup_amplifier_path(project_root):
            logger.warning("Failed to set up amplifier path")
            return error_response("Amplifier modules not available")

        # Check daemon status
        pid_file = Path(".codex/session_monitor.pid")
        daemon_running = False
        daemon_pid = None

        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    daemon_pid = int(f.read().strip())
                os.kill(daemon_pid, 0)  # Check if process exists
                daemon_running = True
            except (OSError, ValueError):
                daemon_running = False

        # Check active sessions
        active_sessions = []
        workspaces_dir = Path(".codex/workspaces")
        if workspaces_dir.exists():
            for workspace_dir in workspaces_dir.iterdir():
                if workspace_dir.is_dir():
                    workspace_id = workspace_dir.name
                    session_pid_file = workspace_dir / "session.pid"
                    termination_request = workspace_dir / "termination-request"

                    session_info = {"workspace_id": workspace_id}

                    if session_pid_file.exists():
                        try:
                            with open(session_pid_file) as f:
                                pid = int(f.read().strip())
                            os.kill(pid, 0)  # Check if exists
                            session_info["session_pid"] = pid
                            session_info["session_running"] = True
                        except (OSError, ValueError):
                            session_info["session_running"] = False
                    else:
                        session_info["session_running"] = False

                    session_info["termination_pending"] = termination_request.exists()
                    active_sessions.append(session_info)

        # Build response
        response_data = {
            "daemon_running": daemon_running,
            "daemon_pid": daemon_pid,
            "active_sessions": active_sessions,
            "workspaces_dir": str(workspaces_dir),
        }

        logger.info(
            f"Monitor status retrieved: daemon {'running' if daemon_running else 'stopped'}, {len(active_sessions)} sessions"
        )
        return success_response(response_data)

    except Exception as e:
        logger.exception("Error getting monitor status", e)
        return error_response("Failed to get monitor status", {"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting Token Monitor MCP Server")
    mcp.run()
