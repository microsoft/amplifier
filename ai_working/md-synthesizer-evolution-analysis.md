# MD-Synthesizer Tool Evolution Analysis

## Executive Summary

The md-synthesizer tool went through 4 major iterations before reaching a working state. Each iteration revealed fundamental issues that weren't apparent during initial development. This document analyzes what went wrong at each stage, what fixes were applied, and most importantly, what the shortest path from v1 to final would have been if we had perfect foresight.

## Version 1: Initial Creation Issues

### What Was Wrong
1. **Missing CLI Parameter Implementation**
   - The `--limit` parameter was completely missing from the CLI implementation
   - The Makefile defined `LIMIT` but didn't pass it to the Python CLI
   - Result: Tool always processed ALL files regardless of user input

2. **Import Errors**
   - Used `TimeoutError` instead of `asyncio.TimeoutError` in 3 files
   - Python's built-in `TimeoutError` is different from asyncio's version
   - Result: Runtime errors when timeout exceptions occurred

3. **Undefined Variable Bug**
   - `expander.py` referenced undefined `file_path` variable in `_parse_expansion` method
   - Method signature didn't include this parameter
   - Result: NameError crashes during Stage 3 execution

### What Was Done to Fix
- Added `--limit` parameter to CLI with default value of 5
- Updated all `TimeoutError` references to `asyncio.TimeoutError`
- Removed `file_path` parameter from `_parse_expansion` method signature
- Modified Makefile to pass `LIMIT` parameter to CLI command

### Root Cause
The agent didn't test the tool end-to-end with actual command-line invocation. These were basic integration issues that would have been caught immediately with a single test run.

---

## Version 2: JSON Parsing Failures

### What Was Wrong
1. **Weak Prompt Instructions**
   - Stage 2 synthesis prompt wasn't forceful enough about JSON-only output
   - Claude was returning natural language preambles like "I'll analyze these document summaries..."
   - No handling for markdown-wrapped JSON responses

2. **No Retry Mechanism**
   - Single attempt at getting JSON from Claude
   - On failure, returned empty list silently
   - No feedback loop to correct format issues

3. **Insufficient Debugging**
   - Response content logged but truncated to 1000 characters
   - Couldn't see full response to understand format issues
   - No distinction between "no ideas found" vs "parsing failed"

### What Was Done to Fix
- Enhanced prompt with explicit "Your response must be ONLY a valid JSON array" instruction
- Added robust JSON parsing with multiple fallback strategies:
  - Strip markdown code blocks
  - Extract JSON from mixed text
  - Regex extraction for individual objects
- Implemented retry mechanism with error feedback:
  - Up to 2 retries
  - Shows Claude what went wrong
  - Provides examples of what NOT to do
- Enhanced logging to show full responses and retry attempts

### Root Cause
The agent assumed Claude would always return pure JSON when asked, without considering the realities of LLM behavior. No defensive programming for common LLM response patterns.

---

## Version 3: Path Resolution Bug

### What Was Wrong
1. **Path Storage Mismatch**
   - Stage 1 stored full absolute paths in file_summaries keys
   - Stage 2 stored only filenames (no path) in source_files arrays
   - Stage 3 tried to read files from current directory using filename only

2. **No Path Context Preservation**
   - Original source directory wasn't tracked between stages
   - No way for Stage 3 to know where the original files were located
   - Checkpoint data structure didn't include source directory

3. **Silent File Read Failures**
   - Files couldn't be read but processing continued
   - Warnings logged but ideas still "expanded" without source content
   - Result looked successful but was actually empty

### What Was Done to Fix
- Updated Stage 2 prompt to explicitly request FULL ABSOLUTE PATHS
- Added fallback path resolution in Stage 3:
  - First try path as-is (for new checkpoints)
  - Fall back to searching file_summaries for matching filenames
  - Use full path from file_summaries when found
- Made fix backward-compatible with existing checkpoints

### Root Cause
The synthesis prompt example showed `["file1.md", "file2.md"]` which Claude followed literally. The agent didn't consider data flow between stages or test with actual file paths.

---

## Version 4: Context Contamination

### What Was Wrong
1. **AI Using System Context Instead of Provided Content**
   - Stage 1 returning generic summaries: "I'll read and summarize the markdown document for you"
   - Stage 2 synthesizing ideas from repo files (AGENTS.md, CLAUDE.md, DISCOVERIES.md)
   - Not processing the actual article content at all

2. **Prompt Triggering Issues**
   - Including file paths in prompts made AI think it should read files itself
   - System context from Claude Code environment was overpowering provided content
   - No explicit instruction to ONLY use provided content

3. **Complete Pipeline Corruption**
   - Useless summaries fed into Stage 2
   - Stage 2 synthesized from wrong sources
   - Stage 3 expanded wrong ideas with wrong content
   - Output looked valid but was completely wrong

### What Was Done to Fix
- Stage 1: Removed file paths from prompts, added "The content is already provided below. Summarize it directly."
- Stage 2: Added "IMPORTANT: Only use the document summaries provided below. Do NOT reference any files from the amplifier-cli-tool-demo repository."
- Added explicit system prompts:
  - Stage 1: "You are a document summarizer. Provide direct summaries only."
  - Stage 2: "You are a synthesis expert. You always respond with valid JSON arrays when requested."

### Root Cause
The agent didn't anticipate that Claude's system context could contaminate the results. Prompts weren't explicit enough about using ONLY provided content.

---

## The Shortest Path from V1 to Final

If we had perfect foresight, here's the minimal set of changes needed to go directly from v1 to the final working version:

### 1. CLI and Parameter Handling
```python
# Add to CLI
@click.option("--limit", "-l", type=int, default=5, help="Maximum files to process (0 for unlimited)")

# Update Makefile
echo "Synthesizing insights from $$dir (limit: $$limit files)..."; \
uv run python -m amplifier.ccsdk_toolkit.tools.md_synthesizer.cli "$$dir" --limit $$limit
```

### 2. Correct Async Import
```python
# In all files: Change
except TimeoutError:
# To
except asyncio.TimeoutError:
```

### 3. Robust JSON Handling with Retry
```python
async def _synthesize_with_retry(self, prompt, session, max_retries=2):
    for attempt in range(max_retries + 1):
        response = await session.query(current_prompt)

        # Try parsing
        ideas = self._parse_json_response(response.content)
        if ideas:
            return ideas

        # On retry, provide error feedback
        if attempt < max_retries:
            current_prompt = self._create_correction_prompt(prompt, response.content)

    return []

def _parse_json_response(self, response):
    # Strip markdown formatting
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        return json.loads(cleaned.strip())
    except:
        return []
```

### 4. Full Path Storage and Resolution
```python
# Stage 2 prompt
"Return ONLY a JSON array where each source_files contains FULL ABSOLUTE PATHS"

# Stage 3 fallback
if not Path(file_path).exists():
    # Search file_summaries for matching filename
    filename = Path(file_path).name
    for full_path in self.state.file_summaries.keys():
        if Path(full_path).name == filename:
            file_path = full_path
            break
```

### 5. Explicit Content Isolation
```python
# Stage 1 prompt
"The content is already provided below. Summarize it directly. Do not attempt to read any files."

# Stage 2 prompt
"IMPORTANT: Only use the document summaries provided below. Do NOT reference any files from the amplifier-cli-tool-demo repository."

# System prompts
system_prompt="You are a document summarizer. Provide direct summaries only."
```

---

## Lessons for CCSDK-Toolkit Improvements

### 1. Mandatory End-to-End Testing
- **Requirement**: Every tool MUST include a test that runs the actual CLI command
- **Implementation**: Add a `test_cli.py` that executes `make` commands with sample data
- **Validation**: Verify actual output, not just that code runs without errors

### 2. LLM Response Robustness
- **Standard Pattern**: All LLM responses should have retry + format cleaning
- **Toolkit Feature**: Provide a `parse_llm_json()` utility that handles common patterns
- **Documentation**: List known response formats (markdown blocks, preambles, etc.)

### 3. Data Flow Validation
- **Requirement**: Multi-stage pipelines must validate data contracts between stages
- **Implementation**: Type hints or schemas for stage inputs/outputs
- **Testing**: Each stage tested with output from previous stage

### 4. Prompt Isolation Guidelines
- **Principle**: Always explicitly state "use ONLY provided content"
- **Anti-pattern Examples**: Never include file paths that AI might try to access
- **System Prompt Standards**: Define role narrowly to prevent context bleed

### 5. Defensive File Operations
- **Path Handling**: Always store and use absolute paths
- **Existence Checks**: Verify files exist before processing
- **Error Propagation**: Fail fast with clear messages, don't continue with bad data

### 6. Progressive Enhancement Testing
- **Start Simple**: Test with 1 file first, then scale
- **Real Data**: Test with actual content, not synthetic examples
- **Error Cases**: Explicitly test timeout, parsing, and missing file scenarios

### 7. Logging and Debugging
- **Full Content**: Never truncate responses in logs during development
- **State Visibility**: Log what's being stored in checkpoints
- **Retry Visibility**: Clear logging when retries happen and why

### 8. Context Contamination Prevention
- **Isolated Prompts**: Design prompts that can't access system context
- **Explicit Boundaries**: "You have no access to any files or system context"
- **Verification**: Test that results come from provided content only

---

## Key Insights

1. **The First Version Was 80% Correct** - Most of the structure was right, but critical details were wrong
2. **Every Bug Was Predictable** - These weren't edge cases but common patterns in LLM tool development
3. **Testing Would Have Caught Everything** - A single end-to-end test run would have revealed all v1 issues
4. **LLM Behavior Assumptions Were Naive** - Assuming JSON-only output without defensive coding
5. **Context Isolation Is Critical** - System context contamination is a real risk that must be explicitly prevented

## Recommendations for CCSDK-Toolkit

1. **Create Tool Template** with:
   - CLI parameter handling boilerplate
   - Standard retry mechanisms for LLM calls
   - JSON parsing utilities
   - Path handling best practices
   - End-to-end test scaffolding

2. **Provide Common Utilities**:
   - `parse_llm_json()` - Handle all common response formats
   - `retry_with_feedback()` - Standard retry pattern for LLM calls
   - `isolate_prompt()` - Ensure prompts can't access system context
   - `validate_stage_data()` - Check data contracts between pipeline stages

3. **Mandatory Testing Checklist**:
   - [ ] CLI invocation with actual `make` command
   - [ ] Process at least 2 real files
   - [ ] Verify output is from provided content
   - [ ] Test timeout handling
   - [ ] Test parsing failures
   - [ ] Test missing file handling

4. **Documentation Requirements**:
   - Example of actual CLI invocation
   - Sample output from real run
   - Common failure modes and solutions
   - Data flow diagram for multi-stage pipelines

## Conclusion

The md-synthesizer tool evolution reveals that the gap between "looks right" and "actually works" is filled with predictable issues. The initial implementation was structurally sound but failed on integration details that should have been caught with basic testing.

The most valuable improvement to the CCSDK-toolkit would be enforcing end-to-end testing and providing battle-tested utilities for common LLM interaction patterns. This would prevent future tools from repeating the same predictable mistakes.