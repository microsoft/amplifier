# Amplifier Cowork — Task Handoff

## Dispatch Status: IDLE

> **Protocol:** Only the designated receiver should act.
> - Claude acts on: `IDLE`, `PR_READY`, `REVIEWING`, `DEPLOYING`
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
**Branch:** feature/oscars-voting-page
**Priority:** normal
**Repository:** C:\claude\amplifier
**Working Directory:** C:\claude\amplifier
**PR Target:** main on psklarkins/amplifier
**PR Link:** https://github.com/psklarkins/amplifier/pull/9

### Objective
Build a standalone Oscars voting page (HTML/CSS/JS) that will be hosted at https://oscars.ergonet.pl, allowing visitors to vote for their favorite movies.

### Detailed Requirements

Create a self-contained web page in `oscars/` directory at the repo root:

**File structure:**
```
oscars/
├── index.html      # Main page
├── style.css       # Styles
└── script.js       # Voting logic
```

**Page requirements:**
1. **Header:** "Oscars 2026 — Vote for Your Favorites" with gold/black Hollywood theme
2. **Movie list:** Display 8-10 nominated movies as cards with:
   - Movie title
   - Category (Best Picture, Best Director, etc.)
   - A "Vote" button per movie
3. **Voting logic (client-side only):**
   - Store votes in localStorage (no backend needed)
   - Show vote count per movie
   - One vote per category per visitor (enforce via localStorage)
   - Show "You already voted in this category" if they try again
4. **Results section:** Live tally of all votes (from localStorage)
5. **Design:** Clean, modern, dark theme with gold accents (#FFD700). Mobile responsive.
6. **No external dependencies** — pure HTML/CSS/JS, no frameworks, no CDNs

**Movie data to include (hardcoded):**

| Movie | Category |
|-------|----------|
| The Brutalist | Best Picture |
| Anora | Best Picture |
| Conclave | Best Picture |
| Emilia Pérez | Best Picture |
| Wicked | Best Picture |
| Brady Corbet | Best Director |
| Sean Baker | Best Director |
| James Mangold | Best Director |
| Adrien Brody | Best Actor |
| Timothée Chalamet | Best Actor |

### Spec
Inline — see Objective and Detailed Requirements

### Context Loading (use your full 1M context)
Load these files completely before starting:
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md
- C:\Przemek\OPENCODE.md — your identity and rules

### Files YOU May Modify
- `oscars/index.html` (CREATE)
- `oscars/style.css` (CREATE)
- `oscars/script.js` (CREATE)
- `HANDOFF.md` (status updates only)

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)
- Any existing files outside `oscars/`

### Acceptance Criteria
- [ ] `oscars/index.html` loads in a browser and displays the movie voting UI
- [ ] Gold/black Hollywood theme with responsive mobile layout
- [ ] Vote buttons work — clicking increments count in localStorage
- [ ] One vote per category enforced (shows message on duplicate vote)
- [ ] Results section shows live tally
- [ ] No external dependencies (no CDN links, no npm)
- [ ] All 3 files exist: index.html, style.css, script.js
- [ ] Code committed to `feature/oscars-voting-page` branch

### Build & Verify (MUST complete before creating PR)

No build step needed — this is static HTML/CSS/JS. Verify by opening in browser:

```bash
# Verify files exist and are not empty
ls -la oscars/
wc -l oscars/index.html oscars/style.css oscars/script.js

# Verify no external dependencies
grep -r "cdn\|googleapis\|unpkg\|jsdelivr" oscars/ && echo "FAIL: external deps found" || echo "PASS: no external deps"
```

Expected: All 3 files exist with content, no external dependency URLs.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

**IMPORTANT: Use the @handoff-gemini agent** to manage your workflow. It will guide you through branch creation, implementation, clean commits, and PR creation.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Build the complete page | component-designer | Create index.html with semantic structure, style.css with gold/black theme and responsive layout, script.js with localStorage voting logic |

**How to use agents:** Dispatch component-designer with the full requirements above. Review its output, fix any issues, then verify.

**Agent tier unlocks:** primary + knowledge + design-specialist (component-designer UNLOCKED for this task)

---

## History

| Date | Direction | Task | PR | Result |
|------|-----------|------|-----|--------|
| 2026-02-16 | Gemini → Claude | Initial cowork setup | — | Agents synced, protocol established |
| 2026-02-17 | Claude → Gemini | Browser integration tests (API-UI parity) | PR#221 (closed, wrong repo) | Gemini created tests in fusecp-enterprise. Claude fixed runner (timeouts, verdict logic), ran suite. Initial: 4 PASS (36%). |
| 2026-02-17 | Claude | Fix all integration issues | — | Fixed HyperV connection string bug (500→200), AuditLog error handling, rewrote test suite to be Blazor-aware. Final: 11/11 PASS (100%). Report: `fusecp-enterprise/docs/reports/integration-report.md` |
| 2026-02-17 | Claude → Gemini | LoadingSpinner + shared Pagination for log pages | PR#74 | Success. Gemini: correct implementation, build passed, right repo. Claude: fixed 4 review issues (loading UX consistency, error handling, null-coalescing, missing @using). First successful improved handoff. |
| 2026-02-17 | Claude → Gemini | DNS server config + record templates | PR#75 | Success. Spec compliance 12/12 PASS, clean code quality. Claude: removed 23 junk files post-merge, updated .gitignore. DB migration + deploy verified. |
