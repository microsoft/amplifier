# ExchangePurge — Design Spec

**Date:** 2026-03-07
**Status:** Approved
**Project:** Standalone (future FuseCP integration)
**Repo:** `exchange-purge` on Gitea

## Problem

When virus or malicious emails land on Exchange servers, admins must react fast to delete them before users click. Currently this requires manually crafting complex PowerShell ComplianceSearch commands with error-prone parameters. One wrong date format or missing quote can search the wrong scope or delete the wrong emails.

## Goal

Build a standalone .NET 10 app (CLI + Web UI) that makes email search and purge operations safe, fast, and auditable. Wraps Exchange ComplianceSearch cmdlets behind structured interfaces that prevent parameter errors and enforce a safety pipeline before any deletion.

## Architecture

### Stack
- .NET 10, self-contained single-file executable
- PowerShell SDK (`System.Management.Automation`) for Exchange remote sessions
- Blazor Server for web UI (same process)
- SQLite for audit log (zero infrastructure)
- Windows Service via `Microsoft.Extensions.Hosting.WindowsServices`
- `System.CommandLine` for CLI

### Project Structure
```
exchange-purge/
├── src/
│   ├── ExchangePurge.Core/          # Business logic, models, audit
│   ├── ExchangePurge.PowerShell/    # Exchange remoting, KQL builder
│   ├── ExchangePurge.Cli/           # CLI commands
│   └── ExchangePurge.Web/           # Blazor UI + Windows Service host
├── tests/
│   ├── ExchangePurge.Core.Tests/
│   └── ExchangePurge.PowerShell.Tests/
└── ExchangePurge.sln
```

### Three Layers
1. **Presentation** — CLI (System.CommandLine) + Web UI (Blazor Server)
2. **Core** — SearchEngine, PurgeEngine, CopyEngine, AuditLog, KqlQueryBuilder
3. **PowerShell** — ComplianceSearchExecutor, RemoteRunspaceManager (WinRM/Kerberos, Polly resilience — reuse patterns from FuseCP's ExchangePowerShellExecutor)

Single process: `exchange-purge.exe` serves both CLI commands and web UI.

## Safety Pipeline

Every destructive action flows through escalating levels (stop at any point):

| Step | Mode | Destructive? | Description |
|------|------|-------------|-------------|
| 1 | **Trial Search** | No | Runs ComplianceSearch, returns match count per mailbox |
| 2 | **Preview** | No | Shows matched message details (subject, sender, date, size) — no bodies |
| 3 | **Dry Run** | No | Simulates purge — reports what would be deleted, logs as "dry-run" |
| 4 | **Copy to Analysis** | No (additive) | Copies matches to designated analysis mailbox for evidence preservation |
| 5 | **Live Purge** | **Yes** | Executes `New-ComplianceSearchAction -Purge` with auto-iteration for >500 matches |

CLI requires `--confirm` flag for live purge. No accidental deletions.

## Search Criteria (Full Power)

### Supported Filters
| Category | Filters |
|----------|---------|
| Sender/Recipient | From, To, CC, BCC (exact or wildcard `*@evil.com`) |
| Content | Subject (contains/exact), Body keywords, Boolean operators (AND/OR/NOT) |
| Attachments | Has attachment (yes/no), Attachment filename (e.g., `*.exe`) |
| Date | Sent date range (after/before/between), Received date range |
| Message properties | Size (greater/less than), Message kind (email/calendar/task/contacts/notes) |
| Scope | All mailboxes, specific mailboxes, distribution group members, folder scope |

### KQL Query Builder
App builds KQL strings from structured input — prevents syntax errors and KQL injection.
Live KQL preview in web UI for power user verification.

### Saved Searches
Stored in SQLite. Reusable from CLI (`--saved "name"`) and web UI dropdown.

## Audit Log (SQLite)

Every action recorded:

| Field | Type | Description |
|-------|------|-------------|
| Id | int | Auto-increment |
| SearchId | string | Human-readable (EP-2026-0001) |
| Timestamp | datetime | UTC |
| User | string | Windows identity (DOMAIN\user) |
| Action | enum | Search, Preview, DryRun, Copy, Purge |
| KqlQuery | string | The KQL query executed |
| Scope | string | AllMailboxes or specific list |
| MatchCount | int | Messages matched |
| PurgedCount | int? | Messages deleted (null for non-purge) |
| CopyTarget | string? | Target mailbox for copy action |
| Status | enum | Completed, Failed, DryRun |
| ErrorDetail | string? | Error message if failed |

Queryable via CLI (`exchange-purge audit --last 20`) and web UI table with filters and CSV export.

## Authentication

### CLI
Windows identity of the caller. Exchange enforces Compliance Management role server-side.

### Web UI
- Windows Authentication (Negotiate/Kerberos)
- AD group membership check (configurable group, default: `Exchange-Purge-Operators`)
- Rejected users see "Access Denied" page

### Exchange Connection
Kerberos implicit auth — no stored credentials. Config in `appsettings.json`:
```json
{
  "Exchange": {
    "Server": "exchangelab.lab.ergonet.pl",
    "UseKerberos": true,
    "AnalysisMailbox": "itsecurity@lab.ergonet.pl"
  },
  "Auth": {
    "RequiredGroup": "Exchange-Purge-Operators"
  },
  "Service": {
    "Port": 9443,
    "UseSsl": true
  }
}
```

## Web UI Pages

| Page | Purpose |
|------|---------|
| Search | Form-based query builder, add/remove filter rows, KQL preview |
| Results | Active/past searches, match counts per mailbox, preview, action buttons |
| Audit | Filterable audit log table, export to CSV |

Real-time progress via Blazor Server SignalR (no polling).

## Windows Service

```bash
exchange-purge install --service-name "ExchangePurge"  # Install as service
exchange-purge serve                                     # Run interactively
exchange-purge search --subject "test" --all-mailboxes  # CLI works independently
```

## CLI Examples

```bash
# Trial search
exchange-purge search --from "*@evil.com" --subject "Invoice" --has-attachment --attachment-name "*.exe" --after 2026-03-07 --all-mailboxes

# Preview results
exchange-purge preview --search-id EP-2026-0001

# Dry run
exchange-purge purge --search-id EP-2026-0001 --dry-run

# Copy evidence
exchange-purge copy --search-id EP-2026-0001 --target-mailbox itsecurity@lab.ergonet.pl

# Live purge
exchange-purge purge --search-id EP-2026-0001 --confirm
```

## Key Technical Risks

1. **ComplianceSearch is async** — `Start-ComplianceSearch` returns immediately, need polling for completion
2. **500-item purge limit** — iteration logic (purge → re-search → purge until clean)
3. **Remote PowerShell session management** — reuse FuseCP's Polly resilience patterns
4. **KQL injection** — sanitize user input before building query strings

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Codebase Research | agentic-search | Study FuseCP ExchangePowerShellExecutor patterns |
| Architecture | zen-architect | Solution structure, project references |
| Implementation — Core | modular-builder | SearchEngine, PurgeEngine, CopyEngine, AuditLog, KQL builder |
| Implementation — PS | modular-builder | ComplianceSearchExecutor, RemoteRunspaceManager |
| Implementation — CLI | modular-builder | System.CommandLine setup, all commands |
| Implementation — Web | modular-builder | Blazor pages, Windows Service host, auth middleware |
| Testing | test-coverage | Unit tests for KQL builder, safety pipeline, audit |
| Security | security-guardian | Destructive operations review, auth, input validation |
| Cleanup | post-task-cleanup | Final hygiene pass |

## Test Plan

- KQL query builder: unit tests for all filter combinations, escaping, injection prevention
- Safety pipeline: verify each step produces correct output, dry-run never deletes
- Audit log: verify all actions are recorded, query/filter works
- Authentication: AD group check enforced on web UI
- Purge iteration: mock >500 results, verify loop completes correctly
- Integration: test against Exchange lab (EXCHANGELAB/EXCHANGELAB2)
