# Design Spec: Re-opened Bug Analysis Pipeline

**Date:** 2026-02-27
**Status:** Approved
**Author:** Claude Code (Senior Developer)

---

## Problem

Re-opened bugs (`ReopenedCount > 0`) in the `/fix-bugs` pipeline are currently treated the same as new bugs — they receive higher priority but go through the identical auto-fix flow. A re-opened bug means a previous fix was applied and failed: either the root cause was misdiagnosed, the fix was incomplete, or the change was overwritten. Repeating the auto-fix flow on the same bug without understanding why the previous fix failed risks applying the same incorrect fix a second time.

---

## Goal

Route re-opened bugs through a dedicated deep analysis flow consisting of:

1. **Previous-fix forensics** — determine what was fixed before and exactly why it failed
2. **Fresh root cause investigation** — trace the full code path with prior-fix context baked in
3. **Handoff to `/brainstorm`** — present findings to the user and launch collaborative solution design

Status updates flow to the bug system at every stage. The normal auto-fix pipeline for new bugs (`ReopenedCount = 0`) is unchanged.

---

## Changes

### 1. Database — New "Investigating" Status

**File:** `src/FuseCP.Database/Migrations/NNN_AddInvestigatingStatus.sql`

Add a new migration that drops and re-adds the CHECK constraint on `BugReports.Status` to include the `Investigating` value.

New constraint:

```sql
CONSTRAINT CHK_BugReports_Status CHECK (
    Status IN ('Open','InProgress','Investigating','Fixed','Verified','Closed','WontFix')
)
```

Rules:
- The migration is additive — no tables, columns, or existing rows are modified.
- The migration must apply cleanly against the existing FuseCP database schema without data loss.
- Migration filename follows the existing sequence convention (`NNN` = next available number).

---

### 2. Portal — Status Display

**File:** `src/FuseCP.Portal/Components/Pages/BugReports.razor`

Two changes:

**a. Status filter dropdown** — Add `Investigating` as a selectable filter option in the same location as existing status values (Open, InProgress, Fixed, etc.).

**b. Badge color** — Display the `Investigating` status badge in amber/orange, distinct from:
- Open → default/gray
- InProgress → blue
- Fixed → green
- Closed/WontFix → muted

Use the same Blazor badge component pattern already used for existing statuses.

---

### 3. `/fix-bugs` Command — New Routing and Analysis Phases

**File:** `.claude/commands/fix-bugs.md`

#### Phase 1 — Fetch and Route (modification to existing phase)

After fetching bugs from the API, split into three buckets and display each in its own table:

| Bucket | Condition | Display | Action |
|--------|-----------|---------|--------|
| Feature Requests | `Type = "FeatureRequest"` | Feature Requests table | Route to `/brainstorm` (unchanged) |
| Re-opened Bugs | `ReopenedCount > 0` | Re-opened Bugs table (shown before new bugs) | Route to Phase 1c–1e (new) |
| New Bugs | `ReopenedCount = 0` | New Bugs table | Normal auto-fix pipeline (unchanged) |

When the user selects a re-opened bug, execute immediately before Phase 1c:

```powershell
set-bug-status.ps1 -BugId {id} -Status Investigating
add-bug-comment.ps1 -BugId {id} -SystemNote -Comment "Re-opened bug picked up for deep analysis (reopened {N} times)"
```

---

#### Phase 1c — Previous-Fix Forensics (new)

**Objective:** Determine why the prior fix failed.

Steps:

1. Fetch full bug detail and comment history via `read-bug.ps1 -BugId {id}`.
2. Dispatch `agentic-search` agent (model: sonnet, `max_turns=15`) with the following READ-ONLY mandate:
   - Locate the PR or commit referenced in any "Fixed" or "fix applied" comment.
   - Read the diff of that PR/commit.
   - Trace the changed code path to verify whether the fix is still present, reverted, or overwritten.
   - Determine the failure mode from this list:
     - Wrong root cause diagnosed
     - Fix incomplete (partial coverage)
     - Fix overwritten by a subsequent merge
     - Environment or configuration issue
     - Race condition or timing issue
     - Other (agent states reason)
3. After agent returns, post result to bug system:
   ```powershell
   add-bug-comment.ps1 -BugId {id} -SystemNote -Comment "Previous fix analysis: {failure mode and detail}"
   ```

---

#### Phase 1d — Fresh Investigation (new)

**Objective:** Produce a new root cause analysis starting from scratch but informed by forensics.

Steps:

1. Dispatch `agentic-search` agent (model: sonnet, `max_turns=20`) with forensics output baked into the prompt context. Agent instructions:
   - Prior fix and its failure mode are known — do not repeat that investigation.
   - Trace the full relevant code path top to bottom as if investigating fresh.
   - Identify the actual root cause, affected files, and entry points.
   - Assess implementation complexity using exactly one of these labels:
     - `Simple` — single-file change, low risk, auto-fix suitable
     - `Needs design` — multi-file or behavioral change, requires solution design
     - `Architectural` — cross-cutting concern, requires architectural decision
2. If bug has attached screenshots, run visual investigation using the existing Phase 3b visual comparison logic.
3. After agent returns, post result:
   ```powershell
   add-bug-comment.ps1 -BugId {id} -SystemNote -Comment "Fresh analysis complete. Root cause: {findings}. Complexity: {label}."
   ```

---

#### Phase 1e — Compile and Brainstorm Handoff (new)

**Objective:** Present full analysis to user and hand off to `/brainstorm`.

Steps:

1. Display analysis summary to user in a structured block:
   - Bug title, ID, reopened count
   - Previous fix summary and failure mode (from Phase 1c)
   - Fresh root cause and affected files (from Phase 1d)
   - Complexity assessment
   - Visual comparison output (if applicable)

2. **STOP** — wait for explicit user confirmation to proceed.

3. On confirmation, post to bug system:
   ```powershell
   add-bug-comment.ps1 -BugId {id} -SystemNote -Comment "Analysis complete. Escalated to brainstorm for solution design."
   ```

4. Launch `/brainstorm` with the full compiled context (bug details + forensics + fresh investigation + complexity assessment) as the initial prompt.

5. Pipeline stops for this bug. `/brainstorm` takes over solution design. The bug remains in `Investigating` status until a fix is eventually deployed and Phase 7f sets it to `Fixed`.

---

### 4. No Changes To

- Phases 2–8 of the normal bug auto-fix pipeline
- Error handling and priority handling logic
- PowerShell scripts (`set-bug-status.ps1`, `add-bug-comment.ps1`, `read-bug.ps1`) — they already accept any valid status string
- CI and deploy flow

---

## Impact

| Area | Scope |
|------|-------|
| Database | 1 migration file — additive CHECK constraint change only |
| Portal | Minor — 1 filter option added, 1 badge color added |
| Command | `fix-bugs.md` gains approximately 150–200 lines (new phases) |
| Scripts | No changes |
| Risk | Low — re-opened bugs are uncommon; normal bug flow is untouched |

---

## Files Changed

| File | Change |
|------|--------|
| `src/FuseCP.Database/Migrations/NNN_AddInvestigatingStatus.sql` | New migration — add `Investigating` to CHECK constraint on `BugReports.Status` |
| `src/FuseCP.Portal/Components/Pages/BugReports.razor` | Add `Investigating` to status filter dropdown; add amber/orange badge color |
| `.claude/commands/fix-bugs.md` | Add Phase 1 bucket routing; add Phase 1c (forensics), 1d (fresh investigation), 1e (brainstorm handoff) |

---

## Agent Allocation

| Phase | Agent | Model | max_turns | Responsibility |
|-------|-------|-------|-----------|---------------|
| Schema change + portal | `modular-builder` | sonnet | 15 | Write SQL migration; update BugReports.razor |
| Command rewrite | `modular-builder` | sonnet | 20 | Modify fix-bugs.md with new routing and phases 1c/1d/1e |
| Forensics investigation | `agentic-search` | sonnet | 15 | Analyze previous fix at runtime (READ-ONLY) |
| Fresh investigation | `agentic-search` | sonnet | 20 | New root cause analysis at runtime (READ-ONLY) |
| PR review | `pr-review-toolkit:code-reviewer` | — | — | Review the implementation PR before merge |

---

## Test Plan

All items below are acceptance criteria. Each must pass before the PR is merged.

1. **Migration applies cleanly** — Run `NNN_AddInvestigatingStatus.sql` against the existing `FuseCPLab` database on `(local)\SQLEXPRESS`. Verify no errors, no data loss, and the constraint now accepts `Investigating` while still rejecting invalid values.

2. **API accepts Investigating status** — Call `set-bug-status.ps1 -BugId {any valid id} -Status Investigating`. Verify the API returns HTTP 200 and the database row reflects the new status.

3. **Portal badge renders correctly** — Navigate to the Bug Reports page in the portal. Filter by `Investigating`. Verify the amber/orange badge appears and the filter returns only bugs with that status.

4. **Re-opened routing in /fix-bugs** — Create a bug, apply a fix (marking it Fixed), then reopen it. Run `/fix-bugs`. Verify:
   - The bug appears in the Re-opened Bugs table, not the New Bugs table.
   - Selecting it sets status to `Investigating` and posts the system note.
   - Phases 1c and 1d execute and post their respective system notes to the bug.
   - Phase 1e presents the analysis summary and stops for user confirmation.
   - After confirmation, `/brainstorm` launches with compiled context.

5. **Normal bugs unaffected** — Create a new bug with `ReopenedCount = 0`. Run `/fix-bugs`. Verify it appears in the New Bugs table and proceeds through the normal auto-fix pipeline (Phases 2–8) without triggering any analysis phases.

6. **Feature request routing unchanged** — Create a bug with `Type = FeatureRequest`. Run `/fix-bugs`. Verify it routes to `/brainstorm` as before, with no interaction with the new analysis phases.
