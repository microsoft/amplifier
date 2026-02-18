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

**From:** Gemini → Claude
**Branch:** feature/pageheader-migration
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise
**PR Link:** https://github.com/psklarkins/fusecp-enterprise/pull/78

### Objective
Migrate ~49 Portal pages from raw `<h1>` headers to the shared `<PageHeader>` component for consistent page layout across the entire application.

### Detailed Requirements

**The Pattern — BEFORE (typical raw header):**
```html
<div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-semibold text-heading">@T["exchange.mailboxes"]</h1>
            <p class="text-sm text-muted">Some subtitle</p>
        </div>
        <div class="flex gap-2">
            <button class="px-4 py-2 ...">Create</button>
        </div>
    </div>
    <!-- page content -->
</div>
```

**The Pattern — AFTER (using PageHeader):**
```html
<PageHeader Title="@T["exchange.mailboxes"]" Subtitle="Some subtitle">
    <Actions>
        <Button Variant="primary" OnClick="@(() => ...)">
            <svg class="w-4 h-4 mr-2" ...>...</svg>
            Create
        </Button>
    </Actions>
</PageHeader>

<div class="p-4 sm:px-6 lg:px-8 py-8">
    <!-- page content -->
</div>
```

**PageHeader component API** (read `Components/Shared/PageHeader.razor` for full source):
- `Title` (required string) — main heading text
- `Subtitle` (optional string) — muted text below title
- `ShowBreadcrumbs` (bool, default true) — shows breadcrumbs above title
- `Actions` (RenderFragment) — action buttons on the right side

**CRITICAL RULES:**
1. Every page that has a `<h1>` or heading `div` must be converted to `<PageHeader>`
2. Keep existing title text exactly as-is (use `@T[...]` translation keys where they exist)
3. Move action buttons into `<Actions>` fragment — convert raw `<button>` to `<Button>` component where possible
4. Page content below the header should be wrapped in `<div class="p-4 sm:px-6 lg:px-8 py-8">`
5. Remove the old header div entirely — don't leave dead code
6. If a page has a back button (←) before the title, use `ShowBreadcrumbs="true"` (default) and remove the manual back button — breadcrumbs handle navigation
7. Ensure `@using FuseCP.Portal.Components.Shared` is present if not already

**GOOD EXAMPLE to follow** — see `Components/Pages/Admin/TenantList.razor` lines 19-28

**Pages to migrate (ALL of these):**

Exchange (15):
- Mailboxes.razor, MailboxPlans.razor, MailboxEdit.razor, MailboxDetail.razor
- DistributionLists.razor, DistributionListEdit.razor, Contacts.razor
- ResourceMailboxes.razor, PublicFolders.razor, AcceptedDomains.razor
- ActiveSyncPolicies.razor, Disclaimers.razor, StorageUsage.razor
- RetentionPolicies.razor, AddressBookPolicies.razor

ActiveDirectory (6):
- Users.razor, Groups.razor, UserEdit.razor, UserDetail.razor
- PasswordPolicy.razor, OrgStatistics.razor

DNS (3):
- Zones.razor, Records.razor, ZoneEdit.razor

Admin (14):
- Dashboard.razor, AuditLog.razor, AuditDashboard.razor, BugReports.razor
- OperationsLog.razor, OrganizationCreate.razor, OrganizationEdit.razor
- PlatformAdmins.razor, PortalUsers.razor, Reports.razor
- Scheduler.razor, TenantServices.razor, TenantPortalUsers.razor, TestNewPage.razor

Organizations (3):
- Index.razor, Detail.razor, Edit.razor

Settings (4):
- Servers.razor, ServerEdit.razor, DnsSettings.razor, Index.razor

HyperV/Vms (6):
- VirtualMachines.razor, VmDetails.razor, VmEdit.razor
- VmSnapshots.razor, VmCreateWizard.razor, HyperV/Library.razor

Other (2):
- Plans.razor, Security/ChangePassword.razor

**DO NOT modify these files:**
- Login.razor (special branding layout)
- Logout.razor, AccessDenied.razor (minimal pages)
- ComponentDemo.razor (demo page)
- Exchange/Tabs/* (sub-components, not full pages)
- Home.razor, Admin/TenantList.razor (already use PageHeader)

### Spec
Inline — see Objective and Detailed Requirements above.

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `src/FuseCP.Portal/Components/Shared/PageHeader.razor` — the component you're migrating TO
- `src/FuseCP.Portal/Components/Shared/Button.razor` — for converting raw buttons
- `src/FuseCP.Portal/Components/Shared/Breadcrumbs.razor` — included in PageHeader
- `src/FuseCP.Portal/Components/Pages/Admin/TenantList.razor` — EXEMPLAR (already migrated)
- `src/FuseCP.Portal/Components/Pages/Home.razor` — EXEMPLAR (already migrated)
- ALL pages listed in "Pages to migrate" above — read them all before starting
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- All .razor files listed in "Pages to migrate" above (49 files)

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)
- Components/Shared/* (do not modify shared components)
- Components/Pages/Login.razor
- Components/Pages/Home.razor
- Components/Pages/Admin/TenantList.razor
- Components/Pages/Admin/ComponentDemo.razor
- Components/Pages/Exchange/Tabs/* (tab sub-components)

### Acceptance Criteria
- [ ] All 49 listed pages use `<PageHeader>` instead of raw h1/heading divs
- [ ] No raw `<h1 class="text-2xl` or `<h1 class="text-xl` patterns remain in migrated pages
- [ ] Action buttons preserved in `<Actions>` fragment where they existed
- [ ] Page content wrapped in `<div class="p-4 sm:px-6 lg:px-8 py-8">` below PageHeader
- [ ] All migrated pages have `@using FuseCP.Portal.Components.Shared` (or already inherited)
- [ ] No functional changes — only header layout standardization
- [ ] All tests pass
- [ ] No lint errors
- [ ] Code committed to feature branch with clear messages

### Build & Verify (MUST complete before creating PR)

Run these commands and confirm they pass. Do NOT create a PR until all pass:

```bash
cd /c/claude/fusecp-enterprise && dotnet build --no-incremental 2>&1 | tail -5
```

Expected: Build succeeded, 0 errors, 0 warnings.

If build fails, fix the errors before proceeding. Include build output summary in PR description.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Read all 49 pages, extract current header patterns | agentic-search | Build a table mapping each file to its current title, subtitle, actions |
| Migrate Exchange pages (15 files) | component-designer | Apply PageHeader pattern to all Exchange pages |
| Migrate ActiveDirectory pages (6 files) | component-designer | Apply PageHeader pattern to all AD pages |
| Migrate DNS pages (3 files) | component-designer | Apply PageHeader pattern to all DNS pages |
| Migrate Admin pages (14 files) | component-designer | Apply PageHeader pattern to all Admin pages |
| Migrate remaining pages (11 files) | component-designer | Organizations, Settings, HyperV, Plans, Security |
| Verify build passes | modular-builder | Run `dotnet build --no-incremental`, fix any errors |

**How to use agents:** For each row above, dispatch the agent as a subagent with a focused prompt describing exactly what to implement. The agent will do the work and return results. Review the output, fix any issues, then move to the next task.

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
| 2026-02-17 | Gemini → Claude | PageHeader Component Migration | PR#78 | Success. Migrated 48 pages to `<PageHeader>`. Standardized padding and navigation. Build passes. |
