#!/usr/bin/env python3
"""Test parallel execution behavior in Claude Code agents."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class TaskExecution:
    """Record of a task execution."""

    task_name: str
    start_time: datetime
    end_time: datetime
    agent_type: str

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()


class ParallelExecutionTester:
    """Test parallel vs sequential execution patterns."""

    def __init__(self):
        self.executions: list[TaskExecution] = []

    def analyze_execution_pattern(self, executions: list[TaskExecution]) -> dict[str, Any]:
        """Analyze whether tasks were executed in parallel or sequentially."""
        if not executions:
            return {"pattern": "none", "parallelism_score": 0}

        # Sort by start time
        sorted_execs = sorted(executions, key=lambda x: x.start_time)

        # Check for overlapping executions
        overlaps = 0
        max_concurrent = 1
        current_concurrent = []

        for exec in sorted_execs:
            # Remove finished tasks
            current_concurrent = [e for e in current_concurrent if e.end_time > exec.start_time]
            # Add current task
            current_concurrent.append(exec)
            max_concurrent = max(max_concurrent, len(current_concurrent))

            # Count overlaps
            for other in sorted_execs:
                if other != exec and other.start_time < exec.end_time and other.end_time > exec.start_time:
                    overlaps += 1

        # Calculate parallelism score (0 = sequential, 1 = fully parallel)
        if len(executions) > 1:
            parallelism_score = overlaps / (len(executions) - 1)
        else:
            parallelism_score = 0

        # Determine pattern
        if parallelism_score > 0.7:
            pattern = "parallel"
        elif parallelism_score > 0.3:
            pattern = "mixed"
        else:
            pattern = "sequential"

        return {
            "pattern": pattern,
            "parallelism_score": parallelism_score,
            "max_concurrent": max_concurrent,
            "total_tasks": len(executions),
            "overlaps": overlaps // 2,  # Divide by 2 since we count each overlap twice
        }

    def simulate_multi_file_analysis(self, parallel: bool = False) -> list[TaskExecution]:
        """Simulate analyzing multiple files - a clearly parallelizable task."""
        from datetime import timedelta

        files = ["auth.py", "database.py", "api.py"]
        executions = []

        start = datetime.now()

        if parallel:
            # Simulate parallel execution - all start nearly simultaneously
            for i, file in enumerate(files):
                exec_start = start
                # Use timedelta to properly handle time addition
                exec_end = start + timedelta(microseconds=100000 + i * 10000)
                executions.append(
                    TaskExecution(
                        task_name=f"Analyze {file}", start_time=exec_start, end_time=exec_end, agent_type="bug-hunter"
                    )
                )
        else:
            # Simulate sequential execution
            current_time = start
            for file in files:
                exec_start = current_time
                # Use timedelta to properly handle time addition
                exec_end = current_time + timedelta(microseconds=100000)
                executions.append(
                    TaskExecution(
                        task_name=f"Analyze {file}", start_time=exec_start, end_time=exec_end, agent_type="bug-hunter"
                    )
                )
                current_time = exec_end

        return executions


def test_parallelism_detection():
    """Test that we can detect parallel vs sequential execution."""
    tester = ParallelExecutionTester()

    print("Testing Parallel Execution Detection")
    print("=" * 50)

    # Test sequential execution
    sequential_execs = tester.simulate_multi_file_analysis(parallel=False)
    seq_analysis = tester.analyze_execution_pattern(sequential_execs)

    print("\n1. Sequential Execution Pattern:")
    print(f"   Pattern: {seq_analysis['pattern']}")
    print(f"   Parallelism Score: {seq_analysis['parallelism_score']:.2f}")
    print(f"   Max Concurrent: {seq_analysis['max_concurrent']}")
    print(f"   Result: {'✗ FAIL - Should be parallel' if seq_analysis['pattern'] == 'sequential' else '✓ PASS'}")

    # Test parallel execution
    parallel_execs = tester.simulate_multi_file_analysis(parallel=True)
    par_analysis = tester.analyze_execution_pattern(parallel_execs)

    print("\n2. Parallel Execution Pattern:")
    print(f"   Pattern: {par_analysis['pattern']}")
    print(f"   Parallelism Score: {par_analysis['parallelism_score']:.2f}")
    print(f"   Max Concurrent: {par_analysis['max_concurrent']}")
    print(f"   Result: {'✓ PASS - Correctly parallel' if par_analysis['pattern'] == 'parallel' else '✗ FAIL'}")

    print("\n" + "=" * 50)

    # Verify test results with assertions
    assert seq_analysis["pattern"] == "sequential", "Sequential pattern should be detected as sequential"
    assert par_analysis["pattern"] == "parallel", "Parallel pattern should be detected as parallel"


def demonstrate_parallelizable_tasks():
    """Demonstrate tasks that should be executed in parallel."""

    print("\nParallelizable Task Examples")
    print("=" * 50)

    examples = [
        {
            "task": "Analyze 3 service implementations",
            "subtasks": [
                "1. Analyze auth-service/main.py",
                "2. Analyze user-service/main.py",
                "3. Analyze payment-service/main.py",
            ],
            "reason": "Independent file analyses with no dependencies",
        },
        {
            "task": "Run multiple test suites",
            "subtasks": ["1. Run unit tests", "2. Run integration tests", "3. Run linting checks"],
            "reason": "Independent test suites can run simultaneously",
        },
        {
            "task": "Gather information from multiple sources",
            "subtasks": [
                "1. Search for authentication patterns",
                "2. Search for database patterns",
                "3. Search for API patterns",
            ],
            "reason": "Independent searches with no shared state",
        },
    ]

    for example in examples:
        print(f"\nTask: {example['task']}")
        print("Parallelizable subtasks:")
        for subtask in example["subtasks"]:
            print(f"   {subtask}")
        print(f"Why parallel: {example['reason']}")

    print("\n" + "=" * 50)
    print("Without parallel execution guidance, these would run sequentially!")


if __name__ == "__main__":
    # Run detection test
    test_parallelism_detection()

    # Show parallelizable examples
    demonstrate_parallelizable_tasks()

    # Summary
    print("\nTest Summary:")
    print("✓ Tests completed - check output above for results")
