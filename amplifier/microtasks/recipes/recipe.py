"""
Recipe: Process Collection
Purpose: Process a collection of markdown files with Claude Code SDK
Contract: Directory of .md files → JSON results with AI processing
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_code_sdk import ClaudeCodeOptions
from claude_code_sdk import ClaudeSDKClient

from amplifier.utils.file_io import read_json
from amplifier.utils.file_io import write_json


async def process_collection(source_dir: Path, output_dir: Path, limit: int | None = None) -> dict[str, Any]:
    """Process a collection of markdown files with resume capability and progress tracking.

    Args:
        source_dir: Directory containing markdown files to process
        output_dir: Directory to save results
        limit: Optional limit on number of files to process

    Returns:
        Dictionary with processing summary and results
    """
    # Setup phase
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"

    # Load existing results for resume capability
    existing = read_json(results_file) if results_file.exists() else {}

    # Discovery phase
    items = list(source_dir.glob("*.md"))
    if limit:
        items = items[:limit]
    total = len(items)

    if total == 0:
        print(f"No markdown files found in {source_dir}")
        return {"status": "complete", "total": 0, "processed": 0, "skipped": 0, "results": existing}

    # Track processing stats
    processed = 0
    skipped = 0
    errors = 0

    # Processing phase with immediate saves
    for idx, item_path in enumerate(items, 1):
        item_id = item_path.stem  # Use filename without extension as ID

        # Skip already processed items
        if item_id in existing:
            print(f"[{idx}/{total}] Skipping {item_path.name} - already processed")
            skipped += 1
            continue

        # Show progress
        print(f"[{idx}/{total}] Processing {item_path.name}...")

        try:
            # Read the markdown content
            content = item_path.read_text(encoding="utf-8")

            # Process with AI (includes timeout)
            result = await process_with_ai(content, item_path.name)

            # Save result immediately
            existing[item_id] = {
                "filename": item_path.name,
                "processed_at": datetime.now().isoformat(),
                "result": result,
            }
            write_json(existing, results_file)
            processed += 1

        except TimeoutError:
            print(f"  ⚠️ Timeout processing {item_path.name} - skipping")
            errors += 1
            # Don't save failed items - allows retry later

        except Exception as e:
            print(f"  ❌ Error processing {item_path.name}: {e}")
            errors += 1
            # Don't save failed items - allows retry later

    # Final summary
    print("\n✅ Processing complete!")
    print(f"  Total files: {total}")
    print(f"  Processed: {processed}")
    print(f"  Skipped (already done): {skipped}")
    if errors > 0:
        print(f"  Errors: {errors}")

    return {
        "status": "complete",
        "total": total,
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
        "results": existing,
    }


async def process_with_ai(content: str, filename: str) -> dict[str, Any]:
    """Process a single markdown file with Claude Code SDK.

    Args:
        content: The markdown content to process
        filename: Name of the file being processed

    Returns:
        Dictionary containing AI processing results
    """
    # CRITICAL: 120-second timeout for SDK operations
    try:
        async with asyncio.timeout(120):
            try:
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="""You are an expert at analyzing and summarizing markdown documents.
                        Extract key information, identify main topics, and provide structured insights.""",
                        max_turns=1,
                    )
                ) as client:
                    # Send the content for processing
                    prompt = f"""Analyze this markdown document and provide:
                    1. A brief summary (2-3 sentences)
                    2. Key topics/themes (list)
                    3. Main insights or takeaways
                    4. Any notable patterns or observations

                    Document: {filename}

                    Content:
                    {content}

                    Return your analysis as structured JSON with keys: summary, topics, insights, patterns"""

                    await client.query(prompt)

                    # Collect response
                    response = ""
                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content_blocks = getattr(message, "content", [])
                            if isinstance(content_blocks, list):
                                for block in content_blocks:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

                    # Parse JSON response
                    if response:
                        # Clean markdown formatting if present
                        cleaned = response.strip()
                        if cleaned.startswith("```json"):
                            cleaned = cleaned[7:]
                        elif cleaned.startswith("```"):
                            cleaned = cleaned[3:]
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3]
                        cleaned = cleaned.strip()

                        try:
                            return json.loads(cleaned)
                        except json.JSONDecodeError:
                            # Fallback: return as plain text if not valid JSON
                            return {"raw_response": response}
                    else:
                        return {"error": "Empty response from AI"}

            except Exception as e:
                # If SDK not available or other error, return minimal result
                return {
                    "error": f"AI processing failed: {str(e)}",
                    "fallback": True,
                    "summary": f"Failed to process {filename}",
                }
    except TimeoutError:
        # Timeout after 120 seconds
        return {
            "error": "Processing timeout after 120 seconds",
            "fallback": True,
            "summary": f"Timeout processing {filename}",
        }

    # This should never be reached, but satisfies type checker
    return {
        "error": "Unexpected error in processing",
        "fallback": True,
        "summary": f"Unable to process {filename}",
    }


def register_recipe():
    """Register this recipe for the amplifier CLI.

    Returns:
        Dictionary with recipe metadata and entry point
    """
    return {
        "name": "process",
        "description": "Process a collection of markdown files with Claude Code SDK",
        "process_collection": process_collection,
        "version": "1.0.0",
        "author": "Amplifier Team",
        "requirements": ["claude_code_sdk", "amplifier.utils.file_io"],
    }


# Allow direct execution for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python recipe.py <source_dir> <output_dir> [limit]")
        sys.exit(1)

    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

    # Run the processing
    result = asyncio.run(process_collection(source, output, limit))
    print(f"\nFinal result: {json.dumps(result, indent=2)}")
