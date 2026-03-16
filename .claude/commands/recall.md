---
description: "Load context from long-term memory. Temporal, topic (BM25), or graph queries."
---

# Recall — Long-Term Memory

Three modes: temporal (date-based session timeline), topic (BM25 search across indexed sessions and memory files), and graph (interactive visualization of session-file relationships). Every recall ends with the **One Thing** — a concrete, highest-leverage next action synthesized from results.

## Arguments

$ARGUMENTS

## Platform Note

`AMPLIFIER_HOME` must resolve to the Amplifier repo root. Detection order:
1. Environment variable `$AMPLIFIER_HOME` if set
2. `/opt/amplifier` (Linux)
3. `/c/claude/amplifier` (Windows/Git Bash)

If not set, detect before running commands:
```bash
AMPLIFIER_HOME="${AMPLIFIER_HOME:-$([ -d /opt/amplifier ] && echo /opt/amplifier || echo /c/claude/amplifier)}"
```

## Step 1: Classify Query

Parse the input and classify:

- **Graph** — starts with "graph": "graph last week", "graph yesterday"
  → Go to Step 2C
- **Temporal** — mentions time: "yesterday", "today", "last week", "this week", a date, "what was I doing", "session history"
  → Go to Step 2A
- **Topic** — mentions a subject: "authentication", "FuseCP exchange", "Hyper-V cluster"
  → Go to Step 2B
- **Both** — temporal + topic: "what did I do with exchange yesterday"
  → Go to Step 2A first, then scan results for the topic

## Step 2A: Temporal Recall (JSONL Timeline)

Run the recall-day script:

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall_day.py list DATE_EXPR
```

Replace `DATE_EXPR` with the parsed date expression. Supported:
- `yesterday`, `today`
- `YYYY-MM-DD`
- `last monday` .. `last sunday`
- `this week`, `last week`
- `N days ago`, `last N days`

Options:
- `--min-msgs N` - filter noise (default: 3)
- `--all-projects` - scan all projects, not just current

Present the table to the user. If they pick a session to expand:

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall_day.py expand SESSION_ID
```

## Step 2B: Topic Recall (BM25 with Query Expansion)

BM25 is keyword-based — it only finds exact word matches. The user's recall of a topic often uses different words. Fix: expand the query into 3-4 keyword variants.

**Step 2B.1: Expand query into variants.** Generate 3-4 alternative phrasings covering synonyms and related terms. Example:
- User says "disk cleanup" → variants: `"disk cleanup free space"`, `"large files storage"`, `"delete cache bloat GB"`, `"free up computer space"`

**Step 2B.2: Run ALL variants in parallel** (fast, ~0.1s each):

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall-search.py "VARIANT_1" -n 5
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall-search.py "VARIANT_2" -n 5
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall-search.py "VARIANT_3" -n 5
```

Run these in parallel via multiple Bash tool calls.

**Step 2B.3: Deduplicate results** by session ID. If same session appears in multiple searches, keep the highest score. Present top 5 unique results.

## Step 3: Fetch Full Documents (Topic path only)

For the top 3 most relevant session results, read the extracted markdown file to get full context:

```bash
head -60 FILEPATH
```

Use the `filepath` field from the search results.

## Step 4: Present Structured Summary

**For temporal queries:** Present the session table and offer to expand any session.

**For topic queries:** Organize results by collection type:

**Sessions** — What was worked on related to this topic, key decisions, current status
**Memory** — Related memory entries, patterns, notes

Keep concise — this is context loading, not a full report.

## Step 5: Synthesize "One Thing"

After presenting results, synthesize the single highest-leverage next action.

**How to pick the One Thing:**
1. Look at what has momentum — sessions with recent activity, things mid-flow
2. Look at what's blocked — removing a blocker unlocks downstream work
3. Look at what's closest to done — finishing > starting
4. Consider dependencies — what unlocks the most other work

Present as:

```
**One Thing:** [specific, actionable next step — not generic]
```

## Step 2C: Graph Visualization

Strip "graph" prefix from query to get the date expression. Run:

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/session-graph.py DATE_EXPR --no-open -o "$AMPLIFIER_HOME/tmp/session-graph.html"
```

Options:
- `--min-files N` - only show sessions touching N+ files (default: 2, use 5+ for cleaner graphs)
- `--min-msgs N` - filter noise (default: 3)
- `--all-projects` - scan all projects

After generating, read the graph output stats and tell the user the node/edge counts and where the file is saved.

## Notes

- Temporal queries go through `recall_day.py` (native JSONL, no index needed)
- Graph queries go through `session-graph.py` (NetworkX + pyvis)
- Topic queries use BM25 (`recall-search.py`) via SQLite FTS5
- Run all search variants in parallel to keep response time fast
- FTS5 index lives at `~/.claude/recall-index.sqlite`
- If index is stale, run: `uv run python scripts/recall/extract-sessions.py --days 30`
