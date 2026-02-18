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
**Branch:** feature/form-standardization
**Priority:** normal
**Repository:** C:\claude\fusecp-enterprise
**Working Directory:** C:\claude\fusecp-enterprise
**PR Target:** master on psklarkins/fusecp-enterprise

### Objective
Standardize all portal page forms to use the `.input` and `.label` CSS classes consistently, replacing inline Tailwind class strings on raw form elements.

### Detailed Requirements

The portal has two form styling patterns:
1. **Standard (correct):** `class="input"` and `class="label"` — defined in `Styles/legacy.css` lines 119-152, theme-aware with CSS custom properties
2. **Non-standard (to fix):** Inline Tailwind strings like `w-full px-4 py-2.5 border border-default rounded-xl text-body focus:border-primary focus:ring-2...`

**Your job:** Find ALL pages using pattern #2 and migrate them to pattern #1.

**What the standard classes look like:**

`.input` (legacy.css:119-144):
```css
.input {
  display: block; width: 100%; border-radius: var(--radius-md);
  background-color: var(--input-bg); color: var(--input-text);
  border: 1px solid var(--input-border); box-shadow: var(--shadow-sm);
  font-size: var(--text-sm); padding: 0.5rem 0.75rem;
  /* Plus :placeholder, :focus, :disabled states */
}
```

`.label` (legacy.css:146-152):
```css
.label {
  display: block; font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-body); margin-bottom: var(--spacing-1);
}
```

**Concrete example — ChangePassword.razor (the worst offender):**

BEFORE (line 51-57):
```razor
<label class="block text-sm font-medium text-body mb-1.5">
    @T["security.current_password"] <span class="text-error">*</span>
</label>
<input type="@(_showCurrentPassword ? "text" : "password")"
       class="w-full px-4 py-2.5 border border-default rounded-xl text-body
              focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all pr-10"
       @bind="_model.CurrentPassword" />
```

AFTER:
```razor
<label class="label">
    @T["security.current_password"] <span class="text-error">*</span>
</label>
<input type="@(_showCurrentPassword ? "text" : "password")"
       class="input pr-10"
       @bind="_model.CurrentPassword"
       placeholder="@T["security.enter_current_password"]" />
```

**Rules:**
1. Replace inline label styling with `class="label"`
2. Replace inline input styling with `class="input"` (add modifiers like `pr-10`, `w-full` only when needed for layout)
3. Apply `class="input"` to `<select>` elements too (they use the same base styling)
4. Apply `class="input"` to `<textarea>` elements (same base styling)
5. Do NOT touch `<input type="checkbox">` or `<input type="radio">` — those have different styling
6. Do NOT touch inputs inside shared components (`TextInput.razor`, `PasswordInput.razor`, `FormField.razor`) — those already have their own styling
7. Do NOT change the Blazor `@bind` / `@onclick` / event handlers — only change `class` attributes
8. Preserve any additional utility classes that aren't part of the base input styling (e.g., `pr-10` for password toggle padding, `bg-surface-secondary` for readonly fields)

**How to audit:** Search for these patterns in `src/FuseCP.Portal/Components/Pages/`:
```bash
# Find non-standard input styling (inline Tailwind on inputs)
grep -rn 'class="w-full.*border.*rounded' --include="*.razor"
grep -rn 'class="block w-full rounded-md border' --include="*.razor"
grep -rn 'class="block text-sm font-medium text-body' --include="*.razor"

# Verify standard pattern is used (should be the majority already)
grep -rn 'class="input' --include="*.razor"
grep -rn 'class="label"' --include="*.razor"
```

### Spec
Inline — see Objective and Detailed Requirements above.

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Styles\legacy.css` — standard `.input`/`.label` definitions
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\Security\ChangePassword.razor` — worst offender, reference for migration
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Shared\TextInput.razor` — DO NOT MODIFY, reference only
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Shared\FormField.razor` — DO NOT MODIFY, reference only
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Shared\PasswordInput.razor` — DO NOT MODIFY, reference only
- `COWORK.md` — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Pages\**\*.razor` — any page file with non-standard form styling

### Files You Must NOT Modify
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Components\Shared\*` — shared components are off-limits
- `C:\claude\fusecp-enterprise\src\FuseCP.Portal\Styles\*` — CSS files are off-limits
- `.claude/*` (always)
- `CLAUDE.md` (always)
- `C:\FuseCP\*` (always)
- `C:\Przemek\OPENCODE.md` (always)

### Acceptance Criteria
- [ ] All raw `<input>` elements (except checkbox/radio) in Pages/ use `class="input"` (with optional modifiers)
- [ ] All raw `<label>` elements in Pages/ use `class="label"`
- [ ] All `<select>` elements in Pages/ use `class="input"`
- [ ] All `<textarea>` elements in Pages/ use `class="input"`
- [ ] No remaining inline Tailwind form styling strings (long `border border-default rounded-xl...` patterns)
- [ ] Shared components in `Components/Shared/` are NOT modified
- [ ] All `@bind`, `@onclick`, event handlers preserved exactly
- [ ] Build passes with 0 errors, 0 warnings

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
| Audit all pages for non-standard form styling | agentic-search | Find every file with inline Tailwind on form elements, report file:line list |
| Migrate form classes in Pages/ | component-designer | For each file found, replace inline Tailwind with `.input`/`.label` classes |
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
