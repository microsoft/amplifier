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

Parse the pipe-delimited output. If no bugs, report "No open bugs found" and stop.

**Separate by Type:** Split results into Bugs (Type=`Bug` or missing/null) and Feature Requests (Type=`FeatureRequest`).

**If Feature Requests exist, present them first:**
```
Found M feature request(s):

| # | ID | Priority | Area | Title | Reported |
|---|-----|----------|------|-------|----------|
| 1 | 45  | Medium   | Portal | Add bulk user import | 2026-02-18 |

Feature requests are NOT auto-fixed. Use /brainstorm to discuss them.
```

**Then present Bugs:**

**Sort bugs by priority:** Re-opened bugs get top priority within their priority level. Then Critical > High > Medium > Low, then by ReportedAt (oldest first within same priority).

```
Found N open bug(s):

| # | ID | Priority | Area | Title | Reported | Re-opened |
|---|-----|----------|------|-------|----------|-----------|
| 1 | 42  | Critical | Portal | Login page crashes on submit | 2026-02-15 | REOPENED(2) |
| 2 | 38  | High     | Exchange | Mailbox creation fails silently | 2026-02-14 | |

Working on #1 (highest priority, re-opened). Say "skip" to pick a different one, or "brainstorm #45" to discuss a feature request.
```

**Re-opened bug handling:** Bugs with `ReopenedCount > 0` (shown as `REOPENED(N)` in the last column) were previously fixed but the fix didn't work. These require extra scrutiny — the previous fix attempt was insufficient. When investigating re-opened bugs, also check the bug's comments for the previous fix description to understand what was tried.

**Feature Request routing:** If the user says "brainstorm #ID" for a feature request, stop the fix pipeline and invoke `/brainstorm` with the feature request details as context. Do NOT attempt to implement feature requests automatically.

**If only Feature Requests remain (no bugs):** Report "No open bugs found. There are M feature request(s) — use /brainstorm to discuss them." and stop.

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

4. **Navigate to the live page** (if PageUrl is provided and Chrome MCP is available):
   ```
   mcp__claude-in-chrome__tabs_context_mcp()
   mcp__claude-in-chrome__tabs_create_mcp()
   mcp__claude-in-chrome__navigate(url="{pageUrl}", tabId={tabId})
   mcp__claude-in-chrome__browser_take_screenshot(type="png")
   ```

5. **Compare** the bug screenshot with the live page to understand:
   - Is the bug still reproducible?
   - What visual elements are broken?
   - What's the expected vs actual state?

6. **If no valid screenshots could be extracted** (no files in `tmp/bug_{id}_*`), skip visual investigation entirely. Note "No screenshots available — investigation based on code analysis only" and proceed to Phase 3c.

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

### 7g. Visual Verification (if Chrome available and PageUrl exists)

After deploy, navigate back to the PageUrl and take a screenshot to verify the fix is visible.

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
