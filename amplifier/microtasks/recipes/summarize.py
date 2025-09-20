"""
Summarize Recipe - Generate summaries and insights from markdown files.

This module processes markdown files incrementally with robust I/O and resume support.
Follows modular design principles for clean, regeneratable implementation.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..llm import LLM


def save_results_with_retry(results_file: Path, results: list[dict[str, Any]], max_retries: int = 3) -> None:
    """Save results with retry logic for cloud-synced directories."""
    retry_delay = 0.5

    for attempt in range(max_retries):
        try:
            # Write to temporary file first
            temp_file = results_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                f.flush()

            # Atomic rename
            temp_file.replace(results_file)
            return

        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                # I/O error, likely cloud sync issue
                if attempt == 0:
                    print("File I/O error - retrying (may be cloud sync delay)...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise


def process_markdown_file(llm: LLM, file_path: Path, timeout_s: int = 120) -> dict[str, Any]:
    """Process a single markdown file to generate summary and insights."""
    try:
        # Read file content
        content = file_path.read_text(encoding="utf-8")

        # Skip empty files
        if not content.strip():
            return {
                "file": str(file_path),
                "name": file_path.name,
                "summary": "Empty file",
                "insights": [],
                "status": "skipped",
            }

        # Truncate content if too long
        max_content = content[:8000] if len(content) > 8000 else content

        # Generate summary
        summary_prompt = f"""
Analyze this markdown document and provide a concise summary.

Document: {file_path.name}

{max_content}

Provide:
1. A 2-3 paragraph summary of the main points
2. Return ONLY the summary text, no labels or formatting
"""

        try:
            summary = llm.complete(summary_prompt, timeout_s=timeout_s)
        except Exception:
            summary = "Summary generation failed"

        # Generate insights
        insights_prompt = f"""
Extract key insights from this document.

Document: {file_path.name}

{max_content}

Provide:
- 3-5 actionable insights or key takeaways
- Format as a simple bullet list
- Return ONLY the bullet points, no labels
"""

        try:
            insights_raw = llm.complete(insights_prompt, timeout_s=timeout_s)
            # Parse insights into list
            insights = [
                line.strip().lstrip("- •").strip()
                for line in insights_raw.split("\n")
                if line.strip() and line.strip()[0] in "-•"
            ]
            if not insights:
                insights = [insights_raw.strip()]
        except Exception:
            insights = ["Insight generation failed"]

        return {
            "file": str(file_path),
            "name": file_path.name,
            "summary": summary.strip(),
            "insights": insights,
            "status": "success",
            "word_count": len(content.split()),
        }

    except Exception as e:
        return {
            "file": str(file_path),
            "name": file_path.name,
            "error": str(e),
            "status": "error",
        }


def run_summarize_recipe(paths: list[str], limit: int = 5, resume: bool = True, progress: Any = None) -> dict[str, Any]:
    """
    Run the summarization recipe on markdown files.

    Args:
        paths: List of paths (directories or files) to process
        limit: Maximum number of files to process
        resume: Whether to resume from existing results
        progress: Optional progress callback

    Returns:
        Summary dict with results
    """
    from ..orchestrator import MicrotaskOrchestrator

    # Initialize
    orch = MicrotaskOrchestrator()
    results_file = Path("results.json")

    # Load existing results if resuming
    existing_results = []
    processed_files = set()
    if resume and results_file.exists():
        try:
            with open(results_file, encoding="utf-8") as f:
                existing_results = json.load(f)
                processed_files = {r["file"] for r in existing_results if "file" in r}
        except (OSError, json.JSONDecodeError):
            pass

    # Find markdown files
    md_files = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".md":
            md_files.append(path)
        elif path.is_dir():
            md_files.extend(sorted(path.glob("**/*.md")))

    # Filter already processed and apply limit
    files_to_process = [f for f in md_files if str(f) not in processed_files]
    files_to_process = files_to_process[: max(0, limit - len(existing_results))]

    if not files_to_process and not existing_results:
        raise ValueError("No markdown files found to process")

    # Define processing steps
    def process_files(llm: LLM, artifacts: Path) -> dict[str, Any]:
        results = list(existing_results)  # Start with existing

        for i, file_path in enumerate(files_to_process):
            print(f"Processing {i + 1}/{len(files_to_process)}: {file_path.name}")

            # Process file
            result = process_markdown_file(llm, file_path)
            results.append(result)

            # Save incrementally
            save_results_with_retry(results_file, results)

            # Save to artifacts too
            (artifacts / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

        # Calculate stats
        successful = sum(1 for r in results if r.get("status") == "success")
        errors = sum(1 for r in results if r.get("status") == "error")
        skipped = sum(1 for r in results if r.get("status") == "skipped")

        # Print summary
        print(f"\n{'=' * 50}")
        print("Summarization Complete")
        print(f"{'=' * 50}")
        print(f"Results saved to: {results_file}")
        print(f"Files processed: {len(results)}")
        print(f"  ✓ Successful: {successful}")
        if errors > 0:
            print(f"  ✗ Errors: {errors}")
        if skipped > 0:
            print(f"  ○ Skipped: {skipped}")

        return {
            "files_processed": len(results),
            "successful": successful,
            "errors": errors,
            "skipped": skipped,
            "output_file": str(results_file),
        }

    # Run orchestrator
    steps = [("summarize", process_files)]
    meta = {
        "source_paths": paths,
        "limit": limit,
        "resume": resume,
        "existing_count": len(existing_results),
        "new_count": len(files_to_process),
    }

    summary = orch.run("summarize", steps, meta=meta, fail_fast=True, on_event=progress)
    return summary.model_dump()
