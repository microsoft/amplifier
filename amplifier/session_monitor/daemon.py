"""Session monitor daemon for handling termination requests and session restarts."""

import asyncio
import json
import logging
import os
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from .models import MonitorConfig
from .models import TerminationPriority
from .models import TerminationRequest

logger = logging.getLogger(__name__)


class SessionMonitorDaemon:
    """Async daemon for monitoring session termination requests and managing restarts.

    Runs continuously, scanning for termination request files and handling
    graceful session termination with automatic restart capability.
    """

    def __init__(self, config: MonitorConfig):
        """Initialize the daemon with configuration.

        Args:
            config: Monitor configuration
        """
        self.config = config
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.daemon")

        # Write daemon PID file
        self.pid_file = Path(".codex/session_monitor.pid")
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Start the monitor daemon."""
        self.running = True
        self.logger.info("Starting session monitor daemon")

        # Write PID file
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

        try:
            while self.running:
                await self._scan_and_process_requests()
                await asyncio.sleep(self.config.check_interval_seconds)
        except Exception as e:
            self.logger.error(f"Daemon error: {e}")
            raise
        finally:
            # Cleanup PID file
            if self.pid_file.exists():
                self.pid_file.unlink()

    async def stop(self):
        """Stop the monitor daemon gracefully."""
        self.logger.info("Stopping session monitor daemon")
        self.running = False

    async def _scan_and_process_requests(self):
        """Scan for termination request files and process them."""
        try:
            workspace_dirs = self._scan_workspaces()

            for workspace_dir in workspace_dirs:
                request_file = workspace_dir / "termination-request"
                if request_file.exists():
                    try:
                        await self.handle_termination_request(request_file)
                    except Exception as e:
                        self.logger.error(f"Error processing request in {workspace_dir}: {e}")

        except Exception as e:
            self.logger.error(f"Error scanning workspaces: {e}")

    def _scan_workspaces(self) -> list[Path]:
        """Find all workspace directories with potential termination requests.

        Returns:
            List of workspace directory paths
        """
        workspaces = []
        if self.config.workspace_base_dir.exists():
            for workspace_dir in self.config.workspace_base_dir.iterdir():
                if workspace_dir.is_dir():
                    workspaces.append(workspace_dir)
        return workspaces

    async def _load_termination_request(self, request_file: Path) -> TerminationRequest:
        """Load and parse a termination request file.

        Args:
            request_file: Path to the termination request JSON file

        Returns:
            Parsed TerminationRequest object

        Raises:
            FileNotFoundError: If request file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        with open(request_file) as f:
            data = json.load(f)
        return TerminationRequest(**data)

    async def handle_termination_request(self, request_file: Path):
        """Handle a termination request file.

        Args:
            request_file: Path to the termination request file
        """
        try:
            request = await self._load_termination_request(request_file)
            self.logger.info(f"Processing termination request: {request.reason} for PID {request.pid}")

            # Validate request
            if not await self._validate_request(request):
                self.logger.warning(f"Invalid termination request: {request}")
                return

            # Handle termination
            await self._terminate_session(request)

            # Remove request file
            request_file.unlink()
            self.logger.info("Termination request processed and removed")

        except Exception as e:
            self.logger.error(f"Error handling termination request {request_file}: {e}")

    async def _validate_request(self, request: TerminationRequest) -> bool:
        """Validate a termination request.

        Args:
            request: Termination request to validate

        Returns:
            True if request is valid
        """
        # Check if PID exists
        try:
            os.kill(request.pid, 0)  # Signal 0 just checks if process exists
            return True
        except OSError:
            self.logger.warning(f"Process {request.pid} does not exist")
            return False

    async def _terminate_session(self, request: TerminationRequest):
        """Terminate a session process and restart it.

        Args:
            request: Termination request with process details
        """
        pid = request.pid
        self.logger.info(f"Terminating session PID {pid} ({request.priority})")

        # Send SIGTERM first
        try:
            os.kill(pid, signal.SIGTERM)
            self.logger.debug(f"Sent SIGTERM to PID {pid}")
        except OSError as e:
            self.logger.error(f"Failed to send SIGTERM to PID {pid}: {e}")
            return

        # Wait for graceful shutdown
        wait_time = 30 if request.priority == TerminationPriority.GRACEFUL else 5
        await self._wait_for_process_exit(pid, wait_time)

        # Check if process is still running
        try:
            os.kill(pid, 0)
            # Process still exists, send SIGKILL
            self.logger.warning(f"Process {pid} still running after {wait_time}s, sending SIGKILL")
            os.kill(pid, signal.SIGKILL)
            await self._wait_for_process_exit(pid, 5)
        except OSError:
            # Process has exited
            pass

        # Restart session
        await self._restart_session(request)

    async def _wait_for_process_exit(self, pid: int, timeout_seconds: int):
        """Wait for a process to exit.

        Args:
            pid: Process ID to wait for
            timeout_seconds: Maximum time to wait
        """
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                os.kill(pid, 0)
                await asyncio.sleep(0.1)
            except OSError:
                # Process has exited
                return
        # Timeout reached

    async def _restart_session(self, request: TerminationRequest):
        """Restart a session with the continuation command.

        Args:
            request: Termination request with continuation command
        """
        command = request.continuation_command
        self.logger.info(f"Restarting session with command: {command}")

        workspace_dir = self.config.workspace_base_dir / request.workspace_id
        if not workspace_dir.exists():
            self.logger.error("Workspace %s does not exist; skipping restart.", workspace_dir)
            return

        command_parts = shlex.split(command)

        # Implement exponential backoff for retries
        backoff = self.config.restart_backoff_seconds
        max_attempts = self.config.max_restart_attempts

        for attempt in range(max_attempts):
            try:
                # Start the process
                process = await asyncio.create_subprocess_exec(
                    *command_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(workspace_dir)
                )

                # Write new PID file
                pid_file = workspace_dir / "session.pid"
                with open(pid_file, "w") as f:
                    f.write(str(process.pid))

                self.logger.info(f"Session restarted with new PID {process.pid}")
                return

            except Exception as e:
                self.logger.error(f"Failed to restart session (attempt {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff

        self.logger.error(f"Failed to restart session after {max_attempts} attempts")

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check of the daemon.

        Returns:
            Health status dictionary
        """
        status = {
            "daemon_running": self.running,
            "pid": os.getpid(),
            "last_check": time.time(),
            "active_sessions": 0,
            "workspace_base_dir": str(self.config.workspace_base_dir),
        }

        # Count active sessions
        try:
            for workspace_dir in self._scan_workspaces():
                pid_file = workspace_dir / "session.pid"
                if pid_file.exists():
                    try:
                        with open(pid_file) as f:
                            pid = int(f.read().strip())
                        os.kill(pid, 0)  # Check if process exists
                        status["active_sessions"] += 1
                    except (OSError, ValueError):
                        # Process doesn't exist or invalid PID
                        pass
        except Exception as e:
            status["error"] = str(e)

        return status
