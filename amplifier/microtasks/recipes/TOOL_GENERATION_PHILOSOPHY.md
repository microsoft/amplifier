# Tool Generation Philosophy

This document guides the AI-driven generation of amplifier CLI tools, ensuring all generated tools follow our core principles and proven patterns.

## Core Principle: Code for Structure, AI for Intelligence

Every generated tool must clearly separate responsibilities:
- **Code handles**: Iteration, state management, file I/O, error recovery, progress tracking
- **AI handles**: Analysis, reasoning, synthesis, creative insights, pattern recognition
- **Never mix**: Don't embed business logic in prompts, don't hardcode what AI should determine

## The Five Pillars of Tool Generation

### 1. Incremental Progress (CRITICAL)

**Rule**: Save after EVERY item processed, not at intervals or completion.

```python
# CORRECT: Save immediately after each item
for item in items:
    result = process(item)
    results[item.id] = result
    save_results(results)  # IMMEDIATE SAVE

# WRONG: Batch saving loses progress
for item in items:
    results.append(process(item))
save_results(results)  # TOO LATE - could lose everything
```

**Rationale**: Users can abort anytime without losing work. Failures don't waste completed processing.

### 2. Resume Capability (MANDATORY)

**Rule**: Always check if work already exists before processing.

```python
# CORRECT: Skip already processed items
existing = load_existing_results()
for item in items:
    if item.id in existing:
        continue  # Skip, don't reprocess
    result = process(item)
    save_result(item.id, result)

# WRONG: Reprocessing everything wastes API calls
for item in items:
    result = process(item)  # Wasteful if already done
```

**Rationale**: Supports incremental updates, handles interruptions gracefully, saves API costs.

### 3. Claude Code SDK Timeout (NON-NEGOTIABLE)

**Rule**: ALWAYS use 120-second timeout for Claude Code SDK operations.

```python
# CORRECT: 120-second timeout
async with asyncio.timeout(120):  # EXACTLY 120, not less
    async with ClaudeSDKClient(...) as client:
        result = await client.query(prompt)

# FATAL: Shorter timeouts break working code
async with asyncio.timeout(30):  # BREAKS IN PRODUCTION
    # This WILL fail for real operations
```

**Rationale**: SDK operations take 30-60+ seconds normally. 120 seconds prevents premature failures.

### 4. Robust File I/O (REQUIRED)

**Rule**: Use retry-enabled file utilities for ALL file operations.

```python
# CORRECT: Use utilities with built-in retry
from amplifier.utils.file_io import write_json, read_json
write_json(data, filepath)  # Handles cloud sync delays

# WRONG: Direct file I/O fails with cloud sync
with open(filepath, 'w') as f:  # Can fail with OSError
    json.dump(data, f)
```

**Rationale**: Cloud-synced directories (OneDrive, Dropbox) cause intermittent I/O errors.

### 5. Clear Progress Communication

**Rule**: Show users what's happening and what remains.

```python
# CORRECT: Informative progress
print(f"Processing item {i}/{total}: {item.name}")
print(f"✓ Completed {item.name} - {total-i} remaining")

# WRONG: Silent processing
for item in items:
    process(item)  # User has no idea what's happening
```

**Rationale**: Long-running tools need visibility. Users need to know if they should wait or abort.

## Evaluation Criteria for Generated Tools

### MUST PASS Checks

1. **Timeout Check**: All SDK calls use >= 120 second timeout
2. **Save Check**: Results saved immediately after each item
3. **Resume Check**: Existing results checked before processing
4. **I/O Check**: File operations use retry utilities
5. **Progress Check**: User-visible progress indicators present

### SHOULD PASS Checks

1. **Simplicity**: No unnecessary abstractions or complexity
2. **Modularity**: Clear separation of concerns
3. **Documentation**: Purpose and usage clearly documented
4. **Error Handling**: Failures reported with actionable messages
5. **Integration**: Makefile target provided for easy access

## Pattern Library

### Collection Processing Pattern

The most common pattern for tools that process multiple items:

```python
async def process_collection(source_dir: Path, output_dir: Path, limit: int = None):
    """Process a collection with resume capability and progress tracking."""

    # 1. Setup with existing results check
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"
    existing = read_json(results_file) if results_file.exists() else {}

    # 2. Discover items to process
    items = list(source_dir.glob("*.md"))[:limit]
    total = len(items)

    # 3. Process with progress and immediate saves
    for i, item in enumerate(items, 1):
        # Check if already processed (resume capability)
        if str(item) in existing:
            print(f"[{i}/{total}] Skipping {item.name} - already processed")
            continue

        print(f"[{i}/{total}] Processing {item.name}...")

        # AI processing with proper timeout
        async with asyncio.timeout(120):
            result = await process_with_ai(item.read_text())

        # Save immediately (incremental progress)
        existing[str(item)] = result
        write_json(existing, results_file)

        print(f"✓ Completed {item.name}")

    return existing
```

### Synthesis Pattern

For tools that combine information from multiple sources:

```python
async def synthesize_insights(sources: List[Path], output_path: Path):
    """Synthesize insights from multiple sources."""

    # 1. Gather all source content
    contents = []
    for source in sources:
        content = read_file(source)  # Using retry-enabled utility
        contents.append({"path": str(source), "content": content})

    # 2. AI synthesis with timeout
    prompt = format_synthesis_prompt(contents)
    async with asyncio.timeout(120):
        synthesis = await ai_synthesize(prompt)

    # 3. Save with structure
    output = {
        "sources": [str(s) for s in sources],
        "synthesis": synthesis,
        "timestamp": datetime.now().isoformat()
    }
    write_json(output, output_path)

    return synthesis
```

## Common Pitfalls to Avoid

### Fatal Errors (Tool will fail in production)

- ❌ SDK timeout < 120 seconds
- ❌ No incremental saves (lose all progress on failure)
- ❌ No resume capability (waste API calls on retries)
- ❌ Direct file I/O without retry (cloud sync failures)
- ❌ Nested asyncio.run() calls (hangs forever)

### Design Errors (Tool works but poorly)

- ❌ Silent failures (user doesn't know what went wrong)
- ❌ No progress indicators (user doesn't know if working)
- ❌ Over-engineering (complex state machines, unnecessary abstractions)
- ❌ Template thinking (forcing all tools into same mold)
- ❌ Missing Makefile integration (hard to discover/use)

## Philosophy Injection Points

During tool generation, inject these principles at each stage:

### Planning Stage
- Remind: "Code for structure, AI for intelligence"
- Ask: "What needs reliability (code) vs creativity (AI)?"
- Consider: "How will users resume if interrupted?"

### Implementation Stage
- Enforce: 120-second timeout rule
- Require: Incremental saves after each item
- Mandate: File I/O through retry utilities
- Include: Progress indicators

### Evaluation Stage
- Check: Do timeouts meet minimum?
- Verify: Are saves incremental?
- Confirm: Can processing resume?
- Test: Will cloud sync delays be handled?

## Success Metrics

A well-generated tool exhibits these qualities:

1. **Resilient**: Handles interruptions, network issues, cloud sync delays
2. **Transparent**: Shows clear progress, reports failures helpfully
3. **Efficient**: Doesn't reprocess completed work, saves API costs
4. **Simple**: No unnecessary complexity, easy to understand
5. **Integrated**: Works seamlessly with amplifier ecosystem

## Remember

> "Every tool is a hybrid: code provides the skeleton, AI provides the brain. Never confuse which does what."

This philosophy ensures generated tools are production-ready from the start, embodying our principles of ruthless simplicity while maintaining robustness where it matters.