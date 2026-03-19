# Exchange EWS MCP — Production Readiness Upgrade

**Date:** 2026-03-19
**Status:** Approved
**Project:** C:\claude\exchange-ews-mcp\

## Problem

The exchange-ews MCP server works in the lab (Kerberos auth, self-signed certs, FuseCP OU scope) but cannot be used for personal mailbox on production Exchange Server because:
1. Auth is hardcoded to Kerberos (requires domain-joined machine)
2. SSL verification is globally disabled
3. OU scope is hardcoded to FuseCP
4. No bulk operations for managing large mailboxes
5. Missing personal productivity tools (reply, forward, drafts, attachments)
6. No proper dependency management (no pyproject.toml)

## Goal

Make exchange-ews MCP production-ready for personal mailbox use while maintaining full backward compatibility with the lab environment. Add bulk operations for mailbox cleanup and personal productivity tools.

## Design Decisions

1. **Auth**: Configurable via `auth_type` in config.json — "ntlm", "basic", "kerberos", or "auto" (default). Auto mode tries NTLM first, falls back to Basic.
2. **SSL**: `verify_ssl` config option, default `true`. Lab sets it to `false`.
3. **Scope**: `scope_ou` optional in config.json. Present = scoped, absent = unrestricted.
4. **Credentials**: Config file only (`~/.config/exchange-ews-mcp/config.json`). No env var override.
5. **Bulk safety**: Bulk tools return preview count first, require `confirm: true` to execute.
6. **Code structure**: Stays single-file (server.py). Expected ~1200 lines after changes.
7. **Backward compatibility**: Lab config just adds `"auth_type": "kerberos"` and `"verify_ssl": false`.

## Config Examples

### Production (personal mailbox)
```json
{
  "server": "mail.yourdomain.com",
  "username": "DOMAIN\\your.name",
  "password": "your-password",
  "verify_ssl": true
}
```

### Lab (existing setup, updated)
```json
{
  "server": "exchangelab.lab.ergonet.pl",
  "auth_type": "kerberos",
  "verify_ssl": false,
  "scope_ou": "lab.ergonet.pl/FuseCP"
}
```

## Changes

### 1. Auth Refactor
- Replace hardcoded Kerberos monkey-patch with configurable auth in `get_account()`
- Support: ntlm (username/password), basic (username/password), kerberos (ticket), auto (try ntlm → basic)
- Kerberos imports conditional (only when auth_type is kerberos)
- `get_config()` validates required fields per auth type (username/password required for ntlm/basic)

### 2. SSL Configurable
- Remove global `NoVerifyHTTPAdapter` hack
- Apply `NoVerifyHTTPAdapter` only when `verify_ssl: false` in config
- Default: SSL verification enabled

### 3. Scope Optional
- `scope_ou` in config: if present, could be used for documentation/logging
- Actual scope enforcement stays on Exchange server side (RBAC)
- No client-side OU filtering needed

### 4. New Tools — Personal Productivity (P1-P3)

| Tool | Params | Behavior |
|------|--------|----------|
| `reply` | email, message_id, body, reply_all (bool, default false) | Reply to message, preserves thread |
| `forward` | email, message_id, to, body (optional) | Forward with original content |
| `download_attachment` | email, message_id, attachment_name (optional) | Returns base64 + saves to temp dir |
| `create_draft` | email, to, subject, body, cc (optional) | Creates draft, returns draft ID |
| `send_draft` | email, draft_id | Sends existing draft |
| `list_drafts` | email, limit (default 10) | Lists drafts |

### 5. New Tools — Bulk Operations

| Tool | Params | Behavior |
|------|--------|----------|
| `bulk_move` | email, filter (subject/sender/date_before/date_after), target_folder, confirm (bool) | Move matching messages. Without confirm: returns count preview only |
| `bulk_delete` | email, filter, permanent (bool, default false), confirm (bool) | Delete matching. soft=Deleted Items, hard=permanent. Without confirm: preview |
| `bulk_archive` | email, older_than_days, target_folder (default "Archive"), confirm (bool) | Archive by age. Without confirm: preview |

### 6. Existing Tool Fixes

| Fix | Details |
|-----|---------|
| `search` across folders | Add optional `folder` param, default searches all folders |
| `move_message` any folder | Search all folders for message_id, not just inbox |
| `get_mailbox_size` performance | Use exchangelib folder properties instead of iterating items |
| `verify_*` hardcoded sleeps | Replace `time.sleep()` with configurable polling intervals |

### 7. Project Modernization

- Add `pyproject.toml` with uv-managed dependencies
- `exchangelib>=5.0` required, `requests-kerberos>=0.14` optional (kerberos only)
- Update README with all 21 tools, both config examples, Claude Desktop + Claude Code registration
- Fix README architecture diagram (multi-auth, not NTLM-only)
- Add basic email format validation on input params

## Files Changed

| File | Change |
|------|--------|
| `C:\claude\exchange-ews-mcp\server.py` | Auth refactor, SSL config, 8 new tools, 4 existing fixes |
| `C:\claude\exchange-ews-mcp\config.example.json` | Updated with all config options |
| `C:\claude\exchange-ews-mcp\pyproject.toml` | NEW — uv-managed dependencies |
| `C:\claude\exchange-ews-mcp\README.md` | Full rewrite — 21 tools, both configs, setup instructions |

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Auth refactor + SSL + config | modular-builder | Rewrite get_account(), config parsing, SSL handling |
| New productivity tools | modular-builder | reply, forward, download_attachment, drafts |
| New bulk tools | modular-builder | bulk_move, bulk_delete, bulk_archive with safety preview |
| Existing fixes | modular-builder | search all-folders, move all-folders, mailbox_size perf, sleep removal |
| Project setup | modular-builder | pyproject.toml, README rewrite |
| Testing | test-coverage | Test against lab Exchange (verify no regressions) |
| Cleanup | post-task-cleanup | Final hygiene pass |

## Test Plan

- [ ] Lab config still works (Kerberos auth, self-signed cert, OU scope)
- [ ] NTLM auth connects to production Exchange over HTTPS
- [ ] Auto auth mode negotiates successfully
- [ ] SSL verification enabled by default (fails on self-signed without verify_ssl: false)
- [ ] All 13 existing tools work unchanged in lab
- [ ] reply/forward preserve conversation threading
- [ ] download_attachment returns valid base64 and saves file
- [ ] Draft lifecycle: create → list → send
- [ ] bulk_move preview returns count without executing
- [ ] bulk_move with confirm: true moves messages
- [ ] bulk_delete soft delete moves to Deleted Items
- [ ] bulk_archive moves old messages to Archive folder
- [ ] search with folder param searches specified folder
- [ ] move_message finds messages in non-inbox folders
- [ ] Claude Desktop registration works (stdio transport)
- [ ] Claude Code registration works (stdio transport)

## Acceptance Criteria

1. Personal mailbox accessible from non-domain PC via NTLM over HTTPS
2. Lab setup works without changes (just add auth_type/verify_ssl to config)
3. All 21 tools functional
4. Bulk operations have safety preview (no accidental mass deletion)
5. pyproject.toml with uv dependency management
6. README documents all tools and both deployment scenarios
