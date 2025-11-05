# Claude Code SDK Developer Guide

_A strategic guide for building AI-native development tools in the Claude Code ecosystem_

## Table of Contents

1. [The Core Idea: Metacognitive Recipes](#the-core-idea-metacognitive-recipes)
2. [Key Principles](#key-principles)
3. [Choosing Your Approach](#choosing-your-approach)
4. [The Amplifier Pattern](#the-amplifier-pattern)
5. [Composition Strategies](#composition-strategies)
6. [Decomposition Patterns](#decomposition-patterns)
7. [Cookbook Patterns](#cookbook-patterns)
8. [Anti-Patterns](#anti-patterns)
9. [Conclusion](#conclusion)

## The Core Idea: Metacognitive Recipes

The Claude Code SDK enables a fundamental shift: **use code for structure, AI for intelligence**.

Instead of trying to get AI to handle complex multi-step reasoning (which often fails), we decompose problems into small, focused AI microtasks orchestrated by deterministic code. Think of it as writing "recipes" where:

- **Code controls the flow** (loops, conditions, error handling, state management)
- **AI provides intelligence** (understanding, creativity, judgment, extraction)
- **Together they amplify** (reliable structure + flexible intelligence = powerful tools)

### Core Design Philosophy

- Break large tasks into small, focused chunks that AI can handle reliably
- Save progress incrementally after each successful operation
- Use parallel processing when tasks are independent
- Let code handle coordination while AI handles cognition

### When to Use This Pattern

✅ **Perfect fit:**
- Multi-step workflows needing AI at each step
- Batch processing with intelligent analysis
- Knowledge extraction and synthesis pipelines
- Parallel exploration of solution spaces
- Document processing at scale
- Content generation with quality control

❌ **Wrong tool:**
- Simple string transformations (use code)
- Real-time requirements (< 1 second)
- Deterministic operations (use algorithms)
- Pure calculations (use libraries)

## Key Principles

### 1. Decompose Ruthlessly
Break ambitious AI tasks into tiny, focused operations. If a single prompt tries to do too much, it's too big.

### 2. Orchestrate with Code
Use Python/JavaScript for control flow, not complex AI prompts. Code handles loops, conditions, and coordination.

### 3. Save Incrementally
Every successful microtask should persist its results. Never lose progress to interruptions.

### 4. Embrace Partial Success
80% extraction beats 0% from failures. Design systems that gracefully handle incomplete results.

### 5. Parallelize When Possible
AI operations without dependencies can run concurrently. Use `asyncio.gather()` liberally.

## Choosing Your Approach

### Quick Decision Tree

```
1. Is it a one-time extraction?
   → Raw SDK call with error handling

2. Processing many documents?
   → Amplifier CLI with batch processing and incremental saves

3. Need interactive development?
   → Slash commands in Claude Code for exploration

4. Complex orchestration with multiple AI steps?
   → Write a Python/JavaScript recipe using the SDK
```

### The Decomposition Test

Can your AI task be reliably completed with a single, focused prompt?

- **✅ Yes** → Use it directly with error handling
- **❌ No** → Decompose into smaller tasks:

```python
# ❌ WRONG: Ambitious single AI operation
await sdk.query("Analyze this entire codebase and suggest improvements")

# ✅ RIGHT: Decomposed into focused microtasks
files = get_all_files()

# Step 1: Parallel analysis (batch of 10)
for batch in chunks(files, 10):
    summaries = await asyncio.gather(*[
        analyze_file(f) for f in batch  # Each file gets focused analysis
    ])
    save_summaries(summaries)

# Step 2: Synthesis (focused task)
all_summaries = load_summaries()
insights = await synthesize_patterns(all_summaries)  # Single focused task
save_insights(insights)
```

### Resource Considerations

**When to optimize:**
- Processing >100 items → Add progress tracking
- Costs >$10/run → Implement token counting
- Frequent failures → Add retry logic with backoff
- Daily use → Build as permanent CLI tool

## The Amplifier Pattern

### What Is Amplification?

The Amplifier pattern represents a hybrid approach where:
1. **Code provides structure** - Control flow, error handling, persistence
2. **AI provides intelligence** - Understanding, creativity, adaptation
3. **Together they amplify** - Achieving more than either could alone

### Core Amplifier Principles

1. **Leverage Strengths** - Use code for what it does best, AI for what it does best
2. **Maintain Boundaries** - Clear interfaces between code and AI components
3. **Enable Iteration** - Easy to swap AI approaches without changing structure
4. **Preserve Context** - Maintain state across AI invocations

### When to Use Amplifier Pattern

**Perfect Fit:**
- Knowledge extraction pipelines
- Content transformation workflows
- Multi-stage analysis processes
- Iterative refinement tasks

**Poor Fit:**
- Simple CRUD operations
- Pure calculation tasks
- Real-time processing
- Deterministic transformations

### Amplifier Implementation Strategy

```python
# The Amplifier pattern in practice
class AmplifiedProcessor:
    def __init__(self):
        self.structure = CodeBasedStructure()  # Deterministic
        self.intelligence = ClaudeCodeSDK()    # Intelligent

    async def process(self, input):
        # Code handles flow
        validated = self.structure.validate(input)

        # AI handles understanding
        insights = await self.intelligence.analyze(validated)

        # Code handles persistence
        self.structure.save(insights)

        # Together: Robust + Intelligent
        return insights
```

### Tool Organization: Where Should Your Tool Live?

When building amplifier CLI tools, follow the **Progressive Maturity Model** for organizing your code:

#### scenarios/[tool_name]/ - Production-Ready Tools

**Use this location when your tool:**
- ✓ Solves a real user problem (not just a demo)
- ✓ Has a clear metacognitive recipe (structured thinking process)
- ✓ Includes complete documentation (README.md + HOW_TO_CREATE_YOUR_OWN.md)
- ✓ Is ready for others to use and learn from
- ✓ Serves as both practical utility AND learning exemplar

**Required structure:**
```
scenarios/[tool_name]/
├── README.md                    # What it does, how to use it
├── HOW_TO_CREATE_YOUR_OWN.md   # How it was created, patterns used
├── __init__.py                  # Python package
├── main.py or cli.py            # Main entry point
├── [other modules]/             # Implementation modules
└── tests/                       # Working examples and test cases
    ├── sample_input.md
    └── expected_output.json
```

**Philosophy:** @scenarios/README.md embodies "minimal input, maximum leverage" - describe what you want, get a working tool, share what you learned.

**THE Exemplar:** @scenarios/blog_writer/ is THE exemplar to model after. When creating new scenario tools:
- Study its README.md structure and content
- Model your HOW_TO_CREATE_YOUR_OWN.md after it
- Match its documentation quality and completeness
- Maintain the same level of detail and learning value

#### ai_working/[tool_name]/ - Experimental Tools

**Use this location when:**
- Tool is in prototype/experimental stage
- Internal development tool not ready for users
- Missing complete documentation
- Rapid iteration and changes expected
- Requirements are still being refined

**Progression:** Tools should graduate from `ai_working/` to `scenarios/` after 2-3 successful uses by real users and when they meet all production-ready criteria above.

#### amplifier/ - Core Library Components

**Use this location for:**
- Core library components (not standalone CLI tools)
- Shared utilities used across multiple tools
- Infrastructure code (sessions, logging, defensive utilities)
- Toolkit components

**Not for:** Standalone CLI tools that users invoke directly.

#### When in Doubt

Ask yourself: "Would this help other developers solve similar problems AND teach them the pattern?"
- **Yes** → scenarios/
- **Not yet** → ai_working/
- **It's not a tool** → amplifier/

#### Always Start with the Template

**CRITICAL:** Begin with the proven template:
```bash
cp amplifier/ccsdk_toolkit/templates/tool_template.py [destination]/[tool_name].py
```

The template contains ALL defensive patterns discovered through real failures. Modify, don't start from scratch.

#### Reference Code (NOT for New Tools)

**amplifier/ccsdk_toolkit/examples/** - Study these for patterns, NEVER place new tools here. These are learning references only.

## Composition Strategies

### Pattern 1: Pipeline Composition

Chain multiple AI operations with code orchestration:

```
Input → [AI: Extract] → [Code: Validate] → [AI: Transform] → [Code: Save] → Output
```

**Use when:** Each step depends on previous results

### Pattern 2: Parallel Composition

Run multiple AI operations simultaneously:

```
        ┌→ [AI: Analyze sentiment]  →┐
Input → ├→ [AI: Extract entities]   →├→ [Code: Merge] → Output
        └→ [AI: Summarize content]  →┘
```

**Use when:** Operations are independent

### Pattern 3: Hierarchical Composition

Nest AI operations within each other:

```
[AI: Plan approach] → [AI: Execute each step] → [AI: Synthesize results]
         ↓                      ↓                         ↓
    (generates steps)    (runs subagents)        (creates summary)
```

**Use when:** High-level reasoning guides detailed execution

### Pattern 4: Iterative Composition

Refine results through multiple passes:

```
Initial → [AI: Generate] → [Code: Score] → [AI: Improve] → [Code: Score] → Final
              ↑________________________________________________↓
                        (loop until score acceptable)
```

**Use when:** Quality matters more than speed

### Composition Decision Matrix

| Pattern | Speed | Quality | Cost | Complexity |
|---------|-------|---------|------|------------|
| Pipeline | Medium | High | Medium | Low |
| Parallel | Fast | Medium | High | Medium |
| Hierarchical | Slow | Highest | High | High |
| Iterative | Slowest | Highest | Highest | Medium |

## Decomposition Patterns

### Pattern 1: Chunking Large Content

When content exceeds what AI can handle in one pass:

```python
# Instead of processing massive documents at once
chunks = split_into_chunks(document, max_tokens=3000)
results = []
for chunk in chunks:
    result = await process_chunk(chunk)  # Focused processing per chunk
    results.append(result)
    save_progress(results)  # Incremental saves
```

### Pattern 2: Map-Reduce for Analysis

Extract different aspects in parallel, then synthesize:

```python
# Map: Parallel focused analysis
analyses = await asyncio.gather(*[
    analyze_aspect(doc, aspect)
    for aspect in ["concepts", "relationships", "insights"]
])

# Reduce: Synthesize results
final = await synthesize(analyses)  # Single focused task
```

### Pattern 3: Progressive Refinement

Start broad, get specific:

```python
# Generate outline first
outline = await generate_outline(requirements)  # High-level structure

# Expand each section
for section in outline.sections:
    content = await expand_section(section)  # Detailed content
    save_section(content)  # Save immediately
```

### Pattern 4: Parallel Batch Processing

Maximize throughput with controlled concurrency:

```python
async def process_batch(items, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(item):
        async with semaphore:
            return await process_item(item)

    results = await asyncio.gather(*[
        process_with_limit(item) for item in items
    ], return_exceptions=True)

    # Handle partial success
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [(i, r) for i, r in enumerate(results) if isinstance(r, Exception)]

    return successful, failed
```

## Cookbook Patterns

### Recipe 1: Resilient Knowledge Extraction

**Problem:** Extract knowledge from documents that might fail partially

**Solution:**
```python
# Save after each step, track what succeeded
for processor in ["concepts", "relationships", "insights"]:
    if not already_processed(doc, processor):
        result = await extract_with_streaming(doc, processor)
        save_result(doc, processor, result)
```

**Key insight:** Partial results are better than no results

### Recipe 2: Parallel Document Analysis

**Problem:** Analyze many documents quickly

**Solution:**
```python
# Process in parallel batches
async def analyze_batch(docs):
    tasks = [analyze_doc(doc) for doc in docs[:10]]  # Limit concurrency
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

**Key insight:** Controlled parallelism prevents overwhelming the system

### Recipe 3: Progressive Refinement

**Problem:** Improve quality through iteration

**Solution:**
```python
# Iterate until quality threshold met
quality = 0
result = initial_result
while quality < threshold and iterations < max:
    result = await refine_with_ai(result, quality_feedback)
    quality = assess_quality(result)
    iterations += 1
```

**Key insight:** Multiple passes yield better results than one complex prompt

### Recipe 4: Context-Preserving Chains

**Problem:** Maintain context across multiple AI calls

**Solution:**
```python
# Build context incrementally
context = {"history": [], "facts": {}}
for step in workflow:
    response = await ai_process(step, context)
    context["history"].append(response)
    context["facts"].update(extract_facts(response))
```

**Key insight:** Explicit context management improves coherence

### Recipe 5: Fallback Strategies

**Problem:** Handle AI service unavailability

**Solution:**
```python
# Graceful degradation
try:
    result = await ai_powered_extraction(doc)
except Exception:
    result = await simple_regex_extraction(doc)  # Fallback
    result["degraded"] = True
```

**Key insight:** Some result is better than failure

## Anti-Patterns

### Anti-Pattern 1: Ambitious AI Operations (The #1 Mistake)

**Wrong - Trying to do too much in one AI call:**

```python
# This will fail, produce poor results, or both
response = await sdk.query("""
Analyze this entire codebase, understand all the patterns,
identify all issues, suggest refactoring strategies,
generate test cases, document everything, and create
a complete improvement plan with timelines.
""")
```

**Right - Decompose into focused microtasks:**

```python
# 1. Inventory phase (deterministic code)
files = collect_source_files()

# 2. Parallel analysis (small AI tasks)
for batch in chunks(files, 10):
    summaries = await asyncio.gather(*[
        summarize_file(f) for f in batch  # Focused task per file
    ])
    save_summaries(summaries)

# 3. Pattern detection (focused AI task)
patterns = await identify_patterns(load_summaries())  # Single purpose
save_patterns(patterns)

# 4. Issue identification (focused AI task)
issues = await find_issues(patterns)  # Single purpose
save_issues(issues)

# 5. Generate plan (synthesis AI task)
plan = await create_improvement_plan(issues, patterns)  # Synthesis
```

**Lesson:** AI excels at focused tasks, struggles with ambitious multi-step reasoning. Let code handle orchestration and state management.

### Anti-Pattern 2: Over-Engineering Simple Tasks

**Wrong:**
```python
# Using AI for simple string manipulation
async def capitalize_text(text):
    response = await claude_sdk.query(f"Capitalize this: {text}")
    return response
```

**Right:**
```python
def capitalize_text(text):
    return text.upper()
```

**Lesson:** Don't use AI where simple code suffices

### Anti-Pattern 3: No Error Handling

**Wrong:**
```python
# No error handling = silent failures
result = await client.query(prompt)
process_result(result)  # What if query failed?
```

**Right:**
```python
# Always handle potential failures
try:
    result = await client.query(prompt)
    if result and result.success:
        process_result(result)
    else:
        handle_failure("Query returned no results")
except Exception as e:
    log_error(f"Query failed: {e}")
    raise  # Or handle appropriately
```

**Lesson:** AI operations can fail - always handle errors explicitly

### Anti-Pattern 4: Sequential When Parallel Would Work

**Wrong:**
```python
# Process one at a time
for doc in documents:
    result = await process(doc)  # Slow!
    results.append(result)
```

**Right:**
```python
# Process in parallel
tasks = [process(doc) for doc in documents]
results = await asyncio.gather(*tasks)
```

**Lesson:** Parallelize independent operations

### Anti-Pattern 5: All-or-Nothing Processing (Context Matters)

This anti-pattern is **situationally dependent**. The right approach depends on your goals:

#### When Processing Large Batches (Goal: Eventually Process Everything)

**Right - Graceful degradation for batch processing:**
```python
# When the goal is to process as many items as possible
successful = []
failed = []

for item in items:
    try:
        result = await ai_process(item)
        save(result)
        successful.append(item)
    except Exception as e:
        log_error(item, e)
        failed.append((item, str(e)))
        continue  # Keep going

print(f"Processed {len(successful)}/{len(items)} successfully")
# Can retry failed items later
```

#### When Quality Cannot Be Compromised

**Right - Fail fast when AI quality is required:**
```python
# When fallback would produce inferior results
try:
    result = await ai_analyze(document)
    if not result or result.confidence < threshold:
        raise ValueError("AI analysis did not meet quality standards")
    return result
except Exception as e:
    # DON'T fall back to regex or simple heuristics
    # FAIL clearly so the issue can be addressed
    raise RuntimeError(f"Cannot proceed without proper AI analysis: {e}")
```

**Wrong - Silent degradation to inferior methods:**
```python
# DON'T do this - hiding AI failures with inferior fallbacks
try:
    result = await ai_extract_entities(text)
except:
    # This regex pattern is NOT equivalent to AI understanding
    result = simple_regex_extraction(text)  # Bad fallback!
```

**Lesson:** Choose your failure strategy based on context:
- **Batch processing**: Save what you can, track failures for retry
- **Quality-critical operations**: Fail explicitly rather than degrade silently
- **Never**: Silently substitute inferior non-AI methods when AI was specifically requested

### Anti-Pattern 6: Mixing Concerns

**Wrong:**
```python
# AI doing everything
prompt = """
Extract entities, validate format, save to database,
send notifications, and update cache for this document
"""
```

**Right:**
```python
# AI for intelligence, code for mechanics
entities = await ai_extract_entities(doc)
validated = code_validate_format(entities)
code_save_to_database(validated)
code_send_notifications(validated)
```

**Lesson:** Separate intelligence from mechanics

### Anti-Pattern 7: Premature Optimization

**Wrong:**
```python
# Complex caching before proving need
class OverEngineeredCache:
    def __init__(self):
        self.l1_cache = {}
        self.l2_cache = {}
        self.distributed_cache = Redis()
        # 200 lines of premature optimization
```

**Right:**
```python
# Start simple
cache = {}  # Add complexity only when needed
```

**Lesson:** Optimize after measuring, not before

## Conclusion

The Claude Code SDK toolkit is about one core insight: **small AI tasks orchestrated by code outperform large ambitious AI operations**.

### Quick Reference Card

```python
# The pattern that works:
async def process_intelligently(data):
    # 1. Code structures the work
    chunks = prepare_data(data)

    # 2. AI provides focused intelligence (parallel when possible)
    results = await asyncio.gather(*[
        ai_analyze(chunk) for chunk in chunks  # Focused analysis per chunk
    ])

    # 3. Code handles persistence
    save_incremental_results(results)

    # 4. AI synthesizes if needed
    synthesis = await ai_synthesize(results)  # Final synthesis

    return synthesis
```

### Your Next Steps

1. Take any task that would fail as a single ambitious AI operation
2. Decompose it into focused, single-purpose chunks
3. Add incremental saves between chunks
4. Measure the improvement in reliability and quality

### The Golden Rule

If your AI prompt is trying to do multiple things at once, decompose it. Each AI operation should have a single, clear purpose. This isn't a limitation—it's a design principle that leads to more reliable and maintainable systems.

---

_This guide is a living document. As the ecosystem evolves and new patterns emerge, it will be updated to reflect the latest insights and best practices._