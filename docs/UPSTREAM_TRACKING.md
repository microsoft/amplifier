# Upstream Tracking & Cherry-Pick Strategy

This document tracks our fork's relationship with upstream repositories and guides cherry-pick decisions.

## Repositories

### Microsoft Amplifier (main upstream)

| | |
|---|---|
| **Upstream** | `https://github.com/microsoft/amplifier.git` (remote: `upstream`) |
| **Our fork** | `https://gitea.ergonet.pl:3001/admin/amplifier.git` (remote: `origin`) |
| **GitHub mirror** | `https://github.com/psklarkins/amplifier.git` (remote: `github`) |
| **Last sync** | 2026-03-02 — adopted PyPI amplifier-core, reviewed all upstream commits |

### Superpowers Chrome (MCP plugin)

| | |
|---|---|
| **Upstream** | `https://github.com/obra/superpowers-chrome` |
| **Installed via** | Claude Code plugin system (`superpowers-chrome@superpowers-marketplace`) |
| **Our version** | v1.6.3 (installed 2026-01-29) |
| **Latest upstream** | v1.8.0 (2026-02-25) |

---

## Our Divergence from Upstream Amplifier

### What we keep that upstream deleted

Upstream cleaned their `.claude/` directory — all 36 agents and 33 commands were removed from the main repo. They now distribute agents/commands via the **bundle system** (separate repos like `amplifier-bundle-superpowers`).

We maintain our own `.claude/agents/` and `.claude/commands/` with heavy customizations:
- 30+ custom agents tuned to our workflows (FuseCP, VMware, cowork, design)
- 11+ custom commands (`/fix-bugs`, `/test-webapp-ui`, `/brainstorm`, `/tdd`, etc.)
- Custom `AGENTS.md`, `CLAUDE.md`, `COWORK.md` with our development philosophy

**Decision**: Keep our `.claude/` as-is. Our customizations are extensive and specific to our environment. We don't use the upstream bundle system for agent distribution.

### What we adopted

| Date | Change | Details |
|------|--------|---------|
| 2026-03-02 | amplifier-core from PyPI | Removed git source, now `amplifier-core==1.0.0` from PyPI. Faster installs. |

### What we skipped (with rationale)

| Change | Rationale |
|--------|-----------|
| Delete `.claude/agents/` and `.claude/commands/` | We have 30+ custom agents and 11+ commands. Upstream moved to bundles; we don't use bundles. |
| `model_role` in agent frontmatter | Requires routing-matrix bundle. Interesting but not needed yet — we manage model selection in agent prompts. |
| `amplifier-app-cli` branch change | Upstream merged rust-core into main. Our `[tool.uv.sources]` already points to `main`. |

---

## Upstream Features to Watch

These are upstream innovations worth monitoring for future adoption.

### routing-matrix bundle
- **What**: Declarative model routing — agents declare semantic roles (`general`, `code`, `reasoning`), matrices resolve to the right model
- **Why watch**: Could replace our manual model selection in agent definitions
- **Adopt when**: We have >3 model providers or need automated cost optimization
- **Repo**: `microsoft/amplifier-bundle-routing-matrix`

### execution-environments bundle
- **What**: Create/target/destroy Docker, SSH, local environments on demand
- **Why watch**: Could improve our testing isolation (currently use git worktrees)
- **Adopt when**: We need Docker-based test environments or multi-server deployment testing
- **Repo**: `microsoft/amplifier-bundle-execution-environments`

### superpowers bundle (upstream version)
- **What**: TDD-driven dev workflows with brainstorm, plan, execute, verify, finish
- **Why watch**: Similar to our custom commands but packaged as a bundle
- **Adopt when**: If upstream version surpasses our customizations in capability
- **Repo**: `microsoft/amplifier-bundle-superpowers`

### skills bundle
- **What**: Skills tool and Microsoft-curated skills collection
- **Why watch**: Complementary to our commands
- **Repo**: `microsoft/amplifier-bundle-skills`

### provider-github-copilot
- **What**: GitHub Copilot as an LLM provider for Amplifier
- **Why watch**: Could add Copilot as a fallback/alternative model
- **Repo**: Community contribution

---

## Superpowers Chrome: Version Gap

### v1.6.3 (our version) -> v1.8.0 (latest)

Features we're missing:

| Version | Feature | Testing Value |
|---------|---------|---------------|
| v1.8.0 | **Viewport emulation** (`set_viewport` action) | Test responsive designs at specific device sizes |
| v1.8.0 | **Full-page screenshots** | Capture entire scrollable pages for visual regression |
| v1.8.0 | **HiDPI fix** | Correct screenshot resolution on high-DPI displays |
| v1.8.0 | **`pid`/`info` actions** | Debug Chrome process state during test failures |
| v1.8.0 | **Dynamic CDP port allocation** | Per-profile meta.json, better multi-session support |
| v1.8.0 | **`clear_cookies` action** | Reset state between test runs |
| v1.6.4 | **Auto-downscale screenshots** | Prevent oversized screenshot files |

### Update procedure

```bash
# In Claude Code, run:
/plugin update superpowers-chrome@superpowers-marketplace
# Or reinstall:
/plugin install superpowers-chrome@superpowers-marketplace
```

---

## Ultra Recall Memory System (External Sources)

### QMD — On-Device Search Engine
- **Upstream**: `tobi/qmd` (GitHub)
- **What**: BM25 + vector search + LLM reranker via GGUF models, SQLite + sqlite-vec + FTS5
- **Our adoption**: Evaluated but not used — requires native node-gyp compilation (Visual Studio Build Tools) which this server lacks. Instead, we use Python-native SQLite FTS5 for BM25 search, achieving the same keyword ranking without external dependencies.

### Recall Scripts — Session Extraction & Search
- **Upstream**: `ArtemXTech/personal-os-skills/skills/recall/` (GitHub)
- **What**: Three-mode recall system — temporal (JSONL scan), topic (QMD BM25), graph (NetworkX + pyvis)
- **Our adaptation**:
  - De-Obsidian'd: Removed all Obsidian vault assumptions, uses our own `~/.claude/recall-sessions/` directory
  - Windows paths: All Path objects, no hardcoded Unix paths
  - Python runtime: `uv run python` instead of bare `python3`
  - Search backend: SQLite FTS5 (Python-native) instead of QMD CLI
  - Session format: Adapted for Claude Code JSONL (type: "user" not "human", message.content structure)
  - Filtering: Strips system tags, command messages; filters warmup/agent sessions
  - Integration: `/recall` Amplifier command + SessionEnd auto-indexing hook

### Files
| Script | Origin | Changes |
|--------|--------|---------|
| `scripts/recall/extract-sessions.py` | ArtemXTech extract-sessions.py | FTS5 indexing, Windows paths, JSONL format adaptation |
| `scripts/recall/recall-day.py` | ArtemXTech recall-day.py | Agent session filtering, UTF-8 output, Windows paths |
| `scripts/recall/recall-search.py` | New (replaces QMD CLI) | Python-native FTS5 BM25 search |
| `scripts/recall/session-graph.py` | ArtemXTech session-graph.py | Imports from recall_day module, Windows paths |
| `.claude/commands/recall.md` | New | Three-mode /recall command with One Thing synthesis |
| `.claude/hooks/session-end-index.sh` | New | Auto-index on session end |

---

## Cherry-Pick Process

When checking upstream for new changes:

1. **Fetch**: `git fetch upstream`
2. **Compare**: `git log main..upstream/main --oneline --no-merges`
3. **Evaluate** each commit against:
   - Does it improve our workflows?
   - Does it conflict with our customizations?
   - Is it a docs-only change to MODULES.md? (usually skip)
4. **Cherry-pick** selectively: `git cherry-pick <sha>`
5. **Update this doc** with what was adopted/skipped and why

### Frequency

Check upstream monthly or before starting major new development work.
