# Amplifier Ecosystem Overview

## What is Amplifier?

Amplifier is a **modular AI agent framework** built on the Linux kernel philosophy: a tiny, stable kernel that provides mechanisms only, with all policies and features living at the edges as replaceable modules.

**Core Principle**: "The center stays still so the edges can move fast."

## The Ecosystem

### Entry Point (amplifier)
The main repository providing:
- User-facing documentation
- Getting started guides
- Ecosystem overview
- Repository governance rules

### Kernel (amplifier-core)
The ultra-thin kernel (~2,600 lines) providing:
- Session lifecycle management
- Module loading/unloading
- Event system and hooks
- Coordinator infrastructure
- Stable contracts and protocols

**Key insight**: The kernel provides MECHANISMS, never POLICIES.

### Foundation Library (amplifier-foundation)
The primary library for building applications:
- Bundle primitives (composition, validation)
- Reference bundles and behaviors
- Best-practice examples
- Shared utilities

### Modules
Swappable capabilities that plug into the kernel (exactly 5 types):

| Type | Purpose | Examples |
|------|---------|----------|
| **Provider** | LLM backends | anthropic, openai, azure, ollama |
| **Tool** | Agent capabilities (LLM-decided) | filesystem, bash, web, search, task |
| **Orchestrator** | **The main engine** driving sessions | loop-basic, loop-streaming, loop-events |
| **Context** | Memory management | context-simple, context-persistent |
| **Hook** | Lifecycle observers (code-decided) | logging, redaction, approval |

**Orchestrator: The Main Engine** - The orchestrator controls the entire execution loop (LLM → tool calls → response). Swapping orchestrators can radically change agent behavior. It's THE control surface, not just "strategy."

**Tool vs Hook** - Tools are LLM-decided (model chooses to call them). Hooks are code-decided (fire on lifecycle events). Both can use models internally, but the triggering mechanism differs.

### Bundles
Composable configuration packages combining:
- Providers, tools, orchestrators
- Behaviors (reusable capability sets - naming convention, not code)
- Agents (specialized personas)
- Context files

### Agents (Built on Bundles, NOT a Module Type)

**Agents ARE bundles.** They use the same file format (markdown + YAML frontmatter) and are loaded via `load_bundle()`. The only difference is frontmatter convention:
- Bundles use `bundle:` with `name` and `version`
- Agents use `meta:` with `name` and `description`

When the `task` tool spawns an agent:
1. Looks up agent config from `coordinator.config["agents"]`
2. Calls the `session.spawn` capability (app-layer, not kernel)
3. Creates a new `AmplifierSession` with merged config and `parent_id` linking
4. Child session runs its own orchestrator loop and returns result

This is a **foundation-layer pattern**. The kernel provides session forking; "agents" are built on top.

### Recipes (requires recipes bundle)
Multi-step AI agent orchestration for repeatable workflows:
- Declarative YAML workflow definitions
- Context accumulation across agent handoffs
- Approval gates for human-in-loop checkpoints
- Resumability after interruption

## Ecosystem Activity Report

**Want to know what's been happening across the Amplifier ecosystem?** Use the ecosystem activity report recipe:

**In a session (recommended):**
```
"run the ecosystem-activity-report recipe"
"show me all ecosystem activity since yesterday"
"what has robotdad been working on this week?"
```

**From CLI:**
```bash
# Your activity today (default)
amplifier tool invoke recipes operation=execute \
  recipe_path=amplifier:recipes/ecosystem-activity-report.yaml

# All ecosystem activity since yesterday
amplifier tool invoke recipes operation=execute \
  recipe_path=amplifier:recipes/ecosystem-activity-report.yaml \
  context='{"activity_scope": "all", "date_range": "since yesterday"}'

# Specific user's activity last week
amplifier tool invoke recipes operation=execute \
  recipe_path=amplifier:recipes/ecosystem-activity-report.yaml \
  context='{"activity_scope": "robotdad", "date_range": "last week"}'
```

This recipe automatically:
- Discovers all repos from MODULES.md
- Filters to repos with activity in the date range
- Analyzes commits and PRs across the ecosystem
- Generates a comprehensive markdown report

For full recipe options, read `amplifier:recipes/ecosystem-activity-report.yaml`.

## The Philosophy

### Mechanism, Not Policy
The kernel provides capabilities; modules decide behavior.

**Litmus test**: "Could two teams want different behavior?" → If yes, it's policy → Module, not kernel.

### Bricks & Studs (LEGO Model)
- Each module is a self-contained "brick"
- Interfaces are "studs" where bricks connect
- Regenerate any brick independently
- Stable interfaces enable composition

### Ruthless Simplicity
- As simple as possible, but no simpler
- Every abstraction must justify its existence
- Start minimal, grow as needed
- Don't build for hypothetical futures

### Event-First Observability
- If it's important, emit an event
- Single JSONL log as source of truth
- Hooks observe without blocking
- Tracing IDs enable correlation

## Getting Started Paths

### For Users
1. Start with `amplifier:docs/USER_ONBOARDING.md` (quick start and commands)
2. Choose a bundle from foundation
3. Run `amplifier run` with your chosen configuration

### For App Developers
1. Study `foundation:examples/` for working patterns
2. Read `foundation:docs/BUNDLE_GUIDE.md` for bundle composition
3. Build your app using bundle primitives

### For Module Developers
1. Understand kernel contracts via `core:docs/`
2. Follow module protocols
3. Test modules in isolation before integration

### For Contributors
1. Read `amplifier:docs/REPOSITORY_RULES.md` for governance
2. Understand the dependency hierarchy
3. Contribute to the appropriate repository

## Deep Dives (Delegate to Specialists)

For detailed information, delegate to the appropriate expert agent:

| Topic | Delegate To | Has Access To |
|-------|-------------|---------------|
| Ecosystem modules, repos, governance | `amplifier:amplifier-expert` | MODULES.md, REPOSITORY_RULES.md, USER_ONBOARDING.md |
| Bundle authoring, patterns, examples | `foundation:foundation-expert` | BUNDLE_GUIDE.md, examples/, PATTERNS.md |
| Kernel internals, module protocols | `core:core-expert` | kernel contracts, HOOKS_API.md, specs/ |
| Recipe authoring, validation | `recipes:recipe-author` | RECIPE_SCHEMA.md, example recipes |

These agents have the heavy documentation @mentioned directly and can provide authoritative answers.
