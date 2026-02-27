---
description: "Autonomous bug-fixing pipeline for FuseCP. Fetches open bugs from the portal API, investigates with agentic-search + visual analysis, fixes with bug-hunter, builds/tests, and deploys with user confirmation."
---

# FuseCP Bug Fix Pipeline

## Overview

Autonomous bug-fixing workflow that processes FuseCP bug reports. When multiple bugs are open, performs an LLM-powered triage to group similar/redundant bugs so they can be investigated and fixed together. Single bugs proceed directly. Fetches bugs from the portal's built-in bug reporting API, investigates using codebase exploration and visual comparison, implements fixes, and deploys with user confirmation.

**Announce at start:** "Starting FuseCP bug fix pipeline. Checking for open bugs..."

## Prerequisites

- FuseCP API must be running at `http://localhost:5010`
- FuseCP Portal must be running at `https://fusecp.ergonet.pl`
- Source code at `C:\claude\fusecp-enterprise`
- Playwright MCP server configured (for visual investigation + post-deploy smoke checks)

## Platform Notes (CRITICAL)

This runs on **Windows Server + Git Bash**. Follow these rules in ALL commands:

- **Paths**: Always use `C:/claude/fusecp-enterprise/` (Windows format with forward slashes). Never use `/c/` Git Bash paths in Python or PowerShell.
- **curl**: Always single-line. Never use `\` line continuation (breaks in Git Bash).
- **Temp files**: Save to `C:/claude/fusecp-enterprise/tmp/` (gitignored). Create with `mkdir -p` if needed.
- **Null output**: Use `> /dev/null 2>&1` (never `> nul`)
- **Python**: Use `uv run python` (not `python` — not on system PATH)
- **PowerShell**: NEVER use inline `powershell -Command` with `$_`, `$()`, or `$variable` — Git Bash mangles dollar signs into `extglob`. Instead, **always write a `.ps1` script file first** using the Write tool, then execute it with `powershell -File "path/to/script.ps1"`. This applies to ALL JSON parsing, Base64 decoding, and any PowerShell logic with variables.
- **Gitea API (CRITICAL)**: NEVER use `curl` to POST JSON to the Gitea API from Git Bash — JSON escaping with double-quotes and backslashes breaks silently, producing `"json: string unexpected end of JSON input"`. **ALWAYS use the PowerShell bugfix scripts** (`create-gitea-pr.ps1`, `merge-gitea-pr.ps1`) which handle JSON properly via `ConvertTo-Json`.
- **Screenshots (CRITICAL)**: NEVER download screenshots using `curl --output file.png`. The screenshot API returns **JSON with base64 data**, NOT raw image bytes. Saving JSON as `.png` and then using `Read` to view it will crash the session permanently (the malformed image poisons the conversation context and every subsequent API call fails). **ALWAYS use the PowerShell bugfix scripts** (`read-bug.ps1 -ExtractScreenshot`, `read-bugs-group.ps1 -ExtractScreenshots`, or `extract-screenshot.ps1`) which properly decode base64 and validate image magic bytes. Scripts support PNG, JPEG, GIF, and WebP — files are saved with the correct extension (`.png`, `.jpg`, `.gif`, `.webp`).

## Bugfix Scripts (Persistent)

Reusable PowerShell scripts live at `C:/claude/fusecp-enterprise/scripts/bugfix/`. Use these instead of writing new scripts each time:

| Script | Purpose | Usage |
|--------|---------|-------|
| `fetch-open-bugs.ps1` | Fetch open bugs, output pipe-delimited | `powershell -File scripts/bugfix/fetch-open-bugs.ps1 [-JsonOut tmp/open_bugs.json]` |
| `read-bug.ps1` | Fetch single bug details + screenshot | `powershell -File scripts/bugfix/read-bug.ps1 -BugId 30 [-ExtractScreenshot]` |
| `read-bugs-group.ps1` | Fetch multiple bugs + screenshots | `powershell -File scripts/bugfix/read-bugs-group.ps1 -BugIds "29,30,34" [-ExtractScreenshots]` |
| `extract-screenshot.ps1` | Extract screenshot (legacy + multi) | `powershell -File scripts/bugfix/extract-screenshot.ps1 -BugId 30` |
| `set-bug-status.ps1` | Update bug status (safe endpoint) | `powershell -File scripts/bugfix/set-bug-status.ps1 -BugId 30 -Status InProgress` |
| `add-bug-comment.ps1` | Add fix description comment to bug | `powershell -File scripts/bugfix/add-bug-comment.ps1 -BugId 30 -Comment "Fixed by..." -SystemNote` |
| `gitea-create-pr.ps1` | Create PR on Gitea (shared, auto-detects repo) | `powershell -File "C:/claude/amplifier/scripts/gitea/gitea-create-pr.ps1" -Title "fix: title" -Head "hotfix/bug-30"` |
| `gitea-merge-pr.ps1` | Merge PR on Gitea (shared, auto-detects repo) | `powershell -File "C:/claude/amplifier/scripts/gitea/gitea-merge-pr.ps1" -PrNumber 1 -DeleteBranch` |

All bugfix scripts default to `ApiBase=http://localhost:5010` and `ApiKey=fusecp-admin-key-2026`. Gitea scripts live at `C:\claude\amplifier\scripts\gitea\` (version-controlled), default to `https://gitea.ergonet.pl:3001` with token from `$GITEA_ADMIN_TOKEN` env var (fallback: hardcoded), and auto-detect the repo by finding which repo contains the `-Head` branch. Screenshots save to `tmp/` by default.

## API Configuration

```
API_BASE=http://localhost:5010
API_KEY=fusecp-admin-key-2026
```

All curl commands use: `curl -sk -H "X-Api-Key: fusecp-admin-key-2026"`

## Phase 1: Fetch Open Bugs

```bash
mkdir -p C:/claude/fusecp-enterprise/tmp
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/fetch-open-bugs.ps1" -JsonOut "C:/claude/fusecp-enterprise/tmp/open_bugs.json"
```

Parse the pipe-delimited output. If no bugs or feature requests, report "No open bugs found" and stop.

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

**Sort re-opened bugs by priority:** Critical > High > Medium > Low, then by LastReopenedAt (most recently reopened first).

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

**Re-opened bug selection:** When the user selects a re-opened bug (or one is auto-selected as highest priority among re-opened), immediately:

```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId {id} -Status Investigating
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/add-bug-comment.ps1" -BugId {id} -SystemNote -Comment "Re-opened bug picked up for deep analysis (reopened {N} times)"
```

Then proceed to **Phase 1c** (below).

**New bug selection:** Proceed to Phase 1b (triage, if 2+ new bugs) or Phase 2 (if 1 new bug) — unchanged.

**Re-opened bug handling:** Bugs with `ReopenedCount > 0` are routed to the analysis flow (Phases 1c → 1d → 1e → /brainstorm) instead of the auto-fix pipeline. They are NOT processed by Phases 2-8.

**Feature Request routing:** If the user says "brainstorm #ID" for a feature request, stop the fix pipeline and invoke `/brainstorm` with the feature request details as context. Do NOT attempt to implement feature requests automatically.

**If only Feature Requests remain (no bugs of either type):** Report "No open bugs found. There are M feature request(s) — use /brainstorm to discuss them." and stop.

**If only Re-opened Bugs remain (no new bugs):** Process re-opened bugs through analysis flow. Do NOT report "no bugs."

**If only New Bugs remain (no re-opened):** Process new bugs through normal pipeline (unchanged).

## Phase 1b: Triage & Group (when 2+ bugs open)

**Skip this phase entirely if only 1 bug is open** — proceed directly to Phase 2.

When there are 2 or more open bugs, dispatch `analysis-engine` to cluster them by likely root cause:

```
Task(subagent_type="analysis-engine", model="haiku", max_turns=8, description="Triage and group open bugs", prompt="
  Analyze these open FuseCP bugs and group them by likely root cause or similarity.

  ## Open Bugs
  {paste the bug list as a table: ID, Priority, Area, Title, Reported date}

  ## Grouping Criteria
  Group bugs that likely share:
  - Same root cause (e.g., two reports of the same broken feature)
  - Same affected component (same Area + related page/functionality)
  - Overlapping symptoms (descriptions point to the same underlying issue)
  - Duplicate reports (same bug reported by different users or at different times)

  Bugs that are clearly independent should be in their own group of 1.

  ## Output Format (CRITICAL — follow exactly)

  Return ONLY this JSON structure, nothing else:

  ```json
  {
    \"groups\": [
      {
        \"name\": \"Short description of the shared issue\",
        \"bugIds\": [42, 38],
        \"rationale\": \"One sentence explaining why these are grouped\",
        \"priority\": \"Critical\"
      }
    ]
  }
  ```

  Rules:
  - Every bug must appear in exactly one group
  - A group can have 1 bug (independent issue)
  - Group priority = highest priority among its bugs
  - Sort groups by priority: Critical > High > Medium > Low
")
```

**Parse the agent response and present to user:**

```
## Bug Triage — {N} bugs in {G} groups

| Group | Bugs | Priority | Description |
|-------|------|----------|-------------|
| 1 | #42, #38 | Critical | Login and auth both fail — likely same session handling bug |
| 2 | #45 | Medium | DNS template preview not rendering (independent) |

Proceed with Group 1 first? Say "regroup" to adjust, or "skip to #N" to pick a different group.
```

**STOP and wait for user confirmation.** Do not proceed until the user approves the grouping.

**If user says "regroup":** Ask which bugs to move between groups, update the groupings, and re-present.

**After confirmation:** Process groups in priority order. For each group, set `_currentGroup` to the list of bug IDs. All subsequent phases operate on the entire group together.

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

## Phase 2: Load Bug Details & Set InProgress

**When processing a group of bugs:** Use `read-bugs-group.ps1` to fetch all at once. For a single bug, use `read-bug.ps1`.

**Single bug:**
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/read-bug.ps1" -BugId {id} -ExtractScreenshot
```

**Group of bugs:**
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/read-bugs-group.ps1" -BugIds "{id1},{id2},{id3}" -ExtractScreenshots
```

Parse the output for these key fields:
- `Title`, `Description` — What's broken
- `Area` — Which subsystem (Portal, Exchange, AD, DNS, HyperV, API)
- `PageUrl` — The URL where the bug was observed (if provided)
- `Priority` — Severity level
- `ScreenshotCount` — Number of screenshots (auto-extracted to `tmp/bug_{id}_screenshot.{ext}` with correct extension if `-ExtractScreenshot(s)` flag used)

**Update status to InProgress:**
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId {id} -Status InProgress
```

**IMPORTANT:** The `set-bug-status.ps1` script uses the `/status` endpoint (not full PUT), which preserves screenshot data.

## Phase 3: Investigate

### 3a. Code Investigation

Dispatch `agentic-search` agent with structured three-phase methodology (Reconnaissance → Targeted Search → Synthesis). This agent has built-in output budgets and always produces a final synthesis — unlike generic Explore which can exhaust turns on tool calls with no summary.

```
Task(subagent_type="agentic-search", model="sonnet", max_turns=20, description="Investigate bug #{id}: {title}", prompt="
  **READ-ONLY MODE: Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files.**

  Search the FuseCP codebase at C:\claude\fusecp-enterprise to find the root cause of this bug.

  Bug: {title}
  Description: {description}
  Area: {area}
  Page URL: {pageUrl}

  **When processing a group:** Replace the single Bug/Description/Area/URL fields above with:

  ## Bugs in this group
  {for each bug in group, list: Bug #{id}: {title} — {description} (Area: {area}, URL: {pageUrl})}

  These bugs are grouped because: {group rationale}

  Investigate the SHARED root cause. If during investigation you discover they are actually unrelated, note this in your synthesis.

  ## Phase 1: Reconnaissance
  Use ctags for fast symbol lookup:
    grep -i '{keyword}' C:/claude/fusecp-enterprise/tags | head -20

  Area-to-code mapping (search in these locations based on Area):
  - Portal → src/FuseCP.Portal/Components/Pages/ (Blazor .razor files)
  - Exchange → src/FuseCP.Providers.Exchange/ and src/FuseCP.EnterpriseServer/Endpoints/ExchangeEndpoints.cs
  - AD → src/FuseCP.Providers.AD/ and src/FuseCP.EnterpriseServer/Endpoints/ADEndpoints.cs
  - DNS → src/FuseCP.Providers.DNS/ and src/FuseCP.EnterpriseServer/Endpoints/DNSEndpoints.cs
  - HyperV → src/FuseCP.Providers.HyperV/ and src/FuseCP.EnterpriseServer/Endpoints/HyperVEndpoints.cs
  - API → src/FuseCP.EnterpriseServer/Endpoints/

  ## Phase 2: Targeted Search (max 8 file reads)
  Architecture layers (trace top to bottom):
  1. Blazor page (.razor) — UI component with @onclick handlers
  2. Portal service (Services/*.cs) — HTTP client calling API
  3. API endpoint (Endpoints/*.cs) — Minimal API route handler
  4. Repository (Database/Repositories/*.cs) — SQL/Dapper data access
  5. Provider (Providers.*/) — External system integration (Exchange/AD/DNS/HyperV)

  Read the identified files and trace the bug through the layers.

  ## Phase 3: Synthesis (CRITICAL — always produce this)
  BEFORE you run out of turns, produce this structured output:

  ## Root Cause
  [What's broken and why — be specific about the code path]

  ## Affected Files
  | File | Line(s) | Issue |
  |------|---------|-------|

  ## Suggested Fix
  [Minimal change needed — specific enough for a developer to implement]

  IMPORTANT: Reserve your last 2-3 turns for writing the synthesis. Do NOT spend all turns on tool calls — the synthesis is the most important output.
")
```

### 3a-fallback. Direct Investigation (if agent fails or returns incomplete)

If the Explore agent returns without a clear root cause, investigate directly. Do NOT dispatch another agent — work in main context using these focused searches:

**Step 1: ctags lookup**
```bash
grep -i '{keyword}' C:/claude/fusecp-enterprise/tags | head -20
```

**Step 2: Grep for the feature**
```
Grep(pattern="{keyword}", path="C:\\claude\\fusecp-enterprise\\src", output_mode="files_with_matches")
```

**Step 3: Area-specific search**

| Area | Search Pattern | Key Files |
|------|---------------|-----------|
| Portal | `Grep pattern in src/FuseCP.Portal/Components/Pages/` | .razor files with @onclick handlers |
| Exchange | `Grep in src/FuseCP.Providers.Exchange/` | ExchangeProvider.cs, ExchangeRepository.cs |
| AD | `Grep in src/FuseCP.Providers.AD/` | ADProvider.cs, ADRepository.cs |
| DNS | `Grep in src/FuseCP.Providers.DNS/` | DNSProvider.cs |
| HyperV | `Grep in src/FuseCP.Providers.HyperV/` | HyperVProvider.cs |
| API | `Grep in src/FuseCP.EnterpriseServer/Endpoints/` | *Endpoints.cs |

**Step 4: Read the identified files** (max 3-5 files to preserve context)

This fallback is faster and more reliable than retrying agent dispatches.

### 3b. Visual Investigation (when screenshot exists)

**CRITICAL: NEVER download screenshots with curl.** The API returns JSON (not raw bytes). Using `curl --output file.png` saves JSON as a PNG file, which crashes the session when Read tries to display it. This is an **unrecoverable crash** — the malformed image poisons the conversation context permanently.

If the bug has screenshots (ScreenshotCount > 0):

1. **Screenshot already extracted** — Phase 2 scripts automatically extract screenshots to `C:/claude/fusecp-enterprise/tmp/`. The scripts handle base64 decoding and image format detection (PNG, JPEG, GIF, WebP). If you need to re-extract:
   ```bash
   powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/extract-screenshot.ps1" -BugId {id}
   ```

   Screenshots are saved with the correct extension based on actual image format:
   - Legacy: `tmp/bug_{id}_screenshot.{png|jpg|gif|webp}`
   - Multi-screenshot: `tmp/bug_{id}_ss_{screenshotId}.{png|jpg|gif|webp}`

2. **Find the extracted file** — list tmp files for this bug to find the actual filename:
   ```bash
   ls C:/claude/fusecp-enterprise/tmp/bug_{id}_screenshot.* C:/claude/fusecp-enterprise/tmp/bug_{id}_ss_*.* 2>/dev/null
   ```
   If no files found, the extraction failed — skip visual analysis and proceed to Phase 3c.

3. **View the screenshot** (the scripts already validate image magic bytes, so extracted files are safe to view):
   ```
   Read(file_path="C:/claude/fusecp-enterprise/tmp/bug_{id}_screenshot.{ext}")
   ```

4. **Navigate to the live page** (if PageUrl is provided) using Playwright MCP:
   ```
   mcp__playwright__browser_navigate(url="{pageUrl}")
   ```

5. **Handle login (if redirected to `/auth/login`)**

   Take a snapshot to check if the page is a login form:
   ```
   mcp__playwright__browser_snapshot()
   ```

   If login form is present, authenticate using the snapshot's element refs:
   ```
   mcp__playwright__browser_click(ref="{username-field-ref}", element="Username input")
   mcp__playwright__browser_type(ref="{username-field-ref}", text="serveradmin", submit=false)
   mcp__playwright__browser_click(ref="{password-field-ref}", element="Password input")
   mcp__playwright__browser_type(ref="{password-field-ref}", text="Fusecp@2026", submit=false)
   mcp__playwright__browser_click(ref="{login-button-ref}", element="Login button")
   ```

   Wait for navigation, then go to the target page:
   ```
   mcp__playwright__browser_wait_for(time=3000)
   mcp__playwright__browser_navigate(url="{pageUrl}")
   ```

6. **Wait for Blazor to stabilize and take baseline screenshot**

   Wait for page content to appear (prefer text-based wait over fixed timer):
   ```
   mcp__playwright__browser_wait_for(text="{expected page heading or content indicator}")
   ```
   If no known text indicator exists for this page, fall back to:
   ```
   mcp__playwright__browser_wait_for(time=3000)
   ```

   Take an accessibility snapshot to verify the page rendered:
   ```
   mcp__playwright__browser_snapshot()
   ```

   Save a **baseline screenshot** (pre-fix state for later comparison in Phase 7g):
   ```
   mcp__playwright__browser_take_screenshot(type="png", filename="C:/claude/fusecp-enterprise/tmp/bug_{id}_baseline.png")
   ```

7. **Interaction testing** (when bug involves UI interactions)

   If the bug description mentions clicking, submitting, selecting, or form input:
   - Use the accessibility snapshot from step 6 to identify the relevant interactive elements
   - Attempt the interaction described in the bug report (click a button, fill a form, select an option)
   - Take a snapshot after the interaction to observe the result
   - Note what happens: error message, blank page, nothing, unexpected behavior

   If the bug is purely visual (layout, styling, missing data), skip interaction testing.

8. **Check console for JavaScript errors**
   ```
   mcp__playwright__browser_console_messages(level="error")
   ```
   Note any errors (ignoring known Blazor noise: `blazor.server.js`, `[HMR]`, `favicon.ico` 404s).

9. **Compare** the bug screenshot (from step 3) with the live page to understand:
   - Is the bug still reproducible?
   - What visual elements are broken?
   - What's the expected vs actual state?
   - Are there console errors that explain the visual issue?

10. **Cleanup — close browser to free resources**
    ```
    mcp__playwright__browser_close()
    ```

11. **If no valid screenshots could be extracted** (no files in `tmp/bug_{id}_*`) AND no PageUrl is provided, skip visual investigation entirely. Note "No screenshots or page URL available — investigation based on code analysis only" and proceed to Phase 3c.

    **If PageUrl exists but no screenshots:** Still navigate and take baseline — the live page investigation is valuable even without a bug screenshot to compare against.

### 3c. Compile Investigation Summary

Before dispatching the fix agent, compile everything learned:

```markdown
## Bug #{id} Investigation Summary

**Bug:** {title}
**Root area:** {file:line references}
**Visual analysis:** {screenshot comparison findings, or "No screenshot provided"}
**Hypothesis:** {likely root cause based on code + visual evidence}
**Affected files:** {list with line numbers}
**Suggested fix:** {minimal change description}
```

## Phase 4: Fix

Dispatch `bug-hunter` with the full investigation context:

```
Task(subagent_type="bug-hunter", model="sonnet", max_turns=20, description="Fix bug #{id}: {title}", prompt="
  Fix this FuseCP bug. The investigation has already been done — go straight to implementing the fix.

  ## Bug Report
  - Title: {title}
  - Description: {description}
  - Area: {area}
  - Page URL: {pageUrl}
  - Priority: {priority}

  ## Investigation Results
  {paste the full investigation summary from Phase 3c — including file paths, line numbers, and suggested fix}

  **When processing a group:** Replace the single Bug fields above with:

  ## Bug Group
  {for each bug in group: Bug #{id}: {title} — {description}}
  Group rationale: {rationale}

  ## Group-Specific Instructions
  1. Fix the SHARED root cause that affects all bugs in this group
  2. If the bugs have slightly different symptoms, ensure the fix addresses all of them

  ## Instructions
  1. Read the identified files to confirm the root cause
  2. Implement the MINIMAL fix — don't refactor surrounding code
  3. If the fix requires changes to multiple files, make all changes
  4. Follow existing code patterns and conventions
  5. The codebase is C# (.NET 8) with Blazor Server for Portal, Minimal APIs for backend

  ## FuseCP Project Structure
  - Portal (Blazor): src/FuseCP.Portal/
  - API: src/FuseCP.EnterpriseServer/
  - Database: src/FuseCP.Database/
  - Providers: src/FuseCP.Providers.*/
  - Tests: tests/

  ## Output
  List every file you changed with a brief description of what you changed and why.
")
```

### Phase 4-fallback. Direct Fix (if bug-hunter fails)

If the bug-hunter returns without completing the fix, implement it directly in main context. You already have the investigation summary — just Read the files and Edit them.

## Phase 5: Build and Test

After the fix is applied:

```bash
cd /c/claude/fusecp-enterprise && dotnet build --no-incremental 2>&1 | tail -5
```

If build fails, fix build errors and retry (max 3 attempts).

```bash
cd /c/claude/fusecp-enterprise && dotnet test --no-build --verbosity quiet 2>&1 | tail -10
```

If tests fail, investigate and fix. Note: 1 pre-existing HyperV test failure is expected (ResourceMailboxTests).

## Phase 6: Report to User

Present a complete summary:

```markdown
## Bug #{id} Fixed: {title}

**Root Cause:** {what was actually wrong}

**Changes:**
| File | Change |
|------|--------|
| {path} | {what changed} |

**Build:** PASS
**Tests:** {N} passing, {M} failing (or "All passing")

**Ready to deploy?** This will:
1. Create `hotfix/bug-{id}` branch from latest main
2. Commit and push, then create a PR
3. Wait for CI (pr-check.yml) to pass
4. Merge PR to main
5. Deploy Portal/API to IIS
6. Mark bug as Fixed in the system
```

**When processing a group, use this template instead:**

```
## Bug Group Fixed: {group name}

**Bugs resolved:** #{id1}, #{id2}, ...
**Root Cause:** {what was actually wrong — shared cause}

**Changes:**
| File | Change |
|------|--------|
| {path} | {what changed} |

**Build:** PASS
**Tests:** {N} passing, {M} failing (or "All passing")

**Ready to deploy?** This will:
1. Create `hotfix/bugs-{id1}-{id2}` branch from latest main
2. Commit and push, then create a PR
3. Wait for CI to pass
4. Merge PR to main
5. Deploy Portal/API to IIS
6. Mark ALL {count} bugs as Fixed in the system
```

**STOP HERE and wait for user confirmation.** Do NOT deploy without explicit approval.

## Phase 7: Commit, PR & Deploy (User-Confirmed)

Only after user says yes:

### 7a. Create hotfix branch and commit

Bug fixes go through the PR process to prevent fixes from being lost when feature branches merge.

**Branch naming:**
- Single bug: `hotfix/bug-{id}`
- Group of bugs: `hotfix/bugs-{id1}-{id2}` (use first two IDs if group is large)

```bash
cd /c/claude/fusecp-enterprise && git stash && git checkout main && git pull origin main && git checkout -b hotfix/bug-{id} && git stash pop
```

```bash
cd /c/claude/fusecp-enterprise && git add {changed-files} && git commit -m "$(cat <<'EOF'
fix: {title} (Bug #{id})

{brief description of root cause and fix}

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
EOF
)"
```

### 7b. Push and create PR on Gitea

**PR title for groups:** `fix: {group name} (Bugs #{id1}, #{id2}, ...)`
**PR body:** List all bug IDs with their titles.

Push to Gitea (primary). The push mirror will sync to GitHub automatically.

```bash
cd /c/claude/fusecp-enterprise && git push -u origin hotfix/bug-{id}
```

Create PR on Gitea using the PowerShell script (**NEVER use curl for Gitea API** — JSON escaping breaks in Git Bash):

```bash
powershell -File "C:/claude/amplifier/scripts/gitea/gitea-create-pr.ps1" -Title "fix: {title} (Bug #{id})" -Head "hotfix/bug-{id}" -Body "## Bug Fix`n`n**Bug ID:** #{id}`n**Priority:** {priority}`n**Area:** {area}`n`n### Root Cause`n{root cause}`n`n### Testing`n- Build: PASS`n- Tests: {N} passing`n`nGenerated with Amplifier"
```

Parse the output for `PR_NUMBER=` line. Save the number for Phase 7c.

### 7c. Review PR (MANDATORY)

Before merging, review the PR to catch issues. Dispatch `pr-review-toolkit:code-reviewer` agent:

```
Task(subagent_type="pr-review-toolkit:code-reviewer", model="sonnet", max_turns=12, description="Review PR #{pr-number}", prompt="
  Review the changes on branch hotfix/bug-{id} in C:\claude\fusecp-enterprise.

  Context: This is a bug fix for Bug #{id}: {title}

  Review for:
  1. Does the fix address the root cause (not just symptoms)?
  2. Are there any regressions or side effects?
  3. Does it follow existing code patterns?
  4. Any edge cases missed?

  Run: git diff main...hotfix/bug-{id}

  Return: APPROVE with summary, or CHANGES_REQUESTED with specific issues.
")
```

**If APPROVE:** Proceed to merge.
**If CHANGES_REQUESTED:** Fix the issues on the hotfix branch, push again, and re-review. Max 2 review cycles — if still failing, present issues to user for decision.

### 7d. Wait for CI, then merge on Gitea

The Gitea push mirror syncs branches to GitHub on commit (+ every 10 min). GitHub Actions `pr-check.yml` triggers on push events to synced branches. Wait for it:

```bash
# Wait for GitHub Actions CI on the branch
gh run list --branch hotfix/bug-{id} --limit 1 --json status,conclusion,name --jq '.[0]'
```

If no run appears within 2 minutes, the push mirror may not have synced yet. Push directly to GitHub:
```bash
cd /c/claude/fusecp-enterprise && git push github hotfix/bug-{id}
```

Then re-check CI:
```bash
gh run watch --branch hotfix/bug-{id}
```

**If GitHub Actions CI is not configured for the branch** (no `pr-check.yml` push trigger), skip CI wait and merge directly — the build and tests were already verified locally in Phase 5.

Merge the PR on Gitea using the PowerShell script:

```bash
powershell -File "C:/claude/amplifier/scripts/gitea/gitea-merge-pr.ps1" -PrNumber {gitea-pr-number} -DeleteBranch
```

Then sync local main:
```bash
cd /c/claude/fusecp-enterprise && git checkout main && git pull origin main
```

If CI fails, investigate the failure, fix on the hotfix branch, push to origin again, and re-check.

### 7e. Deploy from main

Determine what to deploy based on changed files:

- **Portal files changed** (`src/FuseCP.Portal/`):
  ```bash
  C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Stop-WebAppPool -Name 'FuseCP_Portal'"
  cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet publish --configuration Release --output /c/FuseCP/Portal
  C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Start-WebAppPool -Name 'FuseCP_Portal'"
  ```

- **API files changed** (`src/FuseCP.EnterpriseServer/` or `src/FuseCP.Database/` or `src/FuseCP.Providers.*/`):
  ```bash
  C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Stop-WebAppPool -Name 'FuseCP_API'"
  cd /c/claude/fusecp-enterprise/src/FuseCP.EnterpriseServer && dotnet publish --configuration Release --output /c/FuseCP/EnterpriseServer
  C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Start-WebAppPool -Name 'FuseCP_API'"
  ```

- **Both Portal + API changed**: Deploy both (API first, then Portal).

### 7f. Add Fix Comment & Update Bug Status

**MANDATORY: Add a fix description comment to each bug BEFORE marking as Fixed.** The comment documents what was fixed for future reference and appears on the bug report page.

**Comment format:** `**Fix:** {concise description of root cause and what was changed}. PR #{pr-number} ({branch-name}).`

```bash
# For each bug ID:
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/add-bug-comment.ps1" -BugId {id} -SystemNote -Comment "**Fix:** {description of what was changed and why}. PR #{pr-number} ({branch-name})."
```

Then mark as Fixed:
```bash
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId {id} -Status Fixed
```

**When processing a group — comment and mark ALL bugs in the group:**
```bash
# For each bug ID in the group:
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/add-bug-comment.ps1" -BugId {id} -SystemNote -Comment "**Fix:** {description}. PR #{pr-number} ({branch-name})."
powershell -File "C:/claude/fusecp-enterprise/scripts/bugfix/set-bug-status.ps1" -BugId {id} -Status Fixed
```

### 7g. Post-Deploy Smoke Check (Playwright)

After deploy, run an automated smoke check on the fixed page using Playwright MCP. This verifies the deployment succeeded and the page renders without errors.

**Skip if:** No `PageUrl` in the bug report, or bug `Area` is not `Portal`.

**Step 1: Navigate to the page**

```
mcp__playwright__browser_navigate(url="{pageUrl}")
```

**Step 2: Handle login (if redirected to `/auth/login`)**

Take a snapshot to check if the page is a login form:
```
mcp__playwright__browser_snapshot()
```

If login form is present, authenticate using the snapshot's element refs:
```
mcp__playwright__browser_click(ref="{username-field-ref}", element="Username input")
mcp__playwright__browser_type(ref="{username-field-ref}", text="serveradmin", submit=false)
mcp__playwright__browser_click(ref="{password-field-ref}", element="Password input")
mcp__playwright__browser_type(ref="{password-field-ref}", text="Fusecp@2026", submit=false)
mcp__playwright__browser_click(ref="{login-button-ref}", element="Login button")
```

Wait for navigation, then go to the target page:
```
mcp__playwright__browser_wait_for(time=3000)
mcp__playwright__browser_navigate(url="{pageUrl}")
```

**Step 3: Wait for Blazor to stabilize**

Blazor Server establishes a SignalR connection after page load. Prefer text-based wait over fixed timer:
```
mcp__playwright__browser_wait_for(text="{expected page heading or content indicator}")
```
If no known text indicator exists for this page, fall back to:
```
mcp__playwright__browser_wait_for(time=3000)
```

**Step 4: Take accessibility snapshot**

```
mcp__playwright__browser_snapshot()
```

Review the snapshot for:
- Page content rendered (not blank or error page)
- No "Error" or "Exception" banners in the page structure
- Expected UI elements are present (tables, forms, buttons relevant to the bug's area)

**Step 5: Check console for errors**

```
mcp__playwright__browser_console_messages(level="error")
```

Review console errors. **Ignore known Blazor noise:**
- `blazor.server.js` reconnection messages
- `[HMR]` hot module reload messages
- `favicon.ico` 404s

**Flag unexpected errors** — these may indicate the fix introduced a runtime issue.

**Step 6: Take verification screenshot**

```
mcp__playwright__browser_take_screenshot(type="png", filename="C:/claude/fusecp-enterprise/tmp/bug_{id}_post_deploy.png")
```

View the screenshot and compare against available references:
- **Baseline screenshot** (`tmp/bug_{id}_baseline.png` from Phase 3b): Best comparison — same viewport, same Playwright session type. Shows what changed between pre-fix and post-fix.
- **Bug report screenshot** (`tmp/bug_{id}_screenshot.*`): Secondary comparison — may differ in viewport/browser but shows the original reported issue.

If both exist, compare all three (bug report → baseline → post-deploy) to verify the fix addressed the reported issue.

**Step 7: Report result**

Append smoke check result to the bug fix summary:
- **PASS**: Page loads, no console errors, content renders correctly
- **WARN**: Page loads but has console errors or unexpected visual state — report details
- **FAIL**: Page doesn't load, shows error page, or is blank — report details

**Step 8: Cleanup**

```
mcp__playwright__browser_close()
```

**Failure handling:**
- If Playwright MCP is unavailable (tool call fails), skip with note: "Playwright unavailable — smoke check skipped. Verify manually."
- Do NOT block the pipeline on smoke check failures — report the result and continue to Phase 7h.
- If smoke check finds issues, include them in the bug comment (Phase 7f) as a note.

### 7h. Cleanup temp files

```bash
rm -f C:/claude/fusecp-enterprise/tmp/bug_{id}*
```

## Phase 8: Next Bug

After completing a fix:

"Bug #{id} fixed and deployed. {N-1} open bugs remaining. Fix the next one?"

**When processing a group:**
"Bug group fixed and deployed. {remaining groups} group(s) remaining ({total remaining bugs} bugs). Fix the next group?"

If user says yes, loop back to Phase 1.

## Error Handling

- **API unreachable:** "FuseCP API is not responding at localhost:5010. Is the API running?"
- **No open bugs:** "No open bugs found. The bug queue is clear."
- **agentic-search agent fails or returns incomplete:** Fall back to direct investigation (Phase 3a-fallback). Do NOT retry the agent.
- **bug-hunter fails:** Fall back to direct fix in main context (Phase 4-fallback). Do NOT retry the agent.
- **Build failure after 3 attempts:** "Build still failing after 3 fix attempts. Escalating — here's what I've tried: {summary}"
- **Test failure:** "Tests failing after fix. Investigating if these are pre-existing or caused by the fix."
- **CI failure on PR:** Investigate the CI log (`gh run view --branch hotfix/bug-{id}`), fix on the hotfix branch, push to origin again. Do NOT merge a failing PR.
- **Merge conflict:** Rebase the hotfix branch on latest main: `git fetch origin && git rebase origin/main`. Fix any conflicts, then force-push the branch.
- **Deploy failure:** "Deploy failed: {error}. The PR is merged but not deployed. You may need to deploy manually."
- **Screenshot extraction produces no files:** Skip visual analysis entirely. The extraction scripts validate image magic bytes and only keep valid images (PNG, JPEG, GIF, WebP). If no files are saved, proceed with code-only investigation.

## Why PRs for Bug Fixes

Bug fixes MUST go through the PR process (not direct commits to main) because:
1. **Prevents lost fixes:** Feature branches that merge later won't overwrite bug fixes — they must be up-to-date with main before merging.
2. **CI verification:** Push mirror syncs to GitHub where `pr-check.yml` runs build + tests + security scan.
3. **Audit trail:** Each fix has a Gitea PR number linking to the bug ID for traceability.
4. **Branch protection:** Gitea branch protection blocks direct pushes to main — PRs are required on all repos.

## Priority Handling

| Priority | Approach |
|----------|----------|
| Critical | Fix immediately, minimal investigation — speed matters |
| High | Full investigation + fix cycle |
| Medium | Full investigation, consider if test is needed |
| Low | Investigate, propose fix, ask user before implementing |

## Additional Context

$ARGUMENTS
