# AI-First Tool Builder

## Overview

This is the new AI-first architecture for building Claude Code tools from natural language descriptions. The system uses pure AI intelligence for understanding requirements and generating code, while using structured code only for orchestration and state management.

## Architecture

```
tool_builder/
├── pipeline.py          # Main orchestrator
├── state.py            # State management with resumability
├── stages/             # AI-powered processing stages
│   ├── requirements.py # AI requirements analysis
│   ├── analysis.py     # AI metacognitive analysis
│   ├── generation.py   # AI code generation
│   └── validation.py   # AI quality validation
└── cli.py              # Command-line interface
```

## Key Features

### 1. Pure AI Intelligence
- **No templates or rules**: AI understands requirements directly
- **No keyword matching**: AI analyzes intent and context
- **No regex patterns**: AI validates quality holistically

### 2. Resumable Pipeline
- **Save after every stage**: Never lose progress
- **Resume from any point**: Pick up where you left off
- **Cloud-sync safe**: Handles OneDrive/Dropbox delays

### 3. State Management
- **Persistent state tracking**: All progress saved to disk
- **Multiple tools in parallel**: Build several tools at once
- **Failure recovery**: Resume after errors or interruptions

## Usage

### Command Line

```bash
# Build a new tool
python -m amplifier.tools.tool_builder.cli build "file-reader" "A tool that reads files from disk"

# Resume an incomplete build
python -m amplifier.tools.tool_builder.cli resume

# Check build status
python -m amplifier.tools.tool_builder.cli status "file-reader"

# Clean up completed builds
python -m amplifier.tools.tool_builder.cli cleanup
```

### Python API

```python
import asyncio
from amplifier.tools.tool_builder import ToolBuilderPipeline

async def build_tool():
    pipeline = ToolBuilderPipeline()

    result = await pipeline.build_tool(
        tool_name="my-tool",
        description="A tool that does something useful",
        resume=False,  # Set True to resume previous build
        skip_validation=False  # Set True for faster builds
    )

    # Generated code is in result["generated_code"]
    for filename, content in result["generated_code"].items():
        print(f"Generated {filename}")
        print(content)

asyncio.run(build_tool())
```

## Pipeline Stages

### 1. Requirements Analysis
- Analyzes natural language description
- Extracts core functionality
- Identifies inputs, outputs, dependencies
- Determines error handling needs

### 2. Metacognitive Analysis
- Analyzes implementation approach
- Determines architecture patterns
- Identifies complexity and risks
- Plans code organization

### 3. Code Generation
- Generates complete implementation
- Creates test files if needed
- Follows Claude Code patterns
- Includes documentation

### 4. Quality Validation
- Validates generated code
- Checks requirements coverage
- Assesses code quality
- Provides improvement recommendations

## State Files

State files are stored in `~/.amplifier/tool_builder_state/` by default.

Each state file contains:
- Tool metadata (name, description)
- Progress tracking (completed stages)
- Stage outputs (requirements, analysis, code)
- Metrics (AI calls, tokens used)

## Error Recovery

The system automatically handles:
- **AI timeouts**: Retries with exponential backoff
- **JSON parsing errors**: Defensive parsing utilities
- **File I/O errors**: Cloud-sync aware retries
- **Stage failures**: Save state and allow resume

## Configuration

### Timeouts
- Requirements: 120 seconds
- Analysis: 120 seconds
- Generation: 180 seconds (longer for code)
- Validation: 120 seconds

### AI Settings
- Uses ClaudeSession from CCSDK toolkit
- Single-turn conversations (max_turns=1)
- Automatic retry with feedback on failure

## Examples

See `example_usage.py` for complete examples including:
- Building simple tools
- Building complex tools with requirements
- Resuming incomplete builds
- Checking build status

## Migration from Previous Architecture

The AI-first architecture replaces:
- `MetacognitiveAnalyzer` (rule-based) → AI analysis
- `IntegrationAssembler` (templates) → AI generation
- `QualityChecker` (regex) → AI validation
- `SessionManager` → `StateManager` with resumability

## Development

### Running Tests

```bash
# Run new AI-first tests
pytest tests/tools/test_tool_builder_ai.py

# Run all tests
make test
```

### Adding New Stages

1. Create stage module in `stages/`
2. Implement async `analyze/generate/validate` method
3. Use ClaudeSession for AI operations
4. Add to pipeline.py stage mapping
5. Update state.py pipeline order

## Best Practices

1. **Save state frequently**: After every AI operation
2. **Handle failures gracefully**: Allow resume from any point
3. **Use defensive utilities**: parse_llm_json, retry_with_feedback
4. **Keep stages independent**: Each stage self-contained
5. **Document prompts clearly**: Future maintainability

## Troubleshooting

### "Failed to parse AI response"
- AI returned non-JSON format
- System will retry with feedback
- Check logs for raw response

### "State file not found"
- Tool wasn't built before
- Check state directory permissions
- Use --state-dir to specify location

### "All retries exhausted"
- AI service may be down
- Check network connectivity
- Try resume command later

## Philosophy

This architecture embodies the principle: **"Code for structure, AI for intelligence"**

- Code handles orchestration, state, and flow
- AI handles understanding, analysis, and generation
- Clear separation of concerns
- Leverages strengths of both