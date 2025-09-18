# Multi-Turn Conversation System

## Overview

The multi-turn conversation system enables sophisticated dialogue-based module generation with support for clarification requests, checkpointing, and conversation resumption.

## Core Components

### 1. ConversationManager (`conversation.py`)
Manages conversation state and checkpointing.

**Key Features:**
- Track message history
- Save/load conversation checkpoints
- Maintain conversation context
- Support conversation resumption

**Usage:**
```python
from module_generator.core import ConversationManager

manager = ConversationManager(checkpoint_dir=Path(".checkpoints"))
state = manager.start_conversation(
    module_spec=spec,
    working_directory=Path.cwd(),
    target_directory=Path("generated")
)
manager.add_message("user", "Generate a module...")
checkpoint = manager.save_checkpoint()
```

### 2. ResponseParser (`response_parser.py`)
Parses and classifies Claude SDK responses.

**Response Types:**
- `code`: Contains code blocks to generate
- `question`: Requires clarification
- `mixed`: Has both code and questions
- `progress`: Status update
- `error`: Error response

**Usage:**
```python
from module_generator.core import ResponseParser

parser = ResponseParser()
parsed = parser.parse(response_text)
if parsed.requires_clarification:
    # Handle questions
    for question in parsed.questions:
        print(f"Question: {question.question}")
```

### 3. ClarificationHandlers (`clarification.py`)
Different strategies for handling clarification requests.

**Available Handlers:**
- `AutoClarificationHandler`: Uses nested Claude SDK calls
- `InteractiveClarificationHandler`: Prompts user for input
- `HybridClarificationHandler`: Auto with fallback to interactive

**Usage:**
```python
from module_generator.core import AutoClarificationHandler

handler = AutoClarificationHandler(claude_sdk)
answer = await handler.get_clarification(question, context)
```

### 4. DialogueController (`dialogue.py`)
Orchestrates the multi-turn conversation flow.

**Key Features:**
- Manages conversation turns
- Handles different response types
- Saves generated code files
- Supports conversation resumption

**Usage:**
```python
from module_generator.core import DialogueController

controller = DialogueController(
    conversation_manager=manager,
    response_parser=parser,
    clarification_handler=clarifier,
    max_turns=10
)

result = await controller.run_dialogue(
    claude_sdk=sdk,
    initial_prompt=prompt,
    module_spec=spec,
    working_directory=Path.cwd(),
    target_directory=Path("generated")
)
```

### 5. MultiTurnClaudeSDK (`claude_sdk_multi.py`)
Wrapper for Claude SDK with multi-turn support.

**Key Features:**
- Conversation history management
- Message streaming support
- Checkpoint/resume capability
- Simplified interface for backward compatibility

**Usage:**
```python
from module_generator.core import MultiTurnClaudeSDK, MultiTurnOptions

options = MultiTurnOptions(
    system_prompt="Generate Python modules",
    max_turns=10,
    checkpoint_dir=Path(".checkpoints")
)

async with MultiTurnClaudeSDK(options) as sdk:
    response = await sdk.query("Generate a data processor module")
    # Continue conversation
    clarification = await sdk.send_message("Use async processing")
```

## Complete Example

```python
import asyncio
from pathlib import Path
from module_generator.core import (
    ConversationManager,
    ResponseParser,
    AutoClarificationHandler,
    DialogueController,
    MultiTurnClaudeSDK,
    MultiTurnOptions
)

async def generate_module():
    # Setup components
    manager = ConversationManager()
    parser = ResponseParser()
    clarifier = AutoClarificationHandler()

    controller = DialogueController(
        conversation_manager=manager,
        response_parser=parser,
        clarification_handler=clarifier
    )

    # Create SDK
    sdk_options = MultiTurnOptions(
        system_prompt="You are a Python module generator",
        max_turns=10
    )

    async with MultiTurnClaudeSDK(sdk_options) as sdk:
        result = await controller.run_dialogue(
            claude_sdk=sdk,
            initial_prompt="Generate a web scraper module",
            module_spec={"name": "web_scraper"},
            working_directory=Path.cwd(),
            target_directory=Path("generated")
        )

        if result.success:
            print(f"Generated {len(result.generated_files)} files")
        else:
            print(f"Failed: {result.error}")

# Run generation
asyncio.run(generate_module())
```

## Checkpointing and Resumption

The system supports saving and resuming conversations:

```python
# Save checkpoint during conversation
checkpoint = manager.save_checkpoint("my_checkpoint")

# Later, resume from checkpoint
controller = DialogueController(...)
result = await controller.resume_dialogue(
    claude_sdk=sdk,
    checkpoint_path=checkpoint
)
```

## Clarification Strategies

### Auto-Clarification
Best for autonomous generation with reasonable defaults:

```python
handler = AutoClarificationHandler(nested_sdk)
# Automatically answers questions using Claude
```

### Interactive Clarification
Best for user-guided generation:

```python
handler = InteractiveClarificationHandler()
# Prompts user for each question
```

### Hybrid Clarification
Best for balance between automation and control:

```python
handler = HybridClarificationHandler(
    auto_handler=auto,
    interactive_handler=interactive,
    confidence_threshold=0.7
)
# Tries auto first, falls back to interactive for critical decisions
```

## Architecture Benefits

1. **Modular Design**: Each component has a single responsibility
2. **Extensibility**: Easy to add new clarification strategies or parsers
3. **Resilience**: Checkpoint/resume prevents loss of progress
4. **Flexibility**: Supports both autonomous and interactive modes
5. **Testability**: Each component can be tested independently

## Integration with Module Generator

The multi-turn system integrates seamlessly with the existing module generator:

```python
from module_generator.orchestrator import ModuleOrchestrator

# Orchestrator can use multi-turn dialogue for complex generations
orchestrator = ModuleOrchestrator(
    use_multi_turn=True,
    clarification_mode="auto"  # or "interactive", "hybrid"
)

result = await orchestrator.generate_module(spec)
```

## Testing

Run tests with:
```bash
python test_multi_turn.py
```

Run examples with:
```bash
python example_multi_turn.py
```