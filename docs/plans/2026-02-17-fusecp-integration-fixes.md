# FuseCP Integration Test Fixes — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 7 issues identified in the API-UI parity integration report (4 BUG, 3 MISMATCH) — 1 real application bug, 1 code quality fix, and a comprehensive test suite rewrite.

**Architecture:** The issues split into three categories: (A) one real backend bug in HyperVProviderFactory, (B) one code quality issue in the Audit Log page, and (C) five test script issues caused by Blazor Server's async SignalR data loading, missing API parameters, and wrong data source comparisons. The test suite will be rewritten to be Blazor-aware.

**Tech Stack:** C# / ASP.NET (.NET 8), Blazor Server, Node.js + Playwright (browser tests), SQL Server

---

## Issue Triage (from integration report)

| # | Page | Verdict | Root Cause | Category |
|---|------|---------|------------|----------|
| 1 | VMs | BUG (500) | `HyperVProviderFactory.cs:15` uses connection string `"FuseCPDatabase"` but `appsettings.json` defines `"Default"` | **App Bug** |
| 2 | Audit Logs | MISMATCH | `AuditLog.razor:281` `LoadLogs()` has no try/catch — exceptions leave table empty silently | **Code Quality** |
| 3 | AD Groups | BUG (400) | NOT a bug — endpoint requires `ouPath` query parameter. Test omits it. | Test Fix |
| 4 | AD Statistics | BUG (400) | Same — requires `ouPath`. Test omits it. | Test Fix |
| 5 | DNS Zones | MISMATCH | API returns 12 zones. Blazor loads data via SignalR after render — test checks `table tbody tr` too early (0 rows). | Test Fix |
| 6 | Audit Logs | MISMATCH | Same SignalR timing — test reads empty table before data arrives. | Test Fix |
| 7 | Organizations | MISMATCH | Test compares Exchange orgs API (2) with hosting packages page (3 — includes "Neapol Hosting Space"). Different data sources. | Test Fix |
| 8 | Bug Reports | BUG (404) | Page exists and works (user confirmed). Likely Blazor InteractiveServer routing or auth issue in headless Playwright. | Test Fix |

## Files Changed

| Action | File | Purpose |
|--------|------|---------|
| Modify | `src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs:15` | Fix connection string name |
| Modify | `src/FuseCP.Portal/Components/Pages/Admin/AuditLog.razor:281-301` | Add try/catch to LoadLogs |
| Rewrite | `scripts/browser-tests/run-full-suite.js` | Blazor-aware test runner |

All paths relative to `C:\claude\fusecp-enterprise`.

---

## Chunk 1: Application Fixes

### Task 1: Fix HyperV connection string mismatch

**Agent:** bug-hunter

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Services\HyperVProviderFactory.cs:15`
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\appsettings.json` (verify)

**Context:**
- `HyperVProviderFactory.cs:15` requests `configuration.GetConnectionString("FuseCPDatabase")` but `appsettings.json:3` only defines `"Default"`.
- Every other service in the codebase uses `"Default"` (e.g., `Program.cs:59`).
- This causes `InvalidOperationException` on first use, which surfaces as HTTP 500 on `GET /api/hyperv/{host}/vms`.

- [ ] **Step 1: Fix the connection string name**

In `HyperVProviderFactory.cs:15`, change `"FuseCPDatabase"` to `"Default"`:

```csharp
// Before:
_connectionString = configuration.GetConnectionString("FuseCPDatabase")
    ?? throw new InvalidOperationException("FuseCPDatabase connection string not configured");

// After:
_connectionString = configuration.GetConnectionString("Default")
    ?? throw new InvalidOperationException("Default connection string not configured");
```

- [ ] **Step 2: Build and verify**

```bash
cd /c/claude/fusecp-enterprise/src/FuseCP.EnterpriseServer
dotnet build --configuration Release 2>&1 | tail -5
```

Expected: `Build succeeded. 0 Warning(s) 0 Error(s)`

- [ ] **Step 3: Deploy API and test the endpoint**

```bash
# Deploy
powershell -Command "Stop-WebAppPool -Name 'FuseCP_API'"
cd /c/claude/fusecp-enterprise/src/FuseCP.EnterpriseServer
dotnet publish --configuration Release --output /c/FuseCP/EnterpriseServer
powershell -Command "Start-WebAppPool -Name 'FuseCP_API'"

# Wait for startup
sleep 5

# Test
curl -sk -H "X-Api-Key: fusecp-admin-key-2026" "http://localhost:5010/api/hyperv/172.31.251.102/vms"
```

Expected: HTTP 200 with JSON array of VMs (or 200 with empty array if no VMs exist, or 404 if host not in Servers table — but NOT 500).

- [ ] **Step 4: Commit**

```bash
cd /c/claude/fusecp-enterprise
git add src/FuseCP.EnterpriseServer/Services/HyperVProviderFactory.cs
git commit -m "fix: use correct connection string name in HyperVProviderFactory

Changed 'FuseCPDatabase' to 'Default' to match appsettings.json.
This was causing HTTP 500 on all /api/hyperv/* endpoints."
```

---

### Task 2: Add error handling to AuditLog.razor LoadLogs

**Agent:** bug-hunter

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Admin\AuditLog.razor:281-301`

**Context:**
- `LoadLogs()` at line 281 calls `AuditApi.GetLogsAsync(...)` with no try/catch.
- If the API call throws, `_response` stays null, DataTable renders empty — user sees no data and no error message.
- Compare with `AuditDashboard.razor:212-242` which properly wraps its API calls in try/catch and sets `_error`.

- [ ] **Step 1: Add try/catch to LoadLogs**

Wrap the API call in `AuditLog.razor:281-301`:

```csharp
// Before:
private async Task LoadLogs()
{
    int? severityId = null;
    if (!string.IsNullOrEmpty(_filterSeverity) && int.TryParse(_filterSeverity, out var sevId))
    {
        severityId = sevId;
    }

    _response = await AuditApi.GetLogsAsync(
        page: _currentPage,
        pageSize: _pageSize,
        sourceName: string.IsNullOrEmpty(_filterSource) ? null : _filterSource,
        taskName: string.IsNullOrEmpty(_filterTask) ? null : _filterTask,
        severityId: severityId,
        fromDate: _filterFromDate,
        toDate: _filterToDate,
        sortBy: _sortBy,
        sortDesc: _sortDesc);

    StateHasChanged();
}

// After:
private async Task LoadLogs()
{
    try
    {
        int? severityId = null;
        if (!string.IsNullOrEmpty(_filterSeverity) && int.TryParse(_filterSeverity, out var sevId))
        {
            severityId = sevId;
        }

        _response = await AuditApi.GetLogsAsync(
            page: _currentPage,
            pageSize: _pageSize,
            sourceName: string.IsNullOrEmpty(_filterSource) ? null : _filterSource,
            taskName: string.IsNullOrEmpty(_filterTask) ? null : _filterTask,
            severityId: severityId,
            fromDate: _filterFromDate,
            toDate: _filterToDate,
            sortBy: _sortBy,
            sortDesc: _sortDesc);
    }
    catch (Exception ex)
    {
        _error = $"Failed to load audit logs: {ex.Message}";
    }

    StateHasChanged();
}
```

Also verify that `_error` is declared and rendered. Check if the page has an error display section (look for `_error` in the template portion of the file around lines 1-150).

- [ ] **Step 2: Build Portal**

```bash
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal
dotnet build --configuration Release 2>&1 | tail -5
```

Expected: Build succeeded.

- [ ] **Step 3: Deploy Portal and verify**

```bash
powershell -Command "Stop-WebAppPool -Name 'FuseCP_Portal'"
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal
dotnet publish --configuration Release --output /c/FuseCP/Portal
powershell -Command "Start-WebAppPool -Name 'FuseCP_Portal'"
```

Navigate to https://fusecp.ergonet.pl/admin/audit in a browser — confirm audit logs still load correctly.

- [ ] **Step 4: Commit**

```bash
cd /c/claude/fusecp-enterprise
git add src/FuseCP.Portal/Components/Pages/Admin/AuditLog.razor
git commit -m "fix: add error handling to AuditLog LoadLogs method

LoadLogs() had no try/catch — API failures left the table silently empty.
Now catches exceptions and displays error message like AuditDashboard does."
```

---

## Chunk 2: Test Suite Rewrite

### Task 3: Rewrite browser test runner (Blazor-aware)

**Agent:** modular-builder

**Files:**
- Rewrite: `C:\claude\fusecp-enterprise\scripts\browser-tests\run-full-suite.js`

**Context — why the current tests fail:**

1. **Blazor Server uses SignalR WebSocket** for data loading after initial page render. `waitForLoadState('networkidle')` does NOT wait for WebSocket messages. Tables render empty initially, then fill via SignalR.
2. **AD Groups/Statistics** require `ouPath` query parameter — without it, API correctly returns 400.
3. **Organizations** page at `/organizations` redirects to `/admin/organizations` which queries DB directly (shows all 3 packages). API `/api/exchange/organizations` returns only Exchange orgs (2). Different data sources.
4. **Bug Reports** page at `/admin/bugs` works in real browsers but returns 404 in Playwright — likely Blazor InteractiveServer SSR routing issue.

**Key fix: Replace `waitForLoadState('networkidle')` with explicit waits for table rows.**

For Blazor pages, after `page.goto()`:
```javascript
// Wait for Blazor to load data and render table rows
await page.waitForSelector('table tbody tr', { timeout: 15000 }).catch(() => null);
// Small extra delay for any remaining Blazor re-renders
await page.waitForTimeout(1000);
```

- [ ] **Step 1: Plan the rewritten test cases**

The new test runner must handle these patterns:

| Test | API Endpoint | Portal URL | API Params | UI Wait Strategy |
|------|-------------|------------|------------|------------------|
| Organizations | `/api/exchange/organizations` | `/admin/organizations` | none | Wait for `table tbody tr` |
| Servers | `/api/servers` | `/settings/servers` | none | Wait for `table tbody tr` |
| AD Groups | `/api/ad/groups?ouPath={ou}` | `/ad/groups` (needs org context) | `ouPath` from org | Skip UI (requires org navigation) |
| DNS Zones | `/api/dns/zones` | `/dns/zones` | none | Wait for `table tbody tr` |
| VMs | `/api/hyperv/172.31.251.102/vms` | `/vms` | none | Wait for `table tbody tr` |
| Plans | `/api/plans` | `/settings/plans` | none | Wait for `table tbody tr` |
| Audit Logs | `/api/admin/audit/logs` | `/admin/audit` | none | Wait for `table tbody tr` |
| Operations Log | none | `/admin/operations` | none | Page loads OK |
| Admin Dashboard | none | `/admin/dashboard` | none | Page loads OK |
| Bug Reports | none | `/admin/bugs` | none | Page loads OK |
| AD Statistics | `/api/ad/statistics?ouPath={ou}` | `/ad/statistics` (needs org context) | `ouPath` from org | Skip UI (requires org navigation) |

Key changes from current test:
- Organizations: compare with `/admin/organizations` (not `/organizations` which redirects)
- AD Groups/Statistics: pass `ouPath` param from first organization's `organizationId`
- All pages: wait for `table tbody tr` selector (Blazor-aware) instead of `networkidle`
- Bug Reports: try longer wait, classify as SKIP if Blazor routing issue persists

- [ ] **Step 2: Write the rewritten test runner**

Complete rewrite of `run-full-suite.js` with:

```javascript
const axios = require('axios');
const { chromium } = require('playwright');
const fs = require('fs');

const API_BASE = 'http://localhost:5010';
const ADMIN_KEY = 'fusecp-admin-key-2026';
const PORTAL = 'https://fusecp.ergonet.pl';
const USER = 'Agnieszka';
const PASS = 'Kaja@2015';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'X-Api-Key': ADMIN_KEY },
  timeout: 30000,
  validateStatus: () => true,
});

// Helper: wait for Blazor table to render rows
async function waitForTableRows(page, timeout = 15000) {
  try {
    await page.waitForSelector('table tbody tr', { timeout });
    await page.waitForTimeout(500); // Blazor re-render buffer
    return await page.locator('table tbody tr').count();
  } catch {
    return 0; // No rows appeared within timeout
  }
}

// Helper: check if page has error
async function checkPageError(page) {
  const body = await page.textContent('body').catch(() => '');
  if (body.includes('Error') && body.includes('500')) return '500 Error';
  if (body.includes('404') || body.includes('Not Found')) return '404';
  if (body.includes('Not authorized') || body.includes('Access Denied')) return 'AUTH';
  return null;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();
  const results = [];

  try {
    // Login
    console.log('Logging in...');
    await page.goto(`${PORTAL}/login`, { timeout: 60000 });
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.fill('#username', USER);
    await page.fill('#password', PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL(url => !url.href.includes('login'), { timeout: 30000 });
    console.log('Login OK\n');

    // Step 1: Get first org's ouPath for AD endpoints
    let ouPath = null;
    try {
      const orgsRes = await api.get('/api/exchange/organizations');
      if (orgsRes.status === 200 && Array.isArray(orgsRes.data) && orgsRes.data.length > 0) {
        ouPath = orgsRes.data[0].organizationId;
        console.log(`Using ouPath: ${ouPath}\n`);
      }
    } catch (e) {
      console.log('Could not fetch ouPath, AD tests will use API-only mode\n');
    }

    // Test definitions
    const tests = [
      {
        name: 'Organizations',
        api: '/api/exchange/organizations',
        ui: '/admin/organizations',
        note: 'API returns Exchange orgs; UI shows all hosting packages (may differ)',
      },
      { name: 'Servers', api: '/api/servers', ui: '/settings/servers' },
      {
        name: 'AD Groups',
        api: ouPath ? `/api/ad/groups?ouPath=${encodeURIComponent(ouPath)}` : null,
        ui: null, // Requires org context navigation — skip UI
        apiOnly: true,
        skipReason: ouPath ? null : 'No ouPath available',
      },
      { name: 'DNS Zones', api: '/api/dns/zones', ui: '/dns/zones' },
      { name: 'VMs', api: '/api/hyperv/172.31.251.102/vms', ui: '/vms' },
      { name: 'Plans', api: '/api/plans', ui: '/settings/plans' },
      {
        name: 'Audit Logs',
        api: '/api/admin/audit/logs',
        ui: '/admin/audit',
        apiCountPath: 'logs', // response is { logs: [...], total: N }
      },
      { name: 'Operations Log', ui: '/admin/operations', uiOnly: true },
      { name: 'Admin Dashboard', ui: '/admin/dashboard', uiOnly: true },
      { name: 'Bug Reports', ui: '/admin/bugs', uiOnly: true },
      {
        name: 'AD Statistics',
        api: ouPath ? `/api/ad/statistics?ouPath=${encodeURIComponent(ouPath)}` : null,
        ui: null,
        apiOnly: true,
        skipReason: ouPath ? null : 'No ouPath available',
      },
    ];

    // Run tests
    for (const t of tests) {
      console.log(`Testing ${t.name}...`);
      let apiStatus = '-', apiCount = '-', apiError = null;
      let uiStatus = '-', uiCount = '-', uiError = null;

      // --- API ---
      if (t.skipReason) {
        apiStatus = 'SKIP';
        apiError = t.skipReason;
      } else if (t.api) {
        try {
          const res = await api.get(t.api);
          apiStatus = res.status;
          if (res.status >= 200 && res.status < 300) {
            const data = t.apiCountPath
              ? res.data[t.apiCountPath]
              : (Array.isArray(res.data) ? res.data : res.data?.items || []);
            apiCount = Array.isArray(data) ? data.length : '?';
          } else {
            apiError = `HTTP ${res.status}`;
            apiCount = 0;
          }
        } catch (e) {
          apiStatus = 'ERR';
          apiError = e.code || e.message;
          apiCount = 0;
        }
      }

      // --- UI ---
      if (t.apiOnly) {
        uiStatus = 'N/A';
        uiCount = '-';
      } else if (t.ui) {
        try {
          await page.goto(`${PORTAL}${t.ui}`, { timeout: 30000 });
          // Wait for Blazor to render (not just networkidle)
          const error = await checkPageError(page);
          if (error) {
            uiStatus = error;
            uiError = `Page showed ${error}`;
          } else {
            uiStatus = 'OK';
            uiCount = await waitForTableRows(page);
          }
        } catch (e) {
          uiStatus = 'TIMEOUT';
          uiError = e.message.substring(0, 100);
        }
      }

      // --- Verdict ---
      let verdict = 'PASS', details = '';
      if (t.skipReason) {
        verdict = 'SKIP';
        details = t.skipReason;
      } else if (t.uiOnly) {
        if (uiError) { verdict = 'BUG'; details = uiError; }
      } else if (t.apiOnly) {
        if (apiError) { verdict = 'BUG'; details = `API: ${apiError}`; }
      } else if (apiError && uiError) {
        verdict = 'BUG'; details = `API: ${apiError}, UI: ${uiError}`;
      } else if (apiError) {
        verdict = 'BUG'; details = `API error: ${apiError}`;
      } else if (uiError) {
        verdict = 'BUG'; details = `UI error: ${uiError}`;
      } else if (
        apiCount !== '-' && uiCount !== '-' &&
        Number(apiCount) !== Number(uiCount)
      ) {
        // Allow known discrepancy for Organizations
        if (t.name === 'Organizations') {
          verdict = 'INFO';
          details = `API: ${apiCount} Exchange orgs, UI: ${uiCount} hosting packages (expected — different data sources)`;
        } else {
          verdict = 'MISMATCH';
          details = `API: ${apiCount}, UI: ${uiCount}`;
        }
      }

      results.push({ name: t.name, apiStatus, apiCount, uiStatus, uiCount, verdict, details });
      const icon = { PASS:'[PASS]', SKIP:'[SKIP]', INFO:'[INFO]', MISMATCH:'[MISMATCH]', BUG:'[BUG]' }[verdict] || '[?]';
      console.log(`  ${icon} ${t.name} — API:${apiStatus}/${apiCount} UI:${uiStatus}/${uiCount}${details ? ' — '+details : ''}`);
    }
  } catch (e) {
    console.error('Fatal:', e.message);
  } finally {
    await browser.close();
  }

  // --- Report ---
  const dir = 'C:/claude/fusecp-enterprise/docs/reports';
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

  const now = new Date().toISOString().replace('T',' ').substring(0,19);
  let md = `# FuseCP API-UI Parity Integration Report\n\n`;
  md += `**Generated:** ${now}\n`;
  md += `**Portal:** ${PORTAL}\n`;
  md += `**API:** ${API_BASE}\n`;
  md += `**User:** ${USER}\n\n`;

  md += `## Summary\n\n`;
  md += `| Page | API | API Count | UI | UI Count | Verdict | Details |\n`;
  md += `|------|-----|-----------|-----|----------|---------|--------|\n`;
  for (const r of results) {
    md += `| ${r.name} | ${r.apiStatus} | ${r.apiCount} | ${r.uiStatus} | ${r.uiCount} | **${r.verdict}** | ${r.details||'-'} |\n`;
  }

  const total = results.filter(r => r.verdict !== 'SKIP').length;
  const passed = results.filter(r => r.verdict === 'PASS' || r.verdict === 'INFO').length;
  const bugs = results.filter(r => r.verdict === 'BUG').length;
  const mismatches = results.filter(r => r.verdict === 'MISMATCH').length;
  const skipped = results.filter(r => r.verdict === 'SKIP').length;

  md += `\n## Statistics\n\n`;
  md += `- **Total:** ${total} (${skipped} skipped)\n`;
  md += `- **Passed:** ${passed} (${total?((passed/total)*100).toFixed(0):0}%)\n`;
  md += `- **Mismatches:** ${mismatches}\n`;
  md += `- **Bugs:** ${bugs}\n\n`;

  if (bugs + mismatches > 0) {
    md += `## Issues\n\n`;
    for (const r of results.filter(r => r.verdict === 'BUG' || r.verdict === 'MISMATCH')) {
      md += `### ${r.name} — ${r.verdict}\n`;
      md += `- ${r.details}\n`;
      md += `- API: status=${r.apiStatus}, count=${r.apiCount}\n`;
      md += `- UI: status=${r.uiStatus}, count=${r.uiCount}\n\n`;
    }
  }

  fs.writeFileSync(`${dir}/integration-report.md`, md);
  console.log(`\nReport: ${dir}/integration-report.md`);
})();
```

- [ ] **Step 3: Run the rewritten test suite**

```bash
cd /c/claude/fusecp-enterprise/scripts/browser-tests && node run-full-suite.js
```

Expected: Significant improvement — most MISMATCHes should resolve (DNS Zones, Audit Logs now wait for Blazor rendering; AD endpoints pass ouPath; Organizations classified as INFO).

- [ ] **Step 4: Review the generated report**

```bash
cat /c/claude/fusecp-enterprise/docs/reports/integration-report.md
```

Verify:
- DNS Zones: should show API=12, UI=12 (PASS) if Blazor wait works
- Audit Logs: should show matching counts (PASS)
- AD Groups/Statistics: should show 200 with data (PASS or API-only)
- VMs: should be PASS or improved after Task 1 fix
- Organizations: should be INFO (known different data sources)
- Bug Reports: investigate verdict — if still failing, document why

- [ ] **Step 5: Commit**

```bash
cd /c/claude/fusecp-enterprise
git add scripts/browser-tests/run-full-suite.js docs/reports/integration-report.md
git commit -m "fix: rewrite browser tests to be Blazor-aware

- Wait for table rows via selector instead of networkidle (Blazor uses SignalR)
- Pass required ouPath parameter to AD Groups/Statistics endpoints
- Navigate to /admin/organizations (not /organizations redirect)
- Classify Org count diff as INFO (different data sources)
- Add waitForTableRows helper with 15s timeout + re-render buffer"
```

---

### Task 4: Investigate and fix any remaining failures

**Agent:** bug-hunter

**Files:**
- Depends on Task 3 results

After running the rewritten tests in Task 3, investigate any remaining BUG or MISMATCH verdicts:

- [ ] **Step 1: Read the report from Task 3**

Check `C:\claude\fusecp-enterprise\docs\reports\integration-report.md` for remaining issues.

- [ ] **Step 2: For each remaining issue, diagnose**

Common remaining issues and fixes:

**DNS Zones still MISMATCH (UI: 0):**
- Check if `DnsApiClient` is returning data by adding console logging
- Verify the DNS page's `LoadZonesAsync` method in `Zones.razor:259`
- The page may need more wait time or a different selector (check if DataTable renders differently)

**Audit Logs still MISMATCH:**
- After Task 2's try/catch fix, the error will be visible
- If API returns paginated response `{ logs: [...], total: N }`, the test now handles this via `apiCountPath`
- UI uses server-side pagination — `DataTable` may render only one page of rows

**Bug Reports still 404:**
- Try navigating manually in Playwright with screenshots
- May be Blazor InteractiveServer SSR issue in headless mode
- Acceptable to mark as KNOWN_ISSUE if only fails in headless Playwright

- [ ] **Step 3: Apply fixes and re-run**

For each fix, edit the appropriate file, rebuild if needed, re-run tests.

- [ ] **Step 4: Final commit**

```bash
cd /c/claude/fusecp-enterprise
git add -A scripts/browser-tests/ docs/reports/
git commit -m "fix: resolve remaining browser test issues

[describe what was fixed based on investigation]"
```

---

## Chunk 3: Verification & Cleanup

### Task 5: Final verification and report

**Agent:** test-coverage

**Files:**
- Read: `C:\claude\fusecp-enterprise\docs\reports\integration-report.md`
- Read: `C:\claude\fusecp-enterprise\scripts\browser-tests\run-full-suite.js`

- [ ] **Step 1: Run the full test suite one final time**

```bash
cd /c/claude/fusecp-enterprise/scripts/browser-tests && node run-full-suite.js
```

- [ ] **Step 2: Verify the final report**

Target: 80%+ pass rate (was 36%). Acceptable remaining issues:
- Organizations: INFO (known different data sources)
- Bug Reports: KNOWN_ISSUE if Blazor headless routing issue
- AD Groups/Statistics: SKIP if no ouPath available

- [ ] **Step 3: Present summary to user**

Display the final report table and comparison:
- Before: 4 PASS (36%), 3 MISMATCH, 4 BUG
- After: [actual results]

- [ ] **Step 4: Update HANDOFF.md with results**

Update the history table in `C:\claude\amplifier\HANDOFF.md` with final results.

---

## Execution Notes

- **Deploy order matters:** Task 1 (API fix) must deploy before Task 3 (test run) to get accurate VM results
- **Task 2 (Portal fix) must deploy before Task 3** for accurate Audit Log results
- **Tasks 1 and 2 can run in parallel** (different files, different app pools)
- **Task 3 depends on Tasks 1+2 being deployed**
- **Task 4 depends on Task 3 results**
- **Task 5 is the final verification pass**
