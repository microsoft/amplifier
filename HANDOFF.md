# Amplifier Cowork — Task Handoff

## Dispatch Status: PR_READY

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
**Branch:** feature/empty-state-migration
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise

### Getting Started (run these commands first)
```bash
cd /c/claude/fusecp-enterprise
git checkout master && git pull origin master && git checkout -b feature/empty-state-migration
```
**IMPORTANT:** The default branch is `master`, NOT `main`.

### Objective
Replace 11 inline empty state divs with the `<EmptyState />` shared component across 9 portal pages.

### EmptyState Component API
The component is at `src/FuseCP.Portal/Components/Shared/EmptyState.razor`:
```razor
[Parameter] public string? Title { get; set; }          // defaults to T["common.no_data"] if null
[Parameter] public string? Description { get; set; }
[Parameter] public RenderFragment? Icon { get; set; }    // defaults to inbox SVG if null
[Parameter] public RenderFragment? Action { get; set; }  // optional action button area
[Parameter] public string? Class { get; set; }
```
Usage: `<EmptyState Title="@T[\"key\"]" Description="@T[\"desc_key\"]" />` — uses default icon.
All 9 target files already have `@using FuseCP.Portal.Components.Shared` — no import changes needed.

### Exact Replacements (11 changes total)

#### Group A: "No org selected" states (5 files, same pattern)

These all show when `_selectedOrganizationId == 0` and display `T["common.navigate_from_tenants"]`. Replace the inline div+svg with EmptyState using default icon.

**1. ActiveDirectory/Groups.razor — lines 69-76**
Replace:
```razor
        <Card>
            <div class="text-center py-8">
                <svg class="w-16 h-16 text-faint mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                <p class="text-muted">@T["common.navigate_from_tenants"]</p>
            </div>
        </Card>
```
With:
```razor
        <Card>
            <EmptyState Title="@T["common.navigate_from_tenants"]" />
        </Card>
```

**2. Exchange/Disclaimers.razor — lines 64-71**
Replace:
```razor
        <Card>
            <div class="text-center py-8">
                <svg class="w-16 h-16 text-faint mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <p class="text-muted">@T["common.navigate_from_tenants"]</p>
            </div>
        </Card>
```
With:
```razor
        <Card>
            <EmptyState Title="@T["common.navigate_from_tenants"]" />
        </Card>
```

**3. Exchange/PublicFolders.razor — lines 77-84**
Replace:
```razor
        <Card>
            <div class="text-center py-8">
                <svg class="w-16 h-16 text-faint mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                </svg>
                <p class="text-muted">@T["common.navigate_from_tenants"]</p>
            </div>
        </Card>
```
With:
```razor
        <Card>
            <EmptyState Title="@T["common.navigate_from_tenants"]" />
        </Card>
```

**4. Exchange/ResourceMailboxes.razor — lines 76-83**
Replace:
```razor
        <Card>
            <div class="text-center py-8">
                <svg class="w-16 h-16 text-faint mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
                <p class="text-muted">@T["common.navigate_from_tenants"]</p>
            </div>
        </Card>
```
With:
```razor
        <Card>
            <EmptyState Title="@T["common.navigate_from_tenants"]" />
        </Card>
```

**5. Exchange/RetentionPolicies.razor — lines 56-63**
Replace:
```razor
        <Card>
            <div class="text-center py-8">
                <svg class="w-16 h-16 text-faint mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                </svg>
                <p class="text-muted">@T["common.navigate_from_tenants"]</p>
            </div>
        </Card>
```
With:
```razor
        <Card>
            <EmptyState Title="@T["common.navigate_from_tenants"]" />
        </Card>
```

#### Group B: True empty data states (5 files)

**6. ActiveDirectory/Groups.razor — line 196 (no group members)**
Replace:
```razor
                <p class="text-muted text-center py-4">@T["ad.no_members"]</p>
```
With:
```razor
                <EmptyState Title="@T["ad.no_members"]" Class="py-4" />
```

**7. Exchange/Tabs/MailboxMobileDevicesTab.razor — lines 25-31 (no mobile devices)**
Replace:
```razor
        <div class="text-center py-8">
            <svg class="mx-auto h-12 w-12 text-faint" width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
            <h4 class="mt-2 text-sm font-medium text-heading">@T["exchange.no_mobile_devices"]</h4>
            <p class="mt-1 text-sm text-muted">@T["exchange.no_mobile_devices_hint"]</p>
        </div>
```
With:
```razor
        <EmptyState Title="@T["exchange.no_mobile_devices"]" Description="@T["exchange.no_mobile_devices_hint"]" />
```

**8. HyperV/Library.razor — lines 66-72 (no items found)**
Replace:
```razor
            <div class="text-center py-12">
                <svg class="mx-auto h-12 w-12 text-faint" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                </svg>
                <h3 class="mt-2 text-sm font-medium text-heading">@T["No items found"]</h3>
                <p class="mt-1 text-sm text-muted">@T["The specified path does not contain any library items."]</p>
            </div>
```
With:
```razor
            <EmptyState Title="@T["No items found"]" Description="@T["The specified path does not contain any library items."]" />
```

**9. Settings/Servers.razor — lines 38-48 (no servers, with action button)**
Replace:
```razor
            <div class="text-center py-12">
                <svg class="mx-auto h-12 w-12 text-faint" width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
                </svg>
                <h3 class="mt-2 text-sm font-medium text-heading">@T["No servers configured"]</h3>
                <p class="mt-1 text-sm text-muted">@T["Get started by adding a hosting server."]</p>
                <div class="mt-6">
                    <Button Variant="primary" OnClick="@(() => Navigation.NavigateTo("/settings/servers/new"))">
                        @T["Add Server"]
                    </Button>
                </div>
```
With:
```razor
            <EmptyState Title="@T["No servers configured"]" Description="@T["Get started by adding a hosting server."]">
                <Action>
                    <Button Variant="primary" OnClick="@(() => Navigation.NavigateTo("/settings/servers/new"))">
                        @T["Add Server"]
                    </Button>
                </Action>
            </EmptyState>
```

**10. Settings/DnsSettings.razor — lines 84-86 (inside DataTable EmptyTemplate)**
Replace:
```razor
                            <div class="text-center py-12">
                                <p class="text-muted">@T["No Exchange DNS templates configured"]</p>
                            </div>
```
With:
```razor
                            <EmptyState Title="@T["No Exchange DNS templates configured"]" />
```

### CRITICAL: Do NOT change anything else
- Keep all `@if` / `else if` / `else` control flow exactly as-is
- Keep all surrounding HTML (`<Card>`, `<EmptyTemplate>`, etc.) exactly as-is
- Only replace the specific inline empty state markup shown above
- Do NOT modify the MailboxArchiveTab or MailboxLitigationHoldTab — those have embedded forms, not simple empty states

### Files YOU May Modify
- `src/FuseCP.Portal/Components/Pages/ActiveDirectory/Groups.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/Disclaimers.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/PublicFolders.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/ResourceMailboxes.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/RetentionPolicies.razor`
- `src/FuseCP.Portal/Components/Pages/Exchange/Tabs/MailboxMobileDevicesTab.razor`
- `src/FuseCP.Portal/Components/Pages/HyperV/Library.razor`
- `src/FuseCP.Portal/Components/Pages/Settings/DnsSettings.razor`
- `src/FuseCP.Portal/Components/Pages/Settings/Servers.razor`

### Files You Must NOT Modify
- `.claude/*` (always)
- `CLAUDE.md` (always)
- `C:\FuseCP\*` (always)
- `C:\Przemek\OPENCODE.md` (always)
- `Exchange/Tabs/MailboxArchiveTab.razor` (has embedded enable form)
- `Exchange/Tabs/MailboxLitigationHoldTab.razor` (has embedded enable form)

### Acceptance Criteria
- [ ] 5 "no org selected" states replaced with `<EmptyState Title="@T["common.navigate_from_tenants"]" />`
- [ ] Groups.razor "no members" state replaced with `<EmptyState>`
- [ ] MailboxMobileDevicesTab "no devices" replaced with `<EmptyState>`
- [ ] Library.razor "no items" replaced with `<EmptyState>`
- [ ] Servers.razor "no servers" replaced with `<EmptyState>` including `<Action>` button
- [ ] DnsSettings.razor "no templates" replaced with `<EmptyState>`
- [ ] No remaining inline `text-center py-8/py-12` empty state divs in the 9 target files
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
| Replace Group A (5 no-org-selected states) | modular-builder | Replace the 5 inline divs exactly as specified |
| Replace Group B (5 true empty states) | modular-builder | Replace the 5 inline divs exactly as specified |
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
| 2026-02-19 | Gemini → Claude | LoadingSpinner migration (Phase 6.3e) v2 | PR#86 | Success. 6 spinners in 4 files. Merged + deployed to Portal. No fixes needed. |
| 2026-02-19 | Gemini → Claude | EmptyState migration (Phase 6.3d) | PR#87 | Success. Build succeeded (0 errors). Replaced 11 empty states in 9 files. |
