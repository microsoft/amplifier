# Principle #51 - Agent Memory Systems

## Plain-Language Definition

Agent memory systems enable AI agents to maintain state and context across multiple interactions by storing, retrieving, and managing information from past exchanges. Like human working memory, these systems allow agents to reference previous decisions, learn from past interactions, and maintain coherent long-term understanding.

## Why This Matters for AI-First Development

LLMs are fundamentally stateless—each request starts with a blank slate unless explicitly provided with context. When AI agents build and maintain systems over time, this statelessness creates critical problems: agents forget previous decisions, repeat failed approaches, and lack continuity across sessions.

Agent memory systems provide three essential capabilities for AI-first development:

1. **Continuity across interactions**: Agents can reference past decisions, understand evolving requirements, and maintain coherent long-term projects without repeatedly asking for the same information or making contradictory decisions.

2. **Learning from experience**: Memory systems enable agents to store what worked, what failed, and why—allowing them to improve over time and avoid repeating mistakes. This is crucial for agents that operate autonomously across multiple sessions.

3. **Context-aware decision making**: With access to relevant historical context, agents make better decisions by understanding not just the current request but the broader project goals, architectural patterns, and team preferences that have emerged over time.

Without proper memory systems, AI agents become unreliable partners. They might regenerate code in ways that contradict earlier architectural decisions. They might repeatedly try the same failed approaches without learning. They might ask for the same information multiple times, frustrating users and wasting time. As AI-first systems scale from simple tasks to managing entire codebases, robust memory becomes not just helpful but essential.

## Implementation Approaches

### 1. **Conversation History Management**

Maintain a rolling window of recent interactions with intelligent pruning:

```python
class ConversationMemory:
    """Manages conversation history with token budget awareness"""

    def __init__(self, max_tokens: int = 8000):
        self.messages = []
        self.max_tokens = max_tokens
        self.current_tokens = 0

    def add_exchange(self, user_msg: str, assistant_msg: str):
        """Add user-assistant exchange with automatic pruning"""
        exchange = {
            "user": user_msg,
            "assistant": assistant_msg,
            "tokens": count_tokens(user_msg + assistant_msg)
        }

        self.messages.append(exchange)
        self.current_tokens += exchange["tokens"]

        # Prune oldest messages if over budget
        while self.current_tokens > self.max_tokens and len(self.messages) > 1:
            removed = self.messages.pop(0)
            self.current_tokens -= removed["tokens"]

    def get_context(self) -> list[dict]:
        """Get formatted messages for LLM context"""
        context = []
        for msg in self.messages:
            context.append({"role": "user", "content": msg["user"]})
            context.append({"role": "assistant", "content": msg["assistant"]})
        return context
```

When to use: For interactive agents that need recent context but don't require full conversation history.

### 2. **Semantic Memory with Vector Storage**

Store facts and knowledge as searchable embeddings:

```python
from typing import List, Dict
import numpy as np

class SemanticMemory:
    """Stores facts with semantic search capability"""

    def __init__(self, embedding_model):
        self.facts: List[Dict] = []
        self.embeddings: List[np.ndarray] = []
        self.model = embedding_model

    def store_fact(self, content: str, metadata: dict = None):
        """Store a fact with its embedding"""
        embedding = self.model.embed(content)
        fact = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": now()
        }
        self.facts.append(fact)
        self.embeddings.append(embedding)

    def retrieve_relevant(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve most relevant facts for a query"""
        query_embedding = self.model.embed(query)

        # Calculate cosine similarity
        similarities = [
            np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            for emb in self.embeddings
        ]

        # Get top-k most similar
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.facts[i] for i in top_indices]
```

When to use: For agents that need to recall specific facts, decisions, or patterns from a large knowledge base based on semantic relevance.

### 3. **Episodic Memory for Decision Tracking**

Record specific events and decisions with structured metadata:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Episode:
    """Represents a specific decision or event"""
    timestamp: datetime
    action: str
    context: str
    outcome: str
    reasoning: str
    success: bool
    tags: list[str]

class EpisodicMemory:
    """Tracks specific decisions and their outcomes"""

    def __init__(self):
        self.episodes: list[Episode] = []

    def record_decision(
        self,
        action: str,
        context: str,
        reasoning: str,
        tags: list[str] = None
    ) -> str:
        """Record a decision being made"""
        episode = Episode(
            timestamp=datetime.now(),
            action=action,
            context=context,
            outcome="pending",
            reasoning=reasoning,
            success=False,
            tags=tags or []
        )
        self.episodes.append(episode)
        return f"episode_{len(self.episodes)}"

    def record_outcome(self, episode_id: str, outcome: str, success: bool):
        """Record the outcome of a decision"""
        idx = int(episode_id.split("_")[1]) - 1
        self.episodes[idx].outcome = outcome
        self.episodes[idx].success = success

    def get_similar_decisions(self, context: str, limit: int = 5) -> list[Episode]:
        """Find past decisions in similar contexts"""
        # In production, use semantic similarity
        return [ep for ep in self.episodes if context in ep.context][:limit]
```

When to use: For agents that need to learn from past attempts, especially when debugging or making architectural decisions.

### 4. **Working Memory for Active Tasks**

Maintain state for current multi-step operations:

```python
class WorkingMemory:
    """Manages state for active, multi-step tasks"""

    def __init__(self):
        self.active_tasks = {}
        self.task_state = {}

    def start_task(self, task_id: str, goal: str, plan: list[str]):
        """Initialize a new task with its plan"""
        self.active_tasks[task_id] = {
            "goal": goal,
            "plan": plan,
            "current_step": 0,
            "completed_steps": [],
            "variables": {},
            "started_at": now()
        }

    def update_task_state(self, task_id: str, step_result: dict):
        """Update task state after completing a step"""
        task = self.active_tasks[task_id]
        task["completed_steps"].append({
            "step": task["current_step"],
            "result": step_result,
            "completed_at": now()
        })
        task["current_step"] += 1

        # Update working variables
        if "variables" in step_result:
            task["variables"].update(step_result["variables"])

    def get_task_context(self, task_id: str) -> dict:
        """Get current context for task decision-making"""
        task = self.active_tasks[task_id]
        return {
            "goal": task["goal"],
            "remaining_steps": task["plan"][task["current_step"]:],
            "completed_steps": task["completed_steps"],
            "current_variables": task["variables"]
        }
```

When to use: For agents executing complex, multi-step workflows where state must be maintained across steps.

### 5. **Memory Consolidation with Summarization**

Compress old memories to preserve key information while reducing token usage:

```python
class ConsolidatingMemory:
    """Automatically consolidates old memories into summaries"""

    def __init__(self, llm, consolidation_threshold: int = 10):
        self.llm = llm
        self.recent_memories: list[dict] = []
        self.consolidated_summaries: list[str] = []
        self.threshold = consolidation_threshold

    def add_memory(self, memory: dict):
        """Add new memory and consolidate if threshold reached"""
        self.recent_memories.append(memory)

        if len(self.recent_memories) >= self.threshold:
            self._consolidate()

    def _consolidate(self):
        """Use LLM to create summary of recent memories"""
        memories_text = "\n\n".join([
            f"- {m['action']}: {m['outcome']}"
            for m in self.recent_memories
        ])

        prompt = f"""Summarize these recent actions into key lessons learned:

{memories_text}

Focus on:
- Important patterns discovered
- Successful approaches
- Failed attempts and why
- Architectural decisions made"""

        summary = self.llm.generate(prompt)
        self.consolidated_summaries.append(summary)
        self.recent_memories.clear()

    def get_full_context(self) -> str:
        """Get consolidated summaries plus recent memories"""
        context_parts = []

        if self.consolidated_summaries:
            context_parts.append("Historical Context:\n" + "\n\n".join(self.consolidated_summaries))

        if self.recent_memories:
            context_parts.append("Recent Actions:\n" + "\n".join([
                f"- {m['action']}: {m['outcome']}"
                for m in self.recent_memories
            ]))

        return "\n\n".join(context_parts)
```

When to use: For long-running agents that accumulate too much history to fit in context windows.

### 6. **Hierarchical Memory Architecture**

Combine multiple memory types with intelligent routing:

```python
class HierarchicalMemory:
    """Orchestrates multiple memory systems"""

    def __init__(self):
        self.conversation = ConversationMemory(max_tokens=4000)
        self.semantic = SemanticMemory(embedding_model)
        self.episodic = EpisodicMemory()
        self.working = WorkingMemory()

    def store(self, content: str, memory_type: str, metadata: dict = None):
        """Route to appropriate memory system"""
        if memory_type == "conversation":
            self.conversation.add_exchange(content, metadata.get("response", ""))
        elif memory_type == "fact":
            self.semantic.store_fact(content, metadata)
        elif memory_type == "decision":
            self.episodic.record_decision(
                content,
                metadata.get("context", ""),
                metadata.get("reasoning", ""),
                metadata.get("tags", [])
            )

    def recall(self, query: str, context_type: str = "auto") -> str:
        """Retrieve relevant memories for current context"""
        if context_type == "auto":
            # Determine what kind of memory is needed
            context_type = self._classify_query(query)

        memories = []

        if context_type in ["conversation", "all"]:
            memories.extend(self.conversation.get_context())

        if context_type in ["fact", "all"]:
            facts = self.semantic.retrieve_relevant(query, top_k=3)
            memories.extend([f["content"] for f in facts])

        if context_type in ["decision", "all"]:
            episodes = self.episodic.get_similar_decisions(query, limit=3)
            memories.extend([
                f"Past decision: {ep.action} -> {ep.outcome}"
                for ep in episodes
            ])

        return "\n\n".join(memories)
```

When to use: For production agents that need multiple types of memory working together.

## Good Examples vs Bad Examples

### Example 1: Storing Architectural Decisions

**Good:**
```python
class ArchitectureMemory:
    """Proper storage of architectural decisions"""

    def record_decision(self, decision: str, rationale: str, alternatives: list[str]):
        """Store decision with full context"""
        return {
            "decision": decision,
            "rationale": rationale,
            "alternatives_considered": alternatives,
            "timestamp": now(),
            "project_state": get_current_project_snapshot(),
            "tags": extract_tags(decision)
        }

# Agent can later recall: "Why did we choose microservices?"
# Memory system returns full context including alternatives and rationale
```

**Bad:**
```python
class ArchitectureMemory:
    """Loses critical context"""

    def record_decision(self, decision: str):
        """Only stores the decision"""
        return {
            "decision": decision,
            "timestamp": now()
        }

# Agent later asks: "Why did we choose microservices?"
# Memory system: "You chose microservices" (no rationale or alternatives)
```

**Why It Matters:** Architectural decisions need full context. Without rationale and alternatives, agents can't understand trade-offs or validate whether old decisions still make sense as requirements evolve.

### Example 2: Learning from Failed Attempts

**Good:**
```python
def attempt_fix(self, issue: str) -> bool:
    """Learn from failures by recording attempts"""
    # Check if we've tried this before
    past_attempts = self.episodic.get_similar_decisions(issue)
    failed_approaches = [a.action for a in past_attempts if not a.success]

    # Avoid repeating failures
    approach = self.generate_approach(issue, avoid=failed_approaches)

    success = self.execute(approach)

    # Record for future learning
    self.episodic.record_decision(
        action=approach,
        context=issue,
        reasoning=f"Avoided: {failed_approaches}",
        tags=["bugfix", "learned"]
    )
    self.episodic.record_outcome(episode_id, "fixed" if success else "failed", success)

    return success
```

**Bad:**
```python
def attempt_fix(self, issue: str) -> bool:
    """No learning from past failures"""
    # Generate approach without checking history
    approach = self.generate_approach(issue)

    success = self.execute(approach)

    # Don't record the attempt
    return success

# Agent will keep trying the same failed approaches
```

**Why It Matters:** Without learning from failures, agents waste time and resources repeating the same mistakes. Memory enables progressive refinement of strategies.

### Example 3: Context Window Management

**Good:**
```python
class TokenAwareMemory:
    """Manages context budget efficiently"""

    def build_context(self, query: str, max_tokens: int = 8000) -> str:
        """Prioritize most relevant memories within token budget"""
        # Get all potentially relevant memories
        candidates = [
            *self.get_recent_conversation(limit=5),
            *self.get_relevant_facts(query, limit=10),
            *self.get_similar_episodes(query, limit=5)
        ]

        # Rank by relevance and recency
        ranked = self.rank_by_importance(candidates, query)

        # Fill context up to token limit
        context = []
        tokens_used = 0
        for item in ranked:
            item_tokens = count_tokens(item)
            if tokens_used + item_tokens <= max_tokens:
                context.append(item)
                tokens_used += item_tokens
            else:
                break

        return "\n\n".join(context)
```

**Bad:**
```python
class TokenAwareMemory:
    """Exceeds context limits"""

    def build_context(self, query: str) -> str:
        """Dump everything into context"""
        return "\n\n".join([
            *self.conversation_history,  # Could be huge
            *self.all_facts,  # Entire database
            *self.all_episodes  # Everything ever done
        ])
        # Exceeds context window, gets truncated, loses critical info
```

**Why It Matters:** Context windows have limits. Without intelligent prioritization, critical information gets truncated while irrelevant details consume tokens.

### Example 4: Memory Retrieval Strategy

**Good:**
```python
class SmartRetrieval:
    """Context-aware memory retrieval"""

    def retrieve_for_task(self, task: str, task_type: str) -> dict:
        """Get relevant memories based on task type"""
        if task_type == "debugging":
            return {
                "recent_changes": self.get_recent_code_changes(),
                "similar_bugs": self.get_similar_issues(task),
                "past_solutions": self.get_successful_fixes(task)
            }
        elif task_type == "feature":
            return {
                "architecture_decisions": self.get_arch_decisions(),
                "similar_features": self.get_similar_implementations(task),
                "coding_patterns": self.get_project_patterns()
            }
        elif task_type == "refactor":
            return {
                "past_refactors": self.get_refactoring_history(),
                "code_smells": self.get_identified_issues(),
                "team_preferences": self.get_style_decisions()
            }
```

**Bad:**
```python
class SmartRetrieval:
    """Always returns same generic context"""

    def retrieve_for_task(self, task: str, task_type: str) -> dict:
        """Generic retrieval regardless of task"""
        return {
            "recent": self.get_recent(limit=10),
            "all": self.get_all_memories()
        }
        # Debugging gets architecture decisions, features get bug history
```

**Why It Matters:** Different tasks need different types of memory. Generic retrieval wastes tokens on irrelevant context and misses critical information.

### Example 5: Memory Persistence

**Good:**
```python
class PersistentMemory:
    """Saves memory to disk for cross-session continuity"""

    def __init__(self, project_path: Path):
        self.memory_file = project_path / ".agent_memory" / "memory.json"
        self.load_from_disk()

    def load_from_disk(self):
        """Load existing memories on startup"""
        if self.memory_file.exists():
            with open(self.memory_file) as f:
                data = json.load(f)
                self.facts = data.get("facts", [])
                self.episodes = data.get("episodes", [])
                self.summaries = data.get("summaries", [])

    def save_to_disk(self):
        """Persist memories after each session"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump({
                "facts": self.facts,
                "episodes": self.episodes,
                "summaries": self.summaries,
                "last_updated": now().isoformat()
            }, f, indent=2)
```

**Bad:**
```python
class PersistentMemory:
    """Loses all memory between sessions"""

    def __init__(self):
        self.facts = []
        self.episodes = []
        self.summaries = []
        # No persistence - every session starts fresh
        # Agent forgets all previous interactions and decisions
```

**Why It Matters:** Agents working on long-term projects need continuity across sessions. Without persistence, agents lose valuable context and repeat work.

## Related Principles

- **[Principle #50 - RAG Patterns](50-rag-patterns.md)** - RAG provides retrieval mechanisms that memory systems use to access external knowledge stores

- **[Principle #52 - Multi-Agent Coordination](52-multi-agent-coordination.md)** - Shared memory enables agents to coordinate and avoid conflicting decisions

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - Memory systems manage state explicitly, allowing agents to remain stateless while maintaining continuity

- **[Principle #7 - Regenerate, Don't Edit](../process/07-regenerate-dont-edit.md)** - Memory of past regenerations helps agents improve code progressively

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Memory of validation results prevents repeating known failures

- **[Principle #23 - Protected Self-Healing Kernel](23-protected-self-healing-kernel.md)** - Memory systems store recovery patterns for self-healing operations

## Common Pitfalls

1. **Infinite Memory Growth**: Storing everything without pruning or summarization leads to unbounded memory usage and degraded retrieval performance.
   - Example: Keeping full conversation history for year-long projects
   - Impact: Context window exhaustion, slow retrieval, irrelevant information pollution

2. **No Memory Invalidation**: Failing to mark outdated memories as stale when requirements or architecture changes.
   - Example: Remembering architectural decisions that were later reversed
   - Impact: Agents make decisions based on obsolete information

3. **Ignoring Token Budgets**: Building context that exceeds model context windows, causing truncation and information loss.
   - Example: Adding 50,000 tokens of history to every request
   - Impact: Critical recent context gets truncated, model performance degrades

4. **Poor Retrieval Relevance**: Using simple keyword matching instead of semantic similarity for memory retrieval.
   - Example: Missing relevant memories because different words were used
   - Impact: Agents lack important context, make suboptimal decisions

5. **No Memory Verification**: Storing agent outputs without verifying accuracy, leading to accumulation of hallucinations.
   - Example: Agent "remembers" a function that doesn't exist
   - Impact: Compounding errors, unreliable knowledge base

6. **Mixing Memory Types**: Treating episodic, semantic, and working memory the same way instead of managing them distinctly.
   - Example: Storing temporary task state in long-term fact database
   - Impact: Confusion between different types of information, retrieval issues

7. **Missing Temporal Context**: Not recording timestamps and sequencing, losing ability to understand evolution of decisions.
   - Example: Knowing a decision was made but not when or what came before/after
   - Impact: Can't understand decision context or verify if still relevant

## Tools & Frameworks

### Vector Databases
- **Pinecone**: Managed vector database optimized for semantic search at scale
- **Weaviate**: Open-source vector database with built-in ML models
- **Chroma**: Lightweight embedding database designed for LLM applications
- **Milvus**: High-performance vector database for similarity search

### Memory Frameworks
- **MemGPT**: Hierarchical memory system with automatic memory management
- **LangMem**: LangChain's memory abstractions for various memory types
- **Zep**: Long-term memory store specifically designed for conversational AI
- **Mem0**: Vector-based memory layer for personalized AI applications

### State Management
- **Redis**: Fast in-memory store for working memory and session state
- **Momento**: Serverless cache for transient agent state
- **DynamoDB**: Scalable database for persistent agent memory

### Embedding Models
- **OpenAI Embeddings**: High-quality text embeddings via API
- **Sentence-Transformers**: Open-source embedding models
- **Cohere Embed**: Enterprise-grade embeddings with multilingual support

### Memory Patterns
- **LangChain Memory**: Built-in memory types (ConversationBuffer, ConversationSummary, VectorStore)
- **LlamaIndex**: Memory modules for RAG and agent systems
- **Semantic Kernel**: Memory connectors and plugins

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Memory system has clear separation between short-term, working, and long-term memory
- [ ] Token budgets are enforced with intelligent prioritization of relevant memories
- [ ] Semantic search capability exists for retrieving relevant historical context
- [ ] Memory persistence ensures continuity across sessions and restarts
- [ ] Stale or outdated memories can be invalidated or updated
- [ ] Episodic memory records decisions with full context (rationale, alternatives, outcomes)
- [ ] Failed attempts are stored to prevent repeating known failures
- [ ] Memory retrieval strategy varies based on current task type
- [ ] Consolidation mechanism summarizes old memories when they grow too large
- [ ] Memory verification prevents accumulation of hallucinated information
- [ ] Temporal context (timestamps, sequences) is preserved for all memories
- [ ] Cross-session memory includes project state and architectural decisions

## Metadata

**Category**: Technology
**Principle Number**: 51
**Related Patterns**: Vector Databases, Semantic Search, Context Management, State Machines
**Prerequisites**: Understanding of LLM context windows, embeddings, and vector similarity
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
