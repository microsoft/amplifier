# Super-Planner Golden Test Specification

**Complete "spec and test forward" specification for the super-planner system**

This document provides a comprehensive testing strategy that validates the super-planner system works correctly before implementation begins, following amplifier's philosophy of ruthless simplicity and modular design.

## Executive Summary

The super-planner test suite ensures:
- ✅ **Functional Correctness**: All workflows operate as specified
- ✅ **Data Integrity**: No corruption under any circumstances
- ✅ **Performance Requirements**: Meets enterprise-scale demands
- ✅ **Integration Quality**: Seamless amplifier ecosystem integration
- ✅ **Reliability Standards**: 99.9% success rate on valid operations

## Test Architecture Overview

### Test Organization (Following Amplifier Philosophy)

```
tests/planner/
├── README.md                    # Test suite overview and philosophy
├── conftest.py                  # Shared fixtures and utilities
├── test_data/                   # Golden test data (canonical examples)
├── unit/                        # 60% - Fast, isolated component tests
├── integration/                 # 30% - Multi-component interaction tests
├── e2e/                        # 10% - Complete workflow validation
├── performance/                # Scale and throughput validation
├── mocks/                      # External dependency mocks
└── utils/                      # Test builders and verification tools
```

### Testing Pyramid Distribution

- **Unit Tests (60%)**: Individual protocol components, <100ms each
- **Integration Tests (30%)**: Component coordination, <5s each
- **End-to-End Tests (10%)**: Critical user journeys, <30s each

## Golden Test Data

### Core Test Projects

**Simple Web App** (`simple_web_app.json`)
- 8 tasks across 3 components (frontend, backend, deployment)
- 2 levels deep with linear dependencies
- Single team capabilities
- **Purpose**: Validate basic planning and working mode functionality

**Complex Microservices Platform** (`complex_microservices_platform.json`)
- 22 tasks across 8 services
- 2 levels deep with cross-service dependencies
- Multiple agent capabilities (python, typescript, devops, security)
- **Purpose**: Validate multi-agent coordination and complex dependencies

**Enterprise Integration** (Generated)
- 1000+ tasks across 12 teams
- 5+ levels deep with complex dependency webs
- Resource contention scenarios
- **Purpose**: Performance and scale validation

### Failure Scenarios

- **Network Partitions**: Agent coordination failures
- **File I/O Errors**: Cloud sync delays, permission issues
- **Git Conflicts**: Concurrent modifications, merge failures
- **Agent Crashes**: Mid-task failures, recovery scenarios
- **Circular Dependencies**: Complex cycles requiring resolution
- **Resource Exhaustion**: Memory limits, timeout conditions

## Test Scenarios with Success Criteria

### End-to-End Workflows

**E2E-001: Complete Planning Mode Workflow**
- Project creation through recursive task breakdown
- ✅ 8-12 tasks created across 2-3 levels
- ✅ No circular dependencies detected
- ✅ Git commit with semantic message
- ✅ Automatic transition to working mode

**E2E-002: Complete Working Mode Workflow**
- Task assignment through completion tracking
- ✅ Load balanced assignment (variance <20%)
- ✅ Dependencies respected throughout
- ✅ All tasks completed or properly blocked
- ✅ Git commits for major milestones

**E2E-003: Cross-Mode Switching**
- Dynamic switching between planning and working modes
- ✅ No work lost during transitions
- ✅ Agent states preserved
- ✅ New tasks properly integrated
- ✅ Total project coherence maintained

### Multi-Agent Coordination

**COORD-001: Concurrent Task Claiming**
- Multiple agents claiming tasks simultaneously
- ✅ No task assigned to multiple agents
- ✅ File system consistency under concurrent access
- ✅ Optimistic locking prevents race conditions

**COORD-002: Agent Failure Recovery**
- Agent crashes during task execution
- ✅ Failed agent detected within 5 minutes
- ✅ Task reassigned within 2 minutes
- ✅ Work resumption from last checkpoint

**COORD-003: Resource Contention Management**
- More tasks than agent capacity
- ✅ Highest priority tasks assigned first
- ✅ Agent utilization >85% maintained
- ✅ Load balancing considers effort estimates

### Data Integrity

**DATA-001: Concurrent State Modifications**
- Simultaneous state changes with conflict resolution
- ✅ Final state consistent and valid
- ✅ No intermediate corrupted states
- ✅ Complete audit trail maintained

**DATA-002: Dependency Cycle Detection**
- Complex modifications creating circular references
- ✅ Cycles detected before persistence
- ✅ Clear error messages with resolution suggestions
- ✅ Performance acceptable for large projects (<5s)

**DATA-003: File Corruption Recovery**
- System crashes during file operations
- ✅ Corruption detected on startup
- ✅ Recovery from last known good state
- ✅ System functional after recovery

## Performance Benchmarks

### Core Performance Targets

| Operation | Target Time | Scalability | Memory Limit |
|-----------|-------------|-------------|--------------|
| Project Load (1000 tasks) | < 30s | Linear O(n) | < 1GB |
| Task Assignment Batch | < 5s | Constant O(1) | < 100MB |
| State Transition | < 100ms | Constant O(1) | < 10MB |
| Dependency Analysis | < 10s | O(n log n) | < 500MB |

### Concurrent Performance

- **20 concurrent agents**: No deadlocks, fair distribution
- **100 file ops/sec**: <1% failure rate
- **50 state changes/sec**: Zero data corruption
- **10 git commits/min**: No merge conflicts

### Scale Requirements

- **Planning Mode**: Break down 500 tasks in <5 minutes
- **Working Mode**: Process 1000 state changes in <2 minutes
- **Multi-Agent**: Coordinate 10 agents on 200 tasks in <30 minutes

## Mock Implementations

### MockAmplifierTaskTool
- **Purpose**: Simulate agent spawning via amplifier's Task tool
- **Capabilities**: 8 agent types with realistic execution simulation
- **Features**: Configurable failure rates, execution delays, resource limits
- **Integration**: File-based communication, event logging for verification

### MockLLMService
- **Purpose**: Simulate task breakdown without real LLM calls
- **Responses**: Realistic task decomposition based on input complexity
- **Features**: Deterministic outputs for test repeatability
- **Integration**: JSON response parsing with error simulation

### MockGitOperations
- **Purpose**: Test git integration without real repository complexity
- **Operations**: Commit, branch, merge with conflict simulation
- **Features**: Call tracking, state management, failure scenarios
- **Integration**: Compatible with amplifier's git workflow patterns

## Integration with Amplifier Ecosystem

### Task Tool Integration
- Spawn agents using amplifier's existing Task infrastructure
- Compatible with agent catalog and capability matching
- Resource management respecting amplifier's limits
- Error handling following amplifier's patterns

### CCSDK Defensive Utilities
- Use `parse_llm_json()` for robust LLM response handling
- Apply `retry_with_feedback()` for resilient operations
- Implement `isolate_prompt()` for context protection
- Follow established defensive programming patterns

### Git Workflow Compatibility
- Commit messages following amplifier conventions
- Branch management compatible with existing workflows
- Merge conflict resolution using amplifier patterns
- History preservation for debugging and audit

## Test Execution Strategy

### Development Workflow

```bash
# Quick development cycle (2 minutes)
make test-planner-unit

# Integration verification (15 minutes)
make test-planner-integration

# Full validation (60 minutes)
make test-planner-full

# Performance benchmarking (30 minutes)
make test-planner-performance
```

### Continuous Integration

- **PR Validation**: Unit + integration tests on every pull request
- **Daily Builds**: Full test suite including performance benchmarks
- **Release Validation**: Complete E2E testing with real services
- **Performance Monitoring**: Regression detection with 10% threshold

### Manual Testing Checklist

**Pre-Implementation Validation**
- [ ] All test scenarios execute successfully with mocks
- [ ] Performance benchmarks establish baseline expectations
- [ ] Integration points clearly defined and tested
- [ ] Error scenarios comprehensively covered
- [ ] Recovery mechanisms validated

**Post-Implementation Validation**
- [ ] Real system matches test specifications exactly
- [ ] Performance meets or exceeds benchmark targets
- [ ] Integration with amplifier ecosystem seamless
- [ ] Error handling robust under real conditions
- [ ] User experience matches test expectations

## Success Metrics

### Functional Requirements (Must Pass)
- ✅ Planning mode successfully breaks down complex projects
- ✅ Working mode assigns and tracks task execution
- ✅ Multi-agent coordination handles concurrent work
- ✅ State transitions maintain data integrity
- ✅ Recovery mechanisms handle all failure conditions

### Quality Requirements (Must Pass)
- ✅ **Reliability**: 99.9% success rate on valid inputs
- ✅ **Performance**: All operations within target times
- ✅ **Data Integrity**: Zero corruption under any load
- ✅ **User Experience**: Clear errors, visible progress, predictable behavior

### Integration Requirements (Must Pass)
- ✅ **Amplifier Compatibility**: Seamless ecosystem integration
- ✅ **CCSDK Utilization**: Proper use of defensive utilities
- ✅ **Git Integration**: Compatible with amplifier workflows
- ✅ **Agent Coordination**: Works with existing Task infrastructure

## Implementation Guidance

### Development Approach

1. **Start with Tests**: All tests must pass before implementation
2. **Test-Driven Development**: Write failing tests, then make them pass
3. **Golden Data Validation**: Implementation must handle all test scenarios
4. **Performance First**: Meet benchmarks from day one
5. **Integration Focus**: Seamless amplifier ecosystem fit

### Quality Gates

- **Unit Tests**: Must achieve 85% line coverage, 80% branch coverage
- **Integration Tests**: Must cover 70% of end-to-end paths
- **Performance Tests**: Must meet all benchmark targets
- **E2E Tests**: Must validate complete user workflows
- **Manual Testing**: Must pass comprehensive checklist

### Risk Mitigation

- **Complexity Management**: Follow ruthless simplicity principle
- **Error Handling**: Comprehensive defensive programming
- **Performance**: Continuous benchmarking and optimization
- **Integration**: Early and frequent testing with amplifier tools
- **Recovery**: Robust failure handling and state restoration

## Conclusion

This golden test specification provides a complete validation framework for the super-planner system. By following the "spec and test forward" approach, we ensure:

- **Predictable Implementation**: Tests define exact expected behavior
- **Quality Assurance**: Comprehensive coverage of functionality and edge cases
- **Performance Confidence**: Benchmarks validate scale requirements
- **Integration Success**: Seamless amplifier ecosystem compatibility
- **User Trust**: Reliable, fast, and intuitive planning system

The implementation phase can proceed with confidence that the system will work correctly, perform well, and integrate seamlessly into the amplifier ecosystem. All test scenarios represent real-world usage patterns and validate that the super-planner will be a valuable addition to amplifier's capabilities.

**Next Steps**: Begin implementation with full test coverage as the specification. Each component should be built to make the corresponding tests pass, ensuring the final system matches this comprehensive specification exactly.