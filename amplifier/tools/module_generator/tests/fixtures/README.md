# IdeaSynthesizer Example Module

This directory contains the design specifications for the **IdeaSynthesizer** module, which serves as a test case for the module generator CLI tool.

## Purpose

The IdeaSynthesizer is an example module that demonstrates:
- Cross-document insight synthesis using AI
- Proper modular design following the "bricks & studs" philosophy
- Integration with Claude Code SDK for AI operations
- Comprehensive contract-first development

## Files

- `IDEA_SYNTHESIZER_CONTRACT.md` - The public API contract defining what the module does
- `IDEA_SYNTHESIZER_IMPL_SPEC.md` - The implementation specification detailing how it works

## Usage

These files will be used to test the module generator:

```bash
# From the repository root
make generate-module \
  CONTRACT=ai_working/idea_synthesizer/IDEA_SYNTHESIZER_CONTRACT.md \
  SPEC=ai_working/idea_synthesizer/IDEA_SYNTHESIZER_IMPL_SPEC.md
```

The generator should produce a complete module at `amplifier/idea_synthesizer/` with:
- Core implementation files
- Data models
- Tests
- Documentation

## Module Overview

The IdeaSynthesizer takes document summaries as input and generates novel, cross-document ideas by:
1. Loading and validating summary records
2. Batching summaries for efficient processing  
3. Using Claude to synthesize net-new insights
4. Validating novelty and deduplicating results
5. Persisting ideas with full provenance tracking

This demonstrates a realistic, production-grade module that could be part of a larger knowledge synthesis pipeline.
