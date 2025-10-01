"""Failure tracking and analysis"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .tracer import ExecutionTrace


@dataclass
class FailurePattern:
    """Pattern detected in failures"""

    pattern_id: str
    count: int
    description: str
    examples: list[dict]


class FailureDatabase:
    """Stores and analyzes failures"""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path("failures.db")
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY,
                command TEXT,
                exit_code INTEGER,
                stdout TEXT,
                stderr TEXT,
                expected_state TEXT,
                actual_state TEXT,
                trace_fingerprint TEXT,
                timestamp REAL
            )
        """)
        self.conn.commit()

    def record_failure(self, trace: ExecutionTrace, expected: dict, actual: dict):
        """Record a failure"""
        self.conn.execute(
            """
            INSERT INTO failures (
                command, exit_code, stdout, stderr,
                expected_state, actual_state,
                trace_fingerprint, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                trace.command,
                trace.exit_code,
                trace.stdout,
                trace.stderr,
                json.dumps(expected),
                json.dumps(actual),
                trace.fingerprint(),
                trace.timestamp,
            ),
        )
        self.conn.commit()

    def get_patterns(self) -> list[FailurePattern]:
        """Find patterns in failures"""
        cursor = self.conn.execute("""
            SELECT trace_fingerprint, COUNT(*) as count
            FROM failures
            GROUP BY trace_fingerprint
            HAVING count > 1
            ORDER BY count DESC
        """)

        patterns = []
        for fingerprint, count in cursor:
            patterns.append(
                FailurePattern(pattern_id=fingerprint, count=count, description="Repeated failure pattern", examples=[])
            )

        return patterns
