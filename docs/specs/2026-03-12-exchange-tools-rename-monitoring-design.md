# ExchangeTools — Rename and Health Monitoring Design Spec

**Date:** 2026-03-12
**Status:** Approved
**Project:** Standalone (future FuseCP integration)
**Repo:** `exchange-purge` on Gitea (renamed to `exchange-tools`)

## Problem

The ExchangePurge project was scoped to email purge operations. Real-world use against the lab Exchange 2019 cluster has revealed a broader need: admins running manual health checks via PowerShell before and after purge operations, diagnosing DAG replication problems, monitoring certificate expiry, and tracking transport queue depths. The project name "ExchangePurge" no longer fits this expanded scope.

Separately, there is no automated health monitoring for the lab Exchange environment. Admins run ad-hoc PowerShell checks. There is no historical baseline, no trend data, and no single view of cluster health.

## Goal

1. Rename the entire project from ExchangePurge to ExchangeTools — all namespaces, assemblies, config keys, UI labels, and the Gitea repository.
2. Add a health data collector that runs Exchange health checks on a configurable schedule and stores structured results in SQLite.
3. Add a health dashboard Blazor page and on-demand/scheduled report generation from collected data.

## Changes

### Part 1: Project Rename

A mechanical rename across the entire codebase. No logic changes, only identifier substitution.

#### Solution and Projects

| Before | After |
|--------|-------|
| `ExchangePurge.sln` | `ExchangeTools.sln` |
| `src/ExchangePurge.Core/` | `src/ExchangeTools.Core/` |
| `src/ExchangePurge.PowerShell/` | `src/ExchangeTools.PowerShell/` |
| `src/ExchangePurge.Cli/` | `src/ExchangeTools.Cli/` |
| `src/ExchangePurge.Web/` | `src/ExchangeTools.Web/` |
| `tests/ExchangePurge.Core.Tests/` | `tests/ExchangeTools.Core.Tests/` |
| `tests/ExchangePurge.PowerShell.Tests/` | `tests/ExchangeTools.PowerShell.Tests/` |
| `tests/ExchangePurge.Cli.Tests/` | `tests/ExchangeTools.Cli.Tests/` |
| `tests/ExchangePurge.Web.Tests/` | `tests/ExchangeTools.Web.Tests/` |

Each `.csproj` file is updated: `<RootNamespace>ExchangeTools.*</RootNamespace>` and `<AssemblyName>ExchangeTools.*</AssemblyName>`. The CLI output binary changes from `exchange-purge.exe` to `exchange-tools.exe`.

#### Namespaces

All 80+ `.cs` files: `namespace ExchangePurge.*` → `namespace ExchangeTools.*`. All `using ExchangePurge.*` directives updated to match.

#### Configuration

| Key | Before | After |
|-----|--------|-------|
| Database file | `exchange-purge.db` | `exchange-tools.db` |
| Log pattern | `logs/exchangepurge-.log` | `logs/exchangetools-.log` |
| Auth group (operator) | `Exchange-Purge-Operators` | `Exchange-Tools-Operators` |
| Auth group (approver) | `Exchange-Purge-Approvers` | `Exchange-Tools-Approvers` |

#### UI

`MainLayout.razor` sidebar title: `"ExchangePurge"` → `"ExchangeTools"`.

#### Gitea and Git Remote

Gitea repo renamed from `exchange-purge` to `exchange-tools` via Gitea admin or MCP tool. Local git remote URL updated in `C:\claude\exchange-purge\.git\config`:
```
url = https://gitea.ergonet.pl:3001/admin/exchange-tools
```

The local working directory `C:\claude\exchange-purge\` is not renamed.

#### Docs

All references in `docs/specs/`, `docs/plans/`, and `README.md` updated from ExchangePurge to ExchangeTools.

---

### Part 2: Health Data Collector

A new class library project and background service that runs Exchange health checks on a schedule and stores structured results in SQLite.

#### New Project

`src/ExchangeTools.Monitor/` — a class library referenced by `ExchangeTools.Web` and `ExchangeTools.Cli`.

#### HealthCollector Service

`ExchangeTools.Monitor.HealthCollector` implements `IHostedService`. Registered in `Program.cs` via `services.AddHostedService<HealthCollector>()`. Runs on a configurable interval (default: 15 minutes, configured via `Monitor:CollectionIntervalMinutes` in `appsettings.json`).

Each collection run:
1. Creates a `health_snapshots` row with timestamp and `Status = Collecting`.
2. Executes all checks listed below via the existing PowerShell connection layer.
3. Writes each check result as a `health_check_results` row with `detail_json`.
4. Computes `overall_status` (Green / Yellow / Red) from aggregated results.
5. Updates the `health_snapshots` row with final status and `duration_ms`.

**Checks executed per collection run:**

| Check | Cmdlet / Method | Data Stored |
|-------|----------------|-------------|
| Service Health | `Test-ServiceHealth` | Server, role, running count, not-running count |
| Server Components | `Get-ServerComponentState` | Component name, state (Active/Inactive), per server |
| DAG Replication | `Test-ReplicationHealth` | Check name, result (Passed/Failed), per server |
| Database Copies | `Get-MailboxDatabaseCopyStatus` | DB name, server, status, copy queue length, replay queue length, content index state |
| Certificates | `Get-ExchangeCertificate` | Thumbprint, subject, expiry date, services bound, per server |
| Transport Queues | `Get-Queue` | Queue identity, delivery type, message count, per server |
| Managed Availability | `Get-HealthReport` | Health set name, alert value, per server |
| Big Funnel Index | `Get-MailboxStatistics` (sampled) | Indexed count, not-indexed count, corrupted count |
| Disk Space | WMI `Win32_LogicalDisk` | Drive letter, free bytes, total bytes, per server |
| Endpoints | HTTP probe from app server | URL, HTTP status code, response time ms |

**Execution pattern:** The collector writes a `.ps1` script, executes it as a scheduled task (same Kerberos double-hop workaround used by the purge engine), reads back JSON output, then deserializes into `HealthCheckResult` objects.

**Overall status rules:**
- Red: any `Test-ServiceHealth` role not running, DAG replication check Failed, any certificate expiring within 14 days, any database copy status not Healthy, any endpoint returning non-2xx.
- Yellow: any certificate expiring within 30 days, any content index state not Healthy, disk free below 15%.
- Green: all checks pass, no thresholds breached.

#### SQLite Schema

```sql
CREATE TABLE health_snapshots (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      TEXT    NOT NULL,  -- UTC ISO-8601
    overall_status TEXT    NOT NULL,  -- Green | Yellow | Red | Collecting | Failed
    duration_ms    INTEGER
);

CREATE TABLE health_check_results (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id   INTEGER NOT NULL REFERENCES health_snapshots(id),
    category      TEXT    NOT NULL,  -- ServiceHealth | DAGReplication | DatabaseCopies | ...
    check_name    TEXT    NOT NULL,
    server        TEXT,
    status        TEXT    NOT NULL,  -- Passed | Failed | Warning | Info
    detail_json   TEXT    NOT NULL   -- check-specific structured data as JSON
);

CREATE TABLE health_reports (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      TEXT    NOT NULL,  -- UTC ISO-8601
    snapshot_id    INTEGER NOT NULL REFERENCES health_snapshots(id),
    filename       TEXT    NOT NULL,  -- relative path under reports/
    overall_status TEXT    NOT NULL   -- Green | Yellow | Red
);
```

---

### Part 3: Health Dashboard and Report Generation

#### Health Dashboard Page

New Blazor page: `src/ExchangeTools.Web/Components/Pages/HealthDashboardPage.razor`, route `/health`.

Accessible to all users in the `Exchange-Tools-Operators` AD group (same auth as existing pages — no additional role gating).

**Layout:**

1. **Status banner** — spans full width at top. Background color: green (Green), amber (Yellow), red (Red). Displays overall health label, last collection timestamp (human-relative, e.g., "3 minutes ago"), and countdown to next collection.

2. **Summary cards row** — six cards in a single row:
   - Services: `{running}/{total}` Exchange services running
   - DAG: `{passed}/{total}` replication checks passed
   - Certificates: `{days}d` to nearest expiry
   - Disk: `{pct}%` lowest free space across all monitored drives
   - Endpoints: `{ok}/{total}` HTTP probes returning 2xx
   - Queues: total message count across all transport queues
   - Each card includes a sparkline showing the last 24 hours of that metric's values from `health_check_results`.

3. **Detail sections** — one collapsible section per check category. Each section renders per-server detail rows from the latest snapshot. Implemented as reusable Blazor components: `ServiceHealthDetail.razor`, `DagReplicationDetail.razor`, `DatabaseCopiesDetail.razor`, `CertificatesDetail.razor`, `TransportQueuesDetail.razor`, `ManagedAvailabilityDetail.razor`, `DiskSpaceDetail.razor`, `EndpointsDetail.razor`.

4. **Action bar** — "Collect Now" button triggers an immediate collection run (calls `HealthCollector.RunOnceAsync()`). "Generate Report" button triggers report generation for the current snapshot and downloads the HTML file.

#### Report Generation

`ExchangeTools.Monitor.ReportGenerator` service. Renders a snapshot into a self-contained HTML file (inline CSS, no external dependencies). Output stored under `reports/` relative to the app working directory.

Filename pattern: `exchange-tools-health-{timestamp:yyyyMMdd-HHmm}.html`.

Triggered two ways:
- **Scheduled:** Configurable via `Monitor:ReportSchedule` in `appsettings.json` (cron expression, default: `0 8 * * *` — daily at 08:00). Implemented as a second `IHostedService` (`ReportScheduler`).
- **On-demand:** "Generate Report" button on `/health`. Returns the file as a download response.

Report contents: snapshot metadata header, overall status, summary table, per-category detail tables matching the dashboard layout, generation timestamp.

#### Health Reports Page

New Blazor page: `src/ExchangeTools.Web/Components/Pages/HealthReportsPage.razor`, route `/health/reports`.

Displays a table of all rows from `health_reports` ordered by timestamp descending. Columns: Timestamp, Overall Status (colored badge), Download link. Download link serves the file from disk as an HTTP response.

#### Navigation

`MainLayout.razor` sidebar gains a "Health" section with two links:
- Dashboard (`/health`)
- Reports (`/health/reports`)

No role gating beyond the existing `Exchange-Tools-Operators` check that applies to all pages.

## Impact

- All existing purge functionality is preserved unchanged — only identifiers are renamed.
- The SQLite database file changes from `exchange-purge.db` to `exchange-tools.db`. On first run after deployment, a fresh database is created. Existing audit records are not migrated (the rename is a fresh deployment).
- AD group membership must be updated on the domain: rename `Exchange-Purge-Operators` → `Exchange-Tools-Operators` and `Exchange-Purge-Approvers` → `Exchange-Tools-Approvers`, or create the new groups and add the same members.
- The CLI binary name changes. Any scripts or shortcuts calling `exchange-purge.exe` must be updated to `exchange-tools.exe`.
- Gitea webhooks or CI references to the `exchange-purge` repo slug must be updated to `exchange-tools`.

## Files Changed

### Rename

| File | Change |
|------|--------|
| `ExchangePurge.sln` | Rename to `ExchangeTools.sln`, update project paths |
| `src/ExchangePurge.Core/ExchangePurge.Core.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName` |
| `src/ExchangePurge.PowerShell/ExchangePurge.PowerShell.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName` |
| `src/ExchangePurge.Cli/ExchangePurge.Cli.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName`, `AssemblyName` to `exchange-tools` |
| `src/ExchangePurge.Web/ExchangePurge.Web.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName` |
| `tests/ExchangePurge.Core.Tests/ExchangePurge.Core.Tests.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName` |
| `tests/ExchangePurge.PowerShell.Tests/ExchangePurge.PowerShell.Tests.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName` |
| `tests/ExchangePurge.Cli.Tests/ExchangePurge.Cli.Tests.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName` |
| `tests/ExchangePurge.Web.Tests/ExchangePurge.Web.Tests.csproj` | Rename folder and file, update `RootNamespace`, `AssemblyName` |
| All 80+ `.cs` files in `src/` and `tests/` | `namespace ExchangePurge.*` → `namespace ExchangeTools.*`, `using ExchangePurge.*` → `using ExchangeTools.*` |
| `src/ExchangeTools.Web/appsettings.json` | Update `exchange-purge.db` → `exchange-tools.db`, log path, AD group names |
| `src/ExchangeTools.Web/Program.cs` | Update AD group name strings |
| `src/ExchangeTools.Web/Components/Layout/MainLayout.razor` | Sidebar title, add Health nav section |
| `docs/specs/2026-03-07-exchange-purge-design.md` | Update cross-references to ExchangeTools |
| `docs/plans/*.md` (any referencing ExchangePurge) | Update project name references |
| `README.md` | Update project name and repo URL |
| `.git/config` (local) | Update remote URL to `exchange-tools` |

### Monitoring (New)

| File | Change |
|------|--------|
| `src/ExchangeTools.Monitor/ExchangeTools.Monitor.csproj` | New class library project |
| `src/ExchangeTools.Monitor/Models/HealthSnapshot.cs` | New — snapshot entity |
| `src/ExchangeTools.Monitor/Models/HealthCheckResult.cs` | New — result entity with `detail_json` |
| `src/ExchangeTools.Monitor/Models/HealthReport.cs` | New — report index entity |
| `src/ExchangeTools.Monitor/Models/OverallStatus.cs` | New — `Green / Yellow / Red / Collecting / Failed` enum |
| `src/ExchangeTools.Monitor/HealthCollector.cs` | New — `IHostedService`, collection loop, PS execution, status aggregation |
| `src/ExchangeTools.Monitor/ReportGenerator.cs` | New — renders snapshot to self-contained HTML |
| `src/ExchangeTools.Monitor/ReportScheduler.cs` | New — `IHostedService`, cron-based report trigger |
| `src/ExchangeTools.Monitor/HealthRepository.cs` | New — SQLite read/write for all three health tables |
| `ExchangeTools.sln` | Add `src/ExchangeTools.Monitor` project reference |
| `src/ExchangeTools.Web/ExchangeTools.Web.csproj` | Add `<ProjectReference>` to `ExchangeTools.Monitor` |
| `src/ExchangeTools.Web/Program.cs` | Register `HealthCollector` and `ReportScheduler` hosted services |
| `src/ExchangeTools.Web/appsettings.json` | Add `Monitor` section (interval, report cron, server list, endpoint URLs) |
| `src/ExchangeTools.Web/Components/Pages/HealthDashboardPage.razor` | New — `/health` dashboard |
| `src/ExchangeTools.Web/Components/Pages/HealthReportsPage.razor` | New — `/health/reports` list |
| `src/ExchangeTools.Web/Components/Health/ServiceHealthDetail.razor` | New — detail component |
| `src/ExchangeTools.Web/Components/Health/DagReplicationDetail.razor` | New — detail component |
| `src/ExchangeTools.Web/Components/Health/DatabaseCopiesDetail.razor` | New — detail component |
| `src/ExchangeTools.Web/Components/Health/CertificatesDetail.razor` | New — detail component |
| `src/ExchangeTools.Web/Components/Health/TransportQueuesDetail.razor` | New — detail component |
| `src/ExchangeTools.Web/Components/Health/ManagedAvailabilityDetail.razor` | New — detail component |
| `src/ExchangeTools.Web/Components/Health/DiskSpaceDetail.razor` | New — detail component |
| `src/ExchangeTools.Web/Components/Health/EndpointsDetail.razor` | New — detail component |

## Agent Allocation

| Phase | Agent | Responsibility | max_turns |
|-------|-------|---------------|-----------|
| Rename implementation | modular-builder | Mechanical rename across all solution files, .csproj, .cs, .razor, .json, .md | 20 |
| Monitor project scaffold | modular-builder | New `ExchangeTools.Monitor` project, models, SQLite schema, `HealthRepository` | 15 |
| Collector implementation | modular-builder | `HealthCollector` background service, all 10 check implementations, PS script execution, status aggregation | 20 |
| Dashboard UI | modular-builder | `HealthDashboardPage.razor`, all 8 detail components, sparkline rendering, Collect Now / Generate Report actions | 20 |
| Report generator | modular-builder | `ReportGenerator` (HTML rendering), `ReportScheduler` (cron), `HealthReportsPage.razor` | 15 |
| Spec compliance review | test-coverage | Verify all rename requirements applied, all 10 checks implemented, all new pages present, no ExchangePurge identifiers remain | 12 |
| Code quality review | zen-architect | Architecture review of Monitor project, component design, data access patterns | 12 |
| Cleanup | post-task-cleanup | Final hygiene: unused imports, dead code, consistent formatting | 8 |

## Acceptance Criteria

All criteria are pass/fail with no ambiguity.

### Rename

1. `dotnet build ExchangeTools.sln` succeeds with zero errors after rename.
2. `grep -r "ExchangePurge" src/ tests/` returns zero results.
3. CLI binary produced at `exchange-tools.exe`.
4. `appsettings.json` contains `exchange-tools.db` and `logs/exchangetools-.log`.
5. `appsettings.json` references `Exchange-Tools-Operators` (not `Exchange-Purge-Operators`).
6. Gitea remote URL resolves to `exchange-tools` repository.
7. All existing unit tests pass with new namespaces.

### Health Collector

8. `HealthCollector` starts on application launch and executes its first collection within `CollectionIntervalMinutes` of startup.
9. After one collection run, `health_snapshots` contains one row with `overall_status` in `{Green, Yellow, Red}` and `duration_ms > 0`.
10. After one collection run, `health_check_results` contains at least one row per check category (10 categories minimum).
11. Each `health_check_results` row has valid JSON in `detail_json`.
12. A second collection run at the configured interval produces a new `health_snapshots` row without modifying or deleting the first.
13. Collection run failure (Exchange unreachable) sets `overall_status = Failed` on the snapshot and does not crash the hosted service.

### Health Dashboard

14. `GET /health` returns HTTP 200 for authenticated users in `Exchange-Tools-Operators`.
15. Status banner background color matches `overall_status` of the latest snapshot (green/amber/red).
16. Summary cards display values derived from the latest snapshot's `health_check_results` rows.
17. Each of the 8 detail sections renders without JavaScript errors in browser console.
18. Sparklines on summary cards display data points for the last 24 hours (or fewer if less data exists).
19. "Collect Now" button triggers an immediate collection run; the page updates within 60 seconds.
20. "Generate Report" button downloads a valid HTML file named `exchange-tools-health-{timestamp}.html`.

### Report Generation

21. `reports/` directory contains one HTML file after the daily scheduled report runs.
22. Generated HTML file opens in browser without external resource requests (fully self-contained).
23. On-demand report download returns `Content-Type: text/html` with a `Content-Disposition: attachment` header.
24. `health_reports` table contains one row per generated report with a valid `filename` that exists on disk.

### Reports Page

25. `GET /health/reports` returns HTTP 200 and lists all rows from `health_reports` ordered by timestamp descending.
26. Download link for each report serves the correct HTML file.

## Configuration Reference

New `Monitor` section added to `appsettings.json`:

```json
{
  "Monitor": {
    "CollectionIntervalMinutes": 15,
    "ReportSchedule": "0 8 * * *",
    "Servers": ["EXCHANGELAB", "EXCHANGELAB2"],
    "Endpoints": [
      { "Name": "OWA", "Url": "https://lab.ergonet.pl/owa" },
      { "Name": "ECP", "Url": "https://lab.ergonet.pl/ecp" },
      { "Name": "Autodiscover", "Url": "https://autodiscover.lab.ergonet.pl/autodiscover/autodiscover.xml" }
    ],
    "AlertThresholds": {
      "CertExpiryRedDays": 14,
      "CertExpiryYellowDays": 30,
      "DiskFreeYellowPercent": 15
    }
  }
}
```
