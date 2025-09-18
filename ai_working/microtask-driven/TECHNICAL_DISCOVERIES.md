# Technical Discoveries from Microtask-Driven Experiment

## SDK Timeout Patterns

### Discovery: Claude SDK Operations Are Long-Running
**Finding**: Claude SDK operations legitimately take 2-5+ minutes for complex tasks
**Previous assumption**: Operations hanging after 30 seconds were failures
**Reality**: SDK needs 120+ seconds baseline, up to 600 seconds for complex operations

### Solution Pattern: File-Based Heartbeat Monitoring
```python
# Instead of trying to intercept SDK operations, monitor via sidecar file
class ProgressMonitor:
    def __init__(self, task_id: str):
        self.progress_file = Path(f".progress_{task_id}.txt")

    async def update(self, message: str):
        # SDK writes progress to file
        with open(self.progress_file, 'a') as f:
            f.write(f"{time.time()}: {message}\n")

    async def monitor_heartbeat(self):
        # Separate coroutine monitors the file
        last_update = os.path.getmtime(self.progress_file)
        if time.time() - last_update > 120:
            logger.warning("No progress for 2 minutes - may be hung")
```

**Why this works**:
- Non-invasive - doesn't modify SDK code
- File I/O doesn't interfere with async operations
- Can monitor from separate process/coroutine
- Survives process crashes (file remains)

## Async Event Loop Conflicts

### Discovery: Nested Event Loops Break SDK
**Issue**: `asyncio.run()` inside async context causes SDK to hang
**Symptom**: "Claude Code SDK timeout - likely running outside Claude Code environment"
**Reality**: SDK was fine, event loops were conflicting

### Anti-Pattern That Causes Hanging:
```python
# DON'T DO THIS
class Extractor:
    def extract(self, text):
        return asyncio.run(self._extract_async(text))  # Creates new loop

# In async context:
await loop.run_in_executor(None, extractor.extract, text)  # Nested loops!
```

### Correct Pattern:
```python
# DO THIS
class Extractor:
    async def extract(self, text):
        return await self._extract_async(text)  # Direct async

# In async context:
await extractor.extract(text)  # Single event loop
```

## Validation Timing Architecture

### Discovery: Validation Must Be Progressive
**Failed approach**: Validate only at the end
**Why it fails**: Errors compound through stages, making root cause unclear

### Progressive Validation Pipeline:
```python
class ValidationPipeline:
    def __init__(self):
        self.checkpoints = []

    def add_checkpoint(self, name: str, validator: Callable):
        self.checkpoints.append((name, validator))

    async def process(self, desc: str):
        artifact = desc
        for checkpoint_name, validator in self.checkpoints:
            artifact = await self.process_stage(artifact)
            if not validator(artifact):
                raise ValidationError(f"Failed at {checkpoint_name}")
        return artifact
```

### Optimal Checkpoint Locations:
1. **After Requirements Extraction**: Verify all requirements captured
2. **After Design Generation**: Verify design meets requirements
3. **After Code Generation**: Verify code implements design
4. **After Test Generation**: Verify tests cover requirements
5. **After Integration Tests**: Verify end-to-end functionality

## Complex Requirements Need Structure

### Discovery: Natural Language Loses Nuance
**Problem**: "Summarize docs, then synthesize, then expand" becomes "process docs"
**Root cause**: Each transformation step loses information

### Information Loss Cascade:
```
Original DESC (100% information)
    ↓ Requirements Extraction
Bullet points (60% information)
    ↓ Design Generation
Generic design (30% information)
    ↓ Code Generation
Wrong implementation (10% information)
```

### Solution: Structured Intermediate Representation
```python
@dataclass
class StageSpecification:
    """Preserves 95%+ of original information"""
    name: str
    input_pattern: str  # e.g., "*.md", "stage1/*.json"
    output_pattern: str  # e.g., "summaries/*.json"

    # Explicit operation type preserves intent
    operation: Literal["summarize", "synthesize", "expand", "transform"]

    # Full prompt template preserves nuance
    ai_prompt: str

    # Dependencies preserve order
    depends_on: List[str]  # Other stage names

    # Validation preserves success criteria
    validators: List[Callable]
```

## File-Based State Management

### Discovery: Memory is Fragile, Files are Robust
**Problem**: In-memory state lost on crashes/timeouts
**Solution**: Immediate file persistence after every operation

### Robust State Pattern:
```python
class ResilientProcessor:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"processed": [], "failed": [], "pending": []}

    def save_state(self):
        # Save immediately, don't wait for batch
        self.state_file.write_text(json.dumps(self.state))

    async def process_item(self, item: str):
        try:
            result = await self.do_work(item)
            self.state["processed"].append(item)
        except Exception as e:
            self.state["failed"].append({"item": item, "error": str(e)})
        finally:
            self.save_state()  # Always save, even on failure
```

## Timeout Calculation Formula

### Discovery: Task Complexity Predicts Duration
**Finding**: Timeout should scale with input size and operation complexity

### Adaptive Timeout Formula:
```python
def calculate_timeout(
    base: int,
    input_size: int,
    complexity: str,
    has_ai: bool
) -> int:
    # Start with base
    timeout = base

    # Scale by input size (logarithmic)
    size_factor = 1 + math.log10(max(1, input_size / 10))
    timeout *= size_factor

    # Scale by complexity
    complexity_factors = {
        "simple": 1.0,      # Read, write, copy
        "moderate": 2.0,    # Parse, transform, validate
        "complex": 3.0,     # Analyze, synthesize
        "ai_heavy": 5.0     # Multi-stage AI processing
    }
    timeout *= complexity_factors.get(complexity, 1.0)

    # AI operations need extra time
    if has_ai:
        timeout = max(timeout, 120)  # Claude SDK minimum
        timeout *= 1.5  # AI overhead

    return int(min(timeout, 600))  # Cap at 10 minutes
```

## AI Response Parsing Patterns

### Discovery: AI Responses Mix Content Types
**Problem**: AI returns preamble + JSON + explanation
**Failed approach**: Reject if response contains preamble
**Better approach**: Extract valid content from mixed response

### Robust AI Response Parser:
```python
def parse_ai_response(response: str) -> dict:
    # Try multiple extraction strategies

    # Strategy 1: Direct JSON parse
    try:
        return json.loads(response)
    except:
        pass

    # Strategy 2: Extract JSON from markdown
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass

    # Strategy 3: Find JSON-like content
    brace_start = response.find('{')
    bracket_start = response.find('[')

    if brace_start >= 0:
        # Try to extract object
        depth = 0
        for i, char in enumerate(response[brace_start:], brace_start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(response[brace_start:i+1])
                    except:
                        pass

    # Strategy 4: Return as text content
    cleaned = response.strip()
    for garbage in ["I'll analyze", "Let me", "Here's"]:
        if cleaned.startswith(garbage):
            lines = cleaned.split('\n')
            cleaned = '\n'.join(lines[1:])  # Skip first line

    if len(cleaned) > 50:  # Substantial content
        return {"content": cleaned}

    raise ValueError(f"Could not parse response: {response[:100]}...")
```

## Stage Boundary Preservation

### Discovery: Stage Transitions Need Explicit Contracts
**Problem**: Stages blur together without clear boundaries
**Solution**: Explicit input/output contracts between stages

### Stage Contract Pattern:
```python
class StageContract:
    def __init__(self,
                 input_schema: Type[BaseModel],
                 output_schema: Type[BaseModel]):
        self.input_schema = input_schema
        self.output_schema = output_schema

    def validate_input(self, data: Any) -> BaseModel:
        return self.input_schema.parse_obj(data)

    def validate_output(self, data: Any) -> BaseModel:
        return self.output_schema.parse_obj(data)

class Pipeline:
    def __init__(self):
        self.stages = []

    def add_stage(self,
                  name: str,
                  processor: Callable,
                  contract: StageContract):
        self.stages.append({
            "name": name,
            "processor": processor,
            "contract": contract
        })

    async def run(self, initial_input: Any):
        data = initial_input
        for stage in self.stages:
            # Validate input matches contract
            validated_input = stage["contract"].validate_input(data)

            # Process with stage
            result = await stage["processor"](validated_input)

            # Validate output matches contract
            data = stage["contract"].validate_output(result)

        return data
```

## Testing Strategy for Generated Tools

### Discovery: Generated Code Needs Different Testing
**Traditional**: Test implementation details
**Generated**: Test behavioral contracts only

### Behavioral Testing Pattern:
```python
class GeneratedToolTest:
    def test_contract_not_implementation(self):
        # Don't test HOW it works
        # Test WHAT it accomplishes

        # Bad: Testing implementation
        assert tool._parse_method == "regex"  # Too specific

        # Good: Testing behavior
        result = tool.process("input.txt")
        assert result["status"] == "success"
        assert "summary" in result
        assert len(result["summary"]) > 0
```

## Performance Characteristics

### Measured Timings from Experiments:

| Operation | Duration | Notes |
|-----------|----------|-------|
| Simple tool generation | 2m 9s | Line counter |
| Complex pipeline generation | 9m 32s | 4-stage document processor |
| Requirements extraction | 30-60s | Depends on DESC length |
| Design generation | 2-3m | Increases with complexity |
| Code generation | 1-2m | Relatively consistent |
| Integration test generation | 3-5m | Most variable |
| Claude SDK per operation | 30s-2m | Depends on prompt complexity |

### Key Performance Insights:
1. **Parallelization helps little** - Most stages depend on previous output
2. **SDK operations dominate time** - File I/O is negligible
3. **Complexity scaling is exponential** - Each stage adds 2-3x time
4. **Caching would help minimally** - Most operations are unique

---

*These technical discoveries represent hard-won insights from the microtask-driven experiment. Each pattern emerged from solving real problems encountered during development.*