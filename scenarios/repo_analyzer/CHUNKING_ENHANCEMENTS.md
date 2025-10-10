# Analysis Engine - Chunking Enhancements

## Summary
Enhanced the analysis engine to support chunk-aware processing with context preservation for handling large repositories that exceed LLM token limits.

## Key Enhancements

### 1. Automatic Chunking Detection
- Detects when content exceeds 50K characters
- Automatically switches to chunked processing mode
- Falls back to standard analysis for smaller repos

### 2. Chunk-Aware Analysis Method
- New `analyze_repository_chunked` method for processing large content
- Processes chunks sequentially with context preservation
- Maintains analysis continuity across chunk boundaries

### 3. Progressive Context Passing
- Extracts key findings from each chunk
- Passes summary to next chunk for context
- Builds comprehensive analysis incrementally

### 4. Session Management Integration
- Uses SessionManager from ccsdk_toolkit
- Saves progress after EVERY chunk
- Supports resume from interruption
- Tracks chunk processing state

### 5. Incremental Saves Pattern
- Implements continuous saving (not at intervals)
- Each chunk result immediately persisted
- Zero data loss on interruption
- Can resume exactly where left off

## Technical Implementation

### Chunk Processing Flow
1. Content size check (>50K chars triggers chunking)
2. Content split into 15K token chunks
3. Sequential processing with context preservation
4. Incremental saves after each chunk
5. Results merged into final analysis

### Session Structure
```python
{
    "total_source_chunks": N,
    "total_target_chunks": M,
    "processed_chunks": ["chunk_0", "chunk_1", ...],
    "chunk_results": {
        "chunk_0": {...},
        "chunk_1": {...}
    },
    "status": "analyzing" | "complete",
    "request": "user's analysis request",
    "focus_areas": ["area1", "area2"]
}
```

### Context Preservation
- Previous chunk summary included in next chunk's prompt
- Key patterns and high-priority gaps passed forward
- Maximum 2000 characters of context maintained

## Usage

The enhancement is automatic and transparent:

```python
engine = AnalysisEngine()

# Automatically uses chunking if content is large
result = await engine.analyze_repositories(
    source_content=large_source,  # >50K chars
    target_content=large_target,
    analysis_request="Analyze patterns",
    focus_areas=["architecture", "testing"]
)
```

## Benefits

1. **Handles Large Repositories**: No more token limit errors
2. **Preserves Analysis Quality**: Context maintained across chunks
3. **Resilient to Interruption**: Can resume from any point
4. **Transparent Operation**: Same API, automatic detection
5. **Efficient Processing**: Only processes unfinished chunks on resume

## Testing

Run the test script to verify functionality:
```bash
python scenarios/repo_analyzer/test_chunked_analysis.py
```

## Dependencies

- `amplifier.ccsdk_toolkit.sessions` - For session management
- `scenarios.repo_analyzer.chunking` - For content chunking
- Existing defensive utilities for robust LLM interaction