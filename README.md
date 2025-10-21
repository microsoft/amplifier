# Amplifier: Supercharged AI Development Environment

> _"I have more ideas than time to try them out"_ — The problem we're solving.

> [!CAUTION]
> This project is a research demonstrator. It is in early development and may change significantly. Using permissive AI tools in your repository requires careful attention to security considerations and careful human supervision, and even then things can still go wrong. Use it with caution, and at your own risk.

Amplifier is a coordinated and accelerated development system that provides specialized AI agents, persistent knowledge that compounds over time, and workflows that execute complex methodologies.

## 🚀 QuickStart

### Prerequisites Guide

<details>
<summary>Click to expand prerequisite instructions</summary>

1. Check if prerequisites are already met.

   - `python3 --version  # Need 3.11+`
   - `uv --version       # Need any version`
   - `node --version     # Need any version`
   - `pnpm --version     # Need any version`
   - `git --version      # Need any version`

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
# Clone the repository
git clone https://github.com/microsoft/amplifier.git
cd amplifier
```

```bash
# Install Python dependencies
make install
```

```bash
# Activate virtual environment
source .venv/bin/activate # Linux/Mac/WSL
# .venv\Scripts\Activate.ps1 # Windows PowerShell
```

### Use Amplifier via Claude Code

**Option 1** -
Work on a new (or existing) project

```bash
mkdir ai_working/<my-new-project-name> # new
# ln -s ../<relative-path-to-my-existing-project> ai_working/<mt-existing-project-name> # existing
claude
```

_Type into Claude Code:_

```
I'm working in ai_working/<project-name>, and using the capabilities from
amplifier.
```

**Option 2** - Work on the Amplifier project itself

```bash
claude
```

**Option 3** - Use the workspace pattern for serious projects

For projects that need clean boundaries, independent version control, and persistent AI context:

```bash
# Fork/clone Amplifier as your workspace
git clone https://github.com/microsoft/amplifier.git my-workspace
cd my-workspace

# Add your project as a submodule
git submodule add <your-project-url> my-project

# Set up project context (see guide for AGENTS.md template)
cd my-project
# Create AGENTS.md with project guidance

# Start working
cd ..
claude
```

_In Claude Code:_
```
I'm working on the @my-project/ project within this workspace.
Please read @my-project/AGENTS.md for project-specific guidance.
```

**Why use this?** Clean git history per component, independent Amplifier updates, persistent context across sessions, scalable to multiple projects. See the [Workspace Pattern Guide](docs/WORKSPACE_PATTERN.md) for full details.

---

## What Is Amplifier?

**Amplifier is a complete development environment that takes AI coding assistants and supercharges them with discovered patterns, specialized expertise, and powerful automation — turning a helpful assistant into a force multiplier that can deliver complex solutions with minimal hand-holding.**

We've taken our learnings about what works in AI-assisted development and packaged them into a ready-to-use environment. Instead of starting from scratch every session, you get immediate access to proven patterns, specialized agents for different tasks, and workflows that actually work.

**Amplifier provides powerful tools and systems:**

- **20+ Specialized Agents**: Each expert in specific tasks (architecture, debugging, security, etc.)
- **Pre-loaded Context**: Proven patterns and philosophies built into the environment
- **Parallel Worktree System**: Build and test multiple solutions simultaneously
- **Knowledge Extraction System**: Transform your documentation into queryable, connected knowledge
- **Conversation Transcripts**: Never lose context - automatic export before compaction, instant restoration
- **Automation Tools**: Quality checks and patterns enforced automatically

---

## 📖 How to Use Amplifier

### Create Amplifier-powered Tools for Scenarios

Amplifier is designed so **you can create new AI-powered tools** just by describing how they should think. See the [Create Your Own Tools](docs/CREATE_YOUR_OWN_TOOLS.md) guide for more information.

### Explore Ampifier's agents on your code

Try out one of the specialized experts:

- "Use the zen-architect agent to design my application's caching layer"
- "Deploy bug-hunter to find why my login system is failing"
- "Have security-guardian review my API implementation for vulnerabilities"

### Document-Driven Development

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

See the [Document-Driven Development Guide](docs/document_driven_development/) for complete documentation, or run `/ddd:0-help` in Claude Code.

### Parallel Development

**Why use this?** Stop wondering "what if" — build multiple solutions simultaneously and pick the winner.

```bash
# Try different approaches in parallel
make worktree feature-jwt     # JWT authentication approach
make worktree feature-oauth   # OAuth approach in parallel

# Compare and choose
make worktree-list            # See all experiments
make worktree-rm feature-jwt  # Remove the one you don't want
```

Each worktree is completely isolated with its own branch, environment, and context.

See the [Worktree Guide](docs/WORKTREE_GUIDE.md) for advanced features, such as hiding worktrees from VSCode when not in use, adopting branches from other machines, and more.

### Enhanced Status Line

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

### Best Practices & Tips

**Want to get the most out of Amplifier?** Check out [The Amplifier Way](docs/THIS_IS_THE_WAY.md) for battle-tested strategies including:

- Understanding capability vs. context
- Decomposition strategies for complex tasks
- Using transcript tools to capture and improve workflows
- Demo-driven development patterns
- Practical tips for effective AI-assisted development

### Workspace Pattern for Serious Projects

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

See the [Workspace Pattern Guide](docs/WORKSPACE_PATTERN.md) for complete setup, usage patterns, and migration from `ai_working/`.

## 🎯 Key Features

### Specialized Agents

Instead of one generalist AI, you get 20+ specialists:

**Core Development**:

- `zen-architect` - Designs with ruthless simplicity
- `modular-builder` - Builds following modular principles
- `bug-hunter` - Systematic debugging
- `test-coverage` - Comprehensive testing
- `api-contract-designer` - Clean API design

**Analysis & Optimization**:

- `security-guardian` - Security analysis
- `performance-optimizer` - Performance profiling
- `database-architect` - Database design and optimization
- `integration-specialist` - External service integration

**Knowledge & Insights**:

- `insight-synthesizer` - Finds hidden connections
- `knowledge-archaeologist` - Traces idea evolution
- `concept-extractor` - Extracts knowledge from documents
- `ambiguity-guardian` - Preserves productive contradictions

**Meta & Support**:

- `subagent-architect` - Creates new specialized agents
- `post-task-cleanup` - Maintains codebase hygiene
- `content-researcher` - Researches from content collection

[See `.claude/AGENTS_CATALOG.md` for the complete list]

### Knowledge Base

**Why use this?** Stop losing insights. Every document, specification, design decision, and lesson learned becomes part of your permanent knowledge that Claude can instantly access.

> [!NOTE]
> Knowledge extraction is an evolving feature that continues to improve with each update.

1. **Add your content** (any text-based files: documentation, specs, notes, decisions, etc.)

2. **Build your knowledge base**:

   ```bash
   make knowledge-update  # Extracts concepts, relationships, patterns
   ```

3. **Query your accumulated wisdom**:
   ```bash
   make knowledge-query Q="authentication patterns"
   make knowledge-graph-viz  # See how ideas connect
   ```

### Conversation Transcripts

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
make transcript-list            # List available transcripts
make transcript-search TERM="auth"  # Search past conversations
make transcript-restore         # Restore full lineage (for CLI use)
```

### Modular Builder (Lite)

A one-command workflow to go from an idea to a module (**Contract & Spec → Plan → Generate → Review**) inside the Amplifier Claude Code environment.

- **Run inside a Claude Code session:**
  ```
  /modular-build Build a module that reads markdown summaries, synthesizes net-new ideas with provenance, and expands them into plans. mode: auto level: moderate
  ```
- **Docs:** see `docs/MODULAR_BUILDER_LITE.md` for the detailed flow and guardrails.
- **Artifacts:** planning goes to `ai_working/<module>/…` (contract/spec/plan/review); code & tests to `amplifier/<module>/…`.
- **Isolation & discipline:** workers read only this module’s **contract/spec** plus dependency **contracts**. The spec’s **Output Files** are the single source of truth for what gets written. Every contract **Conformance Criterion** maps to tests. 〔Authoring Guide〕

#### Modes

- `auto` (default): runs autonomously if confidence ≥ 0.75; otherwise falls back to `assist`.
- `assist`: asks ≤ 5 crisp questions to resolve ambiguity, then proceeds.
- `dry-run`: plan/validate only (no code writes).

#### Continue later

Re‑run `/modular-build` with a follow‑up ask; it resumes from `ai_working/<module>/session.json`.

### Development Commands

```bash
make check            # Format, lint, type-check
make test             # Run tests
make ai-context-files # Rebuild AI context
```

## 💡 Example Workflows

### Building a Feature in Your Code

1. **Design**: "Use zen-architect to design my notification system"
2. **Build**: "Have modular-builder implement the notification module"
3. **Test**: "Deploy test-coverage to add tests for the new notification feature"

### Debugging Your Application

1. **Investigate**: "Use bug-hunter to find why my application's API calls are failing"
2. **Verify**: "Have security-guardian review my authentication implementation"

### Knowledge-Driven Development

1. **Extract**: `make knowledge-update` (processes your documentation)
2. **Query**: `make knowledge-query Q="error handling patterns"`
3. **Apply**: "Implement error handling using patterns from our knowledge base"

## 🎨 Creating Your Own Scenario Tools

**Want to create tools like the ones in the [scenarios/ directory](scenarios/)? You don't need to be a programmer.**

### Finding Tool Ideas

Not sure what to build? Ask Amplifier to brainstorm with you:

```
/ultrathink-task I'm new to the concepts of "metacognitive recipes" - what are some
interesting tools that you could create that I might find useful, that demonstrate
the value of "metacognitive recipes"? Especially any that would demonstrate how such
could be used to auto evaluate and recover/improve based upon self-feedback loops.
Don't create them, just give me some ideas.
```

This brainstorming session will give you ideas like:

- **Documentation Quality Amplifier** - Improves docs by simulating confused readers
- **Research Synthesis Quality Escalator** - Extracts and refines knowledge from documents
- **Code Quality Evolution Engine** - Writes code, tests it, learns from failures
- **Multi-Perspective Consensus Builder** - Simulates different viewpoints to find optimal solutions
- **Self-Debugging Error Recovery** - Learns to fix errors autonomously

The magic happens when you combine:

1. **Amplifier's brainstorming** - Generates diverse possibilities
2. **Your domain knowledge** - You know your needs and opportunities
3. **Your creativity** - Sparks recognition of what would be useful

### Creating Your Tool

Once you have an idea:

1. **Describe your goal** - What problem are you solving?
2. **Describe the thinking process** - How should the tool approach it?
3. **Let Amplifier build it** - Use `/ultrathink-task` to create the tool
4. **Iterate to refine** - Provide feedback as you use it
5. **Share it back** - Help others by contributing to scenarios/

**Example**: The blog writer tool was created with one conversation where the user described:

- The goal (write blog posts in my style)
- The thinking process (extract style → draft → review sources → review style → get feedback → refine)

No code was written by the user. Just description → Amplifier builds → feedback → refinement.

For detailed guidance, see [scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md](scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md).

> [!IMPORTANT] > **This is an experimental system. _We break things frequently_.**

- Not accepting contributions yet (but we plan to!)
- No stability guarantees
- Pin commits if you need consistency
- This is a learning resource, not production software
- **No support provided** - See [SUPPORT.md](SUPPORT.md)

## 🧪 Testing & Benchmarks

Testing and benchmarking are critical to ensuring that any product leveraging AI, including Amplifier, is quantitatively measured for performance and reliability.
Currently, we leverage [terminal-bench](https://github.com/laude-institute/terminal-bench) to reproducibly benchmark Amplifier against other agents.
Further details on how to run the benchmark can be found in [tests/terminal_bench/README.md](tests/terminal_bench/README.md).

## 🔮 Vision

We're building toward a future where:

1. **You describe, AI builds** - Natural language to working systems
2. **Parallel exploration** - Test 10 approaches simultaneously
3. **Knowledge compounds** - Every project makes you more effective
4. **AI handles the tedious** - You focus on creative decisions

The patterns, knowledge base, and workflows in Amplifier are designed to be portable and tool-agnostic, ready to evolve with the best available AI technologies.

See [AMPLIFIER_VISION.md](AMPLIFIER_VISION.md) for details.

## Current Limitations

- Knowledge extraction works best in Claude environment
- Processing time: ~10-30 seconds per document
- Memory system still in development

---

_"The best AI system isn't the smartest - it's the one that makes YOU most effective."_

---

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
