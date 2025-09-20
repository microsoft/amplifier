# Recipe Module Implementation Specification

## Overview

Create a standardized recipe module framework for the amplifier microtasks system that follows the modular design philosophy, embraces simplicity, and provides robust file I/O handling with cloud sync resilience.

## Module: amplifier/microtasks/recipes/base.py

### Purpose
Provide a base Recipe class and common utilities for all recipe implementations

### Location
`amplifier/microtasks/recipes/base.py`

### Contract

#### Inputs
- Recipe name and configuration
- List of processing steps
- Source data paths/files
- Processing options (limit, resume, timeout)

#### Outputs
- RunSummary with success/failure status
- Processed results in JSON format
- Progress tracking and resume capability
- Error handling with detailed reporting

#### Side Effects
- Creates .data/microtasks/{job-id}/ directories
- Writes incremental results to results.json
- Writes artifacts to artifacts directory
- May show progress output to console

### Dependencies
- amplifier.microtasks.orchestrator.MicrotaskOrchestrator
- amplifier.microtasks.llm.LLM
- amplifier.microtasks.models (JobState, RunSummary, MicrotaskError)
- amplifier.utils.file_io (retry-enabled I/O functions)
- Python standard library: pathlib, json, time, typing

### Key Classes and Functions

#### BaseRecipe (Abstract Base Class)
```python
class BaseRecipe:
    def __init__(self, name: str, description: str)
    def run(self, **kwargs) -> RunSummary
    def process_items(self, items: list, processor: callable) -> dict
    def save_incremental(self, results: dict, output_file: Path)
    def load_previous_results(self, output_file: Path) -> dict
    def handle_cloud_sync_errors(self, operation: callable, max_retries: int = 3)
```

#### RecipeStep (Data Class)
```python
@dataclass
class RecipeStep:
    name: str
    function: Callable[[LLM, Path], dict[str, Any]]
    required: bool = True
    timeout_s: int = 120
```

#### ProcessingResult (Data Class)
```python
@dataclass
class ProcessingResult:
    item_id: str
    status: Literal["success", "error", "skipped", "timeout"]
    result: dict[str, Any] | None
    error: str | None
    processing_time: float
```

## Module: amplifier/microtasks/recipes/registry.py

### Purpose
Maintain a registry of available recipes and provide discovery/loading mechanisms

### Location
`amplifier/microtasks/recipes/registry.py`

### Contract

#### Key Functions
```python
def register_recipe(recipe_class: type[BaseRecipe]) -> None
def get_recipe(name: str) -> BaseRecipe
def list_recipes() -> list[dict[str, str]]
def load_recipe_module(module_path: str) -> None
```

## Implementation Requirements

### Error Handling Strategy

1. **File I/O Resilience**
   - Use amplifier.utils.file_io functions for all file operations
   - Implement retry logic with exponential backoff
   - Handle OSError errno 5 (cloud sync issues)
   - Provide informative warnings about cloud sync interference

2. **Processing Failures**
   - Continue processing on individual item failures
   - Save partial results immediately after each item
   - Track failed items for selective retry
   - Distinguish between "no data" and "processing failed"

3. **Timeout Handling**
   - Use 120-second timeout for Claude Code SDK operations
   - Implement asyncio.timeout for async operations
   - Return partial results on timeout
   - Allow resume from last successful item

### Progress Tracking

1. **Incremental Saves**
   - Save after EVERY item processed
   - Use fixed filename (results.json) that overwrites
   - Support interruption at any point
   - Enable resume from existing results

2. **Status Reporting**
   - Show current item being processed (e.g., "[3/10] Processing file.md")
   - Report success/error/skip counts at completion
   - Log retry attempts for I/O operations
   - Provide clear error messages with actionable fixes

### Resume Capability

1. **State Persistence**
   - Track processed items by unique ID
   - Skip already-processed items on resume
   - Load existing results at startup
   - Merge new results with existing

2. **Idempotency**
   - Ensure re-running doesn't duplicate results
   - Use deterministic item IDs (e.g., file path or stem)
   - Support selective re-processing of failed items

## Design Patterns to Follow

### From DISCOVERIES.md

1. **Avoid triple-quoted templates for code generation**
   - Build code line-by-line and join with "\n"
   - Use sentinel tokens and str.replace for substitutions
   - Embed JSON via json.loads() to avoid type mismatches

2. **Handle cloud sync file I/O issues**
   - Implement retry with exponential backoff
   - Show warning on first retry about cloud sync
   - Use atomic file operations (write to .tmp, then rename)

3. **Distinguish failure types**
   - "Empty results" vs "extraction failed"
   - "Timeout" vs "error" vs "no data found"
   - Save status with each result for selective retry

### From IMPLEMENTATION_PHILOSOPHY.md

1. **Ruthless Simplicity**
   - Minimal abstractions - only what's necessary
   - Direct integration with libraries
   - Start minimal, grow as needed
   - No future-proofing for hypothetical cases

2. **Vertical Slices**
   - Implement complete end-to-end functionality
   - Get data flowing through all layers early
   - One working feature > multiple partial features

3. **Error Handling**
   - Handle common errors robustly
   - Log detailed information for debugging
   - Provide clear error messages to users
   - Fail fast and visibly during development

### From MODULAR_DESIGN_PHILOSOPHY.md

1. **Think "bricks & studs"**
   - Self-contained directory with clear responsibility
   - Public contract via __all__ or interface
   - Keep specs small enough for one prompt
   - Design for regeneration, not patching

2. **Clear Contracts**
   - Define inputs, outputs, side effects
   - Specify dependencies explicitly
   - Document key functions and their signatures
   - Maintain stable interfaces between modules

## Example Recipe Implementation Pattern

```python
from amplifier.microtasks.recipes.base import BaseRecipe, ProcessingResult
from amplifier.utils.file_io import write_json, read_json

class ExampleRecipe(BaseRecipe):
    """Process items with resume capability and robust I/O."""

    def __init__(self):
        super().__init__(
            name="example",
            description="Example recipe with all best practices"
        )

    def run(self, source_path: str, limit: int = 10, resume: bool = True, **kwargs):
        # Setup
        results_file = Path("results.json")
        existing = self.load_previous_results(results_file) if resume else {}

        # Discovery
        items = self.discover_items(source_path)
        items_to_process = self.filter_unprocessed(items, existing)[:limit]

        # Process with incremental saves
        for i, item in enumerate(items_to_process):
            print(f"[{i+1}/{len(items_to_process)}] Processing {item.name}")

            result = self.process_single_item(item)
            existing[item.id] = result

            # Save immediately with retry logic
            self.save_incremental(existing, results_file)

        # Report summary
        self.report_summary(existing)

        return self.create_run_summary(existing)
```

## Test Requirements

1. **Unit Tests**
   - Test retry logic for file I/O operations
   - Test resume capability with partial results
   - Test error handling for various failure modes
   - Test progress tracking and reporting

2. **Integration Tests**
   - Test full recipe execution with real files
   - Test interruption and resume scenarios
   - Test cloud sync error simulation
   - Test timeout handling for SDK operations

3. **Edge Cases**
   - Empty input files/directories
   - Corrupted results.json file
   - Missing dependencies (SDK not available)
   - Concurrent recipe execution

## Success Criteria

1. Recipe module can process 100+ items without failure
2. Supports interruption and resume at any point
3. Handles cloud sync I/O errors gracefully
4. Provides clear progress tracking and error reporting
5. Follows all project design philosophies
6. Code is simple, clear, and maintainable
7. All tests pass with >80% coverage
8. Can be easily extended for new recipe types

## Notes for Implementation

- Keep the base class minimal - only common functionality
- Each recipe should be self-contained in its own file
- Use type hints throughout for clarity
- Follow existing code style from the project
- Ensure all file paths are absolute, not relative
- Test with both Claude Code SDK available and unavailable
- Consider async patterns where beneficial but keep sync where simpler