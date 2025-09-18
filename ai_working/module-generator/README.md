# Module Generator CLI Tool

## Current Status (January 2025) - Working Implementation

**✅ WORKING**: This module generator successfully transforms YAML specifications into complete, working Python modules with full implementations using Claude Code SDK.

### What's Implemented

- ✅ **Complete Module Generation** - Generates 20KB+ of working Python code
- ✅ **Multi-Turn Conversation Support** - Handles Claude SDK clarifications
- ✅ **Progress Tracking** - Real-time spinner with elapsed time
- ✅ **Response Parsing** - Intelligently separates code from commentary
- ✅ **State Management** - Checkpoint/resume capabilities
- ✅ **No Stub Syndrome** - Generates actual implementations, not NotImplementedError

### Quick Start

```bash
# Generate a module from specifications
python -m module_generator generate examples/idea-synthesizer.yaml

# With custom timeout (30-600 seconds)
python -m module_generator generate examples/idea-synthesizer.yaml --timeout 300

# Interactive clarification mode
python -m module_generator generate examples/idea-synthesizer.yaml --clarification-mode interactive
```

## Overview

A revolutionary CLI tool that transforms module specifications (YAML contracts and implementation specs) into complete, working Python modules using Claude Code SDK. This tool embodies the "bricks and studs" philosophy where software modules are regenerated from specifications rather than edited line-by-line.

## Philosophy

### Bricks and Studs

Like construction toys, software should be built from:
- **Bricks**: Self-contained modules with clear responsibilities
- **Studs**: Stable connection points (public APIs) between modules

### Regeneration Over Editing

- Don't patch code - regenerate it from specifications
- Specifications are the source of truth
- Every regeneration produces fresh, consistent code

### Human as Architect, AI as Builder

- **Humans**: Design specifications, validate behavior
- **AI**: Generate implementations, handle mechanical details

## Current Architecture

```
module-generator/
├── src/module_generator/
│   ├── core/                    # Core functionality
│   │   ├── claude_sdk.py        # Claude SDK with progress tracking
│   │   ├── conversation.py      # Multi-turn conversation management
│   │   ├── response_parser.py   # Intelligent response parsing
│   │   └── state.py             # Checkpoint/resume capabilities
│   │
│   ├── generators/              # Code generation components
│   │   ├── interface.py         # Public API generator
│   │   ├── implementation.py    # Full implementation generator
│   │   └── documentation.py     # Documentation generator
│   │
│   ├── models/                  # Data models
│   │   ├── contract.py          # Contract specification models
│   │   └── module.py            # Module structure models
│   │
│   ├── validators/              # Validation components
│   │   └── contract.py          # Contract validation
│   │
│   └── orchestrator.py          # Main orchestration logic
│
├── generated/                   # Generated module output
│   ├── __init__.py             # Public API (500+ lines)
│   ├── implementation.py        # Core implementation (500+ lines)
│   ├── claude_integration.py   # Claude SDK integration (400+ lines)
│   └── state.py                # State management (400+ lines)
│
└── examples/                   # Example specifications
    └── idea-synthesizer.yaml  # Complete example contract/spec
```

## Key Features

### 1. Multi-Turn Conversation Support

The system handles complex dialogues with Claude SDK:

```python
@dataclass
class ConversationState:
    conversation_id: str
    turns: list[Turn]
    context: dict[str, Any]
    status: Literal["active", "awaiting_input", "completed", "failed"]
```

Features:
- Tracks conversation history
- Handles clarification requests
- Three modes: auto, interactive, hybrid
- Persists conversation state for resume

### 2. Intelligent Response Parsing

Separates code from commentary in Claude responses:

```python
ParsedResponse(
    response_type="mixed",  # code/question/mixed/progress/error
    code_blocks=[CodeBlock(language="python", content="...")],
    questions=["Should I use standard library or external dependency?"],
    commentary=["I've implemented a robust solution..."]
)
```

### 3. Real-Time Progress Tracking

Shows what's happening during long operations:

```
🤖 Querying Claude SDK (timeout: 300s, Ctrl+C to abort)...
   ⠸ Elapsed: 0:02:45 | Response: 8,432 chars
```

Features:
- Animated spinner (⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏)
- Elapsed time tracking
- Response size indicator
- Configurable timeout (30-600 seconds)

### 4. State Management & Checkpointing

Every operation is saved for resume capability:

```json
{
  "module_id": "summarizer_20250118_143022",
  "status": "in_progress",
  "completed_phases": ["contract_parsing", "interface_generation"],
  "pending_phases": ["implementation", "integration"],
  "conversations": {
    "implementation": {
      "conversation_id": "conv_abc123",
      "status": "awaiting_input"
    }
  }
}
```

## YAML Specification Format

### Contract (External Interface)

```yaml
contract:
  name: text-summarizer
  version: 1.0.0
  description: Generate concise summaries of markdown documents

  public_interface:
    functions:
      - name: summarize
        async: true
        parameters:
          - name: file_path
            type: Path
            description: Path to markdown file
        returns:
          type: Summary
          description: Generated summary

    classes:
      - name: Summary
        attributes:
          - name: text
            type: str
            description: 100-500 token summary
          - name: key_concepts
            type: list[str]
```

### Implementation Spec (Internal Requirements)

```yaml
implementation:
  architecture:
    style: modular
    patterns: ["dependency injection", "strategy pattern"]

  requirements:
    - Process markdown files up to 100KB
    - Extract key concepts using NLP
    - Generate summaries with Claude SDK
    - Cache results for performance
```

## Generated Module Example

The system successfully generated a complete summarizer module:

- **4 files generated** with 20KB+ of code
- **Full implementations** - no stubs or NotImplementedError
- **Working integration** with Claude SDK
- **Complete error handling** and state management

### Generated Files

1. **`__init__.py`** (190 lines)
   - Public API functions
   - Data models (Summary, SummaryOptions)
   - Custom exception hierarchy

2. **`implementation.py`** (500+ lines)
   - Core summarizer logic
   - Markdown parsing
   - Claude SDK integration
   - Checkpoint/resume support

3. **`claude_integration.py`** (420+ lines)
   - Claude SDK wrapper
   - Retry logic with exponential backoff
   - Response processing
   - Batch operations

4. **`state.py`** (430+ lines)
   - Checkpoint management
   - Operation tracking
   - File I/O with retry logic
   - Thread-safe locking

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/amplifier-generator
cd amplifier-generator/ai_working/module-generator

# Install dependencies
pip install -e .

# Or using uv
uv pip install -e .
```

### Requirements

- Python 3.11+
- Claude CLI (`npm install -g @anthropic-ai/claude-code`)
- Claude Code SDK (`claude-code-sdk>=0.0.20`)

## Usage

### Basic Generation

```bash
# Generate from specification
python -m module_generator generate examples/idea-synthesizer.yaml

# Output structure:
generated/
├── __init__.py           # Public API
├── implementation.py     # Core logic
├── claude_integration.py # AI integration
└── state.py             # State management
```

### Advanced Options

```bash
# Custom timeout (default: 300 seconds)
python -m module_generator generate spec.yaml --timeout 600

# Interactive clarification mode
python -m module_generator generate spec.yaml --clarification-mode interactive

# Resume from checkpoint
python -m module_generator resume checkpoint_20250118_143022.json

# Parallel variant generation (planned)
python -m module_generator variants spec.yaml --count 3
```

## Development Status

### ✅ Completed

- [x] Contract parsing and validation
- [x] Interface generation from contracts
- [x] Implementation generation with Claude SDK
- [x] Multi-turn conversation support
- [x] Response parsing (code/commentary separation)
- [x] Progress tracking with spinner
- [x] State management and checkpointing
- [x] Retry logic with exponential backoff
- [x] Comprehensive error handling

### 🚧 In Progress

- [ ] Test suite generation
- [ ] Documentation generation
- [ ] Integration validation

### 📋 Planned

- [ ] Parallel variant generation
- [ ] Module dependency resolution
- [ ] Incremental regeneration
- [ ] Performance benchmarking
- [ ] A/B testing framework

## Critical Implementation Notes

Based on discoveries during development:

1. **Claude SDK Timeout**: Always use 120-300 second timeout
2. **Response Parsing**: Strip markdown formatting from JSON
3. **File I/O**: Implement retry logic for cloud-synced directories
4. **Progress Visibility**: Essential for long operations
5. **No Fallbacks**: Fail clearly rather than degrade silently

## Testing

```bash
# Run all tests
pytest tests/

# Test specific component
pytest tests/test_conversation.py

# End-to-end test with real generation
python test_final.py

# Validate generated module
python test_generated_module.py
```

## Known Limitations

1. **Requires Claude CLI**: Must have `@anthropic-ai/claude-code` installed globally
2. **Context Window**: Specifications must fit within ~15K tokens
3. **Generation Time**: Complex modules take 2-5 minutes
4. **No Incremental Updates**: Currently regenerates entire module

## Future Vision

### Near Term
- Generate test suites from specifications
- Support multiple programming languages
- Add specification templates library

### Long Term
- Self-improving generation based on feedback
- Distributed generation farms
- Visual specification builder
- Continuous regeneration in CI/CD

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## License

MIT - See LICENSE file for details.

## Acknowledgments

Built on the revolutionary "bricks and studs" philosophy, inspired by construction toys and the principle that software should be regenerated from specifications rather than patched line-by-line.

---

*For comprehensive technical details, see [MODULE_GENERATOR_REPORT.md](MODULE_GENERATOR_REPORT.md)*