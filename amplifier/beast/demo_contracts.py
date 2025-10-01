"""
Demo contracts showing BEAST catching real issues.
"""

from typing import Any

from .contracts import BehavioralContract
from .tracer import ExecutionTrace


class BadDirectoryContract(BehavioralContract):
    """Demonstrates catching a real issue - trying to use non-existent directory."""

    def __init__(self):
        super().__init__("BadDirectoryExample")
        self.description = "Attempts to access /nonexistent/directory (should fail!)"

    def setup(self) -> dict[str, Any]:
        """Setup with non-existent directory."""
        return {"bad_dir": "/nonexistent/directory"}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Try to list files in non-existent directory."""
        return self.tracer.trace_command(["ls", context["bad_dir"]])

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """This should fail because directory doesn't exist."""
        if trace.exit_code == 0:
            # If ls succeeded, something is wrong
            return True, []
        # This is expected - directory doesn't exist
        return False, ["Directory access failed as expected - BEAST caught the issue!"]

    def cleanup(self, context: dict[str, Any]):
        """No cleanup needed."""
        pass


class SlowOperationContract(BehavioralContract):
    """Demonstrates catching performance issues."""

    def __init__(self):
        super().__init__("SlowOperationExample")
        self.description = "Tests if sleep operation completes within 0.1s (will fail!)"

    def setup(self) -> dict[str, Any]:
        """Setup performance test."""
        return {"max_time": 0.1}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Run a slow operation."""
        import time

        start = time.time()
        time.sleep(0.5)  # Sleep for 0.5 seconds
        elapsed = time.time() - start

        return ExecutionTrace(
            command="sleep(0.5)",
            exit_code=0,
            stdout=f"Operation took {elapsed:.2f}s",
            stderr="",
            timestamp=start,
            wall_time=elapsed,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Check if operation was fast enough."""
        if trace.wall_time <= context["max_time"]:
            return True, []
        return False, [
            "Performance requirement not met!",
            f"Expected: < {context['max_time']}s",
            f"Actual: {trace.wall_time:.2f}s",
        ]

    def cleanup(self, context: dict[str, Any]):
        """No cleanup needed."""
        pass


def create_demo_contracts():
    """Create demonstration contracts that show failures."""
    return [
        BadDirectoryContract(),
        SlowOperationContract(),
    ]
