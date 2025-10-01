# Principle #50 - Retrieval-Augmented Generation

## Plain-Language Definition

Retrieval-Augmented Generation (RAG) enhances AI model responses by retrieving relevant information from external knowledge sources and using that context to generate more accurate, factual answers. Instead of relying solely on the model's training data, RAG systems fetch up-to-date information at query time, making responses grounded in actual evidence rather than hallucinated facts.

## Why This Matters for AI-First Development

When AI agents build and maintain systems, they need access to current, domain-specific knowledge that wasn't part of their training. A customer support bot needs to know about last week's product updates. A legal research assistant needs access to recent case law. A code documentation agent needs to understand the latest API changes. Without RAG, AI systems are limited to stale parametric knowledge frozen at training time.

RAG provides three critical benefits for AI-driven development:

1. **Dynamic knowledge without retraining**: AI agents can access the latest information without expensive model updates. When your product documentation changes or new code is committed, RAG systems automatically incorporate this knowledge into responses. This is essential for agents operating in fast-moving environments where facts evolve continuously.

2. **Factual grounding reduces hallucination**: By anchoring responses in retrieved evidence, RAG dramatically reduces the model's tendency to fabricate information. When an AI agent cites specific documentation or code comments it retrieved, the response becomes verifiable and trustworthy. This is critical for production systems where accuracy matters.

3. **Domain specialization without fine-tuning**: RAG enables AI systems to become experts in specific domains by simply pointing them at relevant knowledge bases. A general-purpose model becomes a specialist in your codebase, your company's policies, or your technical documentation—without any model training. This makes AI-first development practical for organizations without ML expertise.

Without RAG, AI-first systems face severe limitations. Agents working with code repositories would miss recent commits and documentation updates. Customer-facing bots would provide outdated information about products and policies. Research assistants would cite non-existent papers or misrepresent findings. These failures compound quickly when agents operate autonomously without human verification at every step.

## Implementation Approaches

### 1. **Basic Semantic Search RAG**

The simplest RAG implementation uses embedding similarity to find relevant context. Documents are split into chunks, embedded into vectors, and stored in a vector database. At query time, the query is embedded and compared against stored chunks using cosine similarity.

When to use: Good for well-structured documentation, knowledge bases with clear semantic relationships, and scenarios where semantic meaning matters more than exact keyword matches.

```python
from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def basic_rag_query(query: str, documents: list[str], client: OpenAI, top_k: int = 3) -> str:
    """Basic RAG using semantic similarity search."""
    # Embed all documents
    doc_embeddings = []
    for doc in documents:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=doc
        )
        doc_embeddings.append(response.data[0].embedding)

    # Embed the query
    query_response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = query_response.data[0].embedding

    # Find most similar documents
    similarities = cosine_similarity(
        [query_embedding],
        doc_embeddings
    )[0]

    # Get top-k most relevant documents
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    context = "\n\n".join([documents[i] for i in top_indices])

    # Generate response with context
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Answer based on the retrieved context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )

    return completion.choices[0].message.content
```

Success looks like: Responses accurately reflect information from the retrieved documents, with minimal hallucination and clear source attribution.

### 2. **Contextual Retrieval with Chunk Enrichment**

Standard chunking loses context when documents are split. Contextual retrieval prepends explanatory context to each chunk before embedding, dramatically improving retrieval accuracy. This technique uses an LLM to generate chunk-specific context from the full document.

When to use: Essential for large document collections (SEC filings, legal documents, research papers) where individual chunks lack sufficient context to be understood in isolation.

```python
def create_contextual_chunks(document: str, chunk_size: int = 1000) -> list[dict]:
    """Split document into chunks with added context from the full document."""
    # Split into chunks (simplified for example)
    chunks = [document[i:i+chunk_size] for i in range(0, len(document), chunk_size)]

    contextualized_chunks = []
    for chunk in chunks:
        # Use LLM to add context
        prompt = f"""<document>
{document}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""

        response = client.chat.completions.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": prompt}]
        )

        context = response.choices[0].message.content
        contextualized_chunk = f"{context}\n\n{chunk}"

        contextualized_chunks.append({
            "original": chunk,
            "contextualized": contextualized_chunk,
            "context": context
        })

    return contextualized_chunks
```

Success looks like: 35-49% reduction in retrieval failures compared to standard chunking, especially for queries requiring cross-chunk understanding.

### 3. **Hybrid Search (BM25 + Semantic)**

Combining lexical matching (BM25) with semantic embeddings captures both exact term matches and conceptual similarity. This is particularly effective when queries include technical terms, error codes, or specific identifiers that semantic search might miss.

When to use: Technical documentation, code search, medical/legal texts with specific terminology, or any domain where exact phrase matching matters alongside semantic understanding.

```python
from rank_bm25 import BM25Okapi
import numpy as np

def hybrid_search(query: str, documents: list[str], embeddings: np.ndarray,
                 query_embedding: np.ndarray, bm25_weight: float = 0.3) -> list[int]:
    """Combine BM25 and semantic search with weighted fusion."""
    # BM25 search
    tokenized_docs = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    # Normalize BM25 scores to 0-1
    bm25_scores = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-9)

    # Semantic search
    semantic_scores = cosine_similarity([query_embedding], embeddings)[0]

    # Combine scores with weighting
    embedding_weight = 1.0 - bm25_weight
    combined_scores = (bm25_weight * bm25_scores) + (embedding_weight * semantic_scores)

    # Return indices sorted by combined score
    return np.argsort(combined_scores)[::-1]
```

Success looks like: Better handling of queries with specific terms (error codes, product names) while maintaining semantic understanding for conceptual queries.

### 4. **Reranking with Cross-Encoder**

Initial retrieval often returns many candidates with varying relevance. Reranking uses a more sophisticated model to score each candidate's relevance to the query, then selects only the most pertinent results for generation.

When to use: When you can afford extra latency for better accuracy, especially for critical applications like medical diagnosis, legal research, or financial analysis where retrieval precision is paramount.

```python
def retrieve_and_rerank(query: str, documents: list[str],
                       initial_k: int = 150, final_k: int = 20) -> list[str]:
    """Retrieve many candidates, then rerank for final selection."""
    # Initial retrieval (broad)
    initial_results = hybrid_search(query, documents, initial_k)
    candidates = [documents[i] for i in initial_results]

    # Rerank with cross-encoder (using Cohere reranker as example)
    import cohere
    co = cohere.Client(api_key="...")

    rerank_response = co.rerank(
        query=query,
        documents=candidates,
        top_n=final_k,
        model="rerank-english-v2.0"
    )

    # Extract top reranked documents
    reranked_docs = [
        candidates[result.index]
        for result in rerank_response.results
    ]

    return reranked_docs
```

Success looks like: 67% reduction in retrieval failures when combined with contextual embeddings and BM25, with acceptable latency trade-off.

### 5. **Adaptive Retrieval with Self-RAG**

Not all queries need retrieval. Adaptive RAG decides when to retrieve based on the query type and generates reflection tokens to assess whether retrieved information is relevant and whether the response is supported by that information.

When to use: Mixed workloads where some queries can be answered from parametric knowledge while others need external information, or when minimizing retrieval cost/latency is important.

```python
def adaptive_rag_query(query: str, documents: list[str], client: OpenAI) -> str:
    """Decide whether to retrieve based on query analysis."""
    # First, ask model if retrieval is needed
    decision_prompt = f"""Does this query require external knowledge retrieval to answer accurately?
Query: {query}

Respond with only 'YES' or 'NO'."""

    decision = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": decision_prompt}],
        max_tokens=5
    )

    needs_retrieval = "YES" in decision.choices[0].message.content.upper()

    if not needs_retrieval:
        # Answer directly without retrieval
        return client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": query}]
        ).choices[0].message.content

    # Retrieve and answer with context
    context = retrieve_context(query, documents)

    # Generate with reflection
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Answer based on retrieved context. Include [Supported] if the answer is well-supported by the context, or [Not Supported] if uncertain."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )

    return response.choices[0].message.content
```

Success looks like: Reduced retrieval costs for simple queries while maintaining high accuracy on knowledge-intensive questions.

### 6. **Iterative RAG for Multi-Step Reasoning**

Complex queries require multiple retrieval cycles where each generation step informs what to retrieve next. This pattern alternates between generation and retrieval, using partial answers to guide subsequent searches.

When to use: Multi-hop reasoning tasks, complex research questions, or scenarios where the answer requires synthesizing information from multiple sources in sequence.

```python
def iterative_rag(query: str, documents: list[str], max_iterations: int = 3) -> str:
    """Perform multiple retrieval-generation cycles for complex queries."""
    current_context = ""
    partial_answer = ""

    for iteration in range(max_iterations):
        # Determine what information is still needed
        if iteration == 0:
            search_query = query
        else:
            # Use partial answer to guide next retrieval
            search_query = f"Given that {partial_answer}, what additional information is needed to answer: {query}"

        # Retrieve relevant documents
        retrieved = retrieve_context(search_query, documents)
        current_context += f"\n\nIteration {iteration+1} context:\n{retrieved}"

        # Generate partial answer
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Provide a partial answer based on available context. Identify what information is still missing."},
                {"role": "user", "content": f"Context:\n{current_context}\n\nQuestion: {query}"}
            ]
        )

        partial_answer = response.choices[0].message.content

        # Check if we have enough information
        if "[Complete]" in partial_answer:
            break

    # Generate final answer with all retrieved context
    final_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": f"Context:\n{current_context}\n\nQuestion: {query}\n\nProvide a complete final answer."}
        ]
    )

    return final_response.choices[0].message.content
```

Success looks like: Ability to answer complex multi-step questions that require synthesizing information from multiple documents across several reasoning steps.

## Good Examples vs Bad Examples

### Example 1: Document Chunking Strategy

**Good:**
```python
def chunk_with_overlap(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Create overlapping chunks to preserve context across boundaries."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)  # Overlap for context preservation

    return chunks

# Example output:
# Chunk 1: "...the revenue grew by 3% over the previous quarter."
# Chunk 2: "...over the previous quarter. The company's EBITDA..." (overlap maintains context)
```

**Bad:**
```python
def chunk_without_overlap(text: str, chunk_size: int = 1000) -> list[str]:
    """Split into fixed-size chunks with no overlap - loses boundary context."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# Example output:
# Chunk 1: "...the revenue grew by 3%"
# Chunk 2: "over the previous quarter..." (sentence split, context lost)
```

**Why It Matters:** Without overlap, important information spanning chunk boundaries becomes unretrievable. A query about "quarterly revenue growth" might miss the answer if "revenue grew by 3%" is in one chunk and "previous quarter" is in the next. Overlap ensures semantic units remain intact.

### Example 2: Query-Context Integration

**Good:**
```python
def create_rag_prompt(query: str, retrieved_docs: list[str]) -> str:
    """Clearly separate context from query and instruct model behavior."""
    context = "\n\n".join([f"[Document {i+1}]\n{doc}" for i, doc in enumerate(retrieved_docs)])

    return f"""Answer the following question based on the retrieved documents. If the documents don't contain sufficient information to answer, say so explicitly rather than guessing.

Retrieved Documents:
{context}

Question: {query}

Answer:"""

# Clear separation, explicit instructions, numbered sources
```

**Bad:**
```python
def create_rag_prompt_bad(query: str, retrieved_docs: list[str]) -> str:
    """Unclear mixing of context and query."""
    return f"{' '.join(retrieved_docs)} {query}"

# Context and query mashed together, no instructions, no source tracking
```

**Why It Matters:** Clear separation helps the model distinguish between query and context. Explicit instructions prevent hallucination when information is missing. Numbered sources enable citation and verification. Without this structure, models often ignore the retrieved context or fabricate answers.

### Example 3: Embedding Model Selection

**Good:**
```python
def embed_domain_specific(text: str, domain: str) -> list[float]:
    """Use domain-appropriate embedding model for better retrieval."""
    # For code
    if domain == "code":
        model = "text-embedding-code-002"  # Optimized for code
    # For general text
    elif domain == "general":
        model = "text-embedding-ada-002"
    # For multilingual
    elif domain == "multilingual":
        model = "multilingual-e5-large"

    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding
```

**Bad:**
```python
def embed_one_size_fits_all(text: str) -> list[float]:
    """Always use the same embedding model regardless of content."""
    # Always uses ada-002, even for code or specialized domains
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding
```

**Why It Matters:** General-purpose embedding models struggle with specialized content. Code embeddings understand syntax and semantics of programming languages. Domain-specific models capture terminology and relationships unique to that field. Using the wrong embedding model can result in 30-50% worse retrieval accuracy.

### Example 4: Retrieval Evaluation

**Good:**
```python
def evaluate_retrieval_quality(query: str, retrieved_docs: list[str],
                               ground_truth: str) -> dict:
    """Measure both retrieval accuracy and generation faithfulness."""
    metrics = {}

    # Check if any retrieved doc contains ground truth
    metrics['recall'] = any(ground_truth in doc for doc in retrieved_docs)

    # Measure semantic relevance
    query_embedding = embed_text(query)
    doc_embeddings = [embed_text(doc) for doc in retrieved_docs]
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    metrics['avg_similarity'] = similarities.mean()
    metrics['top1_similarity'] = similarities.max()

    # Verify generation uses retrieved context
    generated = generate_response(query, retrieved_docs)
    metrics['uses_context'] = check_context_usage(generated, retrieved_docs)

    return metrics
```

**Bad:**
```python
def no_retrieval_evaluation(query: str, retrieved_docs: list[str]) -> str:
    """Just generate without checking if retrieval was helpful."""
    return generate_response(query, retrieved_docs)
    # No metrics, no verification, no way to improve system
```

**Why It Matters:** Without evaluation, you can't identify retrieval failures, tune chunk sizes, or optimize embedding models. Measuring recall, relevance, and context usage enables systematic improvement. Production RAG systems need continuous monitoring to detect when retrieval quality degrades.

### Example 5: Handling Failed Retrieval

**Good:**
```python
def robust_rag_query(query: str, documents: list[str],
                    relevance_threshold: float = 0.7) -> str:
    """Gracefully handle cases where retrieval finds nothing relevant."""
    retrieved = retrieve_context(query, documents)

    # Check if retrieval was successful
    if not retrieved or retrieval_confidence(query, retrieved) < relevance_threshold:
        return {
            "answer": "I don't have sufficient information in the knowledge base to answer this question accurately.",
            "confidence": "low",
            "retrieved_docs": [],
            "recommendation": "Consider adding relevant documentation or rephrasing the query."
        }

    # Generate with retrieved context
    answer = generate_with_context(query, retrieved)

    return {
        "answer": answer,
        "confidence": "high",
        "retrieved_docs": retrieved,
        "sources": [doc['id'] for doc in retrieved]
    }
```

**Bad:**
```python
def always_answer_rag(query: str, documents: list[str]) -> str:
    """Force an answer even when retrieval fails."""
    retrieved = retrieve_context(query, documents)

    # Always generate, even with irrelevant or empty context
    return generate_with_context(query, retrieved)

    # Result: hallucinated answer when nothing relevant was found
```

**Why It Matters:** When retrieval fails, forcing an answer leads to hallucination. Users receive confident-sounding but incorrect information, which is worse than admitting uncertainty. Checking retrieval quality and providing explicit "I don't know" responses maintains trust and helps identify gaps in the knowledge base.

## Related Principles

- **[Principle #46 - Context Window Engineering](46-context-window-engineering.md)** - RAG systems must carefully manage retrieved context to fit within model context windows. Chunking strategies and reranking help prioritize the most relevant information within token limits.

- **[Principle #47 - Few-Shot Learning](47-few-shot-learning.md)** - RAG can be combined with few-shot prompting where retrieved examples serve as demonstrations. This hybrid approach grounds both the examples and the response in actual data.

- **[Principle #48 - Chain-of-Thought Prompting](48-chain-of-thought.md)** - Multi-step reasoning in RAG benefits from CoT, where each reasoning step can trigger additional retrieval. Interleaving retrieval with CoT reasoning improves complex question answering.

- **[Principle #51 - Agent Memory Systems](51-agent-memory.md)** - RAG serves as a form of long-term memory for agents, allowing them to recall relevant past experiences or knowledge when making decisions. The retrieval mechanism functions as memory recall.

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - RAG queries should be idempotent—running the same query multiple times should retrieve consistent information. This requires stable indexing and deterministic retrieval.

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - RAG systems benefit from stateless retrieval where each query independently searches the knowledge base. This enables parallel queries and simplifies scaling.

## Common Pitfalls

1. **Chunking at Arbitrary Boundaries**: Splitting documents at fixed character counts without considering semantic units breaks sentences and paragraphs mid-thought, destroying context.
   - Example: "The company's revenue grew by 3" in one chunk and "% in Q2 2023" in another.
   - Impact: Queries about "Q2 2023 revenue growth" fail to retrieve the split information, resulting in incomplete or inaccurate answers.

2. **Ignoring Chunk Overlap**: Without overlap between chunks, information at chunk boundaries becomes unretrievable when queries span those boundaries.
   - Example: A 1000-token chunk ends with "The study concluded that" and the next chunk begins with "exercise reduces heart disease risk."
   - Impact: A query about "study conclusions on heart disease" misses the relevant information because it's split across chunks.

3. **Over-Retrieving Context**: Retrieving too many documents bloats the prompt with irrelevant information, confusing the model and wasting tokens.
   - Example: Including 50 chunks totaling 20,000 tokens when only 3 chunks contain relevant information.
   - Impact: Model struggles to identify key information, response quality degrades, costs increase 10x, and latency suffers.

4. **Under-Retrieving Context**: Retrieving too few documents misses important information needed to fully answer the query.
   - Example: Retrieving only the top 1 chunk when the complete answer requires synthesizing information from 3-4 related chunks.
   - Impact: Partial or incomplete answers, especially for complex multi-aspect questions.

5. **No Contextual Enrichment**: Embedding chunks without adding document-level context results in chunks that can't be understood in isolation.
   - Example: A chunk saying "The company's revenue grew by 3%" without identifying which company or time period.
   - Impact: 35-49% higher retrieval failure rate because chunks lack the semantic information needed to match relevant queries.

6. **Semantic-Only Search**: Relying exclusively on embeddings misses exact matches for technical terms, error codes, or specific identifiers.
   - Example: A query for "error code TS-999" might retrieve general error documentation instead of the specific TS-999 troubleshooting guide.
   - Impact: Users get irrelevant results when they need exact technical information, especially in code documentation or technical support scenarios.

7. **Stale Embeddings**: Not updating embeddings when documents change leads to the retrieval system working with outdated information.
   - Example: Documentation is updated to reflect a new API endpoint, but the old version remains in the embedding index.
   - Impact: RAG system retrieves and cites deprecated information, leading to incorrect usage of APIs or products.

## Tools & Frameworks

### RAG Frameworks & Libraries
- **LangChain**: Comprehensive framework for building RAG applications with built-in support for multiple retrievers, vector stores, and LLMs. Offers document loaders, text splitters, and chains for RAG workflows.
- **LlamaIndex**: Specialized framework for ingesting, structuring, and accessing private data with LLMs. Provides optimized indexing structures and query engines for RAG.
- **Haystack**: Production-ready framework by deepset with pipeline architecture for RAG. Strong support for hybrid search and reranking.
- **DSPy**: Framework for programming foundation models with built-in RAG support and automatic prompt optimization.

### Vector Databases
- **Pinecone**: Managed vector database with high-performance similarity search at scale. Good for production deployments.
- **Chroma**: Open-source embedding database with simple Python API. Excellent for development and prototyping.
- **Weaviate**: Open-source vector database with hybrid search capabilities combining vector and keyword search.
- **FAISS**: Facebook's library for efficient similarity search and clustering of dense vectors. Good for on-premises deployments.
- **Qdrant**: Vector database with filtering support and hybrid search. Strong Rust performance.

### Embedding Models
- **OpenAI Embeddings (ada-002)**: General-purpose embeddings with good performance across domains. 1536 dimensions.
- **Cohere Embed**: Multilingual embeddings with strong semantic understanding. Multiple size options.
- **Voyage AI**: Embeddings optimized for RAG with strong performance on retrieval benchmarks.
- **BGE (BAAI General Embedding)**: Open-source embeddings that can be fine-tuned for specific domains.
- **E5 Embeddings**: Multilingual embeddings from Microsoft with strong cross-lingual retrieval performance.

### Reranking Services
- **Cohere Rerank**: Cross-encoder reranking service that significantly improves retrieval precision.
- **Voyage Reranker**: Reranking model optimized for RAG pipelines with low latency.
- **Jina Reranker**: Open-source reranking models with various size options.

### Evaluation & Monitoring
- **RAGAS**: Framework for evaluating RAG systems on metrics like faithfulness, answer relevance, and context precision.
- **TruLens**: Evaluation and monitoring toolkit for LLM applications with RAG-specific metrics.
- **LangSmith**: Observability platform for tracking RAG pipeline performance and debugging retrieval issues.
- **Weights & Biases**: MLOps platform with support for tracking RAG experiments and metrics.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Documents are chunked with appropriate size (typically 500-1500 tokens) based on content type and model context limits
- [ ] Chunk overlap (typically 10-20% of chunk size) is used to preserve context across boundaries
- [ ] Chunks are enriched with document-level context before embedding (for large document collections)
- [ ] Embedding model is appropriate for content domain (code, general text, multilingual, etc.)
- [ ] Hybrid search combines semantic embeddings with BM25 for lexical matching
- [ ] Retrieved results are reranked to improve precision before passing to the model
- [ ] Number of retrieved chunks balances completeness with context window constraints (typically top 5-20)
- [ ] Prompts clearly separate retrieved context from the query with explicit instructions
- [ ] Generation is evaluated for faithfulness to retrieved context (not hallucinating beyond sources)
- [ ] Retrieval quality is monitored with metrics like recall, precision, and relevance scores
- [ ] System gracefully handles failed retrieval by acknowledging insufficient information
- [ ] Embeddings are updated when source documents change to prevent stale retrievals
- [ ] Token costs are monitored and optimized through contextual compression if needed
- [ ] Sources are tracked and can be cited for verification and debugging

## Metadata

**Category**: Technology
**Principle Number**: 50
**Related Patterns**: Information Retrieval, Knowledge Graphs, Semantic Search, Hybrid Search, Prompt Engineering
**Prerequisites**: Understanding of embeddings, vector databases, similarity search, basic NLP concepts
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
