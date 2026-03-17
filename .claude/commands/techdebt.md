---
description: "Scan for technical debt: dead code, duplication, complexity, outdated patterns, shallow modules."
---

# Technical Debt Scanner

## Overview

Proactively hunt for accumulated technical debt across a target scope. Produces a severity-ranked report with file:line references and optional auto-fix for easy wins.

**Announce at start:** "Running tech debt scan on <target>."

## Usage

```
/techdebt [target] [--fix]
```

- No arguments: scan files changed on current branch vs main
- Directory: `/techdebt src/` — scan all files in directory
- File: `/techdebt src/utils.py` — scan specific file
- `--fix`: auto-fix high-priority, low-risk items after scan

## The Process

### Step 1: Determine Scan Scope

Parse `$ARGUMENTS` to determine target:

- **No arguments:** Get changed files from current branch vs main:
  ```bash
  git diff --name-only main...HEAD
  ```
  If on main with uncommitted changes, use:
  ```bash
  git diff --name-only HEAD
  ```
- **Directory/file argument:** Use as-is, strip any `--fix` flag

If scope exceeds 30 files, warn the user and suggest narrowing.

### Step 2: Dispatch Parallel Scans

Launch **3 agents in parallel** (single message, three Task calls):

#### Agent 1: Structural Debt Scanner

```
Task(subagent_type="agentic-search", model="haiku", max_turns=10)

**READ-ONLY MODE: Use ONLY Read, Glob, Grep, LS tools. Do NOT use Edit, Write, Bash.**

Scan these files for STRUCTURAL technical debt:
[file list]

Look for:
1. **Dead code**: Unused imports, unreferenced functions/classes, commented-out code blocks
2. **Duplication**: Functions with near-identical logic, copy-pasted blocks (search for similar function signatures and bodies)
3. **Orphaned files**: Files not imported by anything else
4. **Missing test coverage**: Public functions/classes with no corresponding test
5. **Stale TODOs**: TODO/FIXME/HACK comments older than the current branch

For each finding, report:
- Category (dead-code | duplication | orphaned | untested | stale-todo)
- File path and line number
- Severity (critical | high | medium)
- One-line description
- Whether it's safe to auto-fix (yes/no)

Return findings as a structured list. Max 30 findings, prioritized by severity.
```

#### Agent 2: Code Quality Scanner

```
Task(subagent_type="code-quality-reviewer", model="sonnet", max_turns=10)

Scan these files for CODE-LEVEL technical debt (NOT a diff review — scan the full files):
[file list]

Look for:
1. **Complexity hotspots**: Functions >50 lines, nesting >3 levels, cyclomatic complexity
2. **Outdated patterns**: Old-style string formatting, typing.List instead of list, deprecated APIs
3. **Magic numbers**: Hardcoded values that should be named constants
4. **Missing type hints**: Public functions without parameter or return type annotations
5. **Code smells**: God functions (too many responsibilities), excessive parameters (>5), long parameter lists

For each finding, report:
- Category (complexity | outdated-pattern | magic-number | missing-types | code-smell)
- File path and line number
- Severity (critical | high | medium)
- One-line description
- Suggested fix (brief)
- Whether it's safe to auto-fix (yes/no)

Return findings as a structured list. Max 30 findings, prioritized by severity.
```

#### Agent 3: Module Depth Scanner

**Graph-enhanced depth analysis:** If `code-review-graph` MCP is available, use `mcp__code-review-graph__query_graph_tool` to get precise dependency counts per module. A module with high fan-in (many dependents) but low fan-out (few dependencies) is deep and healthy. A module with high fan-out is potentially shallow. The graph provides exact edge counts instead of grep-based estimates.

```
Task(subagent_type="agentic-search", model="sonnet", max_turns=12)

**READ-ONLY MODE: Use ONLY Read, Glob, Grep, LS tools. Do NOT use Edit, Write, Bash.**

Scan these files for MODULE DEPTH issues that confuse AI agents and reduce code quality.
Based on Ousterhout's "deep vs shallow modules" concept.
[file list]

Look for:
1. **Scattered concepts** — A single concept (e.g., "authentication") split across 5+ small files under 50 lines each. Agents lose context jumping between files.
2. **Shallow modules** — Large public interfaces with thin implementations. Signs: more exported functions/types than internal ones, most functions under 10 lines, module is mostly re-exports or thin wrappers.
3. **Testability-driven extraction anti-pattern** — Pure functions extracted solely for testability, creating many small files that hide integration bugs.
4. **Tight coupling clusters** — Modules that can't be understood independently. Signs: circular imports, shared mutable state, functions reaching into other modules' internals, changes rippling across 2+ modules.
5. **Agent confusion signals** — Files over 500 lines, deep nesting (4+ levels), mixed concerns (UI + business logic + data access), inconsistent naming for the same concept.

For each finding, report:
- Category (scattered-concept | shallow-module | testability-extraction | tight-coupling | agent-confusion)
- File path and line number
- Depth score: shallow / medium / deep
- One-line description of the problem
- Impact on agents: how this hurts AI-generated code quality
- Recommendation: deepen by combining modules, or split into focused modules

Return findings as a structured list. Max 20 findings, prioritized by severity.
```

### Step 3: Synthesize Report

Merge results from all three agents, deduplicate, and sort by severity:

```markdown
# Tech Debt Report — <target>

## Critical (blocks quality)
- `file:line` — [category] Description. Fix: suggestion

## High (should fix soon)
- `file:line` — [category] Description. Fix: suggestion

## Medium (improve when touching)
- `file:line` — [category] Description

## Module Depth (agent-friendliness)

#### [Module/File Path]
- **Depth score**: shallow / medium / deep
- **Problem**: [specific issue]
- **Impact on agents**: [how this hurts AI-generated code quality]
- **Recommendation**: [deepen by combining X+Y, or split Z into focused modules]

## Metrics
| Metric | Count |
|--------|-------|
| Files scanned | N |
| Issues found | N |
| Critical | X |
| High | Y |
| Medium | Z |
| Shallow modules | N |
| Auto-fixable | N |
```

### Step 4: Auto-Fix (if --fix flag)

If `--fix` was passed and auto-fixable items exist:

1. Show the list of items that will be auto-fixed
2. Ask for confirmation: "Fix these N items? (y/n)"
3. On confirmation, dispatch `modular-builder` agent:

```
Task(subagent_type="modular-builder", model="sonnet", max_turns=15)

Fix these technical debt items. Make minimal, targeted changes only:
[list of auto-fixable items with file:line references]

Rules:
- Only fix items explicitly listed — no drive-by improvements
- Run linter after changes (ruff check / ruff format for Python)
- Preserve all existing behavior
- One logical change per file
```

4. After fixes, re-run the scan on fixed files to verify issues resolved

### Step 5: Summary

End with actionable next steps:

```
Scan complete. N issues found (X auto-fixed).

Remaining items by priority:
- Critical: X items — fix before next PR
- High: Y items — fix this sprint
- Medium: Z items — fix when touching these files
```

## Arguments

`$ARGUMENTS`

## Integration

**Pairs with:**
- `/finish-branch` — Run before finishing to catch debt before PR
- `/review-changes` — Deeper philosophy-aligned review
- `/create-plan` — Plan a debt reduction sprint from the report

**Agents used:**
- `agentic-search` — Structural scanning (read-only)
- `code-quality-reviewer` — Code-level scanning (read-only)
- `agentic-search` (sonnet) — Module depth / agent-friendliness scanning (read-only)
- `modular-builder` — Auto-fix (write, only with --fix)
