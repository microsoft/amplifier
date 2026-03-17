---
description: "Automated browser testing: discover app, generate test scenarios, run with assertions, auto-fix failures, learn patterns, produce visual HTML report."
---

# /test-browser — Automated Browser Testing

## Usage

```
/test-browser <url> [--scope flow1,flow2] [--depth shallow|deep] [--cycles 3] [--report-dir ./reports]
```

| Flag | Default | Purpose |
|------|---------|---------|
| `<url>` | required | Target web app URL |
| `--scope` | all | Comma-separated flow names to test (e.g., `login,dashboard`) |
| `--depth` | `shallow` | `shallow` = current page only; `deep` = follow links, max 10 pages |
| `--cycles` | `3` | Max auto-fix retry cycles |
| `--report-dir` | `./reports` | Where to write the HTML report |

## Arguments

$ARGUMENTS

## Announce

Say: "Starting automated browser test on <url>."

---

## Phase 0: PRE-FLIGHT

Run these checks in order. Abort on critical failures, warn on non-critical.

### 0.1 Chrome Extension

```
Call: mcp__claude-in-chrome__tabs_context_mcp()
```

- **Success**: Report tab group info. Continue.
- **Failure**: ABORT. Say: "Chrome extension not connected. Open Chrome with the Claude extension and click Connect."

### 0.2 Create Test Tab

```
Call: mcp__claude-in-chrome__tabs_create_mcp()
```

Store the returned `tabId` — use this for ALL subsequent tool calls.

- **Failure**: ABORT. Say: "Cannot create browser tab. Check Chrome MCP server status."

### 0.3 Navigate to Target

```
Call: mcp__claude-in-chrome__navigate(url="<target-url>", tabId=<tabId>)
```

Wait 3 seconds, then:

```
Call: mcp__claude-in-chrome__computer(action="screenshot", tabId=<tabId>)
```

- **Page loads**: Continue.
- **Blank/error page**: ABORT. Say: "Target URL unreachable: <url>. Check the URL and network."

### 0.4 Bot Detection Check

Analyze the screenshot from 0.3. Look for:
- CAPTCHA widgets, "I'm not a robot" checkboxes
- "Verify you're human" text
- Cloudflare/Akamai challenge pages

- **No bot detection**: Continue.
- **Bot detection found**: PAUSE. Say: "Bot detection found on <url>. Please solve it manually in the browser, then say 'continue'." Wait for user confirmation before proceeding.

### 0.5 Load Pattern Library

Check if `.test-patterns/<domain>.json` exists (extract domain from URL, replace `:` and `/` with `-` for localhost URLs like `localhost-3000`).

```
Read: .test-patterns/<domain>.json
```

- **File exists**: Parse and load. Report: "Loaded N patterns for <domain>."
- **File missing**: Warn: "No pattern library for <domain>. Starting fresh." Continue.

### 0.6 Report Directory

```bash
mkdir -p <report-dir>
```

- **Success**: Continue.
- **Failure**: ABORT. Say: "Cannot write to <report-dir>."

### Pre-flight Summary

Print:
```
PRE-FLIGHT COMPLETE
  Chrome extension: connected
  Tab: <tabId>
  Target: <url> (loaded in Xs)
  Bot detection: none
  Pattern library: N patterns loaded | starting fresh
  Report dir: <report-dir> (writable)
```

---

## Phase 1: CONNECT

Already done in pre-flight (steps 0.1-0.3). The tab is open and navigated.

Verify page is fully loaded:
```
Call: mcp__claude-in-chrome__javascript_tool(
  action="javascript_exec",
  text="document.readyState",
  tabId=<tabId>
)
```

If not "complete", wait 2s and retry (max 3 times).

---

## Phase 2: DISCOVER

Build a **site model** through three-phase discovery.

### Phase 2a: Visual Scan

Take a screenshot and reason about it:

```
Call: mcp__claude-in-chrome__computer(action="screenshot", tabId=<tabId>)
```

From the screenshot, determine:
- **App type**: SPA, MPA, static site, documentation, e-commerce, admin panel, etc.
- **Current page type**: login, dashboard, landing, form, list/table, detail view
- **Visual state**: loaded normally, error state, loading spinner, empty state
- **Auth state**: logged in, login wall, public content

### Phase 2b: Structural Scan

Get interactive elements:
```
Call: mcp__claude-in-chrome__read_page(tabId=<tabId>, filter="interactive")
```

Get page structure:
```
Call: mcp__claude-in-chrome__read_page(tabId=<tabId>, filter="all", depth=5)
```

Build an **element inventory**:
- Forms (login, search, data entry, settings)
- Buttons (submit, cancel, delete, toggle)
- Links (navigation, external, anchor)
- Inputs (text, email, password, select, checkbox, radio)
- Dynamic elements (modals, dropdowns, accordions, tabs)

Tag each element with its likely purpose based on text, aria-label, placeholder, and surrounding context.

### Phase 2c: API Scan

```
Call: mcp__claude-in-chrome__read_network_requests(tabId=<tabId>)
```

Identify:
- **API patterns**: REST endpoints (`/api/*`), GraphQL (`/graphql`), WebSocket (`ws://`)
- **Auth mechanism**: Cookie headers, Authorization bearer tokens, API key headers
- **Failed requests**: Any 4xx/5xx on initial load (indicates existing issues)

### Site Model Output

Compose a site model (keep in working memory, do not write to file):

```
SITE MODEL
  URL: <url>
  App type: <SPA|MPA|static>
  Auth type: <cookie|token|oauth|none>
  Auth state: <logged-in|login-wall|public>
  Pages discovered: N
  Interactive elements: N
  API endpoints: N
  Existing issues: [any failed requests or console errors on load]
```

### Deep Discovery (--depth deep)

If `--depth deep` is specified:

1. Collect all navigation links from the structural scan
2. Visit up to 10 unique internal pages (same origin)
3. For each page: screenshot + `read_page(filter="interactive")` + `read_network_requests`
4. Add discovered pages to the site model
5. Return to the original URL when done

---

## Phase 3: PLAN

Generate test scenarios from the site model. Each scenario is a named sequence of steps with assertions.

### Scenario Priority

Generate scenarios in this priority order:

1. **Auth flows** (if login wall detected): login with valid creds, login with invalid creds, logout, session behavior
2. **CRUD operations**: create/read/update/delete on any forms or data tables found
3. **Navigation**: all nav links reachable, no dead ends, back button works, breadcrumbs accurate
4. **Input validation**: empty required fields, invalid email format, boundary values, special characters
5. **Error states**: trigger 404 (navigate to `/nonexistent`), test form submission without required fields
6. **Edge cases**: rapid double-click on buttons, browser resize, very long text input

### Scope Filtering

If `--scope` is provided, only generate scenarios whose flow name matches one of the provided values. For example `--scope login,navigation` generates only auth and navigation scenarios.

### Apply Known Patterns

Before execution, apply any timing adjustments from the pattern library:
- If a pattern says `.modal-overlay` needs 2000ms wait, pre-configure that delay
- If a pattern says a selector was previously stale, use `find` with natural language instead

### Scenario Format

For each scenario, define internally:
```
Scenario: <name>
Flow: <flow-category>
Priority: <1-6>
Steps:
  1. [action] on [target] -> [assertion]
  2. [action] on [target] -> [assertion]
  ...
```

Report to user: "Generated N test scenarios across M flows. Starting execution."

---

## Phase 4: EXECUTE

Run each scenario. Track results in a results table.

### Per-Step Execution Protocol

For EACH step in EACH scenario:

1. **Pre-action screenshot**:
   ```
   Call: mcp__claude-in-chrome__computer(action="screenshot", tabId=<tabId>)
   ```

2. **Find target element** (prefer natural language `find` over hardcoded selectors):
   ```
   Call: mcp__claude-in-chrome__find(query="<element description>", tabId=<tabId>)
   ```

3. **Execute action**:
   - Click: `mcp__claude-in-chrome__computer(action="left_click", ref="<ref>", tabId=<tabId>)`
   - Type: `mcp__claude-in-chrome__form_input(ref="<ref>", value="<text>", tabId=<tabId>)`
   - Navigate: `mcp__claude-in-chrome__navigate(url="<url>", tabId=<tabId>)`

4. **Post-action capture** (run in parallel where possible):
   ```
   Call: mcp__claude-in-chrome__computer(action="screenshot", tabId=<tabId>)
   Call: mcp__claude-in-chrome__read_console_messages(tabId=<tabId>, pattern="error|exception|warn")
   Call: mcp__claude-in-chrome__read_network_requests(tabId=<tabId>, clear=true)
   ```

5. **Evaluate assertions**:
   - `url_changed`: Check current URL via `javascript_tool(text="window.location.href")`
   - `element_visible`: Use `find` or `read_page` to verify element exists
   - `text_present`: Use `get_page_text` and search for expected string
   - `no_console_errors`: Check console messages for errors
   - `network_success`: Check network requests for expected endpoint with 2xx status
   - `network_called`: Verify a specific API endpoint was hit

6. **On failure**: Classify against the 10-category taxonomy (see Phase 5). Capture a **diagnostic bundle**:
   - Screenshot (post-action)
   - Console messages
   - Network requests
   - DOM state (`read_page` around the failing element)
   - The exact assertion that failed and why

### Credential Handling

When an `AUTH_BARRIER` is detected during execution:

1. STOP execution.
2. Say: "Auth barrier detected at <url>. Please provide test credentials to continue, or say 'skip' to skip auth-gated flows."
3. If user provides credentials: use them via `form_input` for login, then continue.
4. If user says 'skip': mark all auth-gated scenarios as SKIPPED.
5. **NEVER** write credentials to the pattern library, reports, or any file.

### Progress Reporting

After every 5 scenarios (or after each scenario if fewer than 5 total), print a progress line:
```
Progress: 8/15 scenarios | 6 passed | 1 failed | 1 skipped
```

---

## Phase 5: AUTO-FIX

After initial execution, if there are failures, run up to `--cycles` fix-and-retry rounds.

### Failure Classification

Classify each failure against this taxonomy:

| Category | Detection Signal |
|----------|-----------------|
| `ELEMENT_NOT_FOUND` | `find` returns 0 matches, `read_page` ref missing |
| `ELEMENT_STALE` | Action on ref fails after it previously existed |
| `NAVIGATION_TIMEOUT` | URL unchanged after 10s, readyState never "complete" |
| `ASSERTION_MISMATCH` | Expected text/element/URL/network state not found |
| `CONSOLE_ERROR` | JS errors captured during or after action |
| `NETWORK_FAILURE` | API returned 4xx/5xx on expected endpoint |
| `AUTH_BARRIER` | Login form, redirect to /login, 401/403 response |
| `ASYNC_TIMING` | Element appears when retried with longer wait |
| `VISUAL_ANOMALY` | Screenshot shows broken layout, overlapping elements |
| `INFRA_ERROR` | MCP tool call itself fails, tab disconnected |

### Auto-Fix Strategies

| Category | Strategy | Max Retries |
|----------|----------|-------------|
| `ELEMENT_NOT_FOUND` | Re-run `find` with broader/alternate query. If still fails, `read_page(filter="all")` and search manually | 2 |
| `ELEMENT_STALE` | `read_page` fresh, get new ref, retry same action | 2 |
| `NAVIGATION_TIMEOUT` | Wait 5s, retry. Check `read_network_requests` for stuck/pending requests | 1 |
| `ASSERTION_MISMATCH` | NO auto-fix. This is likely a real app bug. Keep diagnostic bundle for report | 0 |
| `CONSOLE_ERROR` | Log and continue. Not a test issue — it's an app issue | 0 |
| `NETWORK_FAILURE` | Retry once (could be transient). If persists, flag as app issue | 1 |
| `AUTH_BARRIER` | Ask user for credentials (handled in Phase 4) | Manual |
| `ASYNC_TIMING` | Progressive wait: 500ms -> 1s -> 2s -> 5s between action and assertion | 4 |
| `VISUAL_ANOMALY` | Screenshot + flag for report. No auto-fix | 0 |
| `INFRA_ERROR` | `tabs_context_mcp()` to reconnect. Retry from last successful step | 1 |

### Regression Guard

After EACH fix cycle:
1. Re-run ALL scenarios (not just the fixed ones)
2. Compare pass count to previous cycle
3. **If pass count dropped**: Revert the fix strategy that caused it. Mark that strategy as harmful in working memory (do NOT apply it again this session). Report: "Regression detected: fix for <category> on <element> caused N new failures. Reverted."
4. **If pass count unchanged or improved**: Accept the fix. Continue to next cycle.

### Novel Failure Dispatch

Failures that are:
- Classified as `ASSERTION_MISMATCH`, `CONSOLE_ERROR`, or `NETWORK_FAILURE`
- AND do not match any known pattern in the library

Dispatch to `bug-hunter` subagent for analysis:

```
Agent(subagent_type="bug-hunter", model="sonnet", description="Analyze novel test failure",
  prompt="
    Analyze this browser test failure and determine root cause.

    Scenario: <scenario-name>
    Step: <step-description>
    Category: <failure-category>
    URL: <current-url>

    Diagnostic bundle:
    - Assertion: <what was expected vs what was found>
    - Console errors: <captured errors>
    - Network: <relevant request/response>
    - DOM context: <read_page output around failing element>

    Determine:
    1. Is this an app bug or a test issue?
    2. Root cause analysis (2-3 sentences)
    3. Suggested action: fix test approach, report as app bug, or skip

    Return structured analysis (MAX 200 words).
  ")
```

Dispatch up to 3 `bug-hunter` agents in parallel for multiple novel failures.

---

## Phase 6: LEARN

After all cycles complete, update the pattern library.

### Update Patterns

For each failure that was successfully auto-fixed:
1. Check if a matching pattern already exists in `.test-patterns/<domain>.json`
2. **Existing pattern**: Increment `seen` count, recalculate `confidence` (successful fix = +0.1, max 1.0)
3. **New pattern**: Add with `confidence: 0.6`, `seen: 1`

For each fix that caused a regression:
1. Find the pattern and halve its `confidence`
2. If `confidence < 0.3`, remove it

### Prune

Remove patterns where:
- `confidence < 0.5` AND `seen < 2`
- Pattern is older than 30 runs without being triggered

### Update Baselines

Record timing measurements from this run:
- `page_load_ms`: time from navigate to readyState="complete"
- Average API response time for observed endpoints
- Animation/transition delays that required waits

Write the updated library:
```
Write: .test-patterns/<domain>.json
```

Report: "Pattern library updated: N new patterns, M updated, K pruned."

---

## Phase 7: REPORT

Generate a standalone HTML report file.

### Report Generation

Dispatch a `modular-builder` subagent to generate the HTML:

```
Agent(subagent_type="modular-builder", model="sonnet", description="Generate test browser HTML report",
  prompt="
    Generate a standalone HTML report for an automated browser test run.
    The file must be completely self-contained (inline CSS, no external deps).

    ## Data

    URL: <url>
    App type: <from site model>
    Duration: <total time>
    Timestamp: <ISO timestamp>

    Results:
    <for each scenario: name, flow, priority, steps with pass/fail, failure classifications, screenshots referenced>

    Auto-fix log:
    <cycles run, fixes attempted, regressions detected>

    Pattern library diff:
    <new patterns, updated patterns, pruned patterns>

    Timing:
    <page load, API response, compared to baselines>

    ## Report Structure

    Build an HTML page with these sections:

    1. **Header**: URL, timestamp, duration, overall verdict (PASS/WARN/FAIL)
    2. **Summary bar**: Total scenarios, passed (green), failed (red), skipped (gray), auto-fixed (blue)
    3. **Site model card**: App type, auth type, pages discovered, elements found
    4. **Scenario results**: Expandable cards for each scenario
       - Each card: scenario name, flow badge, pass/fail status
       - Expanded: step-by-step with action, assertion, result, failure classification if failed
       - Color coding: green=pass, red=fail, yellow=auto-fixed, gray=skipped
    5. **Auto-fix log**: Table of fix attempts with strategy, result, regression status
    6. **Pattern library diff**: What was learned (new/updated/pruned)
    7. **Timing dashboard**: Bar chart comparing this run to baselines
    8. **Footer**: 'Generated by Amplifier /test-browser' + timestamp

    ## Style

    Use a clean, professional design:
    - Dark header bar with white text
    - Card-based layout with subtle shadows
    - Monospace font for technical data
    - Color palette: #10B981 (pass), #EF4444 (fail), #F59E0B (warning), #6B7280 (skipped), #3B82F6 (auto-fixed)
    - Responsive: works on desktop and tablet

    ## Verdict Logic

    - PASS: all scenarios passed (including after auto-fix)
    - WARN: some scenarios failed but none are priority 1-2 (auth/CRUD)
    - FAIL: any priority 1-2 scenario failed

    Write the file to: <report-dir>/<domain>-<timestamp>.html
    Return the file path.
  ")
```

### Open Report

After the report is generated, open it in the browser:

```
Call: mcp__claude-in-chrome__tabs_create_mcp()
Call: mcp__claude-in-chrome__navigate(url="file:///<report-path>", tabId=<new-tabId>)
```

### Final Summary

Print to terminal:
```
TEST COMPLETE — <url>
  Verdict: <PASS|WARN|FAIL>
  Scenarios: N total | P passed | F failed | S skipped | A auto-fixed
  Cycles: C fix cycles run
  Patterns: N new | M updated | K pruned
  Report: <report-path>
```

---

## Integration

**Pairs with:**
- `/browser-audit` — run after `/test-browser` for UX scoring and Lighthouse
- `/verify` — include test-browser results as verification evidence
- `/finish-branch` — run before PR to catch regressions
- `/test-webapp-ui` — manual follow-up on failures `/test-browser` can't auto-fix

**Does NOT replace:**
- `/test-verified` — that's for .NET/pytest test suites, not browser interaction
- `/test-siem` — that's for SIEM-specific test pipelines

## Requirements

- Chrome with Claude-in-Chrome extension connected
- `claude-in-chrome` MCP server configured in `.mcp.json`
- Target URL accessible from the dev machine
