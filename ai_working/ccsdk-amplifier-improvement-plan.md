# CCSDK Toolkit & Amplifier Improvement Plan

## Executive Summary

This document provides an exhaustive list of improvements needed across the `amplifier/ccsdk_toolkit/` and `.claude/` subtrees to prevent the issues encountered during md-synthesizer creation and to better leverage Amplifier's Claude Code capabilities. These improvements will transform the toolkit from a collection of utilities into a self-amplifying, foolproof tool creation platform.

## Context

Based on analysis of:
- **md-synthesizer evolution**: 4 iterations revealing predictable, preventable failures
- **CCSDK toolkit architecture**: Strong foundation but missing defensive patterns
- **Amplifier Claude Code leverage**: Sophisticated patterns not fully integrated with toolkit
- **Root causes**: No mandatory testing, missing defensive utilities, insufficient agent orchestration

---

## Part 1: CCSDK Toolkit Improvements (`amplifier/ccsdk_toolkit/`)

### 1. NEW: Defensive Utilities Module (`defensive/`)

**Location**: `amplifier/ccsdk_toolkit/defensive/`

#### File: `llm_parsing.py`
```python
"""
Robust parsing utilities for LLM responses.
Handles ALL common response formats encountered.
"""

def parse_llm_json(response: str, max_attempts: int = 3) -> Optional[Union[dict, list]]:
    """
    Extract JSON from any LLM response format.

    Handles:
    - Plain JSON
    - Markdown-wrapped JSON (```json blocks)
    - JSON with preambles ("Here's the JSON:", "I'll analyze...")
    - Malformed JSON (missing quotes, trailing commas)
    - Mixed text with embedded JSON

    Returns None if extraction fails after all attempts.
    """

def clean_markdown_artifacts(text: str) -> str:
    """Remove all markdown formatting artifacts."""

def extract_json_from_mixed(text: str) -> List[dict]:
    """Extract individual JSON objects from mixed text."""

def validate_json_schema(data: Any, schema: dict) -> Tuple[bool, str]:
    """Validate extracted JSON against expected schema."""
```

#### File: `retry_patterns.py`
```python
"""
Intelligent retry mechanisms for AI operations.
"""

async def retry_with_feedback(
    func: Callable,
    prompt: str,
    parser: Optional[Callable] = None,
    max_retries: int = 2,
    error_feedback_template: str = DEFAULT_TEMPLATE
) -> Any:
    """
    Retry AI operations with error correction feedback.

    On failure, provides specific feedback about what went wrong
    and what format is expected.
    """

def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> float:
    """Calculate retry delay with jitter to prevent thundering herd."""
```

#### File: `prompt_isolation.py`
```python
"""
Prevent context contamination in prompts.
"""

def isolate_prompt(prompt: str, content: str) -> str:
    """
    Create an isolated prompt that prevents AI from using system context.

    Adds explicit boundaries:
    - "Use ONLY the content provided below"
    - "Do NOT reference any system files"
    - "You have no access to any files or system context"
    """

def create_system_prompt(role: str, constraints: List[str]) -> str:
    """Create focused system prompt with explicit constraints."""
```

#### File: `path_handling.py`
```python
"""
Consistent path handling across pipeline stages.
"""

def ensure_absolute_paths(paths: List[str], base_dir: Path) -> List[Path]:
    """Convert all paths to absolute, preserving originals for reference."""

def create_path_mapping(stage_data: dict) -> dict:
    """Create bidirectional mapping between different path representations."""

def resolve_path_references(
    reference: str,
    path_mapping: dict,
    fallback_search: bool = True
) -> Optional[Path]:
    """Resolve path references with intelligent fallbacks."""
```

#### File: `validation.py`
```python
"""
Contract validation between pipeline stages.
"""

def validate_stage_contract(
    data: Any,
    input_spec: dict,
    output_spec: dict,
    stage_name: str
) -> ValidationResult:
    """Validate data contracts between stages."""

def validate_cli_parameters(
    cli_func: Callable,
    makefile_command: str
) -> List[str]:
    """Ensure CLI parameters match Makefile usage."""
```

### 2. NEW: Testing Infrastructure (`testing/`)

**Location**: `amplifier/ccsdk_toolkit/testing/`

#### File: `test_generator.py`
```python
"""
Automatic test generation for CCSDK tools.
"""

def generate_cli_tests(tool_spec: dict) -> str:
    """
    Generate comprehensive CLI tests from tool specification.

    Creates tests for:
    - Basic invocation
    - All parameter combinations
    - Error conditions
    - Output validation
    """

def generate_stage_tests(pipeline_spec: dict) -> str:
    """Generate tests for each pipeline stage."""

def generate_integration_tests(tool_name: str) -> str:
    """Generate end-to-end integration tests."""
```

#### File: `test_runner.py`
```python
"""
Mandatory test execution before deployment.
"""

class MandatoryTestSuite:
    """Enforces test requirements for all tools."""

    def run_pre_deployment_tests(self, tool_path: Path) -> TestReport:
        """
        Run all mandatory tests:
        1. CLI invocation test
        2. Parameter validation
        3. Stage contract tests
        4. Error handling tests
        5. Context isolation tests
        """

    def validate_test_coverage(self, tool_path: Path) -> bool:
        """Ensure minimum test coverage requirements."""
```

#### File: `fixtures/sample_data.py`
```python
"""
Standard test fixtures for common scenarios.
"""

MARKDOWN_RESPONSES = [
    "```json\n{\"key\": \"value\"}\n```",
    "Here's the JSON response:\n\n```json\n[{\"item\": 1}]\n```",
    "I'll analyze this for you. {\"result\": \"data\"}",
    # ... all variations from md-synthesizer issues
]

CONTAMINATED_RESPONSES = [
    "Looking at AGENTS.md, I can see...",
    "Based on the amplifier-cli-tool-demo repository...",
    # ... examples of context contamination
]
```

### 3. NEW: Tool Creation Orchestration (`orchestration/`)

**Location**: `amplifier/ccsdk_toolkit/orchestration/`

#### File: `tool_creator.py`
```python
"""
Orchestrate tool creation with agent assistance and validation.
"""

class ToolCreationOrchestrator:
    """
    Manages the entire tool creation lifecycle.
    """

    async def create_tool(
        self,
        spec: ToolSpecification,
        use_agents: bool = True
    ) -> ToolCreationResult:
        """
        Create tool with full validation pipeline:
        1. Validate specification
        2. Generate scaffolding
        3. Implement with defensive patterns
        4. Generate tests
        5. Run validation
        6. Deploy with monitoring
        """
```

#### File: `spec_validator.py`
```python
"""
Validate and enhance tool specifications.
"""

def validate_tool_spec(spec: dict) -> ValidationResult:
    """
    Ensure tool spec includes:
    - Clear purpose and contract
    - Stage definitions with types
    - Retry strategies
    - Error handling approach
    """

def enhance_spec_with_defaults(spec: dict) -> dict:
    """Add sensible defaults for missing specification elements."""
```

### 4. UPDATE: Core Module Enhancements

#### File: `core/claude_session.py`
```python
# ADD to existing ClaudeSession class:

async def query_with_retry(
    self,
    prompt: str,
    parser: Optional[Callable] = None,
    max_retries: int = 2,
    require_json: bool = False
) -> Any:
    """
    Query with automatic retry and parsing.

    Uses defensive patterns:
    - Prompt isolation
    - Intelligent retry with feedback
    - Automatic JSON extraction if required
    """

async def query_with_validation(
    self,
    prompt: str,
    output_schema: dict
) -> Any:
    """Query with output schema validation."""
```

#### File: `sessions/session_manager.py`
```python
# ADD to existing SessionManager:

def validate_stage_transition(
    self,
    from_stage: str,
    to_stage: str,
    data: Any
) -> bool:
    """Validate data contract between stages."""

def get_stage_checkpoint(self, stage_name: str) -> Optional[dict]:
    """Retrieve checkpoint for specific stage."""
```

#### File: `config/tool_config.py`
```python
# ADD new configuration options:

class ToolConfig(BaseModel):
    """Enhanced configuration with defensive defaults."""

    # Existing fields...

    # New defensive options
    enforce_testing: bool = True
    require_json_validation: bool = True
    max_retry_attempts: int = 2
    use_prompt_isolation: bool = True
    validate_stage_contracts: bool = True
    auto_generate_tests: bool = True
    update_discoveries_on_failure: bool = True
```

### 5. NEW: Templates for Tool Creation (`templates/`)

**Location**: `amplifier/ccsdk_toolkit/templates/`

#### File: `tool_template.py`
```python
"""
Standard template for new CCSDK tools with all defensive patterns.
"""

TOOL_TEMPLATE = '''
"""
{tool_name}: {purpose}

Created with CCSDK Toolkit - includes defensive patterns.
"""

import click
from pathlib import Path
from typing import List, Optional

from amplifier.ccsdk_toolkit.core import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.sessions import SessionManager
from amplifier.ccsdk_toolkit.defensive import (
    parse_llm_json,
    retry_with_feedback,
    isolate_prompt,
    validate_stage_contract
)

class {ToolClass}:
    """Implementation with defensive patterns baked in."""

    async def process(self):
        """Main processing with stage validation."""
        # Stage contracts validated automatically
        # JSON parsing handled defensively
        # Retry logic built in
        # Context isolation enforced
'''
```

#### File: `test_template.py`
```python
"""
Standard test template ensuring comprehensive coverage.
"""

TEST_TEMPLATE = '''
"""
Tests for {tool_name}.

Generated by CCSDK Toolkit - covers all requirements.
"""

def test_cli_invocation(runner):
    """Test actual CLI command execution."""
    result = runner.invoke(cli, {default_args})
    assert result.exit_code == 0

def test_parameter_handling(runner):
    """Test all CLI parameters."""
    # Test each parameter combination

def test_stage_contracts():
    """Validate data flow between stages."""
    # Test stage transitions

def test_error_conditions():
    """Test error handling."""
    # Test timeout, parsing, missing files

def test_context_isolation():
    """Ensure no context contamination."""
    # Test with contaminated inputs
'''
```

### 6. UPDATE: Example Tools with Defensive Patterns

#### File: `tools/md_synthesizer/synthesizer.py`
```python
# UPDATE with all defensive patterns:

async def _parse_synthesis_response(self, response: str) -> List[dict]:
    """Parse synthesis response with full defensive handling."""

    # Use the new defensive utilities
    from amplifier.ccsdk_toolkit.defensive import parse_llm_json

    ideas = parse_llm_json(response)
    if ideas is None:
        logger.warning("Failed to parse JSON after all attempts")
        return []

    # Validate against expected schema
    from amplifier.ccsdk_toolkit.defensive import validate_json_schema

    valid, error = validate_json_schema(ideas, SYNTHESIS_SCHEMA)
    if not valid:
        logger.warning(f"Schema validation failed: {error}")
        return []

    return ideas
```

---

## Part 2: .claude Subtree Improvements

### 1. UPDATE: Agent Definitions (`.claude/agents/`)

#### File: `amplifier-cli-architect.md`
```markdown
# UPDATE agent definition with more specific guidance:

## Critical Context to Always Provide

### From md-synthesizer Lessons
ALWAYS warn about these common failures:
1. **CLI Parameter Synchronization**: Ensure Makefile passes all params to CLI
2. **Import Correctness**: Use asyncio.TimeoutError not TimeoutError
3. **JSON Parsing Robustness**: Never assume pure JSON response
4. **Path Consistency**: Always use absolute paths in stage outputs
5. **Context Isolation**: Explicitly prevent system context access

### Mandatory Patterns to Recommend
When reviewing ANY tool creation:
- Insist on using defensive utilities from toolkit
- Require test generation before implementation
- Enforce stage contract validation
- Mandate retry mechanisms for all AI calls

### Code Snippets to Provide
# Always include these in your guidance:

```python
# Defensive JSON parsing
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
result = parse_llm_json(response)  # Handles ALL formats

# Retry with feedback
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
result = await retry_with_feedback(session.query, prompt)

# Context isolation
from amplifier.ccsdk_toolkit.defensive import isolate_prompt
safe_prompt = isolate_prompt(prompt, content)
```
```

#### NEW File: `tool-validator.md`
```markdown
---
name: tool-validator
description: Specialized agent for validating CCSDK tools before deployment
tools: Grep, Read, Bash
---

You are the Tool Validator, responsible for ensuring all CCSDK tools meet quality standards before deployment.

## Validation Checklist

### Mandatory Requirements
1. [ ] CLI parameters match Makefile usage
2. [ ] All imports use correct modules (asyncio.TimeoutError)
3. [ ] JSON parsing uses defensive utilities
4. [ ] Paths are handled consistently across stages
5. [ ] Context isolation in all prompts
6. [ ] Retry logic for AI operations
7. [ ] Comprehensive error handling
8. [ ] Tests exist and pass

### Testing Requirements
1. [ ] CLI invocation test exists
2. [ ] Tests use actual make command
3. [ ] Parameter variations tested
4. [ ] Error conditions tested
5. [ ] Context contamination tested

## Validation Process
1. Check tool against requirements
2. Run test suite
3. Verify defensive patterns
4. Test with sample data
5. Validate stage contracts
```

### 2. UPDATE: Commands (`.claude/commands/`)

#### File: `ultrathink-task.md`
```markdown
# ADD new section after "Amplifier CLI Tool Opportunities":

## Mandatory Tool Creation Validation

When ANY task involves creating a new CCSDK tool:

### Pre-Creation Checklist
1. **ALWAYS spawn tool-validator agent** before starting implementation
2. **Require tool specification** with:
   - Purpose and contract
   - Stage definitions with types
   - Expected input/output formats
   - Error handling strategy

### During Creation
1. **Use amplifier-cli-architect FIRST** to get patterns and context
2. **Generate tests BEFORE implementation** using test templates
3. **Apply ALL defensive patterns** from toolkit
4. **Validate stage contracts** between pipeline stages

### Post-Creation Validation
1. **Run tool-validator agent** to check all requirements
2. **Execute generated test suite** with real data
3. **Test error conditions** explicitly
4. **Update DISCOVERIES.md** with any new patterns

### Example Orchestration
```python
# 1. Get context and patterns
amplifier-cli-architect: CONTEXTUALIZE mode

# 2. Design with validation
zen-architect: Design tool architecture
tool-validator: Review specification

# 3. Implement with tests
test-coverage: Generate test suite
modular-builder: Implement with defensive patterns

# 4. Validate before deployment
tool-validator: Final validation
bug-hunter: Check for issues
```
```

#### NEW File: `create-ccsdk-tool.md`
```markdown
## Usage

`/create-ccsdk-tool <tool_name> <purpose>`

## Context

Creates a new CCSDK toolkit tool with all defensive patterns and testing.

## Process

1. **Specification Phase**
   - Define tool purpose and contract
   - Specify stages if multi-stage pipeline
   - Determine retry and error strategies

2. **Architecture Phase**
   - Spawn amplifier-cli-architect for context
   - Spawn zen-architect for design
   - Create formal specification

3. **Test Generation Phase**
   - Generate comprehensive test suite
   - Create CLI invocation tests
   - Add error condition tests

4. **Implementation Phase**
   - Use modular-builder with defensive patterns
   - Apply all toolkit utilities
   - Implement with testing in parallel

5. **Validation Phase**
   - Run tool-validator agent
   - Execute all tests
   - Check defensive patterns
   - Verify stage contracts

6. **Deployment Phase**
   - Update Makefile
   - Add to documentation
   - Update DISCOVERIES.md if needed

## Output Format

- Tool implementation in `amplifier/ccsdk_toolkit/examples/{tool_name}/`
- Test suite in same directory
- Makefile command added
- Documentation updated
```

### 3. NEW: Hooks and Automation (`.claude/settings.json` and `.claude/tools/`)

#### Update: `.claude/settings.json`
```json
{
  // Existing configuration...

  "hooks": {
    // Existing hooks...

    // ADD new hooks for tool creation:
    "PreToolCreation": [
      {
        "matcher": "ccsdk_toolkit/examples",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/tools/validate_tool_spec.py"
          }
        ]
      }
    ],

    "PostToolCreation": [
      {
        "matcher": "ccsdk_toolkit/examples",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/tools/run_tool_tests.py"
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/tools/update_discoveries.py"
          }
        ]
      }
    ],

    "OnTestFailure": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/tools/capture_test_failure.py"
          }
        ]
      }
    ]
  }
}
```

#### NEW File: `.claude/tools/validate_tool_spec.py`
```python
#!/usr/bin/env python3
"""
Validate tool specification before creation.
Prevents common issues identified in md-synthesizer evolution.
"""

import json
import sys
from pathlib import Path

def validate_spec(spec_path: Path) -> bool:
    """Validate tool specification completeness."""

    required_fields = [
        'name',
        'purpose',
        'stages',
        'error_strategy',
        'retry_config'
    ]

    # Check specification
    with open(spec_path) as f:
        spec = json.load(f)

    missing = [f for f in required_fields if f not in spec]
    if missing:
        print(f"ERROR: Missing required fields: {missing}")
        return False

    # Validate stages
    for stage in spec.get('stages', []):
        if 'input' not in stage or 'output' not in stage:
            print(f"ERROR: Stage {stage.get('name')} missing input/output")
            return False

    return True

if __name__ == "__main__":
    # Read spec from stdin or file
    # Validate and provide feedback
    # Exit with appropriate code
```

#### NEW File: `.claude/tools/run_tool_tests.py`
```python
#!/usr/bin/env python3
"""
Automatically run tests for newly created tools.
Ensures no tool is deployed without testing.
"""

import subprocess
import sys
from pathlib import Path

def run_mandatory_tests(tool_path: Path) -> bool:
    """Run mandatory test suite for tool."""

    test_requirements = [
        "test_cli_invocation",
        "test_parameter_handling",
        "test_stage_contracts",
        "test_error_conditions",
        "test_context_isolation"
    ]

    # Run pytest with specific test selection
    for test in test_requirements:
        result = subprocess.run(
            ["pytest", f"{tool_path}/test_{tool_path.name}.py::{test}", "-v"],
            capture_output=True
        )

        if result.returncode != 0:
            print(f"FAILED: {test}")
            print(result.stdout.decode())
            return False

    print("All mandatory tests passed!")
    return True
```

#### NEW File: `.claude/tools/capture_test_failure.py`
```python
#!/usr/bin/env python3
"""
Capture test failures and update DISCOVERIES.md.
Implements continuous learning from failures.
"""

import json
from datetime import datetime
from pathlib import Path

def capture_failure(test_output: str, tool_name: str):
    """
    Capture test failure and add to DISCOVERIES.md.
    """

    discovery_entry = f"""
## {tool_name} Test Failure ({datetime.now().strftime('%Y-%m-%d')})

### Issue
{extract_error(test_output)}

### Root Cause
{analyze_cause(test_output)}

### Solution
{suggest_solution(test_output)}

### Prevention
Add to defensive patterns in toolkit

---
"""

    discoveries_path = Path("DISCOVERIES.md")
    with open(discoveries_path, 'a') as f:
        f.write(discovery_entry)
```

### 4. UPDATE: DISCOVERIES.md Automation

Add new section to track tool creation patterns:

```markdown
## Tool Creation Patterns (Auto-Updated)

### Successful Patterns
- [Pattern tracked by hooks]

### Common Failures
- [Automatically captured from test failures]

### Defensive Utilities Added
- [Track new defensive patterns as they're created]
```

---

## Part 3: Integration Workflows

### 1. NEW: Makefile Commands

Add to root `Makefile`:

```makefile
# Tool Creation Commands
create-tool: ## Create new CCSDK tool with validation. Usage: make create-tool NAME=my_tool PURPOSE="..."
	@if [ -z "$(NAME)" ] || [ -z "$(PURPOSE)" ]; then \
		echo "Error: NAME and PURPOSE required"; \
		exit 1; \
	fi
	@echo "Creating tool $(NAME) with purpose: $(PURPOSE)"
	@uv run python -m amplifier.ccsdk_toolkit.orchestration.tool_creator \
		--name $(NAME) \
		--purpose "$(PURPOSE)" \
		--with-tests \
		--with-validation

validate-tool: ## Validate existing tool. Usage: make validate-tool NAME=my_tool
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME required"; \
		exit 1; \
	fi
	@echo "Validating tool $(NAME)..."
	@uv run python -m amplifier.ccsdk_toolkit.testing.test_runner \
		--tool $(NAME) \
		--mandatory-only

test-defensive: ## Test all defensive utilities
	@echo "Testing defensive patterns..."
	@uv run pytest amplifier/ccsdk_toolkit/defensive/ -v

update-tool-templates: ## Update all tool templates with latest patterns
	@echo "Updating tool templates..."
	@uv run python -m amplifier.ccsdk_toolkit.templates.update_all
```

### 2. NEW: GitHub Actions Workflow

```yaml
# .github/workflows/tool-validation.yml
name: CCSDK Tool Validation

on:
  pull_request:
    paths:
      - 'amplifier/ccsdk_toolkit/examples/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run mandatory tests
        run: |
          make validate-tool NAME=${{ env.TOOL_NAME }}

      - name: Check defensive patterns
        run: |
          python .claude/tools/validate_defensive_patterns.py

      - name: Update DISCOVERIES if failed
        if: failure()
        run: |
          python .claude/tools/capture_test_failure.py
```

---

## Part 4: Documentation Updates

### 1. NEW: `amplifier/ccsdk_toolkit/DEFENSIVE_PATTERNS.md`

Document all defensive patterns with examples:

```markdown
# Defensive Patterns for CCSDK Tools

## Always Use These Patterns

### 1. JSON Parsing
```python
# NEVER do this:
ideas = json.loads(response)  # Will fail on markdown

# ALWAYS do this:
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
ideas = parse_llm_json(response)  # Handles all formats
```

### 2. Retry Logic
```python
# NEVER do this:
result = await session.query(prompt)  # Single attempt

# ALWAYS do this:
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
result = await retry_with_feedback(session.query, prompt)
```

### 3. Context Isolation
```python
# NEVER do this:
prompt = f"Summarize {file_path}"  # AI might read system files

# ALWAYS do this:
from amplifier.ccsdk_toolkit.defensive import isolate_prompt
prompt = isolate_prompt(f"Summarize this content", content)
```

### 4. Path Handling
```python
# NEVER do this:
files = ["file1.md", "file2.md"]  # Relative paths

# ALWAYS do this:
from amplifier.ccsdk_toolkit.defensive import ensure_absolute_paths
files = ensure_absolute_paths(files, base_dir)
```

### 5. Stage Validation
```python
# NEVER do this:
stage2_input = stage1_output  # Assume it's correct

# ALWAYS do this:
from amplifier.ccsdk_toolkit.defensive import validate_stage_contract
validated = validate_stage_contract(stage1_output, stage2_spec)
```
```

### 2. UPDATE: `amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md`

Add new sections:

```markdown
## Mandatory Tool Creation Process

### Step 1: Create Specification
Every tool MUST start with a specification:

```yaml
name: my_analyzer
purpose: Analyze code for patterns
stages:
  - name: extraction
    input: List[Path]
    output: List[Dict]
    retry: true
  - name: synthesis
    input: List[Dict]
    output: SynthesisResult
    requires_json: true
```

### Step 2: Generate Tests First
Tests are generated BEFORE implementation:

```bash
make generate-tests NAME=my_analyzer
```

### Step 3: Implement with Defensive Patterns
Use the provided template and defensive utilities:

```python
from amplifier.ccsdk_toolkit.defensive import (
    parse_llm_json,
    retry_with_feedback,
    isolate_prompt
)
```

### Step 4: Validate Before Deploy
Run mandatory validation:

```bash
make validate-tool NAME=my_analyzer
```

## Common Pitfalls and Solutions

Based on md-synthesizer evolution:

| Issue | Solution |
|-------|----------|
| Missing CLI params | Check Makefile passes all params |
| Import errors | Use asyncio.TimeoutError |
| JSON parsing fails | Use parse_llm_json() |
| Path inconsistency | Use ensure_absolute_paths() |
| Context contamination | Use isolate_prompt() |
```

---

## Implementation Priority

### Week 1: Critical Defensive Layer
1. Create `defensive/` module with all utilities
2. Update md_synthesizer with defensive patterns
3. Create test templates
4. Update DEVELOPER_GUIDE.md

### Week 2: Testing Infrastructure
1. Build test generator
2. Create mandatory test runner
3. Add validation hooks
4. Update Makefile commands

### Week 3: Agent Integration
1. Update amplifier-cli-architect with lessons
2. Create tool-validator agent
3. Update ultrathink-task command
4. Create create-ccsdk-tool command

### Week 4: Automation & Learning
1. Implement all hooks
2. Create GitHub Actions workflow
3. Automate DISCOVERIES.md updates
4. Deploy monitoring

---

## Success Metrics

### Immediate (Week 1)
- [ ] md_synthesizer works first time with defensive patterns
- [ ] No JSON parsing failures
- [ ] No context contamination

### Short-term (Month 1)
- [ ] 100% of new tools pass validation first time
- [ ] Zero repeated failures from DISCOVERIES.md
- [ ] All tools have 80%+ test coverage

### Long-term (Quarter 1)
- [ ] Tool creation time reduced by 50%
- [ ] Failure rate < 5% for new tools
- [ ] DISCOVERIES.md automatically captures all patterns
- [ ] Toolkit self-improves from usage

---

## Conclusion

These improvements transform the CCSDK toolkit from a collection of utilities into a self-amplifying platform that:

1. **Prevents predictable failures** through defensive patterns
2. **Enforces quality** through mandatory testing
3. **Learns from experience** via automated discovery capture
4. **Leverages AI assistance** through agent orchestration
5. **Maintains simplicity** while adding robustness

The md-synthesizer's 4-iteration journey revealed that every failure was preventable with proper infrastructure. These improvements ensure future tools succeed on the first attempt by building on captured knowledge and enforced best practices.