# Document-Driven Development (DDD)

**A systematic approach to building software where documentation leads, code follows, and AI assistance is maximized.**

---

## Quick Start

**New to DDD?** Start here:
1. [Overview](overview.md) - What is DDD and why use it
2. [Core Concepts](core_concepts/) - Essential techniques
3. [The Process](phases/) - Step-by-step phases
4. [Reference](reference/) - Checklists and tips

---

## Core Principle

**"Documentation IS the specification. Code implements what documentation describes."**

Traditional approach: Code → Docs (docs lag and drift, context poisoning)
DDD approach: **Docs → Approval → Implementation** (docs lead, code follows, perfect sync)

---

## Philosophy Foundation

Document-Driven Development builds on:
- [IMPLEMENTATION_PHILOSOPHY.md](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md) - Ruthless simplicity
- [MODULAR_DESIGN_PHILOSOPHY.md](../../ai_context/MODULAR_DESIGN_PHILOSOPHY.md) - Bricks and studs

Read these first to understand the underlying principles.

---

## The Process Flow

```
Phase 0: Planning & Alignment
    ↓
Phase 1: Documentation Retcon  ←─┐
    ↓                             │
Phase 2: Approval Gate            │ (iterate if needed)
    ↓                             │
    ├─────────────────────────────┘
    ↓
Phase 3: Implementation Planning
    ↓
Phase 4: Code Implementation
    ↓
Phase 5: Testing & Verification
    ↓
Phase 6: Cleanup & Push
```

---

## Documentation Structure

### [Overview](overview.md)
What DDD is, why it works, and when to use it.

### [Core Concepts](core_concepts/)
Essential techniques used throughout the process:
- [File Crawling](core_concepts/file_crawling.md) - Systematic file processing without context overload
- [Context Poisoning](core_concepts/context_poisoning.md) - Understanding and preventing inconsistent information
- [Retcon Writing](core_concepts/retcon_writing.md) - Writing docs as if feature already exists

### [Phases](phases/)
Detailed guides for each phase:
- [Phase 0: Planning & Alignment](phases/00_planning_and_alignment.md)
- [Phase 1: Documentation Retcon](phases/01_documentation_retcon.md)
- [Phase 2: Approval Gate](phases/02_approval_gate.md)
- [Phase 3: Implementation Planning](phases/03_implementation_planning.md)
- [Phase 4: Code Implementation](phases/04_code_implementation.md)
- [Phase 5: Testing & Verification](phases/05_testing_and_verification.md)
- [Phase 6: Cleanup & Push](phases/06_cleanup_and_push.md)

### [Reference](reference/)
Practical resources:
- [Checklists](reference/checklists.md) - Phase-by-phase verification checklists
- [Tips for Success](reference/tips_for_success.md) - Best practices for humans and AI
- [Common Pitfalls](reference/common_pitfalls.md) - What goes wrong and how to fix it
- [FAQ](reference/faq.md) - Frequently asked questions

---

## Quick Reference

### For AI Assistants

**When starting a DDD cycle:**
1. Load [overview.md](overview.md) to understand the process
2. Load relevant phase docs as you work through each phase
3. Reference [core concepts](core_concepts/) when using those techniques
4. Use [checklists](reference/checklists.md) to verify completion

**For specific modes:**
- **Documentation Mode**: Load Phase 0, 1, 2 + file_crawling + context_poisoning + retcon_writing
- **Implementation Mode**: Load Phase 3, 4, 5 + file_crawling
- **Review Mode**: Load Phase 2, 5 + checklists

### For Humans

**Learning DDD:**
1. Read [overview](overview.md) to understand the approach
2. Skim [core concepts](core_concepts/) to know the techniques
3. Refer to [phases](phases/) as you work through a cycle
4. Use [reference](reference/) materials when needed

**Using DDD:**
- Follow [checklists](reference/checklists.md) to ensure nothing missed
- Review [common pitfalls](reference/common_pitfalls.md) to avoid known issues
- Check [FAQ](reference/faq.md) when questions arise

---

## Why Modular Structure?

This documentation follows the same principles it teaches:

**Maximum DRY**: Each concept lives in ONE place
- File crawling technique: [core_concepts/file_crawling.md](core_concepts/file_crawling.md)
- Context poisoning: [core_concepts/context_poisoning.md](core_concepts/context_poisoning.md)
- Phase-specific guidance: [phases/](phases/)

**Progressive Organization**: Start simple, drill down as needed
- Overview → Core concepts → Detailed phases → Reference

**Right-Sized Modules**: Each doc fits in context window
- Typical doc: 200-400 lines
- Self-contained but cross-referenced
- Can be loaded selectively

**AI-Optimized**: Load only what's needed for current mode
- Documentation mode: Load docs about documentation phases
- Implementation mode: Load docs about implementation phases
- Review mode: Load docs about review and testing

---

## When to Use DDD

✅ **Use DDD for:**
- New features requiring multiple files
- System redesigns or refactoring
- API changes affecting documentation
- Any change touching 10+ files
- Cross-cutting concerns

❌ **Don't use DDD for:**
- Simple typo fixes
- Single-file bug fixes
- Emergency hotfixes
- Trivial updates

Use judgment: Lean toward DDD when uncertain. Process prevents expensive mistakes.

---

## Success Metrics

You're doing DDD well when:
- ✅ Documentation and code never diverge
- ✅ Zero context poisoning incidents
- ✅ Changes require minimal rework
- ✅ AI tools make correct decisions
- ✅ New developers understand from docs alone
- ✅ Examples in docs all work

---

## Related Documentation

**Philosophy:**
- [IMPLEMENTATION_PHILOSOPHY.md](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md) - Ruthless simplicity principles
- [MODULAR_DESIGN_PHILOSOPHY.md](../../ai_context/MODULAR_DESIGN_PHILOSOPHY.md) - Bricks and studs approach

---

**Document Version**: 2.0
**Last Updated**: 2025-10-19
**Based On**: Real implementation experience in amplifier-v2-codespace project
