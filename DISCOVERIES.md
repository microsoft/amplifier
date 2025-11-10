# DISCOVERIES.md

This file documents non-obvious problems, solutions, and patterns discovered during development. Make sure these are regularly reviewed and updated, removing outdated entries or those replaced by better practices or code or tools, updating those where the best practice has evolved.

## Hybrid Packaging @Mention Resolution Requires Parent Fallback (2025-11-10)

### Issue

Collection @mentions like `@toolkit:docs/TOOLKIT_GUIDE.md` were not loading into agent context. Agent system instructions referenced these files but they weren't being injected into the LLM request.

Additionally, cross-references WITHIN loaded toolkit docs used incorrect paths (`toolkit/METACOGNITIVE_RECIPES.md`, `toolkit/examples/`) that didn't exist from any working directory.

### Root Cause

**Two separate but related issues:**

**Issue 1: MentionResolver couldn't find collection resources**

Collections installed via pip/uv create nested package structure:
```
~/.amplifier/collections/amplifier-collection-toolkit/
  docs/                    <-- Resources at ROOT
  agents/
  scenario-tools/

  amplifier_collection_toolkit/    <-- Package subdir
    __init__.py
    pyproject.toml         <-- Metadata here (why resolver returns this path)
```

CollectionResolver returns package subdir (for metadata reading), but resources are at collection ROOT. MentionResolver constructed `collection_path / "docs/FILE.md"` which pointed to non-existent package subdirectory.

**Issue 2: Toolkit docs had incorrect internal cross-references**

- Used `toolkit/` prefix that doesn't exist as directory
- Used `examples/` instead of `scenario-tools/` for tool directory
- Used `tutorial_analyzer` (underscore) instead of `tutorial-analyzer` (hyphen) for directory paths

### Solution

**Fix 1: Add hybrid packaging fallback to MentionResolver**

```python
# Try at collection path first (package subdirectory)
if resource_path.exists() and resource_path.is_file():
    return resource_path.resolve()

# Hybrid packaging fallback: try parent directory
if (collection_path / "pyproject.toml").exists():
    parent_resource_path = collection_path.parent / path
    if parent_resource_path.exists() and parent_resource_path.is_file():
        return parent_resource_path.resolve()
```

Mirrors `discovery.py:66-75` pattern for resource discovery.

**Fix 2: Correct all cross-reference paths in toolkit docs**

Global replacements across 7 doc files:
- `toolkit/examples/` → `scenario-tools/`
- `toolkit/DOCFILE.md` → `DOCFILE.md` (same directory)
- `toolkit/templates/` → `templates/`
- `tutorial_analyzer/` → `tutorial-analyzer/` (for directory paths)
- Preserved `src/tutorial_analyzer/` (Python package name, correct with underscore)

### Key Learnings

1. **Hybrid packaging creates dual path perspectives**: Package subdir has metadata, collection root has resources
2. **CollectionResolver vs MentionResolver serve different purposes**: Collection finds metadata, Mention finds resources
3. **Parent fallback pattern is reusable**: Same pattern in both discovery.py and resolver.py
4. **Cross-references must work from collection root**: Both dev repo and installed collection share same structure
5. **Directory names vs Python package names**: tutorial-analyzer (dir) vs tutorial_analyzer (package)
6. **Documentation references are runtime-critical**: When loaded as context, AI verifies paths work

### Prevention

- **When creating collections**: Test @mention loading from installed collection, not just dev repo
- **Use collection-root-relative paths**: Work from both dev and installed contexts
- **Mirror existing patterns**: When similar functionality exists (like discovery.py), reuse the pattern
- **Separate directory paths from package names**: Hyphens in paths, underscores in Python packages
- **Test with subagent delegation**: Issues may only manifest when docs loaded into subagent context

### Verification

```bash
# Test @mention resolution works
python3 -c "
from amplifier_app_cli.lib.mention_loading import MentionResolver
resolver = MentionResolver()
result = resolver.resolve('@toolkit:docs/TOOLKIT_GUIDE.md')
print(f'Resolved: {result}')
"

# Test agent loading with @mentions
from amplifier_profiles import AgentLoader
agent = loader.load_agent('tool-builder')
print(f'Instruction length: {len(agent.system.instruction)} chars')  # Should be ~270KB
```

**Files changed:**
- `amplifier-app-cli/amplifier_app_cli/lib/mention_loading/resolver.py:77-141`
- `amplifier-collection-toolkit/docs/*.md` (7 files, 49 path corrections)

## Context Compaction: Orphaned Tool Results with Multiple Tool Calls (2025-11-09)

### Issue

Amplifier sessions would fail with Anthropic API error when context compaction occurred during conversations with multiple tool calls:

```
Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error',
'message': 'messages.0.content.0: unexpected `tool_use_id` found in `tool_result` blocks:
toolu_01XQiWirRkAarnHRXo8iDshV. Each `tool_result` block must have a corresponding `tool_use`
block in the previous message.'}}
```

Session transcripts showed orphaned tool results appearing right after system messages, with no preceding assistant message containing the tool_use blocks.

### Root Cause

The context compaction logic in both `amplifier-module-context-simple` and `amplifier-module-context-persistent` had a critical flaw when handling assistant messages with multiple tool_calls.

**The Scenario:**
```
Message N: assistant with 3 tool_calls
Message N+1: tool result 1
Message N+2: tool result 2  <- If compaction keeps this...
Message N+3: tool result 3
```

**The Bug:**

When preserving tool results during compaction, the code only checked the **immediate previous message** (i-1):

```python
# BUGGY CODE
elif msg.get("role") == "tool" and i > 0:
    prev_msg = self.messages[i - 1]  # Only checks i-1!
    if prev_msg.get("role") == "assistant" and prev_msg.get("tool_calls"):
        expanded.add(i - 1)
```

If `keep_indices` contained message N+2 (tool result 2), the code would:
1. Check message N+1 (tool result 1) - NOT an assistant with tool_calls
2. Fail to add the assistant at message N to the preserved set
3. Result: Keep tool results N+1, N+2, N+3 but DROP message N
4. API error: Tool results without matching tool_use blocks

This commonly occurred when the "keep last 10 messages" window included some but not all tool results from a multi-tool assistant message that fell outside the window.

### Solution

Fixed both context modules to **walk backwards** through consecutive tool messages to find the originating assistant:

```python
# FIXED CODE
elif msg.get("role") == "tool":
    # Find the assistant message with tool_calls that this result belongs to
    for j in range(i - 1, -1, -1):
        check_msg = self.messages[j]
        if check_msg.get("role") == "assistant" and check_msg.get("tool_calls"):
            expanded.add(j)
            logger.debug(
                f"Preserving tool group: message {j} (assistant with tool_calls) "
                f"includes tool result at {i}"
            )
            break
        if check_msg.get("role") != "tool":
            # Hit a non-tool message before finding the assistant
            logger.warning(
                f"Tool result at {i} has no matching assistant with tool_calls "
                f"(found {check_msg.get('role')} at {j} instead)"
            )
            break
```

**Files changed:**
- `amplifier-module-context-simple/amplifier_module_context_simple/__init__.py:172-192`
- `amplifier-module-context-persistent/amplifier_module_context_persistent/__init__.py:192-217`
- Both module READMEs updated to document the fix

**Tests:**
- Existing regression test `test_compact_with_multiple_tool_calls_in_one_message` now passes
- All 5 tool pair compaction tests pass

### Key Learnings

1. **Tool pairs are message groups, not pairs**: An assistant with N tool_calls creates 1+N messages that must be preserved as an atomic unit
2. **Adjacent-only checks fail**: Checking only the immediate previous message doesn't work when multiple tool results follow one assistant
3. **Walk backwards through tool results**: Must traverse backwards through consecutive tool messages to find the originating assistant
4. **Test regression scenarios**: The existing test suite already had a test for this exact scenario, proving the importance of comprehensive testing
5. **Both directions matter**: Compaction logic must handle both forward (assistant → results) and backward (result → assistant) preservation

### Prevention

- When implementing message sequence preservation, consider groups not just pairs
- Walk backwards/forwards through message sequences, don't assume adjacency
- Test with realistic scenarios (multiple tool calls in one message is common in practice)
- Add logging to help diagnose message sequence issues during compaction
- Verify test suite covers edge cases before they manifest as bugs in production

## DevContainer Setup: Using Official Features Instead of Custom Scripts (2025-10-22)

### Issue

Claude CLI was not reliably available in DevContainers, and there was no visibility into what tools were installed during container creation.

### Root Cause

1. **Custom installation approach**: Previously attempted to install Claude CLI via npm in post-create script (was commented out, indicating unreliability)
2. **Broken pipx feature URL**: Used `devcontainers-contrib` which was incorrect
3. **No logging**: Post-create script had no output to help diagnose issues
4. **No status reporting**: Users couldn't easily see what tools were available

### Solution

Switched to declarative DevContainer features instead of custom installation scripts:

**devcontainer.json changes:**
```json
// Fixed broken pipx feature URL
"ghcr.io/devcontainers-extra/features/pipx-package:1": { ... }

// Added official Claude Code feature
"ghcr.io/anthropics/devcontainer-features/claude-code:1": {},

// Added VSCode extension
"extensions": ["anthropic.claude-code", ...]

// Named container for easier identification
"runArgs": ["--name=amplifier_devcontainer"]
```

**post-create.sh improvements:**
```bash
# Added logging to persistent file for troubleshooting
LOG_FILE="/tmp/devcontainer-post-create.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Added development environment status report
echo "📋 Development Environment Ready:"
echo "  • Python: $(python3 --version 2>&1 | cut -d' ' -f2)"
echo "  • Claude CLI: $(claude --version 2>&1 || echo 'NOT INSTALLED')"
# ... other tools
```

### Key Learnings

1. **Use official DevContainer features over custom scripts**: Features are tested, maintained, and more reliable than custom npm installs
2. **Declarative > imperative**: Define what you need in devcontainer.json rather than scripting installations
3. **Add logging for troubleshooting**: Persistent logs help diagnose container build issues
4. **Provide status reporting**: Show users what tools are available after container creation
5. **Test with fresh containers**: Only way to verify DevContainer configuration works

### Prevention

- Prefer official DevContainer features from `ghcr.io/anthropics/`, `ghcr.io/devcontainers/`, etc.
- Add logging (`tee` to a log file) in post-create scripts for troubleshooting
- Include tool version reporting to confirm installations
- Use named containers (`runArgs`) for easier identification in Docker Desktop
- Test DevContainer changes by rebuilding containers from scratch

## pnpm Global Bin Directory Not Configured (2025-10-23)

### Issue

`make install` fails with `ERR_PNPM_NO_GLOBAL_BIN_DIR` error when trying to install global npm packages via pnpm in fresh DevContainer builds.

### Root Cause

Two issues combined to cause the failure:

1. **Missing SHELL environment variable**: During DevContainer post-create script execution, the `SHELL` environment variable is not set
2. **pnpm setup requires SHELL**: The `pnpm setup` command fails with `ERR_PNPM_UNKNOWN_SHELL` when `SHELL` is not set
3. **Silent failure**: The error was hidden by `|| true` in the script, allowing the script to continue and report success even though pnpm wasn't configured

From the post-create log:
```
🔧  Setting up pnpm global bin directory...
 ERR_PNPM_UNKNOWN_SHELL  Could not infer shell type.
Set the SHELL environment variable to your active shell.
    ✅ pnpm configured  # <-- False success!
```

### Solution

Fixed post-create script to explicitly set SHELL before running pnpm setup:

**post-create.sh addition:**
```bash
echo "🔧  Setting up pnpm global bin directory..."
# Ensure SHELL is set for pnpm setup
export SHELL="${SHELL:-/bin/bash}"
# Configure pnpm to use a global bin directory
pnpm setup 2>&1 | grep -v "^$" || true
# Export for current session (will also be in ~/.bashrc for future sessions)
export PNPM_HOME="/home/vscode/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"
echo "    ✅ pnpm configured"
```

This ensures:
1. SHELL is explicitly set before pnpm setup runs
2. pnpm's global bin directory is configured on first container build
3. The configuration is added to `~/.bashrc` for all future sessions
4. The environment variables are set for the post-create script itself

### Key Learnings

1. **SHELL not set in post-create context** - DevContainer post-create scripts run in an environment where SHELL may not be set
2. **pnpm requires SHELL** - Unlike npm, pnpm needs to know the shell type to modify the correct config file
3. **Silent failures are dangerous** - Using `|| true` hid the actual error; consider logging errors even when continuing
4. **Check the logs** - The `/tmp/devcontainer-post-create.log` revealed the actual error that was hidden from the console

### Prevention

- Always set SHELL explicitly in post-create scripts before running shell-dependent commands
- Check post-create logs (`/tmp/devcontainer-post-create.log`) after rebuilding containers
- Consider conditional error handling instead of blanket `|| true` to catch real failures
- Test `make install` as part of DevContainer validation

## OneDrive/Cloud Sync File I/O Errors (2025-01-21)

### Issue

Knowledge synthesis and other file operations were experiencing intermittent I/O errors (OSError errno 5) in WSL2 environment. The errors appeared random but were actually caused by OneDrive cloud sync delays.

### Root Cause

The `~/amplifier` directory was symlinked to a OneDrive folder on Windows (C:\ drive). When files weren't downloaded locally ("cloud-only" files), file operations would fail with I/O errors while OneDrive fetched them from the cloud. This affects:

1. **WSL2 + OneDrive**: Symlinked directories from Windows OneDrive folders
2. **Other cloud sync services**: Dropbox, Google Drive, iCloud Drive can cause similar issues
3. **Network drives**: Similar delays can occur with network-mounted filesystems

### Solution

Two-part solution implemented:

1. **Immediate fix**: Added retry logic with exponential backoff and informative warnings
2. **Long-term fix**: Created centralized file I/O utility module

```python
# Enhanced retry logic in events.py with cloud sync warning:
for attempt in range(max_retries):
    try:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
            f.flush()
        return
    except OSError as e:
        if e.errno == 5 and attempt < max_retries - 1:
            if attempt == 0:  # Log warning on first retry
                logger.warning(
                    f"File I/O error writing to {self.path} - retrying. "
                    "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                    "If using cloud sync, consider enabling 'Always keep on this device' "
                    f"for the data folder: {self.path.parent}"
                )
            time.sleep(retry_delay)
            retry_delay *= 2
        else:
            raise

# New centralized utility (amplifier/utils/file_io.py):
from amplifier.utils.file_io import write_json, read_json
write_json(data, filepath)  # Automatically handles retries
```

### Affected Operations Identified

High-priority file operations requiring retry protection:

1. **Memory Store** (`memory/core.py`) - Saves after every operation
2. **Knowledge Store** (`knowledge_synthesis/store.py`) - Append operations
3. **Content Processing** - Document and image saves
4. **Knowledge Integration** - Graph saves and entity cache
5. **Synthesis Engine** - Results saving

### Key Learnings

1. **Cloud sync can cause mysterious I/O errors** - Not immediately obvious from error messages
2. **Symlinked directories inherit cloud sync behavior** - WSL directories linked to OneDrive folders are affected
3. **"Always keep on device" setting fixes it** - Ensures files are locally available
4. **Retry logic should be informative** - Tell users WHY retries are happening
5. **Centralized utilities prevent duplication** - One retry utility for all file operations

### Prevention

- Enable "Always keep on this device" for any OneDrive folders used in development
- Use the centralized `file_io` utility for all file operations
- Add retry logic proactively for user-facing file operations
- Consider data directory location when setting up projects (prefer local over cloud-synced)
- Test file operations with cloud sync scenarios during development

## Tool Generation Pattern Failures (2025-01-23)

### Issue

Generated CLI tools consistently fail with predictable patterns:

- Non-recursive file discovery (using `*.md` instead of `**/*.md`)
- No minimum input validation (synthesis with 1 file when 2+ needed)
- Silent failures without user feedback
- Poor visibility into what's being processed

### Root Cause

- **Missing standard patterns**: No enforced template for common requirements
- **Agent guidance confusion**: Documentation references `examples/` as primary location
- **Philosophy violations**: Generated code adds complexity instead of embracing simplicity

### Solutions

**Standard tool patterns** (enforced in all generated tools):

```python
# Recursive file discovery
files = list(Path(dir).glob("**/*.md"))  # NOT "*.md"

# Minimum input validation
if len(files) < required_min:
    logger.error(f"Need at least {required_min} files, found {len(files)}")
    sys.exit(1)

# Clear progress visibility
logger.info(f"Processing {len(files)} files:")
for f in files[:5]:
    logger.info(f"  • {f.name}")
```

**Tool generation checklist**:

- [ ] Uses recursive glob patterns for file discovery
- [ ] Validates minimum inputs before processing
- [ ] Shows clear progress/activity to user
- [ ] Fails fast with descriptive errors
- [ ] Uses defensive utilities from toolkit

### Key Learnings

2. **Templates prevent predictable failures**: Common patterns should be enforced
3. **Visibility prevents confusion**: Always show what's being processed
4. **Fail fast and loud**: Silent failures create debugging nightmares
5. **Philosophy must be enforced**: Generated code often violates simplicity

### Prevention

- Validate against checklist before accepting generated tools
- Update agent guidance to specify correct directories
- Test with edge cases (empty dirs, single file, nested structures)
- Review generated code for philosophy compliance

## LLM Response Handling and Defensive Utilities (2025-01-19)

### Issue

Some CCSDK tools experienced multiple failure modes when processing LLM responses:

- JSON parsing errors when LLMs returned markdown-wrapped JSON or explanatory text
- Context contamination where LLMs referenced system instructions in their outputs
- Transient failures with no retry mechanism causing tool crashes

### Root Cause

LLMs don't reliably return pure JSON responses, even with explicit instructions. Common issues:

1. **Format variations**: LLMs wrap JSON in markdown blocks, add explanations, or include preambles
2. **Context leakage**: System prompts and instructions bleed into generated content
3. **Transient failures**: API timeouts, rate limits, and temporary errors not handled gracefully

### Solution

Created minimal defensive utilities in `amplifier/ccsdk_toolkit/defensive/`:

```python
# parse_llm_json() - Extracts JSON from any LLM response format
result = parse_llm_json(llm_response)
# Handles: markdown blocks, explanations, nested JSON, malformed quotes

# retry_with_feedback() - Intelligent retry with error correction
result = await retry_with_feedback(
    async_func=generate_synthesis,
    prompt=prompt,
    max_retries=3
)
# Provides error feedback to LLM for self-correction on retry

# isolate_prompt() - Prevents context contamination
clean_prompt = isolate_prompt(user_prompt)
# Adds barriers to prevent system instruction leakage
```

### Real-World Validation (2025-09-19)

**Test Results**: Fresh md_synthesizer run with defensive utilities showed dramatic improvement:

- **✅ Zero JSON parsing errors** (was 100% failure rate in original versions)
- **✅ Zero context contamination** (was synthesizing from wrong system files)
- **✅ Zero crashes** (was failing with exceptions on basic operations)
- **✅ 62.5% completion rate** (5 of 8 ideas expanded before timeout vs. 0% before)
- **✅ High-quality output** - Generated 8 relevant, insightful ideas from 3 documents

**Performance Profile**:

- Stage 1 (Summarization): ~10-12 seconds per file - Excellent
- Stage 2 (Synthesis): ~3 seconds per idea - Excellent with zero JSON failures
- Stage 3 (Expansion): ~45 seconds per idea - Reasonable but could be optimized

**Key Wins**:

1. `parse_llm_json()` eliminated all JSON parsing failures
2. `isolate_prompt()` prevented system context leakage
3. Progress checkpoint system preserved work through timeout
4. Tool now fundamentally sound - remaining work is optimization, not bug fixing

### Key Patterns

1. **Extraction over validation**: Don't expect perfect JSON, extract it from whatever format arrives
2. **Feedback loops**: When retrying, tell the LLM what went wrong so it can correct
3. **Context isolation**: Use clear delimiters to separate user content from system instructions
4. **Defensive by default**: All CCSDK tools should assume LLM responses need cleaning
5. **Test early with real data**: Defensive utilities prove their worth only under real conditions

### Prevention

- Use `parse_llm_json()` for all LLM JSON responses - never use raw `json.loads()`
- Wrap LLM operations with `retry_with_feedback()` for automatic error recovery
- Apply `isolate_prompt()` when user content might be confused with instructions

## Path Dependencies Break GitHub Installation (2025-10-30)

### Issue

`uv tool update amplifier` fails with subdirectory error when libraries use path dependencies:

```
error: Failed to download and build `amplifier-collections @ git+https://github.com/microsoft/amplifier-profiles@main#subdirectory=../amplifier-collections`
  Caused by: The source distribution has no subdirectory `../amplifier-collections`
```

Users could not install or update Amplifier from GitHub.

### Root Cause

**Path dependencies in library pyproject.toml files break GitHub installation**:

```toml
# amplifier-profiles/pyproject.toml
[tool.uv.sources]
amplifier-collections = { path = "../amplifier-collections" }  # ❌ BREAKS GITHUB
```

**Why this breaks**:
1. Works perfectly in local development (directories are siblings)
2. **Fails on GitHub installation** because:
   - `uv` clones amplifier-profiles from GitHub
   - Tries to resolve `path = "../amplifier-collections"`
   - Fails: no `../amplifier-collections` relative to cloned repo

**Violated AGENTS.md guidance**:
> **Avoid path dependencies** in core packages - they break GitHub installation

### Solution

**Two-part fix**:

**1. Change to git URL in library pyproject.toml**:

```toml
# amplifier-profiles/pyproject.toml
[tool.uv.sources]
amplifier-collections = { git = "https://github.com/microsoft/amplifier-collections", branch = "main" }  # ✅ WORKS
```

**2. Auto-reinstall libraries as editable in install-dev scripts**:

```bash
# install-dev.sh (at end, after all other installs)
echo "Reinstalling libraries as editable..."
cd amplifier-collections && uv pip install -e . --quiet && cd ..
cd amplifier-profiles && uv pip install -e . --quiet && cd ..
cd amplifier-module-resolution && uv pip install -e . --quiet && cd ..
```

**How it works now**:

- **GitHub installation**: Git URLs resolve correctly ✅
- **Local development**: Final reinstall step makes editable ✅

### Key Learnings

1. **Path dependencies are local-only**: Work in monorepos, break in distribution
2. **AGENTS.md guidance exists for a reason**: "Avoid path dependencies in core packages"
3. **Git URLs work everywhere**: Both GitHub install and local development (with reinstall)
4. **Test from GitHub**: `uv tool install` from GitHub verifies distribution works
5. **Automate workarounds**: Don't document manual steps, fix the scripts

### Prevention

**When creating library dependencies**:

```toml
# ❌ DON'T: Path dependency
[tool.uv.sources]
my-dependency = { path = "../my-dependency" }

# ✅ DO: Git URL
[tool.uv.sources]
my-dependency = { git = "https://github.com/org/my-dependency", branch = "main" }
```

**When writing install scripts**:
- Install from git URLs first (works for both local and GitHub)
- Then reinstall specific libraries as editable for local dev
- Test with `uv tool install` from GitHub, not just local installs

**Verification checklist**:
- [ ] No path dependencies in library pyproject.toml files
- [ ] All dependencies use git URLs
- [ ] Install scripts reinstall libraries as editable at end
- [ ] Test `uv tool install git+https://github.com/...` succeeds
