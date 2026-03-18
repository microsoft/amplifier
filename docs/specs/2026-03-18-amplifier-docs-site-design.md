# Amplifier Documentation Site — Design Spec

## Problem

Amplifier has 12+ HTML visual docs scattered in `~/.agent/diagrams/` with inconsistent styling, no navigation between them, no auto-updates, and no machine-readable layer. Documentation gets stale between sessions.

## Goal

Build a self-updating documentation website at `https://amplifier.ergonet.pl` that:
- Regenerates only changed pages after each PR merge (page-level granularity)
- Serves bilingual content (EN-first, AI-translated PL via sonnet)
- Provides LLM-consumable data (llms.txt, llms-full.txt, llms-structured.json)
- Uses a unified deep blue + gold design system with sidebar navigation
- Becomes the canonical external documentation reference for Claude Code

## Site Sections (7 + subsections)

| Section | Path | Sources |
|---------|------|---------|
| Home | `/en/index.html` | CLAUDE.md, AGENTS.md, routing-matrix.yaml |
| User Manual | `/en/manual.html` | CLAUDE.md, AGENTS.md, docs/guides/*.md, ai_context/claude_code/*.md |
| Commands | `/en/commands.html` | .claude/commands/**/*.md, routing-matrix.yaml |
| Agents | `/en/agents.html` | .claude/agents/**/*.md, routing-matrix.yaml |
| Deep Dives (4) | `/en/deep-dives/*.html` | Various command/skill files per topic |
| Platform (3) | `/en/platform/*.html` | config/platform.json, platform configs, linux-setup.md |
| Projects (4+) | `/en/projects/*.html` | Per-project memory files, project-specific docs |
| Roadmap | `/en/roadmap.html` | docs/specs/*.md, docs/plans/*.md |
| Sessions | `/en/sessions/*.html` | Git log, PR diffs, commit messages |

Polish mirrors at `/pl/` for all pages.

## File Layout

```
C:\claude\amplifier-docs\
├── en/                          # English pages
│   ├── index.html
│   ├── manual.html
│   ├── commands.html
│   ├── agents.html
│   ├── deep-dives/
│   │   ├── self-improvement.html
│   │   ├── effort-steering.html
│   │   ├── autocontext.html
│   │   └── workflows.html
│   ├── platform/
│   │   ├── index.html
│   │   ├── linux.html
│   │   └── windows.html
│   ├── projects/
│   │   ├── index.html
│   │   ├── fusecp.html
│   │   ├── genetics.html
│   │   ├── siem.html
│   │   └── amplifier.html
│   ├── roadmap.html
│   └── sessions/
│       ├── index.html
│       ├── archive/
├── pl/                          # Polish mirrors
├── assets/
│   └── nav.html
├── prompts/                     # Generation prompts per page
│   ├── _design-system.md
│   ├── home.md
│   ├── manual.md
│   ├── commands.md
│   ├── agents.md
│   └── ...
├── manifest.json
├── generate.ps1                 # Main orchestrator
├── webhook-listener.ps1         # HTTP listener for Gitea webhooks
├── llms.txt
├── llms-full.txt
└── llms-structured.json
```

## Design System

- Fonts: Bricolage Grotesque (body) + Fragment Mono (code)
- Dark-first: --bg: #0b1120, --surface: #111827, --gold: #d4a73a, --teal: #0891b2, --coral: #e07050
- Light mode via prefers-color-scheme media query
- Sidebar navigation (260px fixed, hamburger on mobile)
- Language switcher (EN/PL) swaps /en/ ↔ /pl/ in URL path

## Infrastructure

- IIS site: Amplifier_Docs, app pool: Amplifier_Docs (No Managed Code)
- Physical path: C:\claude\amplifier-docs\
- Binding: https://amplifier.ergonet.pl:443 with *.ergonet.pl wildcard cert
- DNS: amplifier.ergonet.pl → 172.31.251.100 (on FINALTEST DC, 172.31.251.101)
- Default document: en/index.html

## Regeneration Pipeline

### Trigger
Gitea webhook on admin/amplifier repo, fires on PR merge (action=closed + merged=true).
Webhook hits http://localhost:9099/amplifier-docs-rebuild.

### Webhook Listener
PowerShell HTTP listener (webhook-listener.ps1) running as Windows Service.
Validates HMAC signature, spawns generate.ps1 as background job.

### Generate.ps1 Logic
1. Pull latest main from amplifier repo
2. Read manifest.json, expand glob patterns, SHA256 hash source files
3. Compare to stored hashes — build list of changed pages
4. For each changed page: dispatch `claude --headless` with prompt from prompts/<page>.md
5. For each generated EN page: dispatch `claude --headless` with translation prompt → PL version
6. Regenerate llms.txt, llms-full.txt, llms-structured.json from generated content
7. Update manifest.json with new hashes
8. Log to logs/

### Force Regenerate
`generate.ps1 -Force` skips hash comparison, regenerates all pages.

## LLM Documentation Layer

### llms.txt (navigation index)
Standard format: one entry per page with URL, title, description.

### llms-full.txt (full context)
Concatenated plain-text extraction of all EN pages. For full-context handoff.

### llms-structured.json (queryable data)
Machine-optimized JSON with every command, agent, workflow, platform config structured as queryable objects.

### Per-page metadata
Each HTML page embeds: `<script type="application/llm+json">` with page purpose, key concepts, source files, related pages, last updated.

### CLAUDE.md Integration
Add docs site to Memory and Documentation Tools table pointing to llms.txt, llms-full.txt, llms-structured.json via WebFetch.

## Translation Strategy

English-first generation. Separate sonnet dispatch for Polish translation.
Translation preserves: HTML structure, CSS, code blocks, command names, file paths, agent names.
Translates: all visible text content using proper Polish technical terminology.

## Session Recaps

Rolling 30-day window on sessions/index.html. Older recaps move to sessions/archive/.
Generated from merged PR: git log, diff stats, commit messages, key decisions.

## Manifest Dependency Rules

- global_triggers: assets/nav.html, prompts/_design-system.md — changes to these regenerate ALL pages
- PL pages inherit EN sources — if EN regenerates, PL does too
- MEMORY: prefix in sources reads from user memory directory
- Glob patterns expanded at build time

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Infrastructure | modular-builder | DNS, IIS site, app pool, cert binding |
| Webhook system | modular-builder | PS HTTP listener, Gitea webhook, generate.ps1 |
| Manifest system | modular-builder | manifest.json, hash logic, glob expansion |
| Design system | modular-builder | _design-system.md tokens, sidebar nav |
| Page prompts | modular-builder | 15+ generation prompts |
| Initial generation | modular-builder | First full EN build |
| Translation | modular-builder | Translation prompt + PL build |
| LLM layer | modular-builder | llms.txt, llms-full.txt, llms-structured.json |
| CLAUDE.md update | modular-builder | Add docs site to tools table |
| Verification | test-coverage | All pages load, links work, LLM files parse |
| Security | security-guardian | HMAC validation, no sensitive data |

## Execution Waves

- Wave 1: Infrastructure (DNS + IIS + webhook listener) — parallel
- Wave 2: Design system + manifest + generate.ps1 orchestrator
- Wave 3: Page prompts (parallel batches)
- Wave 4: Initial full generation (EN then PL)
- Wave 5: LLM layer + CLAUDE.md update
- Wave 6: Verification + security review

## Test Plan

- [ ] DNS resolves amplifier.ergonet.pl to 172.31.251.100
- [ ] IIS site responds on https://amplifier.ergonet.pl
- [ ] All EN pages load without errors
- [ ] All PL pages load without errors
- [ ] Sidebar navigation works across all pages
- [ ] Language switcher toggles EN/PL correctly
- [ ] llms.txt accessible and well-formed
- [ ] llms-full.txt contains all page content
- [ ] llms-structured.json parses as valid JSON
- [ ] Gitea webhook fires on PR merge
- [ ] Webhook listener receives and validates request
- [ ] generate.ps1 regenerates only changed pages
- [ ] generate.ps1 -Force regenerates all pages
- [ ] No sensitive data (API keys, passwords) in generated pages
