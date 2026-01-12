# Using Recipes with the Amplifier Ecosystem

This guide explains how to use the generic recipes from the `recipes` bundle for Amplifier ecosystem-specific workflows.

## How to Run Recipes

**In a session (recommended):** Just ask naturally:
```
"run repo-activity-analysis for this repo"
"analyze ecosystem activity since yesterday"
```

**From CLI:** Use `amplifier tool invoke recipes`:
```bash
amplifier tool invoke recipes operation=execute recipe_path=<recipe> context='{"key": "value"}'
```

> **Note**: There is no `amplifier recipes` CLI command. Recipes are invoked via the `recipes` tool.

## Prerequisites

Ensure the `recipes` bundle is loaded. The recipes bundle provides the `tool-recipes` module and generic recipe examples.

## Available Generic Recipes

The recipes bundle includes these generic recipes in `recipes:examples/`:

| Recipe | Description | Default |
|--------|-------------|---------|
| `repo-activity-analysis.yaml` | Single repo analysis | Current directory, since yesterday |
| `multi-repo-activity-report.yaml` | Multi-repo synthesis | Requires repo list |

## Quick Start: Analyze Current Repo

The simplest use case - analyze the repo you're currently in:

**In a session:**
```
"analyze this repo's activity since yesterday"
"run repo-activity-analysis for the last 7 days"
```

**From CLI:**
```bash
# Analyze current repo since yesterday
amplifier tool invoke recipes operation=execute \
  recipe_path=recipes:examples/repo-activity-analysis.yaml

# Analyze with custom date range
amplifier tool invoke recipes operation=execute \
  recipe_path=recipes:examples/repo-activity-analysis.yaml \
  context='{"date_range": "last 7 days"}'
```

## Amplifier Ecosystem: Analyze Repos from MODULES.md

For comprehensive Amplifier ecosystem analysis, you'll need to:
1. Extract repo URLs from `docs/MODULES.md`
2. Pass them to the multi-repo recipe

### Step 1: Discover Repos from MODULES.md

First, extract the GitHub repos referenced in MODULES.md:

```bash
# From the amplifier repo root, extract repo URLs
grep -oE 'https://github.com/[^)>\s"]+' docs/MODULES.md | \
  sed 's/\.git$//' | \
  sort -u | \
  jq -R -s 'split("\n") | map(select(length > 0)) | 
    map(capture("https://github.com/(?<owner>[^/]+)/(?<name>[^/@#]+)")) | 
    map({owner, name, url: "https://github.com/\(.owner)/\(.name)"})' \
  > repos-manifest.json
```

Or have an agent discover them:

```
Discover all GitHub repository URLs in amplifier:docs/MODULES.md.
Extract owner and name for each, and write to repos-manifest.json as:
[{"owner": "...", "name": "...", "url": "..."}, ...]
```

### Step 2: Filter Repos (Optional)

Filter to specific orgs or repos:

```bash
# Filter to microsoft org only
jq '[.[] | select(.owner == "microsoft")]' repos-manifest.json > filtered.json

# Filter to specific repos
jq '[.[] | select(.name | test("amplifier-core|amplifier-foundation"))]' repos-manifest.json > filtered.json
```

### Step 3: Run Multi-Repo Analysis

**In a session:**
```
"run multi-repo-activity-report using repos-manifest.json since yesterday"
```

**From CLI:**
```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=recipes:examples/multi-repo-activity-report.yaml \
  context='{"repos_manifest": "./repos-manifest.json", "date_range": "since yesterday"}'
```

Or with an inline repos array:

```bash
amplifier tool invoke recipes operation=execute \
  recipe_path=recipes:examples/multi-repo-activity-report.yaml \
  context='{"repos": [{"owner": "microsoft", "name": "amplifier-core"}, {"owner": "microsoft", "name": "amplifier-foundation"}], "date_range": "last 7 days"}'
```

## Example: Full Ecosystem Activity Report

Complete workflow to generate an activity report for all Amplifier ecosystem repos:

```bash
# 1. Clone/update amplifier if needed
gh repo clone microsoft/amplifier ./amplifier 2>/dev/null || (cd amplifier && git pull)

# 2. Extract repos from MODULES.md
grep -oE 'https://github.com/microsoft/[^)>\s"]+' amplifier/docs/MODULES.md | \
  sed 's/\.git$//' | sort -u | \
  jq -R -s 'split("\n") | map(select(length > 0)) | 
    map(capture("https://github.com/(?<owner>[^/]+)/(?<name>[^/@#]+)")) | 
    map({owner, name, url: "https://github.com/\(.owner)/\(.name)"})' \
  > amplifier-repos.json

# 3. Run the multi-repo analysis
amplifier tool invoke recipes operation=execute \
  recipe_path=recipes:examples/multi-repo-activity-report.yaml \
  context='{"repos_manifest": "./amplifier-repos.json", "date_range": "since yesterday"}'

# 4. Find the report
cat ./ai_working/reports/activity-report.md
```

## Context Variables

### repo-activity-analysis.yaml

| Variable | Default | Description |
|----------|---------|-------------|
| `repo_url` | (detect from CWD) | GitHub repo URL to analyze |
| `date_range` | "since yesterday" | Natural language date range |
| `working_dir` | "./ai_working" | Working directory for output |
| `include_deep_dive` | true | Deep analysis for unclear changes |

### multi-repo-activity-report.yaml

| Variable | Default | Description |
|----------|---------|-------------|
| `repos` | [] | JSON array of {owner, name, url} objects |
| `repos_manifest` | "" | Path to JSON file with repos array |
| `date_range` | "since yesterday" | Natural language date range |
| `working_dir` | "./ai_working" | Working directory for output |
| `report_filename` | "activity-report.md" | Output report filename |

## Output

Both recipes write output to the `working_dir`:

```
ai_working/
├── analyses/
│   ├── {repo-name}-commits.json
│   ├── {repo-name}-prs.json
│   ├── {repo-name}-analysis.json
│   └── {repo-name}-summary.md
├── reports/
│   └── activity-report.md
└── repos-manifest.json (if created)
```

## Tips

1. **Date ranges**: Use natural language like "since yesterday", "last 7 days", "last week", "since 2024-12-01"

2. **gh CLI**: Ensure `gh` is installed and authenticated (`gh auth status`)

3. **Rate limits**: For many repos, you may hit GitHub API rate limits. The recipes include retry logic.

4. **Approval gates**: The multi-repo recipe has an approval gate after discovery - review the plan before committing to a long analysis.

5. **Parallel vs sequential**: The multi-repo recipe runs sequentially by default to avoid rate limits. Set `parallel: true` in the recipe for faster execution if you have higher rate limits.

## Need Help with Recipes?

For recipe authoring assistance, delegate to `recipes:recipe-author` which has direct access to:
- `recipes:docs/RECIPE_SCHEMA.md` - Complete schema reference
- `recipes:docs/BEST_PRACTICES.md` - Patterns and anti-patterns
- `recipes:docs/EXAMPLES_CATALOG.md` - Working examples
