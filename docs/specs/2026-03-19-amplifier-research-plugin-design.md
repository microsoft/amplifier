# amplifier-research Plugin Design Spec

**Date:** 2026-03-19
**Status:** Approved
**Project:** C:\claude\amplifier\

## Problem

Amplifier has no structured web research workflow. When needing competitive intelligence, market research, or technology assessment, users manually invoke WebSearch and hope for the best. There is no validated process, no accuracy tracking, no systematic extraction, and no persistent storage of research findings. Each research session starts from scratch, with no accumulated methodology or cross-session recall of results.

## Goal

Create `amplifier-research` — a new plugin in the amplifier-marketplace that provides a `/research` command with 12 pre-built research process files (9 company-focused, 3 technology-focused) and a methodology skill for building new processes. The plugin brings structured, repeatable web research to Amplifier without any new infrastructure.

## Architecture

- **Location:** `amplifier-marketplace/amplifier-research/` (separate plugin, same pattern as `amplifier-fusecp`, `amplifier-siem`)
- **Default state:** Disabled in `enabledPlugins` — user enables via settings or `/reload-plugins`
- **Dependencies:** Zero new MCP servers — uses existing WebSearch and WebFetch for all search execution
- **Persistence:** Research output written to `.data/research/` and indexed into `recall-index.sqlite` via Stop hook for cross-session access

## Plugin Directory Structure

```
amplifier-marketplace/amplifier-research/
├── commands/
│   └── research.md                        # /research command definition
├── skills/
│   └── research-build/
│       └── SKILL.md                       # methodology for building new process files
└── processes/
    ├── find-profiles.md                   # 6 steps — company fact sheets
    ├── find-competitors.md                # 7 steps — competitor analysis
    ├── find-reviews.md                    # 6 steps — customer reviews
    ├── find-news.md                       # 7 steps — news and events
    ├── find-pr-releases.md                # 5 steps — press releases
    ├── find-hiring.md                     # 5 steps — hiring signals
    ├── find-job-role-insights.md          # 5 steps — job description analysis
    ├── find-growth-signals.md             # 7 steps — growth indicators
    ├── find-negativity.md                 # 6 steps — complaints and churn signals
    ├── find-tech-alternatives.md          # 5 steps — library/tool alternatives
    ├── find-tech-assessment.md            # 6 steps — technology maturity assessment
    └── find-tech-stack.md                 # 5 steps — technology detection
```

## Command: `/research`

The `/research` command operates in two modes:

### Mode 1: Execute Research
```
/research <query>
```
- Auto-selects the best matching process file for the query using `content-researcher`
- Executes the search patterns defined in the selected process file
- Synthesizes findings via `analysis-engine`
- Writes structured output to `.data/research/{date}-{slug}.md`
- Indexes result into `recall-index.sqlite` via existing Stop hook

**Examples:**
```
/research find competitors for SolidCP
/research what is the tech stack for Guacamole
/research customer complaints about cPanel
```

### Mode 2: Build New Process
```
/research build <goal>
```
- Uses `SKILL.md` methodology to create a new process file through iterative testing
- Tests candidate search patterns against real queries
- Produces a new `.md` file in `processes/` with validated steps, extraction specs, and output template

## Process File Format

Every process file follows the same structure. All 12 files conform to this schema:

```markdown
# Process: {process-name}
**Category:** company | technology
**Steps:** N
**Input:** {{input}} — description of what the user provides

## Purpose
One sentence describing what this process finds.

## Search Patterns
Step-by-step queries, each with:
- Exact search string (using {{input}} placeholder)
- What to extract from results
- When to skip (kill list pattern)
- Stop condition (signal that enough data is gathered)

## Step 1: {step-name}
**Query:** `site:linkedin.com "{{input}}" overview`
**Extract:** Founded year, employee count, headquarters, description
**Skip if:** No LinkedIn result on first page
**Stop when:** All four fields populated

... (repeat for each step)

## Kill List
Patterns that waste searches — skip immediately if encountered:
- Results older than 2 years (for news/hiring)
- Forum posts with no cited sources (for fact sheets)
- SEO-spam domains: g2crowd aggregators without review text

## Output Template
Structured markdown the synthesis agent fills in:

# {process-name}: {{input}}
**Date:** YYYY-MM-DD  **Sources checked:** N

## [Section headers specific to this process]
[fields]

## Sources
[ranked list with URLs and quality scores]

## Confidence
Overall: N% | Sources checked: N | Unique domains: N
```

### Key fields required in every process file
- `{{input}}` placeholder used consistently across all search strings
- Explicit stop conditions — prevents over-searching
- Kill list — prevents time-wasting on low-quality sources
- Output template — ensures consistent structure for recall indexing

## Agent Allocation

| Phase | Agent | Model | Responsibility |
|-------|-------|-------|---------------|
| Process selection | `content-researcher` | sonnet | Match query to best process file; explain selection |
| Search execution | `content-researcher` | sonnet | Run WebSearch + WebFetch following process steps |
| Synthesis | `analysis-engine` | sonnet | Score sources, deduplicate findings, compute confidence |
| Storage | `content-researcher` | sonnet | Write `.data/research/{date}-{slug}.md`, trigger recall index |

Process selection and storage are lightweight steps; both run in the same `content-researcher` dispatch to avoid subagent overhead for short operations.

## Output File Format

Written to: `.data/research/YYYY-MM-DD-{input-slug}-{process-slug}.md`

```markdown
# Research: {topic}
**Date:** YYYY-MM-DD
**Process:** {process-name}
**Sources checked:** N
**Confidence:** N%

## Findings
[structured output per the process file's output template]

## Sources
[ranked by quality score, with URLs and brief justification]

## Confidence Breakdown
Overall: N%
Sources checked: N
Unique domains: N
Patterns used: N / {total-patterns-in-process}
Stop condition met: yes | no (exhausted patterns)
```

## Recall Integration

Research output is indexed into `recall-index.sqlite` automatically via the existing Stop hook (`session-end-index.sh`). The hook already scans `.data/` for new markdown files. No changes to the hook are required.

After indexing, results are retrievable in any future session:
```
/recall SolidCP competitors
/recall find-profiles Guacamole
```

## Design Decisions

1. **Separate plugin, disabled by default.** Zero overhead when not researching. Users who never do web research are not affected. Follows the same opt-in pattern as `amplifier-fusecp` and `amplifier-siem`.

2. **No new MCP servers.** WebSearch and WebFetch are sufficient for structured research. Adding a dedicated search MCP server would add infrastructure cost and maintenance burden with no quality gain over systematic process files.

3. **9 company processes imported from research-process-builder (MIT licensed).** The `find-profiles`, `find-competitors`, `find-reviews`, `find-news`, `find-pr-releases`, `find-hiring`, `find-job-role-insights`, `find-growth-signals`, and `find-negativity` processes are battle-tested patterns from the research-process-builder project. License permits inclusion.

4. **3 new technology processes built from scratch.** `find-tech-alternatives`, `find-tech-assessment`, and `find-tech-stack` cover technology research needs not addressed by the imported company processes. Built using the same methodology defined in `SKILL.md`.

5. **Research output indexed into recall for cross-session access.** The Stop hook already handles `.data/` markdown files. No hook modification needed — the output format just needs consistent frontmatter for the indexer to extract metadata.

6. **Plugin follows the same marketplace pattern.** Directory layout, `plugin.json` manifest, command registration, and skill registration all follow the `amplifier-fusecp` reference implementation. No new plugin infrastructure is needed.

7. **Auto-selection over explicit process naming.** Users write `/research find competitors for SolidCP`, not `/research --process find-competitors SolidCP`. The `content-researcher` agent reads process file purposes and selects the best match. This lowers friction and matches natural language use.

## Process Files: Source Notes

### Imported (9 files — MIT licensed from research-process-builder)
- `find-profiles.md` — company fact sheets with LinkedIn, Crunchbase, official site
- `find-competitors.md` — G2, Capterra, analyst reports, community threads
- `find-reviews.md` — G2, Trustpilot, Reddit, App Store
- `find-news.md` — Google News, PR Newswire, TechCrunch, domain-specific press
- `find-pr-releases.md` — official newsrooms, BusinessWire, PRWeb
- `find-hiring.md` — LinkedIn Jobs, Indeed, Glassdoor, Levels.fyi
- `find-job-role-insights.md` — JD analysis for skill signals and org structure
- `find-growth-signals.md` — funding, headcount growth, product launches, partnerships
- `find-negativity.md` — churn signals, support complaints, Reddit/HN criticism

### New (3 files — built with SKILL.md methodology)
- `find-tech-alternatives.md` — finds library and tool alternatives: `site:reddit.com "alternatives to {{input}}"`, GitHub Topics, npm/PyPI comparison pages, "X vs Y" articles
- `find-tech-assessment.md` — maturity assessment: GitHub stars/commits/issues age, OSSF scorecard, CVE history, last release date, company backing signals
- `find-tech-stack.md` — technology detection: BuiltWith, Wappalyzer, Stackshare, job postings for tech keywords, GitHub org repos

## Test Plan

1. **Structural validation.** Verify all 12 process files contain `{{input}}` placeholder in every search string, explicit stop conditions, kill list section, and output template section. Can be validated with a grep pass before merge.

2. **Command smoke test.** Run `/research find competitors for SolidCP` end-to-end:
   - Confirm `content-researcher` selects `find-competitors.md`
   - Confirm WebSearch calls follow the process steps
   - Confirm output file created at `.data/research/YYYY-MM-DD-solidcp-find-competitors.md`
   - Confirm file contains all template sections

3. **Build mode test.** Run `/research build "find open source forks of a GitHub project"`:
   - Confirm `SKILL.md` methodology is followed
   - Confirm a new `.md` file is produced in `processes/`
   - Confirm the file passes structural validation

4. **Recall integration test.** After step 2, run `/recall SolidCP competitors` in a new session:
   - Confirm the research output appears in recall results

5. **Plugin isolation test.** With `amplifier-research` disabled in `enabledPlugins`, confirm `/research` is not available and no `.data/research/` writes occur.

## Impact

- **New:** `amplifier-marketplace/amplifier-research/` plugin (12 process files, 1 command, 1 skill)
- **No changes** to any existing plugin
- **No changes** to existing MCP servers or hook scripts
- **No new dependencies** — WebSearch and WebFetch already available
- **No schema changes** to `recall-index.sqlite`
