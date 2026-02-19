# Amplifier Cowork — Task Handoff

## Dispatch Status: IN_PROGRESS

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
**Branch:** feature/loading-spinner-migration
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise

### Objective
Replace manual loading spinners with the `<LoadingSpinner />` component in the following files:
- `src/FuseCP.Portal/Components/Pages/Admin/AuditDashboard.razor`
- `src/FuseCP.Portal/Components/Pages/Admin/OrganizationCreate.razor`
- `src/FuseCP.Portal/Components/Pages/Admin/Scheduler.razor`
- `src/FuseCP.Portal/Components/Pages/Admin/TenantList.razor`

### Detailed Requirements

**Step 1: Migrate AuditDashboard.razor**
- Replace the inline spinner `div` (approx. line 31-33) with `<LoadingSpinner Class="py-12" />`.

**Step 2: Migrate OrganizationCreate.razor**
- Replace the provisioning overlay spinner `div` (approx. line 551) with `<LoadingSpinner Size="LoadingSpinner.SpinnerSize.Large" Class="mx-auto mb-4" />`.

**Step 3: Migrate Scheduler.razor**
- Replace the main page loading spinner (approx. line 24-26) with `<LoadingSpinner Class="py-12" />`.
- Replace the history modal spinner (approx. line 130-132) with `<LoadingSpinner Size="LoadingSpinner.SpinnerSize.Small" Class="py-8" />`.
- Replace the parameters modal spinner (approx. line 195-197) with `<LoadingSpinner Size="LoadingSpinner.SpinnerSize.Small" Class="py-4" />`.

**Step 4: Migrate TenantList.razor**
- Replace the delete confirmation modal spinner (approx. line 165) with `<LoadingSpinner Size="LoadingSpinner.SpinnerSize.Medium" Class="mb-4" />`.

**Important nuances:**
- Ensure `@using FuseCP.Portal.Components.Shared` is present (it is in all target files).
- Preserve existing logic (`@if (_loading)`, etc.) and only replace the HTML/CSS spinner markup.
- Use the appropriate `Size` enum from `LoadingSpinner`.

### Spec
Standardize loading indicators across the portal using the shared component.

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Shared\LoadingSpinner.razor` — component definition
- `C:\claude\amplifier\COWORK.md` — refresh protocol understanding
- This task section of HANDOFF.md

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
- [ ] `AuditDashboard.razor` uses `<LoadingSpinner />`
- [ ] `OrganizationCreate.razor` uses `<LoadingSpinner />` for provisioning overlay
- [ ] `Scheduler.razor` uses `<LoadingSpinner />` in page, history, and parameters views
- [ ] `TenantList.razor` uses `<LoadingSpinner />` in delete modal
- [ ] All `Size` parameters match the original visual intent
- [ ] Build passes with 0 errors

### Build & Verify (MUST complete before creating PR)

Run these commands and confirm they pass. Do NOT create a PR until all pass:

```bash
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet build --configuration Release
```

Expected: Build succeeded, 0 errors.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Implement migrations | modular-builder | Replace the spinners in the 4 files as specified |
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
| 2026-02-19 | Claude → Gemini | EmptyState component migration (Phase 6.3d) | PR#81 | Success. Gemini replaced inline empty state divs with the reusable `<EmptyState>` component in Servers, DnsSettings, and Library pages. Build succeeded. |
