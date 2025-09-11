# Amplifier: Supercharged AI Development Environment

> "I have more ideas than time to try them out" — The problem we're solving

> [!CAUTION]
> This project is a research demonstrator. It is in early development and may change significantly. Using permissive AI tools in your repository requires careful attention to security considerations and careful human supervision, and even then things can still go wrong. Use it with caution, and at your own risk.

## What Is Amplifier?

**Amplifier is a complete development environment that takes AI coding assistants and supercharges them with discovered patterns, specialized expertise, and powerful automation — turning a helpful assistant into a force multiplier that can deliver complex solutions with minimal hand-holding.**

We've taken our learnings about what works in AI-assisted development and packaged them into a ready-to-use environment. Instead of starting from scratch every session, you get immediate access to proven patterns, specialized agents for different tasks, and workflows that actually work.

**Amplifier provides powerful tools and systems:**

- **20+ Specialized Agents**: Each expert in specific tasks (architecture, debugging, security, etc.)
- **Pre-loaded Context**: Proven patterns and philosophies built into the environment
- **Parallel Worktree System**: Build and test multiple solutions simultaneously
- **Knowledge Extraction System**: Transform your documentation into queryable, connected knowledge
- **Automation Tools**: Quality checks and patterns enforced automatically

## 🚀 Step-by-Step Setup

### Prerequisites

Before starting, you'll need:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js** - [Download Node.js](https://nodejs.org/)
- **VS Code** (recommended) - [Download VS Code](https://code.visualstudio.com/)
- **Git** - [Download Git](https://git-scm.com/)

> **Platform Note**: Development and testing has primarily been done in Windows WSL2. macOS and Linux should work but have received less testing. Your mileage may vary.

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/microsoft/amplifier.git
   cd amplifier
   ```

2. **Run the installer**:

   ```bash
   make install
   ```

   This installs Python dependencies, the Claude CLI, and sets up your environment.

3. **Configure your data directories** (Recommended but optional):

   **Why configure this?** By default, Amplifier stores data in `.data/` (git-ignored). But centralizing your data externally gives you:

   - **Shared knowledge across all worktrees** - Every parallel experiment accesses the same knowledge base
   - **Cross-device synchronization** - Work from any machine with the same accumulated knowledge
   - **Automatic cloud backup** - Never lose your extracted insights
   - **Reusable across projects** - Apply learned patterns to new codebases

   Set up external directories:

   ```bash
   cp .env.example .env
   # Edit .env to point to your preferred locations
   ```

   Example configuration using cloud storage:

   ```bash
   # Centralized knowledge base - shared across all worktrees and devices
   # Using OneDrive/Dropbox/iCloud enables automatic backup!
   AMPLIFIER_DATA_DIR=~/OneDrive/amplifier/data

   # Your source materials (documentation, specs, design docs, notes)
   # Can point to multiple folders where you keep content
   AMPLIFIER_CONTENT_DIRS=ai_context,~/OneDrive/amplifier/content,~/Documents/notes
   ```

4. **Activate the environment** (if not already active):
   ```bash
   source .venv/bin/activate  # Linux/Mac/WSL
   .venv\Scripts\activate     # Windows
   ```

## 📖 How to Use Amplifier

### Basic Usage

Start Claude in the Amplifier directory to get all enhancements automatically:

```bash
cd amplifier
claude  # Everything is pre-configured and ready
```

### Using with Your Own Projects

Want Amplifier's power on your own code? Easy:

1. **Start Claude with both directories**:

   ```bash
   claude --add-dir /path/to/your/project
   ```

2. **Tell Claude where to work** (paste as first message):

   ```
   I'm working in /path/to/your/project which doesn't have Amplifier files.
   Please cd to that directory and work there.
   Do NOT update any issues or PRs in the Amplifier repo.
   ```

3. **Use Amplifier's agents on your code**:
   - "Use the zen-architect agent to design my application's caching layer"
   - "Deploy bug-hunter to find why my login system is failing"
   - "Have security-guardian review my API implementation for vulnerabilities"

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

> [!IMPORTANT] > **This is an experimental system. _We break things frequently_.**

- Not accepting contributions yet (but we plan to!)
- No stability guarantees
- Pin commits if you need consistency
- This is a learning resource, not production software
- **No support provided** - See [SUPPORT.md](SUPPORT.md)

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
