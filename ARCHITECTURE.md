# Architecture Overview

This document provides the high-level architecture and component relationships for the Amplifier project. For operating principles, see CLAUDE.md. For development practices, see AGENTS.md.

## Project Purpose

Amplifier is a metacognitive AI development system that multiplies human capability through AI partnership. It transforms expertise into reusable AI tools by describing thinking processes ("metacognitive recipes") rather than writing code directly. See AMPLIFIER_VISION.md for the full vision.

## Directory Structure

```
amplifier/                    # Core library (Python package)
├── knowledge_synthesis/      # Extract & synthesize knowledge from content
├── knowledge/               # Knowledge graph, querying, visualization
├── ccsdk_toolkit/           # Claude Code SDK utilities & defensive patterns
├── memory/                  # Session memory and persistence
├── content_loader/          # Scan and index content directories
├── extraction/              # Content extraction utilities
├── search/                  # Search and retrieval
├── validation/              # Validation utilities
├── synthesis/               # Multi-stage synthesis pipeline
└── config/                  # Configuration and path management

scenarios/                    # End-user Amplifier CLI tools (see below)
├── blog_writer/             # Transform ideas into blog posts
├── article_illustrator/     # Generate AI illustrations for articles
├── transcribe/              # Transcribe audio/video with enhancement
├── tips_synthesizer/        # Synthesize scattered tips into guides
└── web_to_md/              # Convert web pages to markdown

ai_working/                   # Experimental development
├── decisions/               # Architectural decision records
└── [experiments]/           # Active explorations (graduate when mature)

tools/                        # Build and development utilities
├── transcript_manager.py    # Conversation transcript management
├── worktree_manager.py      # Git worktree utilities
├── build_ai_context_files.py
└── [other build scripts]

.claude/                      # Claude Code configuration
├── agents/                  # Specialized sub-agents
├── commands/                # Slash commands (DDD workflow, etc.)
└── tools/                   # Hooks and status line scripts

docs/                         # User documentation
ai_context/                   # AI context and philosophy documents
tests/                        # Test suite
```

## Core Architectural Patterns

### 1. Knowledge Synthesis Pipeline

**Purpose**: Transform content (articles, papers, docs) into structured, queryable knowledge.

**Flow**:
```
Content Directories → Scan & Index → Extract Knowledge → Synthesize Patterns → Build Graph → Query/Visualize
```

**Components**:
- `content_loader/` - Discovers and indexes content files
- `knowledge_synthesis/` - Extracts concepts, relationships, insights
- `knowledge/` - Builds knowledge graph, enables querying
- Graph exports: GEXF, GraphML for external analysis

**Key Commands**:
```bash
make knowledge-update          # Full pipeline
make knowledge-sync            # Extract from content
make knowledge-synthesize      # Find patterns
make knowledge-query Q="..."   # Query knowledge base
make knowledge-graph-viz       # Interactive visualization
```

### 2. Amplifier CLI Tool Pattern

**Philosophy**: "Code for structure, AI for intelligence"

**Architecture**:
- Python CLI provides reliable iteration and state management
- Claude Code SDK handles complex reasoning and content generation
- Makefile commands provide user-friendly interface
- Session state enables resumability

**Structure** (using blog_writer as exemplar):
```
scenario_name/
├── README.md                 # What it does, how to run
├── HOW_TO_CREATE_YOUR_OWN.md # Learning guide
├── __main__.py              # CLI entry point
├── workflow.py              # Orchestration logic
├── stages.py                # Individual processing stages
├── session.py               # State management
└── tests/                   # Example inputs/outputs
```

**Progressive Maturity Model**:
1. **scenarios/** - Ready for users (experimental but working)
2. **ai_working/** - Active development and refinement
3. **amplifier/** - Core library (stable, reusable)

**Consult `amplifier-cli-architect` agent** for detailed guidance on creating these tools.

### 3. Metacognitive Recipes

**Concept**: Describe HOW to think through a problem, not how to code it.

**Example** (blog_writer recipe):
```
1. Understand the author's writing style from existing posts
2. Draft content matching that style
3. Review draft for accuracy against sources
4. Review draft for style consistency
5. Get user feedback and refine
```

**Key Insight**: You describe the thinking process; Amplifier handles async/await, retry logic, state management, file I/O, error handling.

**See**: scenarios/README.md, AMPLIFIER_VISION.md

### 4. CCSDK Toolkit (Claude Code SDK Utilities)

**Location**: `amplifier/ccsdk_toolkit/`

**Purpose**: Defensive utilities for working with LLM responses.

**Key Utilities**:
- `defensive/parse_llm_json.py` - Extract JSON from any LLM response format
- `defensive/retry_with_feedback.py` - Intelligent retry with error correction
- `defensive/isolate_prompt.py` - Prevent context contamination

**Why It Exists**: LLMs don't reliably return pure JSON, even with instructions. These utilities handle format variations, provide feedback loops, and prevent context leakage.

**See**: DISCOVERIES.md "LLM Response Handling and Defensive Utilities"

### 5. Document-Driven Development (DDD)

**Workflow**: Numbered slash commands for complete feature lifecycle.

```bash
/ddd:1-plan         # Design the feature
/ddd:2-docs         # Update all docs (iterate until approved)
/ddd:3-code-plan    # Plan code changes
/ddd:4-code         # Implement and test (iterate until working)
/ddd:5-finish       # Clean up and finalize
```

**Philosophy**: Docs lead, code follows. Eliminates doc drift and context poisoning.

**See**: docs/document_driven_development/, .claude/commands/

### 6. Worktree-Based Parallel Development

**Purpose**: Experiment with multiple approaches simultaneously.

```bash
make worktree feature-jwt      # Try JWT auth
make worktree feature-oauth    # Try OAuth in parallel
make worktree-list             # Compare both
```

**Key Features**:
- Each worktree has isolated branch, environment, .data copy
- Can stash/unstash to hide/show in VSCode
- Adopt remote branches from other machines

**See**: docs/WORKTREE_GUIDE.md, tools/worktree_manager.py

## Key System Concepts

### Memory System

**Current State**: Session-based memory in `amplifier/memory/`
**Future Vision**: Long-term memory with retrieval sub-agent

**Design Goals** (from CLAUDE.md):
- Working Memory - Current session critical info
- Long-term Memory - Persistent learnings and patterns
- Retrieval System - Sub-agent to pull relevant memories per task
- Learning Log - Track what's been learned and when

### Sub-Agent Ecosystem

**Philosophy**: Delegate everything possible to specialized agents.

**Categories**:
- **Development**: zen-architect, bug-hunter, modular-builder, test-coverage
- **Knowledge Synthesis**: concept-extractor, insight-synthesizer, pattern-emergence
- **Architecture**: api-contract-designer, database-architect, security-guardian
- **Meta**: subagent-architect (creates new agents), amplifier-cli-architect

**See**: .claude/agents/, use Task tool with subagent_type parameter

### Transcript System

**Automatic Export**: PreCompact hook captures conversations before compaction
**Restoration**: `/transcripts` command restores full history
**Management**: `make transcript-list`, `make transcript-search TERM="..."`

**Why**: Never lose context to compaction. Every detail preserved for learning and continuity.

**See**: .claude/tools/hook_pre_compact.sh, tools/transcript_manager.py

## Component Relationships

### Knowledge Flow
```
Content Files → content_loader → knowledge_synthesis → knowledge graph → queries/visualization
                                       ↓
                                  Synthesis results → stored as knowledge
```

### Tool Creation Flow
```
User describes goal + thinking process → Amplifier generates tool → scenarios/[tool_name]/
                                                                            ↓
                                                              User validates → Refines
                                                                            ↓
                                                              Graduates to stable
```

### Development Flow
```
1. Design (DDD Phase 1-2) → 2. Plan Code (Phase 3) → 3. Implement (Phase 4) → 4. Finalize (Phase 5)
                                                                                      ↓
                                                                              Git worktrees for variants
```

## Configuration and Data

### Configuration Files
- `pyproject.toml` - Python dependencies (managed by uv)
- `ruff.toml` - Code formatting and linting
- `.mcp.json` - MCP server configuration
- `.env` - API keys and environment variables (copy from .env.example)

### Data Directory (`.data/`)
- Knowledge base storage
- Session states
- Transcripts
- Generated content
- **Not in git** - Local to each installation/worktree

## Integration Points

### Claude Code SDK
- Sub-agent invocation via Task tool
- Slash commands via .claude/commands/
- Hooks for automation (.claude/tools/)
- Status line customization

### External Services
- Anthropic API (Claude models)
- OpenAI API (GPT models, DALL-E)
- Google Cloud (Imagen)
- Deepgram (transcription)

### MCP Servers
- deepwiki - GitHub repository documentation
- context7 - Library documentation search
- ide - VS Code integration

## Testing Strategy

### Test Organization
- `tests/` - Unit and integration tests
- `tests/terminal_bench/` - Reproducible benchmarks vs other agents
- `scenarios/[tool]/tests/` - Example inputs/outputs per tool
- `amplifier/smoke_tests/` - Quick validation tests

### Running Tests
```bash
make test           # Full test suite
make smoke-test     # Quick validation (< 2 minutes)
make check          # Format, lint, type-check
```

## Common Development Tasks

### Adding Dependencies
```bash
cd [project-directory]    # If workspace with submodules
uv add package-name       # Automatically updates pyproject.toml and uv.lock
uv add --dev package-name # For dev dependencies
```

### Creating a New Scenario Tool
1. Describe goal and thinking process to Claude Code
2. Use `/ultrathink-task` or work interactively
3. Follow scenarios/blog_writer/ as exemplar
4. Consult `amplifier-cli-architect` agent for patterns
5. Document in tool's README.md and HOW_TO_CREATE_YOUR_OWN.md

### Working with Knowledge Base
```bash
make knowledge-update      # Extract + synthesize (full pipeline)
make knowledge-query Q="AI agents"
make knowledge-graph-viz   # Interactive visualization
make knowledge-events      # See recent pipeline activity
```

### Managing Worktrees
```bash
make worktree feature-x    # Create new experimental branch
make worktree-list         # See all worktrees
make worktree-stash name   # Hide from VSCode (keeps directory)
make worktree-rm name      # Remove completely
```

## Important Files for AI Context

When starting work in this codebase, AI assistants should read:

1. **CLAUDE.md** - Operating principles for Claude Code
2. **AGENTS.md** - Development practices and build commands
3. **ARCHITECTURE.md** (this file) - System structure
4. **DISCOVERIES.md** - Known issues and solutions
5. **ai_context/IMPLEMENTATION_PHILOSOPHY.md** - Design principles
6. **ai_context/MODULAR_DESIGN_PHILOSOPHY.md** - Modular approach
7. **scenarios/README.md** - Amplifier CLI tool philosophy

For specific features:
- **Knowledge synthesis**: amplifier/knowledge_synthesis/README.md
- **Scenario tools**: scenarios/[tool]/README.md
- **DDD workflow**: docs/document_driven_development/
- **Worktrees**: docs/WORKTREE_GUIDE.md

## Philosophy Principles

### Ruthless Simplicity
- Every line serves a clear purpose
- Minimize abstractions
- Start minimal, grow as needed
- Code you don't write has no bugs

### Modular "Bricks and Studs"
- Self-contained components with clear interfaces
- Components can be regenerated independently
- Trust in emergence over imposed complexity

### Analysis-First Development
- Think through problems before coding
- Break down complex tasks
- Use TodoWrite for tracking
- Delegate to specialized sub-agents

### Human-AI Partnership
- Humans provide vision and judgment
- AI handles exploration and implementation
- Clear handoffs between human and machine
- Learning compounds across sessions

## Success Metrics

You're using the architecture well when:

1. You quickly locate relevant components for your task
2. You understand how components interact
3. You leverage existing patterns instead of creating new ones
4. You delegate to appropriate sub-agents
5. You consult decision records before changing architecture

---

**For detailed context on any component**, read that component's README.md or consult the specialized sub-agent for that domain.
