# Claude Healer - Direct Claude Code SDK Implementation

A drop-in replacement for Aider that uses Claude Code SDK directly for code healing.

## Features

- **Direct Claude API usage** - No external tool dependencies
- **Simple and focused** - Ruthlessly simple implementation
- **Drop-in replacement** - Works seamlessly with existing auto_healer.py
- **Robust code extraction** - Handles various response formats from Claude

## Implementation

The module provides:
- `heal_with_claude()` - Async function for healing with full control
- `run_claude_healing()` - Sync wrapper matching the original Aider interface
- `extract_code()` - Robust extraction of code from Claude responses

## Usage

The healer is already integrated into `auto_healer.py`. When you run auto-healing:

```python
from amplifier.tools.auto_healer import AutoHealer

healer = AutoHealer()
result = healer.heal_module_safely(Path("module.py"))
```

It will automatically use Claude Code SDK instead of Aider.

## Configuration

The healing session uses these default settings:
- System prompt focused on code improvement
- Single-turn interactions for focused improvements
- Retry attempts for transient failures
- No streaming for batch processing

## Benefits over Aider

1. **No external dependencies** - Uses our existing Claude Code SDK
2. **Faster** - Direct API calls without subprocess overhead
3. **More control** - Full control over prompts and responses
4. **Better integration** - Native Python async support
5. **Simpler** - Less than 150 lines of focused code

## Testing

Run the test script to verify functionality:

```bash
python test_claude_healer.py
```

This will test the healer with a complex code example and show the improvement.