# ExchangePurge — Storage Analysis Feature Design Spec

**Date:** 2026-03-11
**Status:** Approved
**Project:** ExchangePurge (standalone)
**Repo:** `exchange-purge` on Gitea

## Problem

ExchangePurge users must decide whether and what to purge without any visibility into mailbox storage usage. The recoverable items (dumpster) folder breakdown — Deletions, Purges, Versions subfolders and their sizes — is only accessible via Exchange Management Shell. There is no in-app way to identify top offenders, check quota consumption, or see per-subfolder size distribution before initiating a purge.

## Goal

Add a read-only Storage Analysis page that displays recoverable items storage breakdown per mailbox with quota progress bars, subfolder detail, and ranked multi-mailbox summary. The page is accessible to any authenticated user (no policy gate) and provides a direct navigation path to Purge Dumpster for mailboxes requiring action.

## Changes

### Page and Navigation

- New page route: `/storage-analysis`
- Page title: "Storage Analysis"
- Navigation: add a "Tools" section header in `MainLayout.razor` sidebar; place the "Storage Analysis" nav link under it
- No AD group policy gate — the page is read-only and is accessible to any user authenticated via Windows Authentication
- Two view modes:
  - **Single mailbox** — detailed quota bar and subfolder breakdown for one mailbox
  - **Multi-mailbox** — ranked summary table of top offenders across a scope
- Scope selector: All / Specific / OU radio buttons, identical pattern to the existing Purge Dumpster page

### Exchange PowerShell Backend

#### New interface method on `IComplianceSearchExecutor`

```csharp
Task<List<MailboxStorageInfo>> GetMailboxStorageInfoAsync(
    IEnumerable<string> emails,
    CancellationToken ct = default);
```

#### New model `MailboxStorageInfo`

```csharp
public record MailboxStorageInfo(
    string Email,
    string DisplayName,
    long DeletionsSize,
    int DeletionsCount,
    long PurgesSize,
    int PurgesCount,
    long VersionsSize,
    int VersionsCount,
    long TotalRecoverableSize,
    int TotalRecoverableCount,
    long RecoverableItemsQuota,
    long RecoverableItemsWarningQuota);
```

All size fields are stored as bytes. The UI layer formats these values to human-readable units (KB / MB / GB).

#### PowerShell commands per mailbox

1. `Get-MailboxFolderStatistics -Identity <email> -FolderScope RecoverableItems`
   — returns subfolder names (Deletions, Purges, Versions), sizes, and item counts
2. `Get-Mailbox -Identity <email> | Select RecoverableItemsQuota, RecoverableItemsWarningQuota`
   — returns quota limits for the mailbox

#### Multi-mailbox "All" scope

`Get-Mailbox -ResultSize 20 -SortBy TotalDeletedItemSize` — fetches the top 20 mailboxes by deleted item size. Subsequent "Show more" requests fetch the next batch of 20 using an offset parameter.

### Single Mailbox Detail View

- Quota progress bar at top of the page, full width
  - Green when usage is below 70% of `RecoverableItemsQuota`
  - Amber when usage is 70–90%
  - Red when usage exceeds 90%
  - Label format: `4.2 GB / 30 GB recoverable items quota (14%)`
- Mailbox display name shown in the page header alongside the email address
- Subfolder table columns: Folder Name, Item Count, Size, relative progress bar
  - Deletions row: blue progress bar
  - Purges row: red progress bar
  - Versions row: amber progress bar
  - Progress bars are sized relative to the largest subfolder, not to the quota

### Multi-Mailbox Summary View

- Ranked table of top 20 mailboxes ordered by `TotalRecoverableSize` descending
- Columns: Rank, Display Name, Email, Total Recoverable Size (size progress bar relative to the largest mailbox in the list), Quota Usage (green/amber/red quota bar)
- Each row is expandable as an accordion — clicking a row reveals the subfolder breakdown (Deletions, Purges, Versions sizes and counts)
- "Show more" button at the bottom of the table fetches the next 20 mailboxes and appends them to the list
- Each row includes a "Purge Dumpster" quick action link — navigates to `/purge-dumpster` with the mailbox email pre-filled in the scope selector

## Files Changed

| File | Change |
|------|--------|
| `src/ExchangePurge.Core/Models/MailboxStorageInfo.cs` | NEW — record model with all size/count/quota fields |
| `src/ExchangePurge.Core/Engines/IComplianceSearchExecutor.cs` | Add `GetMailboxStorageInfoAsync` method signature |
| `src/ExchangePurge.PowerShell/SearchMailboxExecutor.cs` | Implement `GetMailboxStorageInfoAsync` with `Get-MailboxFolderStatistics` and `Get-Mailbox` calls |
| `src/ExchangePurge.PowerShell/ComplianceSearchExecutor.cs` | Implement `GetMailboxStorageInfoAsync` (same pattern as above, for the compliance executor path) |
| `src/ExchangePurge.Web/Components/Pages/StorageAnalysisPage.razor` | NEW — full page component with scope selector, single/multi view modes, quota bars, subfolder table, accordion rows, show more |
| `src/ExchangePurge.Web/Components/Layout/MainLayout.razor` | Add "Tools" section header and "Storage Analysis" nav link to sidebar |

## Impact

- No changes to existing purge or search flows
- No schema changes — no new SQLite tables or columns
- No new authentication requirements — page is read-only and open to any authenticated Windows user
- PowerShell session reuse follows existing Polly resilience patterns in the executor — no new connection management concerns
- The "Show more" pagination avoids fetching all mailboxes at once — bounded memory usage per request

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Codebase Research | agentic-search | Verify `Get-MailboxFolderStatistics` and `Get-Mailbox` cmdlet invocation patterns in existing executors; confirm scope selector pattern in Purge Dumpster page |
| Implementation | modular-builder | Build `MailboxStorageInfo` model, interface method, both executor implementations, `StorageAnalysisPage.razor`, and `MainLayout.razor` nav changes |
| Review | test-coverage | Verify spec compliance: all fields present, progress bar thresholds correct, no auth gate present, quick action link wired |
| Cleanup | post-task-cleanup | Final hygiene pass |

## Test Plan

| # | Scenario | Pass Condition |
|---|----------|---------------|
| 1 | Page load without policy gate | `/storage-analysis` loads for any Windows-authenticated user; no "Access Denied" redirect |
| 2 | Single mailbox quota bar — green | Mailbox at 50% quota usage renders green progress bar |
| 3 | Single mailbox quota bar — amber | Mailbox at 75% quota usage renders amber progress bar |
| 4 | Single mailbox quota bar — red | Mailbox at 95% quota usage renders red progress bar |
| 5 | Single mailbox subfolder breakdown | Deletions, Purges, and Versions rows appear with correct sizes, counts, and bar colors (blue/red/amber) |
| 6 | Multi-mailbox ranked table | "All" scope loads top 20 mailboxes ordered by recoverable items size descending |
| 7 | Multi-mailbox accordion expansion | Clicking a row reveals subfolder breakdown; clicking again collapses it |
| 8 | Show more pagination | Clicking "Show more" appends the next 20 mailboxes to the table without replacing existing rows |
| 9 | Quick action link | Clicking "Purge Dumpster" on a row navigates to `/purge-dumpster` with the mailbox email pre-filled |
| 10 | Sidebar navigation | "Tools" section header and "Storage Analysis" link are present in the sidebar |
| 11 | Size formatting | Byte values are displayed as KB/MB/GB (not raw bytes) in all views |
| 12 | Display name in header | Single mailbox detail view shows the mailbox display name alongside the email address |
