---
description: "Autonomous bug-fixing pipeline for FuseCP. Fetches open bugs from the portal API, investigates with agentic-search + visual analysis, fixes with bug-hunter, builds/tests, and deploys with user confirmation."
---

# FuseCP Bug Fix Pipeline

## Overview

Autonomous bug-fixing workflow that processes FuseCP bug reports one at a time. Fetches bugs from the portal's built-in bug reporting API, investigates using codebase exploration and visual comparison, implements fixes, and deploys with user confirmation.

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

## API Configuration

```
API_BASE=http://localhost:5010
API_KEY=fusecp-admin-key-2026
```

All curl commands use: `curl -sk -H "X-Api-Key: fusecp-admin-key-2026"`

## Phase 1: Fetch Open Bugs

```bash
mkdir -p C:/claude/fusecp-enterprise/tmp
curl -sk -H "X-Api-Key: fusecp-admin-key-2026" "http://localhost:5010/api/bugs?status=Open" -o C:/claude/fusecp-enterprise/tmp/open_bugs.json
```

**Parse the JSON using a PowerShell script** (never inline — see Platform Notes):

Write this script using the Write tool to `C:/claude/fusecp-enterprise/tmp/parse_bugs.ps1`:
```powershell
$bugs = Get-Content 'C:/claude/fusecp-enterprise/tmp/open_bugs.json' | ConvertFrom-Json
foreach ($b in $bugs) {
    $hasScreenshot = if ($b.screenshotData) { 'Yes' } else { 'No' }
    $type = if ($b.type) { $b.type } else { 'Bug' }
    $reported = if ($b.reportedAt) { ($b.reportedAt -split 'T')[0] } else { 'Unknown' }
    Write-Host "$($b.bugId)|$($b.priority)|$type|$($b.area)|$($b.title)|$reported|$hasScreenshot"
}
```

Then execute:
```bash
powershell -File "C:/claude/fusecp-enterprise/tmp/parse_bugs.ps1"
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

**Sort bugs by priority:** Critical > High > Medium > Low, then by ReportedAt (oldest first within same priority).

```
Found N open bug(s):

| # | ID | Priority | Area | Title | Reported |
|---|-----|----------|------|-------|----------|
| 1 | 42  | Critical | Portal | Login page crashes on submit | 2026-02-15 |
| 2 | 38  | High     | Exchange | Mailbox creation fails silently | 2026-02-14 |

Working on #1 (highest priority). Say "skip" to pick a different one, or "brainstorm #45" to discuss a feature request.
```

**Feature Request routing:** If the user says "brainstorm #ID" for a feature request, stop the fix pipeline and invoke `/brainstorm` with the feature request details as context. Do NOT attempt to implement feature requests automatically.

**If only Feature Requests remain (no bugs):** Report "No open bugs found. There are M feature request(s) — use /brainstorm to discuss them." and stop.

## Phase 2: Load Bug Details & Set InProgress

**Fetch full bug details and save response for later use:**
```bash
curl -sk -H "X-Api-Key: fusecp-admin-key-2026" "http://localhost:5010/api/bugs/{id}" -o C:/claude/fusecp-enterprise/tmp/bug_{id}.json
```

**Extract key fields using a PowerShell script** (never inline — see Platform Notes):

Write this script using the Write tool to `C:/claude/fusecp-enterprise/tmp/read_bug.ps1`:
```powershell
$b = Get-Content 'C:/claude/fusecp-enterprise/tmp/bug_{id}.json' | ConvertFrom-Json
Write-Host "Title: $($b.title)"
Write-Host "Description: $($b.description)"
Write-Host "Area: $($b.area)"
Write-Host "Priority: $($b.priority)"
Write-Host "PageUrl: $($b.pageUrl)"
Write-Host "ReportedInBuild: $($b.reportedInBuild)"
Write-Host "ReportedAt: $($b.reportedAt)"
Write-Host "HasScreenshot: $([bool]$b.screenshotData)"
Write-Host "ScreenshotMimeType: $($b.screenshotMimeType)"
if ($b.screenshotData) {
    [IO.File]::WriteAllBytes('C:/claude/fusecp-enterprise/tmp/bug_{id}_screenshot.png', [Convert]::FromBase64String($b.screenshotData))
    Write-Host 'Screenshot saved to bug_{id}_screenshot.png'
}
```

**IMPORTANT:** Replace `{id}` in the script with the actual bug ID before writing. Then execute:
```bash
powershell -File "C:/claude/fusecp-enterprise/tmp/read_bug.ps1"
```

Parse the output for these key fields:
- `Title`, `Description` — What's broken
- `Area` — Which subsystem (Portal, Exchange, AD, DNS, HyperV, API)
- `PageUrl` — The URL where the bug was observed (if provided)
- `Priority` — Severity level
- `ScreenshotData` — Visual evidence (screenshot auto-extracted to PNG if present)
- `ReportedInBuild` — Which build version had the bug

**Update status to InProgress (status-only endpoint — preserves screenshot):**
```bash
curl -sk -X PUT -H "X-Api-Key: fusecp-admin-key-2026" -H "Content-Type: application/json" "http://localhost:5010/api/bugs/{id}/status" -d "{\"status\":\"InProgress\"}"
```

**IMPORTANT:** Use the `/status` endpoint, NOT the full PUT. The full PUT overwrites all fields including ScreenshotData — any omitted nullable fields get set to NULL.

## Phase 3: Investigate

### 3a. Code Investigation

Dispatch `agentic-search` agent with structured three-phase methodology (Reconnaissance → Targeted Search → Synthesis). This agent has built-in output budgets and always produces a final synthesis — unlike generic Explore which can exhaust turns on tool calls with no summary.

```
Task(subagent_type="agentic-search", max_turns=20, description="Investigate bug #{id}: {title}", prompt="
  Search the FuseCP codebase at C:\claude\fusecp-enterprise to find the root cause of this bug.

  Bug: {title}
  Description: {description}
  Area: {area}
  Page URL: {pageUrl}

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

If the bug has `ScreenshotData`:

1. **Screenshot already extracted** — The `read_bug.ps1` script from Phase 2 automatically decodes the screenshot to `C:/claude/fusecp-enterprise/tmp/bug_{id}_screenshot.png`. No additional extraction needed.

2. **View the screenshot** using the Read tool (it supports images):
   ```
   Read(file_path="C:/claude/fusecp-enterprise/tmp/bug_{id}_screenshot.png")
   ```

3. **Navigate to the live page** (if PageUrl is provided and Chrome MCP is available):
   ```
   mcp__claude-in-chrome__tabs_context_mcp()
   mcp__claude-in-chrome__tabs_create_mcp()
   mcp__claude-in-chrome__navigate(url="{pageUrl}", tabId={tabId})
   mcp__claude-in-chrome__browser_take_screenshot(type="png")
   ```

4. **Compare** the bug screenshot with the live page to understand:
   - Is the bug still reproducible?
   - What visual elements are broken?
   - What's the expected vs actual state?

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
Task(subagent_type="bug-hunter", max_turns=20, description="Fix bug #{id}: {title}", prompt="
  Fix this FuseCP bug. The investigation has already been done — go straight to implementing the fix.

  ## Bug Report
  - Title: {title}
  - Description: {description}
  - Area: {area}
  - Page URL: {pageUrl}
  - Priority: {priority}

  ## Investigation Results
  {paste the full investigation summary from Phase 3c — including file paths, line numbers, and suggested fix}

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

**STOP HERE and wait for user confirmation.** Do NOT deploy without explicit approval.

## Phase 7: Commit, PR & Deploy (User-Confirmed)

Only after user says yes:

### 7a. Create hotfix branch and commit

Bug fixes go through the PR process to prevent fixes from being lost when feature branches merge.

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

### 7b. Push and create PR

```bash
cd /c/claude/fusecp-enterprise && git push -u origin hotfix/bug-{id}
```

```bash
gh pr create --title "fix: {title} (Bug #{id})" --body "$(cat <<'EOF'
## Bug Fix

**Bug ID:** #{id}
**Priority:** {priority}
**Area:** {area}

### Root Cause
{root cause description}

### Changes
| File | Change |
|------|--------|
| {path} | {what changed} |

### Testing
- Build: PASS
- Tests: {N} passing

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)
EOF
)"
```

### 7c. Wait for CI, then merge

Wait for `pr-check.yml` to complete (build + test + security scan):

```bash
gh pr checks {pr-number} --watch
```

If CI passes, merge the PR:

```bash
gh pr merge {pr-number} --squash --delete-branch && cd /c/claude/fusecp-enterprise && git checkout main && git pull origin main
```

If CI fails, investigate the failure, fix on the hotfix branch, push again, and re-check.

### 7d. Deploy from main

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

### 7e. Update Bug Status

```bash
curl -sk -X PUT -H "X-Api-Key: fusecp-admin-key-2026" -H "Content-Type: application/json" "http://localhost:5010/api/bugs/{id}/status" -d "{\"status\":\"Fixed\"}"
```

### 7f. Visual Verification (if Chrome available and PageUrl exists)

After deploy, navigate back to the PageUrl and take a screenshot to verify the fix is visible.

### 7g. Cleanup temp files

```bash
rm -f C:/claude/fusecp-enterprise/tmp/bug_{id}*
```

## Phase 8: Next Bug

After completing a fix:

"Bug #{id} fixed and deployed. {N-1} open bugs remaining. Fix the next one?"

If user says yes, loop back to Phase 1.

## Error Handling

- **API unreachable:** "FuseCP API is not responding at localhost:5010. Is the API running?"
- **No open bugs:** "No open bugs found. The bug queue is clear."
- **agentic-search agent fails or returns incomplete:** Fall back to direct investigation (Phase 3a-fallback). Do NOT retry the agent.
- **bug-hunter fails:** Fall back to direct fix in main context (Phase 4-fallback). Do NOT retry the agent.
- **Build failure after 3 attempts:** "Build still failing after 3 fix attempts. Escalating — here's what I've tried: {summary}"
- **Test failure:** "Tests failing after fix. Investigating if these are pre-existing or caused by the fix."
- **CI failure on PR:** Investigate the CI log (`gh pr checks {number}`), fix on the hotfix branch, push again. Do NOT merge a failing PR.
- **Merge conflict:** Rebase the hotfix branch on latest main: `git fetch origin && git rebase origin/main`. Fix any conflicts, then force-push the branch.
- **Deploy failure:** "Deploy failed: {error}. The PR is merged but not deployed. You may need to deploy manually."

## Why PRs for Bug Fixes

Bug fixes MUST go through the PR process (not direct commits to main) because:
1. **Prevents lost fixes:** Feature branches that merge later won't overwrite bug fixes — they must be up-to-date with main before merging.
2. **CI verification:** `pr-check.yml` runs build + tests + security scan before the fix reaches main.
3. **Audit trail:** Each fix has a PR number linking to the bug ID for traceability.
4. **Branch protection:** GitHub's "Require branches to be up-to-date" setting ensures no branch can merge without incorporating all prior main commits (including bug fixes).

## Priority Handling

| Priority | Approach |
|----------|----------|
| Critical | Fix immediately, minimal investigation — speed matters |
| High | Full investigation + fix cycle |
| Medium | Full investigation, consider if test is needed |
| Low | Investigate, propose fix, ask user before implementing |

## Additional Context

$ARGUMENTS
