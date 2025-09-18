"""
The Synthesis Pipeline Orchestrator

This script manages the end-to-end synthesis process, including:
1. Triage: Filtering a corpus of documents for relevance.
2. Analysis: Performing a deep, structured analysis of each relevant document.
3. Synthesis: Combining the analyses into a final, cohesive report.

It is designed to be the single entry point for the synthesis workflow,
callable from a simple Makefile rule. It handles parallel processing and
in-memory data flow to avoid temporary files and race conditions.
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from tqdm import tqdm

from amplifier.utils.notifications import send_notification

from .analyst import run_analysis
from .config import CACHE_DIR
from .synthesist import run_synthesis
from .triage import run_triage


def get_all_files(path: str) -> list[str]:
    """Recursively finds all Markdown files in a given directory."""
    markdown_files = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))
    return markdown_files


def main():
    """Main entry point for the synthesis pipeline."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Runs the synthesis pipeline.")
    parser.add_argument("-q", "--query", type=str, required=True, help="The high-level research query.")
    parser.add_argument("-f", "--files", type=str, required=True, help="The directory of files to process.")
    parser.add_argument("--use-triaged", action="store_true", help="Enable the triage step to filter files.")
    parser.add_argument("--clear-cache", action="store_true", help="Force re-analysis even if cached versions exist.")
    parser.add_argument("--max-procs", type=int, default=10, help="Maximum number of parallel processes.")
    parser.add_argument("--notify", action="store_true", help="Send desktop notifications on completion.")
    args = parser.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)

    # --- Stage 0: File Collection ---
    all_files = get_all_files(args.files)
    if not all_files:
        print(f"Error: No Markdown files found in '{args.files}'.", file=sys.stderr)
        sys.exit(1)

    files_to_process = all_files

    # --- Stage 1: Triage (Optional) ---
    if args.use_triaged:
        print(f"--- Stage 1: Triaging {len(all_files)} documents (max_procs={args.max_procs}) ---")
        try:
            relevant_files: set[str] = set()
            with ThreadPoolExecutor(max_workers=args.max_procs) as executor:
                future_to_file = {executor.submit(run_triage, file, args.query): file for file in all_files}
                for future in tqdm(as_completed(future_to_file), total=len(all_files), desc="Triage"):
                    if future.result():
                        relevant_files.add(future_to_file[future])

            if not relevant_files:
                print("\n--- Triage resulted in 0 relevant files. Halting. ---")
                if args.notify:
                    send_notification(
                        title="Amplifier",
                        message="No relevant files found during triage",
                        cwd=os.getcwd(),
                    )
                sys.exit(0)

            print(f"\n--- Triage complete. Found {len(relevant_files)} relevant documents. ---")
            files_to_process = list(relevant_files)

            if args.notify:
                send_notification(
                    title="Amplifier",
                    message=f"Triage filtered to {len(relevant_files)}/{len(all_files)} docs",
                    cwd=os.getcwd(),
                )
        except KeyboardInterrupt:
            if args.notify:
                send_notification(
                    title="Amplifier",
                    message="Synthesis pipeline interrupted during triage",
                    cwd=os.getcwd(),
                )
            raise
        except Exception as e:
            if args.notify:
                send_notification(
                    title="Amplifier",
                    message=f"Triage failed: {str(e)[:100]}",
                    cwd=os.getcwd(),
                )
            raise

    # --- Stage 2: Analysis ---
    print(f"\n--- Stage 2: Analyzing {len(files_to_process)} documents (max_procs={args.max_procs}) ---")
    try:
        if args.clear_cache:
            print("Clearing analysis cache...")
            for item in os.listdir(CACHE_DIR):
                if item.endswith(".json"):
                    os.remove(os.path.join(CACHE_DIR, item))

        with ThreadPoolExecutor(max_workers=args.max_procs) as executor:
            # We don't need the results here, just to wait for completion.
            # The run_analysis function handles its own caching and output.
            list(
                tqdm(
                    executor.map(lambda file: run_analysis(file, args.query, args.clear_cache), files_to_process),
                    total=len(files_to_process),
                    desc="Analysis",
                )
            )

        if args.notify:
            send_notification(
                title="Amplifier",
                message=f"Analyzed {len(files_to_process)} documents",
                cwd=os.getcwd(),
            )
    except KeyboardInterrupt:
        if args.notify:
            send_notification(
                title="Amplifier",
                message="Synthesis pipeline interrupted during analysis",
                cwd=os.getcwd(),
            )
        raise
    except Exception as e:
        if args.notify:
            send_notification(
                title="Amplifier",
                message=f"Analysis failed: {str(e)[:100]}",
                cwd=os.getcwd(),
            )
        raise

    # --- Stage 3: Synthesis ---
    print("\n--- Stage 3: Synthesizing report ---")
    try:
        final_report = run_synthesis(args.query)

        print("\n\n" + "=" * 80)
        print("--- FINAL SYNTHESIS REPORT ---")
        print("=" * 80 + "\n")
        print(final_report)

        if args.notify:
            send_notification(
                title="Amplifier",
                message=f"Synthesis complete: {len(files_to_process)} documents processed",
                cwd=os.getcwd(),
            )
    except KeyboardInterrupt:
        if args.notify:
            send_notification(
                title="Amplifier",
                message="Synthesis pipeline interrupted during final synthesis",
                cwd=os.getcwd(),
            )
        raise
    except Exception as e:
        if args.notify:
            send_notification(
                title="Amplifier",
                message=f"Synthesis failed: {str(e)[:100]}",
                cwd=os.getcwd(),
            )
        raise


if __name__ == "__main__":
    main()
