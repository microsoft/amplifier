---
description: "Search and browse project documentation across all repos. BM25 keyword search with project/category filters. Use instead of manual file searches."
---

# Docs — Cross-Project Documentation Search

Search and browse indexed documentation across all projects. Uses FTS5 BM25 ranking for keyword relevance. The doc index covers 11 projects with ~950 markdown files categorized by type (spec, plan, api, agent, config, guide, etc.).

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

- **Search** — a topic or keyword: "exchange deployment", "cluster awareness", "authentication"
  → Go to Step 2A
- **List** — starts with "list": "list amplifier", "list fusecp-enterprise --category spec"
  → Go to Step 2B
- **Recent** — starts with "recent": "recent 7", "recent 30"
  → Go to Step 2C
- **Stats** — "stats" or "index stats"
  → Go to Step 2D

## Step 2A: Search (BM25 with Query Expansion)

BM25 is keyword-based — expand the query into 2-3 keyword variants to improve recall.

**Step 2A.1: Expand query into variants.** Generate 2-3 alternative phrasings covering synonyms and related terms. Example:
- User says "mailbox setup" → variants: `"mailbox setup configuration"`, `"exchange mailbox provider"`, `"email create plan"`

**Step 2A.2: Run ALL variants in parallel** (fast, ~0.1s each):

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/docs-search.py "VARIANT_1" -n 8
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/docs-search.py "VARIANT_2" -n 8
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/docs-search.py "VARIANT_3" -n 8
```

Run these in parallel via multiple Bash tool calls.

Optional filters (append if user specifies):
- `--project PROJECT` — limit to one project (e.g., `fusecp-enterprise`)
- `--category CATEGORY` — limit to category (e.g., `spec`, `plan`, `api`, `agent`)

**Step 2A.3: Deduplicate results** by path. If same doc appears in multiple searches, keep the highest score. Present top 8 unique results.

## Step 2B: List Docs

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/docs-search.py --list PROJECT
```

Replace `PROJECT` with the project name. Add `--category CATEGORY` if specified.

If no project given, list all:
```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/docs-search.py --list
```

## Step 2C: Recent Docs

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/docs-search.py --recent N
```

Replace `N` with number of days. Add `--project PROJECT` if specified.

## Step 2D: Stats

```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/docs-search.py --stats
```

## Step 3: Read Top Results

For search results (Step 2A), automatically read the top 1-3 most relevant documents to provide immediate context:

# Use the path from search results — prepend the project root.
# Use the Read tool instead of cat for reading docs.
#
# Project roots vary by platform. Detect the parent directory:
#   Linux: /opt/ (most projects), /opt/monorepo-workspace/ (siem monorepo)
#   Windows: C:/claude/ (all projects)
#
# Common mappings:
#   amplifier         → Linux: /opt/amplifier/                                    | Windows: C:/claude/amplifier/
#   universal-siem-monorepo → Linux: /opt/monorepo-workspace/universal-siem-monorepo/ | Windows: C:/claude/universal-siem-monorepo/
#   universal-siem-docs     → Linux: /opt/universal-siem-docs/                        | Windows: C:/claude/universal-siem-docs/
#   universal-siem-linux-agent → Linux: /opt/universal-siem-linux-agent/              | Windows: C:/claude/universal-siem-linux-agent/
#   genetics-platform       → Linux: /opt/genetics-platform/                          | Windows: C:/claude/genetics-platform/
#   webtmux                 → Linux: /opt/webtmux/                                    | Windows: C:/claude/webtmux/
#
# For other projects, check /opt/<project>/ (Linux) or C:/claude/<project>/ (Windows).

## Step 4: Present Results

**For search:** Show results table with project, category, title, and snippet. After reading top docs, summarize key findings relevant to the query.

**For list/recent/stats:** Show the output directly.

## Notes

- FTS5 index lives at `~/.claude/docs-index.sqlite`
- Doc registry (cold-start context) at `~/.claude/docs-registry.md`
- If index is stale, run: `uv run python scripts/recall/extract-docs.py --recent 7`
- Full re-index: `uv run python scripts/recall/extract-docs.py --full`
- Regenerate registry: `uv run python scripts/recall/generate-doc-registry.py`
