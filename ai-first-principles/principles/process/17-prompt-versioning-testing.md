# Principle #17 - Prompt Versioning and Testing

## Plain-Language Definition

Prompts are code and should be treated as first-class software artifacts with version control, automated testing, and quality assurance. Just as you wouldn't deploy untested code, you shouldn't deploy untested prompts.

## Why This Matters for AI-First Development

In AI-first systems, prompts are the primary interface between human intent and AI execution. A poorly crafted prompt can cause an AI agent to generate incorrect code, make wrong decisions, or produce inconsistent outputs. Unlike traditional code where bugs are often deterministic and reproducible, prompt-related failures can be subtle, context-dependent, and difficult to diagnose. A prompt that works perfectly with one model version might fail catastrophically with another.

When prompts are treated as throwaway strings rather than critical infrastructure, three problems emerge:

1. **Prompt degradation over time**: As systems evolve, prompts that once worked well become outdated. Without version control and testing, you can't track when and why prompts stopped working effectively, making debugging nearly impossible.

2. **Inability to measure quality**: Without systematic testing, you have no objective way to know if a prompt change improves or degrades output quality. Teams make changes based on intuition rather than data, leading to inconsistent results.

3. **No regression protection**: When prompts are modified, there's no safety net to catch regressions. A "small improvement" to a prompt might fix one case but break ten others, and you won't know until production failures occur.

Treating prompts as code solves these problems through familiar software engineering practices: version control tracks changes over time, automated tests catch regressions before deployment, and systematic evaluation provides objective quality metrics. Just as you wouldn't deploy code without tests, you shouldn't deploy prompts without validation that they produce correct, consistent outputs.

## Implementation Approaches

### 1. **Version Control for Prompt Libraries**

Store prompts as files in version control, separate from application code:

```
prompts/
├── v1/
│   ├── code_generation.md
│   ├── code_review.md
│   └── bug_analysis.md
├── v2/
│   ├── code_generation.md  # Improved version
│   └── code_review.md
└── metadata.json           # Version info and changelogs
```

Each prompt file includes:
- The prompt template itself
- Variables that can be injected
- Expected output format
- Known limitations
- Version history

**When to use**: For any prompt that's used programmatically or repeatedly. Essential for production systems.

**Success looks like**: Complete history of prompt evolution, ability to rollback to previous versions, and clear documentation of what changed and why.

### 2. **Automated Prompt Testing Framework**

Create a test suite that validates prompt outputs against expected behaviors:

```python
def test_code_generation_prompt():
    """Test that code generation prompt produces valid Python"""
    prompt = load_prompt("code_generation", version="v2")
    test_cases = [
        {"input": "Create a function to sort a list", "expected_pattern": r"def \w+\(.*\):"},
        {"input": "Add error handling to this code", "expected_contains": "try:"},
    ]

    for case in test_cases:
        output = generate_with_prompt(prompt, case["input"])
        assert_matches_pattern(output, case["expected_pattern"])
```

Tests verify:
- Output format consistency
- Presence of required elements
- Absence of known failure patterns
- Performance within acceptable bounds

**When to use**: Before deploying any prompt change, as part of CI/CD pipeline.

**Success looks like**: Automated tests catch regressions before deployment, providing confidence in prompt changes.

### 3. **Regression Test Suite for Prompt Changes**

Maintain a suite of real-world examples that previously caused issues:

```python
class PromptRegressionTests:
    """Tests preventing reintroduction of known prompt failures"""

    def test_issue_234_code_generation_infinite_loop(self):
        """
        Issue #234: Prompt generated code with infinite loops
        Fixed in v2.1 by adding explicit loop termination instructions
        """
        prompt = load_prompt("code_generation", version="current")
        output = generate_with_prompt(
            prompt,
            "Create a function that processes items until none remain"
        )
        assert "while True:" not in output or "break" in output

    def test_issue_456_hallucinated_imports(self):
        """
        Issue #456: Prompt caused AI to import non-existent libraries
        Fixed in v2.3 by constraining to standard library
        """
        prompt = load_prompt("code_generation", version="current")
        output = generate_with_prompt(prompt, "Parse JSON data")
        # Should use 'json' not imaginary libraries
        assert "import json" in output
        assert "import jsonparser" not in output
```

**When to use**: Whenever a prompt-related bug is discovered and fixed.

**Success looks like**: Known issues never recur, even after prompt refactoring or model updates.

### 4. **A/B Testing Framework for Prompt Variants**

Test multiple prompt versions in parallel to objectively measure quality:

```python
def ab_test_prompts(prompt_a: str, prompt_b: str, test_inputs: list):
    """Compare two prompt versions across multiple test cases"""
    results = {"prompt_a": [], "prompt_b": []}

    for input_case in test_inputs:
        output_a = generate_with_prompt(prompt_a, input_case)
        output_b = generate_with_prompt(prompt_b, input_case)

        results["prompt_a"].append({
            "input": input_case,
            "output": output_a,
            "score": evaluate_output(output_a, input_case)
        })
        results["prompt_b"].append({
            "input": input_case,
            "output": output_b,
            "score": evaluate_output(output_b, input_case)
        })

    # Statistical comparison
    avg_score_a = mean(r["score"] for r in results["prompt_a"])
    avg_score_b = mean(r["score"] for r in results["prompt_b"])

    return {
        "winner": "prompt_a" if avg_score_a > avg_score_b else "prompt_b",
        "results": results,
        "confidence": calculate_statistical_significance(results)
    }
```

**When to use**: When optimizing prompts, comparing different approaches, or deciding between improvements.

**Success looks like**: Data-driven decisions about which prompt version is better, backed by statistical evidence.

### 5. **Prompt Template Libraries with Validation**

Create reusable, validated prompt components:

```python
class PromptLibrary:
    """Centralized, versioned prompt templates"""

    @staticmethod
    def code_generation(language: str, task: str, version: str = "latest") -> str:
        """
        Generate code in specified language for given task

        Args:
            language: Programming language (python, javascript, etc.)
            task: Description of code to generate
            version: Prompt template version (default: latest)

        Returns:
            Formatted prompt string

        Validation:
            - language must be in supported list
            - task must be non-empty
            - version must exist in prompt library
        """
        validate_language(language)
        validate_task(task)
        template = load_prompt_template("code_generation", version)
        return template.format(language=language, task=task)
```

**When to use**: For any prompt used across multiple parts of the system.

**Success looks like**: Reusable, tested prompt components that reduce duplication and ensure consistency.

### 6. **Output Quality Metrics and Monitoring**

Track prompt performance over time:

```python
class PromptMetrics:
    """Monitor prompt quality in production"""

    def log_prompt_execution(
        self,
        prompt_id: str,
        prompt_version: str,
        input_data: dict,
        output: str,
        execution_time: float
    ):
        """Log prompt execution for analysis"""
        metrics = {
            "timestamp": now(),
            "prompt_id": prompt_id,
            "version": prompt_version,
            "success": validate_output(output),
            "output_length": len(output),
            "execution_time": execution_time,
            "model": get_current_model(),
        }
        self.store_metrics(metrics)

    def get_prompt_quality_report(self, prompt_id: str, days: int = 7) -> dict:
        """Analyze prompt quality over time"""
        recent_executions = self.get_executions(prompt_id, days)
        return {
            "total_executions": len(recent_executions),
            "success_rate": calculate_success_rate(recent_executions),
            "avg_execution_time": mean(e["execution_time"] for e in recent_executions),
            "version_distribution": count_by_version(recent_executions),
            "failure_patterns": identify_failure_patterns(recent_executions),
        }
```

**When to use**: In production systems where prompt quality impacts user experience.

**Success looks like**: Real-time visibility into prompt performance, early detection of degradation.

## Good Examples vs Bad Examples

### Example 1: Version-Controlled Prompt File

**Good:**
```markdown
# Code Generation Prompt v2.3

## Version History
- v2.3 (2025-09-28): Added explicit instruction to avoid infinite loops
- v2.2 (2025-09-15): Constrained imports to standard library
- v2.1 (2025-09-01): Improved error handling instructions
- v2.0 (2025-08-15): Major rewrite for better consistency

## Prompt Template

You are a Python code generator. Generate clean, well-documented Python code.

**Requirements:**
- Use Python 3.11+ syntax
- Include type hints
- Add docstrings for all functions
- Only use standard library imports unless explicitly requested
- All loops must have clear termination conditions

**Task:** {task}

**Constraints:**
- Maximum function length: 50 lines
- Must include error handling for edge cases

**Output format:** Python code only, no explanations
```

**Bad:**
```python
# Inline prompt string, no versioning
prompt = """
Write Python code for this task: {task}
Make it good.
"""
# No version history, no documentation, no constraints
```

**Why It Matters:** Version-controlled prompts with clear documentation enable tracking what changed, why, and when. Inline strings with no history make debugging impossible when prompts stop working.

### Example 2: Prompt Testing Suite

**Good:**
```python
class TestCodeGenerationPrompt:
    """Comprehensive tests for code generation prompt"""

    def test_generates_valid_python_syntax(self):
        """Output should be syntactically valid Python"""
        prompt = load_prompt("code_generation", "v2.3")
        output = generate(prompt, task="create a fibonacci function")

        # Verify it's valid Python
        try:
            compile(output, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated invalid Python syntax: {e}")

    def test_includes_type_hints(self):
        """Output should include type hints as specified"""
        prompt = load_prompt("code_generation", "v2.3")
        output = generate(prompt, task="create a function to sum numbers")

        assert "->" in output  # Return type annotation
        assert ":" in output and "def" in output  # Parameter annotations

    def test_includes_docstrings(self):
        """Output should include docstrings"""
        prompt = load_prompt("code_generation", "v2.3")
        output = generate(prompt, task="create a sorting function")

        assert '"""' in output or "'''" in output

    def test_handles_edge_case_empty_input(self):
        """Prompt should handle edge case of empty/minimal input"""
        prompt = load_prompt("code_generation", "v2.3")
        output = generate(prompt, task="")

        # Should return error message or minimal valid code, not crash
        assert output is not None
        assert len(output) > 0

    def test_constrains_to_standard_library(self):
        """Should not hallucinate non-existent imports"""
        prompt = load_prompt("code_generation", "v2.3")
        output = generate(prompt, task="parse JSON data")

        # Should use standard 'json', not imaginary libraries
        imports = extract_imports(output)
        for imp in imports:
            assert imp in STANDARD_LIBRARY or "json" in imp.lower()

    def test_performance_within_bounds(self):
        """Generation should complete within reasonable time"""
        prompt = load_prompt("code_generation", "v2.3")

        start = time.time()
        output = generate(prompt, task="create a simple function")
        duration = time.time() - start

        assert duration < 10  # Should complete in < 10 seconds
```

**Bad:**
```python
# No tests - just cross fingers and hope
def test_prompt():
    output = generate("Write code for X")
    assert output  # Only checks non-empty output
```

**Why It Matters:** Comprehensive tests catch regressions, validate requirements, and ensure consistent quality. Without tests, prompt changes are risky and unpredictable.

### Example 3: Regression Test for Known Issue

**Good:**
```python
def test_regression_issue_789_no_infinite_loops():
    """
    Regression test for Issue #789 (2025-09-15)

    Problem: Code generation prompt produced code with infinite loops
    when asked to "process all items" or similar open-ended tasks.

    Root cause: Prompt didn't explicitly require loop termination conditions.

    Fix: Added requirement in v2.3 that all loops must have clear
    termination conditions.

    Test input: Task descriptions that previously triggered infinite loops.
    Expected: Generated code includes proper loop termination.
    """
    prompt = load_prompt("code_generation", "v2.3")

    # Test cases that previously caused infinite loops
    test_cases = [
        "process all items in a list",
        "read from a stream until done",
        "handle incoming requests"
    ]

    for task in test_cases:
        output = generate(prompt, task=task)

        # Check for proper loop termination
        if "while" in output.lower():
            # While loops must have break or clear condition
            assert "break" in output or "while " in output
        if "for" in output.lower():
            # For loops should iterate over finite collections
            assert "in " in output or "range(" in output

        # Verify no suspicious infinite loop patterns
        assert "while True:" not in output or "break" in output
        assert "while 1:" not in output
```

**Bad:**
```python
# Issue fixed but no test added
# Next prompt refactoring reintroduces the bug
```

**Why It Matters:** Regression tests are insurance against reintroducing known bugs. Without them, the same issues recur, especially when prompts are refactored or models are updated.

### Example 4: A/B Testing Prompt Variants

**Good:**
```python
def test_compare_prompt_versions():
    """
    Compare v2.3 vs v2.4 to decide which to deploy

    v2.4 hypothesis: Adding examples improves output quality
    """
    prompt_v23 = load_prompt("code_generation", "v2.3")
    prompt_v24 = load_prompt("code_generation", "v2.4")  # Includes examples

    # Test on diverse, real-world tasks
    test_tasks = [
        "create a function to validate email addresses",
        "implement a binary search algorithm",
        "parse command-line arguments",
        "handle file I/O with error handling",
        "create a class for user authentication",
    ]

    results_v23 = []
    results_v24 = []

    for task in test_tasks:
        output_v23 = generate(prompt_v23, task=task)
        output_v24 = generate(prompt_v24, task=task)

        # Score each output on multiple dimensions
        score_v23 = {
            "syntax_valid": is_valid_python(output_v23),
            "has_type_hints": has_type_hints(output_v23),
            "has_docstring": has_docstring(output_v23),
            "handles_errors": has_error_handling(output_v23),
            "code_quality": analyze_code_quality(output_v23),
        }
        score_v24 = {
            "syntax_valid": is_valid_python(output_v24),
            "has_type_hints": has_type_hints(output_v24),
            "has_docstring": has_docstring(output_v24),
            "handles_errors": has_error_handling(output_v24),
            "code_quality": analyze_code_quality(output_v24),
        }

        results_v23.append(score_v23)
        results_v24.append(score_v24)

    # Statistical comparison
    avg_v23 = calculate_average_score(results_v23)
    avg_v24 = calculate_average_score(results_v24)

    print(f"v2.3 average score: {avg_v23:.2f}")
    print(f"v2.4 average score: {avg_v24:.2f}")
    print(f"Improvement: {((avg_v24 - avg_v23) / avg_v23 * 100):.1f}%")

    # Statistical significance
    p_value = ttest_rel(
        [sum(s.values()) for s in results_v23],
        [sum(s.values()) for s in results_v24]
    ).pvalue

    print(f"Statistical significance: p={p_value:.4f}")

    # Decision rule: deploy v2.4 if significantly better (p < 0.05)
    if p_value < 0.05 and avg_v24 > avg_v23:
        print("✓ Deploy v2.4 (statistically significant improvement)")
    else:
        print("✗ Stay with v2.3 (no significant improvement)")
```

**Bad:**
```python
# Just try the new prompt and "see if it feels better"
prompt_new = "Write code for: {task}"
output = generate(prompt_new, task="some task")
print(output)  # Looks good? Ship it!
```

**Why It Matters:** Objective A/B testing provides data-driven evidence about which prompts work better. Subjective "feels better" decisions lead to inconsistent quality and gradual prompt degradation.

### Example 5: Prompt Library with Validation

**Good:**
```python
class PromptLibrary:
    """Centralized, tested, versioned prompt library"""

    # Version registry with validation
    PROMPT_VERSIONS = {
        "code_generation": {
            "v2.3": "prompts/v2.3/code_generation.md",
            "v2.4": "prompts/v2.4/code_generation.md",
            "latest": "v2.4"
        },
        "code_review": {
            "v1.2": "prompts/v1.2/code_review.md",
            "latest": "v1.2"
        }
    }

    @staticmethod
    def get_prompt(
        prompt_id: str,
        version: str = "latest",
        validate: bool = True
    ) -> str:
        """
        Get validated prompt template

        Args:
            prompt_id: Identifier for prompt type
            version: Version to use (default: latest)
            validate: Whether to run validation (default: True)

        Returns:
            Prompt template string

        Raises:
            ValueError: If prompt_id or version doesn't exist
            ValidationError: If prompt fails validation checks
        """
        # Validate prompt exists
        if prompt_id not in PromptLibrary.PROMPT_VERSIONS:
            raise ValueError(f"Unknown prompt: {prompt_id}")

        versions = PromptLibrary.PROMPT_VERSIONS[prompt_id]
        if version == "latest":
            version = versions["latest"]

        if version not in versions:
            raise ValueError(f"Version {version} not found for {prompt_id}")

        # Load prompt
        path = versions[version]
        prompt = load_file(path)

        # Optional validation
        if validate:
            PromptLibrary._validate_prompt(prompt, prompt_id, version)

        return prompt

    @staticmethod
    def _validate_prompt(prompt: str, prompt_id: str, version: str):
        """Validate prompt meets quality standards"""
        # Check minimum length
        if len(prompt) < 50:
            raise ValidationError(f"{prompt_id} v{version} too short")

        # Check for required sections
        if "## Requirements" not in prompt and "## Constraints" not in prompt:
            raise ValidationError(
                f"{prompt_id} v{version} missing requirements or constraints"
            )

        # Check for template variables
        if "{" not in prompt:
            logger.warning(
                f"{prompt_id} v{version} has no template variables"
            )

    @staticmethod
    def format_prompt(prompt_id: str, version: str = "latest", **kwargs) -> str:
        """
        Get prompt and fill template variables

        Args:
            prompt_id: Identifier for prompt type
            version: Version to use (default: latest)
            **kwargs: Variables to fill in template

        Returns:
            Formatted prompt with variables filled
        """
        template = PromptLibrary.get_prompt(prompt_id, version)

        # Validate all template variables are provided
        required_vars = extract_template_vars(template)
        missing = [v for v in required_vars if v not in kwargs]
        if missing:
            raise ValueError(f"Missing template variables: {missing}")

        return template.format(**kwargs)
```

**Bad:**
```python
# Scattered prompt strings throughout codebase
def generate_code(task):
    prompt = f"Write code for: {task}"  # Different everywhere
    return llm.generate(prompt)

def review_code(code):
    prompt = f"Review this code: {code}"  # No consistency
    return llm.generate(prompt)

# No validation, no versioning, no reuse
```

**Why It Matters:** Centralized prompt libraries ensure consistency, enable reuse, and provide a single place to improve prompts. Scattered strings lead to drift, duplication, and maintenance nightmares.

## Related Principles

- **[Principle #09 - Tests as the Quality Gate](09-tests-as-quality-gate.md)** - Just as code requires tests, prompts require validation. Tests serve as quality gates for both traditional code and prompt-generated code.

- **[Principle #15 - Git-Based Everything](15-output-validation-feedback.md)** - Prompt testing is output validation. This principle provides the feedback mechanisms that detect when prompts produce incorrect or unexpected results.

- **[Principle #03 - LLM as Reasoning Engine](../architecture/03-llm-as-reasoning-engine.md)** - Prompts are the instructions to the reasoning engine. Version-controlled, tested prompts ensure the reasoning engine receives clear, consistent instructions.

- **[Principle #13 - Parallel Exploration by Default](../architecture/13-prompt-libraries-infrastructure.md)** - This principle defines the infrastructure for storing prompts; version control and testing make that infrastructure reliable and maintainable.

- **[Principle #39 - Metrics and Evaluation Everywhere](../quality/39-deterministic-llm-patterns.md)** - Testing prompts identifies non-deterministic behaviors. Versioning allows rolling back to prompts that had better consistency.

- **[Principle #43 - Model Lifecycle Management](../quality/43-prompt-injection-defense.md)** - Prompt testing should include security tests for injection attacks. Version control tracks when security improvements were added to prompts.

## Common Pitfalls

1. **Treating Prompts as Throwaway Strings**: Hardcoding prompts inline throughout code without central management or versioning.
   - Example: `llm.generate(f"Create code for {task}")` scattered across 50 different files.
   - Impact: Impossible to track what prompts are being used, no ability to A/B test improvements, inconsistent results across the system.

2. **No Baseline Tests Before Changes**: Changing prompts without first establishing test coverage of current behavior.
   - Example: "This prompt seems verbose, let me simplify it" without testing if the simplification breaks existing functionality.
   - Impact: Regressions go unnoticed, quality degrades, no way to compare before/after objectively.

3. **Testing Only Happy Paths**: Prompt tests that only verify ideal inputs, ignoring edge cases and error conditions.
   - Example: Testing "create a simple function" but not "create a function with invalid inputs" or "create an empty function".
   - Impact: Prompts work fine in demos but fail in production with real, messy data.

4. **No Version History or Changelog**: Making changes without documenting what changed and why.
   - Example: Prompt file is modified in place with no git commit message or changelog entry.
   - Impact: When prompt quality degrades, impossible to identify which change caused the problem or how to fix it.

5. **Subjective Quality Assessment**: Relying on "this output looks better" instead of objective metrics.
   - Example: Developer reads two outputs, likes one more, and declares it better without measuring.
   - Impact: Personal preference replaces data, improvements aren't reproducible, quality becomes inconsistent.

6. **Testing with Tiny Sample Sizes**: Running prompt tests on 1-2 examples and assuming it's sufficient.
   - Example: "I tested the new prompt on one task and it worked, ship it!"
   - Impact: Doesn't catch inconsistency or failure modes that only appear with diverse inputs.

7. **No Regression Testing for Known Issues**: Fixing prompt-related bugs without adding tests to prevent recurrence.
   - Example: Bug #123 is fixed by modifying prompt, but no test is added to detect if it returns.
   - Impact: Same bugs reappear after future prompt changes, wasting time and eroding trust.

## Tools & Frameworks

### Version Control Systems
- **Git**: Standard version control for prompt files. Use branches for A/B testing, tags for production versions.
- **Git LFS**: For storing large prompt libraries or example datasets that accompany prompts.
- **DVC**: Data Version Control for tracking prompt datasets, test cases, and evaluation results alongside code.

### Testing Frameworks
- **pytest**: Python testing framework ideal for prompt testing. Supports fixtures, parameterized tests, and integration with CI/CD.
- **Jest**: JavaScript testing framework for prompt testing in Node.js environments.
- **unittest**: Python's built-in testing framework, sufficient for basic prompt test suites.

### LLM Evaluation Tools
- **LangSmith**: Platform for testing, evaluating, and monitoring LLM applications. Provides prompt versioning and A/B testing capabilities.
- **PromptTools**: Open-source library for testing and evaluating prompts across different models.
- **OpenAI Evals**: Framework for evaluating LLM outputs against expected behaviors.

### Prompt Management Platforms
- **Promptlayer**: Tracks prompt versions, monitors usage, and provides analytics on prompt performance.
- **Helicone**: Observability platform for LLM apps with prompt versioning and quality tracking.
- **Weights & Biases Prompts**: Experiment tracking for prompts with versioning and comparison tools.

### Statistical Analysis
- **scipy.stats**: Python library for statistical significance testing when comparing prompt versions.
- **numpy**: For calculating metrics and aggregating test results.
- **pandas**: For organizing and analyzing prompt test results across many examples.

### CI/CD Integration
- **GitHub Actions**: Automate prompt testing on every commit or PR.
- **GitLab CI**: Run prompt validation pipelines before merging changes.
- **Jenkins**: Enterprise CI/CD with support for complex prompt testing workflows.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All prompts are stored as files in version control, not hardcoded strings
- [ ] Each prompt file includes version history and changelog
- [ ] Prompt templates have clear documentation of variables and expected outputs
- [ ] Automated tests validate prompt outputs against expected patterns
- [ ] Regression tests exist for all previously discovered prompt-related bugs
- [ ] Test suite covers happy paths, edge cases, and error conditions
- [ ] A/B testing framework is in place for comparing prompt variants
- [ ] Objective quality metrics are defined and tracked over time
- [ ] Prompt library provides centralized, validated access to all prompts
- [ ] CI/CD pipeline runs prompt tests before allowing changes to merge
- [ ] Production monitoring tracks prompt performance and detects degradation
- [ ] Team has established process for requesting, reviewing, and approving prompt changes

## Metadata

**Category**: Process
**Principle Number**: 17
**Related Patterns**: Test-Driven Development (TDD), A/B Testing, Version Control, Regression Testing, Prompt Engineering
**Prerequisites**: Version control system, testing framework, basic understanding of statistical analysis
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0