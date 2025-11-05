# Refine Profile Command

Analyze and improve an existing development profile.

## Process

1. **Read Current Profile**
   - Load `profiles/{profile-name}/profile.md`
   - Read philosophy documents in `philosophy/`
   - Review commands in `commands/`
   - Check agents in `agents/`

2. **Analyze Current State**
   - **Philosophy clarity**: Are principles clear and actionable?
   - **Process completeness**: Are all workflow steps defined?
   - **Tool effectiveness**: Do commands/agents work well?
   - **Documentation quality**: Is it easy to understand and use?
   - **Composition**: Is there duplication that should be in `shared/`?

3. **Gather Feedback**
   - Ask user: "What's working well with this profile?"
   - Ask user: "What friction points have you encountered?"
   - Ask user: "What outcomes did you expect vs. get?"
   - Review any metrics or measurements

4. **Identify Improvements**

   **Philosophy Refinements:**
   - Clarify ambiguous principles
   - Add missing decision-making frameworks
   - Better articulate trade-offs
   - Improve when-to-use guidance

   **Process Improvements:**
   - Add missing workflow steps
   - Clarify phase transitions
   - Add feedback loops
   - Improve approval gates

   **Tool Enhancements:**
   - Fix broken commands
   - Add missing commands for workflow steps
   - Create new specialized agents
   - Move shared concerns to `shared/`

   **Documentation Updates:**
   - Add missing examples
   - Clarify confusing sections
   - Add success metrics
   - Document discovered patterns

5. **Propose Changes**
   - Present specific improvements with rationale
   - Explain expected impact
   - Get user approval before implementing

6. **Implement Improvements**
   - Update philosophy documents
   - Modify or add commands
   - Create or refine agents
   - Update profile.md

7. **Test Changes**
   - Use `/test-profile {profile-name}` to validate
   - Try improved profile on real work
   - Measure impact vs. baseline

8. **Document Learnings**
   - What problems did improvements solve?
   - What unexpected outcomes occurred?
   - What would you do differently next time?
   - Add to profile's philosophy or examples

## Common Refinement Patterns

### Clarifying Philosophy

**Before**: "We value quality"
**After**: "We optimize for long-term maintainability over short-term velocity. We'll spend 2x time on design to save 10x time in maintenance."

### Improving Process

**Before**: "Then write code"
**After**: "Then create module specifications (inputs, outputs, contracts), get approval, and implement with modular-builder agent"

### Extracting to Shared

**Before**: Each profile has its own `/commit` command
**After**: Single `/commit` in `shared/commands/`, all profiles import it

### Adding Feedback Loops

**Before**: Linear process with no course correction
**After**: Measurement points and decision gates for iteration vs. progression

## Success Criteria

- Friction points are identified and addressed
- Philosophy is clearer and more actionable
- Process is more complete and well-defined
- Tools are more effective
- Profile is easier to use and understand
- Measurable improvement in outcomes
