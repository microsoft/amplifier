# Claude SDK Progress Visibility

## Overview

The Claude SDK operations now include comprehensive real-time progress visibility, allowing users to monitor the status of long-running generation tasks and detect if they're hung.

## Features

### 1. Real-Time Progress Indicators

When `show_progress=True` (the default), users see:

- **Animated spinner** (⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏) - Shows the system is active
- **Elapsed time counter** - Format: `[MM:SS]` - Shows how long the operation has been running
- **Response size tracking** - Shows characters received and number of chunks
- **Activity monitoring** - Tracks time since last response

Example output:
```
🤖 Querying Claude SDK (timeout: 300s, Ctrl+C to abort)...
⠹ Waiting for Claude SDK... [00:42] | 2847 chars received | 15 chunks
```

### 2. Inactivity Warnings

If no response is received for:
- **30+ seconds**: Warning appears with yellow warning sign (⚠️)
- **60+ seconds**: Additional "(Ctrl+C to abort)" reminder

Example:
```
⠸ Waiting for Claude SDK... [01:35] | 0 chars received | 0 chunks | ⚠️ No response for 35s (Ctrl+C to abort)
```

### 3. Graceful Interruption

Users can press **Ctrl+C** at any time to cleanly abort the operation:
- Progress indicator is cleared
- Clear cancellation message is shown
- `KeyboardInterrupt` is raised for proper handling

### 4. Completion Summary

When the operation completes successfully:
```
✅ Received 5234 chars in 01:23 (42 chunks)
```

## Usage

### Basic Usage (Progress Enabled by Default)

```python
from module_generator.core.claude_sdk import query_claude

# Async usage
response = await query_claude(
    prompt="Generate a Python function",
    timeout=300  # 5 minutes
)

# Sync usage
from module_generator.core.claude_sdk import query_claude_sync

response = query_claude_sync(
    prompt="Generate a Python function",
    timeout=300
)
```

### Disable Progress (for CI/CD or logging)

```python
response = await query_claude(
    prompt="Generate code",
    show_progress=False  # Disable progress indicators
)
```

### In Generators

The `BaseGenerator` class automatically uses progress indicators:

```python
class MyGenerator(BaseGenerator):
    async def generate(self, context):
        # Progress is shown by default
        code = await self.query_claude(
            prompt="Generate module",
            timeout=300
        )
```

## Timeout Guidelines

- **Default**: 300 seconds (5 minutes)
- **Minimum**: 30 seconds
- **Maximum**: 600 seconds (10 minutes)

Recommended timeouts by task complexity:
- Simple functions: 60-120 seconds
- Complete modules: 180-300 seconds
- Large applications: 300-600 seconds

## Benefits

1. **User Confidence**: Users can see the system is working, not hung
2. **Early Detection**: Quickly identify when SDK is unavailable
3. **Clean Cancellation**: Ctrl+C works properly without corrupting state
4. **Progress Tracking**: See how much content has been generated
5. **Timeout Awareness**: Know when operations are taking unusually long

## Testing

Run the test script to see progress visibility in action:

```bash
cd ai_working/module-generator
python test_progress.py
```

This demonstrates:
- Real-time progress updates
- Response accumulation
- Ctrl+C handling
- Timeout behavior

## Implementation Details

The progress system uses:
- **Async tasks** for non-blocking progress updates
- **ANSI escape codes** for line clearing (`\r` carriage return)
- **contextlib.suppress** for clean task cancellation
- **Time tracking** for elapsed and inactive periods
- **Unicode spinners** for smooth animation

All progress output goes to stdout with `flush=True` for immediate display.