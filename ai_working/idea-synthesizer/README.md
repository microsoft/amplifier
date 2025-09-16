# Idea Synthesizer CLI - Project Plan

## Overview
A modular CLI utility that processes markdown documents through AI-powered stages to extract, synthesize, and expand cross-cutting ideas. Built following the "bricks and studs" philosophy with clear module boundaries and stable interfaces.

## Project Goals
1. **Document Summarization**: Process markdown files into concise, insightful summaries
2. **Cross-cutting Synthesis**: Identify patterns and themes across multiple documents
3. **Contextual Expansion**: Deep-dive into synthesized ideas using full source context
4. **Resilient Processing**: Support resume/retry at any stage via checkpointing

## Architecture

### Core Modules (Bricks)
- **file_scanner**: Discover and enumerate markdown files
- **summarizer**: Generate AI summaries of individual documents
- **synthesizer**: Find cross-cutting themes across summaries
- **expander**: Expand ideas using full source context

### Infrastructure Modules (Studs)
- **claude_client**: Wrapper for Claude Code SDK operations
- **state_manager**: Persist and restore processing state
- **orchestrator**: Coordinate workflow and manage stages
- **cli_interface**: Parse arguments and display results

## Module Generation Order
1. **claude_client** - Foundation for all AI operations
2. **state_manager** - Enable checkpointing early
3. **file_scanner** - Simple, testable first module
4. **summarizer** - First AI-integrated module
5. **synthesizer** - Build on summarizer patterns
6. **expander** - Most complex processing module
7. **orchestrator** - Ties everything together
8. **cli_interface** - User-facing layer

## Implementation Phases

### Phase 1: Foundation (Modules 1-3)
- Set up project structure
- Implement claude_client with 120s timeout handling
- Create state_manager with JSON persistence
- Build file_scanner for document discovery

### Phase 2: Core Processing (Module 4)
- Implement summarizer with Claude integration
- Add checkpointing support
- Create test suite for summarization

### Phase 3: Synthesis (Modules 5-6)
- Build synthesizer for pattern recognition
- Implement expander for deep analysis
- Integrate both with orchestrator

### Phase 4: Polish (Modules 7-8)
- Complete orchestrator with full workflow
- Add cli_interface with progress indicators
- Comprehensive testing and documentation

## Key Design Decisions

### Module Boundaries
Each module has:
- **Single Responsibility**: One clear purpose
- **Stable Interface**: Contract defines all connection points
- **Independent Testing**: Can be tested in isolation
- **Clean Dependencies**: Explicit, minimal coupling

### AI Integration Pattern
```python
async def ai_operation(prompt: str) -> str:
    async with asyncio.timeout(120):  # Per DISCOVERIES.md
        async with ClaudeSDKClient(...) as client:
            await client.query(prompt)
            # Stream and collect response
```

### State Management Pattern
```python
# Checkpoint after every significant operation
state = state_manager.load(checkpoint_key)
if not state:
    result = await process()
    state_manager.save(checkpoint_key, result)
```

### Error Handling Strategy
- **FILE_NOT_FOUND**: Clear user message, suggest fix
- **AI_SERVICE_ERROR**: Retry with exponential backoff
- **EXTRACTION_FAILED**: Log details, continue with next item
- **All errors**: Include recovery instructions

## Module Artifacts

### Contract Files (Define "Studs")
- `{module}_CONTRACT.yaml`: External interface specification
- Defines inputs, outputs, errors, dependencies
- Version controlled for compatibility
- Used by other modules to connect

### Specification Files (Guide Implementation)
- `{module}_SPEC.yaml`: Internal implementation guidance
- Defines behaviors, algorithms, data flow
- Testing requirements and non-functional aspects
- Used by AI to generate implementation

## Success Metrics
- **Module Independence**: Each module can be regenerated without breaking others
- **Test Coverage**: >80% for critical paths
- **Performance**: <30s per document (p99)
- **Reliability**: >95% success rate with retry
- **Code Size**: Each module <500 lines

## Dependencies
- Python 3.11+
- claude-code-sdk
- click (CLI framework)
- pydantic (data validation)
- asyncio (async operations)

## Next Steps
1. Generate claude_client module using module generator
2. Validate contract against implementation
3. Create integration tests
4. Move to next module in sequence