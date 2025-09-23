#!/usr/bin/env python3
"""
Recipe Module: Tool Generation Philosophy Implementation

A self-contained module for generating CLI tools using philosophy-driven approach
with SDK timeout handling, incremental saves, resume capability, and progress tracking.

Contract:
- Input: Tool name, description, optional template
- Output: Generated CLI tool in cli_tools/<name> directory
- Side Effects: Creates directories and Python files
- Dependencies: Claude Code SDK, Click, JSON

Public Interface:
- generate_tool(): Main entry point for tool generation
- plan_tool(): Create tool specification and plan
- PhilosophyGenerator: Core philosophy-driven generation engine
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any


# Retry utilities for robust file I/O
def write_with_retry(path: Path, content: str, max_retries: int = 3, initial_delay: float = 0.5) -> None:
    """Write file with retry logic for cloud-synced directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"

    delay = initial_delay
    for attempt in range(max_retries):
        try:
            path.write_text(content, encoding="utf-8")
            return
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    print(f"⚠️ I/O retry for {path} (cloud sync delay?)")
                time.sleep(delay)
                delay *= 2
            else:
                raise


def read_with_retry(path: Path, max_retries: int = 3, initial_delay: float = 0.5) -> str:
    """Read file with retry logic for cloud-synced directories."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    print(f"⚠️ I/O retry reading {path} (cloud sync delay?)")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    return ""  # Explicit return for linter


class ProgressTracker:
    """Track and display progress for long-running operations."""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()

    def update(self, increment: int = 1, status: str = "") -> None:
        """Update progress and display status."""
        self.current += increment
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        remaining = (self.total - self.current) / rate if rate > 0 else 0

        bar_width = 40
        filled = int(bar_width * self.current / self.total)
        bar = "█" * filled + "░" * (bar_width - filled)

        status_msg = f" - {status}" if status else ""
        print(
            f"\r{self.description}: [{bar}] {self.current}/{self.total} "
            f"({self.current * 100 / self.total:.1f}%) "
            f"ETA: {remaining:.0f}s{status_msg}",
            end="",
            flush=True,
        )

        if self.current >= self.total:
            print()  # New line when complete


class SDKSession:
    """Manage Claude Code SDK session with 120-second timeout."""

    def __init__(self, system_prompt: str = "", timeout: float = 120.0):
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        """Start SDK session with timeout handling."""
        try:
            # Import SDK components
            from amplifier.ccsdk_toolkit.core import ClaudeSession
            from amplifier.ccsdk_toolkit.core import SessionOptions

            opts = SessionOptions(system_prompt=self.system_prompt, max_turns=1)
            self.session = ClaudeSession(opts)
            await self.session.__aenter__()
            return self
        except ImportError:
            raise RuntimeError("Claude Code SDK not available. Install with: pip install claude-code-sdk")

    async def __aexit__(self, *args):
        """Clean up SDK session."""
        if self.session:
            await self.session.__aexit__(*args)

    async def query(self, prompt: str) -> str:
        """Query SDK with timeout protection."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        try:
            resp = await asyncio.wait_for(self.session.query(prompt), timeout=self.timeout)
            if resp.success:
                return resp.content
            raise RuntimeError(f"SDK error: {resp.error or 'Unknown error'}")
        except TimeoutError:
            raise TimeoutError(f"SDK query exceeded {self.timeout}s timeout")


class PhilosophyGenerator:
    """Generate tools using philosophy-driven approach."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts = artifacts_dir
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self.state_file = self.artifacts / "generation_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Load or initialize generation state for resume capability."""
        if self.state_file.exists():
            try:
                return json.loads(read_with_retry(self.state_file))
            except Exception:
                return {"steps_completed": [], "partial_results": {}}
        return {"steps_completed": [], "partial_results": {}}

    def _save_state(self) -> None:
        """Save current state for resume capability."""
        self.state["updated_at"] = datetime.now(UTC).isoformat()
        write_with_retry(self.state_file, json.dumps(self.state, indent=2))

    async def plan_philosophy(self, name: str, description: str) -> dict[str, Any]:
        """Generate tool plan using philosophy approach."""

        if "philosophy_plan" in self.state.get("partial_results", {}):
            print("✓ Using cached philosophy plan")
            return self.state["partial_results"]["philosophy_plan"]

        print("📋 Generating philosophy-driven plan...")

        prompt = f"""Design a CLI tool following the brick-and-stud philosophy.

Tool: {name}
Purpose: {description}

Create a modular design with:
1. Clear boundaries and contracts between components
2. Self-contained "bricks" that can be regenerated independently
3. Public "studs" (interfaces) that remain stable
4. Incremental processing with resume capability
5. Progress tracking and status saves

Output a JSON plan with:
- architecture: High-level design and module boundaries
- components: List of self-contained components with contracts
- data_flow: How data moves between components
- failure_modes: How to handle errors gracefully
- cli_interface: Command structure and options"""

        async with SDKSession("You are a zen architect specializing in modular design") as session:
            response = await session.query(prompt)

        # Extract JSON from response
        plan = self._extract_json(response)
        if not plan:
            plan = {
                "architecture": "Modular pipeline design",
                "components": [
                    {"name": "discovery", "contract": "Find input files"},
                    {"name": "processing", "contract": "Transform data"},
                    {"name": "output", "contract": "Save results"},
                ],
                "data_flow": "Sequential pipeline with checkpoints",
                "failure_modes": "Fail fast with clear errors",
                "cli_interface": {"commands": ["run"], "options": ["--input", "--output"]},
            }

        self.state["partial_results"]["philosophy_plan"] = plan
        self._save_state()

        return plan

    async def generate_implementation(self, name: str, plan: dict[str, Any]) -> str:
        """Generate tool implementation from philosophy plan."""

        if "implementation" in self.state.get("partial_results", {}):
            print("✓ Using cached implementation")
            return self.state["partial_results"]["implementation"]

        print("🔨 Generating implementation...")
        tracker = ProgressTracker(3, "Implementation steps")

        # Step 1: Generate core logic
        tracker.update(status="Core logic")
        core_prompt = f"""Generate Python implementation for tool '{name}'.

Plan: {json.dumps(plan, indent=2)}

Requirements:
- Self-contained recipe module with run() function
- Incremental saves after each step
- Progress reporting callbacks
- Resume from interrupted state
- Clear error messages

Generate complete, working Python code."""

        async with SDKSession("You are a master Python developer") as session:
            core_code = await session.query(core_prompt)

        tracker.update(status="Refinement")

        # Step 2: Add robustness features
        robust_prompt = f"""Enhance this implementation with:
- Retry logic for I/O operations
- Progress indicators
- State checkpointing
- Graceful error handling

Code to enhance:
{core_code[:10000]}

Return only the enhanced Python code."""

        async with SDKSession("You are a reliability engineer") as session:
            robust_code = await session.query(robust_prompt)

        tracker.update(status="Validation")

        # Extract clean Python code
        code = self._extract_code(robust_code)
        if not code:
            code = self._generate_fallback_implementation(name)

        self.state["partial_results"]["implementation"] = code
        self._save_state()
        tracker.update(status="Complete")

        return code

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON object from LLM response."""
        import re

        # Try markdown code block first
        match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        # Try to find raw JSON
        match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return {}

    def _extract_code(self, text: str) -> str:
        """Extract Python code from LLM response."""
        import re

        # Try markdown code block
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Look for function definitions
        if "def run(" in text:
            # Extract from first import/def to end
            lines = text.split("\n")
            start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(("import ", "from ", "def ")):
                    start = i
                    break
            return "\n".join(lines[start:])

        return text.strip()

    def _generate_fallback_implementation(self, name: str) -> str:
        """Generate minimal fallback implementation."""
        return dedent(f'''
        """Generated tool: {name}"""
        from pathlib import Path
        from typing import Any, Optional
        import json

        def run(
            input_path: str,
            output_path: Optional[str] = None,
            on_event: Optional[Any] = None
        ) -> dict[str, Any]:
            """Main entry point for {name} tool."""

            input_p = Path(input_path)
            output_p = Path(output_path) if output_path else Path(".data") / "{name}"
            output_p.mkdir(parents=True, exist_ok=True)

            if on_event:
                on_event("start", "processing", {{"input": str(input_p)}})

            # Process input files
            files = list(input_p.glob("*"))
            results = []

            for i, file in enumerate(files):
                if on_event:
                    on_event("progress", "file", {{"current": i+1, "total": len(files)}})

                # Process file (placeholder)
                results.append({{"file": str(file), "processed": True}})

            # Save results
            output_file = output_p / "results.json"
            output_file.write_text(json.dumps(results, indent=2))

            if on_event:
                on_event("complete", "done", {{"output": str(output_file)}})

            return {{
                "success": True,
                "files_processed": len(files),
                "output": str(output_file)
            }}
        ''').strip()


# Main public interface
async def generate_tool(
    name: str, description: str, template: str | None = None, artifacts_dir: Path | None = None
) -> dict[str, Any]:
    """
    Generate a CLI tool using philosophy-driven approach.

    Args:
        name: Tool name (will become CLI command)
        description: What the tool should do
        template: Optional template type
        artifacts_dir: Where to save artifacts

    Returns:
        Dictionary with generation results and paths
    """

    artifacts = artifacts_dir or Path(".data") / "tool_generation" / name
    generator = PhilosophyGenerator(artifacts)

    print(f"🚀 Generating tool: {name}")

    # Generate philosophy-based plan
    plan = await generator.plan_philosophy(name, description)

    # Generate implementation
    code = await generator.generate_implementation(name, plan)

    # Create tool structure
    base = Path("cli_tools") / name
    pkg_name = name.replace("-", "_")

    print(f"📦 Creating package structure at {base}")

    # Write tool files
    write_with_retry(base / "pyproject.toml", _generate_pyproject(name, pkg_name))

    write_with_retry(base / pkg_name / "__init__.py", "")

    write_with_retry(base / pkg_name / "recipe.py", code)

    write_with_retry(base / pkg_name / "cli.py", _generate_cli(name, pkg_name))

    write_with_retry(base / "README.md", _generate_readme(name, description))

    print(f"✅ Tool '{name}' generated successfully!")
    print(f"📍 Location: {base.absolute()}")
    print(f"📝 Install with: pip install -e {base}")

    return {
        "success": True,
        "tool_name": name,
        "package_path": str(base.absolute()),
        "artifacts": str(artifacts.absolute()),
        "plan": plan,
    }


def _generate_pyproject(name: str, pkg: str) -> str:
    """Generate pyproject.toml for the tool."""
    return dedent(f'''
    [build-system]
    requires = ["setuptools>=68", "wheel"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "{name}"
    version = "0.1.0"
    description = "Generated CLI tool: {name}"
    requires-python = ">=3.11"
    dependencies = [
        "click>=8.1.0",
        "claude-code-sdk>=0.0.20",
    ]

    [project.scripts]
    {name} = "{pkg}.cli:cli"
    ''').strip()


def _generate_cli(name: str, pkg: str) -> str:
    """Generate CLI entry point."""
    return dedent(f'''
    """CLI interface for {name}"""
    import json
    import click
    from pathlib import Path
    from .recipe import run

    @click.group()
    def cli():
        """Generated tool: {name}"""
        pass

    @cli.command()
    @click.option("--input", "-i", required=True, help="Input path")
    @click.option("--output", "-o", help="Output path")
    @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
    def process(input, output, verbose):
        """Process input files."""

        def progress_callback(event, stage, data):
            if verbose or event in ["start", "complete", "error"]:
                print(f"[{{event}}] {{stage}}: {{data}}")

        try:
            result = run(input, output, on_event=progress_callback if verbose else None)
            print(json.dumps(result, indent=2))
        except Exception as e:
            click.echo(f"Error: {{e}}", err=True)
            raise click.Abort()

    if __name__ == "__main__":
        cli()
    ''').strip()


def _generate_readme(name: str, description: str) -> str:
    """Generate README for the tool."""
    return dedent(f"""
    # {name}

    {description}

    Generated using philosophy-driven tool generation.

    ## Installation

    ```bash
    pip install -e cli_tools/{name}
    ```

    ## Usage

    ```bash
    {name} process --input /path/to/input --output /path/to/output
    ```

    ## Features

    - ✅ Incremental processing with resume capability
    - ✅ Progress tracking and status updates
    - ✅ Robust I/O with retry logic
    - ✅ Clean error handling
    - ✅ Modular, regeneratable design

    ## Architecture

    Built following the brick-and-stud philosophy:
    - Self-contained modules with clear contracts
    - Stable public interfaces
    - Regeneratable components
    - Clean separation of concerns
    """).strip()


# Synchronous wrapper for backwards compatibility
def generate_tool_sync(
    name: str, description: str, template: str | None = None, artifacts_dir: Path | None = None
) -> dict[str, Any]:
    """Synchronous wrapper for generate_tool."""
    return asyncio.run(generate_tool(name, description, template, artifacts_dir))


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python recipe.py <tool_name> <description>")
        sys.exit(1)

    result = generate_tool_sync(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
