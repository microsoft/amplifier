# Example Improvement: Permission Evolution Patterns

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 2+ specification - examples to be implemented
> **Context**: Example patterns derived from module_generator battle-tested approaches


## Target: New example tool `module_planner.py`

## Priority: 🟡 Important (P2)

## Problem Statement

No examples demonstrate the important safety pattern of progressive tool permissions (read-only analysis before write operations).

## Proposed Implementation

### Create New Example: module_planner.py

```python
#!/usr/bin/env python3
"""
Module Planner - Demonstrates progressive permission patterns.

This tool shows how to safely progress from read-only analysis
to write-enabled implementation.
"""

import asyncio
from pathlib import Path
import click
from rich.console import Console

from amplifier.ccsdk_toolkit import (
    ClaudeSession,
    SessionOptions,
    SessionPresets,
)

console = Console()

async def phase1_analysis(spec_file: Path) -> str:
    """Phase 1: Read-only analysis of requirements."""
    console.print("\n[bold blue]Phase 1: Analysis (Read-Only)[/bold blue]")
    console.print("Permissions: Read, Grep, Glob")

    options = SessionOptions(
        system_prompt="Analyze the specification and existing code. DO NOT modify anything.",
        allowed_tools=["Read", "Grep", "Glob"],  # Read-only tools
        permission_mode="default",
        max_turns=5,
        stream_output=True
    )

    prompt = f"""
    Analyze this specification and the existing codebase:

    {spec_file.read_text()}

    Provide:
    1. Understanding of requirements
    2. Existing code that's relevant
    3. Potential challenges
    4. Recommended approach
    """

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

    console.print(f"✅ Analysis complete (Cost: ${response.cost:.4f})")
    return response.content


async def phase2_planning(analysis: str) -> str:
    """Phase 2: Create implementation plan (still read-only)."""
    console.print("\n[bold yellow]Phase 2: Planning (Read-Only)[/bold yellow]")
    console.print("Permissions: Read, Grep")

    options = SessionOptions(
        system_prompt="Create a detailed implementation plan. DO NOT modify any files.",
        allowed_tools=["Read", "Grep"],  # Still read-only
        permission_mode="default",
        max_turns=3,
        stream_output=True
    )

    prompt = f"""
    Based on this analysis, create a detailed implementation plan:

    {analysis}

    Include:
    1. Files to create/modify
    2. Step-by-step implementation order
    3. Test cases to add
    4. Potential risks
    """

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

    console.print(f"✅ Planning complete (Cost: ${response.cost:.4f})")
    return response.content


async def phase3_implementation(plan: str, dry_run: bool = False) -> str:
    """Phase 3: Implementation with write permissions."""
    if dry_run:
        console.print("\n[bold yellow]Phase 3: Implementation (DRY RUN)[/bold yellow]")
        console.print("Permissions: Read only (dry run mode)")

        options = SessionOptions(
            system_prompt="Describe what changes you would make (dry run - no actual changes).",
            allowed_tools=["Read", "Grep"],
            permission_mode="default",
            max_turns=10,
            stream_output=True
        )
    else:
        console.print("\n[bold green]Phase 3: Implementation (Write-Enabled)[/bold green]")
        console.print("Permissions: Read, Write, Edit, MultiEdit")
        console.print("[yellow]⚠️  File modifications will be auto-approved![/yellow]")

        options = SessionOptions(
            system_prompt="Implement the plan. Create and modify files as needed.",
            allowed_tools=["Read", "Write", "Edit", "MultiEdit"],
            permission_mode="acceptEdits",  # Auto-approve edits
            max_turns=40,  # Enough for complex implementation
            stream_output=True,
            timeout_seconds=None  # No timeout for implementation
        )

    prompt = f"""
    Implement this plan:

    {plan}

    Follow the plan exactly. Create all necessary files and tests.
    """

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

    console.print(f"✅ Implementation complete (Cost: ${response.cost:.4f})")
    return response.content


async def phase4_verification(implementation: str) -> str:
    """Phase 4: Verify implementation (read-only + test execution)."""
    console.print("\n[bold cyan]Phase 4: Verification[/bold cyan]")
    console.print("Permissions: Read, Bash (test execution only)")

    options = SessionOptions(
        system_prompt="Verify the implementation by reading files and running tests.",
        allowed_tools=["Read", "Grep", "Bash"],
        permission_mode="confirm",  # Require confirmation for commands
        max_turns=5,
        stream_output=True
    )

    prompt = f"""
    Verify this implementation:

    {implementation}

    1. Read the created/modified files
    2. Run any tests (if safe)
    3. Check for issues
    4. Provide verification report
    """

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

    console.print(f"✅ Verification complete (Cost: ${response.cost:.4f})")
    return response.content


@click.command()
@click.argument("spec_file", type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Plan only, don't implement")
@click.option("--skip-analysis", is_flag=True, help="Skip analysis phase")
@click.option("--skip-verification", is_flag=True, help="Skip verification phase")
def main(spec_file: Path, dry_run: bool, skip_analysis: bool, skip_verification: bool):
    """
    Plan and implement a module with progressive permissions.

    This demonstrates the safety pattern of:
    1. Read-only analysis
    2. Read-only planning
    3. Write-enabled implementation
    4. Read-only verification
    """
    asyncio.run(run_planner(spec_file, dry_run, skip_analysis, skip_verification))


async def run_planner(
    spec_file: Path,
    dry_run: bool,
    skip_analysis: bool,
    skip_verification: bool
):
    """Run the planning process."""
    total_cost = 0.0

    try:
        # Phase 1: Analysis
        if not skip_analysis:
            analysis = await phase1_analysis(spec_file)
            total_cost += analysis.cost
        else:
            analysis = "Skipped analysis phase"

        # Phase 2: Planning
        plan = await phase2_planning(analysis)
        total_cost += plan.cost

        # Review point
        console.print("\n" + "="*50)
        console.print("[bold]Plan Ready for Review[/bold]")
        console.print("="*50)
        console.print("\nThe plan has been created with read-only access.")

        if not dry_run:
            console.print("\n[yellow]⚠️  Next phase will modify files![/yellow]")
            if not click.confirm("Proceed with implementation?"):
                console.print("[red]Implementation cancelled[/red]")
                return

        # Phase 3: Implementation
        implementation = await phase3_implementation(plan, dry_run)
        total_cost += implementation.cost

        # Phase 4: Verification
        if not skip_verification and not dry_run:
            verification = await phase4_verification(implementation)
            total_cost += verification.cost

        # Summary
        console.print("\n" + "="*50)
        console.print("[bold green]Module Planning Complete[/bold green]")
        console.print("="*50)
        console.print(f"Total cost: ${total_cost:.4f}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
```

### Integration Pattern for Existing Tools

```python
# idea_synthesis/stages/synthesizer.py
async def synthesize_with_progressive_access(summaries: list[str]):
    """Synthesize with progressive permission access."""

    # Stage 1: Read summaries only
    read_options = SessionOptions(
        allowed_tools=["Read"],  # Minimal permissions
        max_turns=2
    )

    async with ClaudeSession(read_options) as session:
        initial_themes = await session.query("Identify themes in these summaries...")

    # Stage 2: Search for patterns
    search_options = SessionOptions(
        allowed_tools=["Read", "Grep", "Glob"],  # Add search
        max_turns=5
    )

    async with ClaudeSession(search_options) as session:
        patterns = await session.query(f"Find patterns related to {initial_themes}...")

    # Stage 3: Write synthesis (if needed)
    if needs_output_files:
        write_options = SessionOptions(
            allowed_tools=["Read", "Write"],  # Add write
            permission_mode="confirm",  # Require confirmation
            max_turns=3
        )

        async with ClaudeSession(write_options) as session:
            await session.query("Write synthesis to files...")
```

## Safety Patterns to Demonstrate

### Pattern 1: Exploration Before Modification
```python
# Always explore read-only first
explore_options = SessionOptions(allowed_tools=["Read", "Grep"])
modify_options = SessionOptions(allowed_tools=["Write", "Edit"])
```

### Pattern 2: Confirmation Gates
```python
# Require confirmation at permission escalation points
if write_needed:
    if not confirm("This will modify files. Continue?"):
        return
```

### Pattern 3: Dry Run Mode
```python
# Offer dry-run for all write operations
if dry_run:
    options.allowed_tools = ["Read", "Grep"]  # Override to read-only
    options.system_prompt += " (DRY RUN - describe changes only)"
```

## Implementation Guidelines

1. **Start with minimal permissions** - Only what's needed
2. **Escalate gradually** - Add permissions as required
3. **Gate dangerous operations** - Require confirmation
4. **Provide dry-run mode** - Test without changes
5. **Document permission usage** - Show what tools are active

## Success Criteria

- Clear demonstration of progressive permissions
- Safety gates at appropriate points
- Dry-run mode for testing
- Educational value for users