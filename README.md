# Amplifier: Metacognitive AI Development System

> _"A system that exponentially grows its own capabilities through modular composition."_

> [!CAUTION]
> This project is a research demonstrator. It is in early development and may change significantly. Using permissive AI tools in your repository requires careful attention to security considerations and careful human supervision, and even then things can still go wrong. Use it with caution, and at your own risk. See [Disclaimer](#disclaimer).

Amplifier is a development system whose architecture is driven by modular philosophy. **Our thesis:** this architecture enables exponential capability growth—not just for code, but for natural language + code scenarios. The system builds on itself, providing more capability as it builds itself out.

**What we're seeing now (early evidence):**

Current capabilities emerge from composing modules into linear workflows (1-D). Examples you can use today:
- **Scenarios** like [`blog_writer`](scenarios/blog_writer/) - multi-stage pipelines that transform rough ideas into polished content
- **DDD workflow** - structured feature development through connected phases
- **Specialized agents** - modular experts that combine to solve complex problems

As the modular foundation accumulates, capabilities will grow exponentially through increasingly complex compositions:

**0-D (Points):** Individual modules like [`StyleExtractor`](scenarios/blog_writer/style_extractor/) - each solves one focused problem

**1-D (Lines):** Linear workflows we're building now:
- [`blog_writer`](scenarios/blog_writer/) - Five modules in sequence transform ideas → polished posts
- DDD workflow - Connected phases ensure docs and code stay synchronized
- Each scenario composes existing modules into new capabilities

**2-D (Surfaces):** Complex interconnections we're moving toward:
- Modules with feedback loops (reviews trigger revisions, quality gates control flow)
- Multiple workflows branching and merging
- Dynamic composition based on context
- The `blog_writer` pipeline shows early 2-D characteristics with its iteration and feedback

**The scalability thesis:** As we build more foundational modules ([`ccsdk_toolkit`](amplifier/ccsdk_toolkit/), [`content_loader`](amplifier/content_loader/), specialized agents), each new capability becomes easier to create. Five modules enable fifteen new combinations. Fifteen enable hundreds. The architecture scales without limit because composition is the core mechanism.

**This is why it's a research demonstrator:** We're exploring whether modular composition can truly enable exponential capability growth in AI development systems. Early evidence suggests yes—each scenario we build makes the next one easier. But we're still discovering the patterns, tools, and workflows that make this real.

---

### What You Can Use Today

These are the "leaves" - end-user capabilities built through modular composition:

**Scenario Tools** (composing multiple modules into workflows):
- **[`blog_writer`](scenarios/blog_writer/)** - Transform rough ideas → polished posts in your voice
- **[`tips_synthesizer`](scenarios/tips_synthesizer/)** - Scattered tips → comprehensive guides
- **[`article_illustrator`](scenarios/article_illustrator/)** - Articles → contextually illustrated content
- **[`transcribe`](scenarios/transcribe/)** - Audio/video → structured transcripts
- **[`web_to_md`](scenarios/web_to_md/)** - Web content → clean markdown

**Development Workflows** (structured processes):
- **[DDD workflow](docs/document_driven_development/)** - `/ddd:1-plan → /ddd:2-docs → /ddd:3-code-plan → /ddd:4-code → /ddd:5-finish`
- Feature development with synchronized docs and code

**Behind the scenes:** Each capability is built from foundational modules:
- [`ccsdk_toolkit`](amplifier/ccsdk_toolkit/) - Claude Code SDK utilities
- [`content_loader`](amplifier/content_loader/) - Document processing
- [Specialized agents](.claude/agents/) - Domain experts (concept-extractor, modular-builder, zen-architect, etc.)
- Scenario-specific modules that combine into pipelines

**The pattern:** What looks like a single capability is actually modules composed together. As the foundation grows, building new capabilities becomes exponentially easier.

## 🚀 QuickStart

### Prerequisites Guide

<details>
<summary>Click to expand prerequisite instructions</summary>

1. Check if prerequisites are already met.

   - ```bash
     python3 --version  # Need 3.11+
     ```
   - ```bash
     uv --version       # Need any version
     ```
   - ```bash
     node --version     # Need any version
     ```
   - ```bash
     pnpm --version     # Need any version
     ```
   - ```bash
     git --version      # Need any version
     ```

2. Install what is missing.

   **Mac**

   ```bash
   brew install python3 node git pnpm uv
   ```

   **Ubuntu/Debian/WSL**

   ```bash
   # System packages
   sudo apt update && sudo apt install -y python3 python3-pip nodejs npm git

   # pnpm
   npm install -g pnpm
   pnpm setup && source ~/.bashrc

   # uv (Python package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **Windows**

   1. Install [WSL2](https://learn.microsoft.com/windows/wsl/install)
   2. Run Ubuntu commands above inside WSL

   **Manual Downloads**

   - [Python](https://python.org/downloads) (3.11 or newer)
   - [Node.js](https://nodejs.org) (any recent version)
   - [pnpm](https://pnpm.io/installation) (package manager)
   - [Git](https://git-scm.com) (any version)
   - [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)

> **Platform Note**: Development and testing has primarily been done in Windows WSL2. macOS and Linux should work but have received less testing. Your mileage may vary.

</details>

### Setup

```bash
# Clone Amplifier repository
git clone https://github.com/microsoft/amplifier.git amplifier
cd amplifier

# Install dependencies
make install

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac/WSL
# .venv\Scripts\Activate.ps1  # Windows PowerShell
```

### Get Started

```bash
# Start Claude Code
claude
```

**Create your first tool in 5 steps:**

1. **Identify a task** you want to automate (e.g., "weekly learning digest")

   Need ideas? Try This:

   ```
   /ultrathink-task I'm new to "metacognitive recipes". What are some useful
   tools I could create with Amplifier that show how recipes can self-evaluate
   and improve via feedback loops? Just brainstorm ideas, don't build them yet.
   ```

2. **Describe the thinking process** - How would an expert handle it step-by-step?

   Need help? Try This:

   ```
   /ultrathink-task This is my idea: <your idea here>. Can you help me describe the
   thinking process to handle it step-by-step?  Please present the final description
   in the following format:

   I want to create a tool called "<tool-name>".
   Goal: help me <your-goal>.
   Steps:

   1. <step 1>
   2. <step 2>
   3. <step 3>
   ...
   ```

3. **Generate with `/ultrathink-task`** - Let Amplifier build the tool

   ```
   /ultrathink-task <your metacognitive recipe here>
   ```

4. **Refine through feedback** - "Make connections more insightful"

   ```
   Let's see how it works. Run <your generated tool>.
   ```

   Then:

   - Observe and note issues.
   - Provide feedback in context.
   - Iterate until satisfied.

**Learn more** with [Create Your Own Tools](docs/CREATE_YOUR_OWN_TOOLS.md) - Deep dive into the process.

---

## 📖 How to Use Amplifier

### The Foundation: Modular Philosophy

**Everything in Amplifier starts with the modular philosophy.** Build systems from small, self-contained modules that snap together like bricks. Each module has clear boundaries and defined connection points—this lets you regenerate any piece independently without breaking the whole.

**Think "bricks and studs":**

- A **brick** = a self-contained component that delivers one clear responsibility
- A **stud** = the public interface where other modules connect
- **Regeneration over patching** - Rebuild components cleanly from their specifications rather than accumulating technical debt

See `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md` for the complete philosophy.

---

### The Amplifier Vision: Dimensional Growth

Amplifier's architecture enables dimensional growth—from simple modules to increasingly complex systems:

**0-D: Single Modules (Points)**

- One self-contained component
- Example: A document parser module, a metadata extractor

**1-D: Linear Workflows (Lines)**

- Modules connected in sequence
- **Metacognitive recipes** - Tools that execute step-by-step thinking processes
- **DDD workflow** - `/ddd:1-plan → /ddd:2-docs → /ddd:3-code-plan → /ddd:4-code → /ddd:5-finish`
- **/ultrathink-task** - Enforces agents in specific order, modularizes tasks into smaller groupings

**2-D: Planar Architectures (Surfaces)**

- Modules connected in more complex patterns (future direction)
- Multiple workflows interacting and branching

**The Exponential Effect:** As you build more modular components and workflows, they become building blocks that enable multiple new capabilities. Each tool you create makes future tools easier to build—not just one, but many. This architecture, driven by modular philosophy, is what enables exponential growth: the system builds on itself and builds itself out.

---

### Why Amplifier is a System, Not Just a Tool

**What makes Amplifier different is its architecture, driven by its modular philosophy.** Traditional LLM applications and development environments provide fixed capabilities—you use what's built into them. Amplifier is a **system** whose architecture enables exponential growth through use.

**The contrast:**

**Single-shot LLM requests:**

- Start from zero each time
- Capabilities don't accumulate
- Each task is independent
- Results don't compound

**Existing LLM software applications:**

- Fixed architecture built once
- Static wrapper around the model
- Predetermined capabilities
- Can't grow beyond initial design

**Amplifier as a system:**

- **Architecture-driven foundation** - Modular philosophy enables infinite composition
- **Exponential growth** - Each tool built enables multiple new tools
- **Builds on itself** - The system builds on itself AND builds itself out
- **Natural language + code** - Works across the full spectrum of automation scenarios
- **Infinite potential** - Modular foundation supports arbitrary complexity without hitting a ceiling

**Why this enables exponential (not just linear) growth:** You're not limited to what a single LLM conversation can do, or what a static application provides. You're building on an accumulating foundation where each contribution doesn't just add one capability—it enables many. A few conversations in, you have tools. A few weeks in, you have workflows. A few months in, you have a compounding automation system that does things no single-shot approach could accomplish.

**This is why Amplifier keeps getting better while other systems stay static.** The modular architecture doesn't just allow growth—it _enables_ exponential growth through use. Every problem solved becomes capability added. Every tool built becomes leverage that enables multiple new tools. The system builds upon itself infinitely.

---

### Leveraging Modularity: Four Key Approaches

These are different ways to apply the modular philosophy and participate in Amplifier's growth:

#### 1. Metacognitive Recipes: Build Tools That Think

Describe how an expert would approach a task step-by-step (a "metacognitive recipe"), and Amplifier builds a tool that executes that thinking process.

**The pattern:**

1. **Identify a workflow** you want to automate
2. **Describe the thinking process** - How would you approach it step-by-step?
3. **Generate with `/ultrathink-task`** - Amplifier builds the tool
4. **Use that tool to build more tools** - Each tool becomes a building block

**Example:** Create a document processor tool → use it to build a content analysis tool → use both to build a knowledge synthesis system. Each tool amplifies what you can do next.

See [Create Your Own Tools](docs/CREATE_YOUR_OWN_TOOLS.md) for the complete guide.

---

#### 2. Document-Driven Development (DDD): Modular Feature Workflows

Execute complete feature development as a linear workflow with explicit phases:

```bash
/ddd:1-plan         # Design the feature
/ddd:2-docs         # Update all docs (iterate until approved)
/ddd:3-code-plan    # Plan code changes
/ddd:4-code         # Implement and test (iterate until working)
/ddd:5-finish       # Clean up and finalize
```

**Why this is modular:** Each phase is a self-contained module that produces artifacts for the next phase. Docs stay synchronized with code because documentation leads implementation.

See [Document-Driven Development Guide](docs/document_driven_development/) for complete details.

---

#### 3. Ultrathink-Task: Modularized Problem Solving

The `/ultrathink-task` command applies modularity to problem-solving:

- Enforces specific agents in specific order
- Breaks tasks into smaller groupings (modularizes the task)
- Different agents handle different modules of the work
- Ensures right-sized tasks that fit within context windows

**Use this to:** Build scenario tools, solve complex problems through structured decomposition, ensure thorough analysis before implementation.

---

#### 4. Parallel Development: Modular Exploration

Use worktrees to create isolated modules of work that don't interfere with each other:

```bash
# Try multiple modular approaches
make worktree feature-jwt        # One approach module
make worktree feature-oauth      # Another approach module

# Work on different task modules in parallel
make worktree feature-dashboard  # Feature module
make worktree fix-security-bug   # Bug fix module

# Manage your modular workspaces
make worktree-list              # See all modules
make worktree-rm feature-jwt    # Clean up finished module
```

**Why this is modular:** Each worktree is an isolated module with its own branch and environment. Explore different approaches without interference, then merge the winner.

See [Worktree Guide](docs/WORKTREE_GUIDE.md) for advanced features.

---

### Growing Amplifier: How the System Builds Itself Out

**This is where the magic happens:** When you solve a problem or build a tool, that solution can become a new module in Amplifier's growing architecture. Your work doesn't just solve your immediate need—it adds capability to the system that everyone benefits from. This is how the system builds on itself and builds itself out.

**The growth pattern when things don't work initially:**

1. **Provide metacognitive context** - Describe the modular approach:

   Instead of: "Process 100 files and extract metadata"

   Try: "I need to process 100 files. Here's the modular approach:

   - Module 1: Tool that reads the file list
   - Module 2: Status tracking system
   - Module 3: File iterator with progress updates
   - Module 4: Metadata extractor per file
   - This ensures each piece can be regenerated and recovered independently"

2. **Break down into smaller modules** - If the task is too large, create useful building blocks first, then compose them

3. **Capture and modularize learning** - Use `/transcripts` to capture collaborative problem-solving, then have Amplifier analyze it to create new reusable modules

4. **Build tools that become modules** - Every tool you create becomes part of Amplifier's growing module library

**This is how dimensional growth happens:** Start with individual modules (0-D), connect them into workflows (1-D), then eventually compose them into more complex architectures (2-D). Each contribution adds to the foundation that everyone builds upon, enabling exponential growth.

---

### Supporting Strategies for Modular Growth

**Context Over Capability**

Most "can't do this" problems are "doesn't have the right context for this module" problems. Provide:

- **Task context** - What module you're trying to create and why
- **Metacognitive context** - The step-by-step modular approach (see example above)
- **Project context** - Your modular architectural principles (use AGENTS.md in workspace pattern)

**Decomposition is Modularization**

Big asks fail because they're monolithic. Break them into small, self-contained modules first. Each module:

- Has clear boundaries and interfaces
- Can be regenerated independently
- Serves multiple purposes in different compositions
- Makes future systems easier to build

**Transcript-Driven Module Creation**

After collaborative problem-solving:

1. Run `/transcripts` or `./tools/claude_transcript_builder.py`
2. Have Amplifier analyze where you provided guidance
3. Convert that guidance into reusable modules
4. Improvements get merged, adding to Amplifier's module library

This is how Amplifier grows from usage—each solved problem becomes a new building block that enables exponential growth.

---

### Project Organization: The Workspace Pattern

For serious projects, organize with Amplifier hosting your project as a git submodule:

- **Clean boundaries** - Project files in project directory, Amplifier stays pristine
- **Context persistence** - AGENTS.md preserves project guidance across sessions
- **Scalability** - Work on multiple projects without interference

See [Workspace Pattern Guide](docs/WORKSPACE_PATTERN.md) for complete details.

---

### Quick Reference: Modular Commands

```bash
# Build modular tools with metacognitive recipes
/ultrathink-task <describe the modular thinking process>

# Execute modular feature workflow
/ddd:1-plan → /ddd:2-docs → /ddd:3-code-plan → /ddd:4-code → /ddd:5-finish

# Create isolated modules for parallel exploration
make worktree <name>       # Create isolated module workspace
make worktree-list         # View all module workspaces
make worktree-rm <name>    # Clean up finished module

# Capture and modularize learning
/transcripts               # Restore full conversation
make transcript-list       # Browse past sessions
./tools/claude_transcript_builder.py  # Build transcript modules

# Organize as modular workspace
git submodule add <url> <name>  # Add project module to workspace
# Create AGENTS.md for persistent modular context
```

**Getting started:** Begin by thinking modularly. Describe a workflow you want to automate in modular terms—what are the self-contained pieces and how do they connect? As you create more modules, they naturally build on each other (0-D → 1-D → 2-D), creating the compounding effect that enables Amplifier's exponential growth.

**The vision:** You're not just using Amplifier—you're participating in building it. Each module you create adds to the foundation that everyone builds upon. This is the system in action—architecture driven by modular philosophy, enabling the system to build on itself and build itself out.

For deeper strategies and advanced techniques, see [The Amplifier Way](docs/THIS_IS_THE_WAY.md).

---

## 🎯 Project Setup

### Setup Your Project

1. For existing GitHub projects

   ```bash
   # Add your project as a submodule
   cd amplifier
   git submodule add git@github.com:yourname/my-project.git my-project
   ```

2. For new projects

   ```bash
   # Create new project and add as a submodule
   cd amplifier
   mkdir my-project
   cd my-project
   git init
   git remote add origin git@github.com:yourname/my-project.git
   cd ..
   git submodule add ./my-project my-project
   ```

```bash
# Install dependencies
make install

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac/WSL
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Set up project context & start Claude
echo "# Project-specific AI guidance" > my-project/AGENTS.md
claude
```

_Tell Claude Code:_

```
I'm working on @yourproject/ with Amplifier.
Read @yourproject/AGENTS.md for project context.
Let's use /ddd:1-plan to design the architecture.
```

> [!NOTE]
>
> **Why use this?** Clean git history per component, independent Amplifier updates, persistent context across sessions, scalable to multiple projects. See [Workspace Pattern for Serious Projects](#workspace-pattern-for-serious-projects) below for full details.

---

## ✨ Features To Try

### 🔧 Create Amplifier-powered Tools for Scenarios

Amplifier is designed so **you can create new AI-powered tools** just by describing how they should think. See the [Create Your Own Tools](docs/CREATE_YOUR_OWN_TOOLS.md) guide for more information.

- _Tell Claude Code:_ `Walk me through creating my own scenario tool`

- _View the documentation:_ [Scenario Creation Guide](docs/CREATE_YOUR_OWN_TOOLS.md)

### 🤖 Explore Amplifier's agents on your code

Try out one of the specialized experts:

- _Tell Claude Code:_

  `Use the zen-architect agent to design my application's caching layer`

  `Deploy bug-hunter to find why my login system is failing`

  `Have security-guardian review my API implementation for vulnerabilities`

- _View the files:_ [Agents](.claude/agents/)

### 📝 Document-Driven Development

**Why use this?** Eliminate doc drift and context poisoning. When docs lead and code follows, your specifications stay perfectly in sync with reality.

Execute a complete feature workflow with numbered slash commands:

```bash
/ddd:1-plan         # Design the feature
/ddd:2-docs         # Update all docs (iterate until approved)
/ddd:3-code-plan    # Plan code changes
/ddd:4-code         # Implement and test (iterate until working)
/ddd:5-finish       # Clean up and finalize
```

Each phase creates artifacts the next phase reads. You control all git operations with explicit authorization at every step. The workflow prevents expensive mistakes by catching design flaws before implementation.

- _Tell Claude Code:_ `/ddd:0-help`

- _View the documentation:_ [Document-Driven Development Guide](docs/document_driven_development/)

### 🌳 Advanced Worktree Workflows

**You've learned the basics above.** Here are advanced worktree patterns for power users:

- **Hide worktrees from VSCode** when not actively using them to reduce clutter
- **Adopt branches from other machines** to continue work across environments
- **Manage long-running experiments** with organized naming conventions
- **Archive completed worktrees** while preserving their git history

See the [Worktree Guide](docs/WORKTREE_GUIDE.md) for complete details on these advanced techniques.

- _Tell Claude Code:_ `What make worktree commands are available to me?`

- _View the documentation:_ [Worktree Guide](docs/WORKTREE_GUIDE.md)

### 📊 Enhanced Status Line

See costs, model, and session info at a glance:

**Example**: `~/repos/amplifier (main → origin) Opus 4.1 💰$4.67 ⏱18m`

Shows:

- Current directory and git branch/status
- Model name with cost-tier coloring (red=high, yellow=medium, blue=low)
- Running session cost and duration

Enable with:

```
/statusline use the script at .claude/tools/statusline-example.sh
```

### 💬 Conversation Transcripts

**Never lose context again.** Amplifier automatically exports your entire conversation before compaction, preserving all the details that would otherwise be lost. When Claude Code compacts your conversation to stay within token limits, you can instantly restore the full history.

**Automatic Export**: A PreCompact hook captures your conversation before any compaction event:

- Saves complete transcript with all content types (messages, tool usage, thinking blocks)
- Timestamps and organizes transcripts in `.data/transcripts/`
- Works for both manual (`/compact`) and auto-compact events

**Easy Restoration**: Use the `/transcripts` command in Claude Code to restore your full conversation:

```
/transcripts  # Restores entire conversation history
```

The transcript system helps you:

- **Continue complex work** after compaction without losing details
- **Review past decisions** with full context
- **Search through conversations** to find specific discussions
- **Export conversations** for sharing or documentation

**Transcript Commands** (via Makefile):

```bash
make transcript-list                # List available transcripts
make transcript-search TERM="auth"  # Search past conversations
make transcript-restore             # Restore full lineage (for CLI use)
```

### 🏗️ Workspace Pattern for Serious Projects

**For long-term development**, consider using the workspace pattern where Amplifier hosts your project as a git submodule. This architectural approach provides:

- **Clean boundaries** - Project files stay in project directory, Amplifier stays pristine and updatable
- **Version control isolation** - Each component maintains independent git history
- **Context persistence** - AGENTS.md preserves project guidance across sessions
- **Scalability** - Work on multiple projects simultaneously without interference
- **Philosophy alignment** - Project-specific decision filters and architectural principles

Perfect for:

- Projects that will live for months or years
- Codebases with their own git repository
- Teams collaborating on shared projects
- When you want to update Amplifier without affecting your projects
- Working on multiple projects that need isolation

The pattern inverts the typical relationship: instead of your project containing Amplifier, Amplifier becomes a dedicated workspace that hosts your projects. Each project gets persistent context through AGENTS.md (AI guidance), philosophy documents (decision filters), and clear namespace boundaries using `@project-name/` syntax.

- _Tell Claude Code:_ `What are the recommended workspace patterns for serious projects?`

- _View the documentation:_ [Workspace Pattern Guide](docs/WORKSPACE_PATTERN.md) - complete setup, usage patterns, and migration from `ai_working/`.

### 💡 Going Deeper

**Already using the core philosophy above?** Ready to level up? Check out [The Amplifier Way](docs/THIS_IS_THE_WAY.md) for advanced strategies including:

- Deep-dive on decomposition patterns for complex tasks
- Advanced transcript tools and workflow capture techniques
- Demo-driven development patterns
- Expert techniques for AI-assisted development
- Context engineering for maximum effectiveness

- _Tell Claude Code:_ `What are the best practices to get the MOST out of Amplifier?`

- _View the documentation:_ [The Amplifier Way](docs/THIS_IS_THE_WAY.md)

### ⚙️ Development Commands

```bash
make check            # Format, lint, type-check
make test             # Run tests
make ai-context-files # Rebuild AI context
```

### 🧪 Testing & Benchmarks

Testing and benchmarking are critical to ensuring that any product leveraging AI, including Amplifier, is quantitatively measured for performance and reliability.
Currently, we leverage [terminal-bench](https://github.com/laude-institute/terminal-bench) to reproducibly benchmark Amplifier against other agents.
Further details on how to run the benchmark can be found in [tests/terminal_bench/README.md](tests/terminal_bench/README.md).

---

## Disclaimer

> [!IMPORTANT] > **This is an experimental system. _We break things frequently_.**

- Not accepting contributions yet (but we plan to!)
- No stability guarantees
- Pin commits if you need consistency
- This is a learning resource, not production software
- **No support provided** - See [SUPPORT.md](SUPPORT.md)

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
