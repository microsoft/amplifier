# Principle #45 - Prompt Design Patterns

## Plain-Language Definition

Prompt design patterns are reusable templates and structures for composing prompts that consistently produce better AI responses. Like design patterns in software engineering, these patterns provide proven solutions to common prompting challenges, from simple instructions to complex multi-step reasoning.

## Why This Matters for AI-First Development

When AI agents build systems, they rely on prompts to communicate with LLMs at every level—generating code, analyzing requirements, debugging issues, and making architectural decisions. Without structured prompt patterns, these interactions become unpredictable, token-inefficient, and error-prone. A poorly structured prompt might cause an agent to generate buggy code, miss critical requirements, or consume excessive tokens retrying failed operations.

Prompt design patterns provide three critical benefits for AI-driven development:

1. **Predictable reasoning quality**: Structured patterns guide LLMs through complex reasoning tasks with consistent results. An agent using Chain-of-Thought patterns for code generation will show its reasoning steps, making errors easier to catch and correct.

2. **Token efficiency**: Well-designed patterns maximize output quality per token spent. The power law relationship between prompt tokens and quality means finding the "maximum ROI zone" is critical—too few tokens yield poor results, too many hit diminishing returns or context rot.

3. **Composable complexity**: Patterns can be combined to handle increasingly complex tasks. An agent might use ReAct (Reasoning + Acting) to debug a system, Tree-of-Thought to explore architectural options, and few-shot examples to generate implementation code—all working together systematically.

Without these patterns, AI-first systems waste resources on trial-and-error prompting, produce inconsistent results across operations, and struggle with tasks requiring multi-step reasoning. An agent generating database migrations without prompt patterns might create syntax errors, miss edge cases, or fail to maintain idempotency. The same agent using established patterns produces reliable, well-reasoned code consistently.

## Implementation Approaches

### 1. **Zero-Shot Patterns (Atomic Prompts)**

The simplest pattern: a single, clear instruction with constraints and output format.

**Structure**: `[TASK] + [CONSTRAINTS] + [OUTPUT FORMAT]`

```python
def zero_shot_prompt(task: str, constraints: list[str], format: str) -> str:
    """Build a zero-shot prompt with clear structure."""
    prompt_parts = [
        f"Task: {task}",
        "",
        "Constraints:",
        *[f"- {c}" for c in constraints],
        "",
        f"Output format: {format}"
    ]
    return "\n".join(prompt_parts)

# Example usage
prompt = zero_shot_prompt(
    task="Generate a Python function to validate email addresses",
    constraints=[
        "Use regex for validation",
        "Include type hints",
        "Add docstring with examples",
        "Handle edge cases (empty string, None)"
    ],
    format="Complete Python function with no placeholders"
)
```

**When to use**: Simple, well-defined tasks where the LLM has sufficient training data. Good for code generation, text transformation, and straightforward analysis.

### 2. **Few-Shot Patterns (Examples as Context)**

Provide 2-5 examples demonstrating the desired behavior before asking for new output.

```python
def few_shot_prompt(
    task: str,
    examples: list[dict[str, str]],
    new_input: str
) -> str:
    """Build a few-shot prompt with examples."""
    prompt_parts = [f"Task: {task}", ""]

    for i, ex in enumerate(examples, 1):
        prompt_parts.extend([
            f"Example {i}:",
            f"Input: {ex['input']}",
            f"Output: {ex['output']}",
            ""
        ])

    prompt_parts.extend([
        "Now your turn:",
        f"Input: {new_input}",
        "Output:"
    ])

    return "\n".join(prompt_parts)

# Example usage
prompt = few_shot_prompt(
    task="Convert function names from snake_case to camelCase",
    examples=[
        {"input": "get_user_data", "output": "getUserData"},
        {"input": "calculate_total_price", "output": "calculateTotalPrice"},
        {"input": "is_valid_email", "output": "isValidEmail"}
    ],
    new_input="create_database_connection"
)
```

**When to use**: Tasks requiring specific formatting, style matching, or domain-specific conventions. Essential when zero-shot produces inconsistent results.

### 3. **Chain-of-Thought Patterns**

Explicitly request step-by-step reasoning before the final answer. Dramatically improves accuracy on complex tasks.

```python
def chain_of_thought_prompt(problem: str, zero_shot: bool = True) -> str:
    """Build a chain-of-thought prompt for complex reasoning."""
    if zero_shot:
        # Zero-shot CoT: just add "Let's think step by step"
        return f"{problem}\n\nLet's think step by step:"
    else:
        # Few-shot CoT: include example reasoning
        return f"""Solve this problem by breaking it down into steps.

Example:
Problem: If a train travels 60 miles in 2 hours, what is its average speed?
Reasoning:
Step 1: Identify the formula: speed = distance / time
Step 2: Plug in values: speed = 60 miles / 2 hours
Step 3: Calculate: speed = 30 miles per hour
Answer: 30 mph

Now solve this problem:
{problem}

Reasoning:"""
```

**When to use**: Math problems, logical reasoning, code debugging, architectural decisions—anything requiring multi-step thinking.

### 4. **ReAct Pattern (Reasoning + Acting)**

Interleave reasoning traces with tool-using actions. The agent thinks, acts, observes, and adjusts iteratively.

```python
def react_prompt_template(question: str, tools_available: list[str]) -> str:
    """Build a ReAct prompt for agent operations."""
    return f"""Answer this question using available tools.

Question: {question}

Available tools: {', '.join(tools_available)}

Use this format:
Thought: [your reasoning about what to do next]
Action: [tool to use with parameters]
Observation: [result from tool]
... (repeat Thought/Action/Observation as needed)
Thought: [final reasoning]
Answer: [final answer to the question]

Begin:"""

# Example usage for AI agent
prompt = react_prompt_template(
    question="What is the current test coverage for the auth module?",
    tools_available=[
        "run_command(cmd)",
        "read_file(path)",
        "search_codebase(pattern)"
    ]
)
```

**When to use**: Multi-step tasks requiring external information or tools. Perfect for debugging, system analysis, and research tasks.

### 5. **Tree-of-Thought Pattern**

Explore multiple reasoning paths in parallel, evaluate them, and choose the best solution.

```python
def tree_of_thought_prompt(problem: str, num_paths: int = 3) -> str:
    """Build a Tree-of-Thought prompt for exploration."""
    return f"""Solve this problem by exploring multiple approaches.

Problem: {problem}

Instructions:
1. Generate {num_paths} different solution approaches
2. For each approach, think through the steps
3. Evaluate each approach (sure/maybe/impossible)
4. Choose the best approach
5. Execute the chosen approach step-by-step

Format:
Approach 1: [description]
Steps: [reasoning steps]
Evaluation: [sure/maybe/impossible]

Approach 2: [description]
Steps: [reasoning steps]
Evaluation: [sure/maybe/impossible]

Approach 3: [description]
Steps: [reasoning steps]
Evaluation: [sure/maybe/impossible]

Best approach: [chosen approach]
Execution: [step-by-step solution]
Final answer: [result]

Begin:"""

# Example usage
prompt = tree_of_thought_prompt(
    problem="Design a caching strategy for our API that handles 10K requests/sec",
    num_paths=3
)
```

**When to use**: Complex problems with multiple valid solutions requiring exploration. Architecture decisions, optimization problems, strategic planning.

### 6. **Self-Consistency Pattern**

Generate multiple reasoning paths independently, then take the majority vote for the final answer.

```python
def self_consistency_prompt(problem: str, num_samples: int = 5) -> list[str]:
    """Generate multiple independent reasoning paths."""
    cot_prompt = f"{problem}\n\nLet's think step by step:"

    # Generate multiple independent solutions
    prompts = [cot_prompt for _ in range(num_samples)]

    return prompts

def aggregate_self_consistency_results(results: list[str]) -> str:
    """Aggregate multiple reasoning paths to find consensus."""
    # Extract final answers from each reasoning path
    answers = [extract_final_answer(r) for r in results]

    # Find most common answer
    from collections import Counter
    answer_counts = Counter(answers)
    most_common = answer_counts.most_common(1)[0]

    return f"Consensus answer (appeared {most_common[1]}/{len(results)} times): {most_common[0]}"
```

**When to use**: High-stakes decisions requiring validation, numerical calculations where errors are costly, any task where confidence matters.

## Good Examples vs Bad Examples

### Example 1: Code Generation Task

**Good:**
```python
# Using zero-shot with clear structure
prompt = """Task: Generate a Python function to parse ISO 8601 timestamps.

Requirements:
- Handle both date-only and datetime formats
- Return Python datetime object
- Include type hints
- Add comprehensive docstring
- Handle invalid input gracefully with ValueError

Output format: Complete, working Python function with no TODO comments.

Function signature: def parse_iso8601(timestamp: str) -> datetime:"""
```

**Bad:**
```python
# Vague, unstructured prompt
prompt = "Write a function to parse timestamps"
```

**Why It Matters:** The good example provides clear constraints, expected behavior, and output format. This guides the LLM to generate production-ready code. The bad example will produce inconsistent, incomplete results requiring multiple iterations and manual fixes.

### Example 2: Debugging Complex Issue

**Good:**
```python
# Using ReAct pattern for systematic debugging
prompt = """Debug why our payment processing service is timing out.

Available tools:
- check_logs(service, time_range)
- check_metrics(metric_name, time_range)
- check_database_connections()
- run_query(sql)

Use this format:
Thought: [reasoning about what to investigate]
Action: [tool to use]
Observation: [result]
... repeat as needed

Question: Why are payments timing out after 2pm?

Begin:"""
```

**Bad:**
```python
# Single-shot prompt without structure
prompt = "Why are payments timing out? Check the logs and tell me what's wrong."
```

**Why It Matters:** The ReAct pattern guides the agent through systematic investigation with explicit reasoning traces. The bad example expects the LLM to know what tools are available and how to use them, leading to hallucinated commands or incomplete analysis.

### Example 3: Architecture Decision

**Good:**
```python
# Using Tree-of-Thought for exploration
prompt = """Design a data retention strategy for user analytics events.

Context:
- 100M events per day
- Legal requirement: keep 90 days
- Query patterns: 90% of queries are last 7 days
- Storage cost: $0.023 per GB-month

Generate 3 different approaches:
1. Approach name
2. Architecture overview
3. Estimated costs
4. Trade-offs
5. Implementation complexity (low/medium/high)
6. Evaluation (recommend/consider/not recommended)

After exploring all approaches, recommend the best one with justification.

Begin:"""
```

**Bad:**
```python
# No structure for comparison
prompt = "What's the best way to store analytics events?"
```

**Why It Matters:** Complex decisions benefit from structured exploration of alternatives. The good example forces comparison of multiple approaches with explicit criteria. The bad example produces a single solution without considering alternatives or trade-offs.

### Example 4: API Response Formatting

**Good:**
```python
# Using few-shot for consistent formatting
prompt = """Format API error responses according to our standard.

Example 1:
Error: Invalid email format
Output: {"error": "validation_error", "message": "Invalid email format", "field": "email", "code": 400}

Example 2:
Error: User not found
Output: {"error": "not_found", "message": "User not found", "resource": "user", "code": 404}

Example 3:
Error: Rate limit exceeded
Output: {"error": "rate_limit", "message": "Rate limit exceeded", "retry_after": 60, "code": 429}

Now format this error:
Error: Database connection timeout

Output:"""
```

**Bad:**
```python
# Zero-shot without examples
prompt = "Format this error message in JSON: Database connection timeout"
```

**Why It Matters:** Few-shot learning ensures consistent structure across all error responses. The bad example will produce arbitrary JSON structures that don't match the API's conventions, breaking client code.

### Example 5: Code Review Comments

**Good:**
```python
# Using Chain-of-Thought for thorough analysis
prompt = """Review this code change and provide feedback.

Code:
{code_diff}

Think through this systematically:

Step 1: What is this code trying to accomplish?
Step 2: Are there any bugs or logic errors?
Step 3: Are there security concerns?
Step 4: Is the code idempotent and safe to retry?
Step 5: Does it follow our style guide?
Step 6: What tests should be added?

After analyzing all aspects, provide:
1. Summary (approve/request changes/needs discussion)
2. Critical issues (if any)
3. Suggestions for improvement
4. Test coverage recommendations

Begin analysis:"""
```

**Bad:**
```python
# No structure for comprehensive review
prompt = f"Review this code:\n{code_diff}"
```

**Why It Matters:** Code review requires systematic evaluation of multiple concerns. The structured prompt ensures nothing is overlooked. The bad example produces surface-level feedback that might miss security issues, race conditions, or testing gaps.

## Related Principles

- **[Principle #3 - Prompt Engineering as Core Skill](../people/03-prompt-engineering-core-skill.md)** - Prompt design patterns are the practical foundation of prompt engineering expertise. Understanding these patterns is essential for effective AI collaboration.

- **[Principle #14 - Context Management Strategies](../process/14-context-management-strategies.md)** - Prompt patterns must be designed with context window constraints in mind. Few-shot examples consume tokens that could be used for other context.

- **[Principle #20 - Token-Aware Design Patterns](20-token-aware-design-patterns.md)** - Different prompt patterns have different token efficiency profiles. Zero-shot is most efficient, Tree-of-Thought most expensive. Choose based on task complexity and token budgets.

- **[Principle #33 - Structured Outputs by Default](33-structured-outputs-by-default.md)** - Prompt patterns should specify output structure explicitly. ReAct and Tree-of-Thought patterns inherently produce structured outputs by design.

- **[Principle #15 - Iterative Refinement Workflows](../process/15-iterative-refinement-workflows.md)** - Prompt patterns support iteration by making LLM reasoning explicit. Chain-of-Thought outputs show where reasoning went wrong, enabling targeted refinement.

- **[Principle #28 - API-First Integration Layer](28-api-first-integration-layer.md)** - ReAct patterns enable agents to use APIs systematically. The Thought/Action/Observation structure maps naturally to API request/response cycles.

## Common Pitfalls

1. **Using Complex Patterns for Simple Tasks**
   - Example: Using Tree-of-Thought with multiple reasoning paths to capitalize a string
   - Impact: Wasted tokens (potentially 10x cost), slower responses, no quality improvement
   - Avoid: Match pattern complexity to task complexity. Use zero-shot for simple tasks, reserve advanced patterns for genuinely complex problems

2. **Inconsistent Pattern Structure Within a System**
   - Example: Some prompts use Chain-of-Thought with "Step 1, Step 2..." while others use "First, then, finally..."
   - Impact: LLM has to adapt to different conventions, reducing reliability and making results harder to parse
   - Avoid: Standardize on specific pattern templates across your system. Create reusable prompt-building functions

3. **Forgetting to Specify Output Format**
   - Example: "Analyze this code for security issues" without specifying JSON, markdown, or plain text format
   - Impact: Unparseable outputs that require regex or brittle string manipulation to extract
   - Avoid: Always include explicit output format in your pattern. "Output format: JSON with keys 'summary', 'issues', 'severity'"

4. **Too Many Few-Shot Examples**
   - Example: Providing 15 examples of error message formatting, consuming 2000 tokens
   - Impact: Context window filled with examples instead of actual content, hitting the "diminishing returns" zone
   - Avoid: 2-5 examples usually sufficient. More examples don't improve quality linearly but do consume tokens linearly

5. **Missing Example Diversity in Few-Shot**
   - Example: All few-shot examples show successful cases, none show edge cases or error handling
   - Impact: LLM only learns happy-path behavior, fails on edge cases
   - Avoid: Include diverse examples covering edge cases, error conditions, and boundary situations

6. **Chain-of-Thought Without Validation**
   - Example: Generating reasoning steps but not verifying the logic before using the conclusion
   - Impact: LLMs can produce coherent-sounding but incorrect reasoning. Following bad reasoning leads to bad code
   - Avoid: Parse and validate reasoning steps. Check that conclusions follow logically from premises

7. **ReAct Pattern Without Proper Tool Descriptions**
   - Example: "Available tools: search, analyze, fix" without describing parameters or return types
   - Impact: LLM hallucinates tool parameters or misuses tools, causing errors
   - Avoid: Provide complete tool signatures with parameter types and return value descriptions

8. **Tree-of-Thought Without Evaluation Criteria**
   - Example: "Generate 3 approaches" without specifying how to evaluate them
   - Impact: All approaches rated equally, no basis for choosing one
   - Avoid: Explicitly state evaluation criteria (cost, complexity, performance, maintainability)

9. **Self-Consistency Without Aggregation Strategy**
   - Example: Generating 5 different solutions but not specifying how to combine them
   - Impact: Unclear which answer to trust when results conflict
   - Avoid: Define aggregation method upfront (majority vote, weighted average, confidence-based selection)

10. **Ignoring the Token-Quality Power Law**
    - Example: Starting with minimal prompt, seeing poor quality, adding 5000 tokens of context
    - Impact: Moving from "too few" directly to "diminishing returns" without finding the ROI sweet spot
    - Avoid: Add tokens incrementally. Test quality after each addition. Stop when quality plateaus

## Tools & Frameworks

### Prompt Engineering Libraries
- **LangChain**: Comprehensive framework with built-in prompt templates for Chain-of-Thought, ReAct, and more. Includes prompt composition utilities and output parsers.
- **Guidance**: Microsoft's library for controlling LLM generation with structured patterns. Excellent for ensuring output format compliance.
- **LMQL**: Query language for LLMs that makes prompt patterns first-class constructs with type safety.
- **PromptSource**: Collection of crowd-sourced prompt templates covering common NLP tasks.

### Agent Frameworks with Pattern Support
- **AutoGPT**: Implements ReAct pattern for autonomous agents with tool use
- **BabyAGI**: Task-driven autonomous agent using Chain-of-Thought reasoning
- **LangGraph**: Graph-based orchestration of multi-step reasoning patterns
- **Semantic Kernel**: Microsoft's SDK for building AI agents with prompt pattern abstractions

### Testing & Validation Tools
- **PromptFoo**: Automated testing for prompt patterns with quality metrics
- **OpenAI Evals**: Framework for evaluating prompt effectiveness across datasets
- **DeepEval**: LLM evaluation framework specifically for prompt pattern validation
- **Trulens**: Observability for LLM applications including prompt pattern analysis

### Development Tools
- **Prompt Flow**: Visual designer for building and testing prompt patterns
- **Humanloop**: Collaborative prompt engineering platform with version control
- **Weights & Biases**: Experiment tracking for prompt pattern optimization
- **LangSmith**: Debugging and monitoring for LangChain-based prompt patterns

### Research & Examples
- **Prompting Guide (promptingguide.ai)**: Comprehensive reference for prompt patterns with examples
- **Learn Prompting**: Interactive tutorials on major prompting techniques
- **Anthropic Prompt Library**: Curated collection of effective prompt patterns
- **OpenAI Cookbook**: Practical examples of prompting patterns in production

## Implementation Checklist

When implementing prompt design patterns, ensure:

- [ ] Pattern complexity matches task complexity (zero-shot for simple, advanced for complex)
- [ ] All prompts explicitly specify output format (JSON schema, markdown structure, etc.)
- [ ] Few-shot examples are diverse and cover edge cases (not just happy paths)
- [ ] Chain-of-Thought prompts validate reasoning steps before using conclusions
- [ ] ReAct patterns include complete tool descriptions with parameters and return types
- [ ] Tree-of-Thought patterns define explicit evaluation criteria for comparing approaches
- [ ] Self-consistency patterns specify aggregation method for multiple samples
- [ ] Prompt templates are reusable functions, not copy-pasted strings
- [ ] Token counts are measured and optimized against quality metrics
- [ ] Pattern structure is consistent across the entire system
- [ ] Examples use current best practices (not outdated patterns from old documentation)
- [ ] Error handling is specified for each pattern (what happens when reasoning fails?)
- [ ] Patterns are versioned and changes are tracked (like API versions)
- [ ] Documentation explains when to use each pattern (decision tree for developers)

## Metadata

**Category**: Technology
**Principle Number**: 45
**Related Patterns**: Template Method, Strategy, Chain of Responsibility, Composite
**Prerequisites**: Basic understanding of LLM capabilities, token budgets, structured output parsing
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
