# Frequently Asked Questions

**Quick answers to common questions about Document-Driven Development**

---

## Process Questions

**Q: What if implementation reveals the design was wrong?**

A: Stop immediately. Fix documentation first. Propose change to user. Get approval. Update approved spec. Then update code to match. Documentation remains source of truth throughout.

---

**Q: Can I skip the approval gate for small changes?**

A: Use judgment. Typo fixes: no gate needed. Design changes, new features, refactoring: always gate. When in doubt, get approval. Gates are cheap, rework is expensive.

---

**Q: Should I commit during documentation iteration?**

A: No. Iterate with human until approved, THEN commit. This prevents git log thrashing with wrong versions. Clean git history prevents another form of context poisoning.

---

**Q: How do I handle backward compatibility?**

A: Don't document it in main docs. Code can maintain backward compat internally, but docs describe only current state. Use [retcon writing](../core_concepts/retcon_writing.md) - write as if the new way always existed. Migration notes belong in CHANGELOG or git history.

---

**Q: What if I have hundreds of files to process?**

A: Use [file crawling technique](../core_concepts/file_crawling.md). Process one at a time. Token efficient, resumable, guarantees completion. Exactly what it's designed for.

---

## Context Poisoning Questions

**Q: How do I know if duplication is bad?**

A: Ask: "If I update this content in one place, would I need to update it in another?" If yes, it's duplication. Delete one, keep only canonical source.

See [context poisoning](../core_concepts/context_poisoning.md).

---

**Q: Should I delete or update duplicate docs?**

A: **Delete**. If it exists, it will drift. Updating fixes it once, but drift will return. Deletion is permanent elimination.

---

**Q: What if global replacement changes wrong instances?**

A: This is why global replacement alone is insufficient. Always review each file individually after global replace. Verify replacement worked correctly in context. Mark complete only after verification.

See [Phase 1 Step 5](../phases/01_documentation_retcon.md#step-5-global-replacements-use-with-extreme-caution).

---

## AI Collaboration Questions

**Q: What if AI forgets to use TodoWrite?**

A: Remind it. The todo list is critical for complex tasks. AI should proactively create it at start of any multi-step work within a turn. If work spans multiple turns with user interaction, use `ai_working/` files instead.

---

**Q: How do I know if AI detected a conflict?**

A: AI should explicitly PAUSE and present conflict with options. If AI continues despite mentioning inconsistency, stop it and ask for proper conflict resolution pattern.

---

**Q: Can AI make decisions about conflicts?**

A: No. Only human has full context. AI should detect, collect instances, propose options, and wait for decision. Never guess.

---

## Testing Questions

**Q: How important is "test as user" phase?**

A: Critical. Code tests verify implementation. User testing verifies experience. This catches issues unit tests miss: confusing UX, broken workflows, unclear output. AI should be QA before human review.

See [Phase 5 Step 3](../phases/05_testing_and_verification.md#step-3-test-as-user-would-critical).

---

**Q: What should user testing reports include?**

A: Scenarios tested, observations (output, logs, behavior, state), issues found (with severity), recommendations for human smoke tests. Be specific. Include enough detail for understanding without re-testing everything.

---

## Documentation Questions

**Q: How do I handle third-party library documentation?**

A: Don't duplicate it. Link to official docs. Document only *your* usage patterns, integration points, and project-specific conventions.

---

**Q: How do I know if documentation organization is progressive enough?**

A: Test: Can a new person start at README and progressively drill down? Can they stop at any level with complete understanding of that level? If they must jump around to understand basics, organization needs work.

---

**Q: What if I detect conflicts during implementation?**

A: PAUSE. Don't fix docs or code without guidance. Collect evidence, present to user with options. User decides. If docs need fixing, return to Phase 1. If code needs fixing, fix code to match docs.

---

**Q: Is it really worth all this process for small changes?**

A: Use judgment. Small isolated changes (typo, small refactor): less process fine. Anything touching multiple files, changing interfaces, or affecting users: process saves time by catching issues early. Lean toward more process when uncertain.

---

## Related Documentation

- [Common Pitfalls](common_pitfalls.md) - What goes wrong and how to fix it
- [Tips for Success](tips_for_success.md) - Best practices
- [Checklists](checklists.md) - Verification steps

---

**Return to**: [Reference](README.md) | [Main Index](../README.md)
