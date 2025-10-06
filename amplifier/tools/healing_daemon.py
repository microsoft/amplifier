#!/usr/bin/env python3
"""
Lightweight background healing daemon for Amplifier.

Runs continuously in the background, periodically checking and healing
modules that fall below health thresholds.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from amplifier.tools.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


def _preferred_runtime_roots(project_root: Path | None = None) -> list[Path]:
    """Return candidate directories for runtime state."""

    roots: list[Path] = []

    env_override = os.environ.get("AMPLIFIER_HEALING_HOME") or os.environ.get("AMPLIFIER_DATA_DIR")
    if env_override:
        roots.append(Path(env_override).expanduser())

    if project_root:
        roots.append(project_root / ".amplifier")
        roots.append(project_root / ".data" / "healing")

    # Add home directory if available
    home_path = Path.home() / ".amplifier" if Path.home() else None
    if home_path:
        roots.append(home_path)
    roots.append(Path(tempfile.gettempdir()) / "amplifier")

    return roots


def _resolve_runtime_dir(project_root: Path | None = None) -> Path:
    """Pick a writable runtime directory for logs and daemon metadata."""

    for candidate in _preferred_runtime_roots(project_root):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except (PermissionError, OSError):
            continue

    # As a last resort fall back to current working directory
    fallback = Path.cwd() / ".amplifier"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


_DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = _resolve_runtime_dir(_DEFAULT_PROJECT_ROOT)


def _configure_logging(data_dir: Path) -> None:
    """Configure logging once, tolerating restricted filesystems."""

    if getattr(_configure_logging, "configured", False):
        return

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    try:
        file_handler = logging.FileHandler(data_dir / "healing.log")
        handlers.append(file_handler)
    except (PermissionError, OSError):
        # Fallback silently to console logging when file writes are blocked
        pass

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    logger.propagate = False
    _configure_logging.configured = True


_configure_logging(RUNTIME_DIR)


class HealingDaemon:
    """Background healing service for continuous code improvement."""

    def __init__(
        self,
        project_root: Path = Path("."),
        check_interval: int = 300,  # 5 minutes
        heal_threshold: float = 70.0,
        max_heals_per_run: int = 1,
        enabled: bool = True,
        data_dir: Path | None = None,
    ):
        self.project_root = project_root.resolve()
        self.check_interval = check_interval
        self.heal_threshold = heal_threshold
        self.max_heals_per_run = max_heals_per_run
        self.enabled = enabled
        self.running = False

        # Create data directory
        self.data_dir = (data_dir or RUNTIME_DIR).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        _configure_logging(self.data_dir)

        # PID file for single instance
        self.pid_file = self.data_dir / "healing_daemon.pid"

        # Status file for monitoring
        self.status_file = self.data_dir / "healing_status.json"

        # Initialize components
        self.monitor = HealthMonitor(project_root)

    def start(self) -> None:
        """Start the healing daemon."""
        if not self.enabled:
            logger.info("Healing daemon is disabled")
            return

        # Check if already running
        if self._is_running():
            logger.info("Healing daemon is already running")
            return

        # Write PID file
        self._write_pid()

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(f"Starting healing daemon (PID: {os.getpid()})")
        self.running = True

        # Run the main loop
        asyncio.run(self._main_loop())

    async def _main_loop(self) -> None:
        """Main daemon loop."""
        while self.running:
            try:
                await self._check_and_heal()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in healing loop: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _check_and_heal(self) -> None:
        """Check module health and heal if needed."""
        start_time = time.time()

        logger.debug("Running health check...")

        # Get candidates for healing
        candidates = self.monitor.get_healing_candidates(self.heal_threshold)

        if not candidates:
            logger.debug("No modules need healing")
            self._update_status(
                {"last_check": datetime.now().isoformat(), "candidates_found": 0, "healed": 0, "status": "healthy"}
            )
            return

        logger.info(f"Found {len(candidates)} modules needing healing")

        # Heal up to max_heals_per_run modules
        from amplifier.tools.auto_healer import heal_batch

        results = heal_batch(self.max_heals_per_run, self.heal_threshold, self.project_root)

        healed_count = 0
        failed_count = 0

        for result in results:
            module_path = Path(result.module_path)

            if result.status == "success":
                healed_count += 1
                logger.info(f"✅ Successfully healed {module_path}")
            else:
                failed_count += 1
                logger.warning(f"⚠️ Failed to heal {module_path}: {result.reason}")

        # Update status
        self._update_status(
            {
                "last_check": datetime.now().isoformat(),
                "candidates_found": len(candidates),
                "healed": healed_count,
                "failed": failed_count,
                "duration": time.time() - start_time,
                "status": "active",
            }
        )

    def stop(self) -> None:
        """Stop the healing daemon."""
        logger.info("Stopping healing daemon...")
        self.running = False
        self._cleanup()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)

    def _is_running(self) -> bool:
        """Check if daemon is already running."""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip())

            # Check if process exists
            os.kill(pid, 0)
            return True
        except (ValueError, OSError, ProcessLookupError):
            # PID file exists but process doesn't
            self.pid_file.unlink(missing_ok=True)
            return False

    def _write_pid(self) -> None:
        """Write PID file."""
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

    def _cleanup(self) -> None:
        """Clean up PID and status files."""
        self.pid_file.unlink(missing_ok=True)

        # Write final status
        self._update_status({"last_check": datetime.now().isoformat(), "status": "stopped"})

    def _update_status(self, status: dict) -> None:
        """Update status file."""
        try:
            with open(self.status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update status: {e}")


def get_daemon_status(data_dir: Path | None = None) -> dict | None:
    """Get the current daemon status."""
    runtime_dir = (data_dir or RUNTIME_DIR).resolve()
    return _read_status_file(runtime_dir / "healing_status.json")


def _read_status_file(status_file: Path) -> dict | None:
    """Read a status file if it exists."""

    if not status_file.exists():
        return None

    try:
        with open(status_file) as f:
            return json.load(f)
    except Exception:
        return None


def is_daemon_running(data_dir: Path | None = None) -> bool:
    """Check if the healing daemon is running."""
    runtime_dir = (data_dir or RUNTIME_DIR).resolve()
    pid_file = runtime_dir / "healing_daemon.pid"

    if not pid_file.exists():
        return False

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, OSError, ProcessLookupError):
        return False


def stop_daemon(data_dir: Path | None = None) -> bool:
    """Stop the running daemon."""
    runtime_dir = (data_dir or RUNTIME_DIR).resolve()
    pid_file = runtime_dir / "healing_daemon.pid"

    if not pid_file.exists():
        return False

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        return True
    except Exception as e:
        logger.error(f"Failed to stop daemon: {e}")
        return False


def main():
    """CLI entry point for the healing daemon."""
    import argparse

    parser = argparse.ArgumentParser(description="Amplifier healing daemon")
    parser.add_argument("command", choices=["start", "stop", "status", "restart"])
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds")
    parser.add_argument("--threshold", type=float, default=70.0, help="Health threshold")
    parser.add_argument("--max-heals", type=int, default=1, help="Max heals per run")
    parser.add_argument("--project", type=Path, default=Path("."), help="Project root")
    parser.add_argument("--disable", action="store_true", help="Disable healing")

    args = parser.parse_args()

    if args.command == "start":
        daemon = HealingDaemon(
            project_root=args.project,
            check_interval=args.interval,
            heal_threshold=args.threshold,
            max_heals_per_run=args.max_heals,
            enabled=not args.disable,
        )
        daemon.start()

    elif args.command == "stop":
        if stop_daemon():
            print("Healing daemon stopped")
        else:
            print("Healing daemon not running")

    elif args.command == "status":
        if is_daemon_running():
            print("Healing daemon is running")
            status = get_daemon_status()
            if status:
                print(json.dumps(status, indent=2))
        else:
            print("Healing daemon is not running")

    elif args.command == "restart":
        stop_daemon()
        time.sleep(1)
        daemon = HealingDaemon(
            project_root=args.project,
            check_interval=args.interval,
            heal_threshold=args.threshold,
            max_heals_per_run=args.max_heals,
            enabled=not args.disable,
        )
        daemon.start()


if __name__ == "__main__":
    main()
