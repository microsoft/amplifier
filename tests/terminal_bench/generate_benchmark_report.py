"""
For each task that failed in a terminal-bench evaluation run this script generates a report of all the failed tasks and why they failed.
It then creates an overall summary report about all the failures and their causes.
"""

import argparse
import asyncio
import json
import shutil
from pathlib import Path

from claude_code_sdk import ClaudeCodeOptions
from claude_code_sdk import ClaudeSDKClient
from pydantic import BaseModel

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    __package__ = "tests.terminal_bench"

from .generate_eval_dashboard import DEFAULT_DASHBOARD_TITLE
from .generate_eval_dashboard import generate_dashboard


class TaskResult(BaseModel):
    task_id: str
    instruction: str
    is_resolved: bool = False
    task_folder: Path
    agent_log: str | None = None
    test_log: str | None = None
    dockerfile: str | None = None
    test_files: str | None = None


def load_result_json(run_dir: Path) -> list[TaskResult]:
    results_path = run_dir / "results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    with results_path.open() as f:
        data = json.load(f)

    task_results = []
    for result in data["results"]:
        task_folder = run_dir / result["task_id"]
        sessions_folder = next(task_folder.glob("*/sessions"), None)

        agent_log_content = None
        test_log_content = None
        if sessions_folder:
            agent_log_path = sessions_folder / "agent.log"
            test_log_path = sessions_folder / "tests.log"
            if agent_log_path.exists():
                agent_log_content = agent_log_path.read_text()
                agent_log_content = parse_agent_log(agent_log_content)
            if test_log_path.exists():
                test_log_content = test_log_path.read_text()
                test_log_content = parse_test_log(test_log_content)

        task_result = TaskResult(
            task_id=result["task_id"],
            instruction=result["instruction"],
            is_resolved=result["is_resolved"] if result["is_resolved"] is not None else False,
            task_folder=task_folder,
            agent_log=agent_log_content,
            test_log=test_log_content,
        )
        task_result = load_dockerfile(task_result)
        task_result = load_test_files(task_result)
        task_results.append(task_result)

    return task_results


def parse_agent_log(agent_log: str) -> str:
    """Parse agent log and extract transcript lines (JSON format)."""
    lines = agent_log.splitlines()
    transcript_lines = []
    transcript_started = False
    for line in lines:
        if not transcript_started and line.startswith('{"type":"system","subtype":"init"'):
            transcript_started = True
        if transcript_started:
            transcript_lines.append(line)
    return "\n".join(transcript_lines)


def parse_test_log(test_log: str) -> str:
    """Parse test log and extract content from test session start onwards."""
    lines = test_log.splitlines()
    test_content_lines = []
    test_started = False
    for line in lines:
        # Remove ANSI color codes for cleaner matching
        clean_line = line.replace("[0m", "").replace("[1m", "").replace("[31m", "").replace("[32m", "")

        if not test_started and "test session starts" in clean_line:
            test_started = True

        if test_started:
            test_content_lines.append(line)
    return "\n".join(test_content_lines)


def load_dockerfile(task_result: TaskResult) -> TaskResult:
    """
    Returns the TaskResult with the dockerfile content associated with the task loaded if it exists.
    """
    cache_path = Path.home() / ".cache/terminal-bench/terminal-bench-core/0.1.1" / task_result.task_id

    if not cache_path.exists():
        return task_result

    # Check for Dockerfile in client/ subdirectory first, then at root
    client_dockerfile = cache_path / "client" / "Dockerfile"
    root_dockerfile = cache_path / "Dockerfile"

    dockerfile_path = client_dockerfile if client_dockerfile.exists() else root_dockerfile
    if dockerfile_path.exists():
        task_result.dockerfile = dockerfile_path.read_text()
    return task_result


def load_test_files(task_result: TaskResult) -> TaskResult:
    """
    Returns the TaskResult with the test files content associated with the task loaded if they exist.
    """
    cache_path = Path.home() / ".cache/terminal-bench/terminal-bench-core/0.1.1" / task_result.task_id
    tests_dir = cache_path / "tests"
    if not tests_dir.exists():
        return task_result

    # Find all test_*.py files
    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        return task_result

    # Concatenate all test file contents with separators
    test_contents = []
    for test_file in sorted(test_files):
        test_contents.append(f"# {test_file.name}\n")
        test_contents.append(test_file.read_text())
        test_contents.append("\n\n")

    task_result.test_files = "".join(test_contents)
    return task_result


async def generate_task_report(task_result: TaskResult, run_dir: Path) -> None:
    """
    Generates a detailed report for a single task using Claude Code SDK.
    Creates a temporary workspace with task context and uses Claude to analyze the failure.
    """

    temp_dir = Path(f"/tmp/terminal_bench_report_{task_result.task_id}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Write all context files
        context_files = {
            "agent_transcript.jsonl": task_result.agent_log,
            "test_output.txt": task_result.test_log,
            "dockerfile.txt": task_result.dockerfile,
            "test_files.py": task_result.test_files,
        }

        for filename, content in context_files.items():
            if content:
                (temp_dir / filename).write_text(content)

        # Create context summary for user prompt
        context_md = f"""# Task: {task_result.task_id}

## Task Instruction
{task_result.instruction}

## Files Overview
- agent_transcript.jsonl: {len(task_result.agent_log or "")} characters
- test_output.txt: {len(task_result.test_log or "")} characters
- dockerfile.txt: {len(task_result.dockerfile or "")} characters
- test_files.py: {len(task_result.test_files or "")} characters"""

        # Define system prompt
        system_prompt = """You are an expert at analyzing terminal-bench task failures. Your goal is to identify WHY the agent failed the task.

ABOUT TERMINAL-BENCH:
Terminal-Bench is an AI agent benchmarking system that evaluates autonomous agents on real-world tasks within sandboxed terminal environments. \
Each task includes a natural language instruction, test scripts for verification, and runs in isolated Docker containers. \
Tasks range from programming and system administration to interactive problem-solving.

IMPORTANT: The files provided are VERY LONG. You MUST:
1. Read files incrementally (use offset/limit with Read tool)
2. Focus on failure points in test_output.txt
3. Trace back through agent_transcript.jsonl to find what the agent did wrong
4. Cross-reference with dockerfile.txt and test_files.py to understand expected behavior

ANALYSIS APPROACH:
- Start with test_output.txt to identify which tests failed
- Find failure messages and stack traces
- Review agent_transcript.jsonl to see what actions the agent took
- Compare agent's approach with Dockerfile setup and test expectations
- Identify the root cause: wrong approach, missing steps, incorrect assumptions, bugs in the agent, etc."""

        # Define user prompt
        user_prompt = f"""Analyze this failed terminal-bench task.

Your mission: Determine WHY the agent failed.

FILES AVAILABLE:
- agent_transcript.jsonl: Full conversation between user and agent (VERY LONG - read incrementally!)
- test_output.txt: Test session output showing which tests passed/failed
- dockerfile.txt: Original task Dockerfile showing environment setup
- test_files.py: Pytest files defining task requirements

START HERE:
1. Scan test_output.txt for failure summary (read last 200 lines first)
2. Identify which tests failed and why
3. Search agent_transcript.jsonl for relevant actions (use Grep tool)
4. Build timeline of what agent did vs. what was needed

OUTPUT: Create a detailed report in `FAILURE_REPORT.md` with:
- Executive Summary (2-3 sentences)
- Test Failures (which tests failed, error messages)
- Agent Actions Timeline (key steps agent took)
- Root Cause Analysis (why it failed)
- What Should Have Been Done

Make sure that your report is factual and accurate. Do not make assumptions that are not supported by the logs and files provided.
---

{context_md}"""

        claude_options = ClaudeCodeOptions(
            system_prompt=system_prompt,
            cwd=str(temp_dir),
            allowed_tools=["Read", "Grep", "Write"],
            max_turns=30,
            permission_mode="default",
        )

        async with ClaudeSDKClient(options=claude_options) as client:
            await client.query(user_prompt)
            # Claude will create the FAILURE_REPORT.md file via Write tool
            async for _message in client.receive_response():
                continue

        # Extract the report
        report_path = temp_dir / "FAILURE_REPORT.md"
        if report_path.exists():
            # Copy to run directory
            output_path = run_dir / "task_reports" / f"{task_result.task_id}_report.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_path.read_text())
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


async def consolidated_report(run_dir: Path) -> None:
    """
    Generate a consolidated report synthesizing all individual task failure reports.
    Uses Claude Code SDK to analyze patterns and common failure modes across all tasks.
    """
    task_reports_dir = run_dir / "task_reports"
    if not task_reports_dir.exists() or not list(task_reports_dir.glob("*_report.md")):
        print("No task reports found to consolidate")
        return

    # Load all individual reports
    report_files = list(task_reports_dir.glob("*_report.md"))
    reports_content = []
    for report_file in report_files:
        task_id = report_file.stem.replace("_report", "")
        content = report_file.read_text()
        reports_content.append(f"## Report for Task: {task_id}\n\n{content}\n\n{'=' * 80}\n")
    all_reports = "\n".join(reports_content)

    # Create temporary working directory for Claude to write output
    temp_dir = Path("/tmp/terminal_bench_consolidated_report")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        system_prompt = """You are an expert at synthesizing terminal-bench failure analysis reports. \
It is critical that the report is factual and accurate based on the provided reports. \
Do not make assumptions and inferences that are not supported by the reports.

ABOUT TERMINAL-BENCH:
Terminal-Bench is an AI agent benchmarking system that evaluates autonomous agents on real-world tasks within sandboxed terminal environments.  \
Each task includes a natural language instruction, test scripts for verification, and runs in isolated Docker containers. \
Tasks range from programming and system administration to interactive problem-solving.

ABOUT THESE REPORTS:
Each individual report was generated by analyzing:
- The task instruction (what the agent was asked to do)
- Agent transcript (full conversation showing all agent actions and tool uses)
- Test output (which tests passed/failed and why)
- Original Dockerfile (environment setup)
- Test files (pytest requirements)

YOUR GOAL:
Identify patterns, common failure modes, and systemic issues across multiple task failures.
Then write a consolidated report summarizing key findings and synthesis about where the agent struggled.

ANALYSIS APPROACH:
- Look for recurring failure patterns (e.g., similar root causes across tasks)
- Identify agent weaknesses (e.g., poor error handling, missing validation, incorrect assumptions)
- Group failures by type (e.g., environment setup issues, logic errors, test misunderstanding)

OUTPUT: Write your consolidated analysis to `CONSOLIDATED_REPORT.md` using the Write tool following the structure provided in the user's message."""

        user_prompt = f"""Analyze the following {len(report_files)} terminal-bench task failure reports and create a consolidated analysis.

Your mission: Identify patterns, common failure modes, and systemic issues across all failed tasks.

OUTPUT: Create a comprehensive report in `CONSOLIDATED_REPORT.md` following this structure:

Sections corresponding to failure categories
   - Group failures by type (e.g., environment issues, logic errors, test misunderstanding)
   - Create up to 5 categories. If there are tasks that don't fit, create an "Other" category.
   - Count and list tasks in each category
   - Include a common root cause analysis for each category as to what went wrong based on the individual reports

Finally, AT THE END, go back and add an executive summary (2-4 sentences) at the top of the report.
   - Overall assessment of agent performance
   - Key patterns observed (list of failure categories, what they are, and the amount of tasks in that category)

DO NOT add:
- A conclusion and appendix
- Recommendations for improvement
- An assessment of the agent's strengths
- Anything else that does not fit the structure above
---

# Individual Task Reports

{all_reports}"""

        claude_options = ClaudeCodeOptions(
            system_prompt=system_prompt,
            cwd=str(temp_dir),
            allowed_tools=["Write"],
            max_turns=10,
            permission_mode="default",
        )

        async with ClaudeSDKClient(options=claude_options) as client:
            await client.query(user_prompt)
            async for _ in client.receive_response():
                continue

        # Extract the consolidated report
        report_path = temp_dir / "CONSOLIDATED_REPORT.md"
        if report_path.exists():
            output_path = run_dir / "CONSOLIDATED_REPORT.md"
            output_path.write_text(report_path.read_text())

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


async def main(run_dir: Path, concurrency: int = 5) -> None:
    """Main entry point for generating benchmark reports."""
    results = load_result_json(run_dir)
    failed_tasks = [r for r in results if not r.is_resolved]

    # Generate reports for each failed task in parallel
    semaphore = asyncio.Semaphore(concurrency)

    async def generate_with_semaphore(task: TaskResult, index: int) -> None:
        async with semaphore:
            print(f"[{index}/{len(failed_tasks)}] Generating report for {task.task_id}")
            await generate_task_report(task, run_dir)

    tasks = [generate_with_semaphore(task, i) for i, task in enumerate(failed_tasks, 1)]
    await asyncio.gather(*tasks)
    print(f"\nAll individual reports generated in: {run_dir / 'task_reports'}")

    await consolidated_report(run_dir)
    print(f"Final consolidated report in: {run_dir / 'CONSOLIDATED_REPORT.md'}")

    dashboard_title = f"{DEFAULT_DASHBOARD_TITLE} — {run_dir.name}"
    dashboard_path = run_dir / "terminal_bench_dashboard.html"
    generate_dashboard([run_dir], dashboard_path, title=dashboard_title)
    print(f"Dashboard written to: {dashboard_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path(__file__).parents[2] / "ai_working" / "tmp" / "2025-10-02__11-02-44",
        help="Directory where terminal-bench run results are stored",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of reports to generate concurrently (default: 5)",
    )

    args = parser.parse_args()
    asyncio.run(main(args.run_dir, args.concurrency))
