---
description: "Audit a deployed web page: navigate, capture screenshots, extract DOM summary, return structured quality report. Use for post-deploy verification or UI testing."
---

# Browser Audit

## Overview

Automated web page audit using the browser-user agent. Navigates to a URL, captures full-page screenshots, extracts DOM structure, and returns a structured report on page health, accessibility, and visual state.

**Announce at start:** "Running browser audit on <url>."

## Usage

```
/browser-audit <url> [--full] [--viewport=mobile|tablet|desktop]
```

- `<url>` — required, the page to audit (e.g., `https://fusecp.ergonet.pl/`)
- `--full` — capture full-page screenshot (requires superpowers-chrome v1.8.0+)
- `--viewport=mobile` — emulate mobile viewport (375x667, touch enabled)
- `--viewport=tablet` — emulate tablet viewport (768x1024)
- `--viewport=desktop` — default (1920x1080)

## The Process

### Step 1: Parse Arguments

Extract URL and flags from `$ARGUMENTS`. Validate the URL is reachable:

```bash
curl -sI "<url>" | head -1
```

If unreachable, report error and stop.

### Step 2: Get Browser Context

First, get current tab state:
```
mcp__claude-in-chrome__tabs_context_mcp()
```

Create a new tab for the audit (never reuse existing tabs):
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

## Integration

**Pairs with:**
- `/test-webapp-ui` — More comprehensive UI testing with interaction flows
- `/verify` — Include browser audit as part of verification evidence
- `/finish-branch` — Run audit on deployed staging before PR

**Agents used:**
- Browser tools (mcp__claude-in-chrome__*) — All captures
- No subagents — this command runs directly in main context (fast, low overhead)

## Requirements

- Superpowers Chrome plugin v1.8.0+ (for viewport emulation and full-page screenshots)
- Chrome browser running with DevTools Protocol enabled
- Target URL must be accessible from the dev machine
