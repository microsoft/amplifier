# Implementation Specification: IdeaSynthesizer

## Design Overview

The IdeaSynthesizer module follows a three-phase approach: Load → Synthesize → Persist. It leverages the Claude Code SDK with specialized subagents to generate net-new insights from document summaries while maintaining clear provenance tracking.

## Architecture

### Core Components

```
idea_synthesizer/
├── __init__.py           # Public API exports
├── core.py              # Main synthesize_ideas implementation
├── models.py            # Data models (SummaryRecord, IdeaRecord, etc.)
├── ai_synthesis.py     # Claude SDK integration
├── deduplication.py    # ID generation and dedup logic
├── persistence.py      # File I/O and atomic writes
└── validation.py       # Input validation and novelty checking
```

### Processing Pipeline

```mermaid
flowchart LR
    A[Load Summaries] --> B[Validate Inputs]
    B --> C[Batch Summaries]
    C --> D[AI Synthesis]
    D --> E[Novelty Check]
    E --> F[Deduplicate]
    F --> G[Persist Ideas]
```

## Claude Code SDK Integration

### Configuration

```python
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

# SDK configuration for synthesis
SDK_OPTIONS = ClaudeCodeOptions(
    system_prompt="""
    You are an idea synthesizer specializing in finding net-new insights 
    across multiple documents. Generate only novel ideas that combine 
    concepts from different sources, never restate single documents.
    """,
    max_turns=1,
    permission_mode="plan",  # Read-only during synthesis
    allowed_tools=["Read", "Grep"],  # Limited tools for safety
    max_thinking_tokens=12000,  # Allow deep reasoning
)
```

### Synthesis Prompt Template

```python
SYNTHESIS_PROMPT = """
Analyze these {count} document summaries and generate {max_ideas} net-new ideas 
that synthesize insights across multiple sources.

Summaries:
{summaries_text}

Requirements:
- Each idea must combine insights from at least {min_sources} different summaries
- Ideas must be genuinely novel, not restatements of any single summary
- Include clear rationale for why each idea is net-new
- Score each idea's novelty (0-1), impact (0-1), and effort (0-1)
- Tag ideas with relevant categories

Output as JSON array with this structure:
{json_schema}

Focus on practical, actionable ideas that could improve the project.
"""
```

## Key Algorithms

### 1. Summary Batching

```python
def batch_summaries(summaries: List[SummaryRecord], batch_size: int = 10):
    """Split summaries into processable batches."""
    # Sort by digest for deterministic ordering
    sorted_summaries = sorted(summaries, key=lambda s: s.digest)
    
    for i in range(0, len(sorted_summaries), batch_size):
        yield sorted_summaries[i:i + batch_size]
```

### 2. ID Generation

```python
import hashlib

def generate_idea_id(title: str, source_digests: List[str]) -> str:
    """Generate stable ID from title and sources."""
    # Normalize title
    normalized_title = title.lower().strip()
    
    # Sort digests for stability
    sorted_digests = sorted(source_digests)
    
    # Create composite key
    composite = f"{normalized_title}|{'|'.join(sorted_digests)}"
    
    # Generate hash
    return hashlib.sha1(composite.encode()).hexdigest()[:12]
```

### 3. Novelty Validation

```python
async def validate_novelty(idea: IdeaRecord, summaries: List[SummaryRecord]):
    """Ensure idea is genuinely cross-source."""
    # Check that idea text doesn't just paraphrase one summary
    for summary in summaries:
        similarity = calculate_similarity(idea.summary, summary.summary)
        if similarity > 0.85:  # Too similar to single source
            return False
    
    # Verify multiple source citations
    if len(idea.sources) < 2:
        return False
    
    return True
```

### 4. Deduplication

```python
def deduplicate_ideas(ideas: List[IdeaRecord]) -> List[IdeaRecord]:
    """Remove duplicate ideas based on ID and similarity."""
    seen_ids = set()
    seen_titles = set()
    unique_ideas = []
    
    for idea in ideas:
        # Check exact ID match
        if idea.id in seen_ids:
            continue
            
        # Check fuzzy title match
        normalized = normalize_text(idea.title)
        if any(similarity(normalized, t) > 0.9 for t in seen_titles):
            continue
        
        seen_ids.add(idea.id)
        seen_titles.add(normalized)
        unique_ideas.append(idea)
    
    return unique_ideas
```

## AI Processing Flow

```python
async def synthesize_with_ai(batch: List[SummaryRecord], params: SynthesisParams):
    """Core AI synthesis using Claude SDK."""
    
    async with ClaudeSDKClient(options=SDK_OPTIONS) as client:
        # Format summaries for context
        summaries_text = format_summaries_for_ai(batch)
        
        # Build prompt
        prompt = SYNTHESIS_PROMPT.format(
            count=len(batch),
            summaries_text=summaries_text,
            max_ideas=params.max_ideas,
            min_sources=params.min_sources_per_idea,
            json_schema=IdeaRecord.json_schema()
        )
        
        # Query Claude
        await client.query(prompt)
        
        # Collect streaming response
        response = ""
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        response += block.text
        
        # Parse JSON response
        ideas = parse_ai_response(response)
        
        # Add source references
        for idea in ideas:
            idea.sources = map_sources_to_summaries(idea, batch)
        
        return ideas
```

## Error Handling Strategy

### Retry Logic

```python
import asyncio
from typing import Optional

async def retry_with_backoff(
    func, 
    max_attempts: int = 3,
    backoff_base: float = 1.5
) -> Optional[Any]:
    """Retry with exponential backoff."""
    delay = 1.0
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except (AIUnavailableError, asyncio.TimeoutError) as e:
            if attempt == max_attempts - 1:
                logger.error(f"Final attempt failed: {e}")
                return None
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
            await asyncio.sleep(delay)
            delay *= backoff_base
```

### Partial Results Handling

```python
def save_partial_results(ideas: List[IdeaRecord], error: Exception, output_dir: Path):
    """Save what we have even if synthesis incomplete."""
    partial_dir = output_dir / "_partial" / datetime.now().isoformat()
    partial_dir.mkdir(parents=True, exist_ok=True)
    
    # Save successful ideas
    for idea in ideas:
        save_idea(idea, partial_dir)
    
    # Log the error
    error_log = partial_dir / "error.json"
    error_log.write_text(json.dumps({
        "error": str(error),
        "timestamp": datetime.now().isoformat(),
        "ideas_saved": len(ideas)
    }))
```

## File I/O Patterns

### Atomic Write Pattern

```python
def atomic_write(path: Path, content: str):
    """Write file atomically using temp + rename."""
    temp_path = path.with_suffix('.tmp')
    
    try:
        # Write to temp file
        temp_path.write_text(content)
        
        # Atomic rename
        temp_path.replace(path)
    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise
```

### Append-Only Index

```python
def append_to_index(idea: IdeaRecord, index_path: Path):
    """Append idea to index file (idempotent)."""
    # Check if already exists
    if index_path.exists():
        with open(index_path, 'r') as f:
            for line in f:
                if json.loads(line)['id'] == idea.id:
                    return  # Already indexed
    
    # Append new entry
    with open(index_path, 'a') as f:
        f.write(json.dumps(idea.dict()) + '\n')
```

## Testing Strategy

### Unit Tests

```python
def test_id_generation():
    """Test stable ID generation."""
    title = "Improve API Performance"
    sources = ["digest1", "digest2"]
    
    id1 = generate_idea_id(title, sources)
    id2 = generate_idea_id(title, sources[::-1])  # Reversed
    
    assert id1 == id2  # Order-independent
    assert len(id1) == 12  # Expected length
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_synthesis_with_mock_ai():
    """Test full synthesis with mocked Claude responses."""
    with mock_claude_sdk(response=SAMPLE_IDEAS_JSON):
        summaries = [create_test_summary() for _ in range(5)]
        params = SynthesisParams(max_ideas=3)
        
        ideas = await synthesize_ideas(summaries, params)
        
        assert len(ideas) == 3
        assert all(len(idea.sources) >= 2 for idea in ideas)
```

### Performance Tests

```python
@pytest.mark.performance
async def test_large_batch_performance():
    """Ensure performance with 100+ summaries."""
    summaries = [create_test_summary() for _ in range(100)]
    params = SynthesisParams(max_ideas=50)
    
    start = time.time()
    ideas = await synthesize_ideas(summaries, params)
    duration = time.time() - start
    
    assert duration < 120  # Under 2 minutes
    assert len(ideas) <= 50
```

## Monitoring and Observability

### Metrics Collection

```python
class SynthesisMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.summaries_processed = 0
        self.ideas_generated = 0
        self.ai_calls = 0
        self.errors = []
    
    def to_dict(self):
        return {
            "duration_seconds": time.time() - self.start_time,
            "summaries_processed": self.summaries_processed,
            "ideas_generated": self.ideas_generated,
            "ideas_per_summary": self.ideas_generated / max(self.summaries_processed, 1),
            "ai_calls": self.ai_calls,
            "error_count": len(self.errors),
            "timestamp": datetime.now().isoformat()
        }
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

async def log_synthesis_progress(event: str, **kwargs):
    """Structured logging for observability."""
    await logger.ainfo(
        event,
        module="idea_synthesizer",
        timestamp=datetime.now().isoformat(),
        **kwargs
    )
```

## Security Considerations

1. **Input Validation**: Validate all summaries before processing
2. **Output Sanitization**: Ensure no sensitive data in outputs
3. **File Permissions**: Write files with 0644 permissions
4. **Path Traversal**: Validate all paths stay within output_dir
5. **AI Prompt Injection**: Sanitize summary text before AI processing

## Performance Optimizations

1. **Batch Processing**: Process summaries in groups of 10
2. **Async I/O**: Use asyncio for all file operations
3. **Caching**: Cache similarity calculations
4. **Early Exit**: Stop if novelty threshold not met
5. **Parallel Synthesis**: Run multiple batches concurrently

## Non-Goals (v1.0)

- No embeddings/vector DB (rely on Claude's reasoning)
- No UI (CLI/API only)
- No real-time updates (batch processing only)
- No automatic reprocessing (manual trigger required)
