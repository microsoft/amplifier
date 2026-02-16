# DISCOVERIES.md

This file documents non-obvious problems, solutions, and patterns discovered during development. Make sure these are regularly reviewed and updated, removing outdated entries or those replaced by better practices or code or tools, updating those where the best practice has evolved.

Archived entries (no longer actively relevant) are in DISCOVERIES-archive.md.

## Dual-Platform Architecture: Runtime Gating vs Separate Branches (2026-02-16)

### Issue

Amplifier runs on two AI platforms (Claude Code + OpenCode/Gemini) daily. Gemini requires platform-specific optimizations (Gold Prefix context caching, zone labels, agent format sync). The question: where does platform-specific code live?

### Root Cause

Initially implemented as runtime-gated code on main (PR #6). Then separated to a branch for "cleanliness." The branch immediately drifted — hook files (the exact files that differ) change frequently, causing constant merge conflicts.

### Solution

**Runtime gating on `main` is the correct approach** when both platforms are actively used. All Gemini-specific code is guarded by `if IS_OPENCODE:` checks in `.claude/tools/platform_detect.py`. The gated code never executes on the wrong machine.

Key files: `platform_detect.py` (detection), `hook_session_start.py` (zone labels), `hook_precompact.py` (GoldPrefixCompactor), `scripts/sync-agents-to-opencode.py` (agent format).

Full documentation: `docs/superpowers/specs/2026-02-15-context-caching-optimization.md`

### Prevention

- Never separate actively-used platform code into long-lived branches
- Runtime gating has zero cost — gated code doesn't execute on the wrong platform
- When adding Gemini features, use `if IS_OPENCODE:` / `else:` pattern
- When adding agents, run `scripts/sync-agents-to-opencode.py` to update OpenCode format

## Subagent Context Exhaustion (2026-02-14)

### Issue

Subagents launched via the Task tool cut off work in high token usage situations. Two failure modes observed:

1. **Abrupt stop** — Agent returns partial results mid-task without finishing
2. **Summary mode fallback** — Agent shifts to describing what it would do instead of doing the work

### Root Cause

Subagents have their own context windows that fill up from incoming content: large file reads, verbose tool results, and tasks that are too big for one agent pass. The existing context budget guardrails (added 2026-02-06) help agents avoid *generating* excessive context but don't protect against *incoming* pressure. When context pressure builds, the model either hits hard limits (abrupt stop) or enters a "conservation instinct" where it summarizes instead of executing (summary mode).

### Solution

**max_turns + Resume pattern:** Set `max_turns` on every Task dispatch to stop agents before context pressure builds. When an agent returns incomplete work, use `resume` with the agent's ID to continue with preserved context. Limit to 3 resume cycles before escalating to the user. See the "Subagent Resilience Protocol" section in AGENTS.md for turn budget values and the full protocol.

**Task decomposition:** Right-size tasks before dispatch: 3-5 files to read, 1-3 files to modify, 1 objective per agent. Decompose large tasks into focused subtasks. See AGENTS.md for sizing guidelines.

### Prevention

- Always include `max_turns` in Task dispatches (never leave it unlimited)
- Break large tasks into agent-sized pieces before dispatching
- When a task is indivisible, use generous `max_turns` and rely on the resume protocol
- Monitor agent completion rates and tune turn budgets based on observation

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
