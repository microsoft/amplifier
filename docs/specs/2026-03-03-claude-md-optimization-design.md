# CLAUDE.md Optimization Design Spec

**Date:** 2026-03-03
**Status:** Approved
**Author:** Claude (validated design)

---

## Problem

The always-loaded instruction set across `C:\claude\CLAUDE.md`, `amplifier/CLAUDE.md`, and `amplifier/AGENTS.md` totals 1,110 lines and consumes a significant portion of every session's context window before any user work begins. The current content has three compounding problems:

1. **Stale sections occupy permanent context.** The "Cowork Identity" section in `amplifier/CLAUDE.md` and the "On-Demand MCP" section in `AGENTS.md` describe infrastructure that is no longer active. These consume ~40 lines of context every session.

2. **Code style is always-loaded despite being lookup content.** Guidelines for Python formatting, Ruff configuration, file organization, dev environment, and external library documentation belong in on-demand reference docs, not in the always-loaded layer. They total ~120 lines that are relevant only when writing code.

3. **Memory and documentation tools are not documented.** The `/recall` command, `/docs` search, the doc registry, and episodic memory (MCP plugin) exist but are absent from the instruction set. Agents cannot use tools they do not know about.

The net effect: a 1,110-line always-loaded layer with ~45% overhead from stale, misplaced, or undocumented content.

---

## Goal

Reduce the always-loaded instruction layer from 1,110 lines to approximately 395 lines — a 64% reduction — while adding explicit documentation of the memory and documentation tools that agents use to retrieve on-demand context.

Secondary goals:
- Eliminate all stale sections.
- Move code style guidance to an on-demand doc retrievable via `/docs search code style`.
- Preserve every piece of critical guidance; nothing is deleted, only relocated or condensed.

---

## Changes

### Summary

| File | Before | After | Delta |
|------|--------|-------|-------|
| `C:\claude\CLAUDE.md` | 237 lines | ~10 lines | -96% |
| `C:\claude\amplifier\CLAUDE.md` | 251 lines | ~110 lines | -56% |
| `C:\claude\amplifier\AGENTS.md` | 622 lines | ~275 lines | -56% |
| `C:\claude\amplifier\docs\guides\code-style.md` | — (new) | ~100 lines | +100 lines |
| **Total always-loaded** | **1,110 lines** | **~395 lines** | **-64%** |

---

### Change 1: New `C:\claude\CLAUDE.md` (~10 lines)

**Action:** Replace entirely.

The global CLAUDE.md becomes a safety-only redirect. It contains no workflow guidance; all context is loaded through Amplifier.

**Required content (exact, verbatim):**

```markdown
# CLAUDE.md — Global Safety Rules

- All files and folders MUST be created under `C:\claude\` only.
  Enforced by PreToolUse hook: `C:\claude\scripts\guard-paths.sh`.
- NEVER create Windows reserved device names as files:
  `nul`, `con`, `prn`, `aux`, `com1`–`com9`, `lpt1`–`lpt9`.
  These corrupt NTFS and can make the system unbootable.
- In Git Bash, use `> /dev/null` for null redirection — NEVER `> nul`.
- For full tools, agents, and workflow context: `cd C:\claude\amplifier && claude`.
```

**Removed from current file:** Workspace structure, directory layout tables, key locations, Amplifier feature list, common commands, environment info, troubleshooting section, file system protection detail, manual protection check commands, and all other content. All retained guidance moves to `amplifier/CLAUDE.md` or `amplifier/AGENTS.md`.

---

### Change 2: New `C:\claude\amplifier\CLAUDE.md` (~110 lines)

**Action:** Replace entirely with the following six sections.

#### Section 1: Identity and Environment (~15 lines)

- What Amplifier is (one sentence).
- Workspace root: `C:\claude\amplifier\`.
- Platform: Windows Server 2025, Git Bash shell.
- Path restriction: one line summary (full enforcement via `guard-paths.sh`).
- Reserved names: one line summary (full detail in `C:\claude\CLAUDE.md`).
- Python managed via UV, Node.js v24.

#### Section 2: @imports (~5 lines)

```markdown
@AGENTS.md
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md
```

No additional @imports. Design philosophy files remain on-demand only.

#### Section 3: Operating Principles (~25 lines)

Condensed from the current 80+ lines. Four rules, each 3–5 lines:

1. **Plan before implementing.** Use TodoWrite for any task with more than one step. Ultra-think when populating the list.
2. **Delegate to subagents.** Check `.claude/AGENTS_CATALOG.md` before starting. Use the Task tool. Launch agents in parallel by sending multiple Task calls in a single message.
3. **Parallel execution is the default.** Sequential tool use requires justification. Never read files one at a time when they can be read in parallel.
4. **Ask when uncertain.** If the goal is ambiguous, ask clarifying questions before writing any code.

#### Section 4: Memory and Documentation Tools (~30 lines)

This section is entirely new. It documents the retrieval layer agents use to access on-demand context.

| Tool | How to invoke | What it retrieves |
|------|--------------|-------------------|
| `/recall <query>` | Temporal: `/recall yesterday`; Topic: `/recall FuseCP exchange`; Graph: `/recall graph last week` | Native JSONL session files indexed in `~/.claude/recall-index.sqlite` (FTS5, auto-updated on session end) |
| `/docs search <terms>` | `/docs search code style`; `/docs search WinRM` | BM25 full-text search across all 16 repos' docs, keyed by doc registry |
| Doc registry | Auto-loaded at session start | Maps doc categories to file paths across all projects |
| Episodic memory | MCP plugin `mcp__plugin_episodic-memory_episodic-memory__search` | Semantic and keyword search across indexed past sessions |

**Usage rule:** Before asking the user for context, agents run a `/recall` or `/docs search` query to check if the answer is already documented.

#### Section 5: LLM-Friendly Documentation (~10 lines)

- `llms.txt` per repo: table of contents for orienting a new Claude session.
- `llms-full.txt` per repo: auto-generated concatenation of all key docs; share with Gemini/OpenCode for full project context in a single file.
- Regenerate: `bash scripts/generate-llms.sh`.
- Update `llms.txt` manually when doc structure changes; never hand-edit `llms-full.txt`.

#### Section 6: Context Strategy (~15 lines)

- Subagents fork context; use them to conserve the main session's window.
- Research agents run in **read-only mode**: Glob, Grep, Read, LS only — no Edit, Write, or Bash.
- Turn budgets are defined in `AGENTS.md` (Subagent Resilience Protocol section).
- If a needed specialized agent does not exist, stop and ask the user to create it via the `/agents` command; provide a detailed description.

#### Section 7: Amplifier Commands (~10 lines)

- Start new work with `/brainstorm`.
- Debug issues with `/debug`.
- Implement features test-first with `/tdd`.
- Available commands are listed in the system prompt's skills section.
- Check the skills section before starting any task to see if a dedicated command exists.

---

### Change 3: Revised `C:\claude\amplifier\AGENTS.md` (~275 lines)

**Action:** Edit in place. Apply trims and removals described below. No section is deleted without its content first being verified as either relocated or genuinely obsolete.

#### Sections kept as-is (no changes)

- Respect User Time (critical principle, top of file)
- Git Commit Message Guidelines
- PR-First Policy
- Git Workflow — Gitea-First
- Subagent Resilience Protocol (turn budgets table, synthesis guard, resume protocol, task decomposition)
- Red Flags table
- Response Authenticity Guidelines
- Zero-BS Principle
- Build/Test/Lint Commands
- Dependency Management

#### Sections condensed

| Section | Current lines | Target lines | Condensation rule |
|---------|--------------|-------------|-------------------|
| Sub-Agent Optimization Strategy | ~30 lines | 5 lines | Collapse to: "Always check `.claude/AGENTS_CATALOG.md` before starting. Proactively delegate. Propose new agents when a task lacks a specialist." |
| Decision Tracking System | ~20 lines | 10 lines | Keep when-to-consult and when-to-create rules. Drop format detail (link to `ai_working/decisions/README.md`). |
| Incremental Processing Pattern | ~15 lines | 10 lines | Keep the four bullet rules. Drop the closing prose. |
| Partial Failure Handling Pattern | ~15 lines | 10 lines | Keep the five bullet rules. Drop the closing prose. |
| Config Management Single Source of Truth | ~30 lines | 15 lines | Keep Principle + Implementation Guidelines + When Duplication is Acceptable. Drop Example Application section. |

#### Sections removed entirely

| Section | Reason |
|---------|--------|
| Long-Term Memory: /recall | Relocated to `amplifier/CLAUDE.md` Section 4 (Memory and Documentation Tools). |
| On-Demand MCP | Stale. Describes an experiment that is no longer the configured approach. |
| Consult DISCOVERIES.md | `DISCOVERIES.md` is unmaintained; no entries have been added in 60+ days. |
| Cowork Identity — Senior Developer | Stale. The Gemini cowork setup described is no longer active. |

#### Sections relocated

| Section | Destination |
|---------|------------|
| Code Style Guidelines | `docs/guides/code-style.md` |
| Formatting Guidelines | `docs/guides/code-style.md` |
| File Organization Guidelines | `docs/guides/code-style.md` |
| Dev Environment Tips | `docs/guides/code-style.md` |
| Service Testing After Code Changes | `docs/guides/code-style.md` |
| Documentation for External Libraries | `docs/guides/code-style.md` |

---

### Change 4: New `C:\claude\amplifier\docs\guides\code-style.md` (~100 lines)

**Action:** Create new file.

This file consolidates all code style, formatting, file organization, dev environment, service testing, and external library documentation guidance relocated from `AGENTS.md`. It is retrievable on-demand via `/docs search code style` and is not always-loaded.

**Required sections:**

1. **Python Code Style** — type hints, import organization, naming conventions, `Optional` usage, Python 3.11+ requirement, Pydantic for validation.
2. **Formatting** — 120-character line length, `ruff.toml` as authority, `# type: ignore` usage, EOF newline requirement.
3. **File Organization** — Do not add files to `/tools`. Organize into module directories. Amplifier CLI tools: consult `amplifier-cli-architect` agent.
4. **Dev Environment** — `make` to create venv, activation command for Windows (`.venv\Scripts\activate`).
5. **Service Testing After Code Changes** — Three-step sequence: run `make check`, start the service, test basic functionality, stop the service. List of common runtime errors not caught by `make check`.
6. **External Library Documentation** — DeepWiki: use `ask_question` only, not `read_wiki_contents`. Context7: first tool for general library docs.

---

## Impact

### Files Changed

| File | Action | Lines before | Lines after |
|------|--------|-------------|-------------|
| `C:\claude\CLAUDE.md` | Replace entirely | 237 | ~10 |
| `C:\claude\amplifier\CLAUDE.md` | Replace entirely | 251 | ~110 |
| `C:\claude\amplifier\AGENTS.md` | Edit in place | 622 | ~275 |
| `C:\claude\amplifier\docs\guides\code-style.md` | Create new | — | ~100 |

### What Is Preserved

Every piece of critical guidance is either kept, condensed, or relocated — nothing is permanently deleted. The relocation map:

| Content | From | To |
|---------|------|----|
| /recall documentation | AGENTS.md | amplifier/CLAUDE.md §4 |
| Code style, formatting, file org, dev env, service testing, library docs | AGENTS.md | docs/guides/code-style.md |
| Workspace structure, Amplifier features | CLAUDE.md (global) | amplifier/CLAUDE.md §1 |

### What Is Removed (Obsolete)

| Content | Reason for removal |
|---------|--------------------|
| On-Demand MCP section | Stale experiment, no longer active |
| Consult DISCOVERIES.md section | File unmaintained for 60+ days |
| Cowork Identity section | Gemini cowork setup is no longer active |
| Directory layout tables, key locations, common commands (from global CLAUDE.md) | Redundant with amplifier/CLAUDE.md; global CLAUDE.md is now safety-only |

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Research | `agentic-search` | Read all four target files; verify every cross-reference, @import path, and section cross-link is valid before any edits begin. Produce a findings report listing broken references. |
| Implementation — global CLAUDE.md | `modular-builder` | Write new 10-line `C:\claude\CLAUDE.md`. |
| Implementation — amplifier/CLAUDE.md | `modular-builder` | Write new `C:\claude\amplifier\CLAUDE.md` with all seven sections. |
| Implementation — AGENTS.md | `modular-builder` | Edit `C:\claude\amplifier\AGENTS.md` in place: condense four sections, remove four sections, verify relocated sections are removed (not duplicated). |
| Implementation — code-style.md | `modular-builder` | Create `C:\claude\amplifier\docs\guides\code-style.md` from the six relocated sections. |
| Review | `code-quality-reviewer` | Diff all four files against this spec. Verify: no critical guidance was accidentally dropped, no stale content remains, all @import paths resolve, the Memory and Documentation Tools section in CLAUDE.md is accurate. |
| Cleanup | `post-task-cleanup` | Final hygiene pass: remove any trailing whitespace, verify EOF newlines, confirm no duplicate content exists across files. |

---

## Test Plan

All acceptance criteria must pass before this work is considered complete.

### 1. Line Count Verification

- [ ] `C:\claude\CLAUDE.md` is between 8 and 12 lines.
- [ ] `C:\claude\amplifier\CLAUDE.md` is between 100 and 120 lines.
- [ ] `C:\claude\amplifier\AGENTS.md` is between 265 and 290 lines.
- [ ] `C:\claude\amplifier\docs\guides\code-style.md` is between 90 and 110 lines.

### 2. Content Preservation

- [ ] `C:\claude\amplifier\docs\guides\code-style.md` contains all six sections: Python Code Style, Formatting, File Organization, Dev Environment, Service Testing, External Library Documentation.
- [ ] `C:\claude\amplifier\CLAUDE.md` Section 4 (Memory and Documentation Tools) contains entries for `/recall`, `/docs search`, doc registry, and episodic memory MCP plugin.
- [ ] Subagent Resilience Protocol (turn budgets table, synthesis guard, resume protocol) is present and unmodified in `AGENTS.md`.
- [ ] Red Flags table is present and unmodified in `AGENTS.md`.
- [ ] Zero-BS Principle is present and unmodified in `AGENTS.md`.
- [ ] PR-First Policy is present and unmodified in `AGENTS.md`.

### 3. Stale Content Removal

- [ ] The phrase "Cowork Identity" does not appear in any always-loaded file.
- [ ] The phrase "On-Demand MCP" does not appear in any always-loaded file.
- [ ] The phrase "DISCOVERIES.md" does not appear in `AGENTS.md`.
- [ ] The phrase "Long-Term Memory: /recall" does not appear as a section heading in `AGENTS.md`.

### 4. @import Validity

- [ ] All three @import paths in `amplifier/CLAUDE.md` resolve to existing files:
  - `AGENTS.md` → `C:\claude\amplifier\AGENTS.md`
  - `ai_context/IMPLEMENTATION_PHILOSOPHY.md` → `C:\claude\amplifier\ai_context\IMPLEMENTATION_PHILOSOPHY.md`
  - `ai_context/MODULAR_DESIGN_PHILOSOPHY.md` → `C:\claude\amplifier\ai_context\MODULAR_DESIGN_PHILOSOPHY.md`

### 5. No Content Duplication

- [ ] Code style guidance appears only in `docs/guides/code-style.md`, not in `AGENTS.md`.
- [ ] `/recall` documentation appears only in `amplifier/CLAUDE.md`, not in `AGENTS.md`.
- [ ] Path restriction warning appears only in `C:\claude\CLAUDE.md` and a one-line summary in `amplifier/CLAUDE.md`; not duplicated in full in both.

### 6. Retrievability

- [ ] Running `/docs search code style` returns `docs/guides/code-style.md` as a result (verifiable once `/docs` index is updated after file creation).
