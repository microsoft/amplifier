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
**Branch:** feature/form-standardization
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise
**PR Link:** https://github.com/psklarkins/fusecp-enterprise/pull/79

### Objective
Standardize all portal page forms to use the `.input` and `.label` CSS classes consistently, replacing inline Tailwind class strings on raw form elements.

### Detailed Requirements
... (unchanged) ...

### Acceptance Criteria
- [x] All raw `<input>` elements (except checkbox/radio) in Pages/ use `class="input"` (with optional modifiers)
- [x] All raw `<label>` elements in Pages/ use `class="label"`
- [x] All `<select>` elements in Pages/ use `class="input"`
- [x] All `<textarea>` elements in Pages/ use `class="input"`
- [x] No remaining inline Tailwind form styling strings (long `border border-default rounded-xl...` patterns)
- [x] Shared components in `Components/Shared/` are NOT modified
- [x] All `@bind`, `@onclick`, event handlers preserved exactly
- [x] Build passes with 0 errors, 0 warnings

### Build & Verify (MUST complete before creating PR)

Run these commands and confirm they pass. Do NOT create a PR until all pass:

```bash
cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet build --configuration Release
```

Expected: Build succeeded, 0 errors.

**Result:** Build succeeded, 0 errors, 0 warnings. (Verified by Gemini 2026-02-18)

If build fails, fix the errors before proceeding. Include build output summary in PR description.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Audit all pages for non-standard form styling | agentic-search | Find every file with inline Tailwind on form elements, report file:line list |
| Migrate form classes in Pages/ | modular-builder | For each file found, replace inline Tailwind with `.input`/`.label` classes. This is mechanical find-and-replace, NOT design work. Read the file, replace class strings, write the file. |
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
