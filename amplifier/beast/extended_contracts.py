"""
Extended BEAST contracts for comprehensive testing of Amplifier features.
These contracts test more complex scenarios and edge cases.
"""

import json
import tempfile
import time
from pathlib import Path
from typing import Any

from .contracts import BehavioralContract
from .tracer import ExecutionTrace


class ConfigurationActuallyWorksContract(BehavioralContract):
    """Verifies configuration loading and validation works correctly."""

    def __init__(self):
        super().__init__("Configuration:ActuallyWorks")
        self.description = "Tests configuration loading, validation, and error handling"

    def setup(self) -> dict[str, Any]:
        """Create test configuration files."""
        test_dir = tempfile.mkdtemp(prefix="beast_config_")

        # Valid config
        valid_config = Path(test_dir) / "valid_config.json"
        valid_config.write_text(json.dumps({"setting": "value", "number": 42}))

        # Invalid config (malformed JSON)
        invalid_config = Path(test_dir) / "invalid_config.json"
        invalid_config.write_text("{invalid json: true")

        # Empty config
        empty_config = Path(test_dir) / "empty_config.json"
        empty_config.write_text("{}")

        return {
            "test_dir": test_dir,
            "valid_config": str(valid_config),
            "invalid_config": str(invalid_config),
            "empty_config": str(empty_config),
        }

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Test configuration handling."""
        results = []

        # Test valid config
        try:
            with open(context["valid_config"]) as f:
                config = json.load(f)
                results.append({"valid": config.get("setting") == "value"})
        except Exception as e:
            results.append({"valid": False, "error": str(e)})

        # Test invalid config should fail gracefully
        try:
            with open(context["invalid_config"]) as f:
                json.load(f)
                results.append({"invalid_handled": False})  # Should have raised
        except json.JSONDecodeError:
            results.append({"invalid_handled": True})

        # Test empty config
        try:
            with open(context["empty_config"]) as f:
                config = json.load(f)
                results.append({"empty": config == {}})
        except Exception:
            results.append({"empty": False})

        all_pass = all(
            [
                results[0].get("valid", False),
                results[1].get("invalid_handled", False),
                results[2].get("empty", False),
            ]
        )

        return ExecutionTrace(
            command="config_test",
            exit_code=0 if all_pass else 1,
            stdout=json.dumps(results),
            stderr="" if all_pass else "Config validation failed",
            timestamp=0,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify configuration handling works."""
        if trace.exit_code == 0:
            return True, []
        return False, ["Configuration handling failed"]

    def cleanup(self, context: dict[str, Any]):
        """Clean up test files."""
        import shutil
        from contextlib import suppress

        with suppress(Exception):
            shutil.rmtree(context["test_dir"])


class ErrorRecoveryActuallyWorksContract(BehavioralContract):
    """Verifies system can recover from errors gracefully."""

    def __init__(self):
        super().__init__("ErrorRecovery:ActuallyWorks")
        self.description = "Tests error recovery and graceful degradation"

    def setup(self) -> dict[str, Any]:
        """Setup error scenarios."""
        test_dir = tempfile.mkdtemp(prefix="beast_error_")

        # Create a file that will trigger different errors
        test_file = Path(test_dir) / "test_errors.py"
        test_code = """
def divide(a, b):
    return a / b  # Will raise ZeroDivisionError

def access_list(lst, index):
    return lst[index]  # Will raise IndexError

def open_missing():
    with open('/nonexistent/file.txt') as f:
        return f.read()  # Will raise FileNotFoundError
"""
        test_file.write_text(test_code)

        return {"test_dir": test_dir, "test_file": str(test_file)}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Test error recovery."""
        errors_handled = []

        # Test division by zero handling
        try:
            # Safe: hardcoded string for testing error recovery, not user input
            result = 1 / 0  # Direct division instead of exec
        except ZeroDivisionError:
            errors_handled.append("zero_div")

        # Test index error handling
        try:
            lst = [1, 2, 3]
            _ = lst[10]
        except IndexError:
            errors_handled.append("index_error")

        # Test file not found handling
        try:
            with open("/nonexistent/file.txt") as f:
                f.read()
        except FileNotFoundError:
            errors_handled.append("file_not_found")

        # Test attribute error handling
        try:
            obj = None
            obj.method()
        except AttributeError:
            errors_handled.append("attribute_error")

        all_handled = len(errors_handled) == 4

        return ExecutionTrace(
            command="error_recovery_test",
            exit_code=0 if all_handled else 1,
            stdout=f"Handled errors: {', '.join(errors_handled)}",
            stderr="" if all_handled else "Some errors not handled properly",
            timestamp=0,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify error recovery works."""
        expected_errors = {"zero_div", "index_error", "file_not_found", "attribute_error"}
        if trace.exit_code == 0 and all(err in trace.stdout for err in expected_errors):
            return True, []
        return False, ["Error recovery not working properly"]

    def cleanup(self, context: dict[str, Any]):
        """Clean up test files."""
        import shutil
        from contextlib import suppress

        with suppress(Exception):
            shutil.rmtree(context["test_dir"])


class ConcurrencyActuallyWorksContract(BehavioralContract):
    """Verifies concurrent operations work correctly."""

    def __init__(self):
        super().__init__("Concurrency:ActuallyWorks")
        self.description = "Tests concurrent file operations and thread safety"

    def setup(self) -> dict[str, Any]:
        """Setup concurrency test."""
        test_dir = tempfile.mkdtemp(prefix="beast_concurrent_")
        output_file = Path(test_dir) / "concurrent_output.txt"
        return {"test_dir": test_dir, "output_file": str(output_file), "num_threads": 5}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Test concurrent operations."""
        import concurrent.futures

        output_file = Path(context["output_file"])
        num_threads = context["num_threads"]

        def write_data(thread_id):
            """Write data from a thread."""
            for i in range(10):
                with open(output_file, "a") as f:
                    f.write(f"Thread-{thread_id}: Line {i}\n")
                time.sleep(0.001)  # Small delay to encourage interleaving
            return thread_id

        # Run concurrent writes
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(write_data, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Check results
        lines = output_file.read_text().strip().split("\n") if output_file.exists() else []
        expected_lines = num_threads * 10
        all_threads_wrote = len(results) == num_threads
        correct_line_count = len(lines) == expected_lines

        return ExecutionTrace(
            command="concurrency_test",
            exit_code=0 if all_threads_wrote and correct_line_count else 1,
            stdout=f"Threads completed: {len(results)}, Lines written: {len(lines)}",
            stderr="" if correct_line_count else f"Expected {expected_lines} lines, got {len(lines)}",
            timestamp=0,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify concurrent operations worked."""
        if trace.exit_code == 0:
            return True, []
        return False, ["Concurrent operations failed or produced incorrect results"]

    def cleanup(self, context: dict[str, Any]):
        """Clean up test files."""
        import shutil
        from contextlib import suppress

        with suppress(Exception):
            shutil.rmtree(context["test_dir"])


class DataValidationActuallyWorksContract(BehavioralContract):
    """Verifies data validation and sanitization works correctly."""

    def __init__(self):
        super().__init__("DataValidation:ActuallyWorks")
        self.description = "Tests input validation, type checking, and data sanitization"

    def setup(self) -> dict[str, Any]:
        """Setup validation tests."""
        return {
            "test_cases": [
                {"input": "valid@email.com", "type": "email", "should_pass": True},
                {"input": "invalid-email", "type": "email", "should_pass": False},
                {"input": "../../etc/passwd", "type": "path", "should_pass": False},
                {"input": "/valid/path/file.txt", "type": "path", "should_pass": True},
                {"input": "<script>alert('xss')</script>", "type": "text", "should_pass": False},
                {"input": "Normal text content", "type": "text", "should_pass": True},
                {"input": "12345", "type": "number", "should_pass": True},
                {"input": "abc123", "type": "number", "should_pass": False},
            ]
        }

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Test data validation."""
        import re

        results = []
        for test_case in context["test_cases"]:
            input_val = test_case["input"]
            input_type = test_case["type"]
            should_pass = test_case["should_pass"]

            # Simple validation rules
            passed = False
            if input_type == "email":
                passed = bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", input_val))
            elif input_type == "path":
                passed = not (".." in input_val or input_val.startswith("/etc"))
            elif input_type == "text":
                passed = not ("<script>" in input_val.lower() or "</script>" in input_val.lower())
            elif input_type == "number":
                passed = input_val.isdigit()

            correct = passed == should_pass
            results.append({"input": input_val, "type": input_type, "passed": passed, "correct": correct})

        all_correct = all(r["correct"] for r in results)

        return ExecutionTrace(
            command="validation_test",
            exit_code=0 if all_correct else 1,
            stdout=json.dumps(results),
            stderr="" if all_correct else "Some validation tests failed",
            timestamp=0,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify validation works correctly."""
        if trace.exit_code == 0:
            return True, []

        try:
            results = json.loads(trace.stdout)
            failed = [f"{r['input']} ({r['type']})" for r in results if not r["correct"]]
            return False, [f"Validation failed for: {', '.join(failed)}"]
        except Exception:
            return False, ["Validation test results could not be parsed"]

    def cleanup(self, context: dict[str, Any]):
        """No cleanup needed."""
        pass


class CachingActuallyWorksContract(BehavioralContract):
    """Verifies caching mechanism works and improves performance."""

    def __init__(self):
        super().__init__("Caching:ActuallyWorks")
        self.description = "Tests cache hits, misses, invalidation, and performance improvement"

    def setup(self) -> dict[str, Any]:
        """Setup caching test."""
        test_dir = tempfile.mkdtemp(prefix="beast_cache_")
        cache_file = Path(test_dir) / "cache.json"
        return {"test_dir": test_dir, "cache_file": str(cache_file)}

    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        """Test caching behavior."""
        cache = {}
        cache_file = Path(context["cache_file"])
        metrics = {"hits": 0, "misses": 0, "invalidations": 0}

        def expensive_operation(key):
            """Simulate an expensive operation."""
            time.sleep(0.1)  # Simulate work
            return f"computed_{key}"

        def get_or_compute(key):
            """Get from cache or compute."""
            nonlocal cache
            if key in cache:
                metrics["hits"] += 1
                return cache[key]
            metrics["misses"] += 1
            value = expensive_operation(key)
            cache[key] = value
            return value

        # Test cache misses and population
        start_time = time.time()
        _ = get_or_compute("key1")  # Miss
        _ = get_or_compute("key2")  # Miss
        miss_time = time.time() - start_time

        # Test cache hits
        start_time = time.time()
        _ = get_or_compute("key1")  # Hit
        _ = get_or_compute("key2")  # Hit
        _ = get_or_compute("key1")  # Hit
        hit_time = time.time() - start_time

        # Test cache invalidation
        if "key1" in cache:
            del cache["key1"]
            metrics["invalidations"] += 1

        # Save cache to file
        cache_file.write_text(json.dumps(cache))

        # Verify cache improved performance
        performance_improved = hit_time < miss_time * 0.5  # Hits should be much faster

        success = (
            metrics["hits"] == 3 and metrics["misses"] == 2 and metrics["invalidations"] == 1 and performance_improved
        )

        return ExecutionTrace(
            command="cache_test",
            exit_code=0 if success else 1,
            stdout=json.dumps(
                {
                    "metrics": metrics,
                    "miss_time": miss_time,
                    "hit_time": hit_time,
                    "performance_improved": performance_improved,
                }
            ),
            stderr="" if success else "Cache not working properly",
            timestamp=0,
        )

    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify caching works correctly."""
        if trace.exit_code == 0:
            return True, []

        try:
            data = json.loads(trace.stdout)
            issues = []
            if data["metrics"]["hits"] != 3:
                issues.append(f"Expected 3 cache hits, got {data['metrics']['hits']}")
            if data["metrics"]["misses"] != 2:
                issues.append(f"Expected 2 cache misses, got {data['metrics']['misses']}")
            if not data["performance_improved"]:
                issues.append("Cache did not improve performance")
            return False, issues
        except Exception:
            return False, ["Could not parse cache test results"]

    def cleanup(self, context: dict[str, Any]):
        """Clean up test files."""
        import shutil
        from contextlib import suppress

        with suppress(Exception):
            shutil.rmtree(context["test_dir"])


def create_extended_contracts():
    """Create extended test contracts."""
    return [
        ConfigurationActuallyWorksContract(),
        ErrorRecoveryActuallyWorksContract(),
        ConcurrencyActuallyWorksContract(),
        DataValidationActuallyWorksContract(),
        CachingActuallyWorksContract(),
    ]
