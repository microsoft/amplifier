# Docs Site Generation Pipeline v2 — Design Spec

## Problem

The v1 generation pipeline (`generate.ps1` + `claude --print`) has three critical issues:
1. **15% failure rate** — `claude --print` outputs descriptions instead of HTML because it lacks a system prompt
2. **Slow** — sequential generation, ~60 min for 36 pages (18 EN + 18 PL)
3. **Encoding bugs** — PowerShell `Set-Content` produces garbled UTF-8 characters

## Goal

Replace with a Python pipeline using `claude_code_sdk` that:
- Uses system_prompt to guarantee raw HTML output (fixing the 15% failure)
- Generates 4 pages concurrently (~3 min total)
- Produces both EN + PL in a single call (halving API usage)
- Validates output before replacing live files
- Handles UTF-8 natively

## Architecture

### generate.py (replaces generate.ps1)

Python script managed by uv. Runs via `uv run generate.py`.

**Flow:**
1. Pull latest amplifier repo (`git pull`)
2. Read manifest.json, expand source globs, compute SHA256 hashes
3. Compare to stored hashes — build list of changed pages (skip unchanged unless --force)
4. Check global_triggers — if changed, regenerate all
5. Batch pages into groups of 4
6. For each batch, run 4 concurrent `claude_code` calls via asyncio
7. Each call uses:
   - system_prompt: "YOU ARE AN HTML PAGE GENERATOR..." (guarantees raw HTML)
   - prompt: design system + page prompt + "Output EN version, then <!-- LANG:PL -->, then PL version"
   - model: "sonnet"
   - max_turns: 1
8. Split response at `<!-- LANG:PL -->` separator → EN and PL content
9. Validate each half:
   - Starts with `<!DOCTYPE html>`
   - Contains `site-sidebar` (has navigation)
   - Size > 5KB (not a description)
   - If invalid: retry up to 3 times
   - If all retries fail: keep previous version, log error
10. Write valid content to temp files, then atomic rename to live paths
11. Regenerate LLM files (llms.txt, llms-full.txt, llms-structured.json)
12. Update manifest.json with new hashes
13. Log everything to logs/

**CLI interface:**
```
uv run generate.py                    # incremental (only changed)
uv run generate.py --force            # regenerate all
uv run generate.py --pages home,agents  # specific pages only
uv run generate.py --skip-translation # EN only
uv run generate.py --dry-run          # show what would regenerate
```

### webhook_server.py (replaces webhook-listener.ps1)

FastAPI server on localhost:9099.

**Endpoints:**
- POST /amplifier-docs-rebuild — Gitea webhook handler
  - Validates HMAC-SHA256 from X-Gitea-Signature header
  - Checks action=closed + merged=true
  - Spawns `uv run generate.py --force` as subprocess
  - Returns 200 immediately
- GET /health — returns {"status": "ok", "last_run": "...", "pages": 18}
- GET /status — returns last generation log summary

**Runs as:** Windows Service via NSSM or scheduled task on boot.

### Dependencies (pyproject.toml)

```toml
[project]
name = "amplifier-docs-generator"
version = "2.0.0"
requires-python = ">=3.11"
dependencies = [
    "claude-code-sdk>=0.1",
    "fastapi>=0.115",
    "uvicorn>=0.34",
]
```

Managed by uv at C:\claude\amplifier-docs\

## Key Design Decisions

### System Prompt (fixes 15% failure rate)
```
YOU ARE AN HTML PAGE GENERATOR. Your ONLY output is raw HTML.

RULES:
- Output starts with <!DOCTYPE html> — NOTHING before it
- Output ends with </html> — NOTHING after it
- No explanations, no descriptions, no markdown, no code fences
- The entire response is raw HTML that can be saved as a .html file

After the EN HTML, output exactly this separator on its own line:
<!-- LANG:PL -->
Then output the complete Polish translation of the same page.
```

### Dual Language Output
Single API call produces both EN and PL, split by `<!-- LANG:PL -->` separator.
If separator not found: EN portion is the whole response, PL is skipped for that page (retry next run).

### Validation Pipeline
```
API response
  → split at <!-- LANG:PL -->
  → validate EN (DOCTYPE + sidebar + >5KB)
  → validate PL (DOCTYPE + sidebar + >5KB)
  → write to temp files
  → atomic rename to live paths
  → update manifest hash
```

If validation fails: retry up to 3 times with same prompt.
If all retries fail: log error, keep previous live version, continue to next page.

### Atomic File Writes
Write to `<path>.tmp`, then `os.replace()` to final path. This prevents serving partial/broken files if the process crashes mid-write.

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| C:\claude\amplifier-docs\generate.py | Create | Main generation script |
| C:\claude\amplifier-docs\webhook_server.py | Create | FastAPI webhook listener |
| C:\claude\amplifier-docs\pyproject.toml | Create | Python project + dependencies |
| C:\claude\amplifier-docs\generate.ps1 | Keep (archive) | Kept as fallback, renamed to generate.ps1.bak |
| C:\claude\amplifier-docs\webhook-listener.ps1 | Keep (archive) | Kept as fallback, renamed |
| C:\claude\amplifier-docs\manifest.json | Modify | Same format, no changes needed |

## Performance

| Metric | v1 (PowerShell) | v2 (Python) |
|--------|-----------------|-------------|
| 18 pages (EN+PL) | ~60 min | ~3 min |
| API calls | 36 (18 EN + 18 PL) | 18 (dual output) |
| Failure rate | ~15% | <1% (system prompt) |
| Encoding issues | Frequent | None (native UTF-8) |
| Parallelism | Sequential | 4 concurrent |

## Test Plan

- [ ] `uv run generate.py --dry-run` shows correct changed pages
- [ ] `uv run generate.py --force --pages home` generates valid EN+PL home page
- [ ] Generated HTML starts with <!DOCTYPE html>
- [ ] Generated HTML contains site-sidebar navigation
- [ ] Generated HTML size > 5KB
- [ ] PL section has lang="pl" and Polish text
- [ ] EN/PL language switcher links are correct
- [ ] `uv run generate.py --force` generates all 18 pages in <5 min
- [ ] Validation rejects descriptions (text not starting with <!DOCTYPE)
- [ ] Failed validation keeps previous version
- [ ] webhook_server.py starts on localhost:9099
- [ ] /health endpoint returns status
- [ ] POST with valid HMAC triggers generation
- [ ] POST with invalid HMAC returns 403
- [ ] Scheduled task starts webhook_server.py on boot
