# Module Generator CLI Tool

## Overview

A sophisticated CLI tool that transforms module specifications (contracts and implementation specs) into working code using Claude Code SDK subagents. This tool embodies the "bricks and studs" philosophy, generating self-contained modules that snap together via stable interfaces.

## Core Architecture

### 1. Amplifier Pattern Integration

Following the amplifier CLI pattern (code for structure, AI for intelligence):
- **Python CLI** provides reliable iteration and state management
- **Claude Code SDK** handles complex reasoning and code generation
- **Make commands** for simple invocation

### 2. Subagent Decomposition Strategy

Breaking module generation into specialized subagents:

#### a. **spec-validator** Agent
- Validates contract and spec YAML files
- Ensures completeness and consistency
- Checks module size constraints (15K token limit)
- Returns validation report

#### b. **code-architect** Agent
- Analyzes specifications to create implementation plan
- Determines file structure and dependencies
- Creates skeleton with proper imports and interfaces
- Outputs architectural blueprint

#### c. **implementation-builder** Agent
- Generates actual implementation code
- Works from architectural blueprint
- Implements one component at a time
- Handles error cases and edge conditions

#### d. **test-generator** Agent
- Creates comprehensive test suite from spec
- Generates unit tests for each function
- Creates integration tests for module interface
- Includes test fixtures and mocks

#### e. **doc-builder** Agent
- Generates documentation from specs
- Creates API documentation
- Writes usage examples
- Produces inline code comments

#### f. **integration-validator** Agent
- Verifies module integrates with system
- Checks interface compliance
- Validates dependencies are satisfied
- Runs integration tests

### 3. Hook System Integration

Leveraging Claude Code hooks for automation:

```json
{
  "hooks": {
    "PreModuleGeneration": [
      {
        "command": "validate_specs.py",
        "description": "Validate YAML specs before generation"
      }
    ],
    "PostCodeGeneration": [
      {
        "command": "make check",
        "description": "Run linting and type checking"
      }
    ],
    "PostTestGeneration": [
      {
        "command": "make test",
        "description": "Run generated tests"
      }
    ]
  }
}
```

### 4. Custom Slash Commands

Creating commands for interactive development:

- `/generate-module [spec-path]` - Generate complete module
- `/validate-spec [spec-path]` - Validate specifications
- `/regenerate [module-name]` - Regenerate existing module
- `/parallel-generate [spec1] [spec2]` - Generate multiple modules

### 5. State Management & Checkpointing

```python
@dataclass
class GenerationState:
    module_name: str
    phase: str  # "validating", "architecting", "implementing", etc.
    completed_phases: List[str]
    artifacts: Dict[str, Any]  # Generated code, tests, docs
    errors: List[str]
    checkpoint_file: str

    def save(self):
        """Save state for resume capability"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(asdict(self), f)

    @classmethod
    def load_or_create(cls, module_name: str) -> 'GenerationState':
        """Load existing state or create new"""
        checkpoint_file = f".checkpoints/{module_name}.json"
        if Path(checkpoint_file).exists():
            with open(checkpoint_file) as f:
                return cls(**json.load(f))
        return cls(
            module_name=module_name,
            phase="validating",
            completed_phases=[],
            artifacts={},
            errors=[],
            checkpoint_file=checkpoint_file
        )
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
1. Set up project structure with Poetry/uv
2. Create CLI with Click framework
3. Implement state management system
4. Create YAML spec loader and validator
5. Set up Claude Code SDK integration with 120-second timeout

### Phase 2: Subagent Development (Week 2-3)
1. Create spec-validator subagent
2. Develop code-architect subagent
3. Build implementation-builder subagent
4. Implement test-generator subagent
5. Create doc-builder subagent
6. Develop integration-validator subagent

### Phase 3: Orchestration Layer (Week 4)
1. Build orchestrator to coordinate subagents
2. Implement parallel generation support
3. Add progress tracking and reporting
4. Create resume/checkpoint functionality
5. Implement rollback on failure

### Phase 4: Advanced Features (Week 5)
1. Add module dependency resolution
2. Implement incremental regeneration
3. Create variant generation (multiple implementations)
4. Add performance benchmarking
5. Implement A/B testing framework

## CLI Interface Design

### Basic Commands

```bash
# Generate a single module
module-gen generate --spec summarizer_SPEC.yaml --contract summarizer_CONTRACT.yaml

# Validate specifications
module-gen validate --spec summarizer_SPEC.yaml

# Generate with specific subagents only
module-gen generate --spec summarizer_SPEC.yaml --agents "architect,implementation"

# Resume interrupted generation
module-gen resume --checkpoint .checkpoints/summarizer.json

# Generate multiple variants in parallel
module-gen variants --spec summarizer_SPEC.yaml --count 3

# Regenerate module from updated spec
module-gen regenerate --module summarizer --spec summarizer_SPEC.yaml
```

### Configuration File

```yaml
# module-gen.config.yaml
claude:
  sdk_timeout: 120  # seconds
  max_turns: 10
  output_format: "stream-json"

subagents:
  spec_validator:
    enabled: true
    timeout: 30
  code_architect:
    enabled: true
    timeout: 60
  implementation_builder:
    enabled: true
    timeout: 120
    chunk_size: 500  # lines per chunk
  test_generator:
    enabled: true
    coverage_target: 80
  doc_builder:
    enabled: true
    format: "markdown"
  integration_validator:
    enabled: true

generation:
  parallel_modules: 3
  checkpoint_interval: "after_each_phase"
  rollback_on_failure: true

output:
  base_directory: "./generated"
  preserve_artifacts: true
  create_git_commits: true
```

## Subagent Communication Protocol

### Message Format

```python
@dataclass
class SubagentMessage:
    agent_name: str
    phase: str
    input_spec: Dict[str, Any]
    context: Dict[str, Any]  # Previous agent outputs
    constraints: Dict[str, Any]  # Token limits, timeouts

@dataclass
class SubagentResponse:
    agent_name: str
    phase: str
    status: str  # "success", "failure", "partial"
    output: Dict[str, Any]
    errors: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]  # tokens used, time taken
```

### Orchestration Flow

```python
class ModuleOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.subagents = self._initialize_subagents()
        self.state = None

    async def generate_module(self, spec_path: str, contract_path: str):
        """Orchestrate complete module generation"""
        self.state = GenerationState.load_or_create(module_name)

        try:
            # Phase 1: Validation
            if "validation" not in self.state.completed_phases:
                validation_result = await self._run_subagent(
                    "spec_validator",
                    {"spec": spec_path, "contract": contract_path}
                )
                self.state.artifacts["validation"] = validation_result
                self.state.completed_phases.append("validation")
                self.state.save()

            # Phase 2: Architecture
            if "architecture" not in self.state.completed_phases:
                arch_result = await self._run_subagent(
                    "code_architect",
                    {"spec": self.state.artifacts["validation"]["processed_spec"]}
                )
                self.state.artifacts["architecture"] = arch_result
                self.state.completed_phases.append("architecture")
                self.state.save()

            # Phase 3: Implementation (can be parallelized)
            if "implementation" not in self.state.completed_phases:
                impl_tasks = []
                for component in self.state.artifacts["architecture"]["components"]:
                    impl_tasks.append(
                        self._run_subagent("implementation_builder", component)
                    )
                impl_results = await asyncio.gather(*impl_tasks)
                self.state.artifacts["implementation"] = impl_results
                self.state.completed_phases.append("implementation")
                self.state.save()

            # Continue with test generation, documentation, validation...

        except Exception as e:
            self.state.errors.append(str(e))
            self.state.save()
            if self.config.rollback_on_failure:
                await self._rollback()
            raise
```

## Memory System Integration

### Module Memory Store

```python
class ModuleMemory:
    """Track module generation history and patterns"""

    def __init__(self, memory_dir: Path = Path(".module-memory")):
        self.memory_dir = memory_dir
        self.patterns_file = memory_dir / "patterns.json"
        self.history_file = memory_dir / "history.jsonl"

    def record_generation(self, module_name: str, spec: Dict, result: Dict):
        """Record successful generation for pattern learning"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "module": module_name,
            "spec_hash": self._hash_spec(spec),
            "patterns_used": result.get("patterns", []),
            "performance": result.get("metrics", {}),
            "success": result.get("status") == "success"
        }
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def suggest_patterns(self, spec: Dict) -> List[str]:
        """Suggest patterns based on similar past generations"""
        # Load patterns that worked well for similar specs
        similar = self._find_similar_specs(spec)
        return [p for p in similar if p["success"]]
```

## Integration with Existing Tools

### 1. Leveraging Existing Subagents

- Use `zen-architect` for architectural decisions
- Employ `test-coverage` for test completeness
- Leverage `bug-hunter` for validation
- Utilize `modular-builder` as reference implementation

### 2. Hook Integration

```python
# .claude/tools/module_gen_hook.py
#!/usr/bin/env python3

import sys
import json
from pathlib import Path

def pre_generation_hook(spec_path: str):
    """Validate before generation starts"""
    # Check spec exists
    if not Path(spec_path).exists():
        print(f"ERROR: Spec file not found: {spec_path}")
        sys.exit(1)

    # Validate YAML structure
    # Check token limits
    # Verify dependencies

def post_generation_hook(module_path: str):
    """Validate after generation completes"""
    # Run make check
    # Verify interfaces match contract
    # Check test coverage
```

### 3. Parallel Generation Support

```python
async def generate_parallel_variants(spec: Dict, count: int = 3):
    """Generate multiple implementation variants in parallel"""
    variants = []

    # Create variant specifications
    for i in range(count):
        variant_spec = spec.copy()
        variant_spec["variant"] = i
        variant_spec["optimization_focus"] = ["performance", "readability", "minimal"][i]
        variants.append(variant_spec)

    # Generate all variants in parallel
    tasks = [generate_module(v) for v in variants]
    results = await asyncio.gather(*tasks)

    # Compare and select best
    best = await compare_variants(results)
    return best
```

## Success Metrics

1. **Generation Success Rate**: >95% of valid specs generate working code
2. **Test Coverage**: Generated code achieves >80% test coverage
3. **Integration Success**: >90% of modules integrate without modification
4. **Generation Speed**: <2 minutes per module
5. **Parallel Efficiency**: Near-linear speedup with parallel generation

## Next Steps

1. Create proof-of-concept with single subagent
2. Implement state management and checkpointing
3. Develop spec-validator subagent
4. Build orchestration layer
5. Add remaining subagents incrementally
6. Implement parallel generation
7. Add memory and pattern learning