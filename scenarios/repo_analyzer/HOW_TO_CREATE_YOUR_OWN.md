# How to Create Your Own Repository Analysis Tool

This guide shows how the Repository Analyzer was built and how you can create similar tools.

## The Architecture Pattern

This tool demonstrates a powerful pattern for complex analysis tasks:

```
Input Processing → Analysis → Generation → Multi-Review → Human Feedback → Iteration
```

Each stage is a separate module with isolated context, preventing contamination and ensuring quality.

## Key Design Decisions

### 1. Modular Pipeline with State Management

**Why**: Long-running analysis needs interruption/resume capability.

**How we did it**:
```python
# State saved after every operation
self.state.set_opportunities(opportunities)
self.state.update_stage("opportunities_generated")
self.state.save()
```

**Your tool**: Include state management if processing might take time or need iteration.

### 2. Isolated Review Contexts

**Why**: Prevents reviewers from being influenced by previous analysis (avoids hallucination).

**How we did it**:
- Each reviewer gets ONLY the raw data and specific review criteria
- No access to previous analysis or other reviews
- Fresh LLM context for each review

**Your tool**: Use isolated contexts when you need unbiased verification.

### 3. Parallel Processing

**Why**: Reviews are independent, so run them simultaneously.

**How we did it**:
```python
grounding, philosophy, completeness = await asyncio.gather(
    grounding_task, philosophy_task, completeness_task
)
```

**Your tool**: Identify independent operations and parallelize them.

### 4. External Tool Integration

**Why**: Leverage existing tools (repomix) instead of reimplementing.

**How we did it**:
```python
subprocess.run(["npx", "repomix@latest", ...])
```

**Your tool**: Don't reinvent wheels - use subprocess for external tools.

## Step-by-Step Creation Process

### Step 1: Define Your Pipeline

Start with the stages your analysis needs:

```python
# Our pipeline stages:
stages = [
    "process_repositories",    # Input processing
    "analyze",                 # Core analysis
    "generate_opportunities",  # Generation
    "review",                 # Quality checks
    "human_feedback",         # User input
    "apply_feedback"          # Iteration
]
```

### Step 2: Create Module Structure

Each stage gets its own module:

```
tool_name/
├── processor/         # Input processing
├── analyzer/         # Core analysis
├── generator/        # Output generation
├── reviewers/        # Quality checks
│   ├── accuracy/
│   ├── alignment/
│   └── completeness/
├── interface/        # Human interaction
├── orchestrator/     # Pipeline coordination
└── state.py         # State management
```

### Step 3: Implement Core Modules

Start with simplest modules first:

```python
# Example: Simple processor module
class Processor:
    async def process(self, input_path: Path) -> ProcessedData:
        # Your processing logic
        return processed_data
```

### Step 4: Add Review Modules

Create focused reviewers:

```python
class AccuracyReviewer:
    async def review(self, data: Any, original: Any) -> ReviewResult:
        # Check accuracy against original
        # Return structured review result
```

### Step 5: Implement Orchestrator

Coordinate all modules:

```python
class Orchestrator:
    async def run(self):
        # Load or resume state
        if self.state.stage == "initialized":
            await self._process()
        
        if self.state.stage == "processed":
            await self._analyze()
            
        # ... continue through stages
```

### Step 6: Add Human Interface

Make results actionable:

```python
class Interface:
    def present_results(self, results):
        # Display results clearly
        # Collect structured feedback
        return user_feedback
```

## Patterns to Reuse

### Feedback Loop Pattern

```python
while stage in ["review_stage", "feedback_applied"]:
    if not self.state.increment_iteration():
        break  # Max iterations reached
        
    # Run reviews
    reviews = await self._run_reviews()
    
    # Get user feedback
    feedback = await self._get_feedback()
    
    if feedback["approved"]:
        break
        
    # Apply feedback
    await self._apply_feedback(feedback)
```

### Checkpoint Pattern

```python
async def process_items(self, items):
    for item in items:
        if item in self.state.processed:
            continue  # Skip if already done
            
        result = await self._process_one(item)
        
        # Save immediately
        self.state.processed.append(item)
        self.state.results.append(result)
        self.state.save()
```

### Parallel Review Pattern

```python
# Run independent reviews in parallel
review_tasks = [
    reviewer.review(data)
    for reviewer in self.reviewers
]
reviews = await asyncio.gather(*review_tasks)
```

## Using the CCSDK Toolkit

This tool is built on `amplifier.ccsdk_toolkit`:

### Defensive LLM Handling

```python
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

# Safely parse LLM responses
parsed = parse_llm_json(llm_response)
```

### Retry with Feedback

```python
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback

result = await retry_with_feedback(
    func=llm_query_function,
    prompt=prompt,
    max_retries=3
)
```

### File I/O with Retry

```python
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry

write_json_with_retry(data, path)  # Handles cloud sync issues
```

## Creating Your Own Tool

### 1. Start with the Template

Use `amplifier/ccsdk_toolkit/templates/tool_template.py` as your starting point.

### 2. Define Your Contract

What does your tool do?
- **Inputs**: What data/files does it need?
- **Processing**: What analysis/transformation?
- **Outputs**: What does it produce?
- **Iteration**: Does it need feedback loops?

### 3. Design Your Pipeline

Break complex analysis into stages:
- Each stage should have one clear purpose
- Stages should be independently testable
- Consider what can run in parallel

### 4. Implement Incrementally

- Start with simplest stage
- Test each stage in isolation
- Add state management early
- Integrate stages one at a time

### 5. Add Quality Checks

- What could go wrong?
- How to verify correctness?
- What needs human review?

### 6. Test with Real Data

- Start with small examples
- Handle edge cases
- Test interruption/resume
- Verify feedback loops work

## Tips from Building This Tool

### What Worked Well

1. **Isolated contexts** - Prevented hallucination in reviews
2. **State management** - Could interrupt 30-min analyses without losing work
3. **Parallel reviews** - 3x faster than sequential
4. **Structured feedback** - Clear options for users

### Challenges and Solutions

1. **Context window limits** → Added file filtering options
2. **Generic suggestions** → Grounding reviewer catches these
3. **Infinite refinement** → Max iteration limit
4. **Unclear feedback** → Structured choice menu

### Key Learnings

- **Start simple**: Basic version first, then add reviews
- **Test early**: Real repositories revealed issues quickly
- **User experience matters**: Clear progress indicators essential
- **Defensive coding**: Always assume LLM output needs cleaning

## Your Next Steps

1. **Identify a pattern** in your workflow that could be automated
2. **Break it into stages** that can be implemented separately
3. **Use this tool's structure** as a template
4. **Start with core functionality**, add reviews later
5. **Share your creation** with the community!

## Resources

- [CCSDK Developer Guide](../../amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md)
- [Tool Template](../../amplifier/ccsdk_toolkit/templates/tool_template.py)
- [Blog Writer Example](../blog_writer/) - Simpler feedback loop example
- [Amplifier Philosophy](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md)

---

**Remember**: The power comes from orchestrating simple modules into sophisticated workflows. Each module does one thing well, and the orchestrator combines them into something powerful.
