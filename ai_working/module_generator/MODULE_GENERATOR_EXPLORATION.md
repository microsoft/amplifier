# Module Generator Exploration Report

**Date**: 2025-09-18
**Purpose**: Document the exploration, testing, and enhancement of the Amplifier Module Generator
**Status**: WIP - Functional but with identified quality issues

## Executive Summary

We successfully tested and enhanced the Amplifier Module Generator, which uses the Claude Code SDK to generate complete Python modules from specification documents. The core module generation worked successfully, producing functional code that operates as intended. However, we identified quality issues with test generation that creates inconsistent test files that don't match the generated implementation.

## What We Built/Enhanced

### 1. Module Generator System (`amplifier/tools/module_generator/`)

A CLI tool that takes two markdown specifications (contract and implementation) and generates a complete Python module using the Claude Code SDK.

**Components**:
- `cli.py` - Command-line interface with enhanced logging
- `sdk_client.py` - SDK integration with retry logic and detailed logging
- `generator.py` - Core generation orchestration
- `parser.py` - Specification parsing
- `models.py` - Data models for specifications

### 2. Test Module: Idea Synthesizer

Generated a complete `idea_synthesizer` module with:
- **Core implementation** (`core.py`) - Main synthesizer logic with 5 synthesis strategies
- **Data models** (`models.py`) - Pydantic models for concepts, connections, insights
- **Test suite** (`tests/test_core.py`) - Generated but broken
- **Package structure** - Proper Python package with `__init__.py` files

### 3. Validation Test CLI

Created `test_idea_synthesizer.py` to validate the generated module works correctly from a user perspective.

## What Worked Well

### ✅ Successful Aspects

1. **Core Module Generation**
   - The SDK successfully generated working Python code
   - All 5 synthesis strategies implemented correctly
   - Data persistence (save/load) functionality works
   - Proper use of Pydantic for data validation
   - Clean, readable code following Python conventions

2. **SDK Integration Enhancements**
   - Added comprehensive logging showing requests/responses
   - Implemented retry logic with exponential backoff
   - Error feedback loop helps SDK self-correct
   - Timeout handling prevents indefinite hangs

3. **Architectural Approach**
   - Specification-driven development works well
   - Separation of contract and implementation specs provides flexibility
   - Module structure follows best practices
   - Generated code is genuinely useful and functional

### 📊 Validation Results

The test CLI confirmed the generated module:
- Creates and manages concepts with unique IDs
- Builds connections between ideas
- Synthesizes insights using multiple strategies (Collision, Emergence, Abstraction, Analogy, Simplification)
- Persists and loads data correctly
- Provides useful statistics
- Handles errors gracefully

## What Didn't Work / Issues Found

### ❌ Problems Identified

1. **Test Generation Quality**
   - Generated tests import non-existent classes
   - Test fixtures use wrong field names (e.g., `priority` vs `confidence`)
   - Tests expect different data structures than what was generated
   - Inconsistency between implementation and test generation

2. **SDK Response Reliability**
   - Sometimes returns narrative text when JSON is expected
   - Occasional empty responses requiring retry
   - Response format inconsistency (markdown-wrapped JSON)

3. **Make Check Failures**
   - Generated tests fail pyright type checking
   - Import errors prevent tests from running
   - This blocks CI/CD pipelines

## Technical Insights

### SDK Behavior Patterns

1. **Response Formatting**
   ```python
   # SDK may return JSON wrapped in markdown:
   ```json
   { "actual": "json content" }
   ```
   # Requires stripping before parsing
   ```

2. **Retry Pattern That Works**
   ```python
   async def _query_sdk_with_retry(...):
       for attempt in range(max_retries):
           try:
               response = await self._query_sdk(...)
               # Include error in retry prompt for self-correction
               if expect_json and parse_fails:
                   retry_prompt = f"{original}\nPrevious error: {error}\nReturn ONLY valid JSON."
   ```

3. **Timeout Configuration**
   - 120 seconds is the sweet spot for SDK operations
   - Shorter timeouts break working code
   - Longer timeouts delay failure detection

### Generation Quality Observations

1. **Consistency Issues**
   - SDK generates different structures for related files
   - Tests don't align with implementation
   - Field names and types vary between components

2. **What the SDK Does Well**
   - Core business logic implementation
   - Data model design
   - Basic CRUD operations
   - Error handling patterns

3. **What the SDK Struggles With**
   - Maintaining consistency across multiple files
   - Generating tests that match implementation
   - Following exact specification details consistently

## Lessons Learned

### 1. Specification Design Matters
- Clear, detailed specifications produce better results
- Ambiguity in specs leads to inconsistent generation
- Examples in specifications help guide the SDK

### 2. Validation is Critical
- Always create independent validation tests
- Don't trust generated tests to validate generated code
- Focus on behavior validation over implementation details

### 3. SDK Integration Best Practices
- Always implement retry logic with error feedback
- Log everything during development/debugging
- Handle multiple response formats defensively
- Set appropriate timeouts (120s for Claude SDK)

### 4. Module Generation Philosophy
- Treat modules as "bricks" that can be regenerated
- Focus on contract stability, not implementation
- Validate through behavior, not code inspection
- Accept that some manual fix-up may be needed

## Recommendations for Future Work

### Immediate Improvements

1. **Fix Test Generation**
   - Add validation that tests import from actual implementation
   - Ensure test data structures match implementation
   - Consider generating tests in a second pass after implementation

2. **Enhance Specifications**
   - Add explicit field definitions to prevent ambiguity
   - Include example data structures
   - Specify exact import paths and class names

3. **SDK Response Handling**
   - Implement more robust JSON extraction
   - Add response format detection
   - Consider multiple parsing strategies

### Strategic Enhancements

1. **Two-Pass Generation**
   - First pass: Generate implementation
   - Parse/analyze generated code
   - Second pass: Generate tests based on actual implementation

2. **Consistency Validation**
   - Add post-generation validation step
   - Check imports, field names, types
   - Auto-fix common inconsistencies

3. **Test Harness Template**
   - Create standard test CLI template
   - Generate alongside module for immediate validation
   - Include in module package

## File Inventory

### Core Module Generator Files (Enhanced)
- `amplifier/tools/module_generator/cli.py` - Added comprehensive logging
- `amplifier/tools/module_generator/sdk_client.py` - Added retry logic and logging
- `amplifier/tools/module_generator/generator.py` - Core orchestration (unchanged)

### Generated Module (Working)
- `amplifier/idea_synthesizer/core.py` - Main implementation ✅
- `amplifier/idea_synthesizer/models.py` - Data models ✅
- `amplifier/idea_synthesizer/__init__.py` - Package initialization ✅
- `amplifier/idea_synthesizer/tests/test_core.py` - Broken tests ❌

### Validation & Testing
- `test_idea_synthesizer.py` - User-perspective validation CLI ✅
- `ai_working/idea_synthesizer/` - Intermediate generation artifacts

### Specifications Used
- Contract spec - Defined module interface
- Implementation spec - Defined internal behavior

## Conclusion

The Module Generator successfully creates functional Python modules from specifications, demonstrating the viability of the "bricks and studs" modular design philosophy. The core generation works well, producing code that genuinely functions as intended. The main quality issue is test generation inconsistency, which is addressable through improved validation and possibly two-pass generation.

The approach proves that AI can generate complete, working modules from specifications, but highlights the importance of independent validation and the need to treat generated tests skeptically. The enhanced logging and retry mechanisms make the generation process more reliable and debuggable.

## Next Steps

1. **Immediate**: Commit enhanced SDK client with logging and retry logic
2. **Short-term**: Fix test generation consistency issues
3. **Medium-term**: Implement two-pass generation with validation
4. **Long-term**: Build library of reusable module specifications

---

*This exploration demonstrates that AI-driven module generation is viable today, with some quality control measures needed to ensure consistency across all generated artifacts.*