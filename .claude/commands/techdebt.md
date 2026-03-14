---
description: "Scan for technical debt: dead code, duplication, complexity hotspots, outdated patterns. Use for periodic codebase hygiene or before major refactors."
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

Launch **2 agents in parallel** (single message, two Task calls):

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

### Step 3: Synthesize Report

Merge results from both agents, deduplicate, and sort by severity:

```markdown
# Tech Debt Report — <target>

## Critical (blocks quality)
- `file:line` — [category] Description. Fix: suggestion

## High (should fix soon)
- `file:line` — [category] Description. Fix: suggestion

## Medium (improve when touching)
- `file:line` — [category] Description

## Metrics
| Metric | Count |
|--------|-------|
| Files scanned | N |
| Issues found | N |
| Critical | X |
| High | Y |
| Medium | Z |
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
- `modular-builder` — Auto-fix (write, only with --fix)
