# Competitive Analysis Tool

Professional-grade competitive intelligence system using expert frameworks and multi-perspective analysis.

## Overview

The Competitive Analysis Tool applies industry-standard strategic frameworks to generate comprehensive competitive intelligence reports. Built on a multi-stage pipeline architecture with JSON checkpointing, it combines web research, framework-based analysis, cross-framework synthesis, and audience-specific formatting.

## Core Features

### Expert Frameworks

- **Porter's Five Forces**: Analyze industry structure, competitive dynamics, and strategic positioning
- **SWOT Analysis**: Identify strengths, weaknesses, opportunities, and threats for each entity
- **Strategic Positioning**: Map market position, differentiation, and competitive advantages

### Multi-Stage Pipeline

1. **Research Stage**: Web search and data gathering with source tracking
2. **Analysis Stage**: Apply multiple frameworks in parallel to the same data
3. **Synthesis Stage**: Extract cross-framework insights and patterns
4. **Format Stage**: Generate audience-specific reports from analysis
5. **Compare Stage**: Highlight changes vs. previous analyses (temporal tracking)

### Audience-Specific Outputs

- **Executive View**: Strategic implications, market positioning, investment recommendations
- **Product Manager View**: Feature gaps, user experience comparisons, roadmap insights
- **Sales View**: Competitive positioning, objection handling, differentiation talking points
- **Investor View**: Market dynamics, growth potential, competitive moats

### Resilience & Checkpointing

The pipeline saves JSON checkpoints after each stage:
- `research.json` - Raw research data with sources
- `analysis.json` - Framework analysis results
- `synthesis.json` - Cross-framework insights
- `report.md` - Formatted audience-specific report
- `comparison.md` - Changes vs. previous run (if available)

This enables:
- Resume after failures
- Refresh research without re-analyzing
- Structured temporal tracking via JSON diffs

## Usage

### Basic Analysis

```bash
# Compare two entities with default settings
make compete ENTITY1="Anthropic" ENTITY2="OpenAI"

# Or use Python directly
python -m ai_working.competitive_analysis "Anthropic" "OpenAI"
```

### Framework Selection

```bash
# Use specific frameworks
make compete ENTITY1="Notion" ENTITY2="Obsidian" FRAMEWORKS="porter,swot"

# Default: All available frameworks
```

### Audience-Specific Reports

```bash
# Generate report for specific audience
make compete ENTITY1="AWS" ENTITY2="Google Cloud" AUDIENCE="executive"

# Available audiences: executive, pm, sales, investor
# Default: executive
```

### Temporal Tracking

```bash
# Compare against previous analysis
make compete ENTITY1="Shopify" ENTITY2="WooCommerce" COMPARE=true

# Automatically detects previous analyses and highlights changes
```

### Custom Output

```bash
# Specify output directory
make compete ENTITY1="Tesla" ENTITY2="Rivian" OUTPUT="reports/automotive"
```

## Architecture

```
competitive_analysis/
├── stages/
│   ├── research.py      (~100 lines) - Web search + data gathering
│   ├── analyze.py       (~150 lines) - Apply frameworks
│   ├── synthesize.py    (~100 lines) - Cross-framework insights
│   └── format.py        (~100 lines) - Audience-specific rendering
├── frameworks/
│   ├── porter.py        (~50 lines) - Five Forces prompts
│   ├── swot.py          (~50 lines) - SWOT prompts
│   └── positioning.py   (~50 lines) - Market positioning prompts
├── models.py            (~50 lines) - Pydantic schemas
├── compare.py           (~100 lines) - Temporal diff analysis
└── cli.py               (~100 lines) - Pipeline orchestration

Total: ~850 lines
```

## Output Structure

### Default Output Directory

```
competitive_analysis_<entity1>_vs_<entity2>_<timestamp>/
├── research.json        # Raw research data
├── analysis.json        # Framework results
├── synthesis.json       # Cross-framework insights
├── report.md            # Formatted report
└── comparison.md        # Changes vs. previous (if available)
```

### Report Format

Each report includes:
- **Executive Summary**: Key findings and strategic implications
- **Framework Analysis**: Results from each applied framework
- **Synthesis**: Cross-framework insights and patterns
- **Recommendations**: Actionable strategic guidance
- **Sources**: Complete citation list

## Design Philosophy

### Modular & Regenerable

- Each stage is self-contained (~100-150 lines)
- Clear JSON contracts between stages
- Can regenerate any stage independently
- Total ~850 lines (philosophy-compliant)

### Frameworks as Prompts

- Frameworks implemented as prompt templates, not class hierarchies
- Simple, focused, maintainable
- Easy to add new frameworks

### Ruthless Simplicity

- No database (JSON files for state)
- No scheduler (run on-demand)
- No visualization library (markdown output)
- YAGNI principle throughout

## Examples

See `EXAMPLES.md` for real-world analyses:
- Anthropic vs. OpenAI (AI industry)
- Notion vs. Obsidian (productivity tools)
- AWS vs. Google Cloud (cloud platforms)
- Tesla vs. Rivian (automotive)

## Implementation Notes

- Uses Claude Code SDK with web search enabled
- Pydantic models for JSON schema validation
- Checkpoint-based pipeline for resilience
- Temporal tracking via JSON diffs
- ~850 lines total implementation
- Follows modular design philosophy

## Requirements

- Claude Code SDK
- click (CLI framework)
- pydantic (data validation)
