   # Follow Anthropic's installation guide
   # https://docs.anthropic.com/codex/installation
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

1. **Start the wrapper script**:
   ```bash
   ./amplify-codex.sh
   ```

   **What you'll see**:
   ```
   🔧 Amplifier Codex Integration
   ✅ Prerequisites verified
   📚 Loading session context...
   🚀 Starting Codex with development profile

   Available MCP Tools:
   • initialize_session - Load memories
   • check_code_quality - Run quality checks
   • save_current_transcript - Export session
   • create_task - Manage tasks
   • search_web - Web research

   Type your prompt or use MCP tools...
   ```

2. **Try initializing a session**:
   ```bash
   codex> initialize_session with prompt "Hello world"
   ```

   **Expected output**:
   ```
   Loaded 3 relevant memories from previous sessions.
   Session context ready for "Hello world" development.
   ```

3. **Try a quality check**:
   ```bash
   codex> check_code_quality with file_paths ["README.md"]
   ```

   **Expected output**:
   ```
   Quality check passed ✅
   • Lint: OK (ruff)
   • Type check: OK (pyright)
   • Tests: 15 passed (pytest)
   Execution time: 2.3s
   ```

## Key Concepts (1 minute)

- **MCP Tools vs Hooks**: Codex uses MCP (Model Context Protocol) servers instead of Claude Code's native hooks. Tools are invoked via natural language or direct calls.

- **Profiles**: Choose the right tool set:
  - `development`: All tools (session, quality, transcripts, tasks, web)
  - `ci`: Quality checks only
  - `review`: Quality + transcripts

- **Memory System**: Automatically loads relevant context from past sessions to maintain continuity.

## Common Commands (1 minute)

**Session Management**:
```bash
codex> initialize_session with prompt "Working on feature"
codex> finalize_session with recent messages
codex> save_current_transcript with format "both"
```

**Quality Checks**:
```bash
codex> check_code_quality with file_paths ["src/file.py"]
codex> run_specific_checks with check_type "lint"
```

**Task Tracking**:
```bash
codex> create_task with title "Fix bug" and description "Login issue"
codex> list_tasks with filter_status "pending"
codex> complete_task with task_id "task_123"
```

**Web Research**:
```bash
codex> search_web with query "python async patterns" and num_results 5
codex> fetch_url with url "https://example.com/guide" and extract_text true