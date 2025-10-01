# BEAST Framework

**Behavioral Execution and Actual System Testing**

BEAST is an AI-resistant testing framework that verifies actual behavior rather than claimed behavior. It traces real execution, validates actual outcomes, and cannot be fooled by mocked implementations or superficial test passes.

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Writing Custom Contracts](#writing-custom-contracts)
- [Available Contracts](#available-contracts)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

## Overview

### What is BEAST?

BEAST is a behavioral verification framework that ensures software components actually work as intended in real-world conditions. Unlike traditional unit tests that can be gamed or mocked, BEAST:

- **Traces actual execution paths** - Records what really happens, not what's claimed
- **Validates real outcomes** - Checks actual state changes and side effects
- **Resists gaming** - Can't be fooled by stub implementations or mock objects
- **Provides continuous validation** - Monitors system behavior over time
- **Enables mutation testing** - Verifies test effectiveness by introducing intentional bugs

### Why BEAST?

In an era of AI-assisted development, traditional testing approaches fall short:

1. **AI can generate passing tests for broken code** - Tests that appear to work but don't catch real issues
2. **Mocks hide real problems** - Mocked dependencies mask integration failures
3. **Coverage metrics lie** - High coverage doesn't mean actual behavior is tested
4. **Behavioral drift goes unnoticed** - Systems gradually degrade without detection

BEAST solves these problems by focusing on **actual runtime behavior** rather than test metrics.

## Core Concepts

### Behavioral Contracts

A behavioral contract defines expected real-world behavior through four phases:

1. **Setup** - Establish real test conditions (files, network, database)
2. **Execute** - Run actual operations with execution tracing
3. **Verify** - Check real outcomes and side effects
4. **Cleanup** - Restore system to clean state

### Execution Tracing

BEAST records detailed execution traces including:
- Function calls and returns
- File I/O operations
- Network requests
- State changes
- Error conditions
- Performance metrics

### AI-Resistant Testing

Tests that cannot be gamed by:
- Checking actual file contents, not just return values
- Verifying real network calls, not mocked responses
- Validating actual state changes in databases
- Measuring real performance, not synthetic benchmarks

## Installation

BEAST is integrated into the Amplifier framework:

```bash
# Install Amplifier with BEAST support
git clone https://github.com/yourusername/amplifier.git
cd amplifier
make install

# Verify installation
amplifier beast list
```

## Usage Guide

### Running All Contracts

Execute all behavioral contracts for comprehensive validation:

```bash
amplifier beast run
```

Output:
```
BEAST - ACTUAL BEHAVIOR VERIFICATION
====================================
Running 14 contracts...

✓ HealingActuallyHeals: Code quality improved (3.2s)
✓ MemoryActuallyPersists: Data survived restart (1.1s)
✓ CLICommandsWork: All commands executable (0.8s)
✓ NetworkContract: Real API calls succeeded (2.4s)
...

Results: 14/14 passed
Total time: 12.3s
```

### Running Specific Contracts

Test individual components or behaviors:

```bash
# Run a specific contract by name
amplifier beast run --contract HealingSystem

# Run with verbose output for debugging
amplifier beast run --contract NetworkContract --verbose

# Output results to JSON for CI/CD integration
amplifier beast run --output results.json
```

### Listing Available Contracts

See all contracts available for your project:

```bash
amplifier beast list
```

Output:
```
Available Behavioral Contracts:
================================
1. HealingActuallyHeals       - Verifies auto-healing improves code quality
2. MemoryActuallyPersists     - Ensures data survives process restarts
3. CLICommandsWork            - Tests all CLI commands execute properly
4. NetworkContract            - Validates real network operations
5. FileOperationContract      - Checks file I/O behavior
6. PerformanceContract        - Measures actual performance metrics
...
```

### Continuous Monitoring

Run contracts continuously to detect behavioral drift:

```bash
# Start continuous validation (checks every 5 minutes)
amplifier beast watch

# Custom interval (in seconds)
amplifier beast watch --interval 600

# Specify history database location
amplifier beast watch --db monitoring.db
```

The continuous validator:
- Runs contracts at specified intervals
- Records results in SQLite database
- Detects behavioral changes over time
- Alerts on contract failures
- Tracks performance trends

### Mutation Testing

Verify your contracts actually catch bugs:

```bash
# Run quick mutation test
amplifier beast mutate --quick

# Full mutation testing on source directory
amplifier beast mutate --source amplifier/
```

Mutation testing:
1. Introduces intentional bugs (mutations)
2. Runs contracts to see if they detect the bugs
3. Reports mutation score (% of mutations caught)
4. Identifies weak contracts that need improvement

## Writing Custom Contracts

### Basic Contract Structure

Create a new contract by extending `BehavioralContract`:

```python
from pathlib import Path
from amplifier.beast import BehavioralContract, ExecutionTrace

class DatabasePersistenceContract(BehavioralContract):
    """Verify that database changes actually persist."""

    def __init__(self):
        super().__init__("DatabasePersistence")

    def setup(self) -> dict:
        """Create test database and initial data."""
        db_path = Path("/tmp/test.db")

        # Create actual database
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO users (name) VALUES ('Alice')")
        conn.commit()
        conn.close()

        return {"db_path": db_path, "initial_count": 1}

    def execute(self, context: dict) -> ExecutionTrace:
        """Perform database operations with tracing."""
        trace = self.tracer.start_trace()

        # Record actual operations
        with self.tracer.track_operation("database_write"):
            import sqlite3
            conn = sqlite3.connect(context["db_path"])
            conn.execute("INSERT INTO users (name) VALUES ('Bob')")
            conn.commit()
            conn.close()

        # Simulate process restart
        with self.tracer.track_operation("process_restart"):
            # In real contract, might actually restart process
            pass

        # Check persistence
        with self.tracer.track_operation("verify_persistence"):
            conn = sqlite3.connect(context["db_path"])
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
            trace.add_measurement("final_count", count)

        return trace

    def verify(self, trace: ExecutionTrace, context: dict) -> bool:
        """Verify data actually persisted."""
        # Check execution completed
        if not trace.has_operation("database_write"):
            print("✗ Database write never occurred")
            return False

        # Verify actual persistence
        final_count = trace.get_measurement("final_count")
        expected_count = context["initial_count"] + 1

        if final_count != expected_count:
            print(f"✗ Data not persisted: expected {expected_count}, got {final_count}")
            return False

        # Verify actual file exists and has content
        if not context["db_path"].exists():
            print("✗ Database file doesn't exist")
            return False

        if context["db_path"].stat().st_size == 0:
            print("✗ Database file is empty")
            return False

        print("✓ Database changes persisted correctly")
        return True

    def cleanup(self, context: dict):
        """Remove test database."""
        if context["db_path"].exists():
            context["db_path"].unlink()
```

### Registering Custom Contracts

Add your contracts to the project's contract loader:

```python
# beast_contracts.py in your project root
from my_contracts import DatabasePersistenceContract
from my_contracts import CachingContract
from my_contracts import AuthenticationContract

def create_contracts():
    """Create project-specific behavioral contracts."""
    return [
        DatabasePersistenceContract(),
        CachingContract(),
        AuthenticationContract(),
    ]
```

## Available Contracts

BEAST includes 14+ built-in contracts for common behaviors:

### Core System Contracts

1. **HealingActuallyHealsContract** - Verifies that auto-healing systems improve code quality
2. **MemoryActuallyPersistsContract** - Ensures data survives process restarts
3. **CLICommandsActuallyWorkContract** - Tests all CLI commands execute properly
4. **KnowledgeSynthesisProducesOutputContract** - Validates knowledge synthesis generates real output

### Infrastructure Contracts

5. **CommandExistsContract** - Verifies required system commands are available
6. **FileOperationContract** - Tests file I/O operations work correctly
7. **NetworkContract** - Validates network operations and API calls
8. **PerformanceContract** - Measures actual performance against thresholds

### Quality Contracts

9. **ConfigurationActuallyWorksContract** - Ensures configuration loading and validation
10. **ErrorRecoveryActuallyWorksContract** - Tests error handling and recovery mechanisms
11. **ConcurrencyActuallyWorksContract** - Validates thread-safe operations
12. **DataValidationActuallyWorksContract** - Checks input validation and sanitization

### Advanced Contracts

13. **CachingActuallyWorksContract** - Verifies cache behavior and invalidation
14. **BadDirectoryContract** (Demo) - Example of failure handling
15. **SlowOperationContract** (Demo) - Example of performance testing

## Architecture

### Component Overview

```
BEAST Framework
├── Behavioral Contracts     # Define expected behavior
│   ├── Setup Phase          # Establish real conditions
│   ├── Execute Phase        # Run with tracing
│   ├── Verify Phase         # Check actual outcomes
│   └── Cleanup Phase        # Restore clean state
│
├── Execution Tracer         # Record actual execution
│   ├── Function Calls       # Track call graphs
│   ├── I/O Operations       # Monitor file/network
│   ├── State Changes        # Capture modifications
│   └── Performance Metrics  # Measure timing/resources
│
├── Contract Verifier        # Run and validate contracts
│   ├── Sequential Execution # Run contracts in order
│   ├── Result Aggregation   # Collect outcomes
│   └── Report Generation    # Format results
│
├── Continuous Validator     # Monitor over time
│   ├── Scheduled Execution  # Run periodically
│   ├── History Tracking     # Store in database
│   └── Drift Detection      # Identify changes
│
└── Mutation Testing         # Verify test effectiveness
    ├── Code Mutation        # Introduce bugs
    ├── Contract Execution   # Run against mutants
    └── Score Calculation    # Measure detection rate
```

### Execution Flow

1. **Contract Loading** - Discover and instantiate contracts
2. **Setup Phase** - Each contract prepares its environment
3. **Traced Execution** - Operations run with full tracing
4. **Verification** - Actual outcomes checked against expectations
5. **Cleanup** - Environment restored to clean state
6. **Reporting** - Results aggregated and formatted

## API Reference

### Core Classes

#### BehavioralContract

Base class for all behavioral contracts:

```python
class BehavioralContract(ABC):
    def __init__(self, name: str)

    @abstractmethod
    def setup(self) -> dict[str, Any]
        """Prepare test environment, return context."""

    @abstractmethod
    def execute(self, context: dict) -> ExecutionTrace
        """Run operations with tracing."""

    @abstractmethod
    def verify(self, trace: ExecutionTrace, context: dict) -> bool
        """Verify actual behavior matches expectations."""

    @abstractmethod
    def cleanup(self, context: dict)
        """Clean up test environment."""
```

#### ExecutionTracer

Records detailed execution information:

```python
class ExecutionTracer:
    def start_trace(self) -> ExecutionTrace
        """Begin recording execution."""

    def track_operation(self, name: str) -> ContextManager
        """Track a named operation."""

    def track_function(self, func: Callable) -> Callable
        """Decorator to trace function calls."""
```

#### ExecutionTrace

Contains recorded execution data:

```python
class ExecutionTrace:
    def add_measurement(self, key: str, value: Any)
        """Record a measurement."""

    def has_operation(self, name: str) -> bool
        """Check if operation was executed."""

    def get_measurement(self, key: str) -> Any
        """Retrieve recorded measurement."""

    def get_duration(self, operation: str) -> float
        """Get operation duration in seconds."""
```

#### ContractVerifier

Runs and validates contracts:

```python
class ContractVerifier:
    def add_contract(self, contract: BehavioralContract)
        """Register a contract."""

    def verify_all(self, verbose: bool = False) -> dict[str, Any]
        """Run all contracts and return results."""

    def verify_contract(self, contract: BehavioralContract) -> dict
        """Run a single contract."""
```

## Best Practices

### Writing Effective Contracts

1. **Test Real Behavior**
   - Use actual files, not temp strings
   - Make real network calls, not mocked responses
   - Interact with real databases, not in-memory substitutes

2. **Verify Side Effects**
   - Check files were actually created/modified
   - Verify database state changes
   - Confirm network requests were sent
   - Validate logs were written

3. **Clean Up Properly**
   - Always restore original state
   - Remove test files and directories
   - Close connections and handles
   - Use try/finally for guaranteed cleanup

4. **Measure Real Performance**
   - Time actual operations, not synthetic loops
   - Check resource usage (memory, CPU, I/O)
   - Validate against realistic thresholds
   - Consider system load and variability

5. **Handle Failures Gracefully**
   - Expect and handle real-world errors
   - Test recovery mechanisms
   - Verify error messages and logging
   - Check partial success scenarios

### Contract Design Patterns

#### The State Validator Pattern
```python
def verify(self, trace, context):
    # Check initial state
    initial = context["initial_state"]

    # Verify transformation occurred
    if not trace.has_operation("transform"):
        return False

    # Check final state
    final = self.get_actual_state()
    return final == expected_from(initial)
```

#### The Side Effect Checker Pattern
```python
def execute(self, context):
    trace = self.tracer.start_trace()

    # Perform operation
    result = do_something()

    # Check all side effects
    trace.add_measurement("file_exists", Path("output.txt").exists())
    trace.add_measurement("log_written", check_log_entry())
    trace.add_measurement("db_updated", query_database())

    return trace
```

#### The Performance Guardian Pattern
```python
def verify(self, trace, context):
    duration = trace.get_duration("critical_operation")

    # Absolute threshold
    if duration > 1.0:  # seconds
        return False

    # Relative threshold (vs baseline)
    baseline = context.get("baseline_duration", 0.5)
    if duration > baseline * 1.5:  # 50% regression
        return False

    return True
```

### Integration Tips

1. **CI/CD Integration**
   ```yaml
   # .github/workflows/beast.yml
   - name: Run BEAST Contracts
     run: |
       amplifier beast run --output results.json
       amplifier beast mutate --quick
   ```

2. **Pre-commit Hooks**
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash
   amplifier beast run --contract critical
   ```

3. **Monitoring Integration**
   ```python
   # monitoring.py
   from amplifier.beast import ContinuousValidator

   validator = ContinuousValidator()
   validator.add_alert_handler(send_to_datadog)
   validator.start(interval=300)
   ```

## Contributing

To contribute new contracts or improvements:

1. Create contracts that test real behavior
2. Ensure contracts are deterministic and reliable
3. Include cleanup in all contracts
4. Document contract purpose and requirements
5. Add tests for the contract itself

## License

BEAST is part of the Amplifier project and shares its license.

---

*"In the jungle of code, BEAST hunts for truth."*