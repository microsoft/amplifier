# Amplifier: Your AI Development Amplified

## 🎯 Why Amplifier?

Claude Code is powerful on its own—but Amplifier transforms it from a coding assistant into a coordinated and accelerated development system. Amplifier offers a pre-built suite of advanced capabilities for immediate use.

**[See how it can benefit you →](https://microsoft.github.io/amplifier)**

---

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

#### Install
```bash
git clone https://github.com/microsoft/amplifier.git
cd amplifier
make configure
make install
source .venv/bin/activate # Linux/Mac/WSL 
# source .venv\Scripts\Activate.ps1 # Windows PowerShell 
```

#### Verify
```bash
make check
make test
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

## ✨ Amplifier in Action: Create Custom Tools in Minutes

One of Amplifier's most powerful features is the ability to rapidly create custom CLI tools tailored to your exact
needs. By using existing tools in `scenarios/` as templates, you can describe your thinking process and let
Amplifier build production-ready tools with minimal iteration.

### The Pattern

> *Claude Code:*
> ```
> /ultrathink-task make me a tool like @scenarios/[template] but that [your custom need]
>```

This simple pattern leverages proven patterns and inherits best practices, generates production code following amplifier's modular design philosophy, and takes minutes, not hours to get working tools.


### Example 1
#### Newsletter from Research Notes

> *Claude Code:*
> ```
> /ultrathink-task make me a tool like @scenarios/blog_writer but that creates
> weekly newsletters from my research notes directory. It should:
>
> • Scan ./research_notes/ for markdown files
> • Group by topic using AI
> • Generate a newsletter with sections per topic
> • Include summaries and key insights
> • Save as HTML email template
> ```

What You Get:
- ✅ Recursive file scanning with proper glob patterns
- ✅ AI-powered topic grouping and clustering
- ✅ Progress checkpoints for interruption/resume
- ✅ HTML output with responsive email formatting
- ✅ Session management for iterative refinement

⏱️ Time: ~10 minutes for working tool


### Example 2
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

What You Get:
- ✅ Data processing with pandas integration
- ✅ AI-powered insight extraction and analysis
- ✅ Chart generation with matplotlib/plotly
- ✅ Professional PDF formatting
- ✅ Batch processing for multiple datasets

⏱️ Time: ~20 minutes for working tool


### Example 3
#### Tutorial Creator from Examples

> *Claude Code:*
> ```
> /ultrathink-task make me a tool like @scenarios/article_illustrator but that
> creates step-by-step tutorials from code examples. It should:
> 
> • Analyze code examples to identify learning progression
> • Generate explanatory text for each step
> • Create diagrams showing code flow
> • Insert illustrations at key learning points
> • Output as interactive markdown with embedded demos
> ```

What You Get:
- ✅ Code analysis and sequencing logic
- ✅ Explanatory content generation with AI
- ✅ Mermaid diagram creation for flows
- ✅ Interactive code blocks with syntax highlighting
- ✅ Progressive learning structure (beginner → advanced)

⏱️ Time: ~15 minutes for working tool


### Try It Yourself

Browse `scenarios/` to find a tool close to your need, then adapt it with `/ultrathink-task`. The closer the template
matches your use case, the faster you'll have a working tool.

> [!TIP]
> Even if no scenario matches perfectly, use the one with the most similar thinking process (e.g., "read files → analyze → generate output") rather than similar domain (e.g., both about writing).

## ✨ How Amplifier is Different from Claude Code

### Four Key Differentiators

> [Persistent Memory & Learning](#persistent-memory-&-learning) | [Parallel
  Specialized Agent Intelligence](#specialized-agent-intelligence) | [Executable
  Methodologies](#executable-methodologies) | [Knowledge Synthesis Pipeline](#knowledge-synthesis-pipeline)

#### Persistent Memory & Learning

Every session with vanilla Claude Code starts from zero. Amplifier builds institutional knowledge that compounds over time.

| Vanilla Claude Code               | Amplifier                                                         |
|-----------------------------------|-------------------------------------------------------------------|
| ❌ Fresh start every session       | ✅ Auto-loaded memory files |
| ❌ Repeatedly explain your project | ✅ Context persists across sessions                                |
| ❌ Repeat past mistakes            | ✅ System learns & prevents recurrence                             |

💡 Real Impact Example:

> You solve a tricky OneDrive file sync issue in WSL2. Amplifier documents the root cause, solution, and prevention strategy in DISCOVERIES.md.
>
> **Result** 
> Future sessions automatically apply this knowledge. You never re-explain. The system literally learned from your experience.
>

#### Specialized Agent Intelligence
One generalist trying to do everything versus an expert team working in parallel. Amplifier orchestrates 25+ specialized agents, each with focused expertise.

| Vanilla Claude Code                       | Amplifier                                       |
|-------------------------------------------|-------------------------------------------------|
| ❌ One generalist AI for everything        | ✅ 25+ specialized agents with focused expertise |
| ❌ Serial processing (one thing at a time) | ✅ Parallel execution across multiple agents     |
| ❌ Single context window gets confused     | ✅ Separate context per agent stays focused      |

💡 Real Impact Example:

> You're building a new authentication feature. With vanilla Claude Code, you'd prompt sequentially: design → security → tests → implementation (30+ messages).
> 
> **Result** 
> Amplifier runs simultaneously: zen-architect (design), security-guardian (vulnerabilities), test-coverage (strategy), modular-builder (implementation). All
> work in parallel, then synthesize results.

#### Executable Methodologies
Manual multi-step prompting vs. one-command workflows. Amplifier transforms complex methodologies into executable slash commands.

| Vanilla Claude Code                | Amplifier                                        |
|------------------------------------|--------------------------------------------------|
| ❌ Manual workflow orchestration    | ✅ Custom slash commands execute entire processes |
| ❌ Repeated prompting for each step | ✅ One command = complete workflow                |
| ❌ Lose place if interrupted        | ✅ TodoWrite tracking + state preservation        |

💡 Real Impact Example:

> You need to implement authentication. With vanilla Claude Code:
> ```
> > "Break down this task"
> > "Now create a plan"
> > "Check for issues"
> > "Identify dependencies"
> [30 messages later...]
> ```
> 
> **Result** 
> With Amplifier, you run "/ultrathink-task implement authentication" and it automatically orchestrates TodoWrite tracking, parallel agent spawning,
> architecture-implementation-review cycles, and validation. 30 messages → 1 command.

#### Knowledge Synthesis Pipeline
Conversation-limited context vs. unlimited knowledge processing. Amplifier extracts, connects, and makes searchable insights from your entire content library.

| Vanilla Claude Code               | Amplifier                                         |
|-----------------------------------|---------------------------------------------------|
| ❌ Limited to conversation context | ✅ Process unlimited content at scale              |
| ❌ Can't analyze 100+ documents    | ✅ Knowledge graphs connect concepts automatically |
| ❌ Lost insights between sessions  | ✅ Semantic search your entire knowledge base      |

💡 Real Impact Example:

> You have 200 articles about distributed systems scattered across folders. Vanilla Claude Code can't process them all—context limits force manual summarization.
> 
> **Result** 
> With Amplifier:
> ```
> make knowledge-sync                               # Extract from all 200 articles
> make knowledge-query Q="CAP theorem tradeoffs"    # Query instantly
> make knowledge-graph-viz                          # See connections visually
> ```
> This isn't summarization—it's building a queryable, evolving knowledge structure that finds patterns you didn't know existed.


## Why Amplifier Works

The magic isn't any single feature—it's how they multiply each other. Persistent
Memory & Learning gives context to Parallel Specialized Agents. Agents coordinate
through Executable Methodologies. Methodologies capture insights via the Knowledge
Synthesis Pipeline. Synthesis feeds back into Memory. It compounds.

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
