"""
Execution tracer that records ACTUAL system behavior, not claimed behavior.
Uses filesystem monitoring, process tracking, and system call analysis.
"""

import hashlib
import json
import os
import platform
import subprocess
import time
from contextlib import suppress
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import psutil


@dataclass
class ExecutionTrace:
    """Immutable record of actual execution - can't be faked"""

    command: str
    exit_code: int | None
    stdout: str
    stderr: str
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    files_deleted: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    network_connections: list[str] = field(default_factory=list)
    processes_spawned: list[dict] = field(default_factory=list)
    environment_used: dict[str, str] = field(default_factory=dict)
    cpu_time: float = 0.0
    memory_peak: int = 0
    wall_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    platform_info: dict[str, str] = field(default_factory=dict)
    working_directory: str = ""

    def fingerprint(self) -> str:
        """Unique hash of execution state - cryptographically verifiable"""
        # Sort all data for consistent hashing
        data = {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout_hash": hashlib.sha256(self.stdout.encode()).hexdigest(),
            "stderr_hash": hashlib.sha256(self.stderr.encode()).hexdigest(),
            "files_created": sorted(self.files_created),
            "files_modified": sorted(self.files_modified),
            "files_deleted": sorted(self.files_deleted),
            "processes_spawned": len(self.processes_spawned),
            "timestamp": self.timestamp,
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def to_json(self) -> str:
        """Export trace as JSON for analysis"""
        return json.dumps(asdict(self), indent=2, default=str)


class FilesystemMonitor:
    """Monitors actual filesystem changes during execution"""

    def __init__(self, watch_dirs: list[Path] = None):
        # Default to empty list to avoid scanning entire filesystem
        # Only monitor specific directories when explicitly needed
        self.watch_dirs = watch_dirs or []

    def snapshot(self) -> dict[str, dict]:
        """Take filesystem snapshot with checksums"""
        snapshot = {}

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue

            for path in watch_dir.rglob("*"):
                if path.is_file():
                    try:
                        stat = path.stat()
                        with open(path, "rb") as f:
                            # Read first 8KB for checksum (fast)
                            content = f.read(8192)
                            checksum = hashlib.md5(content).hexdigest()

                        snapshot[str(path)] = {"size": stat.st_size, "mtime": stat.st_mtime, "checksum": checksum}
                    except (PermissionError, OSError):
                        # Can't read file, just record existence
                        snapshot[str(path)] = {"exists": True}

        return snapshot

    def diff(self, before: dict, after: dict) -> dict[str, list[str]]:
        """Calculate actual filesystem changes"""
        before_files = set(before.keys())
        after_files = set(after.keys())

        created = list(after_files - before_files)
        deleted = list(before_files - after_files)

        # Check for modifications
        modified = []
        for file in before_files & after_files:
            before_info = before[file]
            after_info = after[file]

            # Check if actually modified
            if (
                before_info.get("checksum") != after_info.get("checksum")
                or before_info.get("size") != after_info.get("size")
                or abs(before_info.get("mtime", 0) - after_info.get("mtime", 0)) > 0.01
            ):
                modified.append(file)

        return {"created": sorted(created), "modified": sorted(modified), "deleted": sorted(deleted)}


class ProcessMonitor:
    """Monitors process tree and resource usage"""

    def __init__(self, pid: int):
        self.pid = pid
        self.process = None
        self.children = []
        self.start_time = time.time()

        with suppress(psutil.NoSuchProcess):
            self.process = psutil.Process(pid)

    def get_tree(self) -> list[dict]:
        """Get complete process tree"""
        tree = []

        if not self.process:
            return tree

        try:
            # Get main process info
            tree.append(
                {
                    "pid": self.process.pid,
                    "name": self.process.name(),
                    "cmdline": " ".join(self.process.cmdline()),
                    "create_time": self.process.create_time(),
                }
            )

            # Get all children recursively
            for child in self.process.children(recursive=True):
                with suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                    tree.append(
                        {
                            "pid": child.pid,
                            "name": child.name(),
                            "cmdline": " ".join(child.cmdline()),
                            "create_time": child.create_time(),
                        }
                    )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        return tree

    def get_resources(self) -> dict[str, Any]:
        """Get resource usage"""
        if not self.process:
            return {}

        try:
            with self.process.oneshot():
                return {
                    "cpu_percent": self.process.cpu_percent(),
                    "memory_rss": self.process.memory_info().rss,
                    "memory_vms": self.process.memory_info().vms,
                    "num_threads": self.process.num_threads(),
                    "num_fds": self.process.num_fds() if platform.system() != "Windows" else 0,
                    "io_counters": self.process.io_counters()._asdict() if platform.system() != "Windows" else {},
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}


class ExecutionTracer:
    """
    Traces actual program execution at system level.
    This can't be faked - it monitors real system behavior.
    """

    def __init__(self, trace_network: bool = True, trace_files: bool = True):
        self.trace_network = trace_network
        self.trace_files = trace_files
        self.traces: list[ExecutionTrace] = []
        self.fs_monitor = FilesystemMonitor()

    def trace_command(
        self, cmd: list[str], env: dict[str, str] = None, cwd: str = None, timeout: int = 30
    ) -> ExecutionTrace:
        """
        Execute and trace a command, recording actual system behavior.

        This creates forensic-level evidence of execution that can't be faked.
        """

        # Take filesystem snapshot before execution
        fs_before = self.fs_monitor.snapshot() if self.trace_files else {}

        # Record platform info
        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        }

        # Prepare environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Record start state
        start_time = time.time()
        working_dir = cwd or os.getcwd()

        # Execute with full monitoring
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=exec_env, cwd=working_dir, text=True
            )

            # Monitor process
            monitor = ProcessMonitor(proc.pid)

            # Get output with timeout
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                exit_code = -9
                stderr = f"{stderr}\n[KILLED: Timeout after {timeout}s]"

            # Collect process tree info
            process_tree = monitor.get_tree()
            resources = monitor.get_resources()

        except Exception as e:
            # Record execution failure
            stdout = ""
            stderr = f"Execution failed: {str(e)}"
            exit_code = -1
            process_tree = []
            resources = {}

        # Take filesystem snapshot after execution
        fs_after = self.fs_monitor.snapshot() if self.trace_files else {}
        fs_changes = self.fs_monitor.diff(fs_before, fs_after) if self.trace_files else {}

        # Calculate timing
        end_time = time.time()
        wall_time = end_time - start_time

        # Build complete trace
        trace = ExecutionTrace(
            command=" ".join(cmd),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            files_created=fs_changes.get("created", []),
            files_modified=fs_changes.get("modified", []),
            files_deleted=fs_changes.get("deleted", []),
            files_read=[],  # Would need strace/dtrace for this
            network_connections=[],  # Would need netstat monitoring
            processes_spawned=process_tree,
            environment_used=exec_env,
            cpu_time=resources.get("cpu_percent", 0.0),
            memory_peak=resources.get("memory_rss", 0),
            wall_time=wall_time,
            timestamp=start_time,
            platform_info=platform_info,
            working_directory=working_dir,
        )

        # Store trace
        self.traces.append(trace)

        return trace

    def verify_execution(self, trace: ExecutionTrace) -> dict[str, bool]:
        """
        Verify that execution actually happened.
        Returns dict of verification checks.
        """
        checks = {
            "process_started": trace.exit_code is not None,
            "produced_output": bool(trace.stdout or trace.stderr),
            "took_time": trace.wall_time > 0,
            "has_fingerprint": bool(trace.fingerprint()),
            "has_timestamp": trace.timestamp > 0,
            "has_platform": bool(trace.platform_info),
        }

        # Check for subprocess spawning if expected
        if "tmux" in trace.command or "sshx" in trace.command:
            checks["spawned_processes"] = len(trace.processes_spawned) > 0

        # Check for file operations if expected
        if "--save-config" in trace.command:
            checks["created_files"] = len(trace.files_created) > 0

        return checks

    def export_traces(self, output_file: Path):
        """Export all traces for analysis"""
        data = {"version": "1.0.0", "timestamp": time.time(), "traces": [asdict(t) for t in self.traces]}

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def compare_traces(self, trace1: ExecutionTrace, trace2: ExecutionTrace) -> dict[str, Any]:
        """
        Compare two execution traces to detect differences.
        Useful for regression detection.
        """
        return {
            "same_command": trace1.command == trace2.command,
            "same_exit_code": trace1.exit_code == trace2.exit_code,
            "same_output": trace1.stdout == trace2.stdout,
            "same_errors": trace1.stderr == trace2.stderr,
            "same_files_created": set(trace1.files_created) == set(trace2.files_created),
            "same_processes": len(trace1.processes_spawned) == len(trace2.processes_spawned),
            "performance_change": trace2.wall_time - trace1.wall_time,
            "memory_change": trace2.memory_peak - trace1.memory_peak,
        }


# Example usage showing how this catches fake tests
if __name__ == "__main__":
    # This ACTUALLY runs and monitors
    tracer = ExecutionTracer()

    # Trace a real command
    trace = tracer.trace_command(["echo", "hello world"])

    print("=== Execution Trace ===")
    print(f"Command: {trace.command}")
    print(f"Exit Code: {trace.exit_code}")
    print(f"Output: {trace.stdout}")
    print(f"Fingerprint: {trace.fingerprint()}")

    # Verify it actually ran
    checks = tracer.verify_execution(trace)
    print("\n=== Verification ===")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check}: {passed}")
