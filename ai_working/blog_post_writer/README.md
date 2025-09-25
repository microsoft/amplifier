# Blog Post Writer Tool

A modular AI-powered tool for creating blog posts that match an author's style while maintaining factual accuracy.

## Purpose

Transform brain dumps and rough ideas into polished blog posts that:
- Match the author's unique writing style
- Maintain factual accuracy with source verification
- Allow iterative refinement through user feedback

## Architecture

```
blog_post_writer/
├── README.md                 # Tool specification (this file)
├── __init__.py              # Public interface exports
├── main.py                  # CLI entry point and orchestrator
├── state.py                 # State management module
├── style_extractor/         # Extract author style patterns
├── blog_writer/            # Generate blog content
├── source_reviewer/        # Verify source accuracy
├── style_reviewer/         # Check style consistency
├── user_feedback/          # Handle user interaction
└── data/                   # Working directory for state/output
```

## Module Contracts

### State Management (`state.py`)
**Purpose**: Persist pipeline state for resume capability
**Inputs**: Module states, iteration history
**Outputs**: Saved state file
**Side Effects**: Writes to `data/state.json`

### Style Extractor (`style_extractor/`)
**Purpose**: Analyze existing writings to extract author's style
**Inputs**: Directory of author's writings
**Outputs**: Style profile (tone, vocabulary, patterns)
**Dependencies**: ClaudeSession

### Blog Writer (`blog_writer/`)
**Purpose**: Generate blog post from brain dump using style profile
**Inputs**: Brain dump markdown, style profile
**Outputs**: Draft blog post
**Dependencies**: ClaudeSession, style profile

### Source Reviewer (`source_reviewer/`)
**Purpose**: Verify factual accuracy and source attribution
**Inputs**: Blog draft, source materials
**Outputs**: Accuracy report with suggested corrections
**Dependencies**: ClaudeSession

### Style Reviewer (`style_reviewer/`)
**Purpose**: Check style consistency with author profile
**Inputs**: Blog draft, style profile
**Outputs**: Style consistency report with suggestions
**Dependencies**: ClaudeSession

### User Feedback (`user_feedback/`)
**Purpose**: Parse user feedback and apply changes
**Inputs**: User feedback text with [bracket-comments]
**Outputs**: Parsed feedback directives
**Dependencies**: None (pure parsing)

## Pipeline Flow

1. **Extract Style**: Analyze writings directory → create style profile
2. **Generate Draft**: Brain dump + style → initial blog post
3. **Review Sources**: Check accuracy → feedback if issues
4. **Review Style**: Check consistency → feedback if issues
5. **User Review**: Get user feedback → apply changes
6. **Iterate**: Max 10 iterations with state saved after each
7. **Output**: Final polished blog post

## Usage

```bash
python -m ai_working.blog_post_writer \
  --brain-dump brain_dump.md \
  --writings-dir my_writings/ \
  --output blog_post.md \
  --resume  # Optional: resume from saved state
```

## Key Features

- **Incremental Progress**: State saved after every operation
- **Resume Capability**: Can continue from any interruption
- **Iteration Safety**: Maximum 10 iterations to prevent infinite loops
- **User Control**: Parse [bracket-comments] for specific guidance
- **Defensive I/O**: Retry logic for file operations
- **Clear Logging**: Progress visibility at every stage

## Configuration

Environment variables:
- `CLAUDE_CLI_PATH`: Path to Claude CLI (auto-detected if not set)
- `MAX_ITERATIONS`: Override default 10 iteration limit

## Error Handling

| Error Type | Recovery Strategy |
|------------|------------------|
| LLM Timeout | Retry with exponential backoff |
| File I/O Error | Retry with cloud sync warning |
| Invalid Input | Clear error message and exit |
| Style Extraction Failure | Proceed with generic style |

## Testing

```bash
# Run with sample data
python -m ai_working.blog_post_writer \
  --brain-dump tests/sample_brain_dump.md \
  --writings-dir tests/sample_writings/ \
  --output tests/output.md

# Resume from interruption
python -m ai_working.blog_post_writer --resume data/state.json
```

## Implementation Philosophy

Following the modular "bricks and studs" approach:
- Each module is self-contained with clear contracts
- State management enables regeneration without loss
- Simple, direct implementations without abstractions
- Defensive patterns for LLM and file operations