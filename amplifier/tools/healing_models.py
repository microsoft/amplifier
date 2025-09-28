"""Data models for healing results."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class HealingResult:
    """Result of a healing operation."""

    module_path: Path
    health_before: float
    health_after: float
    status: str  # "success", "failed", "skipped"
    reason: str | None = None
    duration: float = 0.0

    @classmethod
    def success(cls, module_path: Path, health_before: float, health_after: float, duration: float) -> "HealingResult":
        """Create a successful result."""
        return cls(
            module_path=module_path,
            health_before=health_before,
            health_after=health_after,
            status="success",
            duration=duration,
        )

    @classmethod
    def failed(cls, module_path: Path, health_before: float, reason: str, duration: float) -> "HealingResult":
        """Create a failed result."""
        return cls(
            module_path=module_path,
            health_before=health_before,
            health_after=health_before,
            status="failed",
            reason=reason,
            duration=duration,
        )

    @classmethod
    def skipped(cls, module_path: Path, health_before: float, reason: str) -> "HealingResult":
        """Create a skipped result."""
        return cls(
            module_path=module_path,
            health_before=health_before,
            health_after=health_before,
            status="skipped",
            reason=reason,
        )

    def dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "module_path": str(self.module_path),
            "health_before": self.health_before,
            "health_after": self.health_after,
            "status": self.status,
            "reason": self.reason,
            "duration": self.duration,
        }
