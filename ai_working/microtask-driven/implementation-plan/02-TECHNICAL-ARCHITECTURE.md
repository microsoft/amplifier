# Technical Architecture: Amplifier CLI Tool Builder

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CLI INTERFACE                         │
│                 (Click Framework)                        │
│  amplifier-tool-builder create|analyze|test|package      │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                     │
│                   (Python Core)                          │
│  • Session Management                                    │
│  • State Persistence                                     │
│  • Pipeline Coordination                                 │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                   PIPELINE STAGES                        │
│              (Sequential Processing)                     │
│  1. Requirements Analysis                                │
│  2. Architecture Design                                  │
│  3. Code Generation                                      │
│  4. Quality Verification                                 │
│  5. Packaging & Deployment                               │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                 MICROTASK AGENTS                         │
│            (Claude Code SDK Integration)                 │
│  • Requirements Analyzer (5-10s per aspect)              │
│  • Architecture Designer (5-10s per component)           │
│  • Code Generator (5-10s per module)                     │
│  • Quality Verifier (5-10s per check)                    │
│  • Metacognitive Analyzer (learns from failures)         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              PERSISTENCE & RECOVERY                      │
│                  (File System)                           │
│  • Session State (JSON)                                  │
│  • Generated Code (Python)                               │
│  • Metadata & Metrics (JSON)                             │
│  • Pattern Library (YAML)                                │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. CLI Interface Layer

**Technology**: Python Click Framework

```python
# amplifier_tool_builder/cli.py
import click
from pathlib import Path

@click.group()
def cli():
    """Amplifier CLI Tool Builder - Create intelligent CLI tools"""
    pass

@cli.command()
@click.argument('name')
@click.option('--description', required=True)
@click.option('--input-type', default='text')
@click.option('--output-type', default='json')
@click.option('--resume', help='Resume from session ID')
def create(name: str, description: str, input_type: str, output_type: str, resume: str):
    """Create a new Amplifier CLI Tool"""
    session = Session.load(resume) if resume else Session.new(name)
    asyncio.run(build_tool(name, description, input_type, output_type, session))
```

### 2. Orchestration Layer

**Purpose**: Manages workflow, state, and coordination

```python
# amplifier_tool_builder/orchestrator.py
class ToolBuilderOrchestrator:
    def __init__(self, session: Session):
        self.session = session
        self.stages = self._initialize_stages()
        self.storage = Storage(session.id)

    def _initialize_stages(self) -> List[Stage]:
        return [
            RequirementsAnalysisStage(),
            ArchitectureDesignStage(),
            CodeGenerationStage(),
            QualityVerificationStage(),
            PackagingStage()
        ]

    async def build_tool(self, spec: ToolSpecification) -> GeneratedTool:
        """Main orchestration logic"""
        for stage in self.stages:
            if self.session.is_completed(stage.name):
                continue

            result = await stage.execute(spec, self.session.context)
            self.session.save_stage_result(stage.name, result)
            self.storage.save_checkpoint(self.session)

        return self._assemble_tool(self.session.results)
```

### 3. Microtask Agent Architecture

**Key Principle**: Each AI call is focused, 5-10 seconds max

```python
# amplifier_tool_builder/agents/base.py
class MicrotaskAgent:
    """Base class for all microtask agents"""

    def __init__(self, task_type: str, timeout: int = 10):
        self.task_type = task_type
        self.timeout = timeout

    async def execute(self, input_data: Dict) -> Dict:
        """Execute a single focused microtask"""
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt=self._get_system_prompt(),
                max_turns=1,
                timeout=self.timeout
            )
        ) as client:
            prompt = self._build_prompt(input_data)
            await client.query(prompt)

            response = ""
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            response += block.text

            return self._parse_response(response)
```

### 4. Pipeline Stage Implementation

#### Stage 1: Requirements Analysis

```python
# amplifier_tool_builder/stages/requirements.py
class RequirementsAnalysisStage(Stage):
    """Analyzes tool requirements through focused microtasks"""

    async def execute(self, spec: ToolSpecification, context: Dict) -> RequirementsAnalysis:
        analysis = RequirementsAnalysis()

        # Microtask 1: Identify core problem (5-10s)
        problem = await self.agents.problem_identifier.execute({
            "description": spec.description,
            "examples": spec.examples
        })
        analysis.core_problem = problem
        self.save_progress(analysis)

        # Microtask 2: Determine code vs AI split (5-10s)
        split = await self.agents.split_analyzer.execute({
            "problem": problem,
            "constraints": spec.constraints
        })
        analysis.code_ai_split = split
        self.save_progress(analysis)

        # Microtask 3: Identify data flows (5-10s)
        flows = await self.agents.flow_analyzer.execute({
            "problem": problem,
            "input_type": spec.input_type,
            "output_type": spec.output_type
        })
        analysis.data_flows = flows
        self.save_progress(analysis)

        # Microtask 4: Determine required agents (5-10s)
        agents = await self.agents.agent_designer.execute({
            "split": split,
            "flows": flows
        })
        analysis.required_agents = agents
        self.save_progress(analysis)

        return analysis
```

#### Stage 2: Architecture Design

```python
# amplifier_tool_builder/stages/architecture.py
class ArchitectureDesignStage(Stage):
    """Designs tool architecture through focused microtasks"""

    async def execute(self, spec: ToolSpecification, context: Dict) -> Architecture:
        requirements = context['requirements_analysis']
        architecture = Architecture()

        # Microtask 1: Design module structure (5-10s)
        modules = await self.agents.module_designer.execute({
            "requirements": requirements,
            "patterns": self.load_patterns()
        })
        architecture.modules = modules
        self.save_progress(architecture)

        # Microtask 2: Define interfaces (5-10s)
        interfaces = await self.agents.interface_designer.execute({
            "modules": modules,
            "data_flows": requirements.data_flows
        })
        architecture.interfaces = interfaces
        self.save_progress(architecture)

        # Microtask 3: Design error handling (5-10s)
        error_handling = await self.agents.error_designer.execute({
            "modules": modules,
            "critical_paths": requirements.critical_paths
        })
        architecture.error_handling = error_handling
        self.save_progress(architecture)

        return architecture
```

#### Stage 3: Code Generation

```python
# amplifier_tool_builder/stages/generation.py
class CodeGenerationStage(Stage):
    """Generates code through focused microtasks"""

    async def execute(self, spec: ToolSpecification, context: Dict) -> GeneratedCode:
        architecture = context['architecture']
        generated = GeneratedCode()

        for module in architecture.modules:
            # Microtask: Generate module code (5-10s each)
            code = await self.agents.code_generator.execute({
                "module": module,
                "interfaces": architecture.interfaces,
                "patterns": self.get_pattern_for_module(module)
            })

            generated.add_module(module.name, code)
            self.save_progress(generated)

            # Microtask: Generate tests (5-10s each)
            tests = await self.agents.test_generator.execute({
                "module": module,
                "code": code
            })

            generated.add_tests(module.name, tests)
            self.save_progress(generated)

        return generated
```

#### Stage 4: Quality Verification

```python
# amplifier_tool_builder/stages/verification.py
class QualityVerificationStage(Stage):
    """Verifies quality through focused microtasks"""

    async def execute(self, spec: ToolSpecification, context: Dict) -> VerificationResult:
        generated = context['generated_code']
        result = VerificationResult()

        # Microtask 1: Verify code quality (5-10s)
        code_quality = await self.agents.code_verifier.execute({
            "code": generated.get_all_code(),
            "standards": self.quality_standards
        })
        result.code_quality = code_quality

        # Microtask 2: Verify pattern compliance (5-10s)
        pattern_compliance = await self.agents.pattern_verifier.execute({
            "code": generated.get_all_code(),
            "required_patterns": ["microtask", "incremental_save", "feedback_loop"]
        })
        result.pattern_compliance = pattern_compliance

        # Microtask 3: Test execution simulation (5-10s)
        test_results = await self.agents.test_simulator.execute({
            "tests": generated.get_all_tests(),
            "code": generated.get_all_code()
        })
        result.test_results = test_results

        if not result.passes_threshold():
            # Metacognitive: Analyze why it failed
            failure_analysis = await self.agents.metacognitive_analyzer.execute({
                "result": result,
                "context": context
            })
            result.improvement_strategy = failure_analysis.strategy

        return result
```

### 5. Metacognitive System

```python
# amplifier_tool_builder/metacognitive/analyzer.py
class MetacognitiveAnalyzer:
    """Analyzes failures and improves strategies"""

    async def analyze_failure(self,
                             attempt: Dict,
                             result: VerificationResult,
                             history: List[Dict]) -> Strategy:
        """Analyze why generation failed and suggest improvements"""

        # Focused analysis of failure patterns
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="""You are a metacognitive analyzer.
                Analyze tool generation failures and suggest improvements.""",
                max_turns=1
            )
        ) as client:

            prompt = f"""
            Analyze this tool generation failure:

            Attempt: {json.dumps(attempt, indent=2)}
            Result: {json.dumps(result.to_dict(), indent=2)}
            History: {json.dumps(history[-3:], indent=2)}  # Last 3 attempts

            Identify:
            1. Root cause of failure
            2. Pattern in failures
            3. Suggested strategy adjustment
            4. Should we retry or escalate?
            """

            await client.query(prompt)
            response = await self._collect_response(client)

            return Strategy.from_analysis(response)
```

### 6. Session Management & Recovery

```python
# amplifier_tool_builder/session.py
class Session:
    """Manages tool building session with full recovery capability"""

    def __init__(self, session_id: str):
        self.id = session_id
        self.created_at = datetime.now()
        self.state = "initializing"
        self.completed_stages = []
        self.current_stage = None
        self.results = {}
        self.metadata = {}

    def save(self):
        """Save session state to disk"""
        session_path = Path(f".amplifier/sessions/{self.id}.json")
        session_path.parent.mkdir(parents=True, exist_ok=True)

        with open(session_path, 'w') as f:
            json.dump({
                "id": self.id,
                "created_at": self.created_at.isoformat(),
                "state": self.state,
                "completed_stages": self.completed_stages,
                "current_stage": self.current_stage,
                "results": self.results,
                "metadata": self.metadata
            }, f, indent=2)

    @classmethod
    def load(cls, session_id: str) -> 'Session':
        """Load session from disk"""
        session_path = Path(f".amplifier/sessions/{session_id}.json")

        if not session_path.exists():
            raise ValueError(f"Session {session_id} not found")

        with open(session_path) as f:
            data = json.load(f)

        session = cls(data['id'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.state = data['state']
        session.completed_stages = data['completed_stages']
        session.current_stage = data['current_stage']
        session.results = data['results']
        session.metadata = data['metadata']

        return session
```

### 7. Pattern Library

```python
# amplifier_tool_builder/patterns/library.py
class PatternLibrary:
    """Reusable patterns for tool generation"""

    PATTERNS = {
        "microtask_executor": """
async def execute_microtask(self, task: str, input_data: Dict) -> Dict:
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt=f"Execute {task}",
            max_turns=1,
            timeout=10
        )
    ) as client:
        await client.query(json.dumps(input_data))
        return await self._collect_response(client)
""",

        "incremental_save": """
def save_progress(self, data: Any):
    checkpoint_file = self.get_checkpoint_file()
    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)
""",

        "feedback_loop": """
async def process_with_feedback(self, item: Any) -> Result:
    for attempt in range(self.max_attempts):
        result = await self.process(item)
        if await self.verify(result):
            return result
        feedback = await self.analyze_failure(result)
        self.adjust_strategy(feedback)
    return result
""",

        "metacognitive_improvement": """
async def analyze_and_improve(self, failure: Dict) -> Strategy:
    analysis = await self.metacognitive_agent.analyze(failure)
    if analysis.suggests_retry:
        return self.adjust_strategy(analysis.improvements)
    return self.escalate_to_human(analysis)
"""
    }
```

### 8. Custom Tools via MCP

```python
# amplifier_tool_builder/mcp/tools.py
class ToolBuilderMCPServer:
    """MCP server providing custom tools for tool building"""

    @tool("validate_python_syntax")
    async def validate_syntax(self, code: str) -> Dict:
        """Validate Python syntax"""
        try:
            compile(code, "<string>", "exec")
            return {"valid": True}
        except SyntaxError as e:
            return {"valid": False, "error": str(e)}

    @tool("test_generated_code")
    async def test_code(self, code: str, test: str) -> Dict:
        """Test generated code"""
        # Implementation for testing
        pass

    @tool("check_pattern_compliance")
    async def check_patterns(self, code: str, patterns: List[str]) -> Dict:
        """Check if code follows required patterns"""
        # Implementation for pattern checking
        pass
```

## Data Models

```python
# amplifier_tool_builder/models.py
from pydantic import BaseModel
from typing import List, Dict, Optional

class ToolSpecification(BaseModel):
    name: str
    description: str
    input_type: str = "text"
    output_type: str = "json"
    examples: List[Dict] = []
    constraints: List[str] = []

class RequirementsAnalysis(BaseModel):
    core_problem: str
    code_ai_split: Dict[str, List[str]]
    data_flows: List[Dict]
    required_agents: List[str]
    critical_paths: List[str]

class Architecture(BaseModel):
    modules: List[Module]
    interfaces: List[Interface]
    error_handling: ErrorStrategy
    patterns_used: List[str]

class GeneratedCode(BaseModel):
    modules: Dict[str, str]
    tests: Dict[str, str]
    configuration: Dict
    documentation: str

class VerificationResult(BaseModel):
    code_quality: float
    pattern_compliance: Dict[str, bool]
    test_results: TestResults
    improvement_strategy: Optional[Strategy]

    def passes_threshold(self) -> bool:
        return (self.code_quality >= 0.8 and
                all(self.pattern_compliance.values()) and
                self.test_results.pass_rate >= 0.95)
```

## Error Handling Strategy

```python
# amplifier_tool_builder/errors.py
class AmplifierError(Exception):
    """Base exception for Amplifier Tool Builder"""
    pass

class MicrotaskTimeout(AmplifierError):
    """Raised when a microtask exceeds time limit"""
    pass

class GenerationFailure(AmplifierError):
    """Raised when code generation fails after max attempts"""
    pass

class ErrorHandler:
    """Centralized error handling with recovery strategies"""

    async def handle_with_recovery(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                return await operation()
            except MicrotaskTimeout:
                # Fall back to simpler approach
                return await self.fallback_operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt - escalate
                    return await self.escalate_to_metacognitive(e)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Performance Optimizations

### Parallel Microtask Execution

```python
# amplifier_tool_builder/parallel.py
async def execute_parallel_microtasks(tasks: List[MicrotaskAgent],
                                     input_data: Dict) -> List[Dict]:
    """Execute independent microtasks in parallel"""

    # Create tasks for parallel execution
    coroutines = [
        task.execute(input_data) for task in tasks
    ]

    # Execute in parallel with timeout
    results = await asyncio.gather(*coroutines, return_exceptions=True)

    # Handle any failures
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Fallback for failed task
            processed_results.append(await tasks[i].fallback_execute(input_data))
        else:
            processed_results.append(result)

    return processed_results
```

### Caching Strategy

```python
# amplifier_tool_builder/cache.py
class PatternCache:
    """Cache for commonly used patterns and generated code"""

    def __init__(self):
        self.pattern_cache = {}
        self.code_cache = {}

    def get_cached_pattern(self, pattern_key: str) -> Optional[str]:
        """Retrieve cached pattern if available"""
        return self.pattern_cache.get(pattern_key)

    def cache_generated_code(self, spec_hash: str, code: str):
        """Cache generated code for similar specifications"""
        self.code_cache[spec_hash] = {
            "code": code,
            "timestamp": datetime.now(),
            "usage_count": 0
        }
```

## Deployment Architecture

```
amplifier-tool-builder/
├── amplifier_tool_builder/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point
│   ├── orchestrator.py         # Main orchestration
│   ├── session.py              # Session management
│   ├── models.py               # Data models
│   ├── errors.py               # Error handling
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py            # Base microtask agent
│   │   ├── requirements.py    # Requirements agents
│   │   ├── architecture.py    # Architecture agents
│   │   ├── generation.py      # Code generation agents
│   │   └── verification.py    # Verification agents
│   ├── stages/
│   │   ├── __init__.py
│   │   └── ... (stage implementations)
│   ├── patterns/
│   │   ├── __init__.py
│   │   └── library.py         # Pattern library
│   ├── metacognitive/
│   │   ├── __init__.py
│   │   └── analyzer.py        # Metacognitive analysis
│   └── mcp/
│       ├── __init__.py
│       └── tools.py           # MCP server tools
├── tests/
│   └── ... (comprehensive tests)
├── templates/
│   └── ... (tool templates)
├── pyproject.toml
├── README.md
└── Makefile
```

## Integration Points

### Claude Code SDK Integration

- Each microtask uses focused Claude Code SDK calls
- System prompts are specialized per task type
- Timeouts ensure 5-10 second execution
- Custom tools via MCP extend capabilities

### File System Integration

- Sessions saved as JSON for recovery
- Generated code written incrementally
- Pattern library stored as YAML
- Metrics tracked in JSON

### External Tool Integration

- Git for version control of generated tools
- Python packaging tools for distribution
- Testing frameworks for validation
- Documentation generators

## Security Considerations

1. **Input Validation**: All user inputs validated before processing
2. **Sandboxed Execution**: Generated code tested in isolated environment
3. **API Key Management**: Secure handling of Claude API credentials
4. **Session Isolation**: Each session isolated from others
5. **Output Sanitization**: Generated code checked for security issues

## Next Steps

Continue to [Implementation Roadmap](03-IMPLEMENTATION-ROADMAP.md) for the phased development plan.