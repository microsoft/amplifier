# Amplifier: Your AI Development Amplified

## 🚀 QuickStart 

### Prerequisites

```bash
python3 --version  # Need 3.11+
uv --version       # Need any version
node --version     # Need any version
pnpm --version     # Need any version
git --version      # Need any version
claude --version   # For now. To be removed in the future.
```

Missing something? [→ Quick Install Guide](#quick-install-guide)


### Setup

```bash
git clone https://github.com/microsoft/amplifier.git
cd amplifier
make configure
make install
make check
make test
source .venv/bin/activate # Linux/Mac/WSL 
# source .venv\Scripts\Activate.ps1 # Windows PowerShell 
```

### Use Amplifier via Claude Code

**Option 1** - 
Work on a new (or existing) project
```bash
mkdir ../quickstart-demo
ln -s ../../quickstart-demo ai_working/quickstart-demo
claude
```

> *Claude Code:*
> ```
> I'm working in ai_working/quickstart-demo, and using the capabilities from 
> amplifier.
>```

**Option 2** - Work on the Amplifier project itself
```bash
claude
```

---

## 🎯 How is Amplifier Different from Claude Code?

Claude Code is powerful on its own—but Amplifier transforms it from a coding assistant into a coordinated and accelerated development system. Amplifier offers a pre-built suite of advanced capabilities for immediate use.

### Persistent Memory & Learning

Every session with vanilla Claude Code starts from zero. Amplifier builds institutional knowledge that compounds over time.

| Vanilla Claude Code               | Amplifier                                                         |
|-----------------------------------|-------------------------------------------------------------------|
| ❌ Fresh start every session       | ✅ Auto-loaded memory files |
| ❌ Repeatedly explain your project | ✅ Context persists across sessions                                |
| ❌ Repeat past mistakes            | ✅ System learns & prevents recurrence                             |

### Specialized Agent Intelligence
One generalist trying to do everything versus an expert team working in parallel. Amplifier orchestrates 25+ specialized agents, each with focused expertise.

| Vanilla Claude Code                       | Amplifier                                       |
|-------------------------------------------|-------------------------------------------------|
| ❌ One generalist AI for everything        | ✅ 25+ specialized agents with focused expertise |
| ❌ Serial processing (one thing at a time) | ✅ Parallel execution across multiple agents     |
| ❌ Single context window gets confused     | ✅ Separate context per agent stays focused      |

### Executable Methodologies
Manual multi-step prompting vs. one-command workflows. Amplifier transforms complex methodologies into executable slash commands.

| Vanilla Claude Code                | Amplifier                                        |
|------------------------------------|--------------------------------------------------|
| ❌ Manual workflow orchestration    | ✅ Custom slash commands execute entire processes |
| ❌ Repeated prompting for each step | ✅ One command = complete workflow                |
| ❌ Lose place if interrupted        | ✅ TodoWrite tracking + state preservation        |

### Knowledge Synthesis Pipeline
Conversation-limited context vs. unlimited knowledge processing. Amplifier extracts, connects, and makes searchable insights from your entire content library.

| Vanilla Claude Code               | Amplifier                                         |
|-----------------------------------|---------------------------------------------------|
| ❌ Limited to conversation context | ✅ Process unlimited content at scale              |
| ❌ Can't analyze 100+ documents    | ✅ Knowledge graphs connect concepts automatically |
| ❌ Lost insights between sessions  | ✅ Semantic search your entire knowledge base      |

### Automated Quality & Intelligence Layer

  Vanilla Claude Code requires manual quality checks. Amplifier enforces
  excellence through an automation layer.

  | Vanilla Claude Code | Amplifier |
  |---------------------|-----------|
  | ❌ Manual quality checks | ✅ Automatic checks after every code change |
  | ❌ No session tracking | ✅ Comprehensive logging of all interactions |
  | ❌ Easy to miss errors | ✅ Desktop notifications for important events |



## Why Amplifier Works

The magic isn't any single feature—it's how they compound each other:

> Base Claude Code × Memory × Agents × Commands × Hooks × Integration
= 10,000x+ Capability Multiplication

### The Feedback Loop

Action → Hook Logs It → Analysis → Discovery → Memory Update →
Better Context → Smarter Agents → Better Actions → (repeat)

Each component amplifies the others:
- **Memory** provides context for **Agents**
- **Agents** execute through **Commands**
- **Commands** trigger **Hooks** for quality
- **Hooks** capture insights for **Memory**
- **Memory** makes everything smarter next time

This creates a self-improving system that gets better with every use.


---

## ✨ Amplifier in Action: Quick Wins to Try

### 1. Quick Tool Creation (5-10 minutes)

#### Suggested Pattern
> *Claude Code:* 
> ```
> /ultrathink-task make me a tool like @scenarios/blog_writer but that [your need]
> ```

#### Report Builder from Data Files

> *Claude Code:*
> ```
> /ultrathink-task make me a tool like @scenarios/blog_writer but that creates
> executive reports from CSV data. It should:
> 
> • Read CSV files from ./data/ directory
> • Analyze trends and patterns with AI
> • Generate visualizations (charts/graphs)
> • Create narrative explanations of insights
> • Output as formatted PDF report
> ```

Browse `scenarios/` to find a tool close to your need, then adapt it with `/ultrathink-task`. The closer the template matches your use case, the faster you'll have a working tool.

> [!TIP]
> Even if no scenario matches perfectly, use the one with the most similar thinking process (e.g., "read files → analyze → generate output") rather than similar domain (e.g., both about writing).


### 2. Knowledge Processing (10-20 minutes)
> *Claude Code:*
> ```
> Analyze all markdown files in [your directory] and build a knowledge graph
> showing concept relationships. Use @scenarios/blog_writer pattern for
> file processing.
> ```

### 3. Automated Code Review (Instant)
> *Claude Code:*
> ```
> /review-code-at-path src/auth/
> ```
> Spawns `security-guardian` + `zen-architect` + `test-coverage` specialist agents in parallel.






**[See how it can benefit you →](https://microsoft.github.io/amplifier)**



 ### More Power Commands

  Beyond `/ultrathink-task`, Amplifier includes:

  - `/prime` - Load philosophical context before major work
  - `/commit` - Generate context-aware commit messages
  - `/review-code-at-path <path>` - Deep code review with philosophy check
  - `/modular-build` - Build following modular design principles
  - `/transcripts` - Manage conversation history and compaction

  Commands can call other commands and spawn agents—workflows that orchestrate workflows.

---

## Quick Install Guide

<details>
<summary>Click to expand installation instructions</summary>

### Mac

```bash
brew install python3 node git pnpm uv
npm install -g @anthropic-ai/claude-cli
```

### Ubuntu/Debian/WSL

```bash
# System packages
sudo apt update && sudo apt install -y python3 python3-pip nodejs npm git

# pnpm
npm install -g pnpm
pnpm setup && source ~/.bashrc

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Claude Code CLI
npm install -g @anthropic-ai/claude-cli
```

### Windows

1. Install [WSL2](https://learn.microsoft.com/windows/wsl/install)
2. Run Ubuntu commands above inside WSL

### Manual Downloads

- [Python](https://python.org/downloads) (3.11 or newer)
- [Node.js](https://nodejs.org) (any recent version)
- [pnpm](https://pnpm.io/installation) (package manager)
- [Git](https://git-scm.com) (any version)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Claude Code CLI](https://github.com/anthropics/claude-code) (AI assistant)

</details>

---

*Experience the interactive documentation at [microsoft.github.io/amplifier](https://microsoft.github.io/amplifier)*
