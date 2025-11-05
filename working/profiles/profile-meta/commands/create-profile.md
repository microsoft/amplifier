# Create Profile Command

Create a new development profile from scratch.

## Process

1. **Understand the Need**
   - Ask user about the problem this methodology solves
   - Identify the target context (project type, team, constraints)
   - Clarify what existing profiles don't address

2. **Define Core Philosophy**
   - What are the non-negotiable principles?
   - What trade-offs does this methodology make?
   - What does it optimize for? (speed, correctness, innovation, safety, etc.)
   - When should/shouldn't this profile be used?

3. **Design the Process**
   - What are the major workflow phases?
   - What artifacts does each phase produce/consume?
   - Where are the approval gates and decision points?
   - What feedback loops enable course correction?

4. **Scaffold the Structure**
   ```bash
   mkdir -p profiles/{profile-name}/{philosophy,commands,agents}
   ```

5. **Create profile.md**
   - Write the "pitch" (philosophy, process overview, when to use)
   - Include success metrics
   - Document key principles and trade-offs

6. **Create Philosophy Documents**
   - Deep dive on core principles
   - Decision-making frameworks
   - Historical context and rationale

7. **Create Workflow Commands**
   - One command per major process step
   - Self-documenting with examples
   - Clear inputs/outputs

8. **Create Specialized Agents** (optional)
   - Agents that embody the profile's principles
   - Domain-specific expertise
   - Process-aware automation

9. **Identify Shared Resources**
   - What commands/agents can be imported from `@shared/`?
   - What can be referenced from other profiles?
   - Document composition in profile.md

10. **Test the Profile**
    - Use `/test-profile {profile-name}` to validate structure
    - Try the profile on a small real task
    - Refine based on friction points

11. **Document Examples**
    - Create example workflows
    - Show before/after comparisons
    - Capture learnings and discoveries

## Output

A complete, ready-to-use profile in `profiles/{profile-name}/` with:
- `profile.md` - The pitch and overview
- `philosophy/` - Deep philosophy documents
- `commands/` - Workflow implementation
- `agents/` (optional) - Specialized agents

## Success Criteria

- Philosophy is clear and actionable
- Process steps are well-defined
- Developer knows what to do next
- Success metrics are measurable
- Boundaries (when to use/not use) are explicit
