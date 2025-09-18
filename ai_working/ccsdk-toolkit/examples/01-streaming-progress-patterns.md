# Example Improvement: Streaming Progress Patterns

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 2+ specification - examples to be implemented
> **Context**: Example patterns derived from module_generator battle-tested approaches


## Target: `amplifier/ccsdk_toolkit/tools/`

## Priority: 🔴 Critical (P1)

## Problem Statement

Current example tools don't demonstrate streaming output or progress visibility, leaving users unaware of ongoing operations.

## Current Implementation

```python
# idea_synthesis/utils/claude_helper.py
async with ClaudeSession(options) as session:
    response = await session.query(prompt)  # Silent operation
    # User waits with no feedback
```

## Proposed Implementation

### Update idea_synthesis Tool

```python
# idea_synthesis/cli.py
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live

async def process_with_streaming(prompt: str, console: Console):
    """Process with real-time streaming output."""
    options = SessionOptions(
        system_prompt="Synthesize ideas...",
        max_turns=5,
        stream_output=True,  # Enable streaming
        timeout_seconds=None  # No timeout for synthesis
    )

    with console.status("[bold green]Processing...") as status:
        async with ClaudeSession(options) as session:
            response = await session.query(prompt)
            return response

# Alternative: Custom progress display
async def process_with_rich_progress(files: list[Path]):
    """Process files with rich progress display."""
    console = Console()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing files...", total=len(files))

        for file in files:
            # Create session with custom progress callback
            def update_progress(text: str):
                # Update the progress description with recent output
                if len(text) > 50:
                    progress.update(task, description=f"Processing: ...{text[-50:]}")

            options = SessionOptions(
                progress_callback=update_progress,
                stream_output=False  # Use callback instead
            )

            async with ClaudeSession(options) as session:
                response = await session.query(f"Analyze {file}")
                progress.advance(task)
```

### Update code_complexity_analyzer Tool

```python
# code_complexity_analyzer.py
import sys
from pathlib import Path

async def analyze_with_visibility(file_path: Path, verbose: bool = False):
    """Analyze file with progress visibility."""

    # Different output modes based on verbosity
    if verbose:
        # Full streaming for verbose mode
        options = SessionOptions(
            system_prompt="Analyze code complexity...",
            stream_output=True,
            max_turns=1
        )
    else:
        # Progress indicator for normal mode
        def progress_indicator(text: str):
            # Simple progress dots
            sys.stdout.write(".")
            sys.stdout.flush()

        options = SessionOptions(
            system_prompt="Analyze code complexity...",
            progress_callback=progress_indicator,
            max_turns=1
        )

    print(f"Analyzing {file_path.name}", end="")

    async with ClaudeSession(options) as session:
        response = await session.query(f"Analyze: {file_path.read_text()}")

    if not verbose:
        print(" Done!")

    return response
```

### New Pattern: Multi-Stage Progress

```python
# New example: module_planner.py
async def plan_module_with_stages(spec: str):
    """Multi-stage planning with progress per stage."""
    console = Console()
    stages = [
        ("📖 Reading specification", "Read and understand the spec"),
        ("🔍 Analyzing requirements", "Identify key requirements"),
        ("🏗️ Designing architecture", "Design module architecture"),
        ("📝 Creating implementation plan", "Create detailed plan")
    ]

    results = []

    with console.status("[bold]Planning module...") as status:
        for emoji, description in stages:
            status.update(f"{emoji} {description}")

            options = SessionOptions(
                stream_output=console.is_terminal,  # Stream if terminal
                max_turns=3
            )

            async with ClaudeSession(options) as session:
                response = await session.query(f"{description}: {spec}")
                results.append(response)

            console.print(f"✅ {description} complete")

    return results
```

### Pattern: Adaptive Streaming

```python
async def adaptive_processing(prompt: str, output_file: Path | None = None):
    """Adapt streaming based on output destination."""

    if output_file:
        # No streaming when writing to file
        print(f"Processing (output to {output_file})...")
        options = SessionOptions(stream_output=False)
    elif not sys.stdout.isatty():
        # No streaming when piped
        options = SessionOptions(stream_output=False)
    else:
        # Full streaming to terminal
        print("Processing (streaming enabled)...")
        options = SessionOptions(stream_output=True)

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

    if output_file:
        output_file.write_text(response.content)
        print(f"✅ Output saved to {output_file}")
    elif not sys.stdout.isatty():
        # Clean output for piping
        print(response.content)
    else:
        # Already streamed, just confirm
        print("\n✅ Processing complete")

    return response
```

## Implementation Guidelines

1. **Always stream for long operations** - Any operation over 5 seconds
2. **Adapt to output context** - Terminal vs file vs pipe
3. **Provide stage indicators** - Show which phase is running
4. **Use rich for complex displays** - Progress bars, spinners, etc.
5. **Fallback gracefully** - Simple dots if rich unavailable

## Testing Requirements

- Test streaming appears in real-time
- Verify non-terminal outputs work correctly
- Test progress callbacks are called
- Ensure clean output when piped

## Success Criteria

- Users see progress during all long operations
- Output adapts to context appropriately
- Examples demonstrate various patterns
- Clear documentation of when to use each pattern