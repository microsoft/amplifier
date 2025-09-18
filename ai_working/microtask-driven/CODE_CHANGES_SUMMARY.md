# Code Changes Summary: What to Keep, Fix, and Discard

## Files Created (Keep These)

### Core Infrastructure ✅

#### `amplifier_microtask/progress_monitor.py`
```python
# KEEP - Excellent file-based progress monitoring
class ProgressMonitor:
    """File-based heartbeat monitoring for SDK operations"""
    def __init__(self, task_id: str, stage_name: str)
    async def update(self, message: str)
    async def monitor_heartbeat(self, check_interval: int = 30)
```
**Why keep**: Non-invasive monitoring pattern that works with any async operation

#### `amplifier_microtask/validation.py`
```python
# KEEP - Good structure, needs integration
class RequirementsValidator:
    def extract_requirements(self, desc: str) -> Dict[str, List[str]]
    def validate_stage(self, stage_name: str, output: Any) -> ValidationResult
```
**Why keep**: Solid validation framework, just needs proper integration points

#### `amplifier_microtask/context.py`
```python
# KEEP - Philosophy injection system
PHILOSOPHY_CONTEXT = """..."""
def inject_context(prompt: str) -> str
```
**Why keep**: Successfully reduces bad patterns in generated code

## Files Modified (Selective Changes)

### `amplifier_microtask/stages.py`
```python
# KEEP this function:
def calculate_task_timeout(base_timeout: int, task_type: str, context: dict) -> int:
    """Adaptive timeout calculation based on task complexity"""
    if task_type == "integration_test_generation":
        return 600  # 10 minutes
    elif task_type == "design":
        return 300  # 5 minutes
    # ... etc
```
**Why keep**: Proven timeout values from empirical testing

### `amplifier_microtask/orchestrator.py`
```python
# FIX: Line 138
# Change: session.stage → session.current_stage
```
**Required fix**: Attribute name mismatch

### `amplifier_microtask/agent.py`
```python
# KEEP: Progress monitor integration pattern
async def execute_task(self, context: dict):
    monitor = ProgressMonitor(context.get("task_id"), context.get("stage"))
    # ... integration code
```
**Why keep**: Clean integration pattern for monitoring

## Files to Fix (Syntax Errors)

### Test Files with Syntax Errors ❌
```
amplifier_workspace/tests/17aeb3b6/test_main.py  # Has unclosed string
amplifier_workspace/tests/a70a8c05/test_main.py  # Has unclosed string
```
**Action**: Either fix the syntax errors or delete these test files

### Generated Tool with Issues ⚠️
```
amplifier_workspace/tools/document_insight_pipeline/cli.py
# Line 135: default=false → default=False (Python boolean)
```
**Action**: Fix Python syntax error (already fixed in working copy)

## Files to Review (Generated Output)

### `amplifier_workspace/tools/document_insight_pipeline/`
This entire directory is the failed tool generation example:
- **cli.py**: Generic processor instead of 4-stage pipeline
- **tests/test_cli.py**: Tests that don't verify actual requirements
- **README.md**: Documentation that doesn't match implementation

**Recommendation**: Keep as example of what NOT to generate, or delete entirely

## Integration Points Needed

### Where to Add Validation Hooks
```python
# In orchestrator.py, after each stage:

result = await stage.process(input)
# ADD: Validation checkpoint here
validator = RequirementsValidator(requirements)
if not validator.validate_stage(stage_name, result):
    raise ValidationError(f"Stage {stage_name} failed validation")
```

### Where to Add Progress Monitoring
```python
# Already integrated in agent.py, but extend to:
- Requirements extraction stage
- Design generation stage
- Code generation stage
- Test generation stage
```

## Patterns to Propagate

### File-Based State Pattern
```python
# Use this pattern everywhere for resilience:
def save_state_immediately(self, state: dict):
    """Save after EVERY operation, not at intervals"""
    with open(self.state_file, 'w') as f:
        json.dump(state, f)
```

### Timeout Handling Pattern
```python
# Use this pattern for all SDK operations:
try:
    async with asyncio.timeout(calculate_task_timeout(...)):
        result = await sdk_operation()
except asyncio.TimeoutError:
    logger.warning(f"Operation timed out after {timeout}s")
    # Provide actionable guidance
```

## Quick Fixes Script

To quickly fix the syntax errors preventing `make check` from passing:

```bash
# Fix Python boolean in generated CLI
sed -i 's/default=false/default=False/g' amplifier_workspace/tools/document_insight_pipeline/cli.py

# Remove problematic test files (or fix their syntax)
rm -f amplifier_workspace/tests/17aeb3b6/test_main.py
rm -f amplifier_workspace/tests/a70a8c05/test_main.py

# Fix session attribute
sed -i 's/session\.stage/session.current_stage/g' amplifier_microtask/orchestrator.py
```

## Commit Strategy

### Recommended Git Commits

1. **Infrastructure improvements** (✅ Safe to merge)
   ```
   git add amplifier_microtask/progress_monitor.py
   git add amplifier_microtask/validation.py
   git add amplifier_microtask/context.py
   git commit -m "Add progress monitoring, validation framework, and context injection"
   ```

2. **Timeout improvements** (✅ Safe to merge)
   ```
   git add amplifier_microtask/stages.py  # Just the timeout function
   git commit -m "Add adaptive timeout calculation for SDK operations"
   ```

3. **Documentation** (✅ Safe to merge)
   ```
   git add ai_working/microtask-driven/
   git commit -m "Document microtask-driven experiment findings and lessons learned"
   ```

4. **Failed example** (⚠️ Optional - for learning)
   ```
   git add amplifier_workspace/tools/document_insight_pipeline/
   git commit -m "Example of failed multi-stage pipeline generation (learning artifact)"
   ```

## Testing Checklist

Before committing, verify:

- [ ] `make check` passes (after fixing syntax errors)
- [ ] Progress monitoring works with a simple test
- [ ] Timeout calculation returns appropriate values
- [ ] Validation framework can extract requirements
- [ ] Context injection adds philosophy to prompts

## Summary

**Definitely Keep**: Progress monitoring, validation framework, context injection, adaptive timeouts, documentation

**Fix and Keep**: Orchestrator session attribute, CLI boolean syntax

**Consider Discarding**: Generated document_insight_pipeline tool (unless kept as learning example)

**Delete**: Broken test files with syntax errors

The infrastructure improvements are solid and should be preserved. The generated tool example shows what not to do and could be kept for reference or discarded. The documentation provides valuable lessons for the next iteration.

---

*This summary helps identify what code changes to preserve from the microtask-driven experiment.*