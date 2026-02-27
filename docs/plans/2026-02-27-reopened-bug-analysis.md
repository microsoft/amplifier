# Re-opened Bug Analysis Pipeline — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route re-opened bugs (ReopenedCount > 0) through a deep analysis flow (forensics + fresh investigation) that hands off to /brainstorm, instead of the auto-fix pipeline.

**Architecture:** Three changes — one SQL migration adding "Investigating" status, portal badge/filter updates, and a rewrite of fix-bugs.md Phase 1 with three new sub-phases (1c/1d/1e). Normal bug flow is untouched.

**Tech Stack:** SQL Server (migration), Blazor Server (portal), Markdown (command file)

**Spec:** `docs/specs/2026-02-27-reopened-bug-analysis-design.md`

---

## Chunk 1: Database and Portal

### Task 1: Add "Investigating" status to database

**Agent:** modular-builder
**Model:** haiku

**Files:**
- Create: `src/FuseCP.Database/Migrations/113_AddInvestigatingStatus.sql`

The existing CHECK constraint is `CK_BugReports_Status` defined in `src/FuseCP.Database/Migrations/111_EnhanceBugReportSystem.sql:66-67`. Current valid values: `('Open', 'InProgress', 'Fixed', 'Closed', 'WontFix', 'Verified')`. The latest migration file is `112_AddBugReopenTracking.sql`, so this is `113`.

- [ ] **Step 1: Write the migration file**

```sql
-- 113_AddInvestigatingStatus.sql
-- Add 'Investigating' to allowed bug statuses for re-opened bug analysis flow

-- Drop existing constraint
ALTER TABLE BugReports DROP CONSTRAINT CK_BugReports_Status;

-- Re-add with Investigating included
ALTER TABLE BugReports ADD CONSTRAINT CK_BugReports_Status
    CHECK (Status IN ('Open', 'InProgress', 'Investigating', 'Fixed', 'Verified', 'Closed', 'WontFix'));
```

- [ ] **Step 2: Run the migration against the database**

```bash
powershell -Command "Invoke-Sqlcmd -ServerInstance '(local)\SQLEXPRESS' -Database 'FuseCPLab' -InputFile 'C:\claude\fusecp-enterprise\src\FuseCP.Database\Migrations\113_AddInvestigatingStatus.sql'"
```

Expected: No errors.

- [ ] **Step 3: Verify the constraint accepts "Investigating"**

Write and run a quick verification script:

```bash
powershell -Command "Invoke-Sqlcmd -ServerInstance '(local)\SQLEXPRESS' -Database 'FuseCPLab' -Query \"SELECT OBJECT_DEFINITION(OBJECT_ID('CK_BugReports_Status'))\""
```

Expected: Output contains `'Investigating'` in the constraint definition.

- [ ] **Step 4: Verify the API accepts the new status**

```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId 1 -Status Investigating
```

Expected: HTTP 200 (or if bug ID 1 doesn't exist, use any valid open bug ID). Then set it back:

```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId 1 -Status Open
```

- [ ] **Step 5: Commit**

```bash
cd /c/claude/fusecp-enterprise && git add src/FuseCP.Database/Migrations/113_AddInvestigatingStatus.sql && git commit -m "$(cat <<'EOF'
feat: add Investigating status for re-opened bug analysis

Adds 'Investigating' to the CK_BugReports_Status CHECK constraint.
Used by the fix-bugs pipeline when a re-opened bug enters deep analysis.

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
EOF
)"
```

---

### Task 2: Add "Investigating" to portal status filter and badge

**Agent:** modular-builder
**Model:** haiku

**Files:**
- Modify: `src/FuseCP.Portal/Components/Pages/Admin/BugReports.razor`

Key locations in `BugReports.razor`:
- **Filter dropdown**: lines 51-56 (6 `<option>` elements for Open, InProgress, Fixed, Verified, Closed, WontFix)
- **Modal edit dropdown**: lines 328-332 (5 options — Open, InProgress, Fixed, Closed, WontFix; no Verified)
- **Badge color method**: lines 1309-1316 (`GetStatusBadgeClass` method with switch on status string)
- **ReopenedCount display**: lines 168-170 (already shows `REOPENED(N)` badge in warning color)

- [ ] **Step 1: Read the current file to confirm line numbers**

```
Read(file_path="C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Admin\BugReports.razor", offset=48, limit=12)
```

Verify the filter dropdown options are at lines 51-56.

- [ ] **Step 2: Add "Investigating" to the filter dropdown**

Add `<option value="Investigating">@T["bugs.status.investigating"]</option>` after the `InProgress` option (line 53). If there's no translation key yet, use the same pattern as existing keys — check what `@T["bugs.status.inprogress"]` looks like and follow the pattern.

- [ ] **Step 3: Add "Investigating" to the modal edit dropdown (if appropriate)**

Read lines 325-335 to see the modal dropdown. Add `Investigating` as an option there too — admins may want to manually set a bug to Investigating.

- [ ] **Step 4: Add badge color for "Investigating"**

Read lines 1305-1320 to see the `GetStatusBadgeClass` method. Add a case for `"Investigating"`. Use an amber/orange color that's distinct from existing statuses:

```csharp
"Investigating" => "bg-warning text-warning-emphasis",
```

This uses the warning palette (amber/orange) but with the solid `bg-warning` variant instead of the muted `bg-warning-muted` already used by InProgress, making them visually distinct.

- [ ] **Step 5: Build to verify no errors**

```bash
cd /c/claude/fusecp-enterprise && dotnet build --no-incremental 2>&1 | tail -5
```

Expected: Build succeeded.

- [ ] **Step 6: Commit**

```bash
cd /c/claude/fusecp-enterprise && git add src/FuseCP.Portal/Components/Pages/Admin/BugReports.razor && git commit -m "$(cat <<'EOF'
feat: add Investigating status to portal bug reports page

Adds Investigating to filter dropdown, modal edit dropdown, and
badge color (amber/orange). Supports the re-opened bug analysis flow.

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
EOF
)"
```

---

## Chunk 2: Command File Rewrite

### Task 3: Modify fix-bugs.md Phase 1 routing for re-opened bugs

**Agent:** modular-builder
**Model:** sonnet

**Files:**
- Modify: `.claude/commands/fix-bugs.md`

This is the largest task. The fix-bugs.md file is 757 lines. We modify Phase 1 (lines ~66-100) and insert three new phases (1c, 1d, 1e) between Phase 1b (line 166) and Phase 2 (line 168).

**Current Phase 1 flow (lines 66-100):**
1. Separate Feature Requests from Bugs (line 68)
2. Display Feature Requests with note "use /brainstorm" (lines 70-78)
3. Display Bugs sorted by priority, re-opened first (lines 82-93)
4. Note about re-opened bugs requiring extra scrutiny (line 96)
5. Feature request routing to /brainstorm (line 98)

**New Phase 1 flow:**
1. Separate into THREE buckets: Feature Requests, Re-opened Bugs, New Bugs
2. Display Feature Requests (unchanged)
3. Display Re-opened Bugs in separate table with note about analysis flow
4. Display New Bugs (unchanged)
5. On re-opened bug selection: set Investigating + system comment, proceed to 1c
6. On new bug selection: proceed to Phase 1b/2 as before

- [ ] **Step 1: Read the full Phase 1 section**

```
Read(file_path="C:\claude\amplifier\.claude\commands\fix-bugs.md", offset=59, limit=110)
```

Understand the exact structure of lines 59-168 (Phase 1 through Phase 1b).

- [ ] **Step 2: Rewrite Phase 1 — three-bucket routing**

Replace lines 66-100 (the current bug/feature separation and display) with the new three-bucket logic:

```markdown
**Separate by Type:** Split results into three buckets:
1. **Feature Requests** (Type=`FeatureRequest`)
2. **Re-opened Bugs** (Type=`Bug` or missing/null, AND `ReopenedCount > 0`)
3. **New Bugs** (Type=`Bug` or missing/null, AND `ReopenedCount = 0`)

**If Feature Requests exist, present them first:**
```
Found M feature request(s):

| # | ID | Priority | Area | Title | Reported |
|---|-----|----------|------|-------|----------|
| 1 | 45  | Medium   | Portal | Add bulk user import | 2026-02-18 |

Feature requests are NOT auto-fixed. Use /brainstorm to discuss them.
```

**If Re-opened Bugs exist, present them next:**
```
Found R re-opened bug(s) (previous fix failed — requires deep analysis):

| # | ID | Priority | Area | Title | Last Reopened | Times |
|---|-----|----------|------|-------|---------------|-------|
| 1 | 42  | High     | Portal | Login page crashes | 2026-02-25 | 2 |

Re-opened bugs go through analysis → /brainstorm (not auto-fix).
```

**Then present New Bugs:**

**Sort new bugs by priority:** Critical > High > Medium > Low, then by ReportedAt (oldest first within same priority).

```
Found N new bug(s):

| # | ID | Priority | Area | Title | Reported |
|---|-----|----------|------|-------|----------|
| 1 | 38  | High     | Exchange | Mailbox creation fails silently | 2026-02-14 |

Working on #1 (highest priority). Say "skip" to pick a different one, or "brainstorm #45" to discuss a feature request.
```

**Re-opened bug selection:** When the user selects a re-opened bug (or one is auto-selected as highest priority), immediately:

```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId {id} -Status Investigating
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/add-bug-comment.ps1" -BugId {id} -SystemNote -Comment "Re-opened bug picked up for deep analysis (reopened {N} times)"
```

Then proceed to **Phase 1c** (below).

**New bug selection:** Proceed to Phase 1b (triage, if 2+ new bugs) or Phase 2 (if 1 new bug) — unchanged.

**Feature Request routing:** If the user says "brainstorm #ID" for a feature request, stop the fix pipeline and invoke `/brainstorm` with the feature request details as context. Do NOT attempt to implement feature requests automatically.

**If only Feature Requests remain (no bugs of either type):** Report "No open bugs found. There are M feature request(s) — use /brainstorm to discuss them." and stop.

**If only Re-opened Bugs remain (no new bugs):** Process re-opened bugs through analysis flow. Do NOT report "no bugs."

**If only New Bugs remain (no re-opened):** Process new bugs through normal pipeline (unchanged).
```

- [ ] **Step 3: Insert Phase 1c — Previous-Fix Forensics**

Insert after Phase 1b (after line ~166, before Phase 2). This phase ONLY runs for re-opened bugs.

```markdown
## Phase 1c: Previous-Fix Forensics (Re-opened Bugs Only)

**Skip this phase for new bugs** — proceed directly to Phase 2.

This phase determines why the prior fix failed. The previous fix description is in the bug's comments (added by Phase 7f of the prior pipeline run). Format: `**Fix:** {description}. PR #{pr-number} ({branch-name}).`

**Step 1: Fetch full bug details and comments:**
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/read-bug.ps1" -BugId {id} -ExtractScreenshot
```

Parse the output for the fix comment. Look for comments with `IsSystemNote=true` that contain `**Fix:**`.

**Step 2: Dispatch forensics agent:**

```
Task(subagent_type="agentic-search", model="sonnet", max_turns=15, description="Forensics on previous fix for bug #{id}", prompt="
  **READ-ONLY MODE: Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files.**

  A previous fix for this FuseCP bug FAILED. Analyze why.

  ## Bug
  - Title: {title}
  - Description: {description}
  - Area: {area}
  - Page URL: {pageUrl}

  ## Previous Fix (from bug comments)
  {paste the **Fix:** comment text verbatim}

  ## Instructions
  1. Find the PR branch or commit mentioned in the fix comment:
     ```bash
     cd /c/claude/fusecp-enterprise && git log --oneline --all --grep='Bug #{id}' | head -10
     ```
     Or search for the branch name from the comment:
     ```bash
     cd /c/claude/fusecp-enterprise && git log --oneline --all | grep '{branch-name}' | head -5
     ```
  2. Read the diff of the relevant commit(s):
     ```bash
     cd /c/claude/fusecp-enterprise && git show {commit-hash} --stat
     cd /c/claude/fusecp-enterprise && git show {commit-hash}
     ```
  3. Trace the changed code path — is the fix still present or was it reverted/overwritten?
     Read the current version of each changed file and compare to the diff.
  4. Determine WHY the fix failed. Classify as one of:
     - **Wrong root cause** — the original diagnosis was incorrect
     - **Incomplete fix** — correct direction but missed edge cases or code paths
     - **Overwritten** — a subsequent merge or commit reverted/conflicted with the fix
     - **Environment issue** — fix was correct but a config/data/timing issue remains
     - **Other** — state the specific reason

  ## Output (CRITICAL — reserve last 2-3 turns for this)
  ## Previous Fix Analysis
  **PR/Commit:** {reference}
  **What was changed:** {files and summary of changes}
  **Fix still present:** Yes/No — {explanation}
  **Failure mode:** {one of the categories above}
  **Why it failed:** {specific technical explanation}
  **What was missed:** {what the previous investigation got wrong or overlooked}
")
```

**Step 3: Update bug with forensics findings:**
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/add-bug-comment.ps1" -BugId {id} -SystemNote -Comment "Previous fix analysis: {failure mode}. {brief explanation of what was missed}."
```
```

- [ ] **Step 4: Insert Phase 1d — Fresh Investigation**

Insert after Phase 1c. This phase ONLY runs for re-opened bugs.

```markdown
## Phase 1d: Fresh Investigation (Re-opened Bugs Only)

**Skip this phase for new bugs** — proceed directly to Phase 2.

Armed with knowledge of what was already tried and why it failed, run a fresh codebase investigation from scratch.

**Step 1: Dispatch fresh investigation agent:**

```
Task(subagent_type="agentic-search", model="sonnet", max_turns=20, description="Fresh investigation for re-opened bug #{id}", prompt="
  **READ-ONLY MODE: Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files.**

  Investigate this re-opened FuseCP bug with FRESH EYES. A previous fix was applied and failed.

  ## Bug
  - Title: {title}
  - Description: {description}
  - Area: {area}
  - Page URL: {pageUrl}

  ## Previous Fix Forensics (DO NOT repeat this approach)
  - What was tried: {from Phase 1c output}
  - Failure mode: {from Phase 1c output}
  - What was missed: {from Phase 1c output}

  ## Instructions
  1. Start from scratch — do NOT assume the previous root cause was correct
  2. Use ctags for fast symbol lookup:
     ```bash
     grep -i '{keyword}' C:/claude/fusecp-enterprise/tags | head -20
     ```
  3. Area-to-code mapping (search in these locations based on Area):
     - Portal → src/FuseCP.Portal/Components/Pages/ (Blazor .razor files)
     - Exchange → src/FuseCP.Providers.Exchange/ and src/FuseCP.EnterpriseServer/Endpoints/ExchangeEndpoints.cs
     - AD → src/FuseCP.Providers.AD/ and src/FuseCP.EnterpriseServer/Endpoints/ADEndpoints.cs
     - DNS → src/FuseCP.Providers.DNS/ and src/FuseCP.EnterpriseServer/Endpoints/DNSEndpoints.cs
     - HyperV → src/FuseCP.Providers.HyperV/ and src/FuseCP.EnterpriseServer/Endpoints/HyperVEndpoints.cs
     - API → src/FuseCP.EnterpriseServer/Endpoints/
  4. Trace the FULL code path top to bottom:
     - Blazor page (.razor) → Portal service (Services/*.cs) → API endpoint (Endpoints/*.cs) → Repository (Database/Repositories/*.cs) → Provider (Providers.*/)
  5. Look specifically for what the previous investigation missed
  6. Consider: is this a symptom of a deeper architectural issue?

  ## Output (CRITICAL — reserve last 2-3 turns for this)
  ## Fresh Investigation Results
  **Root cause:** {what's actually broken — be specific about the code path}
  **Differs from previous analysis:** Yes/No — {explain how and why}
  **Affected files:**
  | File | Line(s) | Issue |
  |------|---------|-------|
  **Complexity:** Simple / Needs design / Architectural
  - Simple = single-file change, low risk
  - Needs design = multi-file or behavioral change, requires solution design
  - Architectural = cross-cutting concern, requires architectural decision
  **Recommended approach:** {if Simple: describe the fix. If Needs design or Architectural: note what needs to be designed}
")
```

**Step 2: Visual investigation (if screenshots exist):**

Follow the same visual investigation process as Phase 3b (navigate to PageUrl, compare bug screenshot with live page). This is unchanged — reuse the existing Phase 3b instructions.

**Step 3: Update bug with findings:**
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/add-bug-comment.ps1" -BugId {id} -SystemNote -Comment "Fresh analysis complete. Root cause: {root cause summary}. Complexity: {Simple|Needs design|Architectural}."
```
```

- [ ] **Step 5: Insert Phase 1e — Compile & Brainstorm Handoff**

Insert after Phase 1d. This phase ONLY runs for re-opened bugs.

```markdown
## Phase 1e: Compile Analysis & Brainstorm Handoff (Re-opened Bugs Only)

**Skip this phase for new bugs** — proceed directly to Phase 2.

After Phases 1c and 1d complete, compile all findings and hand off to `/brainstorm`.

**Step 1: Present analysis summary to user:**

```markdown
## Re-opened Bug #{id} — Analysis Complete

**Bug:** {title}
**Reopened:** {N} times
**Area:** {area}

### Previous Fix (Phase 1c)
- **What was tried:** {from forensics}
- **Why it failed:** {failure mode and explanation}
- **Fix still present:** {yes/no}

### Fresh Investigation (Phase 1d)
- **Root cause:** {from fresh investigation}
- **Differs from previous analysis:** {yes/no + explanation}
- **Complexity:** {Simple / Needs design / Architectural}
- **Affected files:**
  | File | Line(s) | Issue |
  |------|---------|-------|

### Visual Comparison
{screenshot findings or "No screenshots available"}

Ready to start /brainstorm with this context?
```

**STOP HERE and wait for explicit user confirmation.** Do NOT proceed without approval.

**Step 2: On confirmation, update bug:**
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/add-bug-comment.ps1" -BugId {id} -SystemNote -Comment "Analysis complete. Escalated to brainstorm for solution design."
```

**Step 3: Launch /brainstorm**

Invoke `/brainstorm` with the full compiled context as the input message. Include:
- Bug title, ID, description, area, page URL
- Previous fix forensics summary (what was tried, why it failed)
- Fresh investigation results (root cause, affected files, complexity)
- Visual comparison findings (if any)

The brainstorm session receives all context needed to skip its own investigation and go straight to exploring solution approaches.

**Step 4: Pipeline stops for this bug.** `/brainstorm` takes over solution design. The bug remains in `Investigating` status until a fix is eventually deployed through the normal Phase 7 flow (which sets it to `Fixed`).

**After brainstorm completes:** The user will use `/create-plan` → `/subagent-dev` to implement the designed solution. The resulting PR and deploy go through the standard Phase 7 process, which marks the bug as Fixed.
```

- [ ] **Step 6: Update the re-opened bug note at line 96**

The existing note (line 96) about re-opened bugs requiring "extra scrutiny" should be removed or replaced since re-opened bugs now have their own dedicated flow (Phases 1c-1e) and never reach the normal investigation phases.

Replace the note at line 96 with:
```markdown
**Re-opened bug handling:** Bugs with `ReopenedCount > 0` are routed to the analysis flow (Phases 1c → 1d → 1e → /brainstorm) instead of the auto-fix pipeline. They are NOT processed by Phases 2-8.
```

- [ ] **Step 7: Verify the command file is valid markdown**

Read the full file to check for formatting issues, unclosed code blocks, or broken markdown structure.

- [ ] **Step 8: Commit**

```bash
cd /c/claude/amplifier && git add .claude/commands/fix-bugs.md && git commit -m "$(cat <<'EOF'
feat: route re-opened bugs through analysis flow in /fix-bugs

Re-opened bugs (ReopenedCount > 0) now go through:
- Phase 1c: Previous-fix forensics (why did the last fix fail?)
- Phase 1d: Fresh investigation (new root cause from scratch)
- Phase 1e: Compile findings and hand off to /brainstorm

Normal bugs (ReopenedCount = 0) are unaffected.

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
EOF
)"
```

---

## Chunk 3: Verification

### Task 4: Deploy and verify the full flow

**Agent:** modular-builder
**Model:** haiku

**Files:**
- No new files — verification only

- [ ] **Step 1: Deploy Portal and API**

Portal (for badge/filter changes):
```bash
C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Stop-WebAppPool -Name 'FuseCP_Portal'"
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet publish --configuration Release --output /c/FuseCP/Portal
C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Start-WebAppPool -Name 'FuseCP_Portal'"
```

API (no code changes, but rebuild to be safe):
```bash
C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Stop-WebAppPool -Name 'FuseCP_API'"
cd /c/claude/fusecp-enterprise/src/FuseCP.EnterpriseServer && dotnet publish --configuration Release --output /c/FuseCP/EnterpriseServer
C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Start-WebAppPool -Name 'FuseCP_API'"
```

- [ ] **Step 2: Verify "Investigating" status via API**

```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId {test-bug-id} -Status Investigating
```

Expected: HTTP 200, bug status updated.

Reset:
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId {test-bug-id} -Status Open
```

- [ ] **Step 3: Verify portal badge renders**

Navigate to https://fusecp.ergonet.pl bug reports page. Check:
- "Investigating" appears in the status filter dropdown
- If any bug is set to Investigating, the amber/orange badge renders correctly

- [ ] **Step 4: Verify fix-bugs.md command structure**

Read the modified fix-bugs.md end to end. Verify:
- Phase 1 has three-bucket routing
- Phases 1c, 1d, 1e are present and well-formed
- Phase 2 onwards is unchanged
- No broken markdown formatting

- [ ] **Step 5: Summary**

Report results:
```
## Verification Results

| Check | Status |
|-------|--------|
| Migration applied | PASS/FAIL |
| API accepts Investigating | PASS/FAIL |
| Portal filter dropdown | PASS/FAIL |
| Portal badge color | PASS/FAIL |
| fix-bugs.md structure | PASS/FAIL |
```
