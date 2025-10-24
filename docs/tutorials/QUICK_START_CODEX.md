   # Follow Anthropic's installation guide
   codex --version
   ```

2. **Clone the project**:
   ```bash
   git clone <repository-url>
   cd amplifier-project
   ```

3. **Install dependencies**:
   ```bash
   make install
   ```

## First Session (2 minutes)

Start your first Codex session with Amplifier integration:

```bash
./amplify-codex.sh
```

**What you'll see:**
- ✅ Prerequisites check (Codex CLI, uv, virtual env)
- 📚 Session initialization (loads relevant memories)
- 🚀 Codex starts with MCP servers enabled
- 💡 Guidance box showing available tools and commands

**Try these commands:**

```bash
codex> initialize_session with prompt "Hello world project"
```

**Expected output:**
```
Loaded 3 memories from previous sessions:
- Memory 1: Basic project setup patterns
- Memory 2: Hello world implementations
- Memory 3: Testing approaches
```

```bash
codex> check_code_quality with file_paths ["README.md"]
```

**Expected output:**
```
Quality check results:
✅ Linting: Passed (ruff)
✅ Type checking: Passed (pyright)
✅ Tests: 15 passed, 0 failed
```

## Key Concepts (1 minute)

- **MCP Tools vs Hooks**: Codex uses MCP (Model Context Protocol) servers instead of Claude Code's native hooks. Tools are invoked via natural language or direct calls.

- **Profiles**: Choose your workflow:
  - `development`: All tools (memory, quality, transcripts)
  - `ci`: Quality checks only
  - `review`: Quality + transcript management

- **Memory System**: Automatically loads relevant context from previous sessions to maintain continuity.

## Common Commands (1 minute)

**Session Management:**
```bash
codex> initialize_session with prompt "Working on feature X"
codex> finalize_session with recent messages
codex> save_current_transcript with format "both"
```

**Quality Checks:**
```bash
codex> check_code_quality with file_paths ["src/file.py"]
codex> run_specific_checks with check_type "lint"
```

**Task Tracking (coming soon):**
```bash
codex> create_task with title "Implement auth" and description "Add user authentication"
codex> list_tasks
codex> complete_task with task_id "task_123"
```

**Web Research (coming soon):**
```bash
codex> search_web with query "Python async patterns" and num_results 5
codex> fetch_url with url "https://example.com/api-docs"