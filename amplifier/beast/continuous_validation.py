"""
Continuous Validation Runner - Monitors system behavior over time.
Enables autonomous improvement by detecting degradations and successes.
"""

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .contracts import ContractVerifier
from .example_contracts import CommandExistsContract
from .example_contracts import create_amplifier_contracts


@dataclass
class ValidationRun:
    """Record of a validation run."""

    timestamp: float
    total_contracts: int
    passed: int
    failed: int
    success_rate: float
    failures: list[dict]
    execution_time: float


class ValidationHistory:
    """Tracks validation results over time."""

    def __init__(self, db_path: str = "validation_history.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        """Create database schema."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                total_contracts INTEGER,
                passed INTEGER,
                failed INTEGER,
                success_rate REAL,
                failures TEXT,
                execution_time REAL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS failure_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE,
                first_seen REAL,
                last_seen REAL,
                occurrence_count INTEGER,
                contracts_affected TEXT
            )
        """)

        self.conn.commit()

    def record_run(self, run: ValidationRun):
        """Record a validation run."""
        self.conn.execute(
            """
            INSERT INTO validation_runs
            (timestamp, total_contracts, passed, failed, success_rate, failures, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run.timestamp,
                run.total_contracts,
                run.passed,
                run.failed,
                run.success_rate,
                json.dumps(run.failures),
                run.execution_time,
            ),
        )

        # Update failure patterns
        for failure in run.failures:
            pattern = f"{failure['contract']}:{','.join(failure['reasons'])}"
            cursor = self.conn.execute(
                "SELECT id, occurrence_count FROM failure_patterns WHERE pattern = ?", (pattern,)
            )
            existing = cursor.fetchone()

            if existing:
                self.conn.execute(
                    """
                    UPDATE failure_patterns
                    SET last_seen = ?, occurrence_count = ?
                    WHERE id = ?
                """,
                    (run.timestamp, existing[1] + 1, existing[0]),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO failure_patterns
                    (pattern, first_seen, last_seen, occurrence_count, contracts_affected)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (pattern, run.timestamp, run.timestamp, 1, failure["contract"]),
                )

        self.conn.commit()

    def get_trends(self, hours: int = 24) -> dict[str, Any]:
        """Analyze trends over specified time period."""
        cutoff = time.time() - (hours * 3600)

        cursor = self.conn.execute(
            """
            SELECT * FROM validation_runs
            WHERE timestamp > ?
            ORDER BY timestamp
        """,
            (cutoff,),
        )

        runs = cursor.fetchall()

        if not runs:
            return {"no_data": True}

        # Calculate trends
        success_rates = [r[5] for r in runs]  # success_rate column
        avg_success = sum(success_rates) / len(success_rates)

        # Detect degradation
        if len(success_rates) >= 2:
            recent_avg = sum(success_rates[-3:]) / len(success_rates[-3:])
            older_avg = sum(success_rates[:-3]) / max(1, len(success_rates[:-3]))
            degrading = recent_avg < older_avg - 5  # 5% threshold
        else:
            degrading = False

        # Get recurring failures
        cursor = self.conn.execute(
            """
            SELECT pattern, occurrence_count
            FROM failure_patterns
            WHERE last_seen > ?
            ORDER BY occurrence_count DESC
            LIMIT 5
        """,
            (cutoff,),
        )

        recurring = cursor.fetchall()

        return {
            "total_runs": len(runs),
            "average_success_rate": avg_success,
            "is_degrading": degrading,
            "recurring_failures": recurring,
            "latest_success_rate": success_rates[-1] if success_rates else 0,
        }


class ContinuousValidator:
    """Runs validation continuously and enables autonomous improvement."""

    def __init__(
        self,
        interval_seconds: int = 300,  # 5 minutes
        history_db: str = "validation_history.db",
    ):
        self.interval = interval_seconds
        self.history = ValidationHistory(history_db)
        self.running = False
        self.thread = None
        self.contracts = self._load_contracts()
        self.improvement_callbacks = []

    def _load_contracts(self) -> list:
        """Load all contracts for validation."""
        # Check if we're in the Amplifier project
        if Path("amplifier/__init__.py").exists():
            return create_amplifier_contracts()

        # Default contracts for any project
        return [
            CommandExistsContract("python"),
            CommandExistsContract("git"),
            CommandExistsContract("make"),
        ]

    def add_improvement_callback(self, callback):
        """Add callback for autonomous improvement triggers."""
        self.improvement_callbacks.append(callback)

    def _run_validation(self) -> ValidationRun:
        """Run a single validation cycle."""
        start_time = time.time()

        verifier = ContractVerifier()
        for contract in self.contracts:
            verifier.add_contract(contract)

        report = verifier.verify_all(verbose=False)

        return ValidationRun(
            timestamp=time.time(),
            total_contracts=report["summary"]["total_contracts"],
            passed=report["summary"]["passed"],
            failed=report["summary"]["failed"],
            success_rate=report["summary"]["success_rate"],
            failures=report["failures"],
            execution_time=time.time() - start_time,
        )

    def _validation_loop(self):
        """Main validation loop."""
        while self.running:
            try:
                # Run validation
                run = self._run_validation()
                self.history.record_run(run)

                # Check for improvement opportunities
                self._check_for_improvements(run)

                # Log status
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"Validation: {run.passed}/{run.total_contracts} passed "
                    f"({run.success_rate:.1f}%)"
                )

                if run.failures:
                    for failure in run.failures[:2]:
                        print(f"  Failed: {failure['contract']}")

            except Exception as e:
                print(f"Validation error: {e}")

            # Wait for next cycle
            time.sleep(self.interval)

    def _check_for_improvements(self, run: ValidationRun):
        """Check if autonomous improvement should be triggered."""

        trends = self.history.get_trends(hours=24)

        # Trigger improvement if:
        # 1. Success rate drops below 90%
        # 2. Degradation detected
        # 3. Recurring failures found

        triggers = []

        if run.success_rate < 90:
            triggers.append({"type": "low_success_rate", "value": run.success_rate, "threshold": 90})

        if trends.get("is_degrading"):
            triggers.append(
                {
                    "type": "degradation",
                    "current": trends["latest_success_rate"],
                    "average": trends["average_success_rate"],
                }
            )

        if trends.get("recurring_failures"):
            triggers.append({"type": "recurring_failures", "patterns": trends["recurring_failures"]})

        # Notify callbacks
        for trigger in triggers:
            for callback in self.improvement_callbacks:
                callback(trigger, run, trends)

    def start(self):
        """Start continuous validation."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._validation_loop, daemon=True)
        self.thread.start()
        print(f"Continuous validation started (interval: {self.interval}s)")

    def stop(self):
        """Stop continuous validation."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Continuous validation stopped")

    def get_status(self) -> dict[str, Any]:
        """Get current validation status."""
        trends = self.history.get_trends(hours=24)
        return {"running": self.running, "interval_seconds": self.interval, "trends": trends}


class ImprovementAgent:
    """Autonomous improvement agent that responds to validation failures."""

    def __init__(self, source_dir: str | None = None):
        self.source_dir = Path(source_dir) if source_dir else Path.cwd()
        self.improvements_made = []

    def handle_trigger(self, trigger: dict, run: ValidationRun, trends: dict):
        """Handle improvement trigger from continuous validation."""

        print("\n🤖 Improvement Agent Activated")
        print(f"   Trigger: {trigger['type']}")

        if trigger["type"] == "recurring_failures":
            self._fix_recurring_failures(trigger["patterns"])
        elif trigger["type"] == "low_success_rate":
            self._analyze_failures(run.failures)
        elif trigger["type"] == "degradation":
            self._investigate_degradation(trends)

    def _fix_recurring_failures(self, patterns):
        """Attempt to fix recurring failure patterns."""
        print(f"   Analyzing {len(patterns)} recurring failure patterns...")

        for pattern, count in patterns[:3]:  # Top 3 patterns
            print(f"   • {pattern[:50]}... (occurred {count} times)")

            # Here an AI agent would:
            # 1. Analyze the failure pattern
            # 2. Generate a fix
            # 3. Test the fix with contracts
            # 4. Commit if successful

            self.improvements_made.append(
                {
                    "timestamp": time.time(),
                    "pattern": pattern,
                    "action": "would_fix",  # Placeholder
                }
            )

    def _analyze_failures(self, failures):
        """Analyze and potentially fix failures."""
        print(f"   Analyzing {len(failures)} failures...")

        # Group failures by contract
        by_contract = {}
        for failure in failures:
            contract = failure["contract"]
            if contract not in by_contract:
                by_contract[contract] = []
            by_contract[contract].extend(failure["reasons"])

        for contract, reasons in by_contract.items():
            print(f"   • {contract}: {len(reasons)} reason(s)")

    def _investigate_degradation(self, trends):
        """Investigate performance degradation."""
        print(
            f"   Success rate degraded from {trends['average_success_rate']:.1f}% "
            f"to {trends['latest_success_rate']:.1f}%"
        )

        # Here an AI agent would:
        # 1. Check recent code changes
        # 2. Identify potential causes
        # 3. Run targeted tests
        # 4. Propose fixes


def demo_continuous_validation():
    """Demonstrate continuous validation with simulated time."""

    print("=" * 70)
    print("CONTINUOUS VALIDATION DEMONSTRATION")
    print("=" * 70)

    # Create validator with short interval for demo
    validator = ContinuousValidator(interval_seconds=2)  # 2 seconds for demo

    # Add improvement agent
    agent = ImprovementAgent()
    validator.add_improvement_callback(agent.handle_trigger)

    # Start validation
    validator.start()

    print("\nRunning continuous validation for 10 seconds...")
    print("(In production, this would run indefinitely)\n")

    # Let it run for demo
    time.sleep(10)

    # Stop and show status
    validator.stop()

    status = validator.get_status()
    print("\n" + "=" * 70)
    print("VALIDATION STATUS")
    print("=" * 70)

    if "trends" in status and not status["trends"].get("no_data"):
        trends = status["trends"]
        print(f"Total runs: {trends['total_runs']}")
        print(f"Average success rate: {trends['average_success_rate']:.1f}%")
        print(f"Latest success rate: {trends['latest_success_rate']:.1f}%")
        print(f"Degrading: {trends['is_degrading']}")

        if trends["recurring_failures"]:
            print("\nRecurring failures:")
            for pattern, count in trends["recurring_failures"]:
                print(f"  • {pattern[:60]}... ({count} times)")
    else:
        print("No validation data collected yet")

    print("\nThis demonstrates how the BEAST framework can:")
    print("  1. Continuously monitor system behavior")
    print("  2. Detect degradations and patterns")
    print("  3. Trigger autonomous improvements")
    print("  4. Enable recursive self-improvement without human intervention")


if __name__ == "__main__":
    demo_continuous_validation()
