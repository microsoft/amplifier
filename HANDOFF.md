# Amplifier Cowork — Task Handoff

## Dispatch Status: WAITING_FOR_GEMINI

> **Protocol:** Only the designated receiver should act.
> - Claude acts on: `IDLE`, `PR_READY`, `REVIEWING`, `DEPLOYING`, `WAITING_FOR_CLAUDE`
> - Gemini acts on: `WAITING_FOR_GEMINI`

## State Transitions
```
IDLE ──(Claude writes task)──→ WAITING_FOR_GEMINI
WAITING_FOR_GEMINI ──(Gemini starts)──→ IN_PROGRESS
IN_PROGRESS ──(Gemini pushes PR)──→ PR_READY
PR_READY ──(Claude reviews)──→ REVIEWING
REVIEWING ──(Claude merges/deploys)──→ DEPLOYING
DEPLOYING ──(Claude tests pass)──→ IDLE
```

---

## Current Task

**From:** Claude → Gemini
**Branch:** feature/loading-spinner-migration-v2
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise

### Getting Started (run these commands first)
```bash
cd /c/claude/fusecp-enterprise
git checkout master && git pull origin master && git checkout -b feature/loading-spinner-migration-v2
```
**IMPORTANT:** The default branch is `master`, NOT `main`.

### Objective
Replace 6 manual inline CSS spinners with the `<LoadingSpinner />` component in 4 admin pages. This is a retry — previous PRs #82-85 were closed without merge.

### LoadingSpinner Component API
The component is at `src/FuseCP.Portal/Components/Shared/LoadingSpinner.razor`:
```razor
@* Parameters: *@
[Parameter] public SpinnerSize Size { get; set; } = SpinnerSize.Medium;  // Small=h-4/w-4, Medium=h-8/w-8, Large=h-12/w-12
[Parameter] public string? Message { get; set; }
[Parameter] public string? Class { get; set; }

public enum SpinnerSize { Small, Medium, Large }
```
Usage: `<LoadingSpinner />` or `<LoadingSpinner Size="LoadingSpinner.SpinnerSize.Large" Class="mx-auto mb-4" />`

All 4 target files already have `@using FuseCP.Portal.Components.Shared` — no import changes needed.

### Exact Replacements (6 changes total)

**1. AuditDashboard.razor — line 31-33 (page loading)**
Replace:
```razor
        <div class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
```
With:
```razor
        <LoadingSpinner Class="py-12" />
```

**2. OrganizationCreate.razor — line 551 (provisioning overlay, inside modal)**
Replace:
```razor
            <div class="w-12 h-12 border-4 border-default border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
```
With:
```razor
            <LoadingSpinner Size="LoadingSpinner.SpinnerSize.Large" Class="mx-auto mb-4" />
```

**3. Scheduler.razor — line 24-26 (page loading)**
Replace:
```razor
        <div class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
```
With:
```razor
        <LoadingSpinner Class="py-12" />
```

**4. Scheduler.razor — line 130-132 (history modal)**
Replace:
```razor
                        <div class="flex items-center justify-center py-8">
                            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                        </div>
```
With:
```razor
                        <LoadingSpinner Size="LoadingSpinner.SpinnerSize.Small" Class="py-8" />
```

**5. Scheduler.razor — line 195-197 (parameters modal)**
Replace:
```razor
                        <div class="flex items-center justify-center py-4">
                            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                        </div>
```
With:
```razor
                        <LoadingSpinner Size="LoadingSpinner.SpinnerSize.Small" Class="py-4" />
```

**6. TenantList.razor — line 165 (delete modal)**
Replace:
```razor
                    <div class="w-8 h-8 border-4 border-default border-t-error-500 rounded-full animate-spin mb-4"></div>
```
With:
```razor
                    <LoadingSpinner Size="LoadingSpinner.SpinnerSize.Medium" Class="mb-4" />
```

### CRITICAL: Do NOT change anything else
- Keep all `@if` / `else if` / `else` control flow exactly as-is
- Keep all surrounding HTML exactly as-is
- Only replace the specific `<div>` elements shown above

### Files YOU May Modify
- `src/FuseCP.Portal/Components/Pages/Admin/AuditDashboard.razor`
- `src/FuseCP.Portal/Components/Pages/Admin/OrganizationCreate.razor`
- `src/FuseCP.Portal/Components/Pages/Admin/Scheduler.razor`
- `src/FuseCP.Portal/Components/Pages/Admin/TenantList.razor`

### Files You Must NOT Modify
- `.claude/*` (always)
- `CLAUDE.md` (always)
- `C:\FuseCP\*` (always)
- `C:\Przemek\OPENCODE.md` (always)

### Acceptance Criteria
- [ ] `AuditDashboard.razor` uses `<LoadingSpinner />` (1 replacement)
- [ ] `OrganizationCreate.razor` uses `<LoadingSpinner />` for provisioning overlay (1 replacement)
- [ ] `Scheduler.razor` uses `<LoadingSpinner />` in 3 places (page, history modal, parameters modal)
- [ ] `TenantList.razor` uses `<LoadingSpinner />` in delete modal (1 replacement)
- [ ] No manual `animate-spin` spinner divs remain in the 4 files
- [ ] Build passes with 0 errors

### Build & Verify (MUST complete before creating PR)

```bash
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet build --configuration Release
```

Expected: Build succeeded, 0 errors. Do NOT create a PR until build passes.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Implement all 6 replacements | modular-builder | Replace the spinners in the 4 files exactly as specified above |
| Build verification | modular-builder | Run `dotnet build` and fix any errors |

**Agent tier unlocks:** primary + knowledge

---

## History

| Date | Direction | Task | PR | Result |
|------|-----------|------|-----|--------|
| 2026-02-16 | Gemini → Claude | Initial cowork setup | — | Agents synced, protocol established |
| 2026-02-17 | Claude → Gemini | Browser integration tests (API-UI parity) | PR#221 (closed, wrong repo) | Gemini created tests in fusecp-enterprise. Claude fixed runner (timeouts, verdict logic), ran suite. Initial: 4 PASS (36%). |
| 2026-02-17 | Claude | Fix all integration issues | — | Fixed HyperV connection string bug (500→200), AuditLog error handling, rewrote test suite to be Blazor-aware. Final: 11/11 PASS (100%). Report: `fusecp-enterprise/docs/reports/integration-report.md` |
| 2026-02-17 | Claude → Gemini | LoadingSpinner + shared Pagination for log pages | PR#74 | Success. Gemini: correct implementation, build passed, right repo. Claude: fixed 4 review issues (loading UX consistency, error handling, null-coalescing, missing @using). First successful improved handoff. |
| 2026-02-17 | Claude → Gemini | DNS server config + record templates | PR#75 | Success. Spec compliance 12/12 PASS, clean code quality. Claude: removed 23 junk files post-merge, updated .gitignore. DB migration + deploy verified. |
| 2026-02-17 | Claude → Gemini | Oscars 2026 — all 24 categories + voter ID | PR#1 (oscars repo) | Success. Spec 12/12 PASS. Claude fixed 3 issues: Change Name vote-clearing scope, alert→modal, deprecated pageYOffset. Deployed to oscars.ergonet.pl. |
| 2026-02-17 | Claude → Gemini | JSON voter database + voters page + Node.js API | PR#2 (oscars repo) | Success. Claude fixed 2 issues: GET /api/votes response format (array→object), voters.html API parsing. Added IIS reverse proxy (web.config) + scheduled task for Node.js persistence. Deployed to oscars.ergonet.pl. |
| 2026-02-17 | Claude → Gemini | Movie poster images for Oscar nominees | PR#3 (oscars repo) | Success. 15 unique TMDB poster URLs, all verified HTTP 200. Clean implementation, no fixes needed. Deployed to oscars.ergonet.pl. |
| 2026-02-17 | Gemini → Claude | BLOCKED: Permission denied accessing fusecp-enterprise repo | — | Cannot access external directory C:\claude\fusecp-enterprise despite allowed rules. Handoff updated to WAITING_FOR_CLAUDE. |
| 2026-02-17 | Gemini → Claude | Exchange Tenant Isolation Audit | PR#76 | Success. Gemini audited 13 pages, fixed 5. Claude merged + fixed 4 review issues (2 Critical: empty orgSlug/null orgOu bypass, 2 Important: guard logic inversion + toast count). Deployed to Portal. |
| 2026-02-17 | Claude → Gemini | Semantic Color Token Migration (Phase 6.2) | PR#77 | Success. Migration was already ~95% done. Gemini fixed remaining 3 files (sky→primary, text-white→text-button-secondary). Claude fixed 2 more (text-invert on surface-invert, missed secondary button). Verified 0 hardcoded slate/bg-white remaining. |
| 2026-02-18 | Claude → Gemini | PageHeader Component Migration (Phase 6.3a) | PR#78 | Success. Gemini migrated 48/50 pages, Claude review caught 2 missed (MailboxEdit, DistributionListEdit). Gemini fixed in follow-up commit. Claude fixed orphaned `</div>` formatting post-merge. 50 pages now use PageHeader. Deployed to Portal. |
| 2026-02-18 | Claude → Gemini | Form Standardization (.input/.label classes) (Phase 6.3b) | PR#79 | Success. Gemini standardized 42+ pages. Claude resolved merge conflicts with master (Bug #18 type selector), fixed CI formatting (DnsSettingsRepository whitespace), fixed 15+ test failures (Bug #18 Set-Mailbox capture pattern). All 2789 tests pass. Deployed to Portal + API.
| 2026-02-18 | Claude → Gemini | CSS utility class migrations (Phase 6.3c) | PR#80 | Success. Gemini migrated 40+ pages to use new `page-content`, `section-title`, `card-section`, and `section-group` utility classes. Build succeeded with 0 errors. |
| 2026-02-19 | Claude → Gemini | EmptyState component migration (Phase 6.3d) | PR#81 | Closed without merge. Build succeeded but PR was not merged to master. |
| 2026-02-19 | Claude → Gemini | LoadingSpinner migration (Phase 6.3e) | PR#82-85 | 4 attempts, all closed without merge. Build succeeded each time but none merged to master. Re-dispatching as v2. |
