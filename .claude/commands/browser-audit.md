---
description: "Audit a deployed web page: navigate, capture screenshots, extract DOM summary, return structured quality report. Use for post-deploy verification or UI testing."
---

# Browser Audit

## Overview

Automated web page audit using the browser-user agent. Navigates to a URL, captures full-page screenshots, extracts DOM structure, and returns a structured report on page health, accessibility, and visual state.

**Announce at start:** "Running browser audit on <url>."

## Usage

```
/browser-audit <url> [--full] [--viewport=mobile|tablet|desktop] [--lighthouse] [--a11y] [--slim]
```

- `<url>` — required, the page to audit (e.g., `https://fusecp.ergonet.pl/`)
- `--full` — capture full-page screenshot (requires superpowers-chrome v1.8.0+)
- `--viewport=mobile` — emulate mobile viewport (375x667, touch enabled)
- `--viewport=tablet` — emulate tablet viewport (768x1024)
- `--viewport=desktop` — default (1920x1080)
- `--lighthouse` — run Lighthouse performance/a11y/SEO audit via Chrome DevTools MCP
- `--a11y` — run accessibility audit via Chrome DevTools MCP
- `--slim` — use DevTools MCP slim mode (navigate + screenshot + JS only — fast, low token cost)

**DevTools MCP flags** require `chrome-devtools` MCP server to be enabled (disabled by default). Enable: edit `.mcp.json`, set `chrome-devtools.disabled` to `false`, restart Claude Code.

## The Process

### Step 1: Parse Arguments

Extract URL and flags from `$ARGUMENTS`. Validate the URL is reachable:

```bash
curl -sI "<url>" | head -1
```

If unreachable, report error and stop.

### Step 2: Get Browser Context

Get current tab state and look for an existing tab with the target URL:
```
mcp__claude-in-chrome__tabs_context_mcp()
```

**Tab reuse logic:** Search the returned tabs for one whose URL matches the target (exact match or same origin+path, ignoring query params and fragments).

- **If matching tab found:** Reuse it. Navigate to the exact target URL to ensure fresh state:
  ```
  mcp__claude-in-chrome__navigate(url="<url>", tabId=<matching_tab_id>)
  ```
- **If no matching tab:** Create a new one:
  ```
  mcp__claude-in-chrome__tabs_create_mcp(url="<url>")
  ```

### Step 3: Set Viewport (if specified)

For mobile/tablet viewports (requires v1.8.0+):
```
mcp__claude-in-chrome__resize_window(width=375, height=667)  # mobile
mcp__claude-in-chrome__resize_window(width=768, height=1024) # tablet
```

### Step 4: Capture Page State

Run these captures in sequence:

1. **Wait for page load:**
```
mcp__claude-in-chrome__javascript_tool(code="document.readyState")
```

2. **Screenshot:**
```
mcp__claude-in-chrome__computer(action="screenshot")
```

3. **Extract page text and structure:**
```
mcp__claude-in-chrome__get_page_text()
```

4. **Read page DOM summary:**
```
mcp__claude-in-chrome__read_page()
```

5. **Check console for errors:**
```
mcp__claude-in-chrome__read_console_messages(pattern="error|warn|exception")
```

6. **Check network failures:**
```
mcp__claude-in-chrome__read_network_requests()
```

### Step 5: Analyze and Report

Synthesize all captures into a structured report:

```markdown
# Browser Audit Report — <url>

## Page Load
- Status: [loaded/error]
- Title: <page title>
- Viewport: <width>x<height>

## Visual State
- Screenshot captured: [yes/no]
- Above-the-fold content: [description of what's visible]
- Layout issues: [any obvious problems]

## Console Health
- Errors: N
- Warnings: N
- [List each error with message]

## Network Health
- Failed requests: N
- Slow requests (>2s): N
- [List each failure with URL and status]

## Content Summary
- Headings found: N
- Forms found: N
- Interactive elements: N
- [Key content visible on page]

## Issues Found
### Critical
- [Issues that indicate broken functionality]

### Warning
- [Issues that degrade experience]

### Info
- [Observations worth noting]

## Verdict: [PASS / WARN / FAIL]
```

### Step 6: Multi-Viewport (if requested)

If `--viewport=mobile` was specified alongside the default desktop audit, run Steps 3-5 again with the mobile viewport and include both results in the report with a comparison section.

### Step 7: Notify (if configured)

If `NTFY_TOPIC` is set, send a notification with the verdict:
```bash
./scripts/notify.sh "Browser Audit" "<url>: <VERDICT>" 3
```

## Arguments

$ARGUMENTS

## Chrome DevTools MCP Audits (when --lighthouse or --a11y)

**Prerequisite:** `chrome-devtools` MCP server must be enabled (disabled by default). If `mcp__chrome-devtools__*` tools are unavailable, report: "Chrome DevTools MCP not enabled. Edit .mcp.json, set chrome-devtools.disabled to false, restart session."

### Lighthouse Audit (--lighthouse)

Navigate to the URL via DevTools MCP, then run Lighthouse:
```
Call: mcp__chrome-devtools__lighthouse(url="<target-url>")
```

Append to the report:
```
## Lighthouse Audit

| Category | Score |
|----------|-------|
| Performance | XX |
| Accessibility | XX |
| Best Practices | XX |
| SEO | XX |

### Key Opportunities
<top 3 performance opportunities from Lighthouse>
```

### Accessibility Audit (--a11y)

```
Call: mcp__chrome-devtools__accessibility_snapshot()
```

Append to the report:
```
## Accessibility Audit

### Issues Found
<list a11y violations with element refs and severity>

### Summary
PASS: X checks | WARN: X checks | FAIL: X checks
```

### Slim Mode (--slim)

When `--slim` is specified, use DevTools MCP in slim mode (3 tools only: navigate, execute JS, screenshot). This is faster and uses fewer tokens. Good for quick post-deploy checks.

## Integration

**Pairs with:**
- `/test-webapp-ui` — More comprehensive UI testing with interaction flows
- `/verify` — Include browser audit as part of verification evidence
- `/finish-branch` — Run audit on deployed staging before PR
- `/fix-bugs` Phase 7g — Post-deploy smoke check

**Tools used:**
- Browser tools (mcp__claude-in-chrome__*) — Screenshots, DOM, console
- Chrome DevTools MCP (mcp__chrome-devtools__*) — Lighthouse, a11y, performance (opt-in)
- No subagents — runs directly in main context

## Requirements

- Chrome 146+ (for DevTools MCP v0.20.0 features)
- Superpowers Chrome plugin (for viewport emulation and full-page screenshots)
- Chrome DevTools MCP server (optional — for --lighthouse and --a11y flags)
- Target URL must be accessible from the dev machine
