"""AI-driven smoke test system for Amplifier."""

from amplifier.smoke_tests.runner import AITestRunner
from amplifier.smoke_tests.runner import main as run_smoke_tests

__all__ = ["AITestRunner", "run_smoke_tests"]
