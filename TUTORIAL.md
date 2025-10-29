### Summary
# When to Use Codex Commands vs Python Scripts
Based on the tutorial documentation, here's a clear guide on when to use direct Codex commands versus Python scripts for Codex integration:

## 🎯 Direct Codex Commands (Interactive Sessions)

**Use direct Codex commands when:**

### 1. **Working Interactively in a Codex Session**
You're inside an active Codex CLI session and want to use MCP tools:

```bash
# Start Codex session first
./amplify-codex.sh

# Then use MCP tools interactively
codex> initialize_session with prompt "Working on authentication"
codex> check_code_quality with file_paths ["src/auth.py"]
codex> create_task with title "Fix login bug"
codex> search_web with query "python oauth2 best practices"
```

**Why:** These commands leverage Codex's natural language interface and provide immediate feedback within your development session.

### 2. **Manual Development Workflow**
You want the full interactive experience with:
- Real-time AI assistance
- Natural language tool invocation
- Immediate visual feedback
- Conversational context

**Example workflow:**
```bash
./amplify-codex.sh                    # Start session
codex> initialize_session             # Load context
# ... work on code ...
codex> check_code_quality             # Verify changes
codex> save_current_transcript        # Save work
codex> exit                           # End session
```

### 3. **Complex Multi-Agent Orchestration**
For tasks requiring multiple specialized agents working together:

```bash
./amplify-codex.sh                    # Start session

# Primary method: Context file (works with all Codex versions)
codex exec --context-file=.codex/prompts/ultrathink-task.md "Refactor authentication system to use JWT tokens"

# Alternative: Interactive TUI (if prompt registry supported)
codex> /prompts:                      # Browse available prompts
codex> [Select ultrathink-task]       # Choose from menu

# Alternative: Natural language delegation
codex> Please analyze the codebase architecture and suggest improvements using ultrathink-task
```

**What is ultrathink-task?**
A specialized custom prompt that orchestrates multiple agents for complex tasks:
- **Triage Specialist**: Analyzes the task and creates a structured breakdown
- **Analysis Expert**: Deep dives into specific aspects
- **Synthesis Master**: Combines findings into actionable recommendations
- **Bug Hunter / Architect / Tester**: Specialized agents as needed

**When to use ultrathink-task:**
- Complex refactoring requiring multiple perspectives
- Architecture reviews needing comprehensive analysis
- Bug investigations spanning multiple components
- Feature planning requiring detailed exploration
- Quality improvements needing systematic approach

**Key features:**
- Maintains task context across agent transitions
- Synthesizes findings from multiple perspectives
- Produces comprehensive documentation
- Tracks progress and intermediate results
- Generates actionable next steps

**Example scenarios:**
```bash
# Architecture review (using --context-file, works reliably)
codex exec --context-file=.codex/prompts/ultrathink-task.md "Review the authentication system architecture for security and maintainability"

# Complex refactoring
codex exec --context-file=.codex/prompts/ultrathink-task.md "Refactor the database layer to support multiple backends"

# Bug investigation
codex exec --context-file=.codex/prompts/ultrathink-task.md "Investigate intermittent connection failures in production"

# Feature planning
codex exec --context-file=.codex/prompts/ultrathink-task.md "Design a new caching layer for the API"
```

**Note**: If your Codex version supports `--prompt` and named arguments, you can use:
```bash
codex exec --prompt ultrathink-task --task_description "<your task>"
```
However, `--context-file` is the most portable approach.

**Comparison with direct agent invocation:**
- **Direct agents**: Quick, focused, single perspective
- **ultrathink-task**: Comprehensive, multi-perspective, structured approach

For more details on custom prompts, see `.codex/prompts/README.md` and `.codex/README.md`.

---

## 🐍 Python Scripts (Automation & Integration)

**Use Python scripts when:**

### 1. **Automating Codex Operations**
You need to integrate Codex functionality into scripts, CI/CD pipelines, or other tools:

```python
from amplifier import get_backend

# Get Codex backend programmatically
backend = get_backend()  # Uses AMPLIFIER_BACKEND=codex

# Run operations without interactive session
result = backend.initialize_session("Automated build")
result = backend.run_quality_checks(["src/"])
```

**Why:** Scripts provide programmatic access without requiring an interactive Codex session.

### 2. **CI/CD Integration**
Running quality checks or other operations in automated pipelines:

```python
# In your CI script
from amplifier.core.backend import CodexBackend

backend = CodexBackend()
result = backend.run_quality_checks(["src/", "tests/"])

if not result.get("passed"):
    sys.exit(1)  # Fail the build
```

### 3. **Custom Tooling & Workflows**
Building custom tools that leverage Codex capabilities:

```python
# Custom deployment script
from amplifier import spawn_agent

# Use Codex agent for pre-deployment checks
result = spawn_agent(
    agent_name="security-guardian",
    task="Review deployment configuration for security issues"
)
```

### 4. **Batch Processing**
Processing multiple items without manual intervention:

```python
# Batch quality checks
from amplifier.core.backend import CodexBackend

backend = CodexBackend()
files = ["file1.py", "file2.py", "file3.py"]

for file in files:
    result = backend.run_quality_checks([file])
    print(f"{file}: {'✅' if result['passed'] else '❌'}")
```

### 5. **Using the MCP Client Directly**
When you need low-level control over MCP tool invocation:

```python
from codex_mcp_client import CodexMCPClient

client = CodexMCPClient(profile="development")

# Call MCP tools directly
result = client.call_tool(
    server="amplifier_quality",
    tool_name="check_code_quality",
    file_paths=["src/auth.py"]
)
```

**Why:** Direct MCP client access gives you fine-grained control for specialized use cases.

---

## 📊 Quick Decision Matrix

| Scenario | Use | Example |
|----------|-----|---------|
| **Interactive development** | Codex commands | `codex> check_code_quality` |
| **AI-assisted coding** | Codex commands | `codex> initialize_session` |
| **CI/CD pipeline** | Python scripts | `backend.run_quality_checks()` |
| **Automation scripts** | Python scripts | `spawn_agent("bug-hunter", task)` |
| **Batch processing** | Python scripts | Loop with `backend.run_quality_checks()` |
| **Custom tooling** | Python scripts | `CodexMCPClient().call_tool()` |
| **Manual testing** | Codex commands | `codex> search_web with query` |
| **Integration with other tools** | Python scripts | Import `amplifier` modules |

---

## 🔄 Hybrid Approach

You can also combine both approaches:

### Example: Wrapper Script Pattern
The `amplify-codex.sh` wrapper uses Python scripts for setup/cleanup but launches Codex for interactive work:

```bash
#!/bin/bash
# 1. Python script for initialization
uv run python .codex/tools/session_init.py --prompt "$1"

# 2. Start interactive Codex session
codex --profile development

# 3. Python script for cleanup
uv run python .codex/tools/session_cleanup.py
```

**Why:** This gives you the best of both worlds—automated setup/teardown with interactive development.

---

## 💡 Key Takeaways

1. **Codex Commands** = Interactive, conversational, real-time feedback
2. **Python Scripts** = Automated, programmatic, integration-friendly
3. **Wrapper Scripts** = Combine both for complete workflows
4. **Backend Abstraction** = Write once, works with both Codex and Claude Code

Choose based on your context:
- **Human in the loop?** → Codex commands
- **Automated process?** → Python scripts
- **Building tools?** → Python scripts
- **Daily development?** → Codex commands (via wrapper)

---

## 📚 Related Documentation

- **[Quick Start Tutorial](docs/tutorials/QUICK_START_CODEX.md)** - Interactive Codex usage
- **[Beginner Guide](docs/tutorials/BEGINNER_GUIDE_CODEX.md)** - Complete workflows
- **[Backend Abstraction](amplifier/core/README.md)** - Programmatic usage
- **[Codex Integration](docs/CODEX_INTEGRATION.md)** - Complete reference