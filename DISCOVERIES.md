# DISCOVERIES.md

This file documents non-obvious problems, solutions, and patterns discovered during development. Make sure these are regularly reviewed and updated, removing outdated entries or those replaced by better practices or code or tools, updating those where the best practice has evolved.

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
