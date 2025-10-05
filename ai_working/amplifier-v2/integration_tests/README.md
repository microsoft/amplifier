# Amplifier v2 Integration Tests

This directory contains comprehensive integration tests for the Amplifier v2 system, verifying that all components work together correctly.

## Test Coverage

The integration test suite (`test_integration.py`) verifies:

### Core Components
1. **Kernel Module Loading** - Tests that the kernel can discover, load, and initialize modules via entry points
2. **Message Bus Event Routing** - Verifies events are correctly routed between multiple modules
3. **Model Provider Registration** - Tests LLM provider registration, retrieval, and invocation
4. **Tool Registration & Execution** - Verifies tools can be registered and executed with parameters
5. **Philosophy Injection** - Tests that philosophy guidance is correctly injected into prompts
6. **Agent Registry** - Verifies agent registration, listing, and execution management
7. **End-to-End Workflow** - Tests a complete workflow with multiple modules working together
8. **Concurrent Event Handling** - Verifies the message bus handles multiple concurrent events
9. **Error Handling** - Tests that errors in one module don't crash the system
10. **Module Discovery** - Simulates the entry point discovery mechanism

## Running the Tests

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run all tests
```bash
pytest test_integration.py -v
```

### Run specific test
```bash
pytest test_integration.py::test_kernel_module_loading -v
```

### Run with detailed logging
```bash
pytest test_integration.py -v -s
```

## Test Architecture

The tests use mock implementations to isolate integration testing from external dependencies:

- **MockModelProvider** - Simulates LLM providers without actual API calls
- **MockTool** - Simulates tools with execution tracking
- **TestModule** - A complete test module that registers providers and tools
- **PhilosophyTestModule** - Tests philosophy injection into prompts
- **AgentRegistryModule** - Simulates agent management functionality

## Key Integration Points Tested

1. **Module ↔ Kernel**: Modules can register with kernel and access kernel services
2. **Module ↔ Message Bus**: Modules can publish and subscribe to events
3. **Module ↔ Module**: Modules can communicate via the message bus
4. **Provider ↔ Tool ↔ Agent**: Complete workflow from prompt to execution
5. **Philosophy ↔ Prompts**: Philosophy injection modifies prompts before sending
6. **Error Isolation**: Failures in one component don't affect others

## Test Results

All 10 integration tests pass successfully, confirming:
- ✅ Core kernel loads and manages modules
- ✅ Message bus properly routes events
- ✅ LLM providers can be registered and called
- ✅ Philosophy injection modifies prompts correctly
- ✅ Tools can be registered and executed
- ✅ Agent registry manages agents properly
- ✅ End-to-end workflows function correctly
- ✅ System handles concurrent operations
- ✅ Errors are isolated and handled gracefully
- ✅ Module discovery pattern works as designed

## Architecture Validation

These tests validate the Amplifier v2 architecture principles:
- **Modular Design**: Each component can be tested in isolation and integration
- **Event-Driven**: Message bus enables loose coupling between modules
- **Plugin System**: Modules can be dynamically loaded via entry points
- **Extensibility**: New providers, tools, and agents can be easily added
- **Resilience**: System continues operating despite individual component failures