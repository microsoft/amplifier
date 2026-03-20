# Stage 3: CLAUDE_PLUGIN_DATA Migration — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate guard freeze state and review command temp files to `${CLAUDE_PLUGIN_DATA}` for cross-session persistence and clean state isolation.

**Architecture:** Replace `/tmp/` mktemp calls with `${CLAUDE_PLUGIN_DATA}/reviews/` directory. Add persistent freeze state file. Add shared review history log (JSONL) across all 3 review engines. Add `--history` flag to `/second-opinion`.

**Tech Stack:** Bash (in command .md files), JSONL (history log)

**Scope Mode:** HOLD SCOPE

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `commands/guard.md` | Modify | Add freeze state persistence + session recovery |
| `commands/second-opinion.md` | Modify | Replace mktemp, add history logging, add --history |
| `commands/codex-review.md` | Modify | Add history logging after review |
| `commands/gemini-review.md` | Modify | Replace mktemp, add history logging |

No new files created. 4 existing files modified.

---

## State Directory Layout

```
${CLAUDE_PLUGIN_DATA}/
├── guard-freeze-dir.txt          # Persisted freeze boundary (one line: absolute path)
├── reviews/
│   └── history.jsonl             # Shared review log across all engines
├── failures.jsonl                # (Stage 4, already exists)
├── rate-limit-flag.json          # (Stage 4, already exists)
└── telemetry/                    # (Reserved for future use)
```

---

### Task 1 [TRACER]: Update guard.md with persistent freeze state

**Agent:** modular-builder
**Review:** L1 (simple, low-risk — command markdown edits)

TRIVIAL EXEMPTION: markdown instruction edits in a single command file

**Files:**
- Modify: `commands/guard.md` — "Setting the freeze boundary" section (~line 58-63) and "Deactivation" section (~line 73)

- [ ] **Step 1:** Read `commands/guard.md` in full

- [ ] **Step 2:** In the "Setting the freeze boundary" section (after "resolve to absolute path and remember it for the session"), add:

```markdown
**Persisting freeze state:**

After resolving the freeze directory path, persist it for cross-session recovery:

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA"
echo "$FREEZE_DIR" > "$PLUGIN_DATA/guard-freeze-dir.txt"
```

**Session recovery:** When `/guard` or `/guard freeze` is invoked, check for a previous freeze boundary FIRST:

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
if [ -f "$PLUGIN_DATA/guard-freeze-dir.txt" ]; then
  PREV_FREEZE=$(cat "$PLUGIN_DATA/guard-freeze-dir.txt")
  echo "Previous freeze boundary found: $PREV_FREEZE"
fi
```

If a previous boundary exists, ask the user:
- A) Restore previous boundary (`$PREV_FREEZE`)
- B) Set a new boundary
- C) Clear the old boundary and proceed without freeze
```

- [ ] **Step 3:** In the "Deactivation" section, after the confirmation flow, add:

```markdown
After deactivation, clean up the persistent state:

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
rm -f "$PLUGIN_DATA/guard-freeze-dir.txt"
```
```

- [ ] **Step 4:** Deploy: `cp commands/guard.md ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/guard.md`

- [ ] **Step 5:** Commit

```bash
git add commands/guard.md
git commit -m "feat: persist guard freeze state to CLAUDE_PLUGIN_DATA

Freeze boundary now survives session restarts. On /guard invocation,
checks for previous boundary and offers to restore it."
```

---

### Task 2: Update second-opinion.md — replace mktemp + add history

**Agent:** modular-builder
**Review:** L1

TRIVIAL EXEMPTION: command markdown edits, pattern replacement

**Files:**
- Modify: `commands/second-opinion.md` — lines 45, 56, 110 (mktemp calls)

- [ ] **Step 1:** Read `commands/second-opinion.md`

- [ ] **Step 2:** Replace ALL 3 mktemp lines. Each occurrence of:
```bash
DIFF_FILE=$(mktemp /tmp/second-opinion-diff-XXXXXX.txt)
```
Replace with:
```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA/reviews"
DIFF_FILE="$PLUGIN_DATA/reviews/$(date +%Y%m%d-%H%M%S)-sonnet-diff.txt"
```

- [ ] **Step 3:** After the "Present:" block in Step 3A (review mode, ~line 95), add history logging:

```markdown
5. **Log to review history:**

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA/reviews"
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"engine\":\"sonnet\",\"mode\":\"review\",\"branch\":\"$(git rev-parse --abbrev-ref HEAD 2>/dev/null)\",\"verdict\":\"PASS_OR_FAIL\",\"findings\":{\"p1\":N,\"p2\":N,\"p3\":N},\"pr_number\":null}" >> "$PLUGIN_DATA/reviews/history.jsonl"
```

Replace PASS_OR_FAIL and N values with actual results from the review output.
```

- [ ] **Step 4:** Add `--history` mode. In the Arguments table, add a row:

```
| `/second-opinion --history` | history | Show review history across all engines |
```

After the Arguments section, add:

```markdown
## History Mode

If the user runs `/second-opinion --history`:

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
HISTORY="$PLUGIN_DATA/reviews/history.jsonl"
if [ -f "$HISTORY" ]; then
  echo "Review History (all engines):"
  cat "$HISTORY"
else
  echo "No review history found."
fi
```

Present the history as a formatted table:
| Date | Engine | Mode | Branch | Verdict | P1 | P2 | P3 |
```

- [ ] **Step 5:** Deploy + commit

```bash
cp commands/second-opinion.md ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/second-opinion.md
git add commands/second-opinion.md
git commit -m "feat: migrate /second-opinion to CLAUDE_PLUGIN_DATA with review history"
```

---

### Task 3: Update gemini-review.md — replace mktemp + add history

**Agent:** modular-builder
**Review:** L1

TRIVIAL EXEMPTION: same pattern as Task 2, different file

**Files:**
- Modify: `commands/gemini-review.md` — lines 66, 81 (mktemp calls)

- [ ] **Step 1:** Read `commands/gemini-review.md`

- [ ] **Step 2:** Replace both mktemp lines:
```bash
DIFF_FILE=$(mktemp /tmp/gemini-review-diff-XXXXXX.txt)
```
With:
```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA/reviews"
DIFF_FILE="$PLUGIN_DATA/reviews/$(date +%Y%m%d-%H%M%S)-gemini-diff.txt"
```

- [ ] **Step 3:** After the "Present Results" section (Step 4, ~line 132), add history logging:

```markdown
After presenting results, log to shared review history:

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA/reviews"
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"engine\":\"gemini\",\"mode\":\"review\",\"branch\":\"$(git rev-parse --abbrev-ref HEAD 2>/dev/null)\",\"verdict\":\"PASS_OR_FAIL\",\"findings\":{\"p1\":N,\"p2\":N,\"p3\":N},\"pr_number\":${PR_NUMBER:-null}}" >> "$PLUGIN_DATA/reviews/history.jsonl"
```
```

- [ ] **Step 4:** Deploy + commit

```bash
cp commands/gemini-review.md ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/gemini-review.md
git add commands/gemini-review.md
git commit -m "feat: migrate /gemini-review to CLAUDE_PLUGIN_DATA with review history"
```

---

### Task 4: Update codex-review.md — add history logging

**Agent:** modular-builder
**Review:** L1

TRIVIAL EXEMPTION: add 1 block to command file (codex-review has no mktemp — Codex CLI handles diffs internally)

**Files:**
- Modify: `commands/codex-review.md` — after Step 4 "Present Results" (~line 131)

- [ ] **Step 1:** Read `commands/codex-review.md`

- [ ] **Step 2:** After the gate verdict block (~line 129), add:

```markdown
After presenting results, log to shared review history:

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA/reviews"
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"engine\":\"codex\",\"mode\":\"review\",\"branch\":\"$(git rev-parse --abbrev-ref HEAD 2>/dev/null)\",\"verdict\":\"PASS_OR_FAIL\",\"findings\":{\"p1\":N,\"p2\":N,\"p3\":N},\"pr_number\":${PR_NUMBER:-null}}" >> "$PLUGIN_DATA/reviews/history.jsonl"
```
```

- [ ] **Step 3:** Deploy + commit

```bash
cp commands/codex-review.md ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/codex-review.md
git add commands/codex-review.md
git commit -m "feat: add review history logging to /codex-review"
```

---

## Verification Checklist

- [ ] `commands/guard.md` references `${CLAUDE_PLUGIN_DATA}` for freeze state
- [ ] `commands/guard.md` has session recovery (check for previous freeze)
- [ ] `commands/guard.md` cleans up state on `/guard off`
- [ ] `commands/second-opinion.md` has no `/tmp/` mktemp calls
- [ ] `commands/second-opinion.md` logs to `reviews/history.jsonl`
- [ ] `commands/second-opinion.md` has `--history` mode
- [ ] `commands/gemini-review.md` has no `/tmp/` mktemp calls
- [ ] `commands/gemini-review.md` logs to `reviews/history.jsonl`
- [ ] `commands/codex-review.md` logs to `reviews/history.jsonl`
- [ ] All 4 commands deployed to plugin marketplace

## Task Count

| Task | Files | Checkboxes |
|------|-------|------------|
| Task 1 [TRACER]: guard.md freeze persistence | 1 | 5 |
| Task 2: second-opinion.md mktemp + history | 1 | 5 |
| Task 3: gemini-review.md mktemp + history | 1 | 4 |
| Task 4: codex-review.md history | 1 | 3 |
| **Total** | **4** | **17** |
