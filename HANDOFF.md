# Amplifier Cowork — Task Handoff

## Dispatch Status: REVIEWING

PR: https://github.com/psklarkins/fusecp-enterprise/pull/95

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
**Branch:** feature/p64-component-polish
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** main on psklarkins/fusecp-enterprise

### Objective
Execute P6.4 Component Library Polish — migrate raw palette colors to semantic tokens, raw HTML elements to shared components (`<Badge>`, `<Button>`), and create frontend Style Guide documentation.

### Detailed Requirements

This is a systematic page-by-page sweep of all portal Razor files. The implementation plan at `docs/plans/2026-02-20-p64-component-polish.md` contains **exact before/after code** for every change. Follow it precisely.

**Three types of changes:**

1. **Palette color → semantic token** — Replace raw Tailwind palette colors (`bg-orange-100 text-orange-700`, `bg-purple-100 text-purple-700`, `hover:bg-purple-50`, `dark:bg-blue-900`, etc.) with semantic tokens (`bg-warning-muted text-warning-emphasis`, `bg-info-muted text-info-emphasis`, `hover:bg-hover`, etc.). The full mapping table is in the plan's "Semantic Token Reference" section.

2. **Inline `<span>` badges → `<Badge>` component** — Replace `<span class="px-2 py-1 text-xs font-medium rounded-full @GetStatusClass(...)">` with `<Badge Class="@GetStatusClass(...)" Size="BadgeSize.Small">`. Keep existing helper methods (`GetStatusClass`, `GetPriorityClass`, `GetTypeClass`) and pass via `Class=` attribute.

3. **Raw `<button>` → `<Button>` component** — Replace `<button class="px-4 py-2 text-sm ..." @onclick="...">` with `<Button Variant="primary|secondary|danger|ghost|link" Size="sm|md" OnClick="...">`. Modal cancel = `secondary`, submit = `primary`, delete = `danger`, table actions = `ghost` or `link`.

**Task 6 (final):** Create `docs/frontend/STYLE_GUIDE.md` documenting the design token system, color rules, component usage patterns, and before/after migration examples.

### Spec
`docs/plans/2026-02-20-p64-component-polish.md` — contains all 6 tasks with exact before/after code snippets, file paths, and line number hints.

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `HANDOFF.md` — this file, refresh protocol understanding
- `docs/plans/2026-02-20-p64-component-polish.md` — the implementation plan (PRIMARY reference)
- `src/FuseCP.Portal/Styles/app.css` — semantic token definitions (lines 606-836)
- `src/FuseCP.Portal/Components/Shared/Badge.razor` — Badge component API
- `src/FuseCP.Portal/Components/Shared/Button.razor` — Button component API

### Files YOU May Modify
- `src/FuseCP.Portal/Components/Pages/Admin/BugReports.razor` (Task 1)
- `src/FuseCP.Portal/Components/Pages/Admin/OperationsLog.razor` (Task 2)
- `src/FuseCP.Portal/Components/Pages/Admin/Scheduler.razor` (Task 2)
- `src/FuseCP.Portal/Components/Pages/Admin/PortalUsers.razor` (Task 3)
- `src/FuseCP.Portal/Components/Pages/Admin/PlatformAdmins.razor` (Task 3)
- `src/FuseCP.Portal/Components/Pages/Admin/TenantList.razor` (Task 4)
- `src/FuseCP.Portal/Components/Pages/Admin/TenantPortalUsers.razor` (Task 4)
- `src/FuseCP.Portal/Components/Pages/Admin/TenantServices.razor` (Task 4)
- `src/FuseCP.Portal/Components/Pages/Settings/DnsSettings.razor` (Task 5)
- `src/FuseCP.Portal/Components/Pages/HyperV/Library.razor` (Task 5)
- `src/FuseCP.Portal/Components/Pages/AccessDenied.razor` (Task 5)
- `src/FuseCP.Portal/Components/Pages/Admin/Reports.razor` (Task 5)
- `src/FuseCP.Portal/Components/Pages/Exchange/MailboxEdit.razor` (Task 5)
- `docs/frontend/STYLE_GUIDE.md` (Task 6 — new file)

### Files You Must NOT Modify
- `.claude/*` (always)
- `CLAUDE.md` (always)
- `C:\FuseCP\*` (always)
- `C:\Przemek\OPENCODE.md` (always)
- `src/FuseCP.Portal/Components/Pages/Admin/ComponentDemo.razor` (intentionally uses raw colors for demo)
- Any shared component in `src/FuseCP.Portal/Components/Shared/` (they are already token-aware)

### Acceptance Criteria
- [ ] All raw palette colors in the 13 target files replaced with semantic tokens
- [ ] All inline badge `<span>` elements migrated to `<Badge>` component
- [ ] All raw `<button>` elements migrated to `<Button>` component
- [ ] No `dark:` Tailwind prefix usage remaining (only `[data-theme="dark"]` system)
- [ ] `docs/frontend/STYLE_GUIDE.md` created with token system, color rules, component usage, patterns
- [ ] `ComponentDemo.razor` is untouched
- [ ] Build succeeds with 0 errors
- [ ] All tests pass
- [ ] Code committed to feature branch with clear messages per task

### Build & Verify (MUST complete before creating PR)

```bash
cd /c/claude/fusecp-enterprise && dotnet build --configuration Release src/FuseCP.Portal/FuseCP.Portal.csproj
```

Expected: Build succeeded, 0 errors.

After all tasks, run the palette color verification:
```bash
grep -rn "bg-orange-1\|bg-purple-1\|bg-blue-1\|bg-teal-1\|bg-cyan-1\|text-orange-[0-9]\|text-purple-[0-9]\|hover:bg-purple\|hover:bg-orange\|hover:text-purple\|hover:text-orange\|dark:bg-\|dark:text-\|btn btn-" src/FuseCP.Portal/Components/Pages/ --include="*.razor" | grep -v "ComponentDemo.razor"
```

Expected: 0 results.

If build fails, fix the errors before proceeding. Include build output summary in PR description.

### Implementation Notes

**Do ALL implementation in your main session.** OpenCode subagents are read-only — use them only for codebase search/research. Use `/user:handoff` to start, `/user:review-pr` before creating PR.

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
| 2026-02-19 | Gemini → Claude | EmptyState migration (Phase 6.3d) v2 | PR#87 | Success. 11 empty states in 9 files. Build 0 errors. Merged + deployed to Portal. No fixes needed. |
