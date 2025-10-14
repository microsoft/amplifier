# Debugging Tricks

## Print Debugging

### Strategic Print Statements
Don't just print variable values. Print context too:
```python
print(f"[CHECKPOINT] Function: process_data, Line 42, user_id={user_id}, status={status}")
```
This makes it easy to trace execution flow and identify where things go wrong.

### Binary Search Debugging
When debugging a long function, add a print statement in the middle. If the bug occurs before the print, focus on the first half. Otherwise, focus on the second half. Repeat until you isolate the issue.

## Using Debuggers

### Conditional Breakpoints
Instead of breaking on every iteration of a loop, set conditional breakpoints:
```python
# Break only when i == problematic_value
if i == 42:
    import pdb; pdb.set_trace()
```

### Remote Debugging
For production issues, use remote debugging tools. Python's `debugpy` allows you to attach a debugger to a running process:
```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()  # Blocks until debugger connects
```

## Logging Strategies

### Structured Logging
Use structured logging with consistent fields:
```python
logger.info("Processing request", extra={
    "user_id": user_id,
    "action": "create_order",
    "duration_ms": elapsed_time
})
```
This makes logs searchable and parseable.

### Debug Levels
Use appropriate log levels:
- DEBUG: Detailed diagnostic info
- INFO: General informational messages
- WARNING: Something unexpected but handled
- ERROR: Error that needs attention
- CRITICAL: System might fail

## Problem Isolation

### Rubber Duck Debugging
Explain your code line-by-line to a rubber duck (or colleague). Often, the act of explaining reveals the problem.

### Minimal Reproduction
Create the smallest possible code that reproduces the bug. This eliminates unrelated complexity and often reveals the root cause.

### Git Bisect
Use `git bisect` to find the commit that introduced a bug:
```bash
git bisect start
git bisect bad  # Current version is bad
git bisect good abc123  # This old commit was good
# Git will checkout commits for you to test
```

## Performance Debugging

### Profiling First
Before optimizing, profile to find actual bottlenecks:
```python
import cProfile
cProfile.run('your_function()', sort='cumulative')
```

### Memory Leaks
Use memory profilers to find leaks:
```python
from memory_profiler import profile

@profile
def potentially_leaky_function():
    # Your code here
```