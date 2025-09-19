"""Telemetry utilities for metrics collection and storage.

Provides simple telemetry recording for tracking operations,
performance metrics, and resource usage.
"""

import time
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from amplifier.utils.atomic_write import atomic_write_json


@dataclass
class TelemetryMetrics:
    """Container for telemetry metrics."""

    run_id: str = field(default_factory=lambda: str(uuid4()))
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_s: float | None = None
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    retries: int = 0
    max_latency_s: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    sdk_session_id: str | None = None
    cost_usd: float | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    custom_metrics: dict[str, Any] = field(default_factory=dict)


class TelemetryRecorder:
    """Records and persists telemetry metrics."""

    def __init__(self, output_dir: Path | str = "logs"):
        """Initialize telemetry recorder.

        Args:
            output_dir: Base directory for telemetry logs
        """
        self.output_dir = Path(output_dir)
        self.metrics = TelemetryMetrics()
        self._operation_starts: dict[str, float] = {}

    def start_operation(self, operation_id: str) -> None:
        """Mark the start of an operation."""

        self._operation_starts[operation_id] = time.time()

    # Backwards compatibility aliases -------------------------------------------------
    def start_timer(self, timer_id: str) -> None:
        """Alias for legacy API used by generated code."""

        self.start_operation(timer_id)

    def end_operation(self, operation_id: str) -> float:
        """Mark the end of an operation and return duration."""

        if operation_id not in self._operation_starts:
            return 0.0

        start = self._operation_starts.pop(operation_id)
        duration = time.time() - start
        self.metrics.max_latency_s = max(self.metrics.max_latency_s, duration)
        return duration

    def end_timer(self, timer_id: str) -> float:
        """Alias for legacy API used by generated code."""

        return self.end_operation(timer_id)

    def record_item_processed(self, success: bool = True) -> None:
        """Record a processed item.

        Args:
            success: Whether processing was successful
        """
        self.metrics.total_items += 1
        if success:
            self.metrics.processed_items += 1
        else:
            self.metrics.failed_items += 1

    def record_retry(self) -> None:
        """Record a retry attempt."""
        self.metrics.retries += 1

    def record_tokens(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Record token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.metrics.tokens_input += input_tokens
        self.metrics.tokens_output += output_tokens

    def record_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Record an error with context.

        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {},
        }
        self.metrics.errors.append(error_record)

    def record(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Record a custom event entry.

        Args:
            event: Event name
            payload: Optional payload
        """

        self.metrics.events.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "payload": payload or {},
            }
        )

    def set_custom_metric(self, key: str, value: Any) -> None:
        """Set a custom metric value.

        Args:
            key: Metric key
            value: Metric value
        """
        self.metrics.custom_metrics[key] = value

    def finalize(self) -> TelemetryMetrics:
        """Finalize metrics and compute derived values.

        Returns:
            Finalized metrics
        """
        self.metrics.end_time = time.time()
        if self.metrics.start_time:
            self.metrics.duration_s = self.metrics.end_time - self.metrics.start_time
        return self.metrics

    def get_metrics(self) -> dict[str, Any]:
        """Return a dictionary snapshot of current metrics."""

        return asdict(self.metrics)

    def save(self, module_name: str) -> Path:
        """Save metrics to file.

        Args:
            module_name: Name of the module generating metrics

        Returns:
            Path to saved metrics file
        """
        self.finalize()

        # Create output directory
        module_dir = self.output_dir / module_name
        module_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{self.metrics.run_id[:8]}.metrics.json"
        filepath = module_dir / filename

        # Convert metrics to dict and save
        metrics_dict = asdict(self.metrics)
        metrics_dict["timestamp"] = datetime.now().isoformat()
        atomic_write_json(filepath, metrics_dict, indent=2)

        return filepath
