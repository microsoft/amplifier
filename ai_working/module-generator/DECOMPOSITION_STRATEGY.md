# Module Generation Decomposition Strategy

## Core Insight: Breaking Down the Elephant

Module generation is too complex for a single AI prompt. By decomposing it into specialized, focused tasks, we enable:
- **Parallel execution** of independent steps
- **Focused context** for each subagent (staying within token limits)
- **Incremental progress** with checkpointing
- **Quality gates** between phases

## Decomposition Principles

### 1. Task Size Guidelines

Each subtask should be:
- **Single Responsibility**: One clear goal
- **Context-Bounded**: <10K tokens of input/output
- **Time-Bounded**: Complete within 2 minutes (120-second SDK timeout)
- **Independently Testable**: Has clear success criteria

### 2. Information Flow

```
Spec → [Validation] → Validated Spec
         ↓
       [Architecture] → Blueprint
         ↓
       [Parallel Implementation]
         ├→ [Core Logic] → core.py
         ├→ [Interface] → __init__.py
         ├→ [Models] → models.py
         └→ [Utils] → utils.py
         ↓
       [Test Generation] → tests/
         ↓
       [Documentation] → docs/
         ↓
       [Integration] → Validated Module
```

## Detailed Task Breakdown

### Phase 1: Specification Processing (Sequential)

#### Task 1.1: Contract Validation
**Agent**: `spec-validator`
**Input**: Contract YAML file (typically <1K tokens)
**Output**: Validation report + normalized contract
**Time**: ~10 seconds
**Success Criteria**: Valid YAML, all required fields present, types correct

#### Task 1.2: Spec Validation
**Agent**: `spec-validator`
**Input**: Implementation spec YAML (typically <3K tokens)
**Output**: Validation report + normalized spec
**Time**: ~15 seconds
**Success Criteria**: Valid YAML, references match contract, constraints satisfied

#### Task 1.3: Dependency Analysis
**Agent**: `dependency-analyzer`
**Input**: Normalized spec + contract
**Output**: Dependency graph, import requirements, external interfaces
**Time**: ~20 seconds
**Success Criteria**: All dependencies identified, no circular dependencies

### Phase 2: Architecture Design (Sequential)

#### Task 2.1: Structure Planning
**Agent**: `code-architect`
**Input**: Normalized spec + dependency graph
**Output**: File structure, class hierarchy, function signatures
**Time**: ~30 seconds
**Success Criteria**: All spec requirements mapped to code structure

#### Task 2.2: Interface Design
**Agent**: `interface-designer`
**Input**: Contract + structure plan
**Output**: Public API design, type definitions, error hierarchy
**Time**: ~20 seconds
**Success Criteria**: Interface matches contract exactly

#### Task 2.3: Data Flow Design
**Agent**: `data-flow-designer`
**Input**: Spec behaviors + structure plan
**Output**: Data transformations, state management, caching strategy
**Time**: ~25 seconds
**Success Criteria**: All data paths defined, no undefined transformations

### Phase 3: Implementation (Parallel)

#### Task 3.1: Models Implementation
**Agent**: `model-builder`
**Input**: Data models from architecture, max 2K tokens
**Output**: Pydantic models, serialization logic
**Time**: ~30 seconds
**Success Criteria**: Models validate sample data, serialization works

#### Task 3.2: Core Logic Implementation
**Agent**: `logic-builder`
**Input**: Function signatures + behaviors, chunked to 3K tokens
**Output**: Implementation of core algorithms
**Time**: ~60 seconds per chunk
**Success Criteria**: Logic handles happy path and specified error cases

#### Task 3.3: Interface Implementation
**Agent**: `interface-builder`
**Input**: Public API design + core logic references
**Output**: __init__.py with exports, facade patterns
**Time**: ~20 seconds
**Success Criteria**: All contract methods exposed, typing correct

#### Task 3.4: Utilities Implementation
**Agent**: `utils-builder`
**Input**: Helper function specs
**Output**: Utility functions, validators, formatters
**Time**: ~30 seconds
**Success Criteria**: All utilities pure functions, well-tested

### Phase 4: Testing (Parallel)

#### Task 4.1: Unit Test Generation
**Agent**: `unit-test-generator`
**Input**: Implementation code + behaviors
**Output**: Pytest unit tests
**Time**: ~40 seconds per module file
**Success Criteria**: >80% code coverage, all behaviors tested

#### Task 4.2: Integration Test Generation
**Agent**: `integration-test-generator`
**Input**: Contract + interface implementation
**Output**: End-to-end tests
**Time**: ~30 seconds
**Success Criteria**: All contract scenarios tested

#### Task 4.3: Test Fixtures Creation
**Agent**: `fixture-generator`
**Input**: Models + test scenarios
**Output**: Test data, mocks, fixtures
**Time**: ~20 seconds
**Success Criteria**: Fixtures cover all test cases

### Phase 5: Documentation (Parallel)

#### Task 5.1: API Documentation
**Agent**: `api-doc-generator`
**Input**: Interface code + contract
**Output**: API reference documentation
**Time**: ~20 seconds
**Success Criteria**: All public methods documented

#### Task 5.2: Usage Examples
**Agent**: `example-generator`
**Input**: Interface + test cases
**Output**: README with examples
**Time**: ~25 seconds
**Success Criteria**: Common use cases demonstrated

#### Task 5.3: Inline Documentation
**Agent**: `docstring-generator`
**Input**: Implementation code
**Output**: Docstrings and comments
**Time**: ~15 seconds per file
**Success Criteria**: All functions have docstrings

### Phase 6: Validation (Sequential)

#### Task 6.1: Static Analysis
**Agent**: `static-analyzer`
**Input**: Complete module code
**Output**: Linting report, type check results
**Time**: ~15 seconds
**Success Criteria**: No errors, warnings addressed

#### Task 6.2: Test Execution
**Agent**: `test-runner`
**Input**: Module + tests
**Output**: Test results, coverage report
**Time**: ~30 seconds
**Success Criteria**: All tests pass, coverage >80%

#### Task 6.3: Integration Validation
**Agent**: `integration-validator`
**Input**: Module + system interfaces
**Output**: Integration report
**Time**: ~40 seconds
**Success Criteria**: Module integrates without errors

## Chunking Strategies

### 1. Code Chunking for Large Modules

When implementation exceeds token limits:

```python
def chunk_implementation(spec: Dict, max_tokens: int = 3000) -> List[Dict]:
    """Break large implementations into chunks"""
    chunks = []

    # Group by logical units
    for behavior_group in spec["behaviors"]:
        estimated_tokens = estimate_tokens(behavior_group)

        if estimated_tokens < max_tokens:
            chunks.append(behavior_group)
        else:
            # Further split large groups
            for behavior in behavior_group["items"]:
                chunks.append({"items": [behavior]})

    return chunks
```

### 2. Parallel Chunk Processing

```python
async def process_chunks_parallel(chunks: List[Dict]) -> List[str]:
    """Process multiple chunks in parallel"""
    tasks = []

    for i, chunk in enumerate(chunks):
        task = generate_chunk_implementation(
            chunk,
            chunk_id=i,
            context=get_shared_context()
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return merge_implementations(results)
```

## Subagent Specification Templates

### Standard Subagent Structure

```markdown
# [Agent Name] Subagent

## Purpose
Single, clear responsibility

## Input Contract
- **Required**: Specific inputs needed
- **Optional**: Additional context
- **Constraints**: Token limits, format requirements

## Output Contract
- **Success Output**: Expected format and content
- **Error Output**: Failure indicators
- **Metrics**: Performance data to return

## Processing Rules
1. Specific step-by-step approach
2. Error handling requirements
3. Quality criteria

## Examples
[Concrete input/output examples]
```

### Example: Model Builder Subagent

```markdown
# model-builder Subagent

## Purpose
Generate Pydantic models from data specifications

## Input Contract
- **models_spec**: YAML defining data models (max 2K tokens)
- **validation_rules**: Business validation requirements
- **serialization_needs**: JSON, YAML, or other formats

## Output Contract
- **models.py**: Complete Pydantic model definitions
- **validators.py**: Custom validators if needed
- **metrics**: {lines_of_code, models_created, validators_created}

## Processing Rules
1. Create base models first
2. Add validators as methods
3. Include serialization helpers
4. Generate from_dict/to_dict methods
5. Add comprehensive type hints

## Quality Criteria
- All fields have types
- Validators handle edge cases
- Models are immutable where specified
- Serialization round-trips correctly
```

## Orchestration Patterns

### 1. Pipeline Pattern
Sequential tasks where output feeds next input:
```
Validate → Architect → Implement → Test → Deploy
```

### 2. Fan-Out Pattern
Parallel independent tasks:
```
           ├→ Generate Models
Blueprint →├→ Generate Logic
           ├→ Generate Tests
           └→ Generate Docs
```

### 3. Map-Reduce Pattern
Process chunks then merge:
```
        ├→ Chunk 1 → Implementation 1 ↘
Spec →  ├→ Chunk 2 → Implementation 2 → Merge → Module
        └→ Chunk 3 → Implementation 3 ↗
```

### 4. Retry Pattern
Handle failures gracefully:
```python
async def generate_with_retry(agent: str, input: Dict, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            result = await run_subagent(agent, input)
            if result.status == "success":
                return result
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Progress Tracking

### Visual Progress Indicator

```python
class GenerationProgress:
    def __init__(self, total_tasks: int):
        self.total = total_tasks
        self.completed = 0
        self.current_phase = ""
        self.task_status = {}

    def update(self, task_id: str, status: str):
        self.task_status[task_id] = status
        if status == "completed":
            self.completed += 1

        # Print progress bar
        percent = (self.completed / self.total) * 100
        bar_length = 40
        filled = int(bar_length * self.completed // self.total)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(f"\rProgress: [{bar}] {percent:.1f}% - {self.current_phase}", end="")
```

### Checkpoint Management

```python
class CheckpointManager:
    def __init__(self, module_name: str):
        self.checkpoint_dir = Path(f".checkpoints/{module_name}")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_task_result(self, task_id: str, result: Dict):
        """Save individual task result"""
        file = self.checkpoint_dir / f"{task_id}.json"
        with open(file, 'w') as f:
            json.dump(result, f, indent=2)

    def load_completed_tasks(self) -> Dict[str, Dict]:
        """Load all completed task results"""
        results = {}
        for file in self.checkpoint_dir.glob("*.json"):
            task_id = file.stem
            with open(file) as f:
                results[task_id] = json.load(f)
        return results

    def can_skip_task(self, task_id: str) -> bool:
        """Check if task was already completed"""
        return (self.checkpoint_dir / f"{task_id}.json").exists()
```

## Error Recovery Strategies

### 1. Graceful Degradation
If optional components fail, continue with core functionality:
- Skip docstring generation if it fails
- Use simple types if complex typing fails
- Generate basic tests if comprehensive testing fails

### 2. Fallback Implementations
Have simpler alternatives ready:
- If parallel fails, run sequentially
- If custom agent fails, use generic implementation
- If optimization fails, use working baseline

### 3. Human-in-the-Loop
For critical failures, prompt for human intervention:
- Architecture decisions that affect entire module
- Contract violations that can't be resolved
- Dependency conflicts requiring design changes

## Success Metrics

### Per-Task Metrics
- **Completion Rate**: % of tasks that succeed
- **Retry Rate**: % of tasks requiring retry
- **Time Distribution**: Histogram of task durations
- **Token Usage**: Actual vs estimated tokens

### Per-Module Metrics
- **Total Generation Time**: Wall clock time
- **Code Quality Score**: Linting, complexity, coverage
- **Integration Success**: Works with system?
- **Human Edits Required**: Changes after generation

### System-Wide Metrics
- **Module Success Rate**: % generated without errors
- **Average Generation Time**: Across all modules
- **Parallel Efficiency**: Speedup from parallelization
- **Cost per Module**: API tokens and compute time