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
**Branch:** feature/semantic-color-migration
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise

### Objective
Migrate all remaining hardcoded Tailwind color classes to semantic theme tokens across Portal pages and shared components (Phase 6.2 completion).

### Detailed Requirements

The FuseCP Portal already has a complete theme token system defined in `Styles/app.css`:
- Semantic CSS custom properties for light/dark modes (`:root` and `[data-theme="dark"]`)
- Custom Tailwind utilities via `@utility` directives
- ThemeToggle component with light/dark/system modes

**The problem:** ~53 hardcoded color references remain across 20 files, preventing proper dark mode support. These use raw Tailwind palette classes (`text-slate-900`, `bg-white`, `border-slate-200`) instead of semantic tokens (`text-heading`, `bg-surface`, `border-default`).

**Your job:** Replace every hardcoded color class with its semantic equivalent. The mapping is:

#### Color Class → Semantic Token Mapping

| Hardcoded Class | Semantic Token | When to use |
|----------------|----------------|-------------|
| `text-slate-900`, `text-gray-900` | `text-heading` | Page titles, headings, primary text |
| `text-slate-700`, `text-gray-700` | `text-body` | Body text, descriptions |
| `text-slate-500`, `text-gray-500` | `text-muted` | Secondary text, labels, captions |
| `text-slate-400`, `text-gray-400` | `text-faint` | Placeholder-like text, very subtle |
| `text-white` (on dark backgrounds) | `text-invert` | Text on inverted/dark surfaces |
| `text-white` (on sidebar) | `text-sidebar` | Sidebar text (keep as-is if already correct) |
| `bg-white` | `bg-surface` | Card backgrounds, main content areas |
| `bg-slate-50`, `bg-gray-50` | `bg-surface-secondary` | Subtle backgrounds, table headers |
| `bg-slate-100`, `bg-gray-100` | `bg-surface-tertiary` | Tertiary surfaces, code blocks |
| `bg-slate-900` | `bg-surface-invert` | Inverted backgrounds |
| `border-slate-200`, `border-gray-200` | `border-default` | Standard borders |
| `border-slate-300`, `border-gray-300` | `border-strong` | Emphasized borders, input borders |
| `border-slate-100` | `border-muted` | Subtle borders |
| `text-sky-600`, `text-blue-600` | `text-icon` | Icon colors (already defined as `--color-icon`) |

**IMPORTANT EXCEPTIONS — Do NOT replace:**
- Color classes inside `bg-sky-100`, `bg-blue-100`, `bg-green-100`, `bg-red-100` etc. used for colored icon circles — these are intentional accent colors, not theme-dependent
- `text-primary-600`, `text-error-600`, `text-success-600`, `text-warning-600` — these already use the palette tokens and switch properly
- Sidebar-specific colors — the sidebar stays dark in both themes, keep its hardcoded colors
- Login page colors — the login page has its own distinct styling

#### Files to Modify (with occurrence counts)

**Pages (17 files, ~46 occurrences):**
1. `Components/Pages/Home.razor` — 4 occurrences
2. `Components/Pages/Admin/PortalUsers.razor` — 6 occurrences
3. `Components/Pages/Admin/TenantPortalUsers.razor` — 4 occurrences
4. `Components/Pages/Admin/TenantList.razor` — 3 occurrences
5. `Components/Pages/Admin/ComponentDemo.razor` — 15 occurrences
6. `Components/Pages/Admin/BugReports.razor` — 2 occurrences
7. `Components/Pages/Admin/PlatformAdmins.razor` — 2 occurrences
8. `Components/Pages/Admin/OperationsLog.razor` — 1 occurrence
9. `Components/Pages/Admin/AuditLog.razor` — 1 occurrence
10. `Components/Pages/Admin/AuditDashboard.razor` — 1 occurrence
11. `Components/Pages/Admin/Scheduler.razor` — 1 occurrence
12. `Components/Pages/Admin/TenantServices.razor` — 1 occurrence
13. `Components/Pages/Admin/TestNewPage.razor` — 1 occurrence
14. `Components/Pages/VmDetails.razor` — 1 occurrence
15. `Components/Pages/Plans.razor` — 1 occurrence
16. `Components/Pages/Vms/VmCreateWizard.razor` — 1 occurrence
17. `Components/Pages/Vms/VmEdit.razor` — 1 occurrence

**Shared Components (3 files, ~7 occurrences):**
18. `Components/Shared/Button.razor` — 5 occurrences
19. `Components/Shared/Pagination.razor` — 1 occurrence
20. `Components/Shared/WizardForm.razor` — 1 occurrence

#### How to Verify Your Work

After migration, run this grep to confirm zero hardcoded colors remain:
```bash
grep -rn "text-slate-\|bg-slate-\|border-slate-\|bg-white\|text-white" src/FuseCP.Portal/Components/Pages/ src/FuseCP.Portal/Components/Shared/ --include="*.razor" | grep -v "// " | wc -l
```
Expected: 0 (or only legitimate exceptions listed above).

### Spec
Inline — see Objective and Detailed Requirements above.

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `COWORK.md` — refresh protocol understanding
- This task section of `HANDOFF.md`
- `src/FuseCP.Portal/Styles/app.css` — **READ FULLY** — contains the complete token system, semantic variables, and `@utility` definitions you'll be mapping to
- All 20 files listed above — read each one to find the hardcoded color references

### Files YOU May Modify
- `src/FuseCP.Portal/Components/Pages/Home.razor`
- `src/FuseCP.Portal/Components/Pages/Admin/*.razor` (all admin pages listed)
- `src/FuseCP.Portal/Components/Pages/VmDetails.razor`
- `src/FuseCP.Portal/Components/Pages/Plans.razor`
- `src/FuseCP.Portal/Components/Pages/Vms/VmCreateWizard.razor`
- `src/FuseCP.Portal/Components/Pages/Vms/VmEdit.razor`
- `src/FuseCP.Portal/Components/Shared/Button.razor`
- `src/FuseCP.Portal/Components/Shared/Pagination.razor`
- `src/FuseCP.Portal/Components/Shared/WizardForm.razor`

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)
- `src/FuseCP.Portal/Styles/app.css` — the token system is complete, do NOT change it
- `src/FuseCP.Portal/Components/Shared/ThemeToggle.razor` — already working
- `src/FuseCP.Portal/Services/ThemeService.cs` — already working
- Exchange pages (`Components/Pages/Exchange/*.razor`) — already migrated

### Acceptance Criteria
- [ ] All hardcoded `text-slate-*`, `bg-slate-*`, `border-slate-*`, `bg-white`, `text-white` classes in the 20 listed files replaced with semantic tokens
- [ ] Exceptions preserved (accent icon backgrounds, sidebar, login page)
- [ ] No visual regressions in light mode — pages should look identical to before
- [ ] Dark mode properly inverts all migrated elements
- [ ] Grep verification returns 0 (or only legitimate exceptions)
- [ ] Build passes: `dotnet build --no-incremental` from repo root
- [ ] Code committed to feature branch with clear messages

### Build & Verify (MUST complete before creating PR)

```bash
cd /c/claude/fusecp-enterprise && dotnet build --no-incremental 2>&1 | tail -5
```

Expected: Build succeeded, 0 errors.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Read app.css and build token mapping reference | agentic-search | Load Styles/app.css, extract all @utility definitions, create mapping cheatsheet |
| Migrate Admin pages (10 files, ~35 occurrences) | component-designer | Replace hardcoded colors with semantic tokens in all Admin/*.razor files |
| Migrate other Pages (5 files, ~8 occurrences) | component-designer | Replace colors in Home, VmDetails, Plans, Vms/* |
| Migrate Shared components (3 files, ~7 occurrences) | component-designer | Replace colors in Button, Pagination, WizardForm |
| Verify migration completeness | agentic-search | Run grep verification, confirm 0 remaining hardcoded colors |
| Build verification | test-coverage | Run dotnet build, verify no errors |

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
