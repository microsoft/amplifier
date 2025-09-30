# Cross-Reference Index

This index maps the relationships between all 44 AI-First Development Principles. Understanding these connections helps you apply principles effectively and recognize when multiple principles work together (or trade off against each other).

**Status**: Initial version with #31 relationships mapped. Will be updated as each specification is completed.

**Last Updated**: 2025-09-30

## Relationship Types

- **Dependency**: Principle A requires Principle B to be effective
- **Enabler**: Principle A makes Principle B possible or easier
- **Synergy**: Principles A and B work exceptionally well together
- **Trade-off**: Principles A and B create tension that requires balance
- **Complement**: Principles A and B address related aspects of the same concern

## Quick Reference by Principle

### People

#### #01 - Small AI-first Working Groups
- **Related**: [To be documented]

#### #02 - Strategic Human Touchpoints Only
- **Related**: [To be documented]

#### #03 - Prompt Engineering as Core Skill
- **Related**: [To be documented]

#### #04 - Test-Based Verification Over Code Review
- **Related**: [To be documented]

#### #05 - Conversation-Driven Development
- **Related**: [To be documented]

#### #06 - Human Escape Hatches Always Available
- **Related**: [To be documented]

### Process

#### #07 - Regenerate, Don't Edit
- **Enabled by**: #31 (Idempotency by Design) - Idempotency makes regeneration safe
- **Related**: [To be fully documented]

#### #08 - Contract-First Everything
- **Related**: [To be documented]

#### #09 - Tests as the Quality Gate
- **Related**: [To be documented]

#### #10 - Git as Safety Net
- **Synergy with**: #31 (Idempotency by Design) - Git operations are largely idempotent
- **Related**: [To be fully documented]

#### #11 - Continuous Validation with Fast Feedback
- **Synergy with**: #31 (Idempotency by Design) - Validation can run repeatedly without side effects
- **Related**: [To be fully documented]

#### #12 - Incremental Processing as Default
- **Related**: [To be documented]

#### #13 - Parallel Exploration by Default
- **Related**: [To be documented]

#### #14 - Context Management as Discipline
- **Related**: [To be documented]

#### #15 - Git-Based Everything
- **Related**: [To be documented]

#### #16 - Docs Define, Not Describe
- **Related**: [To be documented]

#### #17 - Prompt Versioning and Testing
- **Related**: [To be documented]

#### #18 - Contract Evolution with Migration Paths
- **Related**: [To be documented]

#### #19 - Cost and Token Budgeting
- **Related**: [To be documented]

### Technology

#### #20 - Self-Modifying AI-First Codebase
- **Related**: [To be documented]

#### #21 - Limited and Domain-Specific by Design
- **Related**: [To be documented]

#### #22 - Separation of Concerns Through Layered Virtualization
- **Related**: [To be documented]

#### #23 - Protected Self-Healing Kernel
- **Depends on**: #31 (Idempotency by Design) - Self-healing requires idempotent recovery operations
- **Related**: [To be fully documented]

#### #24 - Long-Running Agent Processes
- **Related**: [To be documented]

#### #25 - Simple Interfaces by Design
- **Related**: [To be documented]

#### #26 - Stateless by Default
- **Synergy with**: #31 (Idempotency by Design) - Stateless operations are naturally more idempotent
- **Related**: [To be fully documented]

#### #27 - Disposable Components Everywhere
- **Enabled by**: #31 (Idempotency by Design) - Idempotent operations make components safely disposable
- **Related**: [To be fully documented]

#### #28 - CLI-First Design
- **Related**: [To be documented]

#### #29 - Tool Ecosystems as Extensions
- **Related**: [To be documented]

#### #30 - Observability Baked In
- **Related**: [To be documented]

#### #31 - Idempotency by Design ✨
- **Enables**: #07 (Regenerate, Don't Edit), #27 (Disposable Components), #23 (Protected Self-Healing Kernel), #32 (Error Recovery Patterns)
- **Synergies**: #26 (Stateless by Default), #10 (Git as Safety Net), #11 (Continuous Validation)
- **Dependencies**: None (foundational principle)
- **Related**: All principles benefit from idempotency, but especially error recovery and state management principles

#### #32 - Error Recovery Patterns Built In
- **Depends on**: #31 (Idempotency by Design) - Can't safely retry operations that aren't idempotent
- **Related**: [To be fully documented]

#### #33 - Graceful Degradation by Design
- **Related**: [To be documented]

#### #34 - Feature Flags as Deployment Strategy
- **Related**: [To be documented]

#### #35 - Least-Privilege Automation with Scoped Permissions
- **Related**: [To be documented]

#### #36 - Dependency Pinning and Security Scanning
- **Related**: [To be documented]

#### #37 - Declarative Over Imperative
- **Related**: [To be documented]

### Governance & Operations

#### #38 - Access Control and Compliance as First-Class
- **Related**: [To be documented]

#### #39 - Metrics and Evaluation Everywhere
- **Related**: [To be documented]

#### #40 - Knowledge Stewardship and Institutional Memory
- **Related**: [To be documented]

#### #41 - Adaptive Sandboxing with Explicit Approvals
- **Related**: [To be documented]

#### #42 - Data Governance and Privacy Controls
- **Related**: [To be documented]

#### #43 - Model Lifecycle Management
- **Related**: [To be documented]

#### #44 - Self-Serve Recovery with Known-Good Snapshots
- **Related**: [To be documented]

## Relationship Clusters

### Cluster: Safe Regeneration
Principles that work together to enable safe, repeatable code generation:

- **#07** - Regenerate, Don't Edit
- **#31** - Idempotency by Design (foundation)
- **#27** - Disposable Components Everywhere
- **#26** - Stateless by Default
- **#10** - Git as Safety Net

**How they work together**: Idempotency (#31) ensures regeneration is safe. Statelessness (#26) makes operations more naturally idempotent. Disposable components (#27) mean you can throw away and regenerate without fear. Git (#10) provides rollback if regeneration goes wrong.

### Cluster: Error Recovery and Resilience
[To be documented as related specifications are completed]

### Cluster: Testing and Validation
[To be documented as related specifications are completed]

### Cluster: Human-AI Collaboration
[To be documented as related specifications are completed]

### Cluster: Contract-Driven Architecture
[To be documented as related specifications are completed]

## Dependency Graph

This section will be populated as more specifications are completed. It will show:
- Which principles must be implemented first (foundational)
- Which principles build on others (derivative)
- Which principles are independent (can be adopted separately)

### Foundational Principles (No Dependencies)
- **#31** - Idempotency by Design

### Second-Layer Principles (Depend on Foundational)
- **#07** - Regenerate, Don't Edit (depends on #31)
- **#27** - Disposable Components (depends on #31)
- **#32** - Error Recovery Patterns (depends on #31)
- **#23** - Protected Self-Healing Kernel (depends on #31)

### Higher-Layer Principles
[To be mapped as specifications are completed]

## Trade-off Relationships

Some principles create productive tensions that require balancing:

[To be documented as specifications are completed. Examples might include:
- Simplicity vs Observability
- Speed vs Safety
- Flexibility vs Constraints
- Automation vs Human Control]

## Implementation Paths

Suggested sequences for implementing principles based on your starting point:

### Path 1: Starting from Scratch
1. Start with **#31 - Idempotency by Design** (foundation)
2. [To be completed as more specs are available]

### Path 2: Retrofitting Existing System
[To be documented]

### Path 3: AI-First Greenfield Project
[To be documented]

## Updates

When completing a new specification:

1. **Add its relationships to this index** under the principle's entry
2. **Update related principles' entries** to reference the new spec
3. **Add to relevant clusters** if the principle fits an existing pattern
4. **Update dependency graph** to show where it fits in the hierarchy
5. **Document any trade-offs** if the principle creates tensions
6. **Update implementation paths** if the principle changes recommended sequences

## Maintenance Notes

- This index should be updated every time a new specification is completed
- Bidirectional references should always be maintained (if A references B, B should reference A)
- When specifications are revised, check that cross-references remain accurate
- Periodically review clusters to ensure they still make sense as understanding evolves

---

**Next Update**: After completing specifications #07, #26, #27, or #32 (highest priority related to #31)