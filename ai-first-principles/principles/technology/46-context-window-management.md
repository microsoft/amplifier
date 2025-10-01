# Principle #46 - Context Window Management

## Plain-Language Definition

Context window management is the practice of efficiently using an AI model's limited token budget by strategically selecting, organizing, and optimizing the information included in each request. Like packing a suitcase with weight limits, every token counts—what you include, what you leave out, and how you arrange it all determines whether the model can perform the task successfully.

## Why This Matters for AI-First Development

AI models have finite context windows—typically 8K to 200K tokens—and every token consumes computational resources, adds latency, and increases cost. When AI agents build and modify systems autonomously, inefficient context management creates compounding problems: wasted API costs, slower responses, incomplete information reaching the model, and degraded performance as irrelevant information dilutes critical context.

Context window management becomes critical for AI-first development in three key ways:

1. **Cost scaling**: As AI agents make thousands of API calls during development cycles, token waste multiplies rapidly. A 100K token context that could be 20K tokens means 5x higher costs across every operation—testing, debugging, code generation, and validation.

2. **Information density**: Models perform better when context is information-dense rather than information-dilute. Filling the context window with irrelevant examples, redundant instructions, or verbose documentation reduces the model's ability to focus on what matters. Quality over quantity determines success.

3. **Cognitive load management**: Just as humans struggle with information overload, models become less precise when context windows contain competing signals, contradictory examples, or excessive noise. Strategic curation prevents degradation.

Without proper context window management, AI-driven systems waste resources on every operation, perform worse despite using more tokens, and create invisible technical debt through inefficient patterns that compound over time. A poorly managed 100K context might deliver worse results than a well-curated 10K context at 10x the cost.

## Implementation Approaches

### 1. **Progressive Context Loading**

Load information incrementally as needed rather than front-loading the entire context window:

```python
class ProgressiveContextManager:
    def __init__(self, model_max_tokens: int = 100_000):
        self.max_tokens = model_max_tokens
        self.current_tokens = 0
        self.context_layers = []

    def add_layer(self, content: str, priority: int, token_count: int) -> bool:
        """Add context layer if budget allows, ordered by priority."""
        if self.current_tokens + token_count > self.max_tokens:
            return False

        self.context_layers.append({
            "content": content,
            "priority": priority,
            "tokens": token_count
        })
        self.current_tokens += token_count
        return True

    def build_context(self) -> str:
        """Assemble context from highest to lowest priority."""
        # Sort by priority (highest first)
        sorted_layers = sorted(
            self.context_layers,
            key=lambda x: x["priority"],
            reverse=True
        )
        return "\n\n".join([layer["content"] for layer in sorted_layers])

# Usage
context = ProgressiveContextManager(max_tokens=8000)
context.add_layer(system_prompt, priority=10, token_count=200)
context.add_layer(critical_examples, priority=9, token_count=1500)
context.add_layer(documentation, priority=5, token_count=3000)
# Optional layers only if budget permits
context.add_layer(edge_cases, priority=3, token_count=2000)
```

When to use: Complex tasks requiring multiple types of information where not everything fits. Start with essentials, add optional context only if space permits.

### 2. **Semantic Chunking with Context Preservation**

Break large documents into meaningful chunks while preserving context about what each chunk represents:

```python
def create_contextual_chunks(
    document: str,
    chunk_size: int = 800,
    context_instruction: str = None
) -> list[dict]:
    """
    Chunk document while adding explanatory context to each chunk.
    Based on Anthropic's Contextual Retrieval technique.
    """
    chunks = split_document(document, chunk_size)
    contextualized_chunks = []

    for chunk in chunks:
        # Use Claude to generate chunk-specific context
        context_prompt = f"""
        <document>
        {document}
        </document>

        Here is the chunk we want to situate within the whole document:
        <chunk>
        {chunk}
        </chunk>

        Please give a short succinct context (50-100 tokens) to situate
        this chunk within the overall document for improving search retrieval.
        Answer only with the succinct context and nothing else.
        """

        chunk_context = call_model(context_prompt)

        contextualized_chunks.append({
            "original": chunk,
            "contextualized": f"{chunk_context}\n\n{chunk}",
            "context_only": chunk_context
        })

    return contextualized_chunks
```

When to use: RAG systems, knowledge bases, or any scenario requiring document chunking. Prevents information loss that traditional chunking causes.

### 3. **Dynamic Example Selection**

Select the most relevant examples for each specific query rather than using static few-shot examples:

```python
def select_relevant_examples(
    query: str,
    example_bank: list[dict],
    max_examples: int = 3,
    max_tokens: int = 2000
) -> list[dict]:
    """
    Dynamically select most relevant examples based on query similarity.
    """
    from sklearn.metrics.pairwise import cosine_similarity

    # Embed query and all examples
    query_embedding = embed(query)
    example_embeddings = [embed(ex["input"]) for ex in example_bank]

    # Calculate similarity scores
    similarities = cosine_similarity(
        [query_embedding],
        example_embeddings
    )[0]

    # Rank examples by similarity
    ranked_indices = similarities.argsort()[::-1]

    # Select top examples within token budget
    selected = []
    current_tokens = 0

    for idx in ranked_indices:
        example = example_bank[idx]
        example_tokens = count_tokens(example["input"] + example["output"])

        if len(selected) >= max_examples:
            break
        if current_tokens + example_tokens > max_tokens:
            break

        selected.append(example)
        current_tokens += example_tokens

    return selected

# Usage
query = "Calculate revenue growth for Q2 2023"
relevant_examples = select_relevant_examples(
    query,
    all_examples,
    max_examples=3,
    max_tokens=2000
)
```

When to use: Few-shot learning scenarios where you have many examples but limited context budget. Maximizes example relevance while respecting token constraints.

### 4. **Context Pruning and Compression**

Remove redundant or low-value information before sending context:

```python
def prune_context(
    context: str,
    target_tokens: int,
    strategy: str = "importance"
) -> str:
    """
    Reduce context size while preserving most important information.
    """
    if count_tokens(context) <= target_tokens:
        return context

    if strategy == "importance":
        # Use extractive summarization to keep important sentences
        sentences = split_into_sentences(context)
        sentence_scores = score_sentence_importance(sentences, context)

        # Sort by importance, select until token budget reached
        ranked = sorted(
            zip(sentences, sentence_scores),
            key=lambda x: x[1],
            reverse=True
        )

        pruned = []
        current_tokens = 0
        for sent, score in ranked:
            sent_tokens = count_tokens(sent)
            if current_tokens + sent_tokens > target_tokens:
                break
            pruned.append(sent)
            current_tokens += sent_tokens

        # Maintain original order
        pruned_ordered = [s for s in sentences if s in pruned]
        return " ".join(pruned_ordered)

    elif strategy == "summarization":
        # Use LLM to compress while preserving key information
        summary_prompt = f"""
        Compress the following text to approximately {target_tokens} tokens
        while preserving all critical information:

        {context}
        """
        return call_model(summary_prompt)

# Usage
large_context = load_documentation()  # 50K tokens
compressed = prune_context(large_context, target_tokens=10_000, strategy="importance")
```

When to use: Documentation, retrieved passages, or historical context that exceeds budget. Balance information preservation with token efficiency.

### 5. **Layered Context Architecture**

Organize context into priority tiers, including only higher tiers when budget is constrained:

```python
class LayeredContext:
    """
    Organize context into priority layers for flexible budget allocation.
    """
    def __init__(self):
        self.layers = {
            "system": [],      # Priority 1: Always include
            "critical": [],    # Priority 2: Core task information
            "supporting": [],  # Priority 3: Helpful but not essential
            "optional": []     # Priority 4: Nice to have
        }

    def add(self, layer: str, content: str):
        """Add content to a specific layer."""
        if layer not in self.layers:
            raise ValueError(f"Unknown layer: {layer}")
        self.layers[layer].append(content)

    def build(self, max_tokens: int) -> str:
        """Build context respecting token budget."""
        context_parts = []
        remaining_tokens = max_tokens

        # Process layers in priority order
        for layer_name in ["system", "critical", "supporting", "optional"]:
            layer_content = "\n\n".join(self.layers[layer_name])
            layer_tokens = count_tokens(layer_content)

            if layer_tokens <= remaining_tokens:
                context_parts.append(layer_content)
                remaining_tokens -= layer_tokens
            else:
                # Include what fits from this layer
                truncated = truncate_to_tokens(layer_content, remaining_tokens)
                if truncated:
                    context_parts.append(truncated)
                break

        return "\n\n".join(context_parts)

# Usage
context = LayeredContext()
context.add("system", "You are a Python code analyzer...")
context.add("critical", "Analyze this function: def process()...")
context.add("supporting", "Coding standards: PEP 8...")
context.add("optional", "Historical context: Previous versions...")

final_context = context.build(max_tokens=4000)
```

When to use: Multi-faceted tasks where different types of information have clear priority hierarchies. Ensures essential information never gets crowded out.

### 6. **Token Budget Allocation**

Explicitly allocate token budgets across different context components:

```python
class TokenBudgetManager:
    """
    Manage token allocation across context components.
    """
    def __init__(self, total_budget: int):
        self.total_budget = total_budget
        self.allocations = {}
        self.used = {}

    def allocate(self, component: str, tokens: int):
        """Reserve tokens for a component."""
        if sum(self.allocations.values()) + tokens > self.total_budget:
            raise ValueError(f"Budget exceeded: {component} needs {tokens}")
        self.allocations[component] = tokens
        self.used[component] = 0

    def use(self, component: str, content: str) -> bool:
        """Mark tokens as used for a component."""
        token_count = count_tokens(content)
        if token_count > self.allocations[component]:
            return False
        self.used[component] = token_count
        return True

    def get_remaining(self, component: str) -> int:
        """Get remaining tokens for a component."""
        return self.allocations[component] - self.used[component]

    def summary(self) -> dict:
        """Get budget utilization summary."""
        return {
            "total_budget": self.total_budget,
            "allocated": sum(self.allocations.values()),
            "used": sum(self.used.values()),
            "remaining": self.total_budget - sum(self.used.values()),
            "per_component": {
                comp: {
                    "allocated": self.allocations[comp],
                    "used": self.used[comp],
                    "remaining": self.allocations[comp] - self.used[comp]
                }
                for comp in self.allocations
            }
        }

# Usage
budget = TokenBudgetManager(total_budget=8000)
budget.allocate("system_prompt", 500)
budget.allocate("examples", 2000)
budget.allocate("documentation", 3000)
budget.allocate("query", 500)
budget.allocate("buffer", 2000)  # Reserved for response
```

When to use: Complex applications where multiple context types compete for limited space. Prevents any single component from monopolizing the context window.

## Good Examples vs Bad Examples

### Example 1: Few-Shot Learning Efficiency

**Good:**
```python
def build_few_shot_context(
    task_description: str,
    examples: list[dict],
    query: str,
    max_examples: int = 3
) -> str:
    """
    Efficient few-shot context with diminishing returns awareness.
    Research shows 2-4 examples often optimal; more = diminishing returns.
    """
    # Select most diverse/relevant examples
    selected = select_diverse_examples(examples, max_count=max_examples)

    context = f"{task_description}\n\n"

    for i, ex in enumerate(selected, 1):
        context += f"Example {i}:\n"
        context += f"Input: {ex['input']}\n"
        context += f"Output: {ex['output']}\n\n"

    context += f"Now your turn:\nInput: {query}\nOutput:"

    return context  # ~1500 tokens, optimal performance/cost ratio
```

**Bad:**
```python
def build_few_shot_context(
    task_description: str,
    examples: list[dict],
    query: str
) -> str:
    """
    Wasteful: includes all examples regardless of value.
    """
    context = f"{task_description}\n\n"

    # Include ALL examples (might be 20-50!)
    for i, ex in enumerate(examples, 1):
        context += f"Example {i}:\n"
        context += f"Input: {ex['input']}\n"
        context += f"Output: {ex['output']}\n\n"

    context += f"Now your turn:\nInput: {query}\nOutput:"

    return context  # ~15K tokens, minimal benefit over 3-5 examples
```

**Why It Matters:** Research shows few-shot learning exhibits diminishing returns—each additional example beyond 3-5 provides less benefit while consuming more tokens. The bad example wastes ~13.5K tokens for marginal (often zero) improvement, multiplying costs 10x with no performance gain.

### Example 2: Documentation Retrieval

**Good:**
```python
def retrieve_relevant_docs(
    query: str,
    doc_database: list[dict],
    max_tokens: int = 3000
) -> str:
    """
    Retrieve and rank documentation, include only what fits.
    """
    # Semantic search for relevant docs
    ranked_docs = search_docs(query, doc_database, top_k=20)

    # Rerank for precision
    reranked = rerank_docs(query, ranked_docs, top_k=10)

    # Include docs until token budget exhausted
    selected_docs = []
    current_tokens = 0

    for doc in reranked:
        doc_tokens = count_tokens(doc["content"])
        if current_tokens + doc_tokens > max_tokens:
            # Try to include partial content
            remaining = max_tokens - current_tokens
            if remaining > 200:  # Minimum useful chunk
                selected_docs.append(truncate_to_tokens(doc["content"], remaining))
            break

        selected_docs.append(doc["content"])
        current_tokens += doc_tokens

    return "\n\n---\n\n".join(selected_docs)
```

**Bad:**
```python
def retrieve_relevant_docs(
    query: str,
    doc_database: list[dict]
) -> str:
    """
    Naive: dumps all potentially relevant docs without ranking or limiting.
    """
    # Search for relevant docs (no ranking)
    relevant_docs = search_docs(query, doc_database, top_k=50)

    # Include everything
    all_docs = [doc["content"] for doc in relevant_docs]

    return "\n\n---\n\n".join(all_docs)  # Might be 50K+ tokens!
```

**Why It Matters:** The bad example might include 50 documents totaling 50K+ tokens, overwhelming the context window and diluting the truly relevant information. The good example uses semantic search + reranking + budget constraints to deliver dense, relevant context within 3K tokens—better results at a fraction of the cost.

### Example 3: Conversation History Management

**Good:**
```python
class ConversationManager:
    """
    Smart conversation history with automatic pruning.
    """
    def __init__(self, max_history_tokens: int = 4000):
        self.messages = []
        self.max_tokens = max_history_tokens

    def add_message(self, role: str, content: str):
        """Add message and prune if needed."""
        self.messages.append({"role": role, "content": content})
        self._prune_if_needed()

    def _prune_if_needed(self):
        """Keep recent messages within token budget."""
        total_tokens = sum(count_tokens(m["content"]) for m in self.messages)

        if total_tokens <= self.max_tokens:
            return

        # Keep system message + recent conversation
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        conversation = [m for m in self.messages if m["role"] != "system"]

        # Remove oldest conversation messages until within budget
        while total_tokens > self.max_tokens and len(conversation) > 2:
            removed = conversation.pop(0)
            total_tokens -= count_tokens(removed["content"])

        self.messages = system_msgs + conversation

    def get_context(self) -> list[dict]:
        """Return current conversation context."""
        return self.messages
```

**Bad:**
```python
class ConversationManager:
    """
    Keeps entire conversation history indefinitely.
    """
    def __init__(self):
        self.messages = []

    def add_message(self, role: str, content: str):
        """Just append, never prune."""
        self.messages.append({"role": role, "content": content})

    def get_context(self) -> list[dict]:
        """Return ALL history, no matter how long."""
        return self.messages  # Grows unbounded!
```

**Why It Matters:** Long conversations can easily exceed context windows. The bad example eventually crashes (when history exceeds max tokens) or wastes massive amounts of tokens on ancient history. The good example maintains relevant recent context within budget, ensuring consistent performance and costs.

### Example 4: Code Context for AI Coding Assistants

**Good:**
```python
def build_code_context(
    target_file: str,
    query: str,
    codebase_root: str,
    max_tokens: int = 10_000
) -> str:
    """
    Strategic code context: target file + relevant dependencies.
    """
    context_parts = []
    budget = TokenBudgetManager(max_tokens)

    # Allocate budget strategically
    budget.allocate("target_file", 3000)
    budget.allocate("direct_imports", 4000)
    budget.allocate("related_files", 2000)
    budget.allocate("buffer", 1000)

    # Target file (always include)
    target_code = read_file(target_file)
    target_truncated = truncate_to_tokens(target_code, 3000)
    context_parts.append(f"# Target file: {target_file}\n{target_truncated}")

    # Direct imports (high priority)
    imports = extract_imports(target_code)
    for imp in imports[:5]:  # Limit to top 5 imports
        import_code = read_file(find_import_file(imp, codebase_root))
        import_truncated = truncate_to_tokens(import_code, 800)
        context_parts.append(f"# Import: {imp}\n{import_truncated}")

    # Related files (if budget permits)
    related = find_related_files(target_file, query, codebase_root)
    remaining = budget.get_remaining("related_files")
    for rel in related:
        rel_code = read_file(rel)
        rel_tokens = min(count_tokens(rel_code), remaining // len(related))
        rel_truncated = truncate_to_tokens(rel_code, rel_tokens)
        context_parts.append(f"# Related: {rel}\n{rel_truncated}")

    return "\n\n".join(context_parts)
```

**Bad:**
```python
def build_code_context(
    target_file: str,
    query: str,
    codebase_root: str
) -> str:
    """
    Naive: dump entire files without budget management.
    """
    context_parts = []

    # Include target file (might be huge)
    target_code = read_file(target_file)
    context_parts.append(f"# Target file: {target_file}\n{target_code}")

    # Include ALL imports (might be dozens)
    imports = extract_imports(target_code)
    for imp in imports:
        import_code = read_file(find_import_file(imp, codebase_root))
        context_parts.append(f"# Import: {imp}\n{import_code}")

    # Include ALL related files
    related = find_related_files(target_file, query, codebase_root)
    for rel in related:
        rel_code = read_file(rel)
        context_parts.append(f"# Related: {rel}\n{rel_code}")

    return "\n\n".join(context_parts)  # Might be 100K+ tokens!
```

**Why It Matters:** Code files can be enormous, and codebases have complex dependency graphs. The bad example might include 50+ files totaling 100K+ tokens, exceeding most context windows and causing API errors. The good example provides strategic snippets from key files, respecting token budgets while maintaining sufficient context for the task.

### Example 5: Batch Processing with Context Reuse

**Good:**
```python
def process_batch_with_caching(
    items: list[str],
    shared_context: str,
    instruction_template: str
) -> list[str]:
    """
    Use prompt caching for shared context across batch.
    Anthropic's prompt caching reduces costs by 90% for repeated context.
    """
    results = []

    # Mark shared context for caching
    cached_prompt = {
        "system": [
            {
                "type": "text",
                "text": shared_context,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    }

    # Process items reusing cached context
    for item in items:
        prompt = instruction_template.format(item=item)

        response = call_model_with_cache(
            system=cached_prompt["system"],
            messages=[{"role": "user", "content": prompt}]
        )

        results.append(response)

    return results
    # First call: Full cost for shared_context
    # Subsequent calls: 90% discount on shared_context
```

**Bad:**
```python
def process_batch_naive(
    items: list[str],
    shared_context: str,
    instruction_template: str
) -> list[str]:
    """
    Naive: repeats full context for every item.
    """
    results = []

    for item in items:
        # Build full prompt from scratch every time
        full_prompt = f"{shared_context}\n\n{instruction_template.format(item=item)}"

        response = call_model(full_prompt)
        results.append(response)

    return results
    # Every call: Full cost for entire context
    # 100 items = 100x the context cost!
```

**Why It Matters:** When processing 100 items with 10K tokens of shared context, the bad example processes 1M tokens of redundant context. The good example caches the shared context, processing just 10K + (100 * query_tokens). For a 10K shared context and 100-token queries, that's 1M tokens vs. 20K tokens—a 50x cost reduction with identical results.

## Related Principles

- **[Principle #14 - Context-Aware Agent Prompting](../process/14-context-aware-agent-prompting.md)** - Context window management enables context-aware prompting by ensuring the right information reaches the model within budget constraints. You can't be context-aware if you don't manage the context window effectively.

- **[Principle #45 - Prompt Design Patterns](45-prompt-design-patterns.md)** - Prompt patterns define what to say; context window management determines how much you can say and what to prioritize. These work together to maximize effectiveness within token constraints.

- **[Principle #47 - Few-Shot Learning](47-few-shot-learning.md)** - Few-shot learning is a primary consumer of context window space. Context window management provides strategies for example selection and allocation to balance learning effectiveness with token efficiency.

- **[Principle #50 - Retrieval-Augmented Generation (RAG)](50-rag-patterns.md)** - RAG systems require careful context window management to fit retrieved documents alongside prompts and examples. Chunking, reranking, and budget allocation are critical for RAG performance.

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - Stateless design reduces context window pressure by avoiding the need to maintain conversation history or session state. Each request stands alone with minimal context requirements.

- **[Principle #32 - Error Recovery Patterns Built In](32-error-recovery-patterns.md)** - Context window overflow is a common error mode. Recovery patterns include automatic pruning, fallback to smaller contexts, and graceful degradation when budget is exceeded.

## Common Pitfalls

1. **Ignoring Diminishing Returns on Examples**
   - Example: Including 20 few-shot examples when 3-5 provide equivalent performance
   - Impact: Wastes 10-15K tokens with zero benefit, multiplying costs without improving quality. Research consistently shows 3-5 examples hit the performance ceiling for most tasks.

2. **No Token Budget Planning**
   - Example: Building prompts ad-hoc without tracking token allocation across components
   - Impact: Unpredictable context overflow, API errors when inputs vary in size, inability to troubleshoot which components are consuming budget.

3. **Treating All Context as Equally Important**
   - Example: Including documentation, examples, and instructions in a single unstructured blob
   - Impact: Can't prioritize what matters most, can't gracefully degrade when budget is tight, can't optimize allocation across components.

4. **Naive Conversation History Management**
   - Example: Appending every message to history indefinitely without pruning
   - Impact: Conversations eventually exceed context windows and crash, or waste huge amounts of tokens on ancient history that no longer matters.

5. **Chunking Without Context Preservation**
   - Example: Breaking documents into chunks without explaining what each chunk represents
   - Impact: Retrieval systems fail to find relevant chunks because they lack surrounding context. A chunk saying "revenue grew 3%" is useless without knowing which company and time period.

6. **Fixed Context Regardless of Task Complexity**
   - Example: Always using the same prompt template and examples regardless of query complexity
   - Impact: Simple queries waste tokens on unnecessary context; complex queries lack sufficient context. Dynamic context assembly adapts to task needs.

7. **No Monitoring of Token Utilization**
   - Example: Never measuring actual token usage vs. budget allocation
   - Impact: Can't identify waste, can't optimize allocation, can't detect when context is approaching limits until failures occur.

## Tools & Frameworks

### Context Management Libraries
- **[LangChain](https://python.langchain.com/)**: Built-in token counting, text splitters with overlap, conversation memory with pruning strategies, retrieval chains with context assembly
- **[LlamaIndex](https://www.llamaindex.ai/)**: Index structures optimized for context window constraints, query engines with budget-aware retrieval, response synthesis with context management
- **[Semantic Kernel](https://github.com/microsoft/semantic-kernel)**: Context management primitives, memory connectors with pruning, planner with token-aware operation selection

### Token Counting & Optimization
- **[tiktoken](https://github.com/openai/tiktoken)**: OpenAI's official tokenizer for accurate token counting
- **[transformers](https://huggingface.co/docs/transformers/)**: Tokenizers for various model families (GPT, Claude, Llama, etc.)
- **[anthropic-tokenizer](https://github.com/anthropics/anthropic-sdk-python)**: Claude-specific tokenization for accurate Anthropic API usage

### Retrieval & Reranking
- **[Cohere Rerank](https://cohere.com/rerank)**: Semantic reranking to select most relevant chunks from retrieved candidates
- **[Voyage AI](https://www.voyageai.com/)**: High-quality embeddings and reranking for context-aware retrieval
- **[Chroma](https://www.trychroma.com/)**: Vector database with built-in token-aware retrieval strategies

### Prompt Caching & Optimization
- **[Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)**: Cache frequently used context for 90% cost reduction on repeated content
- **[OpenAI Prompt Caching](https://platform.openai.com/docs/guides/prompt-caching)**: Automatic caching of prompt prefixes in supported models
- **[PromptLayer](https://promptlayer.com/)**: Track prompt performance, token usage, and cost across requests

### Context Compression
- **[LLMLingua](https://github.com/microsoft/LLMLingua)**: Prompt compression that maintains semantic meaning while reducing tokens by 20-40%
- **[AutoCompressors](https://arxiv.org/abs/2305.14788)**: Train models to compress long contexts into compact summary vectors

### Evaluation & Monitoring
- **[Phoenix by Arize AI](https://github.com/Arize-ai/phoenix)**: LLM observability with token usage tracking, context analysis, and performance metrics
- **[LangSmith](https://smith.langchain.com/)**: Trace context assembly, measure token utilization per component, identify optimization opportunities

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Token counting is accurate for your specific model (use official tokenizers)
- [ ] Context has explicit priority layers (system, critical, supporting, optional)
- [ ] Progressive loading includes only what's needed, not everything available
- [ ] Few-shot examples are limited to 3-5 per pattern type (respect diminishing returns)
- [ ] Conversation history is pruned to maintain recency within budget constraints
- [ ] Retrieved documents use semantic chunking with context preservation
- [ ] Reranking is applied when retrieving from large document sets (>20 candidates)
- [ ] Token budget is allocated across components with explicit limits per component
- [ ] Monitoring tracks actual token usage vs. budget allocation
- [ ] Prompt caching is enabled for repeated context (Anthropic, OpenAI)
- [ ] Graceful degradation handles context overflow (prune optional layers first)
- [ ] Dynamic context assembly adapts to query complexity (more context for complex queries)

## Metadata

**Category**: Technology
**Principle Number**: 46
**Related Patterns**: RAG, Few-Shot Learning, Prompt Engineering, Semantic Search, Context Compression, Token Optimization
**Prerequisites**: Understanding of tokenization, embeddings, semantic search, and prompt engineering basics
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
