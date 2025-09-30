# Principle #19 - Cost and Token Budgeting

## Plain-Language Definition

Cost and token budgeting means setting hard limits on how much money and computational resources your AI operations can consume, tracking usage in real-time, and optimizing context to prevent runaway expenses.

## Why This Matters for AI-First Development

AI operations have real, measurable costs that scale with usage. Unlike traditional software where compute costs are relatively fixed, every LLM API call consumes tokens and incurs charges. A poorly optimized prompt can cost 10x more than a well-crafted one. An unconstrained code generation loop can burn through thousands of dollars in minutes. These costs compound quickly in AI-first development where agents autonomously generate code, analyze systems, and iterate on solutions.

When AI agents build and modify systems, they lack the human intuition to recognize when a task is becoming too expensive. An agent might recursively analyze an entire codebase when a targeted search would suffice. It might regenerate the same module dozens of times trying to fix a test failure. Without explicit cost guardrails, these behaviors can exhaust API budgets, trigger rate limits, or accumulate unexpected bills.

Cost and token budgeting provides three critical protections:

1. **Financial predictability**: Hard limits prevent surprise bills and ensure AI operations stay within allocated budgets.

2. **Performance optimization**: Token constraints force efficient prompt design and smart context management, leading to faster responses and better system performance.

3. **Resource allocation**: Budget tracking enables informed decisions about which tasks warrant expensive models and which can use cheaper alternatives.

Without cost budgeting, AI systems become financial liabilities. A single runaway agent can consume an entire month's budget in hours. Unbounded context windows can push every request to the maximum token limit. Lack of caching can cause redundant, expensive API calls for the same information. These problems are invisible until the bill arrives, making proactive cost management essential.

## Implementation Approaches

### 1. **Token Limits at Request Level**

Set hard token limits for individual API requests to prevent any single operation from consuming excessive resources:

```python
def call_llm(prompt: str, max_tokens: int = 4000, max_cost: float = 0.50):
    """Enforce token and cost limits per request"""
    # Estimate input tokens
    input_tokens = estimate_tokens(prompt)
    estimated_cost = calculate_cost(input_tokens, max_tokens)

    if estimated_cost > max_cost:
        raise BudgetExceededError(
            f"Request would cost ${estimated_cost:.2f}, limit is ${max_cost:.2f}"
        )

    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
```

Use this approach for all LLM calls to prevent individual requests from exceeding budget thresholds.

### 2. **Session-Level Budget Tracking**

Track cumulative costs across an entire AI session to enforce total spending limits:

```python
class BudgetedSession:
    def __init__(self, max_cost: float):
        self.max_cost = max_cost
        self.spent = 0.0
        self.requests = []

    def call_llm(self, prompt: str, **kwargs):
        cost = self._estimate_cost(prompt, kwargs.get('max_tokens', 1000))

        if self.spent + cost > self.max_cost:
            raise BudgetExceededError(
                f"Session budget ${self.max_cost} would be exceeded. "
                f"Spent: ${self.spent:.2f}, Request: ${cost:.2f}"
            )

        response = client.chat.completions.create(**kwargs)
        actual_cost = self._calculate_actual_cost(response)
        self.spent += actual_cost
        self.requests.append({
            "timestamp": now(),
            "cost": actual_cost,
            "tokens": response.usage.total_tokens
        })

        return response
```

Session tracking prevents death-by-a-thousand-cuts where many small requests add up to large costs.

### 3. **Context Window Optimization**

Aggressively trim context to minimize token usage while preserving essential information:

```python
def optimize_context(full_context: str, target_tokens: int) -> str:
    """Reduce context to fit within token budget"""
    current_tokens = estimate_tokens(full_context)

    if current_tokens <= target_tokens:
        return full_context

    # Progressive reduction strategies
    strategies = [
        remove_comments,
        remove_whitespace,
        summarize_repeated_sections,
        extract_key_information
    ]

    for strategy in strategies:
        full_context = strategy(full_context)
        current_tokens = estimate_tokens(full_context)

        if current_tokens <= target_tokens:
            return full_context

    # Last resort: truncate with warning
    logger.warning(f"Context truncated from {current_tokens} to {target_tokens} tokens")
    return truncate_to_tokens(full_context, target_tokens)
```

Context optimization is critical for cost control because input tokens often dominate API costs.

### 4. **Intelligent Model Selection**

Route requests to cheaper models when appropriate, reserving expensive models for complex tasks:

```python
def select_model(task_type: str, complexity: str) -> tuple[str, float]:
    """Choose cost-effective model for the task"""
    model_catalog = {
        "simple": ("gpt-3.5-turbo", 0.002),      # $0.002/1K tokens
        "moderate": ("gpt-4o-mini", 0.005),      # $0.005/1K tokens
        "complex": ("gpt-4", 0.03)               # $0.03/1K tokens
    }

    # Task-specific rules
    if task_type == "code_review" and complexity == "simple":
        return model_catalog["simple"]
    elif task_type == "architecture" or complexity == "complex":
        return model_catalog["complex"]
    else:
        return model_catalog["moderate"]

def call_llm_with_smart_routing(prompt: str, task_type: str, complexity: str):
    model, cost_per_1k = select_model(task_type, complexity)
    logger.info(f"Using {model} (${cost_per_1k}/1K tokens) for {task_type}")

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

Smart routing can reduce costs by 10-15x by avoiding expensive models for simple tasks.

### 5. **Response Caching**

Cache LLM responses to eliminate redundant API calls for identical or similar requests:

```python
class CachedLLMClient:
    def __init__(self, cache_ttl: int = 3600):
        self.cache = {}
        self.cache_ttl = cache_ttl

    def call_llm(self, prompt: str, **kwargs):
        # Generate cache key from prompt and parameters
        cache_key = self._hash_request(prompt, kwargs)

        # Check cache
        if cache_key in self.cache:
            cached_entry = self.cache[cache_key]
            if time.time() - cached_entry["timestamp"] < self.cache_ttl:
                logger.info("Cache hit - $0.00 cost")
                return cached_entry["response"]

        # Cache miss - make API call
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )

        # Store in cache
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time(),
            "cost": calculate_cost(response.usage.total_tokens)
        }

        return response
```

Caching is especially valuable during development when agents repeatedly ask similar questions.

### 6. **Rate Limiting and Budget Alerts**

Implement proactive alerts when approaching budget limits to prevent hard failures:

```python
class BudgetMonitor:
    def __init__(self, daily_limit: float, warning_threshold: float = 0.8):
        self.daily_limit = daily_limit
        self.warning_threshold = warning_threshold
        self.daily_spent = 0.0
        self.alert_sent = False

    def track_request(self, cost: float):
        self.daily_spent += cost
        usage_percent = self.daily_spent / self.daily_limit

        # Warning alert
        if usage_percent >= self.warning_threshold and not self.alert_sent:
            logger.warning(
                f"Budget warning: {usage_percent*100:.1f}% of daily limit used "
                f"(${self.daily_spent:.2f} of ${self.daily_limit})"
            )
            send_alert("Budget Warning", f"Approaching daily limit")
            self.alert_sent = True

        # Hard limit
        if self.daily_spent >= self.daily_limit:
            raise BudgetExceededError(
                f"Daily budget of ${self.daily_limit} exceeded "
                f"(${self.daily_spent:.2f} spent)"
            )
```

Alerts enable intervention before hitting hard limits that might halt critical operations.

## Good Examples vs Bad Examples

### Example 1: Request-Level Token Limiting

**Good:**
```python
def generate_code(spec: str, max_tokens: int = 2000) -> str:
    """Generate code with explicit token limit"""
    # Enforce token budget
    input_tokens = estimate_tokens(spec)
    if input_tokens > 1000:
        raise ValueError(f"Spec too long: {input_tokens} tokens (max 1000)")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Generate concise, production-ready code."},
            {"role": "user", "content": spec}
        ],
        max_tokens=max_tokens,  # Hard limit on output
        temperature=0.3
    )

    # Log costs for tracking
    cost = calculate_cost(response.usage.total_tokens, "gpt-4")
    logger.info(f"Code generation: {response.usage.total_tokens} tokens, ${cost:.4f}")

    return response.choices[0].message.content
```

**Bad:**
```python
def generate_code(spec: str) -> str:
    """Generate code with no token limits"""
    # No token limits - can use max context window
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Generate comprehensive code with examples."},
            {"role": "user", "content": spec}
        ],
        # No max_tokens specified - defaults to model maximum
        temperature=0.3
    )

    # No cost tracking or logging
    return response.choices[0].message.content
```

**Why It Matters:** Without token limits, a single request can consume thousands of tokens and cost dollars. The bad example could generate 8K tokens of output ($0.24 at GPT-4 rates) when 2K tokens ($0.06) would suffice. Over hundreds of requests, this 4x cost multiplier is unsustainable.

### Example 2: Context Window Optimization

**Good:**
```python
def analyze_codebase(files: list[Path], question: str) -> str:
    """Analyze codebase with optimized context"""
    # Budget: 4000 tokens for context, 1000 for response
    target_tokens = 4000

    # Build minimal context
    relevant_files = filter_relevant_files(files, question)  # Reduce from 50 to 5 files
    context_parts = []

    for file in relevant_files:
        content = file.read_text()
        # Remove comments and docstrings to save tokens
        minimal_content = strip_non_code(content)
        context_parts.append(f"# {file.name}\n{minimal_content}")

    context = "\n\n".join(context_parts)

    # Ensure we're within budget
    if estimate_tokens(context) > target_tokens:
        context = truncate_to_tokens(context, target_tokens)
        logger.warning(f"Context truncated to {target_tokens} tokens")

    return call_llm(f"Context:\n{context}\n\nQuestion: {question}", max_tokens=1000)
```

**Bad:**
```python
def analyze_codebase(files: list[Path], question: str) -> str:
    """Analyze codebase with full context"""
    # No token budget - include everything
    context_parts = []

    for file in files:  # All 50 files included
        content = file.read_text()
        # Include full file with comments, whitespace, everything
        context_parts.append(f"# {file.name}\n{content}")

    context = "\n\n".join(context_parts)
    # Context might be 50K tokens = $1.50 per request

    return call_llm(f"Context:\n{context}\n\nQuestion: {question}")
```

**Why It Matters:** The bad example could send 50K tokens of context ($1.50 input) when 4K tokens ($0.12) would answer the question. That's a 12.5x cost increase. If an agent asks 100 questions during development, that's $150 vs $12 - a $138 difference for identical results.

### Example 3: Intelligent Caching

**Good:**
```python
class SmartCache:
    """Cache LLM responses with deduplication"""

    def __init__(self):
        self.exact_cache = {}      # Exact prompt matches
        self.semantic_cache = {}   # Similar prompts

    def get_or_call(self, prompt: str, **kwargs) -> str:
        # Check exact match cache
        cache_key = hash_prompt(prompt, kwargs)
        if cache_key in self.exact_cache:
            logger.info("Exact cache hit - $0.00")
            return self.exact_cache[cache_key]

        # Check semantic similarity cache
        similar_key = find_similar_prompt(prompt, self.semantic_cache.keys())
        if similar_key and similarity_score(prompt, similar_key) > 0.9:
            logger.info("Semantic cache hit - $0.00")
            return self.semantic_cache[similar_key]

        # Cache miss - make API call
        response = call_llm(prompt, **kwargs)
        cost = calculate_cost(response.usage.total_tokens)
        logger.info(f"Cache miss - ${cost:.4f}")

        # Store in both caches
        self.exact_cache[cache_key] = response
        self.semantic_cache[prompt] = response

        return response
```

**Bad:**
```python
def get_or_call(prompt: str, **kwargs) -> str:
    """No caching - every request hits API"""
    response = call_llm(prompt, **kwargs)
    return response

    # Even identical prompts make full API calls
    # No cost savings from repeated operations
```

**Why It Matters:** During iterative development, agents often ask the same or very similar questions. Without caching, analyzing a function 10 times costs 10x the single-call price. Smart caching can reduce costs by 60-80% in typical development workflows while making responses instant.

### Example 4: Model Selection Strategy

**Good:**
```python
class CostOptimizedLLM:
    """Route to appropriate model based on task complexity"""

    MODELS = {
        "fast": {"name": "gpt-3.5-turbo", "cost_per_1k": 0.002},
        "balanced": {"name": "gpt-4o-mini", "cost_per_1k": 0.005},
        "powerful": {"name": "gpt-4", "cost_per_1k": 0.03}
    }

    def call(self, prompt: str, task_complexity: str = "auto"):
        # Auto-detect complexity if not specified
        if task_complexity == "auto":
            task_complexity = self._assess_complexity(prompt)

        model_tier = {
            "simple": "fast",       # Syntax checks, formatting
            "moderate": "balanced", # Code review, refactoring
            "complex": "powerful"   # Architecture, debugging
        }[task_complexity]

        model = self.MODELS[model_tier]
        logger.info(f"Using {model['name']} (${model['cost_per_1k']}/1K) for {task_complexity} task")

        return client.chat.completions.create(
            model=model["name"],
            messages=[{"role": "user", "content": prompt}]
        )

    def _assess_complexity(self, prompt: str) -> str:
        """Heuristic for task complexity"""
        # Simple patterns
        if any(kw in prompt.lower() for kw in ["format", "lint", "style"]):
            return "simple"
        # Complex patterns
        if any(kw in prompt.lower() for kw in ["architecture", "design", "debug"]):
            return "complex"
        return "moderate"
```

**Bad:**
```python
def call_llm(prompt: str):
    """Always use most expensive model"""
    # No model selection - always use GPT-4
    return client.chat.completions.create(
        model="gpt-4",  # $0.03/1K tokens
        messages=[{"role": "user", "content": prompt}]
    )

    # Uses GPT-4 even for simple tasks like formatting
    # 15x more expensive than GPT-3.5-turbo for same result
```

**Why It Matters:** Using GPT-4 for every task when GPT-3.5-turbo handles 70% of them is a 10x cost increase on those requests. On 1000 requests with 50% being simple tasks, smart routing saves approximately $12 (500 requests × ($0.03 - $0.002)/1K × 1K tokens average).

### Example 5: Budget Monitoring with Alerts

**Good:**
```python
class BudgetTracker:
    """Track costs with proactive alerts"""

    def __init__(self, daily_limit: float = 50.0):
        self.daily_limit = daily_limit
        self.daily_spent = 0.0
        self.request_log = []

    def track_request(self, cost: float, metadata: dict):
        self.daily_spent += cost
        self.request_log.append({
            "timestamp": time.time(),
            "cost": cost,
            "metadata": metadata
        })

        usage = self.daily_spent / self.daily_limit

        # Progressive warnings
        if usage >= 0.5 and not self._alert_sent(0.5):
            logger.warning(f"50% of daily budget used (${self.daily_spent:.2f})")

        if usage >= 0.8 and not self._alert_sent(0.8):
            logger.error(f"80% of daily budget used (${self.daily_spent:.2f})")
            send_email_alert("Budget Warning", self._cost_breakdown())

        if usage >= 1.0:
            logger.critical(f"Daily budget exceeded!")
            raise BudgetExceededError(
                f"Daily limit of ${self.daily_limit} exceeded. "
                f"Spent: ${self.daily_spent:.2f}"
            )

    def _cost_breakdown(self) -> str:
        """Generate cost report for alerts"""
        by_model = {}
        for req in self.request_log:
            model = req["metadata"].get("model", "unknown")
            by_model[model] = by_model.get(model, 0) + req["cost"]

        breakdown = "\n".join([f"{model}: ${cost:.2f}" for model, cost in by_model.items()])
        return f"Total: ${self.daily_spent:.2f}\n{breakdown}"
```

**Bad:**
```python
def track_request(cost: float):
    """Track cost with no alerts"""
    global daily_spent
    daily_spent += cost

    # No warnings or alerts
    # Only find out budget exceeded when API calls start failing
    # No visibility into cost breakdown
```

**Why It Matters:** Without proactive monitoring, you only discover budget overruns when API calls fail or bills arrive. The good example provides early warnings at 50% and 80% thresholds, allowing intervention before hitting hard limits. It also provides cost breakdowns showing which models or operations consume the most budget, enabling optimization.

## Related Principles

- **[Principle #14 - Explicit Constraints Always](14-explicit-constraints-always.md)** - Cost limits are explicit constraints that prevent unbounded resource consumption. Token budgets and spending caps enforce boundaries on AI operations.

- **[Principle #39 - Real-Time Monitoring and Observability](../technology/39-real-time-monitoring-observability.md)** - Cost tracking is a form of observability that enables real-time awareness of resource consumption and immediate response to budget anomalies.

- **[Principle #12 - Fail Fast with Clear Error Messages](12-fail-fast-clear-errors.md)** - Budget limits should fail fast with clear messages about what limit was exceeded, how much was spent, and what operation triggered the failure.

- **[Principle #13 - Defensive Code by Default](13-defensive-code-default.md)** - Cost budgeting is defensive programming for AI operations, protecting against runaway expenses through validation, limits, and monitoring.

- **[Principle #43 - Performance Budgets and Optimization](../technology/43-performance-budgets-optimization.md)** - Token budgets are performance budgets for AI operations. Optimizing context windows and model selection improves both speed and cost.

- **[Principle #03 - Documentation as Code](../people/03-documentation-as-code.md)** - Cost budgets should be documented in code through constants, configuration files, and inline comments explaining budget rationale.

## Common Pitfalls

1. **No Token Limits on Output**: Allowing unbounded output tokens means a single request can consume the model's maximum context window (8K+ tokens), costing significantly more than necessary.
   - Example: Not setting `max_tokens` parameter, allowing 4000 token responses when 500 would suffice.
   - Impact: 8x cost increase per request, unsustainable for high-volume operations.

2. **Context Window Bloat**: Including entire codebases or files in context when only small relevant sections are needed wastes thousands of input tokens.
   - Example: Sending 10K tokens of boilerplate code to ask about a 50-line function.
   - Impact: 200x more input tokens than necessary, dramatically increasing costs.

3. **Redundant API Calls**: Making identical API calls without caching, especially during iterative development where agents ask similar questions repeatedly.
   - Example: Analyzing the same function 20 times without caching results.
   - Impact: 20x unnecessary costs for information that could be cached.

4. **Always Using Premium Models**: Using GPT-4 or Claude Opus for simple tasks that GPT-3.5-turbo or Claude Haiku could handle equally well.
   - Example: Using GPT-4 ($0.03/1K) to format code when GPT-3.5-turbo ($0.002/1K) achieves identical results.
   - Impact: 15x higher costs for no quality improvement.

5. **No Session Budget Tracking**: Tracking individual request costs but not cumulative session costs allows slow budget exhaustion through many small requests.
   - Example: 1000 requests at $0.05 each totals $50 without triggering per-request limits.
   - Impact: Budget overruns invisible until aggregated, no opportunity to intervene.

6. **Missing Cost Estimates**: Not estimating costs before making API calls, leading to surprise expenses when operations are more expensive than expected.
   - Example: Summarizing 100 documents without estimating total token cost first.
   - Impact: Unexpected budget exhaustion mid-operation, wasted partial work.

7. **No Cost Attribution**: Tracking total costs without attributing them to specific operations, users, or workflows prevents targeted optimization.
   - Example: Knowing daily spend is $100 but not knowing which operations consume the most.
   - Impact: Can't identify and optimize expensive operations, waste continues.

## Tools & Frameworks

### Cost Tracking Libraries
- **LiteLLM**: Unified interface for multiple LLM providers with built-in cost tracking and token counting across all models
- **OpenAI Token Counter**: Official tiktoken library for accurate GPT token estimation before API calls
- **Anthropic Token Counter**: Built-in token counting for Claude models with model-specific tokenization

### Budget Management Platforms
- **Promptlayer**: LLM request logging with cost tracking, analytics, and budget alerts across providers
- **Helicone**: Open-source LLM observability with real-time cost monitoring, caching, and rate limiting
- **LangSmith**: LangChain's platform for tracing LLM calls with cost attribution and budget enforcement

### Caching Solutions
- **Redis**: Fast in-memory cache for LLM responses with TTL support and similarity search via Redis Stack
- **Momento**: Serverless cache specifically designed for LLM applications with semantic caching
- **GPTCache**: Purpose-built semantic caching library for LLM responses with multiple similarity algorithms

### Context Optimization
- **LlamaIndex**: Context optimization through smart document chunking and retrieval for RAG applications
- **LangChain Text Splitters**: Token-aware text splitting that respects token budgets while preserving semantic meaning
- **AutoCompressor**: Automatic context compression using smaller models to summarize context for larger models

### Model Routing
- **OpenRouter**: Intelligent routing across 100+ models with automatic fallback and cost optimization
- **Portkey**: Model gateway with smart routing, load balancing, and cost-based model selection
- **Martian**: LLM router that selects models based on task complexity and cost constraints

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All LLM API calls have explicit `max_tokens` limits appropriate to the task
- [ ] Input token counts are estimated before making API calls to prevent oversized requests
- [ ] Session-level budget tracking accumulates costs and enforces daily/monthly limits
- [ ] Progressive budget alerts warn at 50%, 80%, and 95% of limits before hard failure
- [ ] Response caching is implemented for repeated or similar requests
- [ ] Model selection logic routes simple tasks to cheaper models (GPT-3.5-turbo, Claude Haiku)
- [ ] Context windows are optimized to include only relevant information, not entire codebases
- [ ] Cost attribution tags operations, users, or workflows to identify expensive patterns
- [ ] Budget exhaustion errors are clear and actionable, suggesting optimization strategies
- [ ] Cost estimates are calculated and logged before expensive operations
- [ ] Regular cost reports identify trends and opportunities for optimization
- [ ] Token counting uses model-specific tokenizers (tiktoken for GPT, anthropic for Claude)

## Metadata

**Category**: Process
**Principle Number**: 19
**Related Patterns**: Circuit Breaker, Rate Limiting, Resource Pooling, Caching, Lazy Loading
**Prerequisites**: LLM API integration, basic cost model understanding, logging infrastructure
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0