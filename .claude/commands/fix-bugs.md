---
description: "Autonomous bug-fixing pipeline for FuseCP. Fetches open bugs from the portal API, investigates with agentic-search + visual analysis, fixes with bug-hunter, builds/tests, and deploys with user confirmation."
---

# FuseCP Bug Fix Pipeline

## Overview

Autonomous bug-fixing workflow that processes FuseCP bug reports one at a time. Fetches bugs from the portal's built-in bug reporting API, investigates using code search and visual comparison, implements fixes, and deploys with user confirmation.

**Announce at start:** "Starting FuseCP bug fix pipeline. Checking for open bugs..."

## Prerequisites

- FuseCP API must be running at `http://localhost:5010`
- FuseCP Portal must be running at `https://fusecp.ergonet.pl`
- Working directory should be `C:\claude\fusecp-enterprise` (or the Amplifier root — API calls work from anywhere)

## API Configuration

```
API_BASE=http://localhost:5010
API_KEY=fusecp-admin-key-2026
AUTH_HEADER="X-Api-Key: fusecp-admin-key-2026"
```

All curl commands use: `curl -sk -H "X-Api-Key: fusecp-admin-key-2026"`

## Phase 1: Fetch Open Bugs

```bash
curl -sk -H "X-Api-Key: fusecp-admin-key-2026" "http://localhost:5010/api/bugs?status=Open"
```

Parse the JSON response. If no open bugs, report "No open bugs found" and stop.

**Sort by priority:** Critical > High > Medium > Low, then by ReportedAt (oldest first within same priority).

**Present to user:**
```
Found N open bugs:

| # | ID | Priority | Area | Title | Reported |
|---|-----|----------|------|-------|----------|
| 1 | 42  | Critical | Portal | Login page crashes on submit | 2026-02-15 |
| 2 | 38  | High     | Exchange | Mailbox creation fails silently | 2026-02-14 |

Working on #1 (highest priority). Say "skip" to pick a different one.
```

## Phase 2: Load Bug Details

```bash
curl -sk -H "X-Api-Key: fusecp-admin-key-2026" "http://localhost:5010/api/bugs/{id}"
```

**Extract key fields:**
- `Title`, `Description` — What's broken
- `Area` — Which subsystem (Portal, Exchange, AD, DNS, HyperV, API)
- `PageUrl` — The URL where the bug was observed (if provided)
- `Priority` — Severity level
- `ScreenshotData` / `ScreenshotMimeType` — Visual evidence (Base64, if provided)
- `ReportedInBuild` — Which build version had the bug

**Update status to InProgress:**
```bash
curl -sk -X PUT -H "X-Api-Key: fusecp-admin-key-2026" -H "Content-Type: application/json" \
  "http://localhost:5010/api/bugs/{id}" \
  -d '{"bugId":{id},"title":"{title}","description":"{description}","status":"InProgress","priority":"{priority}","area":"{area}"}'
```

## Phase 3: Investigate

### 3a. Code Investigation

Dispatch `agentic-search` to understand the affected code area:

```
Task(subagent_type="agentic-search", max_turns=12, description="Investigate bug #{id} code area", prompt="
  Search the FuseCP codebase at C:\claude\fusecp-enterprise to answer:

  Bug: {title}
  Description: {description}
  Area: {area}
  Page URL: {pageUrl}

  Find:
  1. The Blazor component/page that handles this URL (look in src/FuseCP.Portal/Components/)
  2. The API endpoint(s) that the page calls
  3. The service/repository layer that processes the request
  4. Any recent changes to these files (git log --oneline -5 -- <file>)

  The ctags index is at C:\claude\fusecp-enterprise\tags.

  Area-to-code mapping:
  - Portal → src/FuseCP.Portal/Components/Pages/
  - Exchange → src/FuseCP.Providers.Exchange/ and Endpoints/ExchangeEndpoints.cs
  - AD → src/FuseCP.Providers.AD/ and Endpoints/ADEndpoints.cs
  - DNS → src/FuseCP.Providers.DNS/ and Endpoints/DNSEndpoints.cs
  - HyperV → src/FuseCP.Providers.HyperV/ and Endpoints/HyperVEndpoints.cs
  - API → src/FuseCP.EnterpriseServer/Endpoints/
")
```

### 3b. Visual Investigation (when screenshot exists)

If the bug has `ScreenshotData`:

1. **Save the screenshot** to a temp file for viewing:
   ```bash
   # Decode Base64 screenshot from API response
   echo "{screenshotData}" | base64 -d > /tmp/bug_{id}_screenshot.png
   ```

2. **View the screenshot** using the Read tool (it supports images):
   ```
   Read(file_path="/tmp/bug_{id}_screenshot.png")
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
**Root area:** {file:line references from agentic-search}
**Visual analysis:** {screenshot comparison findings, or "No screenshot provided"}
**Hypothesis:** {likely root cause based on code + visual evidence}
**Affected files:** {list from agentic-search}
```

## Phase 4: Fix

Dispatch `bug-hunter` with the full investigation context:

```
Task(subagent_type="bug-hunter", max_turns=15, description="Fix bug #{id}: {title}", prompt="
  Fix this FuseCP bug. The investigation has already been done — go straight to implementing the fix.

  ## Bug Report
  - Title: {title}
  - Description: {description}
  - Area: {area}
  - Page URL: {pageUrl}
  - Priority: {priority}

  ## Investigation Results
  {paste the investigation summary from Phase 3c}

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

## Phase 5: Build and Test

After the fix is applied:

```bash
cd /c/claude/fusecp-enterprise && dotnet build --no-incremental 2>&1 | tail -5
```

If build fails, fix build errors and retry (max 3 attempts).

```bash
cd /c/claude/fusecp-enterprise && dotnet test --no-build --verbosity quiet 2>&1 | tail -10
```

If tests fail, investigate and fix (dispatch bug-hunter again if needed).

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
1. Commit changes: `fix: {title} (Bug #{id})`
2. Deploy Portal/API to IIS
3. Mark bug as Fixed in the system
```

**STOP HERE and wait for user confirmation.** Do NOT deploy without explicit approval.

## Phase 7: Deploy (User-Confirmed)

Only after user says yes:

### 7a. Commit
```bash
cd /c/claude/fusecp-enterprise
git add {changed-files}
git commit -m "fix: {title} (Bug #{id})"
```

### 7b. Deploy

Determine what to deploy based on changed files:

- **Portal files changed** (`src/FuseCP.Portal/`):
  ```bash
  powershell -Command "Stop-WebAppPool -Name 'FuseCP_Portal'"
  cd /c/claude/fusecp-enterprise/src/FuseCP.Portal
  dotnet publish --configuration Release --output /c/FuseCP/Portal
  powershell -Command "Start-WebAppPool -Name 'FuseCP_Portal'"
  ```

- **API files changed** (`src/FuseCP.EnterpriseServer/`):
  ```bash
  powershell -Command "Stop-WebAppPool -Name 'FuseCP_API'"
  cd /c/claude/fusecp-enterprise/src/FuseCP.EnterpriseServer
  dotnet publish --configuration Release --output /c/FuseCP/EnterpriseServer
  powershell -Command "Start-WebAppPool -Name 'FuseCP_API'"
  ```

- **Provider/Database changes**: Deploy API (providers are part of the API assembly).

### 7c. Update Bug Status

```bash
curl -sk -X PUT -H "X-Api-Key: fusecp-admin-key-2026" -H "Content-Type: application/json" \
  "http://localhost:5010/api/bugs/{id}" \
  -d '{"bugId":{id},"title":"{title}","description":"{description}","status":"Fixed","priority":"{priority}","area":"{area}"}'
```

### 7d. Visual Verification (if Chrome available and PageUrl exists)

After deploy, navigate back to the PageUrl and take a screenshot to verify the fix is visible.

## Phase 8: Next Bug

After completing a fix:

"Bug #{id} fixed and deployed. {N-1} open bugs remaining. Fix the next one?"

If user says yes, loop back to Phase 1.

## Error Handling

- **API unreachable:** "FuseCP API is not responding at localhost:5010. Is the API running?"
- **No open bugs:** "No open bugs found. The bug queue is clear."
- **Build failure after 3 attempts:** "Build still failing after 3 fix attempts. Escalating — here's what I've tried: {summary}"
- **Test failure:** "Tests failing after fix. Investigating if these are pre-existing or caused by the fix."
- **Deploy failure:** "Deploy failed: {error}. The commit is saved but not deployed. You may need to deploy manually."

## Priority Handling

| Priority | Approach |
|----------|----------|
| Critical | Fix immediately, minimal investigation — speed matters |
| High | Full investigation + fix cycle |
| Medium | Full investigation, consider if test is needed |
| Low | Investigate, propose fix, ask user before implementing |

## Additional Context

$ARGUMENTS
