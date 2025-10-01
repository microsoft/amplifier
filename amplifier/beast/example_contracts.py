"""
Example behavioral contracts showing how to use BEAST for any project.
These demonstrate patterns for creating your own contracts.
"""

import os
import tempfile
from pathlib import Path
from typing import Any

from .contracts import BehavioralContract
from .tracer import ExecutionTrace


class CommandExistsContract(BehavioralContract):
    """Verifies a command exists and is runnable."""

    def __init__(self, command_name: str):
        super().__init__(f"CommandExists:{command_name}")
        self.command_name = command_name
        self.description = f"Verifies '{command_name}' command is installed and can be executed"

    def setup(self) -> dict[str, Any]:
        """Setup test environment."""
        return {"command": self.command_name, "start_time": os.times()}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Try to run the command with --help."""
        return self.tracer.trace_command([context["command"], "--help"])

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify command executed successfully."""
        checks = []
        reasons = []

        # Command should exist (exit code 0 or 1 for --help)
        if trace.exit_code in [0, 1]:
            checks.append(True)
        else:
            checks.append(False)
            reasons.append(f"Command failed with exit code {trace.exit_code}")

        # Should produce some output
        if trace.stdout or trace.stderr:
            checks.append(True)
        else:
            checks.append(False)
            reasons.append("No output produced")

        return all(checks), reasons

    def cleanup(self, context: dict[str, Any]):
        """No cleanup needed for command checking."""
        pass


class FileOperationContract(BehavioralContract):
    """Verifies file operations work correctly."""

    def __init__(self, operation_name: str, test_function):
        super().__init__(f"FileOperation:{operation_name}")
        self.operation_name = operation_name
        self.test_function = test_function
        self.description = f"Tests file {operation_name} operations in temporary directory"

    def setup(self) -> dict[str, Any]:
        """Create test environment."""
        test_dir = tempfile.mkdtemp(prefix="beast_test_")
        test_file = Path(test_dir) / "test.txt"
        test_file.write_text("test content")

        return {"test_dir": test_dir, "test_file": str(test_file), "original_content": "test content"}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Execute the file operation."""
        # Run the test function
        result = self.test_function(context["test_file"])

        # Create a trace from the result
        return ExecutionTrace(
            command=f"test_function({context['test_file']})",
            exit_code=0 if result else 1,
            stdout=str(result) if result else "",
            stderr="" if result else "Operation failed",
            timestamp=os.times().elapsed,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify operation succeeded."""
        if trace.exit_code == 0:
            return True, []
        return False, ["File operation failed"]

    def cleanup(self, context: dict[str, Any]):
        """Clean up test files."""
        import shutil
        from contextlib import suppress

        with suppress(Exception):
            shutil.rmtree(context["test_dir"])


class PerformanceContract(BehavioralContract):
    """Verifies performance requirements are met."""

    def __init__(self, operation_name: str, test_function, max_time_seconds: float):
        super().__init__(f"Performance:{operation_name}")
        self.operation_name = operation_name
        self.test_function = test_function
        self.max_time = max_time_seconds
        self.description = f"Ensures {operation_name} completes within {max_time_seconds}s per iteration"

    def setup(self) -> dict[str, Any]:
        """Setup performance test."""
        return {"max_time": self.max_time, "iterations": 10}  # Reduced for faster testing

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Run performance test."""
        import time

        start_time = time.time()

        # Run multiple iterations
        for _ in range(context["iterations"]):
            self.test_function()

        elapsed = time.time() - start_time
        avg_time = elapsed / context["iterations"]

        return ExecutionTrace(
            command=f"performance_test({self.operation_name})",
            exit_code=0,
            stdout=f"Average time: {avg_time:.4f}s",
            stderr="",
            timestamp=start_time,
            wall_time=elapsed,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify performance meets requirements."""
        avg_time = trace.wall_time / context["iterations"]

        if avg_time <= context["max_time"]:
            return True, []
        return False, [f"Performance requirement not met: {avg_time:.4f}s > {context['max_time']}s"]

    def cleanup(self, context: dict[str, Any]):
        """No cleanup needed for performance testing."""
        pass


class NetworkContract(BehavioralContract):
    """Verifies network operations work correctly."""

    def __init__(self, service_name: str, port: int):
        super().__init__(f"Network:{service_name}")
        self.service_name = service_name
        self.port = port
        self.description = f"Verifies {service_name} is accessible on port {port}"

    def setup(self) -> dict[str, Any]:
        """Setup network test."""
        return {"service": self.service_name, "port": self.port, "host": "localhost"}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Test network connection."""
        import socket

        try:
            # Try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((context["host"], context["port"]))
            sock.close()

            if result == 0:
                return ExecutionTrace(
                    command=f"connect({context['host']}:{context['port']})",
                    exit_code=0,
                    stdout=f"Connected to {context['service']} on port {context['port']}",
                    stderr="",
                    timestamp=os.times().elapsed,
                )
            return ExecutionTrace(
                command=f"connect({context['host']}:{context['port']})",
                exit_code=result,
                stdout="",
                stderr=f"Connection failed: {result}",
                timestamp=os.times().elapsed,
            )
        except Exception as e:
            return ExecutionTrace(
                command=f"connect({context['host']}:{context['port']})",
                exit_code=1,
                stdout="",
                stderr=str(e),
                timestamp=os.times().elapsed,
            )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify network connection succeeded."""
        if trace.exit_code == 0:
            return True, []
        return False, [f"{context['service']} not accessible on port {context['port']}"]

    def cleanup(self, context: dict[str, Any]):
        """No cleanup needed for network testing."""
        pass


# Example of how to use contracts for a specific project
def create_amplifier_contracts():
    """Create contracts specific to the Amplifier project."""
    contracts = []

    # Test that key commands exist
    contracts.append(CommandExistsContract("uv"))
    contracts.append(CommandExistsContract("python"))
    contracts.append(CommandExistsContract("make"))

    # Test file operations
    def test_json_write(filepath):
        import json

        try:
            with open(filepath, "w") as f:
                json.dump({"test": "data"}, f)
            return True
        except Exception:
            return False

    contracts.append(FileOperationContract("json_write", test_json_write))

    # Test performance
    def test_import_speed():
        import importlib

        importlib.import_module("amplifier")

    contracts.append(PerformanceContract("import_amplifier", test_import_speed, 0.1))

    # Import Amplifier-specific contracts
    try:
        from amplifier.beast.amplifier_contracts import CLICommandsActuallyWorkContract
        from amplifier.beast.amplifier_contracts import HealingActuallyHealsContract
        from amplifier.beast.amplifier_contracts import KnowledgeSynthesisProducesOutputContract
        from amplifier.beast.amplifier_contracts import MemoryActuallyPersistsContract

        # Add real Amplifier behavioral contracts
        contracts.append(HealingActuallyHealsContract())
        contracts.append(MemoryActuallyPersistsContract())
        contracts.append(KnowledgeSynthesisProducesOutputContract())
        contracts.append(CLICommandsActuallyWorkContract())
    except ImportError:
        pass  # Not in Amplifier project context

    # Import extended contracts
    try:
        from amplifier.beast.extended_contracts import create_extended_contracts

        # Add extended test contracts
        contracts.extend(create_extended_contracts())
    except ImportError:
        pass  # Extended contracts not available

    return contracts
