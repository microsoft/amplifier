# Amplifier Cowork — Task Handoff

## Dispatch Status: PR_READY

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
**Branch:** feature/voter-database-and-page
**Priority:** normal
**Repository:** C:\claude\oscars
**Working Directory:** C:\claude\oscars
**PR Target:** main on psklarkins/oscars
**PR Link:** https://github.com/psklarkins/oscars/pull/2

### Objective
Add a JSON-file voter database with a Node.js API server, and create a voters listing page with navigation menu between the ballot and voters pages.


### Detailed Requirements

This is an UPDATE to the existing Oscars voting page at `C:\claude\oscars`. The page is live at https://oscars.ergonet.pl.

**Current architecture:** Pure static HTML/CSS/JS using localStorage for vote storage. 3 files: `index.html`, `style.css`, `script.js`.

**New architecture:** Node.js HTTP server serving static files + JSON API. Votes persisted to a JSON file on disk instead of localStorage.

#### Requirement 1: Node.js API Server (`server.js`)

Create a server using ONLY built-in Node.js modules (`http`, `fs`, `path`). NO npm dependencies. NO package.json needed.

```javascript
// server.js structure:
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const DATA_FILE = path.join(__dirname, 'data', 'votes.json');
```

**API endpoints:**

| Method | Path | Request Body | Response | Purpose |
|--------|------|-------------|----------|---------|
| GET | `/api/votes` | — | `{ votes: {...} }` | Return all votes from votes.json |
| POST | `/api/vote` | `{ voter, nomineeId, category }` | `{ success: true, voteKey }` | Save/update a vote |
| GET | `/api/voters` | — | `{ voters: [{name, voteCount, categories: [...]}] }` | Unique voter list with stats |

**Static file serving:** For any non-API request, serve static files from the working directory. Map file extensions to correct MIME types (html→text/html, css→text/css, js→application/javascript, json→application/json). Return 404 for missing files.

**Vote storage format in `data/votes.json`:**
```json
{
  "Alice-Best Picture": {
    "voter": "Alice",
    "nomineeId": "bp-sinners",
    "category": "Best Picture",
    "timestamp": "2026-02-17T15:30:00.000Z"
  },
  "Bob-Best Director": {
    "voter": "Bob",
    "nomineeId": "dir-coogler",
    "category": "Best Director",
    "timestamp": "2026-02-17T15:31:00.000Z"
  }
}
```

**Vote key format:** `${voter}-${category}` (same as current localStorage key format). This enforces one vote per category per voter — a new vote in the same category overwrites the previous one.

**Server must:**
- Create `data/` directory if it doesn't exist on startup
- Create `data/votes.json` with `{}` if it doesn't exist on startup
- Use file locking or atomic writes (write to temp file then rename) to prevent data corruption
- Return proper CORS headers (Access-Control-Allow-Origin: *) for development
- Log requests to console: `[timestamp] METHOD /path`

#### Requirement 2: Voters Page (`voters.html`)

Create a new page showing all voters and their voting activity. Must match the existing gold/black theme.

**Page structure:**
```html
<!-- Same header as index.html but with navigation -->
<header id="app-header">
    <h1>Oscars 2026 — Voters</h1>
    <nav id="page-nav">
        <a href="index.html">Ballot</a>
        <a href="voters.html" class="active">Voters</a>
    </nav>
</header>

<main id="voters-container">
    <!-- Voter cards rendered by JavaScript -->
</main>
```

**Voter card layout (for each voter):**
```
┌─────────────────────────────┐
│  Voter Name                 │
│  Votes: 12/24 categories    │
│                             │
│  Best Picture: Sinners      │
│  Best Director: Coogler     │
│  Best Actor: Chalamet       │
│  ... (all their votes)      │
└─────────────────────────────┘
```

**The voters page JS (`voters.js` or inline in voters.html):**
- On load, fetch `GET /api/voters` and `GET /api/votes`
- Build the nominee lookup from the same `nominees` array (copy from script.js or import)
- For each voter: show their name, vote count, and list of their picks (nominee title per category)
- Sort voters by number of votes (most active first)
- Auto-refresh every 30 seconds to show new votes

#### Requirement 3: Navigation Menu

Add a simple page navigation to BOTH pages (index.html and voters.html):

**In the header of both pages:**
```html
<nav id="page-nav">
    <a href="index.html">Ballot</a>
    <a href="voters.html">Voters</a>
</nav>
```

**Style the nav (add to style.css):**
- Inline links in the header, right side
- Gold (#D4AF37) color for links, underline on active page
- Responsive: stack vertically on mobile

#### Requirement 4: Update Frontend (`script.js`)

Replace localStorage vote storage with API calls:

**Current pattern (localStorage):**
```javascript
// Loading votes
const loadVotes = () => {
    try {
        votes = JSON.parse(localStorage.getItem('oscarsVotes2026')) || {};
    } catch (e) { votes = {}; }
};
// Saving votes
const saveVotes = () => {
    try {
        localStorage.setItem('oscarsVotes2026', JSON.stringify(votes));
    } catch (e) { }
};
```

**New pattern (fetch API):**
```javascript
// Loading votes from server
const loadVotes = async () => {
    try {
        const res = await fetch('/api/votes');
        const data = await res.json();
        votes = data.votes || {};
    } catch (e) {
        console.error('Failed to load votes:', e);
        votes = {};
    }
};

// Saving a single vote to server
const saveVote = async (voter, nomineeId, category) => {
    try {
        await fetch('/api/vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ voter, nomineeId, category })
        });
    } catch (e) {
        console.error('Failed to save vote:', e);
    }
};
```

**Keep voter name in localStorage** — the name modal and localStorage for `oscarsVoterName` stays as-is. Only vote data moves to the server.

**Update the vote click handler** to call `saveVote()` instead of `saveVotes()`.

**Make `init()` async** since `loadVotes()` now returns a promise.

#### Requirement 5: Data Directory

Create `data/` directory with:
- `data/votes.json` — initialized as `{}` (empty object)
- `data/.gitkeep` — so git tracks the empty directory
- Add `data/votes.json` to `.gitignore` (don't commit actual vote data, only the empty template)

### Spec
Inline — see Objective and Detailed Requirements

### Context Loading (use your full 1M context)
Load these files completely before starting:
- `C:\claude\oscars\index.html` — current HTML structure (50 lines)
- `C:\claude\oscars\style.css` — current styles (377 lines)
- `C:\claude\oscars\script.js` — current voting logic (445 lines), especially the nominees array and vote model
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- `index.html` (MODIFY — add page navigation)
- `style.css` (MODIFY — add nav styles, voter page styles)
- `script.js` (MODIFY — replace localStorage with fetch API calls)

### Files YOU Must Create
- `server.js` (CREATE — Node.js HTTP server)
- `voters.html` (CREATE — voters listing page)
- `data/votes.json` (CREATE — empty JSON object `{}`)
- `data/.gitkeep` (CREATE — keep data dir in git)
- `.gitignore` (CREATE — ignore data/votes.json)

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)

### Acceptance Criteria
- [ ] `server.js` starts with `node server.js` and serves static files + API on port 3000
- [ ] No npm dependencies — uses only built-in Node.js modules (http, fs, path)
- [ ] `GET /api/votes` returns all votes from data/votes.json
- [ ] `POST /api/vote` saves a vote to data/votes.json with voter name, nomineeId, category, timestamp
- [ ] `GET /api/voters` returns unique voter list with vote counts
- [ ] `voters.html` page displays all voters with their vote details, matching gold/black theme
- [ ] Navigation menu on both pages links between Ballot and Voters
- [ ] `script.js` uses fetch() API calls instead of localStorage for vote storage
- [ ] Voter name identification still uses localStorage (name modal unchanged)
- [ ] Vote key format `${voter}-${category}` enforces one vote per category per voter
- [ ] `data/votes.json` created with empty `{}`, tracked in .gitignore
- [ ] Code committed to `feature/voter-database-and-page` branch with clear messages

### Build & Verify (MUST complete before creating PR)

```bash
# Start the server
node server.js &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Test static file serving
curl -s http://localhost:3000/ | head -5
curl -s http://localhost:3000/voters.html | head -5

# Test API - save a vote
curl -s -X POST http://localhost:3000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"voter":"TestUser","nomineeId":"bp-sinners","category":"Best Picture"}'

# Test API - get all votes
curl -s http://localhost:3000/api/votes | python3 -m json.tool 2>/dev/null || curl -s http://localhost:3000/api/votes

# Test API - get voters
curl -s http://localhost:3000/api/voters

# Verify vote was persisted to file
cat data/votes.json

# Verify no npm dependencies
test ! -f package.json && echo "PASS: no package.json" || echo "FAIL: package.json exists"
test ! -d node_modules && echo "PASS: no node_modules" || echo "FAIL: node_modules exists"

# Cleanup
kill $SERVER_PID 2>/dev/null
```

Expected: Server starts, serves HTML, API endpoints work, vote persisted to JSON file.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

**IMPORTANT: Use the @handoff-gemini agent** to manage your workflow.

| Task | Agent | What to delegate |
|------|-------|-----------------|
| Create server.js with static serving + API endpoints | modular-builder | Build the Node.js HTTP server with GET/POST endpoints and file I/O |
| Create voters.html + update styles | component-designer | Build voters page with voter cards, add navigation to both pages, style everything in gold/black theme |
| Update script.js to use fetch API | modular-builder | Replace localStorage vote calls with fetch(), make init async |

**How to use agents:** Dispatch modular-builder first for server.js (it's the foundation), then component-designer for voters.html + navigation, then modular-builder again for script.js frontend changes.

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
