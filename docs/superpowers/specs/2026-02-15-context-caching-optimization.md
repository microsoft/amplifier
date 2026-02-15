# Context Caching Optimization (Gold Prefix) Design Spec

## Overview
Optimize Gemini 3 context caching in OpenCode by implementing a "Gold Prefix" strategy. This involves restructuring prompts to isolate static content from dynamic variables, ensuring bit-for-bit stability for the first 100k+ tokens to maximize "Cache Read" operations and minimize TPM limit hits.

## Goals
- Maximize Gemini context caching hits (>80% of prompt).
- Reduce TPM (Tokens Per Minute) pressure by reusing cached codebase context.
- Ensure subagents benefit from the same cache as the controller.
- Prevent daily cache invalidation caused by "Today's Date" at the top of the prompt.

## Architecture

### 1. The "Gold Prefix" Structure
The prompt will be divided into two zones:

**Frozen Zone (Static Prefix - 100k+ tokens):**
- Core Mandates and Identity
- `AMPLIFIER-AGENTS.md` (Full Manifest)
- Core Skills (Brainstorming, TDD, Writing Plans, Subagent Development)
- Project Constitution (`CLAUDE.md`)
- High-level Architecture Docs

**Churn Zone (Dynamic Suffix):**
- `Today's Date`
- `Working Directory`
- `Git Status` (Branch, Untracked files)
- Environment Variables
- Tool Outputs

### 2. Subagent Mirroring
The `Task` tool in the Superpowers bridge will be refactored:
- **Mirroring:** Instead of a minimal prompt, subagents will receive the same "Frozen Zone" as the controller.
- **Specialization:** The subagent's specific instructions (e.g., "You are the modular-builder...") will be appended *after* the Frozen Zone.
- **Benefit:** Subagents will start with a warm cache, leading to near-instant responses and 0 additional TPM usage for the codebase context.

### 3. Cache-Aware Compaction
Refactor `amplifier/.claude/tools/hook_precompact.py`:
- **Anchor:** The Frozen Zone is never summarized.
- **Snapshotting:** Only the "Middle History" (turns 3 to N-5) is summarized into a stable "Progress Snapshot" block.
- **Stability:** Ensure the summary block doesn't change frequently (only updates when compaction is triggered).

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Architecture | zen-architect | Design prompt sequence and hook integration points. |
| Hook Implementation | amplifier-cli-architect | Refactor `hook_precompact.py` for stable prefixes. |
| Bridge Implementation | modular-builder | Modify Superpowers `Task` tool for Subagent Mirroring. |
| Profiling | performance-optimizer | Monitor `opencode stats` to verify cache hits. |
| Cleanup | post-task-cleanup | Final hygiene pass. |

## Success Criteria
- `opencode stats` shows "Cache Read" tokens significantly exceeding "Input" tokens for multi-turn sessions.
- Subagent turns show >90% cache hits.
- TPM limit errors are reduced during heavy development sessions.
