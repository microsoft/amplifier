# Best Practices for AI-Assisted Development

## Module Design

### Self-Contained Modules

- Each module should be a complete, independent unit
- Include all necessary code, tests, and documentation in the module directory
- Define clear public interfaces through `__all__` exports
- Hide implementation details as private (underscore-prefixed)

### Clear Contracts

- Document inputs, outputs, and side effects explicitly
- Use type hints for all public functions and methods
- Provide usage examples in docstrings
- Write README.md as the module's contract specification

### Regeneration-Ready Code

- Structure code to be easily regenerated from specifications
- Keep module boundaries clean and well-defined
- Avoid tight coupling between modules
- Design for replaceability, not permanence

## Error Handling

### Fail Fast and Clearly

- Validate inputs at module boundaries
- Provide descriptive error messages
- Include context about what went wrong and how to fix it
- Use appropriate exception types

### Graceful Degradation

- Handle predictable failure modes
- Provide fallback behavior where appropriate
- Log errors for debugging without crashing
- Continue operation when non-critical components fail

## Testing Philosophy

### Test the Contract, Not the Implementation

- Focus tests on public interfaces
- Verify behavior, not internal state
- Test edge cases and error conditions
- Keep tests simple and focused

### Integration Over Unit Tests

- Prioritize end-to-end functionality tests
- Test how modules work together
- Verify the system delivers value to users
- Add unit tests for complex internal logic

## Documentation

### Document for Regeneration

- Write specifications that could recreate the module
- Include all necessary context and constraints
- Document design decisions and trade-offs
- Provide examples that demonstrate intended usage

### Living Documentation

- Keep documentation close to code
- Update docs when behavior changes
- Use docstrings for function-level documentation
- Write README files for module-level documentation

## Performance Considerations

### Optimize When Measured

- Start with correct, simple implementation
- Measure before optimizing
- Profile to find actual bottlenecks
- Document performance characteristics

### Resource Management

- Clean up resources explicitly
- Use context managers for automatic cleanup
- Handle connection pools and caches carefully
- Monitor memory usage in long-running processes

## Collaboration with AI

### Clear Communication

- Write prompts that clearly specify requirements
- Provide context about the system architecture
- Include examples of desired behavior
- Reference existing patterns and modules

### Trust but Verify

- Review generated code for correctness
- Test behavior, not just syntax
- Validate that contracts are maintained
- Ensure philosophy principles are followed