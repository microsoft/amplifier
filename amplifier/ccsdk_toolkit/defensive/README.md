# CCSDK Defensive Utilities

Minimal, battle-tested patterns for reliable LLM integration and file I/O in cloud environments.

## Quick Start

```python
from amplifier.ccsdk_toolkit.defensive import (
    parse_llm_json,      # Extract JSON from any LLM response
    retry_with_feedback, # Intelligent retry with error correction
    isolate_prompt,      # Prevent context contamination
    write_json_with_retry # Cloud sync-aware file operations
)
```

## What This Solves

These utilities address the three most common failure modes in LLM-integrated applications:

1. **Unpredictable LLM Output** - Models wrap JSON in markdown, add explanations, or return malformed data
2. **Context Contamination** - System instructions leak into generated content
3. **Cloud Sync I/O Errors** - Mysterious failures in OneDrive/Dropbox directories

## Core Utilities

- `parse_llm_json()` - Extracts JSON from any format (markdown blocks, mixed prose, etc.)
- `retry_with_feedback()` - Retries with error details so LLM can self-correct
- `isolate_prompt()` - Prevents instruction injection and context bleeding
- `write_json_with_retry()` / `read_json_with_retry()` - Handles cloud sync delays gracefully

## Canonical Example

The `idea_synthesis` tool demonstrates best practices:

```python
from amplifier.ccsdk_toolkit.defensive import parse_llm_json, isolate_prompt

# 1. Isolate user content
safe_content = isolate_prompt(user_text)

# 2. Get LLM response
response = await llm.complete(f"Analyze: {safe_content}")

# 3. Parse defensively with fallback
result = parse_llm_json(response, default={"status": "unknown"})

# 4. Save with cloud sync awareness
write_json_with_retry(result, output_path)
```

## Learn More

See [PATTERNS.md](./PATTERNS.md) for:
- Detailed usage examples
- Common failure modes and solutions
- Performance implications
- Migration guide from custom implementations
- Best practices for LLM interactions

## Philosophy

Following our ruthless simplicity principle, these utilities:
- Do one thing well
- Have minimal dependencies
- Handle the 95% case
- Provide clear error messages
- Work silently when things go right

## When to Use

**Always** - These should be your first import when building any CCSDK tool that:
- Processes LLM responses
- Handles user-provided prompts
- Performs file I/O in user directories

Don't reinvent these patterns. They're battle-tested across multiple production tools and handle edge cases you haven't thought of yet.