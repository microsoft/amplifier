# Install Codex CLI (follow Anthropic's instructions)
# Visit: https://docs.anthropic.com/codex/installation

# Verify installation
codex --version
# Expected output: codex 0.1.x
```

### Step 2: Clone and Setup Project

```bash
# Clone the Amplifier project
git clone <your-repository-url>
cd amplifier-project

# Install dependencies using uv
make install

# Verify Python version
python --version
# Expected: Python 3.11.x or higher
```

### Step 3: Configure Codex

```bash
# Initialize Codex configuration
codex --config .codex/config.toml --init

# The config file should be created at .codex/config.toml
ls .codex/config.toml
```

**Exercise 1**: Open `.codex/config.toml` and verify it contains basic configuration sections like `[mcp_servers]` and `[profiles]`.

### Step 4: Verify Setup

```bash
# Run project checks
make check

# Test Codex configuration
codex --profile development --help

# Test MCP servers individually
uv run python .codex/mcp_servers/session_manager/server.py --help
uv run python .codex/mcp_servers/quality_checker/server.py --help
```

**Expected Output**:
```
# All checks passed
Lint: OK
Type check: OK
Tests: 15 passed
```

**Exercise 2**: If any checks fail, note the error messages. We'll address common issues in the troubleshooting section.

## Your First Session (5 minutes)

### Starting a Session

The easiest way to start Codex with Amplifier is using the wrapper script:

```bash
# Make the wrapper executable (first time only)
chmod +x amplify-codex.sh

# Start your first session
./amplify-codex.sh
```

**What You'll See**:
```
🔍 Checking prerequisites...
✅ Codex CLI found
✅ uv package manager found
✅ Virtual environment activated
✅ Project dependencies installed

🧠 Initializing session...
📚 Loaded 3 relevant memories from previous work

🚀 Starting Codex with development profile...
MCP Servers: session_manager, quality_checker, task_tracker, web_research

Available MCP Tools:
• initialize_session - Load context at session start
• check_code_quality - Run make check on files
• create_task - Add new development task
• search_web - Research topics online
• spawn_agent - Execute specialized AI agents

Type your message or use MCP tools...
codex>
```

### Understanding the Interface

The Codex interface shows:
- **Status messages**: What Amplifier is doing (loading memories, starting servers)
- **Available tools**: MCP tools you can invoke
- **Prompt**: `codex>` ready for your input

### Using MCP Tools

Try your first MCP tool call:

```bash
codex> initialize_session with prompt "Setting up my first Codex session"
```

**Expected Response**:
```json
{
  "memories": [
    {
      "content": "Previous session covered basic setup...",
      "timestamp": "2024-01-01T10:00:00Z",
      "source": "amplifier_memory"
    }
  ],
  "metadata": {
    "memoriesLoaded": 3,
    "source": "amplifier_memory"
  }
}
```

**Exercise 3**: Try the quality checker tool on an existing file:

```bash
codex> check_code_quality with file_paths ["README.md"]
```

### Ending a Session

```bash
# Exit Codex
codex> exit
# Or press Ctrl+D

# The wrapper will automatically:
# ✅ Extract memories from your conversation
# ✅ Export transcript to .codex/transcripts/
# ✅ Display session summary
```

**Session Summary Example**:
```
🎯 Session Complete!

📊 Summary:
• Duration: 15 minutes
• Messages: 12
• Tools Used: 2
• Memories Extracted: 3

📁 Transcript saved to: .codex/transcripts/2024-01-01-10-00-AM__project__abc123/
```

## Core Workflows (10 minutes)

Now that you know the basics, let's explore the main development workflows.

### Development Workflow with Memory System

**Scenario**: You're working on a new feature and want to leverage past work.

```bash
# Start session with context
./amplify-codex.sh

# Load relevant memories
codex> initialize_session with prompt "Working on user authentication feature"

# Work on your code...
# Edit files, ask questions, etc.

# Run quality checks after changes
codex> check_code_quality with file_paths ["src/auth.py", "tests/test_auth.py"]

# Save progress
codex> save_current_transcript with format "standard"

# Exit (memories automatically extracted)
```

**Exercise 4**: Modify a file (add a comment), run quality checks, and observe the results.

### Quality Checking Workflow

**When to use**: After editing code to catch issues early.

```bash
# Check specific files
codex> check_code_quality with file_paths ["src/new_feature.py"]

# Check entire directory
codex> check_code_quality with file_paths ["src/"]

# Run specific checks only
codex> run_specific_checks with check_type "lint"
codex> run_specific_checks with check_type "type"
codex> run_specific_checks with check_type "test"
```

**Expected Output**:
```json
{
  "passed": true,
  "output": "All checks passed\nLint: OK\nType check: OK\nTests: 15 passed",
  "issues": [],
  "metadata": {
    "tools_run": ["ruff", "pyright", "pytest"],
    "execution_time": 2.3
  }
}
```

### Task Management Workflow

**New Feature**: Equivalent to Claude Code's TodoWrite.

```bash
# Create a task
codex> create_task with title "Implement password reset" and description "Add forgot password functionality to auth module"

# List current tasks
codex> list_tasks

# Update task progress
codex> update_task with task_id "task_001" and updates {"status": "in_progress"}

# Mark task complete
codex> complete_task with task_id "task_001"

# Export tasks
codex> export_tasks with format "markdown"
```

**Exercise 5**: Create a task for "Add error handling to API endpoints", then mark it complete.

### Web Research Workflow

**New Feature**: Equivalent to Claude Code's WebFetch.

```bash
# Search for information
codex> search_web with query "Python async best practices" and num_results 5

# Fetch specific content
codex> fetch_url with url "https://docs.python.org/3/library/asyncio.html"

# Summarize content
codex> summarize_content with content "Long article text..." and max_length 500
```

**Expected Output**:
```json
{
  "results": [
    {
      "title": "Async Best Practices",
      "url": "https://example.com/async-guide",
      "snippet": "Use asyncio.gather() for concurrent operations..."
    }
  ],
  "metadata": {
    "query": "Python async best practices",
    "results_count": 5,
    "search_engine": "duckduckgo"
  }
}
```

### Agent Spawning Workflow

**Scenario**: You need specialized help with a complex task.

```bash
# Spawn a bug hunter agent
codex> spawn_agent with agent_name "bug-hunter" and task "Find and fix the memory leak in the cache module"

# The agent will:
# 1. Analyze the codebase
# 2. Identify potential issues
# 3. Suggest fixes
# 4. Provide implementation

# Results are integrated back into your session
```

**Available Agents**:
- `bug-hunter`: Find and fix bugs
- `test-coverage`: Analyze test coverage
- `security-guardian`: Security vulnerability checks
- `zen-architect`: Architecture design
- `modular-builder`: Code implementation

**Exercise 6**: Try spawning the `analysis-engine` agent to analyze your codebase structure.

## Advanced Features (5 minutes)

### Profiles and When to Use Them

Codex uses profiles to enable different MCP server combinations:

```bash
# Development profile (all features)
./amplify-codex.sh --profile development

# CI profile (quality checks only)
./amplify-codex.sh --profile ci

# Review profile (quality + transcripts)
./amplify-codex.sh --profile review
```

**Profile Guide**:
- **development**: Full workflow with memory, quality, tasks, research
- **ci**: Automated quality assurance for CI/CD
- **review**: Code review with quality checks and documentation

### Backend Abstraction

Amplifier provides a unified API across backends:

```python
from amplifier import get_backend

# Automatically uses Codex backend
backend = get_backend()

# Same API regardless of backend
result = backend.initialize_session("Working on feature")
result = backend.run_quality_checks(["file.py"])
```

### Transcript Management

```bash
# Export current session
codex> save_current_transcript with format "both"

# List available sessions
codex> list_available_sessions

# Convert formats
codex> convert_transcript_format with session_id "abc123" to "claude"
```

**Transcript Formats**:
- **standard**: Conversation-focused markdown
- **extended**: Detailed with all events and metadata
- **compact**: Space-efficient for storage

### Context Bridge for Agents

**New Feature**: Pass conversation context to agents.

```bash
# The wrapper automatically handles context serialization
# When you spawn an agent, it receives:
# - Recent conversation messages
# - Current task context
# - Relevant file information
# - Session metadata
```

## Troubleshooting (3 minutes)

### Common Issues and Solutions

**Issue**: "Codex CLI not found"
```bash
# Solution: Install Codex CLI
# Visit: https://docs.anthropic.com/codex/installation
codex --version  # Verify
```

**Issue**: "MCP server connection failed"
```bash
# Check server logs
tail -f .codex/logs/session_manager.log

# Test server directly
uv run python .codex/mcp_servers/session_manager/server.py
```

**Issue**: "Quality checks failing"
```bash
# Verify Makefile exists
ls Makefile

# Run checks manually
make check

# Check tool installation
uv pip list | grep ruff
```

**Issue**: "Memory system not working"
```bash
# Check environment variable
echo $MEMORY_SYSTEM_ENABLED

# Verify memory files exist
ls .data/memories/
```

### Where to Find Logs

```bash
# MCP server logs
.codex/logs/
├── session_manager.log
├── quality_checker.log
├── task_tracker.log
└── web_research.log

# Session logs
.codex/logs/
├── session_init.log
└── session_cleanup.log

# Wrapper script logs
amplify-codex.log
```

### How to Get Help

1. **Check the logs**: Most issues are logged with detailed error messages
2. **Run diagnostics**: `./amplify-codex.sh --check-only`
3. **Review documentation**: 
   - `docs/CODEX_INTEGRATION.md` - Main integration guide
   - `docs/tutorials/TROUBLESHOOTING_TREE.md` - Decision tree guide
   - `.codex/README.md` - Codex-specific docs
4. **Community support**: Create an issue in the project repository

**Quick Diagnostic Commands**:
```bash
# Full system check
./amplify-codex.sh --check-only

# Test individual components
codex --version
uv --version
python --version
make check
```

## Congratulations!

You've completed the beginner guide to Codex integration! You now know how to:

- ✅ Set up and configure Codex with Amplifier
- ✅ Start productive development sessions
- ✅ Use MCP tools for common workflows
- ✅ Manage tasks and conduct web research
- ✅ Spawn agents for specialized work
- ✅ Troubleshoot common issues

### Next Steps

- **Quick Start**: Try the 5-minute guide in `QUICK_START_CODEX.md`
- **Feature Comparison**: See how Codex compares to Claude Code in `FEATURE_PARITY_MATRIX.md`
- **Workflow Diagrams**: Visualize the architecture in `WORKFLOW_DIAGRAMS.md`
- **Advanced Topics**: Explore the main integration guide in `../CODEX_INTEGRATION.md`

### Quick Reference

```bash
# Start development session
./amplify-codex.sh

# Start with specific profile
./amplify-codex.sh --profile ci

# Check system status
./amplify-codex.sh --check-only

# Get help
./amplify-codex.sh --help