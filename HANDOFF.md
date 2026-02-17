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
**Branch:** feature/movie-poster-images
**Priority:** normal
**Repository:** C:\claude\oscars
**Working Directory:** C:\claude\oscars
**PR Target:** main on psklarkins/oscars

### Objective
Find movie poster images from the internet for all Oscar 2026 nominated films and display them on nominee cards.

### Detailed Requirements

This is an UPDATE to the existing Oscars voting page at `C:\claude\oscars`. The page is live at https://oscars.ergonet.pl.

**Current architecture:** Node.js server (server.js) + static HTML/CSS/JS. Vote data in JSON file via API. Two pages: index.html (ballot) and voters.html (voter listing).

#### Requirement 1: Find Poster Images for All Unique Movies

Search the internet for movie poster images for each unique film title below. Use **TMDB image CDN URLs** (format: `https://image.tmdb.org/t/p/w300/<hash>.jpg`) where possible — these are publicly accessible and don't require API keys for display. Alternatively, use any other reliable, publicly accessible image URL.

**Unique feature film titles to search for (these appear across multiple categories):**

| # | Movie Title | Notes |
|---|------------|-------|
| 1 | Sinners | Ryan Coogler film, appears in ~10 categories |
| 2 | One Battle After Another | Paul Thomas Anderson film |
| 3 | Frankenstein | Guillermo del Toro film |
| 4 | Hamnet | Chloé Zhao film |
| 5 | Marty Supreme | Josh Safdie film, Timothée Chalamet |
| 6 | Sentimental Value | Joachim Trier film |
| 7 | Bugonia | Yorgos Lanthimos film, Emma Stone |
| 8 | F1 | Brad Pitt racing film |
| 9 | Train Dreams | Denis Villeneuve film |
| 10 | The Secret Agent | Brazilian film, Wagner Moura |
| 11 | Avatar: Fire and Ash | James Cameron sequel |
| 12 | Blue Moon | Richard Linklater film, Ethan Hawke |
| 13 | If I Had Legs I'd Kick You | Rose Byrne |
| 14 | Song Sung Blue | Kate Hudson |
| 15 | Weapons | Amy Madigan |
| 16 | It Was Just an Accident | French film |
| 17 | Sirāt | Spanish film |
| 18 | The Voice of Hind Rajab | Tunisian film |
| 19 | Kokuho | Makeup category |
| 20 | The Smashing Machine | Makeup category |
| 21 | The Ugly Stepsister | Animated/makeup |
| 22 | Jurassic World Rebirth | Spielberg sequel |
| 23 | The Lost Bus | VFX category |
| 24 | Diane Warren: Relentless | Documentary about Diane Warren |
| 25 | Viva Verdi! | Song category film |

**Animated features:**

| # | Movie Title |
|---|------------|
| 26 | Arco |
| 27 | Elio | Pixar film |
| 28 | KPop Demon Hunters |
| 29 | Little Amélie or the Character of Rain |
| 30 | Zootopia 2 | Disney sequel |

**Documentary features:**

| # | Movie Title |
|---|------------|
| 31 | The Alabama Solution |
| 32 | Come See Me in the Good Light |
| 33 | Cutting Through Rocks |
| 34 | Mr. Nobody Against Putin |
| 35 | The Perfect Neighbor |

**Shorts (animated, documentary, live action) — lower priority, find what you can:**

| # | Movie Title | Type |
|---|------------|------|
| 36 | Butterfly | Animated short |
| 37 | Forevergreen | Animated short |
| 38 | The Girl Who Cried Pearls | Animated short |
| 39 | Retirement Plan | Animated short |
| 40 | The Three Sisters | Animated short |
| 41 | All the Empty Rooms | Doc short |
| 42 | Armed Only With a Camera | Doc short |
| 43 | Children No More | Doc short |
| 44 | The Devil Is Busy | Doc short |
| 45 | Perfectly a Strangeness | Doc short |
| 46 | Butcher's Stain | Live action short |
| 47 | A Friend of Dorothy | Live action short |
| 48 | Jane Austen's Period Drama | Live action short |
| 49 | The Singers | Live action short |
| 50 | Two People Exchanging Saliva | Live action short |

**How to search:** Use your web search capabilities to find poster image URLs. Search for `"<movie title>" 2025 2026 movie poster` or check TMDB, IMDb, or Wikipedia. For major releases (Sinners, Avatar, F1, Zootopia 2, etc.) posters should be easy to find. For obscure shorts, skip if no poster is available.

**Store results in a `posters` object** inside `script.js` that maps movie titles to image URLs:

```javascript
// Add after the nominees array, before the categories extraction
const posters = {
    'Sinners': 'https://image.tmdb.org/t/p/w300/xxxxx.jpg',
    'F1': 'https://image.tmdb.org/t/p/w300/yyyyy.jpg',
    'Avatar: Fire and Ash': 'https://image.tmdb.org/t/p/w300/zzzzz.jpg',
    // ... all found posters
    // Movies with no poster found are simply omitted from this object
};
```

**Key:** The poster key is the movie TITLE string (not the nominee ID), because many nominees share the same movie. For nominees that are people (directors, actors), use their `subtitle` field to look up the movie poster.

#### Requirement 2: Update Nominee Card Rendering in `script.js`

Modify the `renderNominees()` function to show poster images on cards.

**Current card HTML (script.js:285-291):**
```javascript
card.innerHTML = `
    <div>
        <h3 class="nominee-title">${nominee.title}</h3>
        <p class="nominee-subtitle">${nominee.subtitle || '&nbsp;'}</p>
    </div>
    <button class="vote-button" data-id="${nominee.id}" data-category="${category}">Vote</button>
`;
```

**New card HTML:**
```javascript
// Look up poster: use subtitle (movie name) for person nominees, title for movie nominees
const movieTitle = nominee.subtitle || nominee.title;
const posterUrl = posters[movieTitle];
const posterHtml = posterUrl
    ? `<img class="nominee-poster" src="${posterUrl}" alt="${movieTitle}" loading="lazy">`
    : `<div class="nominee-poster-placeholder"></div>`;

card.innerHTML = `
    ${posterHtml}
    <div>
        <h3 class="nominee-title">${nominee.title}</h3>
        <p class="nominee-subtitle">${nominee.subtitle || '&nbsp;'}</p>
    </div>
    <button class="vote-button" data-id="${nominee.id}" data-category="${category}">Vote</button>
`;
```

#### Requirement 3: Update CSS for Poster Display

Add to `style.css`:

```css
.nominee-poster {
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 3px 3px 0 0;
    margin-bottom: 0.5rem;
}

.nominee-poster-placeholder {
    width: 100%;
    height: 180px;
    background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
    border-radius: 3px 3px 0 0;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Adjust card padding for poster */
.nominee-card {
    padding: 0;
    overflow: hidden;
}

.nominee-card > div,
.nominee-card > button {
    padding: 0 1rem;
}

.nominee-card > button {
    margin: 0.5rem 1rem 1rem;
}
```

**Responsive:** On mobile (max-width: 480px), reduce poster height to 120px.

#### Requirement 4: Duplicate Posters in `voters.html`

The voters page also has a nominees array (inline in `<script>`). Add the same `posters` object there so voter cards can optionally show the movie poster for each vote pick. This is OPTIONAL — if it adds too much complexity, skip it for voters.html.

### Spec
Inline — see Objective and Detailed Requirements

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `C:\claude\oscars\script.js` — current voting logic (446 lines), especially nominees array (lines 3-176) and renderNominees (lines 266-298)
- `C:\claude\oscars\style.css` — current styles (506 lines), especially .nominee-card (lines 119-130)
- `C:\claude\oscars\index.html` — page structure (54 lines)
- `C:\claude\oscars\voters.html` — voters page (312 lines)
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- `script.js` (MODIFY — add posters object, update renderNominees)
- `style.css` (MODIFY — add poster styles, adjust card padding)
- `voters.html` (MODIFY — optionally add posters to voter picks)

### Files YOU Must Create
- None — all changes are to existing files

### Files You Must NOT Modify
- `server.js` (no server changes needed)
- `index.html` (no HTML changes needed)
- `.claude/*` (always)
- `CLAUDE.md` (always)
- `C:\FuseCP\*` (always)
- `C:\Przemek\OPENCODE.md` (always)

### Acceptance Criteria
- [ ] Poster images display on nominee cards for movies where posters were found
- [ ] Cards without posters show a graceful placeholder (dark gradient, not broken image)
- [ ] Poster lookup uses movie title (not nominee ID) — shared movies show same poster across categories
- [ ] For person nominees (directors, actors), poster is looked up via the subtitle (movie name)
- [ ] `loading="lazy"` attribute on poster images for performance
- [ ] Poster height is consistent (180px desktop, 120px mobile)
- [ ] Cards still look clean — poster above title, title above vote button
- [ ] At least 15 major films have working poster images (Sinners, Avatar, F1, Zootopia 2, etc.)
- [ ] No broken image icons — missing posters use placeholder, not 404 images
- [ ] Gold/black theme maintained — posters don't clash with existing design
- [ ] Code committed to `feature/movie-poster-images` branch with clear messages

### Build & Verify (MUST complete before creating PR)

```bash
# Start the server
node server.js &
# Wait for server
sleep 2

# Test that pages load
curl -s http://localhost:3000/ | head -5
curl -s http://localhost:3000/voters.html | head -5

# Verify posters object exists in script.js
grep -c "posters\[" script.js || grep -c "const posters" script.js

# Verify poster rendering in script.js
grep "nominee-poster" script.js

# Verify poster CSS
grep "nominee-poster" style.css

# Count how many poster URLs were found
grep -c "http" script.js | head -1

# Verify no broken syntax
node -c script.js && echo "PASS: No syntax errors" || echo "FAIL: Syntax error"

# Cleanup
kill %1 2>/dev/null
```

Expected: Pages load, poster images appear on cards, no syntax errors.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

**IMPORTANT: Use the @handoff-gemini agent** to manage your workflow.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Search web for poster images for all 50 movie titles | agentic-search | Use web search to find TMDB/IMDb poster URLs for each movie title. Return a JSON mapping of title→URL |
| Add posters object + update renderNominees in script.js | modular-builder | Add the posters data, update card rendering to show images |
| Add poster CSS styles | component-designer | Poster image styles, placeholder, responsive adjustments |

**How to use agents:** Dispatch agentic-search first to find all poster URLs (this is the bulk of the work). Then modular-builder to integrate the URLs into script.js. Then component-designer for CSS.

**Agent tier unlocks:** primary + knowledge + design-specialist (component-designer UNLOCKED)

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
