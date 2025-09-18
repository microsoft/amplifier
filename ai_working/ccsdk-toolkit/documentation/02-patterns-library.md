# Documentation: Pattern Library

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Philosophy and patterns documentation for future development
> **Context**: Documentation improvements derived from module_generator insights


## Target: New file `amplifier/ccsdk_toolkit/PATTERNS.md`

## Priority: 🟡 Important (P2)

## Proposed Content

```markdown
# CCSDK Toolkit Patterns

Common patterns for effective use of the Claude Code SDK Toolkit.

## Table of Contents
- [Progress Patterns](#progress-patterns)
- [Cost Management](#cost-management)
- [Permission Patterns](#permission-patterns)
- [Error Handling](#error-handling)
- [Session Management](#session-management)

## Progress Patterns

### Simple Streaming
**When to use**: Default for any operation over 5 seconds

```python
options = SessionOptions(stream_output=True)
async with ClaudeSession(options) as session:
    response = await session.query(prompt)  # Streams to stdout
```

### Rich Progress Display
**When to use**: Professional CLI tools with complex operations

```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("Processing...", total=len(items))

    for item in items:
        options = SessionOptions(
            progress_callback=lambda t: progress.console.print(t, end="")
        )
        async with ClaudeSession(options) as session:
            response = await session.query(f"Process {item}")
            progress.advance(task)
```

### Multi-Stage Progress
**When to use**: Operations with distinct phases

```python
stages = [
    ("Analysis", "Read-only exploration"),
    ("Planning", "Create implementation plan"),
    ("Implementation", "Write code")
]

for stage_name, stage_desc in stages:
    print(f"\n📍 {stage_name}: {stage_desc}")

    options = SessionOptions(
        stream_output=True,
        max_turns=10 if stage_name == "Implementation" else 3
    )

    async with ClaudeSession(options) as session:
        response = await session.query(stage_prompt)
        print(f"✅ {stage_name} complete (${response.cost:.4f})")
```

## Cost Management

### Budget Enforcement
**When to use**: Batch operations with cost limits

```python
class BudgetEnforcer:
    def __init__(self, max_budget: float):
        self.max_budget = max_budget
        self.spent = 0.0

    async def execute_with_budget(self, prompt: str) -> SessionResponse | None:
        if self.spent >= self.max_budget:
            print(f"Budget exceeded: ${self.spent:.2f} >= ${self.max_budget:.2f}")
            return None

        async with ClaudeSession() as session:
            response = await session.query(prompt)
            self.spent += response.cost

            print(f"Cost: ${response.cost:.4f} (Total: ${self.spent:.2f})")
            return response
```

### Cost Estimation
**When to use**: Before expensive operations

```python
async def estimate_cost(operation: str, sample_size: int = 1000) -> float:
    """Estimate cost by running on sample."""
    sample_prompt = f"{operation}: {'x' * sample_size}"

    options = SessionOptions(max_turns=1)
    async with ClaudeSession(options) as session:
        response = await session.query(sample_prompt)

    return response.cost

# Usage
estimated = await estimate_cost("Analyze code", 5000)
total_estimate = estimated * number_of_files
if input(f"Estimated cost: ${total_estimate:.2f}. Continue? [y/N]: ") != 'y':
    return
```

## Permission Patterns

### Read-Analyze-Write Pattern
**When to use**: Any operation that modifies files

```python
async def safe_modification(target: Path):
    # Step 1: Read and understand
    read_opts = SessionOptions(
        allowed_tools=["Read", "Grep"],
        max_turns=3
    )
    async with ClaudeSession(read_opts) as session:
        analysis = await session.query(f"Analyze {target}")

    # Step 2: Plan changes
    plan_opts = SessionOptions(
        allowed_tools=["Read"],
        max_turns=2
    )
    async with ClaudeSession(plan_opts) as session:
        plan = await session.query(f"Plan changes based on: {analysis.content}")

    # Step 3: Implement (with confirmation)
    if input("Proceed with modifications? [y/N]: ") == 'y':
        write_opts = SessionOptions(
            allowed_tools=["Read", "Write", "Edit"],
            permission_mode="acceptEdits",
            max_turns=10
        )
        async with ClaudeSession(write_opts) as session:
            result = await session.query(f"Implement: {plan.content}")
```

### Progressive Tool Access
**When to use**: Exploring unfamiliar codebases

```python
# Start minimal
tools_progression = [
    ["Read"],                           # Just read files
    ["Read", "Grep"],                   # Add searching
    ["Read", "Grep", "Glob"],          # Add file finding
    ["Read", "Grep", "Glob", "Write"]  # Finally allow writes
]

for tools in tools_progression:
    options = SessionOptions(allowed_tools=tools)
    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

    if response.success:
        break  # Stop if successful

    print(f"Need more tools, trying with: {tools}")
```

## Error Handling

### Retry with Exponential Backoff
**When to use**: Network or rate limit errors

```python
async def resilient_query(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            async with ClaudeSession() as session:
                response = await session.query(prompt)

            if response.error_details:
                if response.error_details.error_type == "RateLimitError":
                    wait_time = 2 ** attempt * 10  # 10, 20, 40 seconds
                    print(f"Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue

            return response

        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")

    raise Exception("Max retries exceeded")
```

### Graceful Degradation
**When to use**: When partial results are valuable

```python
async def best_effort_analysis(files: list[Path]):
    results = []
    failures = []

    for file in files:
        try:
            async with ClaudeSession() as session:
                response = await session.query(f"Analyze {file}")

            if response.success:
                results.append((file, response.content))
            else:
                failures.append((file, response.error))

        except Exception as e:
            failures.append((file, str(e)))
            continue  # Keep processing other files

    print(f"Succeeded: {len(results)}, Failed: {len(failures)}")
    return results, failures
```

## Session Management

### Checkpoint Long Operations
**When to use**: Operations that might be interrupted

```python
from pathlib import Path
import json

class CheckpointedOperation:
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.state = self._load_checkpoint()

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_file.exists():
            return json.loads(self.checkpoint_file.read_text())
        return {"completed": [], "session_id": None}

    def _save_checkpoint(self):
        self.checkpoint_file.write_text(json.dumps(self.state))

    async def process_items(self, items: list):
        # Skip already completed
        remaining = [i for i in items if i not in self.state["completed"]]

        # Resume or create session
        session = None
        if self.state["session_id"]:
            session = await resume_session(self.state["session_id"])

        if not session:
            session = ClaudeSession()

        async with session:
            for item in remaining:
                response = await session.query(f"Process {item}")

                self.state["completed"].append(item)
                self.state["session_id"] = response.session_id
                self._save_checkpoint()

        # Clean up on success
        self.checkpoint_file.unlink()
```

### Session History Context
**When to use**: Multi-turn conversations needing context

```python
class ContextualSession:
    def __init__(self):
        self.history = []

    async def query_with_context(self, prompt: str, include_last_n: int = 3):
        # Build context from history
        context = "\n\n".join([
            f"Previous Q: {h['q']}\nPrevious A: {h['a'][:200]}..."
            for h in self.history[-include_last_n:]
        ])

        full_prompt = f"{context}\n\nCurrent question: {prompt}" if context else prompt

        async with ClaudeSession() as session:
            response = await session.query(full_prompt)

        # Save to history
        self.history.append({"q": prompt, "a": response.content})

        return response
```

## Best Practices

1. **Start simple** - Use basic patterns first, add complexity only when needed
2. **Make progress visible** - Users should always know what's happening
3. **Track costs** - Every operation should report its cost
4. **Progressive permissions** - Start read-only, escalate carefully
5. **Handle failures gracefully** - Partial results are better than none
6. **Document patterns** - Help others learn from your solutions
```

## Success Criteria

- Comprehensive pattern coverage
- Clear when-to-use guidance
- Working code examples
- Best practices documented