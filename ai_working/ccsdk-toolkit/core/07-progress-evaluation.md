# Core Improvement: Progress Evaluation Hooks

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🟢 Valuable (P3)

## Problem Statement

For long-running sessions, we need ways to evaluate if meaningful progress is being made rather than relying on timeouts. This enables intelligent decisions about whether to continue, pivot, or stop.

## Current Implementation

```python
# No progress evaluation - just timeout or completion
```

## Proposed Solution

### Add Progress Evaluation Support

```python
# ccsdk_toolkit/core/models.py
from typing import Protocol
from dataclasses import dataclass

@dataclass
class ProgressInfo:
    """Information about session progress."""
    turns_completed: int
    total_turns: int
    tokens_generated: int
    time_elapsed_ms: int
    recent_output: str  # Last 500 chars
    cost_so_far: float

class ProgressEvaluator(Protocol):
    """Protocol for progress evaluation."""
    async def should_continue(self, info: ProgressInfo) -> tuple[bool, str]:
        """Return (should_continue, reason)."""
        ...

class SessionOptions(BaseModel):
    # Existing fields...

    progress_evaluator: ProgressEvaluator | None = Field(
        default=None,
        description="Optional progress evaluation callback"
    )
    evaluation_interval: int = Field(
        default=5,
        description="Evaluate progress every N turns"
    )
```

### Implement Progress Checking

```python
# ccsdk_toolkit/core/session.py
async def query(self, prompt: str) -> SessionResponse:
    turns_completed = 0
    start_time = time.time()
    total_tokens = 0
    recent_outputs = []

    async for message in self.client.receive_response():
        # ... handle message ...

        # Track progress
        if is_turn_complete(message):
            turns_completed += 1
            recent_outputs.append(recent_text)
            if len(recent_outputs) > 3:
                recent_outputs.pop(0)

            # Evaluate progress at intervals
            if (self.options.progress_evaluator and
                turns_completed % self.options.evaluation_interval == 0):

                info = ProgressInfo(
                    turns_completed=turns_completed,
                    total_turns=self.options.max_turns,
                    tokens_generated=total_tokens,
                    time_elapsed_ms=int((time.time() - start_time) * 1000),
                    recent_output="".join(recent_outputs[-3:])[-500:],
                    cost_so_far=current_cost
                )

                should_continue, reason = await self.options.progress_evaluator.should_continue(info)

                if not should_continue:
                    return SessionResponse(
                        content=collected_text,
                        metadata=metadata,
                        error=f"Stopped by progress evaluator: {reason}"
                    )
```

## Usage Patterns

### Pattern 1: Simple Progress Check

```python
class SimpleProgressEvaluator:
    async def should_continue(self, info: ProgressInfo) -> tuple[bool, str]:
        # Stop if generating too slowly
        if info.tokens_generated / (info.time_elapsed_ms / 1000) < 1:  # Less than 1 token/sec
            return False, "Generation too slow"

        # Stop if repeating
        if info.recent_output.count(info.recent_output[:100]) > 3:
            return False, "Detected repetition"

        # Stop if cost exceeds budget
        if info.cost_so_far > 10.0:
            return False, f"Cost exceeded $10 (${info.cost_so_far:.2f})"

        return True, "Making progress"

options = SessionOptions(
    progress_evaluator=SimpleProgressEvaluator(),
    evaluation_interval=3  # Check every 3 turns
)
```

### Pattern 2: Intelligent Progress Analysis

```python
class SmartProgressEvaluator:
    def __init__(self):
        self.last_outputs = []

    async def should_continue(self, info: ProgressInfo) -> tuple[bool, str]:
        # Use another Claude call to evaluate progress!
        evaluation_prompt = f"""
        Evaluate if this session is making meaningful progress:
        - Turns: {info.turns_completed}/{info.total_turns}
        - Time: {info.time_elapsed_ms/1000:.1f}s
        - Recent output: {info.recent_output[-200:]}

        Is meaningful progress being made? Respond with YES or NO and a brief reason.
        """

        # Quick evaluation with separate session
        eval_options = SessionOptions(max_turns=1, timeout_seconds=10)
        async with ClaudeSession(eval_options) as eval_session:
            eval_response = await eval_session.query(evaluation_prompt)

            if "NO" in eval_response.content.upper():
                return False, eval_response.content
            return True, "Progress confirmed"
```

### Pattern 3: User-Interactive Progress

```python
class InteractiveProgressEvaluator:
    async def should_continue(self, info: ProgressInfo) -> tuple[bool, str]:
        print(f"\n--- Progress Check (Turn {info.turns_completed}) ---")
        print(f"Cost so far: ${info.cost_so_far:.2f}")
        print(f"Recent output: ...{info.recent_output[-100:]}")
        response = input("Continue? [Y/n]: ")

        if response.lower() == 'n':
            return False, "User requested stop"
        return True, "User approved continuation"
```

## Implementation Considerations

- Progress evaluation should be async to allow for external calls
- Evaluation should not count against turn limits
- Failed evaluations should not lose work done so far
- Consider caching evaluation results to avoid redundant checks

## Testing Requirements

- Test evaluator is called at correct intervals
- Verify session stops when evaluator returns False
- Test that work is preserved when stopped
- Ensure evaluation doesn't interfere with main operation

## Success Criteria

- Long sessions can be monitored for productivity
- Costs can be controlled via progress checks
- Intelligent stopping prevents waste
- User maintains control over long operations

## Philosophy Note

Progress evaluation enables trust without blind faith. By periodically assessing whether work is meaningful, we can allow indefinite runtime while preventing wasteful spinning. This is smarter than arbitrary time limits.