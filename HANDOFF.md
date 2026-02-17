# Amplifier Cowork — Task Handoff

## Dispatch Status: WAITING_FOR_GEMINI

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
**Branch:** feature/oscars-2026-all-categories
**Priority:** normal
**Repository:** C:\claude\oscars
**Working Directory:** C:\claude\oscars
**PR Target:** main on psklarkins/oscars

### Objective
Update the Oscars voting page with all 24 categories from the 98th Academy Awards (2026), and add voter name identification (name input before voting, no login/auth).

### Detailed Requirements

This is an UPDATE to the existing Oscars voting page at `C:\claude\oscars`. The page is already live at https://oscars.ergonet.pl.

**Existing file structure (all 3 files exist — MODIFY, don't recreate from scratch):**
```
index.html      # Main page
style.css       # Styles
script.js       # Voting logic
```

#### Requirement 1: Voter Name Identification

Before a visitor can vote, they must enter their name. This is NOT a login — just a simple name input.

**Implementation:**
- On page load, show a modal/overlay asking "Enter your name to vote"
- Text input + "Start Voting" button
- Store the voter name in `localStorage.setItem('oscarsVoterName', name)`
- If name already exists in localStorage, skip the modal and show a greeting: "Welcome back, [Name]!"
- Display the voter's name in the header area
- Add a "Change Name" or "Not you?" link to re-enter name
- Votes should be associated with the voter name in localStorage

**Current voting data structure in script.js (line 19-20):**
```javascript
let votes = JSON.parse(localStorage.getItem('oscarsVotes')) || {};
let votedCategories = JSON.parse(localStorage.getItem('oscarsVotedCategories')) || {};
```

**New voting data structure — store voter name with votes:**
```javascript
let voterName = localStorage.getItem('oscarsVoterName') || '';
let votes = JSON.parse(localStorage.getItem('oscarsVotes')) || {};
let votedCategories = JSON.parse(localStorage.getItem('oscarsVotedCategories')) || {};
```

#### Requirement 2: Full 98th Academy Awards (2026) Nominee Data

Replace the current 10-movie hardcoded array with ALL 24 categories and ALL nominees. The current data structure is (script.js line 2-13):
```javascript
const movies = [
    { id: 'the-brutalist', title: 'The Brutalist', category: 'Best Picture' },
    // ...
];
```

**New data — use this EXACT data (all 24 categories, 120+ nominees):**

```javascript
const nominees = [
    // Best Picture (10 nominees)
    { id: 'bp-bugonia', title: 'Bugonia', category: 'Best Picture' },
    { id: 'bp-f1', title: 'F1', category: 'Best Picture' },
    { id: 'bp-frankenstein', title: 'Frankenstein', category: 'Best Picture' },
    { id: 'bp-hamnet', title: 'Hamnet', category: 'Best Picture' },
    { id: 'bp-marty-supreme', title: 'Marty Supreme', category: 'Best Picture' },
    { id: 'bp-one-battle', title: 'One Battle After Another', category: 'Best Picture' },
    { id: 'bp-secret-agent', title: 'The Secret Agent', category: 'Best Picture' },
    { id: 'bp-sentimental-value', title: 'Sentimental Value', category: 'Best Picture' },
    { id: 'bp-sinners', title: 'Sinners', category: 'Best Picture' },
    { id: 'bp-train-dreams', title: 'Train Dreams', category: 'Best Picture' },

    // Best Director (5 nominees)
    { id: 'dir-zhao', title: 'Chloé Zhao', subtitle: 'Hamnet', category: 'Best Director' },
    { id: 'dir-safdie', title: 'Josh Safdie', subtitle: 'Marty Supreme', category: 'Best Director' },
    { id: 'dir-anderson', title: 'Paul Thomas Anderson', subtitle: 'One Battle After Another', category: 'Best Director' },
    { id: 'dir-trier', title: 'Joachim Trier', subtitle: 'Sentimental Value', category: 'Best Director' },
    { id: 'dir-coogler', title: 'Ryan Coogler', subtitle: 'Sinners', category: 'Best Director' },

    // Best Actor (5 nominees)
    { id: 'act-chalamet', title: 'Timothée Chalamet', subtitle: 'Marty Supreme', category: 'Best Actor' },
    { id: 'act-dicaprio', title: 'Leonardo DiCaprio', subtitle: 'One Battle After Another', category: 'Best Actor' },
    { id: 'act-hawke', title: 'Ethan Hawke', subtitle: 'Blue Moon', category: 'Best Actor' },
    { id: 'act-jordan', title: 'Michael B. Jordan', subtitle: 'Sinners', category: 'Best Actor' },
    { id: 'act-moura', title: 'Wagner Moura', subtitle: 'The Secret Agent', category: 'Best Actor' },

    // Best Actress (5 nominees)
    { id: 'actr-buckley', title: 'Jessie Buckley', subtitle: 'Hamnet', category: 'Best Actress' },
    { id: 'actr-byrne', title: 'Rose Byrne', subtitle: 'If I Had Legs I\'d Kick You', category: 'Best Actress' },
    { id: 'actr-hudson', title: 'Kate Hudson', subtitle: 'Song Sung Blue', category: 'Best Actress' },
    { id: 'actr-reinsve', title: 'Renate Reinsve', subtitle: 'Sentimental Value', category: 'Best Actress' },
    { id: 'actr-stone', title: 'Emma Stone', subtitle: 'Bugonia', category: 'Best Actress' },

    // Best Supporting Actor (5 nominees)
    { id: 'sact-deltoro', title: 'Benicio del Toro', subtitle: 'One Battle After Another', category: 'Best Supporting Actor' },
    { id: 'sact-elordi', title: 'Jacob Elordi', subtitle: 'Frankenstein', category: 'Best Supporting Actor' },
    { id: 'sact-lindo', title: 'Delroy Lindo', subtitle: 'Sinners', category: 'Best Supporting Actor' },
    { id: 'sact-penn', title: 'Sean Penn', subtitle: 'One Battle After Another', category: 'Best Supporting Actor' },
    { id: 'sact-skarsgard', title: 'Stellan Skarsgård', subtitle: 'Sentimental Value', category: 'Best Supporting Actor' },

    // Best Supporting Actress (5 nominees)
    { id: 'sactr-fanning', title: 'Elle Fanning', subtitle: 'Sentimental Value', category: 'Best Supporting Actress' },
    { id: 'sactr-lilleaas', title: 'Inga Ibsdotter Lilleaas', subtitle: 'Sentimental Value', category: 'Best Supporting Actress' },
    { id: 'sactr-madigan', title: 'Amy Madigan', subtitle: 'Weapons', category: 'Best Supporting Actress' },
    { id: 'sactr-mosaku', title: 'Wunmi Mosaku', subtitle: 'Sinners', category: 'Best Supporting Actress' },
    { id: 'sactr-taylor', title: 'Teyana Taylor', subtitle: 'One Battle After Another', category: 'Best Supporting Actress' },

    // Best Animated Feature (5 nominees)
    { id: 'anim-arco', title: 'Arco', category: 'Best Animated Feature' },
    { id: 'anim-elio', title: 'Elio', category: 'Best Animated Feature' },
    { id: 'anim-kpop', title: 'KPop Demon Hunters', category: 'Best Animated Feature' },
    { id: 'anim-amelie', title: 'Little Amélie or the Character of Rain', category: 'Best Animated Feature' },
    { id: 'anim-zootopia', title: 'Zootopia 2', category: 'Best Animated Feature' },

    // Best Animated Short (5 nominees)
    { id: 'ashort-butterfly', title: 'Butterfly', category: 'Best Animated Short' },
    { id: 'ashort-forevergreen', title: 'Forevergreen', category: 'Best Animated Short' },
    { id: 'ashort-pearls', title: 'The Girl Who Cried Pearls', category: 'Best Animated Short' },
    { id: 'ashort-retirement', title: 'Retirement Plan', category: 'Best Animated Short' },
    { id: 'ashort-sisters', title: 'The Three Sisters', category: 'Best Animated Short' },

    // Best Cinematography (5 nominees)
    { id: 'cin-frankenstein', title: 'Frankenstein', category: 'Best Cinematography' },
    { id: 'cin-marty', title: 'Marty Supreme', category: 'Best Cinematography' },
    { id: 'cin-one-battle', title: 'One Battle After Another', category: 'Best Cinematography' },
    { id: 'cin-sinners', title: 'Sinners', category: 'Best Cinematography' },
    { id: 'cin-train', title: 'Train Dreams', category: 'Best Cinematography' },

    // Best Costume Design (5 nominees)
    { id: 'cos-avatar', title: 'Avatar: Fire and Ash', category: 'Best Costume Design' },
    { id: 'cos-frankenstein', title: 'Frankenstein', category: 'Best Costume Design' },
    { id: 'cos-hamnet', title: 'Hamnet', category: 'Best Costume Design' },
    { id: 'cos-marty', title: 'Marty Supreme', category: 'Best Costume Design' },
    { id: 'cos-sinners', title: 'Sinners', category: 'Best Costume Design' },

    // Best Documentary Feature (5 nominees)
    { id: 'doc-alabama', title: 'The Alabama Solution', category: 'Best Documentary Feature' },
    { id: 'doc-good-light', title: 'Come See Me in the Good Light', category: 'Best Documentary Feature' },
    { id: 'doc-rocks', title: 'Cutting Through Rocks', category: 'Best Documentary Feature' },
    { id: 'doc-putin', title: 'Mr. Nobody Against Putin', category: 'Best Documentary Feature' },
    { id: 'doc-neighbor', title: 'The Perfect Neighbor', category: 'Best Documentary Feature' },

    // Best Documentary Short (5 nominees)
    { id: 'dshort-rooms', title: 'All the Empty Rooms', category: 'Best Documentary Short' },
    { id: 'dshort-camera', title: 'Armed Only With a Camera', category: 'Best Documentary Short' },
    { id: 'dshort-children', title: 'Children No More', category: 'Best Documentary Short' },
    { id: 'dshort-devil', title: 'The Devil Is Busy', category: 'Best Documentary Short' },
    { id: 'dshort-strange', title: 'Perfectly a Strangeness', category: 'Best Documentary Short' },

    // Best Film Editing (5 nominees)
    { id: 'edit-f1', title: 'F1', category: 'Best Film Editing' },
    { id: 'edit-marty', title: 'Marty Supreme', category: 'Best Film Editing' },
    { id: 'edit-one-battle', title: 'One Battle After Another', category: 'Best Film Editing' },
    { id: 'edit-sentimental', title: 'Sentimental Value', category: 'Best Film Editing' },
    { id: 'edit-sinners', title: 'Sinners', category: 'Best Film Editing' },

    // Best International Feature (5 nominees)
    { id: 'intl-secret-agent', title: 'The Secret Agent (Brazil)', category: 'Best International Feature' },
    { id: 'intl-accident', title: 'It Was Just an Accident (France)', category: 'Best International Feature' },
    { id: 'intl-sentimental', title: 'Sentimental Value (Norway)', category: 'Best International Feature' },
    { id: 'intl-sirat', title: 'Sirāt (Spain)', category: 'Best International Feature' },
    { id: 'intl-hind', title: 'The Voice of Hind Rajab (Tunisia)', category: 'Best International Feature' },

    // Best Casting (NEW category for 2026!) (5 nominees)
    { id: 'cast-hamnet', title: 'Hamnet (Nina Gold)', category: 'Best Casting' },
    { id: 'cast-marty', title: 'Marty Supreme (Jennifer Venditti)', category: 'Best Casting' },
    { id: 'cast-one-battle', title: 'One Battle After Another (Cassandra Kulukundis)', category: 'Best Casting' },
    { id: 'cast-secret-agent', title: 'The Secret Agent (Gabriel Domingues)', category: 'Best Casting' },
    { id: 'cast-sinners', title: 'Sinners (Francine Maisler)', category: 'Best Casting' },

    // Best Makeup and Hairstyling (5 nominees)
    { id: 'mua-frankenstein', title: 'Frankenstein', category: 'Best Makeup and Hairstyling' },
    { id: 'mua-kokuho', title: 'Kokuho', category: 'Best Makeup and Hairstyling' },
    { id: 'mua-sinners', title: 'Sinners', category: 'Best Makeup and Hairstyling' },
    { id: 'mua-smashing', title: 'The Smashing Machine', category: 'Best Makeup and Hairstyling' },
    { id: 'mua-stepsister', title: 'The Ugly Stepsister', category: 'Best Makeup and Hairstyling' },

    // Best Original Score (5 nominees)
    { id: 'score-bugonia', title: 'Bugonia', category: 'Best Original Score' },
    { id: 'score-frankenstein', title: 'Frankenstein', category: 'Best Original Score' },
    { id: 'score-hamnet', title: 'Hamnet', category: 'Best Original Score' },
    { id: 'score-one-battle', title: 'One Battle After Another', category: 'Best Original Score' },
    { id: 'score-sinners', title: 'Sinners', category: 'Best Original Score' },

    // Best Original Song (5 nominees)
    { id: 'song-dear-me', title: '"Dear Me"', subtitle: 'Diane Warren: Relentless', category: 'Best Original Song' },
    { id: 'song-golden', title: '"Golden"', subtitle: 'KPop Demon Hunters', category: 'Best Original Song' },
    { id: 'song-i-lied', title: '"I Lied to You"', subtitle: 'Sinners', category: 'Best Original Song' },
    { id: 'song-sweet-dreams', title: '"Sweet Dreams of Joy"', subtitle: 'Viva Verdi!', category: 'Best Original Song' },
    { id: 'song-train-dreams', title: '"Train Dreams"', subtitle: 'Train Dreams', category: 'Best Original Song' },

    // Best Production Design (5 nominees)
    { id: 'prod-frankenstein', title: 'Frankenstein', category: 'Best Production Design' },
    { id: 'prod-hamnet', title: 'Hamnet', category: 'Best Production Design' },
    { id: 'prod-marty', title: 'Marty Supreme', category: 'Best Production Design' },
    { id: 'prod-one-battle', title: 'One Battle After Another', category: 'Best Production Design' },
    { id: 'prod-sinners', title: 'Sinners', category: 'Best Production Design' },

    // Best Live Action Short (5 nominees)
    { id: 'lshort-butcher', title: "Butcher's Stain", category: 'Best Live Action Short' },
    { id: 'lshort-dorothy', title: 'A Friend of Dorothy', category: 'Best Live Action Short' },
    { id: 'lshort-austen', title: "Jane Austen's Period Drama", category: 'Best Live Action Short' },
    { id: 'lshort-singers', title: 'The Singers', category: 'Best Live Action Short' },
    { id: 'lshort-saliva', title: 'Two People Exchanging Saliva', category: 'Best Live Action Short' },

    // Best Sound (5 nominees)
    { id: 'snd-f1', title: 'F1', category: 'Best Sound' },
    { id: 'snd-frankenstein', title: 'Frankenstein', category: 'Best Sound' },
    { id: 'snd-one-battle', title: 'One Battle After Another', category: 'Best Sound' },
    { id: 'snd-sinners', title: 'Sinners', category: 'Best Sound' },
    { id: 'snd-sirat', title: 'Sirāt', category: 'Best Sound' },

    // Best Visual Effects (5 nominees)
    { id: 'vfx-avatar', title: 'Avatar: Fire and Ash', category: 'Best Visual Effects' },
    { id: 'vfx-f1', title: 'F1', category: 'Best Visual Effects' },
    { id: 'vfx-jurassic', title: 'Jurassic World Rebirth', category: 'Best Visual Effects' },
    { id: 'vfx-lost-bus', title: 'The Lost Bus', category: 'Best Visual Effects' },
    { id: 'vfx-sinners', title: 'Sinners', category: 'Best Visual Effects' },

    // Best Adapted Screenplay (5 nominees)
    { id: 'asc-bugonia', title: 'Bugonia', category: 'Best Adapted Screenplay' },
    { id: 'asc-frankenstein', title: 'Frankenstein', category: 'Best Adapted Screenplay' },
    { id: 'asc-hamnet', title: 'Hamnet', category: 'Best Adapted Screenplay' },
    { id: 'asc-one-battle', title: 'One Battle After Another', category: 'Best Adapted Screenplay' },
    { id: 'asc-train', title: 'Train Dreams', category: 'Best Adapted Screenplay' },

    // Best Original Screenplay (5 nominees)
    { id: 'osc-blue-moon', title: 'Blue Moon', category: 'Best Original Screenplay' },
    { id: 'osc-accident', title: 'It Was Just an Accident', category: 'Best Original Screenplay' },
    { id: 'osc-marty', title: 'Marty Supreme', category: 'Best Original Screenplay' },
    { id: 'osc-sentimental', title: 'Sentimental Value', category: 'Best Original Screenplay' },
    { id: 'osc-sinners', title: 'Sinners', category: 'Best Original Screenplay' },
];
```

#### Requirement 3: Category Navigation

With 24 categories, the page needs navigation. Add:
- A sidebar or top tab bar listing all 24 category names
- Clicking a category scrolls to / filters to that category
- Highlight the active/selected category
- Consider grouping: "Main Awards" (Picture, Director, Acting), "Technical" (Cinematography, Editing, etc.), "Other" (Shorts, Docs, International)
- Mobile: collapsible category menu

#### Requirement 4: Updated Results Section

The results section should:
- Group results by category
- Show voter name next to their vote (if available)
- Sort nominees within each category by vote count (descending)

### Spec
Inline — see Objective and Detailed Requirements

### Context Loading (use your full 1M context)
Load these files completely before starting:
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md
- C:\Przemek\OPENCODE.md — your identity and rules
- The existing `index.html`, `style.css`, `script.js` in the repo root (understand current patterns)

### Files YOU May Modify
- `index.html` (MODIFY — update structure for categories + voter name)
- `style.css` (MODIFY — add category nav, voter modal, expanded layout)
- `script.js` (MODIFY — replace movie data, add voter name logic, category nav)
- `HANDOFF.md` (status updates only — this file is in C:\claude\amplifier, NOT in the oscars repo)

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)

### Acceptance Criteria
- [ ] All 24 Oscar categories displayed with correct nominees (120+ total)
- [ ] Voter name modal appears on first visit — must enter name before voting
- [ ] Returning visitors see "Welcome back, [Name]!" greeting
- [ ] "Change name" option available to re-enter voter name
- [ ] Category navigation works — can browse/filter all 24 categories
- [ ] One vote per category per visitor still enforced
- [ ] Votes stored in localStorage with voter name association
- [ ] Results section groups by category with vote counts
- [ ] Gold/black Hollywood theme maintained, mobile responsive
- [ ] No external dependencies (no CDN links, no npm)
- [ ] All 3 files exist: index.html, style.css, script.js
- [ ] Code committed to `feature/oscars-2026-all-categories` branch

### Build & Verify (MUST complete before creating PR)

No build step needed — this is static HTML/CSS/JS. Verify:

```bash
# Verify files exist and are not empty
ls -la index.html style.css script.js
wc -l index.html style.css script.js

# Verify no external dependencies
grep -r "cdn\|googleapis\|unpkg\|jsdelivr" . --include="*.html" --include="*.js" --include="*.css" && echo "FAIL: external deps found" || echo "PASS: no external deps"

# Verify all 24 categories are present in the data
grep -c "category:" script.js
```

Expected: All 3 files with content, no external deps, 120+ category entries in script.js.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

**IMPORTANT: Use the @handoff-gemini agent** to manage your workflow. It will guide you through branch creation, implementation, clean commits, and PR creation.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Update all 3 files with new data, voter name, and category nav | component-designer | Modify index.html (add voter modal, category nav), style.css (modal styles, nav styles, category groups), script.js (replace data array with 120+ nominees, add voter name logic, category filtering) |

**How to use agents:** Dispatch component-designer with the full requirements and the EXACT nominee data from above. Review its output, fix any issues, then verify.

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
