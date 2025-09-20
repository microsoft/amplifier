# Idea Synthesis Tool

A Claude Code SDK-powered tool that synthesizes insights from markdown documentation through a 4-stage AI pipeline.

## Overview

The Idea Synthesis tool processes your AI context documentation (or any markdown files) to:
- Extract key points and ideas from each document
- Identify cross-cutting themes across documents
- Synthesize themes into actionable insights
- Generate comprehensive reports with recommendations

## Features

- **4-Stage Pipeline**:
  1. **Reader**: Loads markdown files from directories
  2. **Summarizer**: Creates AI-powered summaries of each file
  3. **Synthesizer**: Identifies themes across all summaries
  4. **Expander**: Expands themes with context and action items

- **Defensive LLM Handling**: Uses CCSDK defensive utilities for robust JSON parsing
- **Incremental Processing**: Saves progress after every item
- **Resume Support**: Continue interrupted sessions with `--resume`
- **Cloud-Sync Resilient**: Handles OneDrive/Dropbox file I/O issues
- **Multiple Output Formats**: Markdown reports or JSON data

## Installation

Requires Claude Code SDK CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

## Usage

### Basic Usage

Process all markdown files in a directory:
```bash
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/
```

### Process with Limit

Process only the first 5 files:
```bash
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/ --limit 5
```

### Save Results

Specify output directory:
```bash
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/ --output results/
```

### Resume Interrupted Session

If processing was interrupted, resume with the session ID:
```bash
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/ --resume abc123
```

### JSON Output

Get results in JSON format:
```bash
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/ --json-output
```

## Options

- `--pattern TEXT`: File pattern to match (default: `*.md`)
- `--recursive`: Search directories recursively (default: true)
- `--limit INTEGER`: Process only N files
- `--resume TEXT`: Resume from previous session ID
- `--output PATH`: Output directory for results
- `--json-output`: Output results as JSON
- `--verbose`: Enable verbose output

## Output

The tool generates:

1. **synthesis_state.json**: Current processing state (for resume)
2. **synthesis_report.md**: Markdown report with themes and insights
3. **synthesis_results.json**: JSON data (when using --json-output)

### Sample Report Structure

```markdown
# Idea Synthesis Report

## Cross-Cutting Themes
- Theme descriptions
- Supporting points
- Source documents
- Confidence scores

## Expanded Synthesis
- Actionable insights
- Synthesized ideas
- Action items
- Supporting quotes
```

## Architecture

The tool follows modular design principles:

```
idea_synthesis/
├── cli.py              # Main CLI entry point
├── models.py           # Data structures
├── stages/
│   ├── reader.py       # File reading stage
│   ├── summarizer.py   # AI summarization
│   ├── synthesizer.py  # Theme extraction
│   └── expander.py     # Idea expansion
└── utils/
    ├── claude_helper.py  # Claude SDK wrapper
    └── file_io.py        # Retry-enabled I/O
```

## Key Features

### Incremental Saves
- Saves after every file processed
- Saves after every theme synthesized
- Never lose progress, even on errors

### Smart Resume
- Skip already-processed files
- Continue from exact stopping point
- Preserve all previous work

### Cloud Sync Handling
- Automatic retry on file I/O errors
- Handles OneDrive/Dropbox delays
- Clear warnings about cloud sync issues

### Natural Completion
- Operations run to completion without time limits
- Streaming provides visibility into progress
- Trust through transparency philosophy

## Requirements

- Python 3.11+
- Claude Code SDK CLI installed globally
- Access to Claude Code API
