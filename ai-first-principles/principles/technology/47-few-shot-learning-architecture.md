# Principle #47 - Few-Shot Learning Architecture

## Plain-Language Definition

Few-shot learning architecture is the systematic design and curation of examples that teach AI models how to perform tasks through demonstration rather than explicit instruction. It's the practice of showing the model 2-5 high-quality examples that establish patterns, formats, and expectations, enabling the model to generalize to new inputs.

## Why This Matters for AI-First Development

When AI agents generate code, analyze systems, or automate workflows, they need clear patterns to follow. Few-shot examples act as executable specifications—they show not just what to do, but how to do it. Unlike traditional documentation that describes behavior in prose, few-shot examples demonstrate actual input-output patterns that models can directly replicate and adapt.

Few-shot learning architecture provides three critical benefits for AI-driven development:

1. **Precision through demonstration**: A single well-crafted example often communicates requirements more clearly than paragraphs of description. AI agents can see exact formatting, error handling patterns, edge case behavior, and output structure in concrete form rather than inferring from abstract instructions.

2. **Consistency across operations**: When multiple AI agents or operations need to produce similar outputs, few-shot examples establish a shared template. This ensures API responses follow the same structure, code follows the same patterns, and error messages use consistent formats—without explicit rules for every decision.

3. **Reduced hallucination and drift**: Models are more likely to stay grounded when they have concrete examples to anchor their responses. Few-shot examples constrain the solution space, reducing the likelihood of the model inventing non-existent APIs, fabricating data structures, or drifting into off-topic responses.

Without thoughtful few-shot architecture, AI systems become unpredictable. An agent might generate code in wildly different styles depending on minor prompt variations. It might invent plausible-sounding but incorrect API patterns. It might struggle with edge cases because it never saw examples of how to handle them. These failures compound in AI-first systems where one agent's output becomes another agent's input—poor example selection early in a pipeline cascades into system-wide inconsistency.

## Implementation Approaches

### 1. **Static Example Banks**

Create curated collections of high-quality examples organized by task type, complexity, and domain. Store these in version-controlled repositories where they can be tested, reviewed, and evolved.

When to use: For stable, well-understood tasks where the pattern doesn't change frequently (API response formats, code style conventions, data transformation patterns).

```python
EXAMPLE_BANK = {
    "error_handling": [
        {
            "input": "Division by zero in calculate_average",
            "output": {
                "error": "ValidationError",
                "message": "Cannot calculate average: denominator is zero",
                "suggestion": "Ensure input array is non-empty before calling calculate_average"
            }
        },
        {
            "input": "Null pointer in database connection",
            "output": {
                "error": "ConnectionError",
                "message": "Database connection is null",
                "suggestion": "Verify database service is running and credentials are correct"
            }
        }
    ],
    "api_response": [
        {
            "input": "User registration successful",
            "output": {
                "status": "success",
                "data": {"user_id": "usr_abc123", "email": "user@example.com"},
                "meta": {"timestamp": "2025-09-30T10:00:00Z"}
            }
        }
    ]
}

def get_examples(task_type: str, count: int = 3) -> list[dict]:
    """Retrieve examples from the bank for a given task type."""
    return EXAMPLE_BANK.get(task_type, [])[:count]
```

### 2. **Dynamic Example Selection**

Select examples at runtime based on similarity to the current input. Use embeddings or keyword matching to find the most relevant demonstrations from a larger pool.

When to use: When inputs vary significantly and generic examples don't capture the diversity of cases (domain-specific code generation, natural language tasks with wide vocabulary, context-dependent formatting).

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class DynamicExampleSelector:
    def __init__(self, example_pool: list[dict]):
        self.example_pool = example_pool
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.example_embeddings = self.model.encode(
            [ex["input"] for ex in example_pool]
        )

    def select_examples(self, query: str, k: int = 3) -> list[dict]:
        """Select k most similar examples to the query."""
        query_embedding = self.model.encode([query])[0]
        similarities = np.dot(self.example_embeddings, query_embedding)
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        return [self.example_pool[i] for i in top_k_indices]
```

### 3. **Stratified Example Coverage**

Ensure examples cover the full range of complexity, edge cases, and variations. Include simple cases, complex cases, error cases, and boundary conditions.

When to use: For tasks where edge cases are critical and the model needs to handle diverse scenarios (data validation, security-sensitive operations, multi-step workflows).

```python
def build_stratified_examples(domain: str) -> list[dict]:
    """Build examples that cover complexity spectrum."""
    return [
        # Simple baseline
        {"complexity": "simple", "input": "2 + 2", "output": "4"},

        # Standard case
        {"complexity": "standard", "input": "(5 * 3) + 2", "output": "17"},

        # Edge case: division by zero
        {"complexity": "edge", "input": "10 / 0",
         "output": "Error: Division by zero"},

        # Complex nested expression
        {"complexity": "complex", "input": "((2 + 3) * (4 - 1)) / (6 + 2)",
         "output": "1.875"},

        # Boundary: very large numbers
        {"complexity": "boundary", "input": "999999 * 999999",
         "output": "999998000001"}
    ]
```

### 4. **Chain-of-Thought Examples**

Structure examples to expose reasoning steps, not just input-output pairs. Show intermediate calculations, decision points, and the path to the final answer.

When to use: For complex tasks requiring multi-step reasoning (debugging, optimization, design decisions, mathematical problem-solving).

```python
COT_EXAMPLES = [
    {
        "input": "Find the bug in this code: `for i in range(len(arr)): arr[i+1] = arr[i] * 2`",
        "thinking": [
            "1. Loop iterates from i=0 to i=len(arr)-1",
            "2. Inside loop, accessing arr[i+1] which goes up to arr[len(arr)]",
            "3. This causes IndexError when i = len(arr)-1",
            "4. Should be arr[i] = arr[i] * 2, not arr[i+1]"
        ],
        "output": "Bug: Array index out of bounds. Change arr[i+1] to arr[i]."
    }
]
```

### 5. **Format-First Example Design**

Create examples that establish formatting conventions first, then vary the content. This teaches models the structure before introducing complexity.

When to use: For structured output generation (JSON APIs, configuration files, code templates, documentation).

```python
FORMAT_EXAMPLES = [
    {
        "description": "User authentication endpoint",
        "example": {
            "endpoint": "/api/v1/auth/login",
            "method": "POST",
            "request": {"email": "user@example.com", "password": "***"},
            "response": {"token": "jwt_token_here", "expires_in": 3600}
        }
    },
    {
        "description": "User profile retrieval endpoint",
        "example": {
            "endpoint": "/api/v1/users/{id}",
            "method": "GET",
            "request": None,
            "response": {"id": "usr_123", "name": "John Doe", "email": "john@example.com"}
        }
    }
]
```

### 6. **Adaptive Example Pruning**

Start with a rich set of examples, then remove those that don't improve performance. Measure which examples contribute to accuracy and which add token cost without benefit.

When to use: When optimizing for cost and latency after establishing baseline accuracy (production optimization, high-volume operations, cost-sensitive applications).

```python
def evaluate_example_contribution(
    task: str,
    example_set: list[dict],
    test_cases: list[dict]
) -> dict[int, float]:
    """Measure each example's contribution to accuracy."""
    contributions = {}

    for i in range(len(example_set)):
        # Test with all examples except i
        reduced_set = example_set[:i] + example_set[i+1:]
        accuracy = measure_accuracy(task, reduced_set, test_cases)
        contributions[i] = accuracy

    return contributions

def prune_examples(examples: list[dict], contributions: dict[int, float],
                   baseline_accuracy: float, threshold: float = 0.95) -> list[dict]:
    """Remove examples that don't significantly impact accuracy."""
    return [
        ex for i, ex in enumerate(examples)
        if contributions[i] >= baseline_accuracy * threshold
    ]
```

## Good Examples vs Bad Examples

### Example 1: Code Generation Task

**Good:**
```python
# Few-shot examples showing style, error handling, and docstrings
EXAMPLES = [
    {
        "task": "Write a function to validate email",
        "code": '''def validate_email(email: str) -> bool:
    """Validate email format using regex.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))'''
    },
    {
        "task": "Write a function to parse JSON safely",
        "code": '''def parse_json(json_string: str) -> dict | None:
    """Parse JSON string with error handling.

    Args:
        json_string: JSON-formatted string

    Returns:
        Parsed dictionary or None if parsing fails
    """
    import json
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None'''
    }
]
```

**Bad:**
```python
# Examples that don't establish clear patterns
EXAMPLES = [
    {
        "task": "Write a function",
        "code": "def func(x): return x * 2"  # No docstring, unclear purpose
    },
    {
        "task": "Another function",
        "code": """
        def process(data):
            # TODO: implement this
            pass
        """  # Incomplete example
    }
]
```

**Why It Matters:** Good examples establish conventions for documentation, type hints, error handling, and code organization. Bad examples teach inconsistent patterns—the model learns that sometimes you document, sometimes you don't, leading to unpredictable output quality.

### Example 2: API Response Formatting

**Good:**
```python
# Consistent response structure across different scenarios
RESPONSE_EXAMPLES = [
    {
        "scenario": "Success with data",
        "response": {
            "status": "success",
            "data": {"user_id": "usr_123", "name": "Alice"},
            "meta": {"timestamp": "2025-09-30T10:00:00Z", "version": "1.0"}
        }
    },
    {
        "scenario": "Error with details",
        "response": {
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Email address is invalid",
                "field": "email"
            },
            "meta": {"timestamp": "2025-09-30T10:00:01Z", "version": "1.0"}
        }
    },
    {
        "scenario": "Success with pagination",
        "response": {
            "status": "success",
            "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
            "pagination": {"page": 1, "total_pages": 10, "total_items": 95},
            "meta": {"timestamp": "2025-09-30T10:00:02Z", "version": "1.0"}
        }
    }
]
```

**Bad:**
```python
# Inconsistent response structures
RESPONSE_EXAMPLES = [
    {"user": {"id": "usr_123"}},  # No status or meta
    {"status": "ok", "result": {"id": 456}},  # Different key names
    {"error": "Invalid input"},  # No structure, just string
]
```

**Why It Matters:** Consistent response structures allow client code to reliably parse responses. Inconsistent examples teach the model that anything goes, resulting in unpredictable API behavior that breaks client integrations.

### Example 3: Example Selection Strategy

**Good:**
```python
def select_diverse_examples(query: str, pool: list[dict], k: int = 3) -> list[dict]:
    """Select examples that cover different aspects of the task."""
    # Get most similar example
    most_similar = find_most_similar(query, pool)

    # Get examples covering edge cases
    edge_cases = [ex for ex in pool if ex.get("is_edge_case", False)]

    # Get example with error handling
    error_example = next((ex for ex in pool if "error" in ex["output"]), None)

    # Combine for diversity
    selected = [most_similar]
    if edge_cases:
        selected.append(edge_cases[0])
    if error_example and error_example not in selected:
        selected.append(error_example)

    return selected[:k]
```

**Bad:**
```python
def select_examples(query: str, pool: list[dict], k: int = 3) -> list[dict]:
    """Just return the first k examples."""
    return pool[:k]  # Always returns same examples regardless of query
```

**Why It Matters:** Dynamic selection based on query similarity and diversity improves model performance by providing relevant demonstrations. Static selection wastes context window on irrelevant examples and may miss critical patterns the query needs.

### Example 4: Token Budget Management

**Good:**
```python
def build_efficient_prompt(
    instruction: str,
    examples: list[dict],
    query: str,
    max_tokens: int = 4000
) -> str:
    """Build prompt that fits within token budget."""
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")

    # Reserve tokens for instruction and query
    instruction_tokens = len(enc.encode(instruction))
    query_tokens = len(enc.encode(query))
    available_for_examples = max_tokens - instruction_tokens - query_tokens - 500  # Buffer

    # Add examples until budget exhausted
    prompt_parts = [instruction]
    examples_used = 0

    for example in examples:
        example_str = format_example(example)
        example_tokens = len(enc.encode(example_str))

        if example_tokens <= available_for_examples:
            prompt_parts.append(example_str)
            available_for_examples -= example_tokens
            examples_used += 1
        else:
            break

    prompt_parts.append(f"Now solve: {query}")
    return "\n\n".join(prompt_parts)
```

**Bad:**
```python
def build_prompt(instruction: str, examples: list[dict], query: str) -> str:
    """Build prompt with all examples regardless of token count."""
    prompt = instruction + "\n\n"

    # Include all examples even if they exceed context window
    for ex in examples:
        prompt += format_example(ex) + "\n\n"

    prompt += f"Now solve: {query}"
    return prompt
```

**Why It Matters:** Context windows have hard limits. Naively including all examples can exceed limits, causing truncation or errors. Token-aware prompt building ensures the most valuable examples fit within the budget, maintaining quality while respecting constraints.

### Example 5: Chain-of-Thought Formatting

**Good:**
```python
COT_EXAMPLES = [
    {
        "input": "Optimize query: SELECT * FROM users WHERE active = 1 AND created_at > '2025-01-01'",
        "thinking": [
            "Step 1: Analyze current query structure",
            "- Full table scan on 'users' table",
            "- Two WHERE conditions (active and created_at)",
            "",
            "Step 2: Identify optimization opportunities",
            "- SELECT * retrieves all columns (wasteful if not all needed)",
            "- Likely missing index on (active, created_at) combination",
            "",
            "Step 3: Propose improvements",
            "- Create composite index: CREATE INDEX idx_users_active_created ON users(active, created_at)",
            "- Replace SELECT * with specific columns if possible",
        ],
        "output": "CREATE INDEX idx_users_active_created ON users(active, created_at);\nSELECT id, email, name FROM users WHERE active = 1 AND created_at > '2025-01-01';"
    }
]
```

**Bad:**
```python
COT_EXAMPLES = [
    {
        "input": "Optimize query: SELECT * FROM users WHERE active = 1",
        "output": "Add an index"  # No reasoning shown
    }
]
```

**Why It Matters:** Chain-of-thought examples teach models systematic reasoning processes. Without visible reasoning steps, models produce answers without showing their work, making it impossible to verify correctness or debug failures.

## Related Principles

- **[Principle #45 - Prompt Design Patterns](45-prompt-design-patterns.md)** - Few-shot examples are a core component of effective prompt patterns; they work together to create comprehensive prompting strategies

- **[Principle #46 - Context Window Management](46-context-window-management.md)** - Few-shot examples consume context window budget; careful example selection and pruning are essential for staying within limits

- **[Principle #48 - Chain-of-Thought Patterns](48-chain-of-thought-patterns.md)** - Chain-of-thought is a specific type of few-shot example that exposes reasoning; it's a specialized application of few-shot learning

- **[Principle #20 - Test-First AI Integration](20-test-first-ai-integration.md)** - Test cases serve as few-shot examples showing expected behavior; tests and examples are complementary ways to specify requirements

- **[Principle #25 - Observable Everything Everywhere](25-observable-everything-everywhere.md)** - Example selection benefits from observability data showing which examples correlate with better outcomes

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Validation metrics guide example curation by revealing which examples improve model performance

## Common Pitfalls

1. **Using Too Many Examples**: Adding more examples yields diminishing returns while consuming valuable context tokens. Beyond 5-7 examples, accuracy improvements plateau but costs continue rising.
   - How to avoid: Start with 3 examples, measure accuracy, add more only if improvement justifies token cost. Use example pruning techniques to identify non-contributing examples.

2. **Examples Too Similar**: Using near-identical examples wastes tokens without teaching the model anything new. Redundant examples provide no additional information about edge cases or variations.
   - How to avoid: Ensure examples cover different complexity levels, input formats, and edge cases. Use diversity metrics like cosine distance between example embeddings to verify coverage.

3. **Incomplete or Placeholder Examples**: Examples with "TODO" comments, incomplete logic, or missing error handling teach models to produce incomplete code. Models learn the pattern you show, including the incompleteness.
   - How to avoid: Every example must be production-quality code that actually runs. Test examples as part of your build process. Never include placeholder or sketch code.

4. **Inconsistent Formatting Across Examples**: When examples use different styles, naming conventions, or structures, models learn that inconsistency is acceptable. Output becomes unpredictable.
   - How to avoid: Establish and document formatting standards. Use linters and formatters on example code. Review examples for consistency during code review.

5. **Missing Edge Case Examples**: Only showing happy-path examples leaves models unprepared for errors, null values, empty inputs, or boundary conditions. Models assume inputs are always well-formed.
   - How to avoid: Include at least one example showing error handling, one with edge cases (empty lists, null values), and one with boundary conditions (max/min values).

6. **Static Examples for Dynamic Tasks**: Using the same examples regardless of input context means models don't see relevant demonstrations. A query about error handling gets examples about API design.
   - How to avoid: Implement dynamic example selection using similarity search or keyword matching. Select examples that match the current task's domain and complexity.

7. **Not Measuring Example Contribution**: Including examples without measuring their impact on accuracy means you may be wasting tokens on unhelpful demonstrations.
   - How to avoid: A/B test example sets. Measure accuracy with and without each example. Prune examples that don't improve outcomes above a threshold (e.g., 95% of baseline accuracy).

## Tools & Frameworks

### Example Selection & Embedding
- **[sentence-transformers](https://www.sbert.net/)**: Generate embeddings for semantic similarity-based example selection
- **[OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)**: High-quality embeddings for dynamic example retrieval
- **[Faiss](https://github.com/facebookresearch/faiss)**: Fast similarity search for retrieving relevant examples from large pools
- **[ChromaDB](https://www.trychroma.com/)**: Vector database for storing and querying example embeddings

### Prompt Engineering Frameworks
- **[LangChain Example Selectors](https://python.langchain.com/docs/modules/model_io/prompts/example_selectors/)**: Built-in tools for semantic similarity, max marginal relevance, and length-based selection
- **[Guidance](https://github.com/guidance-ai/guidance)**: Structured prompting with example-based templates
- **[DSPy](https://github.com/stanfordnlp/dspy)**: Automated few-shot example optimization through programming
- **[PromptTools](https://github.com/hegelai/prompttools)**: Testing framework for comparing different few-shot configurations

### Token Counting & Budgeting
- **[tiktoken](https://github.com/openai/tiktoken)**: Fast tokenizer for measuring prompt sizes and managing token budgets
- **[transformers tokenizers](https://huggingface.co/docs/transformers/main_classes/tokenizer)**: Tokenizers for various model families
- **[anthropic-tokenizer](https://docs.anthropic.com/claude/reference/how-to-count-tokens)**: Claude-specific token counting

### Example Management
- **[Weights & Biases Prompts](https://docs.wandb.ai/guides/prompts)**: Track and version example sets across experiments
- **[LangSmith](https://www.langchain.com/langsmith)**: Monitor which examples correlate with better outcomes
- **[PromptLayer](https://promptlayer.com/)**: Log prompts and examples for analysis and debugging

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Example bank contains 3-7 examples per task type with clear input-output pairs
- [ ] Examples cover simple, standard, edge case, and complex scenarios for each task
- [ ] All code examples are syntactically correct and tested
- [ ] Example formats are consistent within each task category
- [ ] At least one example demonstrates error handling or edge case behavior
- [ ] Examples are ordered from simple to complex when possible
- [ ] Token count for examples is measured and fits within context budget
- [ ] Dynamic example selection is implemented for high-variance tasks
- [ ] Chain-of-thought reasoning is shown in examples for complex tasks
- [ ] Example contribution to accuracy is measured and non-contributing examples are pruned
- [ ] Examples are versioned and tracked like code (in git, tested in CI)
- [ ] Documentation explains when to use which example sets

## Metadata

**Category**: Technology
**Principle Number**: 47
**Related Patterns**: Prompt Engineering, Retrieval-Augmented Generation, Context Curation, Template Methods, Example-Based Learning
**Prerequisites**: Understanding of language model context windows, tokenization, prompt design basics
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
