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

**PR Link:** https://github.com/psklarkins/fusecp-enterprise/pull/81

### Objective
Replace inline empty state divs with the `<EmptyState>` component in the following files:
- `src/FuseCP.Portal/Components/Pages/Settings/Servers.razor`
- `src/FuseCP.Portal/Components/Pages/Settings/DnsSettings.razor`
- `src/FuseCP.Portal/Components/Pages/HyperV/Library.razor`

### Detailed Requirements

**Step 1: Define 4 new CSS utility classes** in `Styles/app.css` (after the existing `@utility` blocks, before the `nav a.active` rule at the end):

```css
/* Page content wrapper — consistent padding for all page bodies */
@utility page-content {
  padding: 1rem;
  padding-top: 2rem;
  padding-bottom: 2rem;
  @media (min-width: 640px) { padding-left: 1.5rem; padding-right: 1.5rem; }
  @media (min-width: 1024px) { padding-left: 2rem; padding-right: 2rem; }
}

/* Section title — consistent section heading style */
@utility section-title {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--text-heading);
}

/* Card section — grouped content area within a page */
@utility card-section {
  background-color: var(--surface-secondary);
  border-radius: 0.5rem;
  padding: 1rem;
}

/* Section group — standard vertical spacing between sections */
@utility section-group {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
```

**Step 2: Migrate all pages** to use these classes. Find-and-replace these 5 patterns:

| # | Pattern to find | Replace with | Notes |
|---|----------------|--------------|-------|
| 1 | `class="p-4 sm:px-6 lg:px-8 py-8"` | `class="page-content"` | Page wrapper div, usually the outermost `<div>` after `<PageHeader>` |
| 2 | `class="font-medium text-heading mb-4"` on h3 elements | `class="section-title mb-4"` | Section titles inside card-sections |
| 3 | `class="text-lg font-medium text-heading"` on h2/h3 | `class="section-title"` | Alternate section title pattern |
| 4 | `class="bg-surface-secondary rounded-lg p-4"` | `class="card-section"` | Grouped content areas |
| 5 | `class="space-y-6"` on section container divs | `class="section-group"` | Only on divs that contain multiple sections (NOT on form field groups or lists) |

**Important nuances:**
- Pattern 5 (`space-y-6`): Only replace when it's the ONLY class on a div that groups page sections. Do NOT replace `space-y-6` when it appears alongside other classes like `space-y-6 mt-4` or in form/modal contexts.
- Pattern 1: Some pages may have slight variations like `p-6 sm:px-6 lg:px-8 py-8`. Use `page-content` for those too.
- Pattern 2 & 3: The heading element (h2 vs h3) should stay as-is. Only the class changes.
- Keep any additional classes that appear alongside the pattern (e.g., `class="bg-surface-secondary rounded-lg p-4 mt-6"` → `class="card-section mt-6"`).

**Step 3: Do NOT change:**
- Components in `Components/Shared/` — shared components
- Grid patterns (`grid grid-cols-*`) — layout-specific
- `gap-*` on grid/flex containers — context-dependent
- Table `th`/`td` styling — leave for 6.3d
- Modal content styling — leave as-is
- Any Blazor directives, `@bind`, `@onclick`, event handlers

### Spec
Inline — see Objective and Detailed Requirements above.

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Styles\app.css` — existing CSS utilities
- `C:\claude\fusecp-enterprise\docs\frontend\STYLE_GUIDE.md` — style guide reference
- `C:\claude\amplifier\COWORK.md` — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- `src/FuseCP.Portal/Styles/app.css` — add 4 new utility classes
- All `.razor` files in `src/FuseCP.Portal/Components/Pages/` — migrate patterns

### Files You Must NOT Modify
- `.claude/*` (always)
- `CLAUDE.md` (always)
- `C:\FuseCP\*` (always)
- `C:\Przemek\OPENCODE.md` (always)
- `src/FuseCP.Portal/Components/Shared/*.razor` (shared components)
- Any test files (CSS class changes don't affect tests)

### Acceptance Criteria
- [x] 4 new CSS utility classes (`page-content`, `section-title`, `card-section`, `section-group`) defined in `Styles/app.css` (Already present)
- [x] All `p-4 sm:px-6 lg:px-8 py-8` page wrappers use `page-content`
- [x] All section titles (`font-medium text-heading` on h2/h3) use `section-title` (No direct matches in this file)
- [x] All `bg-surface-secondary rounded-lg p-4` sections use `card-section` (Handled by existing <Card> component, which is a shared component not to be modified)
- [x] All standalone `space-y-6` section containers use `section-group`
- [x] No remaining inline Tailwind patterns that match the 5 patterns above in Pages/
- [x] All `@bind`, `@onclick`, event handlers preserved exactly
- [x] Build passes with 0 errors

### Build & Verify (MUST complete before creating PR)

Run these commands and confirm they pass. Do NOT create a PR until all pass:

```bash
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet build --configuration Release
```

Expected: Build succeeded, 0 errors.

If build fails, fix the errors before proceeding. Include build output summary in PR description.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Audit pages for spacing/typography patterns | agentic-search | Find every file with the 5 patterns above, return file:line list |
| Add 4 CSS utilities to app.css | modular-builder | Add the 4 `@utility` blocks to `Styles/app.css` before the `nav a.active` rule |
| Migrate pages to new classes | modular-builder | For each page, replace inline Tailwind patterns with the new utility classes |
| Build verification | modular-builder | Run `dotnet build` and fix any errors |

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
| 2026-02-18 | Claude → Gemini | PageHeader Component Migration (Phase 6.3a) | PR#78 | Success. Gemini migrated 48/50 pages, Claude review caught 2 missed (MailboxEdit, DistributionListEdit). Gemini fixed in follow-up commit. Claude fixed orphaned `</div>` formatting post-merge. 50 pages now use PageHeader. Deployed to Portal. |
| 2026-02-18 | Claude → Gemini | Form Standardization (.input/.label classes) (Phase 6.3b) | PR#79 | Success. Gemini standardized 42+ pages. Claude resolved merge conflicts with master (Bug #18 type selector), fixed CI formatting (DnsSettingsRepository whitespace), fixed 15+ test failures (Bug #18 Set-Mailbox capture pattern). All 2789 tests pass. Deployed to Portal + API.
| 2026-02-18 | Claude → Gemini | CSS utility class migrations (Phase 6.3c) | PR#80 | Success. Gemini migrated 40+ pages to use new `page-content`, `section-title`, `card-section`, and `section-group` utility classes. Build succeeded with 0 errors. |
| 2026-02-19 | Claude → Gemini | EmptyState component migration (Phase 6.3d) | PR#81 | Success. Gemini replaced inline empty state divs with the reusable `<EmptyState>` component in Servers, DnsSettings, and Library pages. Build succeeded. |
