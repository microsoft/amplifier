"""Exemplar library for tool generation - provides patterns to learn from, not rigid templates."""

import json
from pathlib import Path
from typing import Any


def load_exemplars() -> dict[str, str]:
    """Load exemplar patterns from existing tools and philosophy.

    Returns dict of exemplar_name -> pattern_code
    """
    exemplars = {}

    # Collection processor pattern (most common)
    exemplars["collection_processor"] = '''
async def process_collection(source_dir: Path, output_dir: Path, limit: int = None):
    """Process a collection with resume capability and progress tracking."""

    # Setup with existing results check
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"
    existing = read_json(results_file) if results_file.exists() else {}

    # Discover items to process
    items = list(source_dir.glob("*.md"))[:limit]
    total = len(items)

    # Process with progress and immediate saves
    for i, item in enumerate(items, 1):
        # Check if already processed (resume capability)
        if str(item) in existing:
            print(f"[{i}/{total}] Skipping {item.name} - already processed")
            continue

        print(f"[{i}/{total}] Processing {item.name}...")

        # AI processing with proper timeout
        async with asyncio.timeout(120):  # CRITICAL: 120-second timeout
            result = await process_with_ai(item.read_text())

        # Save immediately (incremental progress)
        existing[str(item)] = result
        write_json(existing, results_file)

        print(f"✓ Completed {item.name}")

    return existing
'''

    # Synthesis pattern (combining sources)
    exemplars["synthesis"] = '''
async def synthesize_insights(sources: List[Path], output_path: Path):
    """Synthesize insights from multiple sources."""

    # Gather all source content
    contents = []
    for source in sources:
        content = read_file(source)  # Using retry-enabled utility
        contents.append({"path": str(source), "content": content})

    # AI synthesis with timeout
    prompt = format_synthesis_prompt(contents)
    async with asyncio.timeout(120):  # CRITICAL: 120-second timeout
        synthesis = await ai_synthesize(prompt)

    # Save with structure
    output = {
        "sources": [str(s) for s in sources],
        "synthesis": synthesis,
        "timestamp": datetime.now().isoformat()
    }
    write_json(output, output_path)

    return synthesis
'''

    # Multi-stage pipeline pattern
    exemplars["multi_stage_pipeline"] = '''
def step_discover(art: Path, src: Path, limit: int) -> dict[str, Any]:
    """Discovery stage - find items to process."""
    files = sorted(src.glob('*.md'))[:limit]
    (art / 'discover.json').write_text(json.dumps([str(p) for p in files], indent=2))
    return {'count': len(files), 'files': [str(p) for p in files]}

def step_process_each(art: Path, work: Path) -> dict[str, Any]:
    """Process each item with resume capability."""
    listing = json.loads((art / 'discover.json').read_text())
    out_dir = work / 'processed'
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, item_path in enumerate(listing, 1):
        p = Path(item_path)
        out = out_dir / f"{p.stem}.processed.json"

        # Skip if already processed (resume capability)
        if out.exists():
            continue

        # Process with AI
        result = process_item(p)

        # Save immediately
        out.write_text(json.dumps(result, indent=2))

    return {'processed': len(listing)}
'''

    # Error handling pattern
    exemplars["error_handling"] = """
try:
    async with asyncio.timeout(120):
        result = await process_with_ai(content)
except asyncio.TimeoutError:
    print(f"Timeout processing {item_name} - likely SDK unavailable")
    result = {"error": "timeout", "item": item_name}
except Exception as e:
    print(f"Error processing {item_name}: {e}")
    result = {"error": str(e), "item": item_name}

# Save even failed results for debugging
results[item_name] = result
write_json(results, output_file)
"""

    return exemplars


def find_similar(ask: str) -> list[dict[str, Any]]:
    """Find exemplars relevant to the user's ask.

    Args:
        ask: User's tool description/requirements

    Returns:
        List of relevant exemplars with metadata
    """
    ask_lower = ask.lower()
    exemplars = load_exemplars()
    relevant = []

    # Pattern matching for relevance
    if any(word in ask_lower for word in ["collection", "multiple", "files", "batch", "process each"]):
        relevant.append(
            {
                "name": "collection_processor",
                "code": exemplars["collection_processor"],
                "description": "Pattern for processing collections with resume capability",
            }
        )

    if any(word in ask_lower for word in ["synthesize", "combine", "merge", "aggregate", "summary"]):
        relevant.append(
            {
                "name": "synthesis",
                "code": exemplars["synthesis"],
                "description": "Pattern for combining information from multiple sources",
            }
        )

    if any(word in ask_lower for word in ["pipeline", "stages", "steps", "workflow"]):
        relevant.append(
            {
                "name": "multi_stage_pipeline",
                "code": exemplars["multi_stage_pipeline"],
                "description": "Pattern for multi-stage processing pipelines",
            }
        )

    # Always include error handling as it's critical
    relevant.append(
        {
            "name": "error_handling",
            "code": exemplars["error_handling"],
            "description": "Pattern for robust error handling",
        }
    )

    return relevant


def get_exemplar_context(exemplars: list[dict[str, Any]]) -> str:
    """Format exemplars as context for AI generation.

    Args:
        exemplars: List of exemplar dicts with name, code, description

    Returns:
        Formatted string for inclusion in prompts
    """
    if not exemplars:
        return "No specific exemplars identified for this task."

    context = "Here are relevant patterns from existing successful tools:\n\n"

    for ex in exemplars:
        context += f"## {ex['name']}\n"
        context += f"{ex['description']}\n\n"
        context += f"```python\n{ex['code']}\n```\n\n"

    context += """
Note: These are PATTERNS to learn from, not templates to copy exactly.
Adapt them to the specific requirements while maintaining their core principles:
- Incremental saves after each item
- Resume capability by checking existing results
- 120-second timeout for all SDK calls
- Retry-enabled file I/O utilities
"""

    return context
