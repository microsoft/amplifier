# Design Spec: /test-browser — Automated Browser Testing Skill

**Date:** 2026-03-17
**Status:** Approved
**Replaces:** None (new capability; complements `/test-webapp-ui` and `/browser-audit`)

## Problem

Amplifier has fragmented browser capabilities:
- `/test-webapp-ui` — interactive discovery + manual testing
- `/browser-audit` — screenshots + UX scoring + Lighthouse
- `superpowers-chrome` — single tool, auto-capture
- `claude-in-chrome` MCP — 18 tools, rich debugging

No single skill orchestrates these for **automated test runs** with failure classification, auto-fix cycles, pattern learning, and visual reporting.

## Goal

Build `/test-browser` — a unified automated browser testing skill that:
1. Discovers any web app's structure autonomously (visual + structural + API scan)
2. Generates and runs test scenarios with real assertions
3. Classifies failures against a 10-category taxonomy
4. Auto-fixes retryable failures with regression guards
5. Learns timing/selector patterns per domain, persisted across sessions
6. Produces a standalone visual HTML report

## Interface

```
/test-browser <url> [--scope flow1,flow2] [--depth shallow|deep] [--cycles 3] [--report-dir ./reports]
```

| Flag | Default | Purpose |
|------|---------|---------|
| `<url>` | required | Target web app URL |
| `--scope` | all | Comma-separated flow names to test |
| `--depth` | `shallow` | `shallow` = visible page; `deep` = follow links (max 10 pages) |
| `--cycles` | `3` | Max auto-fix retry cycles |
| `--report-dir` | `./reports` | Where to write the HTML report |

## Architecture

Single command file (`.claude/commands/test-browser.md`). No supporting code — all logic in the prompt, orchestrating `claude-in-chrome` MCP tools and dispatching subagents for novel failures.

### File Layout

```
.claude/commands/test-browser.md    <- Skill prompt (orchestrator)
.test-patterns/                     <- Pattern library (per domain)
  fusecp.ergonet.pl.json
  localhost-3000.json
reports/                            <- HTML reports
  fusecp.ergonet.pl-2026-03-17T14-30.html
```

## Phases

### Phase 0: PRE-FLIGHT

| Check | Method | Fail Action |
|-------|--------|-------------|
| Chrome extension connected | `tabs_context_mcp()` | Abort: "Chrome extension not connected" |
| Can create tab | `tabs_create_mcp()` | Abort: "Cannot create browser tab" |
| Target URL reachable | `navigate(url)` + wait 10s + screenshot | Abort: "Target URL unreachable" |
| No bot detection | Screenshot analysis for CAPTCHA | Pause: "Bot detection found. Solve manually, then say 'continue'" |
| Pattern library loadable | Read `.test-patterns/{domain}.json` | Warn: "No pattern library. Starting fresh." (continue) |
| Report dir writable | Check dir exists or create | Abort: "Cannot write to {report-dir}" |

### Phase 1: CONNECT

- `tabs_context_mcp()` to get current state
- `tabs_create_mcp()` for a fresh tab
- `navigate(url, tabId)` to target
- Verify page loads (screenshot + readyState check)

### Phase 2: DISCOVER (Three-Phase)

**2a: Visual Scan**
- Full-page screenshot via `computer(action="screenshot")`
- Claude reasons about the screenshot: app type, layout, login page vs dashboard vs form

**2b: Structural Scan**
- `read_page(filter="interactive")` — all clickable/typeable elements
- `read_page(filter="all", depth=5)` — page structure (headings, landmarks)
- Build element inventory: forms, buttons, links, inputs, dropdowns, modals
- Tag elements with likely purpose

**2c: API Scan**
- `read_network_requests()` — API calls on page load
- Identify patterns: REST endpoints, GraphQL, WebSocket
- Detect auth mechanism: cookie, token header, OAuth redirect

**Output: Site Model**
```json
{
  "url": "https://myapp.com",
  "appType": "SPA|MPA|static",
  "authType": "cookie-session|token|oauth|none",
  "pages": [
    { "path": "/", "type": "login", "elements": [...] }
  ],
  "apiPatterns": ["/api/auth/*", "/api/data/*"]
}
```

If `--depth deep`, navigate links to discover additional pages (max 10).

### Phase 3: PLAN

- Generate test scenarios from site model
- Priority: auth > CRUD > navigation > validation > error states > edge cases
- Load `.test-patterns/{domain}.json` for known timing/selector adjustments
- If `--scope` provided, filter to matching flows

### Phase 4: EXECUTE

Run each scenario step-by-step:
- Before each action: screenshot (baseline)
- Execute via `claude-in-chrome` tools (`find` -> click/type, or `form_input`)
- After each action: screenshot + `read_console_messages` + `read_network_requests`
- Evaluate assertions against captured state
- On failure: classify against taxonomy, capture diagnostic bundle

**Credential handling:** When login wall detected, pause and ask user. Credentials never written to pattern library or reports.

### Phase 5: AUTO-FIX (max `--cycles`)

Apply known patterns -> retry failed scenarios -> regression guard.

If pass count drops after a fix attempt, revert that strategy and mark as harmful.

Novel failures (`ASSERTION_MISMATCH`, `CONSOLE_ERROR`, `NETWORK_FAILURE` with no known pattern) -> dispatch `bug-hunter` subagent (sonnet, 25 turns) with diagnostic bundle.

Max 3 parallel `bug-hunter` agents for novel failures.

### Phase 6: LEARN

- Update `.test-patterns/{domain}.json` with new patterns
- Record timing baselines (page load, modal animation, API response)
- Prune patterns with `confidence < 0.5` or `seen < 2`
- Halve confidence of patterns that caused regressions

### Phase 7: REPORT

Generate standalone HTML file with:
- Summary bar: total/pass/fail/skipped, duration, URL
- Site model: discovered pages, app type, auth type
- Scenario results: expandable cards with steps, pass/fail, screenshots, failure classification
- Auto-fix log: attempts, successes, regressions
- Pattern library diff: new patterns, confidence changes, pruned entries
- Timing dashboard: page load, API response vs baselines

File: `{report-dir}/{domain}-{timestamp}.html`

## Failure Taxonomy (10 Categories)

| Category | Detection | Auto-fix | Retryable |
|----------|-----------|----------|-----------|
| `ELEMENT_NOT_FOUND` | `find` returns 0 matches | Broaden query, `read_page` full tree | Yes |
| `ELEMENT_STALE` | Action on ref fails after prior success | Re-read page, get fresh ref | Yes |
| `NAVIGATION_TIMEOUT` | URL unchanged after 10s | Wait 5s, check blocking requests | Yes (1x) |
| `ASSERTION_MISMATCH` | Expected state not found | Capture diagnostics, no auto-fix | No |
| `CONSOLE_ERROR` | `read_console_messages(onlyErrors)` matches | Log and continue | No |
| `NETWORK_FAILURE` | `read_network_requests` shows 4xx/5xx | Retry once (transient) | Yes (1x) |
| `AUTH_BARRIER` | Login form, redirect to /login, 401/403 | Ask user for credentials | Manual |
| `ASYNC_TIMING` | Element appears on retry with longer wait | Progressive: 500ms->1s->2s->5s | Yes |
| `VISUAL_ANOMALY` | Screenshot shows layout issues | Screenshot + flag | No |
| `INFRA_ERROR` | MCP tool call fails, tab disconnected | Reconnect, retry from checkpoint | Yes (1x) |

## Pattern Library Schema

`.test-patterns/{domain}.json`:
```json
{
  "domain": "example.com",
  "learned": [
    {
      "pattern": "ASYNC_TIMING",
      "selector": ".modal-overlay",
      "fix": "wait_2000ms",
      "confidence": 0.9,
      "seen": 3
    }
  ],
  "baselines": {
    "page_load_ms": 1200,
    "modal_animation_ms": 2000,
    "api_response_ms": 400
  }
}
```

## Agent Allocation

| Phase | Agent | Model | Responsibility |
|-------|-------|-------|----------------|
| Pre-flight & Connect | inline | opus | MCP tool calls, validation |
| Discovery | inline | opus | Visual reasoning, site model |
| Scenario generation | inline | opus | Test planning from site model |
| Execution | inline | opus | Drive chrome tools, assertions |
| Novel failure analysis | bug-hunter | sonnet | Root cause on unclassified failures |
| Report generation | modular-builder | sonnet | Generate HTML report file |
| Pattern library | inline | opus | Update learned patterns |

## Test Plan

- [ ] Pre-flight catches missing Chrome extension (disconnect and run)
- [ ] Pre-flight catches unreachable URL
- [ ] Discovery produces valid site model for SPA (FuseCP)
- [ ] Discovery produces valid site model for static site
- [ ] Auth barrier detected and user prompted
- [ ] ELEMENT_NOT_FOUND triggers broader find query
- [ ] ASYNC_TIMING triggers progressive wait
- [ ] Regression guard reverts harmful fix
- [ ] Pattern library persists across runs
- [ ] HTML report renders correctly with all sections
- [ ] `--scope` filters scenarios correctly
- [ ] `--depth deep` discovers linked pages (max 10)
