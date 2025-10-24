# Amplifier: Metacognitive AI Development

> _"Automate complex workflows by describing how you think through them."_

> [!CAUTION]
> This project is a research demonstrator. It is in early development and may change significantly. Using permissive AI tools in your repository requires careful attention to security considerations and careful human supervision, and even then things can still go wrong. Use it with caution, and at your own risk. See [Disclaimer](#disclaimer).

Amplifier is a coordinated and accelerated development system that turns your expertise into reusable AI tools without requiring code. Describe the step-by-step thinking process for handling a task—a "metacognitive recipe"—and Amplifier builds a tool that executes it reliably. As you create more tools, they combine and build on each other, transforming individual solutions into a compounding automation system.

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
   thinking process to handle it step-by-step?
   ```

   Example of a metacognitive recipe:

   ```markdown
   I want to create a tool called "Research Synthesizer". Goal: help me research a topic by finding sources, extracting key themes, then asking me to choose which themes to explore in depth, and finally producing a summarized report.

   Steps:

   1. Do a preliminary web research on the topic and collect notes.
   2. Extract the broad themes from the notes.
   3. Present me the list of themes and highlight the top 2-3 you recommend focusing on (with reasons).
   4. Allow me to refine or add to that theme list.
   5. Do in-depth research on the refined list of themes.
   6. Draft a report based on the deep research, ensuring the report stays within my requested length and style.
   7. Offer the draft for my review and incorporate any feedback.
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

### Choosing Your Backend

Amplifier supports two AI backends:

**Claude Code** (VS Code Extension):
- Native VS Code integration
- Automatic hooks for session management
- Slash commands for common tasks
- Best for: VS Code users, GUI-based workflows

**Codex** (CLI):
- Standalone command-line interface
- MCP servers for extensibility
- Scriptable and automatable
- Best for: Terminal users, CI/CD, automation

#### Using Claude Code
```bash
# Set backend (optional, this is the default)
export AMPLIFIER_BACKEND=claude

# Start Claude Code normally
claude
```

#### Using Codex
```bash
# Set backend
export AMPLIFIER_BACKEND=codex

# Start Codex with Amplifier integration
./amplify-codex.sh

# Or with specific profile
./amplify-codex.sh --profile review
```

#### Environment Variables
- `AMPLIFIER_BACKEND` - Choose backend: "claude" or "codex" (default: claude)
- `CODEX_PROFILE` - Codex profile to use: "development", "ci", "review" (default: development)
- `MEMORY_SYSTEM_ENABLED` - Enable/disable memory system: "true" or "false" (default: true)

See `.env.example` for complete configuration options.

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

## Codex Integration

The `amplify-codex.sh` wrapper provides seamless integration with Codex CLI:

### Features
- **Automatic Session Management**: Loads context at start, saves memories at end
- **MCP Server Integration**: Quality checks, transcript export, memory system
- **Profile Support**: Different configurations for development, CI, and review
- **User Guidance**: Clear instructions for available tools and workflows

### Quick Start
```bash
# Make wrapper executable (first time only)
chmod +x amplify-codex.sh

# Start Codex with Amplifier
./amplify-codex.sh

# Follow the on-screen guidance to use MCP tools
```

### Available MCP Tools

When using Codex, these tools are available:

- **initialize_session** - Load relevant memories from previous work
- **check_code_quality** - Run quality checks after editing files
- **save_current_transcript** - Export session transcript
- **finalize_session** - Extract and save memories before ending

See [.codex/README.md](.codex/README.md) for detailed documentation.

### Manual Session Management

You can also run session management scripts manually:

```bash
# Initialize session with specific context
uv run python .codex/tools/session_init.py --prompt "Working on authentication"

# Clean up after session
uv run python .codex/tools/session_cleanup.py --session-id a1b2c3d4
```

### Wrapper Options

```bash
# Use specific profile
./amplify-codex.sh --profile ci

# Skip initialization
./amplify-codex.sh --no-init

# Skip cleanup
./amplify-codex.sh --no-cleanup

# Show help
./amplify-codex.sh --help
```

### Agent Conversion

Amplifier includes 25+ specialized agents that have been converted from Claude Code format to Codex format:

**Converting Agents:**
```bash
# Convert all agents from .claude/agents/ to .codex/agents/
make convert-agents

# Preview conversion without writing files
make convert-agents-dry-run

# Validate converted agents
make validate-codex-agents
```

**Using Converted Agents:**
```bash
# Automatic agent selection based on task
codex exec "Find and fix the authentication bug"
# Routes to bug-hunter agent

# Manual agent selection
codex exec --agent zen-architect "Design the caching layer"

# Programmatic usage
from amplifier import spawn_agent
result = spawn_agent("bug-hunter", "Investigate memory leak")
```

**Available Agents:**
- **Architecture**: zen-architect, database-architect, api-contract-designer
- **Implementation**: modular-builder, integration-specialist
- **Quality**: bug-hunter, test-coverage, security-guardian
- **Analysis**: analysis-engine, pattern-emergence, insight-synthesizer
- **Knowledge**: concept-extractor, knowledge-archaeologist, content-researcher
- **Specialized**: amplifier-cli-architect, performance-optimizer

See [.codex/agents/README.md](.codex/agents/README.md) for complete agent documentation.

## Backend Abstraction

Amplifier provides a unified API for working with both Claude Code and Codex backends through the backend abstraction layer.

### Quick Start

```python
from amplifier import get_backend

# Get backend (automatically selects based on AMPLIFIER_BACKEND env var)
backend = get_backend()

# Initialize session with memory loading
result = backend.initialize_session("Working on authentication")

# Run quality checks
result = backend.run_quality_checks(["src/auth.py"])

# Finalize session with memory extraction
messages = [{"role": "user", "content": "..."}]
result = backend.finalize_session(messages)
```

### Backend Selection

Choose your backend via environment variable:

```bash
# Use Claude Code (default)
export AMPLIFIER_BACKEND=claude

# Use Codex
export AMPLIFIER_BACKEND=codex

# Auto-detect based on available CLIs
export AMPLIFIER_BACKEND_AUTO_DETECT=true
```

### Agent Spawning

Spawn sub-agents with a unified API:

```python
from amplifier import spawn_agent

result = spawn_agent(
    agent_name="bug-hunter",
    task="Find potential bugs in src/auth.py"
)
print(result['result'])
```

### Available Operations

- **Session Management**: `initialize_session()`, `finalize_session()`
- **Quality Checks**: `run_quality_checks()`
- **Transcript Export**: `export_transcript()`
- **Agent Spawning**: `spawn_agent()`

### Documentation

For detailed documentation, see:
- [Backend Abstraction Guide](amplifier/core/README.md)
- [Claude Code Integration](.claude/README.md)
- [Codex Integration](.codex/README.md)

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

### 🌳 Parallel Development

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

### 💡 Best Practices & Tips

**Want to get the most out of Amplifier?** Check out [The Amplifier Way](docs/THIS_IS_THE_WAY.md) for battle-tested strategies including:

- Understanding capability vs. context
- Decomposition strategies for complex tasks
- Using transcript tools to capture and improve workflows
- Demo-driven development patterns
- Practical tips for effective AI-assisted development

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

## Project Structure

- `amplify-codex.sh` - Wrapper script for Codex CLI with Amplifier integration
- `tools/convert_agents.py` - Script to convert Claude Code agents to Codex format
- `.codex/` - Codex configuration, MCP servers, and tools
  - `config.toml` - Codex configuration with MCP server definitions
  - `mcp_servers/` - MCP server implementations (session, quality, transcripts)
  - `tools/` - Session management scripts (init, cleanup, export)
  - `README.md` - Detailed Codex integration documentation
- `.codex/agents/` - Converted agent definitions for Codex
  - `README.md` - Agent usage documentation
  - `*.md` - Individual agent definitions
- `.claude/` - Claude Code configuration and hooks
  - `README.md` - Claude Code integration documentation
- `amplifier/core/` - Backend abstraction layer
  - `backend.py` - Core backend interface and implementations
  - `agent_backend.py` - Agent spawning abstraction
  - `config.py` - Backend configuration management
  - `README.md` - Detailed backend abstraction documentation

Both backends share the same amplifier modules (memory, extraction, etc.) for consistent functionality. See [.codex/README.md](.codex/README.md) and [.claude/README.md](.claude/README.md) for detailed backend-specific documentation.

---

## Troubleshooting

### Codex Issues

**Wrapper script won't start:**
- Ensure Codex CLI is installed: `codex --version`
- Check that `.codex/config.toml` exists
- Verify virtual environment: `ls .venv/`
- Check logs: `cat .codex/logs/session_init.log`

**MCP servers not working:**
- Verify server configuration in `.codex/config.toml`
- Check server logs: `tail -f .codex/logs/*.log`
- Ensure amplifier modules are importable: `uv run python -c "import amplifier.memory"`

**Session management fails:**
- Check `MEMORY_SYSTEM_ENABLED` environment variable
- Verify memory data directory exists: `ls .data/memories/`
- Run scripts manually with `--verbose` flag for debugging

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

### Working with Agents

**Converting Agents:**
When Claude Code agents are updated, reconvert them:
```bash
make convert-agents
make validate-codex-agents
```

**Testing Agent Conversion:**
```bash
make test-agent-conversion
```

**Creating New Agents:**
1. Create agent in `.claude/agents/` following existing patterns
2. Run conversion: `make convert-agents`
3. Review converted agent in `.codex/agents/`
4. Test with Codex: `codex exec --agent <name> "<test-task>"`

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
