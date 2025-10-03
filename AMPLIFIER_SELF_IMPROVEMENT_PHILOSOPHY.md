# Amplifier Self-Improvement Philosophy

This document establishes the architectural principles that guide how Amplifier improves itself through AI-first development. These principles inform every decision about how AI agents work on the Amplifier codebase, from module regeneration to feature development to self-healing operations.

**Core Concept**: Amplifier is designed to be improved primarily by AI agents working on itself, with humans providing strategic guidance rather than writing most code. This requires a fundamentally different architecture than traditional software development.

## Cross-References

This philosophy integrates with:
- `IMPLEMENTATION_PHILOSOPHY.md` - Ruthless simplicity in implementation
- `MODULAR_DESIGN_PHILOSOPHY.md` - Bricks and studs architecture
- `DISCOVERIES.md` - Lessons learned from real operations
- `AGENTS.md` - Practical guidelines for AI agents

---

## People

1. **Small AI-first working groups** – teams are small and optimized for working alongside AI agents rather than managing large human teams

2. **Strategic human touchpoints only** – humans stay in the loop for spec approval, architecture decisions, test validation, and quality checks, not line-by-line code review

3. **Prompt engineering as core skill** – writing effective prompts becomes as important as writing code, since the conversation IS the code

4. **Test-based verification over code review** – humans verify behavior through tests instead of reading all the AI-generated code

5. **Conversation-driven development** – the team embraces that specifications and dialogue with AI are the primary development artifacts

6. **Human escape hatches always available** – even with 95% AI-written code, make it easy for humans to pause, override, or hot-patch without fighting the automation

## Process

7. **Regenerate, don't edit** – default action is "regenerate this module from spec" instead of manually editing lines of code

8. **Contract-first everything** – specs, interfaces, and APIs get defined declaratively before any code generation happens

9. **Tests as the quality gate** – tests become the primary validation since humans aren't reading every line, and tests ARE the specification

10. **Git as safety net** – version control with aggressive branching is the main protection, only merge after automated checks pass

11. **Continuous validation with fast feedback** – automated lint/type/test suites plus smoke tests run after each AI edit, auto-halt when guardrails trip, aim for sub-second cycles

12. **Incremental processing as default** – save progress after every item using fixed filenames that overwrite, not timestamps, so operations can be interrupted without data loss

13. **Parallel exploration by default** – run multiple implementation approaches simultaneously, pick the winner, throw away the rest

14. **Context management as discipline** – actively manage the AI's context window, use checkpoints, and fork context through sub-agents

15. **Git-based everything** – version control becomes your database, git ops for workflows, branch-per-experiment, merge as deployment

16. **Docs define, not describe** – README files and docs are executable specs that define what to build, not descriptions of what was built

17. **Prompt versioning and testing** – prompts are code and need version control, A/B testing, regression detection, and the same rigor as any other artifact

18. **Contract evolution with migration paths** – plan how specs and interfaces change over time while maintaining backward compatibility, with clear versioning and migration strategies

19. **Cost and token budgeting** – explicit management of AI API costs, token usage tracking, and rate limiting to prevent runaway spending since every operation has a dollar cost

## Technology

20. **Self-modifying AI-first codebase** – AI writes 95%+ of the code and the AI tool writes code on itself, creating a self-modifying architecture

21. **Limited and domain-specific by design** – features and functionality are deliberately narrow and focused on specific domains

22. **Separation of concerns through layered virtualization** – spec/file-based contracts at one layer, container orchestration at another, infrastructure as code at another

23. **Protected self-healing kernel** – a small, stable, read-only kernel with versioned releases handles core functions and can heal itself, small enough to replicate endlessly

24. **Long-running agent processes** – very long-running multi-threaded processes with agents spawning sub-agents is now the default mode

25. **Simple interfaces by design** – UI and interfaces stay deliberately simple with progressive disclosure and minimal cognitive load

26. **Stateless by default** – components are stateless where possible, with state pushed to the edges like databases and files for easier regeneration

27. **Disposable components everywhere** – any component can be deleted and regenerated from its spec, so replace rather than patch

28. **CLI-first design** – everything optimized for AI interaction with text in/out, composable commands, pipe-able and machine-readable outputs

29. **Tool ecosystems as extensions** – use MCP (Model Context Protocol) and custom tools with explicit capability declarations so AI can interact with domain-specific systems

30. **Observability baked in** – structured logging, audit trails of AI decisions, clear error surfaces, and diagnostic-first design from day one

31. **Idempotency by design** – operations are safely repeatable since AI agents often retry, so everything from API calls to file writes handles "do this again" without breaking

32. **Error recovery patterns built in** – explicit retry policies, exponential backoff, circuit breakers, graceful degradation, and bulkheads to prevent cascade failures

33. **Graceful degradation by design** – system continues functioning when components fail, even if with reduced capabilities

34. **Feature flags as deployment strategy** – enable and disable features without code changes, critical for parallel variant testing and rollback

35. **Least-privilege automation with scoped permissions** – AI tools declare explicit capabilities and permission scopes, never exceeding allowed access when manipulating their environment

36. **Dependency pinning and security scanning** – lock dependency versions, scan for vulnerabilities, and audit AI's package choices since generated code can introduce supply chain risks

37. **Declarative over imperative** – prefer config files over procedural code, infrastructure as code, and schema-driven development patterns

## Governance & Operations

38. **Access control and compliance as first-class** – treat permissions, audit logging, and kill-switches as core features with defined escalation paths when AI wants to exceed its boundaries

39. **Metrics and evaluation everywhere** – every agent loop emits measurable outcomes like latency, success rate, and diff quality with automated regression detection and red/green dashboards

40. **Knowledge stewardship and institutional memory** – capture prompts, decisions, and postmortems in structured memory systems so regenerated modules inherit past context and surface discoveries automatically

41. **Adaptive sandboxing with explicit approvals** – move long-running agent processes between safe sandboxes and higher-permission environments only via explicit approvals, preventing context drift into privileged areas

42. **Data governance and privacy controls** – explicitly define what data agents can access, redact sensitive information from logs, and ensure prompts and results comply with retention and residency requirements

43. **Model lifecycle management** – treat model choice, upgrades, and rollbacks like dependency management with provenance tracking, gated evaluation suites before version swaps, and fallback models ready if quality regresses

44. **Self-serve recovery with known-good snapshots** – system keeps verified snapshots and can reinstall itself or spin up fresh instances without human help when things go wrong

---

## Applying These Principles

When working on Amplifier:

1. **Before starting work**: Check which principles apply to your task
2. **During design**: Reference relevant principles in specs and contracts
3. **In implementation**: Follow the technology and process guidelines
4. **After completion**: Verify governance and operations requirements are met
5. **When something breaks**: Update `DISCOVERIES.md` with lessons that refine these principles

These principles evolve as we learn. When you discover a better pattern, propose an update to this document.