# Example Improvement: Cost Tracking Patterns

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 2+ specification - examples to be implemented
> **Context**: Example patterns derived from module_generator battle-tested approaches


## Target: `amplifier/ccsdk_toolkit/tools/`

## Priority: 🟡 Important (P2)

## Problem Statement

Example tools don't demonstrate cost awareness, which is critical for long-running operations that could incur significant API costs.

## Current Implementation

```python
# No cost tracking or reporting in current examples
```

## Proposed Implementations

### Pattern 1: Simple Cost Reporting

```python
# code_complexity_analyzer.py
async def analyze_files_with_cost(files: list[Path]):
    """Analyze files and report costs."""
    total_cost = 0.0
    results = []

    for file in files:
        async with ClaudeSession(options) as session:
            response = await session.query(f"Analyze {file}")

            total_cost += response.cost
            results.append({
                "file": file.name,
                "complexity": response.content,
                "cost": response.cost
            })

            # Report running total
            print(f"Analyzed {file.name} (${response.cost:.4f}) - Total: ${total_cost:.4f}")

    # Final report
    print(f"\n📊 Analysis Complete:")
    print(f"Files analyzed: {len(files)}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Average per file: ${total_cost/len(files):.4f}")

    return results
```

### Pattern 2: Budget-Aware Processing

```python
# idea_synthesis/cli.py
async def synthesize_with_budget(
    files: list[Path],
    max_budget: float = 10.0,
    warn_at: float = 5.0
):
    """Process with budget constraints."""
    total_cost = 0.0
    processed = []
    skipped = []

    console = Console()

    for file in files:
        # Check budget before processing
        if total_cost >= max_budget:
            console.print(f"[red]Budget exceeded! Stopping at ${total_cost:.2f}[/red]")
            skipped.extend(files[len(processed):])
            break

        # Warn when approaching limit
        if total_cost >= warn_at and len(processed) == int(warn_at / (total_cost / len(processed))):
            console.print(f"[yellow]Warning: ${total_cost:.2f} spent (budget: ${max_budget:.2f})[/yellow]")

        options = SessionOptions(
            system_prompt="Synthesize ideas...",
            max_turns=5,
            stream_output=True
        )

        async with ClaudeSession(options) as session:
            response = await session.query(f"Process {file}")

            total_cost += response.cost
            processed.append(file)

            # Show per-item cost
            console.print(f"✅ {file.name} - ${response.cost:.4f}")

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"Processed: {len(processed)} files")
    console.print(f"Skipped: {len(skipped)} files")
    console.print(f"Total cost: ${total_cost:.4f}")
    if skipped:
        console.print(f"[yellow]Skipped files due to budget:[/yellow]")
        for f in skipped[:5]:  # Show first 5
            console.print(f"  - {f.name}")
        if len(skipped) > 5:
            console.print(f"  ... and {len(skipped)-5} more")

    return processed, skipped, total_cost
```

### Pattern 3: Cost Estimation

```python
# New example: cost_estimator.py
async def estimate_operation_cost(
    operation_type: str,
    file_count: int,
    avg_file_size: int
) -> dict[str, float]:
    """Estimate cost before running operation."""

    # Run on sample to estimate
    sample_text = "x" * avg_file_size  # Synthetic sample

    options = SessionOptions(max_turns=1)

    async with ClaudeSession(options) as session:
        response = await session.query(f"{operation_type}: {sample_text}")

    sample_cost = response.cost

    # Calculate estimates
    return {
        "per_file_estimate": sample_cost,
        "total_estimate": sample_cost * file_count,
        "confidence": "high" if avg_file_size < 5000 else "medium",
        "note": "Actual costs may vary based on complexity"
    }

# Usage
async def main():
    files = list(Path("src").glob("*.py"))
    avg_size = sum(f.stat().st_size for f in files) // len(files)

    estimate = await estimate_operation_cost(
        "Analyze complexity",
        len(files),
        avg_size
    )

    print(f"Estimated cost: ${estimate['total_estimate']:.2f}")
    proceed = input("Proceed? [y/N]: ")

    if proceed.lower() == 'y':
        await analyze_files_with_cost(files)
```

### Pattern 4: Cost Logger

```python
# New utility: cost_logger.py
from datetime import datetime
from pathlib import Path
import json

class CostLogger:
    """Track costs across sessions."""

    def __init__(self, log_file: Path = Path("~/.ccsdk/costs.jsonl").expanduser()):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_costs = []

    def log_operation(self, response: SessionResponse, operation: str, context: dict = None):
        """Log cost for an operation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "cost": response.cost,
            "duration_ms": response.metadata.duration_ms,
            "session_id": response.session_id,
            "context": context or {}
        }

        self.session_costs.append(entry["cost"])

        # Append to file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_session_total(self) -> float:
        """Get total cost for current session."""
        return sum(self.session_costs)

    def get_daily_total(self) -> float:
        """Get total cost for today."""
        today = datetime.now().date()
        total = 0.0

        if self.log_file.exists():
            with open(self.log_file) as f:
                for line in f:
                    entry = json.loads(line)
                    if datetime.fromisoformat(entry["timestamp"]).date() == today:
                        total += entry["cost"]

        return total

    def generate_report(self, days: int = 7) -> dict:
        """Generate cost report for last N days."""
        from collections import defaultdict

        costs_by_day = defaultdict(float)
        costs_by_operation = defaultdict(float)

        if self.log_file.exists():
            cutoff = datetime.now() - timedelta(days=days)

            with open(self.log_file) as f:
                for line in f:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry["timestamp"])

                    if timestamp >= cutoff:
                        day = timestamp.date().isoformat()
                        costs_by_day[day] += entry["cost"]
                        costs_by_operation[entry["operation"]] += entry["cost"]

        return {
            "total": sum(costs_by_day.values()),
            "by_day": dict(costs_by_day),
            "by_operation": dict(costs_by_operation),
            "daily_average": sum(costs_by_day.values()) / max(len(costs_by_day), 1)
        }

# Usage in tools
cost_logger = CostLogger()

async def tracked_operation():
    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

        cost_logger.log_operation(
            response,
            "code_analysis",
            {"file": "main.py", "lines": 500}
        )

        print(f"Session cost: ${cost_logger.get_session_total():.2f}")
        print(f"Today's total: ${cost_logger.get_daily_total():.2f}")
```

## Implementation Guidelines

1. **Always report costs** for operations over $0.01
2. **Implement budget limits** for batch operations
3. **Provide estimates** before expensive operations
4. **Log costs** for tracking and analysis
5. **Show running totals** during long operations

## Testing Requirements

- Verify cost accumulation is accurate
- Test budget limits stop processing
- Ensure cost logging works correctly
- Test report generation

## Success Criteria

- Users aware of costs during operations
- Budget controls prevent surprises
- Cost history available for analysis
- Clear patterns for cost management