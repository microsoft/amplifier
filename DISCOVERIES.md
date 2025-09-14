# DISCOVERIES.md

This file documents non-obvious problems, solutions, and patterns discovered during development.

## Claude Code SDK Integration (2025-01-16)

### Issue

Knowledge Mining system was getting empty responses when trying to use Claude Code SDK. The error "Failed to parse LLM response as JSON: Expecting value: line 1 column 1 (char 0)" indicated the SDK was returning empty strings.

### Root Cause

The Claude Code SDK (`claude-code-sdk` Python package) requires:

1. The npm package `@anthropic-ai/claude-code` to be installed globally
2. Running within the Claude Code environment or having proper environment setup
3. Correct async/await patterns for message streaming

### Solution

```python
# Working pattern from ai_working/prototypes/wiki_extractor.py:
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async with ClaudeSDKClient(
    options=ClaudeCodeOptions(
        system_prompt="Your system prompt",
        max_turns=1,
    )
) as client:
    await client.query(prompt)

    response = ""
    async for message in client.receive_response():
        if hasattr(message, "content"):
            content = getattr(message, "content", [])
            if isinstance(content, list):
                for block in content:
                    if hasattr(block, "text"):
                        response += getattr(block, "text", "")
```

### Key Learnings

1. **The SDK is designed for Claude Code environment** - It works seamlessly within Claude Code but requires setup outside
2. **Handle imports gracefully** - Use try/except for imports and provide fallback behavior
3. **Message streaming is async** - Must properly handle the async iteration over messages
4. **Content structure is nested** - Messages have content lists with blocks that contain text
5. **Empty responses mean SDK issues** - If you get empty strings, check the SDK installation and environment

### Prevention

- Always test Claude Code SDK integration with a simple example first
- Use the working pattern from `wiki_extractor.py` as reference
- Provide clear error messages when SDK is not available
- Consider fallback mechanisms for when running outside Claude Code environment

## JSON Parsing with Markdown Code Blocks (2025-01-16)

### Issue
Knowledge Mining system was failing to parse LLM responses with error "Expecting value: line 1 column 1 (char 0)" even though the response contained valid JSON. The response was wrapped in markdown code blocks.

### Root Cause
Claude Code SDK sometimes returns JSON wrapped in markdown formatting:
```
```json
{ "actual": "json content" }
```
```
This causes `json.loads()` to fail because it encounters backticks instead of valid JSON.

### Solution
Strip markdown code block formatting before parsing JSON:
```python
# Strip markdown code block formatting if present
cleaned_response = response.strip()
if cleaned_response.startswith("```json"):
    cleaned_response = cleaned_response[7:]  # Remove ```json
elif cleaned_response.startswith("```"):
    cleaned_response = cleaned_response[3:]  # Remove ```

if cleaned_response.endswith("```"):
    cleaned_response = cleaned_response[:-3]  # Remove trailing ```

cleaned_response = cleaned_response.strip()
data = json.loads(cleaned_response)
```

### Key Learnings
1. **LLMs may format responses** - Even with "return ONLY JSON" instructions, LLMs might add markdown formatting
2. **Always clean before parsing** - Strip common formatting patterns before JSON parsing
3. **Check actual response content** - The error message showed the response started with "```json"
4. **Simple fixes are best** - Just strip the markdown, don't over-engineer

### Prevention
- Always examine the actual response content when JSON parsing fails
- Add response cleaning before parsing
- Test with various response formats

## Claude Code SDK Integration - Proper Timeout Handling (2025-01-20) [FINAL SOLUTION]

### Issue

Knowledge extraction hanging indefinitely outside Claude Code environment. The unified knowledge extraction system would hang forever when running outside the Claude Code environment, never returning results or error messages.

### Root Cause

The `claude_code_sdk` Python package requires the Claude Code environment to function properly:
- The SDK can be imported successfully even outside Claude Code
- Outside the Claude Code environment, SDK operations hang indefinitely waiting for the CLI
- There's no way to detect if the SDK will work until you try to use it
- The SDK will ONLY work inside the Claude Code environment

### Final Solution

**Use a 120-second (2-minute) timeout for all Claude Code SDK operations.** This is the sweet spot that:
- Gives the SDK plenty of time to work when available
- Prevents indefinite hanging when SDK/CLI is unavailable
- Returns empty results gracefully on timeout

```python
import asyncio

async def extract_with_claude_sdk(prompt: str, timeout_seconds: int = 120):
    """Extract using Claude Code SDK with proper timeout handling"""
    try:
        # Always use 120-second timeout for SDK operations
        async with asyncio.timeout(timeout_seconds):
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt="Extract information...",
                    max_turns=1,
                )
            ) as client:
                await client.query(prompt)
                
                response = ""
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    response += getattr(block, "text", "")
                return response
    except asyncio.TimeoutError:
        print(f"Claude Code SDK timed out after {timeout_seconds} seconds - likely running outside Claude Code environment")
        return ""
    except Exception as e:
        print(f"Claude Code SDK error: {e}")
        return ""
```

### Key Learnings

1. **Original code had NO timeout** - This worked in Claude Code environment but hung forever outside it
2. **5-second timeout was too short** - Broke working code by not giving SDK enough time
3. **30-second timeout was still too short** - Some operations need more time
4. **120-second timeout is the sweet spot** - Enough time for SDK to work, prevents hanging
5. **The SDK will ONLY work inside Claude Code environment** - Accept this limitation

### Prevention

- **Always use 120-second timeout for Claude Code SDK operations**
- Accept that outside Claude Code, you'll get empty results after timeout
- Don't try to make SDK work outside its environment - it's impossible
- Consider having a fallback mechanism for when SDK is unavailable
- Test your code both inside and outside Claude Code environment

### Timeline of Attempts

1. **Original**: No timeout → Works in Claude Code, hangs forever outside
2. **First fix**: 5-second timeout → Breaks working code, too short
3. **Second fix**: 30-second timeout → Better but still too short for some operations
4. **Final fix**: 120-second timeout → Perfect balance, this is the correct approach

## Claude Code CLI Global Installation Requirement (2025-01-20)

### Issue

Knowledge extraction was failing with timeouts even though claude_code_sdk Python package was installed.

### Root Cause

The Claude Code CLI (`@anthropic-ai/claude-code`) MUST be installed globally via npm, not locally. The Python SDK uses subprocess to call the `claude` CLI, which needs to be in the system PATH.

### Solution

Install the Claude CLI globally:
```bash
npm install -g @anthropic-ai/claude-code
```

Verify installation:
```bash
which claude  # Should return a path like /home/user/.nvm/versions/node/v22.14.0/bin/claude
```

Add CLI availability check in __init__:
```python
def __init__(self):
    """Initialize the extractor and check for required dependencies"""
    # Check if claude CLI is installed
    try:
        result = subprocess.run(["which", "claude"], capture_output=True, text=True, timeout=2)
        if result.returncode != 0:
            raise RuntimeError("Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        raise RuntimeError("Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
```

### Key Learnings

1. **Local npm installation (without -g) does NOT work** - The CLI must be globally accessible
2. **The CLI must be globally accessible in PATH** - Python SDK calls it via subprocess
3. **Always check for CLI availability at initialization** - Fail fast with clear instructions
4. **Provide clear error messages with installation instructions** - Tell users exactly what to do

### Prevention

- Always check for the CLI with `which claude` before using SDK
- Document the global installation requirement clearly
- Fail fast with helpful error messages
- Add initialization checks to detect missing CLI early

## SPO Extraction Timeout Issue (2025-01-20)

### Issue

SPO extraction was timing out consistently while concept extraction worked fine. The error "SPO extraction timeout - SDK may not be available" occurred after only 10 seconds, which was not enough time for the Claude Code SDK to process SPO extraction.

### Root Cause

The unified knowledge extractor had different timeout values for concept and SPO extraction:
- Concept extraction: 125 seconds (adequate)
- SPO extraction: 10 seconds (TOO SHORT)

Since both operations use the Claude Code SDK which can take 30-60+ seconds to process text, the 10-second timeout for SPO extraction was causing premature timeouts.

### Solution

Increased SPO extraction timeout to 120 seconds to match concept extraction:
```python
# In unified_extractor.py _extract_spo method:
async with asyncio.timeout(120):  # Changed from 10 to 120 seconds
    knowledge_graph = await self.spo_extractor.extract_knowledge(...)
```

Also improved error handling to:
1. Raise RuntimeError on timeout to stop processing completely
2. Update CLI to catch and report timeout errors clearly
3. Suggest checking Claude CLI installation on timeout

### Key Learnings

1. **Consistent timeouts are important** - Both concept and SPO extraction should have the same timeout
2. **120 seconds is the sweet spot** - Enough time for SDK operations without hanging forever
3. **Fail fast on timeouts** - Don't save partial results when extraction fails
4. **SPO extraction needs time** - Complex relationship extraction can take 60+ seconds

### Prevention

- Always use consistent timeout values for similar operations
- Test extraction on actual data to verify timeout adequacy
- Implement proper error propagation to stop on critical failures
- Monitor extraction times to tune timeout values appropriately

## Unnecessary Text Chunking in SPO Extraction (2025-01-20)

### Issue

SPO extraction was splitting articles into 6+ chunks even though the entire article was only ~1750 tokens. This caused unnecessary API calls and slower extraction when Claude could easily handle the entire article in one request.

### Root Cause

The SPO extractor had an extremely conservative chunk size of only 200 words:
- Default in `ExtractionConfig`: `chunk_size: int = 200`
- Hardcoded in unified_extractor: `ExtractionConfig(chunk_size=200, ...)`

This 200-word limit is from early GPT-3 days and is completely unnecessary for Claude, which can handle 100,000+ tokens (roughly 75,000+ words) in a single request.

### Solution

Increased chunk size to 10,000 words:
```python
# In unified_extractor.py:
self.spo_config = ExtractionConfig(chunk_size=10000, extraction_style="comprehensive", canonicalize=True)

# In models.py default:
chunk_size: int = 10000  # words per chunk - Claude can handle large contexts
```

### Key Learnings

1. **Claude has massive context windows** - Can handle 100K+ tokens, no need for tiny chunks
2. **200-word chunks are outdated** - This limit is from GPT-3 era, not needed for modern LLMs
3. **Fewer chunks = better extraction** - Single-pass extraction maintains better context
4. **Check defaults carefully** - Don't blindly accept conservative defaults from older code

### Prevention

- Always check and adjust chunk sizes for the specific LLM being used
- Consider the model's actual token limits when setting chunk sizes
- Prefer single-pass extraction when possible for better context preservation
- Update old code patterns that were designed for smaller context windows

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

## Claude Code SDK Subprocess Invocation Deep Dive (2025-01-05)

### Issue

Knowledge extraction system experiencing inconsistent behavior with Claude Code SDK - sometimes working, sometimes hanging or timing out. Need to understand exactly how the SDK invokes the claude CLI via subprocess.

### Investigation

Created comprehensive debugging script to intercept and log all subprocess calls made by the Claude Code SDK. Key findings:

1. **SDK uses absolute paths** - The SDK calls the CLI with the full absolute path (e.g., `~/.local/share/reflex/bun/bin/claude`), not relying on PATH lookup
2. **Environment is properly passed** - The subprocess receives the full environment including PATH, BUN_INSTALL, NODE_PATH
3. **The CLI location varies by installation method**:
   - Reflex/Bun installation: `~/.local/share/reflex/bun/bin/claude`
   - NPM global: `~/.npm-global/bin/claude` or `~/.nvm/versions/node/*/bin/claude`
   - System: `/usr/local/bin/claude`

### Root Cause

The SDK works correctly when the claude CLI is present and executable. Issues arise from:
1. **Timeout configuration** - Operations can take 30-60+ seconds, but timeouts were set too short
2. **Missing CLI** - SDK fails silently if claude CLI is not installed
3. **Installation method confusion** - Different installation methods put CLI in different locations

### Solution

```python
# 1. Verify CLI installation at initialization
def __init__(self):
    # Check if claude CLI is available (SDK uses absolute path internally)
    import shutil
    claude_path = shutil.which("claude")
    if not claude_path:
        # Check common installation locations
        known_locations = [
            "~/.local/share/reflex/bun/bin/claude",
            os.path.expanduser("~/.npm-global/bin/claude"),
            "/usr/local/bin/claude"
        ]
        for loc in known_locations:
            if os.path.exists(loc) and os.access(loc, os.X_OK):
                claude_path = loc
                break
        
        if not claude_path:
            raise RuntimeError(
                "Claude CLI not found. Install with one of:\n"
                "  - npm install -g @anthropic-ai/claude-code\n"
                "  - bun install -g @anthropic-ai/claude-code"
            )

# 2. Use proper timeout (120 seconds)
async with asyncio.timeout(120):  # SDK operations can take 60+ seconds
    async with ClaudeSDKClient(...) as client:
        # ... SDK operations ...
```

### How the SDK Actually Works

The SDK invocation chain:
1. Python `claude_code_sdk` imports and creates `ClaudeSDKClient`
2. Client spawns subprocess via `asyncio` subprocess (`Popen`)
3. Command executed: `claude --output-format stream-json --verbose --system-prompt "..." --max-turns 1 --input-format stream-json`
4. SDK finds CLI by checking common locations in order:
   - Uses `which claude` first
   - Falls back to known installation paths
   - Uses absolute path for subprocess call
5. Communication via stdin/stdout with streaming JSON

### Key Learnings

1. **SDK doesn't rely on PATH for execution** - It finds the CLI and uses absolute path
2. **The PATH environment IS preserved** - Subprocess gets full environment
3. **CLI can be anywhere** - As long as it's executable and SDK can find it
4. **Timeout is critical** - 120 seconds is the sweet spot for SDK operations
5. **BUN_INSTALL environment variable** - Set by Reflex, helps SDK locate bun-installed CLI

### Prevention

- Always verify CLI is installed and executable before using SDK
- Use 120-second timeout for all SDK operations
- Check multiple known CLI locations, not just PATH
- Provide clear installation instructions when CLI is missing
- Test SDK integration both inside and outside Claude Code environment
- Avoid nested asyncio event loops - call async methods directly
- Never use `run_in_executor` with methods that create their own event loops

## Silent Failures in Knowledge Extraction Pipeline (2025-01-21)

### Issue

Knowledge extraction pipeline had multiple silent failure points where processing would fail but appear successful:
- Empty extractions from timeouts were indistinguishable from legitimate "no data found" cases
- Failed sub-processors (relationships, insights) resulted in saving zero results that looked valid
- Items with failures couldn't be re-processed because they appeared "complete"
- No visibility into partial failures or success rates

### Root Cause

1. **Design flaw**: Empty extractions weren't saved, creating infinite retry loops
2. **No failure state**: System only tracked "processed" or "not processed", no "failed" state
3. **Binary completion**: Partial successes were treated same as full failures
4. **Silent degradation**: Timeouts and errors returned empty but valid-looking results

### Solution

Implemented resilient knowledge mining system (`resilient_miner.py`) with:

1. **Per-processor tracking**: Track success/failure for each sub-processor independently
2. **Partial result saving**: Save what succeeded even when some processors fail
3. **Status persistence**: JSON files track processing state per article
4. **Selective retry**: Re-run only failed processors, not entire articles
5. **Comprehensive reporting**: Show success rates and items needing attention

```python
# New pattern for graceful degradation
class ResilientKnowledgeMiner:
    async def process_article(self, article):
        status = load_or_create_status(article.id)
        
        for processor in ["concepts", "relationships", "insights"]:
            if already_succeeded(status, processor):
                continue
                
            result = await run_with_timeout(processor, article)
            status.processor_results[processor] = result
            save_status(status)  # Save after EACH processor
            
        return status
```

### Key Learnings

1. **Partial results have value** - Better to save 80% of extractions than lose everything
2. **Distinguish failure types** - "No data" vs "extraction failed" need different handling
3. **Incremental saves critical** - Save after each sub-processor to preserve progress
4. **Transparent reporting essential** - Users need to know what failed and why
5. **Graceful degradation philosophy** - 4-hour batch completing with partial results beats early failure

### Prevention

- Design batch systems with partial failure handling from the start
- Always distinguish between "empty results" and "processing failed"
- Implement per-component status tracking for complex pipelines
- Provide comprehensive error reporting at end of long runs
- Allow selective retry of only failed components

## Claude Code SDK Async Integration Issues (2025-01-21) 

### Issue

Knowledge extraction hanging indefinitely when using Claude Code SDK, even though the CLI was properly installed. The SDK would timeout with "Claude Code SDK timeout - likely running outside Claude Code environment" message despite the CLI being accessible.

### Root Cause

**Nested asyncio event loop conflict** - The issue wasn't PATH or CLI accessibility, but improper async handling:

1. `unified_extractor.py` had a synchronous `extract()` method that used `asyncio.run()` internally
2. The CLI was calling this via `run_in_executor()` from an async context
3. This created nested event loops, causing the SDK's async operations to hang

### Solution

Fixed by making the extraction fully async throughout the call chain:

```python
# BEFORE (causes nested event loop)
class UnifiedKnowledgeExtractor:
    def extract(self, text: str, source_id: str):
        # This creates a new event loop
        return asyncio.run(self._extract_async(text, source_id))
        
# In CLI:
result = await loop.run_in_executor(None, extractor.extract, content, article_id)

# AFTER (proper async handling)
class UnifiedKnowledgeExtractor:
    async def extract_from_text(self, text: str, title: str = "", source: str = ""):
        # Directly async, no nested loops
        return await self._extract_async(text, title, source)
        
# In CLI:
result = await extractor.extract_from_text(content, title=article.title)
```

### Key Learnings

1. **Nested event loops break async operations** - Never use `asyncio.run()` inside a method that might be called from an async context
2. **SDK requires proper async context** - The Claude Code SDK uses async operations internally and needs a clean event loop
3. **The error message was misleading** - "running outside Claude Code environment" actually meant "async operations are blocked"
4. **PATH was never the issue** - The SDK could find the CLI perfectly fine once async was fixed

### Prevention

- Design APIs to be either fully sync or fully async, not mixed
- Never use `run_in_executor()` with methods that create event loops
- When integrating async SDKs, ensure the entire call chain is async
- Test async operations with proper error handling to surface the real issues
- Don't assume timeout errors mean the SDK can't find the CLI
