# Verify Python version
python --version
# Should show: Python 3.11.x or higher

# Verify uv installation
uv --version
# Should show version information

# Check for Codex CLI
codex --version
# Should show version information
```

### Step-by-Step Installation

1. **Clone the Amplifier Repository:**
```bash
git clone <your-amplifier-repo-url>
cd amplifier-project
```

2. **Install Dependencies:**
```bash
# Install all project dependencies
make install

# This runs: uv sync --dev
# Expected output: Successfully installed dependencies
```

3. **Verify Installation:**
```bash
# Run project checks
make check

# Expected output: All checks pass (lint, type, test)
# If any fail, run: uv run ruff check . --fix
```

### Configuration Walkthrough

Codex uses TOML configuration in `.codex/config.toml`. Let's set it up:

1. **Initialize Configuration:**
```bash
# Create config directory
mkdir -p .codex

# Codex will create a default config when first run
codex --config .codex/config.toml --init
```

2. **Review Default Configuration:**
```toml
# .codex/config.toml (key sections)
model = "claude-3-5-sonnet-20241022"
approval_policy = "on-request"

[mcp_servers.amplifier_session]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/session_manager/server.py"]
env = { AMPLIFIER_ROOT = "." }

[mcp_servers.amplifier_quality]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/quality_checker/server.py"]

[mcp_servers.amplifier_transcripts]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/transcript_saver/server.py"]

[mcp_servers.amplifier_tasks]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/task_tracker/server.py"]
env = { AMPLIFIER_ROOT = "." }

[mcp_servers.amplifier_web]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/web_research/server.py"]
env = { AMPLIFIER_ROOT = "." }

[profiles.development]
mcp_servers = ["amplifier_session", "amplifier_quality", "amplifier_transcripts", "amplifier_tasks", "amplifier_web"]
```

3. **Customize for Your Needs:**
```bash
# Edit config if needed
# nano .codex/config.toml

# Common customizations:
# - Change model if you have access to others
# - Adjust approval_policy to "auto" for faster workflow
# - Add custom MCP servers
```

### Verification Steps

1. **Test MCP Servers:**
```bash
# Test session manager
uv run python .codex/mcp_servers/session_manager/server.py --help

# Test quality checker
uv run python .codex/mcp_servers/quality_checker/server.py --help

# Expected: Help output for each server
```

2. **Test Wrapper Script:**
```bash
# Make executable
chmod +x amplify-codex.sh

# Test prerequisites check
./amplify-codex.sh --check-only

# Expected: "All prerequisites met" or specific error messages
```

3. **Quick Configuration Test:**
```bash
# Test Codex with config
codex --config .codex/config.toml --profile development --help

# Expected: Profile information and available options
```

**🎉 Setup Complete!** Your Codex integration is ready. If you encountered any errors, check the troubleshooting section at the end.

## Your First Session (5 minutes)

Now let's start your first Codex session with Amplifier integration.

### Starting a Session

**Option 1: Wrapper Script (Recommended)**
```bash
# Start with full automation
./amplify-codex.sh

# Expected output:
# ✅ Prerequisites check passed
# 🔄 Initializing session...
# 📝 Loaded 3 relevant memories
# 🚀 Starting Codex...
#
# [Codex session begins]
```

**Option 2: Manual Start**
```bash
# Initialize manually
uv run python .codex/tools/session_init.py --prompt "Learning Codex integration"

# Start Codex
codex --profile development
```

### Understanding the Interface

When Codex starts, you'll see:

```
Codex session started. Type 'help' for assistance.

Available MCP tools:
• initialize_session - Load context and memories
• check_code_quality - Run code quality checks
• save_current_transcript - Export session transcript
• create_task - Create development tasks
• search_web - Research topics online
• finalize_session - Save memories for next session

codex>
```

**Interface Elements:**
- **Command Prompt**: `codex>` - Where you type commands
- **Tool List**: Available MCP tools with descriptions
- **Status Indicators**: Memory loading, tool availability
- **Session Info**: Current working directory, active profile

### Using MCP Tools

Let's try some basic tools:

1. **Load Session Context:**
```bash
codex> initialize_session with prompt "Getting started with Codex"
```

**Expected Output:**
```json
{
  "memories": [
    {
      "content": "Previous session on project setup...",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ],
  "metadata": {
    "memoriesLoaded": 2,
    "source": "amplifier_memory"
  }
}
```

2. **Check Code Quality:**
```bash
codex> check_code_quality with file_paths ["README.md"]
```

**Expected Output:**
```json
{
  "passed": true,
  "output": "All checks passed\nLint: OK\nType check: OK",
  "issues": [],
  "metadata": {
    "tools_run": ["ruff", "pyright"],
    "execution_time": 1.2
  }
}
```

3. **Create a Task:**
```bash
codex> create_task with title "Complete Codex tutorial" and description "Finish the beginner guide"
```

**Expected Output:**
```json
{
  "task_id": "task_abc123",
  "task": {
    "title": "Complete Codex tutorial",
    "description": "Finish the beginner guide",
    "status": "pending",
    "created_at": "2024-01-01T10:30:00Z"
  }
}
```

### Ending a Session

1. **Save Your Work:**
```bash
codex> save_current_transcript with format "both"
```

**Expected Output:**
```json
{
  "exported_path": ".codex/transcripts/2024-01-01-10-00-AM__project__abc123/",
  "metadata": {
    "file_size": 5432,
    "event_count": 45
  }
}
```

2. **Exit Codex:**
```bash
codex> exit
# Or press Ctrl+D
```

**Wrapper Script Cleanup:**
```
Session ended. Running cleanup...
📝 Extracted 3 memories from session
💾 Transcript saved to .codex/transcripts/
✅ Cleanup complete
```

**🎯 First Session Complete!** You've successfully started, used tools, and ended a Codex session.

## Core Workflows (10 minutes)

Now let's explore the main workflows that make Codex with Amplifier powerful.

### Development Workflow with Memory System

**Goal**: Build features while learning from past sessions.

1. **Start with Context:**
```bash
./amplify-codex.sh
codex> initialize_session with prompt "Adding user authentication feature"
```

2. **Develop Iteratively:**
```bash
# Edit code
# Codex assists with suggestions

# Check quality after changes
codex> check_code_quality with file_paths ["src/auth.py", "tests/test_auth.py"]
```

3. **Save Progress:**
```bash
codex> save_current_transcript with format "standard"
```

4. **End and Learn:**
```bash
# Exit Codex
# Memories automatically extracted for next session
```

**Benefits:**
- Relevant context loaded automatically
- Quality checks catch issues early
- Progress preserved across sessions

### Quality Checking Workflow

**Goal**: Maintain code quality throughout development.

1. **After Code Changes:**
```bash
codex> check_code_quality with file_paths ["src/new_feature.py"]
```

2. **Run Specific Checks:**
```bash
# Only linting
codex> run_specific_checks with check_type "lint"

# Only tests
codex> run_specific_checks with check_type "test" and file_paths ["tests/"]
```

3. **Review Results:**
```json
{
  "passed": false,
  "output": "Lint: FAILED\n- Line 15: Unused import\nType check: PASSED\nTests: 8/10 passed",
  "issues": [
    {
      "type": "lint",
      "file": "src/new_feature.py",
      "line": 15,
      "message": "Unused import 'os'"
    }
  ]
}
```

4. **Fix and Re-check:**
```bash
# Fix the issue, then re-check
codex> check_code_quality with file_paths ["src/new_feature.py"]
```

### Task Management Workflow

**Goal**: Track development tasks within your coding session.

1. **Plan Tasks:**
```bash
codex> create_task with title "Implement login endpoint" and priority "high"
codex> create_task with title "Add password validation" and priority "medium"
codex> create_task with title "Write unit tests" and priority "medium"
```

2. **Work on Tasks:**
```bash
# Start working
codex> update_task with task_id "task_123" and updates {"status": "in_progress"}

# Complete when done
codex> complete_task with task_id "task_123"
```

3. **Track Progress:**
```bash
codex> list_tasks
```

**Expected Output:**
```json
{
  "tasks": [
    {
      "id": "task_123",
      "title": "Implement login endpoint",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "task_456",
      "title": "Add password validation",
      "status": "in_progress",
      "priority": "medium"
    }
  ],
  "count": 3
}
```

4. **Export for Documentation:**
```bash
codex> export_tasks with format "markdown"
```

### Web Research Workflow

**Goal**: Research solutions during development.

1. **Search for Information:**
```bash
codex> search_web with query "python oauth2 best practices 2024"
```

**Expected Output:**
```json
{
  "query": "python oauth2 best practices 2024",
  "results": [
    {
      "title": "OAuth2 Best Practices in Python",
      "url": "https://example.com/oauth2-guide",
      "snippet": "Learn modern OAuth2 implementation patterns..."
    }
  ]
}
```

2. **Fetch Detailed Content:**
```bash
codex> fetch_url with url "https://example.com/oauth2-guide" and extract_text true
```

3. **Summarize for Quick Reference:**
```bash
codex> summarize_content with content "Fetched article content..." and max_length 200
```

### Agent Spawning Workflow

**Goal**: Use specialized AI assistants for complex tasks.

1. **Identify Need:**
```bash
# For bug investigation
codex> spawn_agent with agent_name "bug-hunter" and task "Investigate memory leak in auth module"
```

2. **Agent Execution:**
```bash
# Codex executes: codex exec .codex/agents/bug-hunter.md --context="..."
# Agent works on the task
# Results integrated back
```

3. **Review Results:**
```bash
# Agent output appears in session
# Context bridge preserves conversation flow
```

**Available Agents:**
- `bug-hunter` - Debug and fix issues
- `zen-architect` - Design clean architecture
- `test-coverage` - Improve test coverage
- `security-guardian` - Security analysis

## Advanced Features (5 minutes)

Let's explore some advanced capabilities.

### Profiles and When to Use Them

**Development Profile (Default):**
```bash
codex --profile development
# All tools enabled for full workflow
```

**CI Profile:**
```bash
codex --profile ci
# Only quality checks for automated testing
```

**Review Profile:**
```bash
codex --profile review
# Quality + transcripts for code review
```

**When to Use Each:**
- **Development**: Interactive coding with all features
- **CI**: Automated quality gates in pipelines
- **Review**: Code review and documentation

### Backend Abstraction

Use the same API regardless of backend:

```python
from amplifier import get_backend

backend = get_backend()  # Returns CodexBackend or ClaudeCodeBackend

# Same methods work for both
result = backend.initialize_session("Working on feature")
result = backend.run_quality_checks(["file.py"])
result = backend.manage_tasks("create", title="New task")
```

### Transcript Management

**View Available Sessions:**
```bash
codex> list_available_sessions
```

**Export Specific Session:**
```bash
codex> save_current_transcript with format "extended"
```

**Convert Formats:**
```bash
# Convert between Codex and Claude Code formats
python tools/transcript_manager.py convert session_id --from codex --to claude
```

### Context Bridge for Agents

**Seamless Agent Integration:**
```bash
# Context automatically passed to agents
codex> spawn_agent_with_context "architect" "Design the API"

# Agent receives full conversation context
# Results integrated back into main session
```

**Benefits:**
- No manual context copying
- Agents understand full project context
- Results flow naturally in conversation

## Troubleshooting (3 minutes)

Let's cover common issues and solutions.

### Common Issues and Solutions

**"MCP server connection failed"**
```bash
# Check server status
uv run python .codex/mcp_servers/session_manager/server.py

# Verify config
cat .codex/config.toml | grep mcp_servers

# Check logs
tail -f .codex/logs/session_manager.log
```

**"Memory system not working"**
```bash
# Check environment variable
echo $MEMORY_SYSTEM_ENABLED

# Verify memory files exist
ls .data/memories/

# Test memory loading
uv run python .codex/tools/session_init.py --verbose
```

**"Quality checks failing"**
```bash
# Test tools individually
make lint
make type
make test

# Check Makefile exists
ls Makefile

# Verify virtual environment
which python  # Should point to .venv/bin/python
```

**"Codex command not found"**
```bash
# Check PATH
which codex

# Add to PATH if needed
export PATH="$HOME/.codex/bin:$PATH"

# Reinstall Codex
# Follow: https://docs.anthropic.com/codex/installation
```

### Where to Find Logs

**Server Logs:**
```bash
# All server logs
ls .codex/logs/
tail -f .codex/logs/*.log
```

**Session Logs:**
```bash
# Initialization logs
cat .codex/logs/session_init.log

# Cleanup logs
cat .codex/logs/session_cleanup.log
```

**Codex Global Logs:**
```bash
# System logs
tail -f ~/.codex/logs/codex.log
```

### How to Get Help

**Documentation Resources:**
- [Quick Start Tutorial](./QUICK_START_CODEX.md) - 5-minute overview
- [Workflow Diagrams](./WORKFLOW_DIAGRAMS.md) - Visual guides
- [Feature Parity Matrix](./FEATURE_PARITY_MATRIX.md) - Detailed comparisons
- [Troubleshooting Tree](./TROUBLESHOOTING_TREE.md) - Decision-tree guide

**Debug Mode:**
```bash
# Enable verbose logging
export CODEX_DEBUG=true
./amplify-codex.sh

# Test servers individually
uv run python .codex/mcp_servers/session_manager/server.py --debug