# Super-Planner Test Suite

This directory contains comprehensive golden test specifications for the super-planner system, following the "spec and test forward" approach. Tests are designed to validate the system before implementation begins.

## Test Architecture

### Test Organization

```
tests/planner/
├── README.md                    # This file
├── conftest.py                  # Shared fixtures and configuration
├── test_data/                   # Golden test data and sample projects
│   ├── projects/                # Sample project configurations
│   ├── failure_scenarios/       # Failure and edge case data
│   └── performance/             # Large-scale test data
├── unit/                        # Unit tests for individual components
│   ├── test_state_transitions.py
│   ├── test_agent_coordination.py
│   ├── test_deadlock_prevention.py
│   ├── test_conflict_resolution.py
│   └── test_defensive_coordination.py
├── integration/                 # Multi-component integration tests
│   ├── test_planning_workflow.py
│   ├── test_working_workflow.py
│   ├── test_multi_agent_coordination.py
│   └── test_git_integration.py
├── e2e/                        # End-to-end workflow tests
│   ├── test_complete_planning_cycle.py
│   ├── test_agent_spawning_workflow.py
│   └── test_cross_mode_switching.py
├── performance/                # Performance and scale tests
│   ├── test_large_projects.py
│   ├── test_concurrent_agents.py
│   └── test_file_io_performance.py
├── mocks/                      # Mock implementations
│   ├── mock_amplifier_task.py
│   ├── mock_git_operations.py
│   └── mock_llm_services.py
└── utils/                      # Test utilities and helpers
    ├── test_builders.py
    ├── verification.py
    └── assertions.py
```

### Test Categories

1. **Unit Tests (60%)**
   - Test individual protocol components in isolation
   - Fast execution (<100ms per test)
   - High coverage of edge cases and error conditions
   - Mock external dependencies

2. **Integration Tests (30%)**
   - Test component interactions within the planner system
   - Medium execution time (<5s per test)
   - Focus on protocol coordination and data flow
   - Use lightweight mocks for external services

3. **End-to-End Tests (10%)**
   - Test complete workflows from start to finish
   - Slower execution (up to 30s per test)
   - Test with real or near-real external dependencies
   - Critical user journeys only

## Test Philosophy

### Ruthless Simplicity in Testing

Following amplifier's implementation philosophy:

- **Simple test data**: Real-world scenarios without unnecessary complexity
- **Clear assertions**: Focus on behavior, not implementation details
- **Minimal mocking**: Mock only what's necessary, prefer fakes when possible
- **Self-contained tests**: Each test creates its own data and cleans up
- **Predictable outcomes**: Deterministic tests that always produce same results

### Spec-Forward Testing

- **Test specifications define the API**: Tests document expected behavior
- **Implementation follows tests**: Code is written to make tests pass
- **Golden test data**: Canonical examples of inputs and expected outputs
- **Behavior verification**: Focus on what the system does, not how it does it

## Test Data Strategy

### Sample Projects

1. **Simple Project** (`simple_web_app`)
   - 8 tasks across 3 components (frontend, backend, deployment)
   - 2 levels deep (feature → implementation tasks)
   - Linear dependencies with one parallel branch
   - Single team/agent capabilities required

2. **Complex Project** (`microservices_platform`)
   - 150+ tasks across 8 microservices
   - 5+ levels deep (epic → feature → story → implementation → testing)
   - Complex dependency web with cross-service dependencies
   - Multiple agent capabilities required (python, typescript, devops, qa)

3. **Multi-Team Project** (`enterprise_integration`)
   - 300+ tasks across 12 teams
   - Concurrent agent scenarios (up to 8 agents)
   - Resource contention and scheduling challenges
   - Git coordination across multiple branches/worktrees

### Failure Scenarios

- **Network Partitions**: Agent coordination failures during distributed work
- **File I/O Errors**: Cloud sync delays, permission issues, disk full
- **Git Conflicts**: Concurrent modifications, merge conflicts, branch issues
- **Agent Crashes**: Mid-task failures, recovery scenarios, state restoration
- **Circular Dependencies**: Complex dependency cycles, resolution strategies
- **Resource Exhaustion**: Too many concurrent agents, memory limits, timeout conditions

### Edge Cases

- **Empty Projects**: No tasks, minimal configuration
- **Single Task Projects**: Edge of recursion, minimal complexity
- **Deep Hierarchies**: 10+ levels of task breakdown
- **Wide Hierarchies**: 100+ sibling tasks at one level
- **Orphaned Tasks**: Tasks without parents due to failures
- **Malformed Data**: Corrupted task files, invalid JSON, missing fields

## Test Execution Strategy

### Automated Testing

```bash
# Run all tests
make test-planner

# Run by category
make test-planner-unit
make test-planner-integration
make test-planner-e2e

# Run performance tests
make test-planner-performance

# Run with coverage
make test-planner-coverage
```

### Manual Validation

- **Visual Inspection**: Task breakdown trees, dependency graphs
- **Interactive Testing**: CLI commands with real user input
- **Stress Testing**: Large projects with resource monitoring
- **User Acceptance**: Real project scenarios with feedback

## Success Criteria

### Functional Requirements

- ✅ Planning mode successfully breaks down complex projects
- ✅ Working mode assigns and tracks task execution
- ✅ Multi-agent coordination handles concurrent work
- ✅ State transitions maintain data integrity
- ✅ Deadlock prevention detects and resolves cycles
- ✅ Conflict resolution handles concurrent modifications
- ✅ Git integration provides version control and collaboration
- ✅ Recovery mechanisms handle various failure conditions

### Performance Requirements

- **Planning Mode**: Break down 1000-task project in <60s
- **Working Mode**: Assign 100 tasks to 8 agents in <30s
- **State Transitions**: Process 1000 state changes in <10s
- **File I/O**: Handle 100 concurrent file operations without corruption
- **Git Operations**: Commit task changes with <5s latency
- **Memory Usage**: Support 10,000 tasks in <1GB memory
- **Concurrent Agents**: Support 20 concurrent agents without deadlock

### Quality Requirements

- **Reliability**: 99.9% success rate on valid inputs
- **Data Integrity**: Zero data corruption under concurrent access
- **Error Recovery**: Graceful degradation from all failure modes
- **User Experience**: Clear error messages, visible progress, predictable behavior

## Test Implementation Guidelines

### Writing Tests

```python
# Good: Behavior-focused test
def test_task_assignment_balances_load_across_agents():
    """Test that tasks are distributed evenly across available agents"""
    # Arrange
    project = create_project_with_tasks(task_count=100)
    agents = create_agents(count=4, capabilities=["python"])

    # Act
    assignments = assign_tasks_to_agents(project, agents)

    # Assert
    assert_load_balanced(assignments, tolerance=0.1)
    assert_all_tasks_assigned(assignments, project.tasks)

# Bad: Implementation-focused test
def test_assignment_engine_uses_round_robin_algorithm():
    """Test internal algorithm implementation"""
    # This tests HOW instead of WHAT - avoid this approach
```

### Test Data Creation

```python
# Use builders for consistent test data
project = ProjectBuilder() \
    .with_name("test_project") \
    .with_tasks(8) \
    .with_max_depth(3) \
    .with_dependencies("linear") \
    .build()

# Use golden test data for complex scenarios
project = load_test_project("complex_microservices_platform")
```

### Verification Patterns

```python
# State verification
assert_task_state(task, TaskState.IN_PROGRESS)
assert_dependencies_satisfied(task)

# Behavior verification
assert_file_contents_match(expected_tasks, actual_file)
assert_git_commit_created(commit_message_pattern)

# Performance verification
with assert_completes_within(seconds=30):
    result = break_down_project(large_project)
```

This test suite ensures the super-planner system meets all requirements before implementation begins, following amplifier's philosophy of simplicity, reliability, and user-focused design.