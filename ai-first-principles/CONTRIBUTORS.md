# Contributors Guide - AI-First Principles Specification Library

## Overview

This guide documents the process for contributing new principles to the AI-First Principles Specification Library. It's designed for both humans and AI agents who want to extend the library with new specifications.

## Table of Contents

1. [Understanding the Library Structure](#understanding-the-library-structure)
2. [The Principle Creation Process](#the-principle-creation-process)
3. [Quality Standards](#quality-standards)
4. [Tools and Validation](#tools-and-validation)
5. [Integration Workflow](#integration-workflow)
6. [Common Pitfalls](#common-pitfalls)

## Understanding the Library Structure

### Current Organization

The library contains 44 principles organized into 4 categories:

```
ai-first-principles/
├── principles/
│   ├── people/          # 1-6: Team structure, human-AI collaboration
│   ├── process/         # 7-19: Development workflows, methodologies
│   ├── technology/      # 20-37: Technical implementation patterns
│   └── governance/      # 38-44: Policy and operations
├── tools/              # Validation and search tools
├── README.md           # Main index and documentation
├── TEMPLATE.md         # Specification template
├── PROGRESS.md         # Tracking document
└── CONTRIBUTORS.md     # This file
```

### Principle Numbering

- Principles are numbered sequentially: 01-44 (currently)
- New principles should continue the sequence: 45, 46, 47...
- Each category maintains its number range
- Cross-references use these numbers

### File Naming Convention

```
{category}/{number}-{slug-name}.md

Examples:
- people/01-small-ai-first-working-groups.md
- technology/45-prompt-design-patterns.md
- process/20-context-curation-pipelines.md
```

## The Principle Creation Process

### Phase 1: Source Content Analysis

**For each new principle:**

1. **Identify Core Concept**
   - What is the atomic, actionable principle?
   - Why is it specifically important for AI-first development?
   - How does it differ from existing principles?

2. **Gather Source Materials**
   - Collect 3-5 authoritative sources
   - Look for:
     - Academic papers
     - Engineering blog posts
     - Open-source implementations
     - Industry best practices
   - Document sources for citations

3. **Map to Existing Principles**
   - Check for overlaps with existing 44 principles
   - Identify complementary principles for cross-references
   - Determine which category fits best

### Phase 2: Specification Drafting

Use `TEMPLATE.md` as the foundation. Each section has specific requirements:

#### 1. Plain-Language Definition (1-2 sentences)
- Must be understandable without technical jargon
- Should capture the essence without being reductive
- Test: Can a junior developer understand it?

**Example:**
```markdown
An operation is idempotent when running it multiple times produces
the same result as running it once. Idempotency by design means
building systems where operations can be safely retried without
causing unintended side effects or accumulating errors.
```

#### 2. Why This Matters for AI-First Development (2-3 paragraphs)

Structure:
1. **Problem Context**: What unique challenges AI-first introduces
2. **Specific Benefits**: How this principle addresses those challenges (numbered list of 3)
3. **Consequences**: What happens when violated

Requirements:
- Focus on AI-agent-specific scenarios
- Include concrete failure modes
- Reference real-world implications

#### 3. Implementation Approaches (4-6 approaches)

Each approach needs:
- **Bold name**: Clear, descriptive title
- **Description**: How to implement (2-3 sentences)
- **When to use**: Specific scenarios
- **Code example** (if applicable): Working, tested code

Structure:
```markdown
### 1. **Approach Name**

Description of the approach in 2-3 sentences.

When to use: Specific scenario where this approach shines.

```python
# Working code example
def example_implementation():
    pass
```
```

#### 4. Good Examples vs Bad Examples (3-5 pairs)

Each example pair includes:
- **Scenario name**: Contextual title
- **Good example**: Complete, runnable code
- **Bad example**: Complete, runnable anti-pattern
- **Why It Matters**: Concrete impact explanation

Requirements:
- Code must be syntactically correct
- Examples should be realistic (not toy code)
- Differences should be clear and significant
- Must demonstrate actual problems, not style preferences

#### 5. Related Principles (3-6 cross-references)

Format:
```markdown
- **[Principle #{number} - {Name}](path/to/spec.md)** -
  {Relationship explanation: dependency, enabler, synergy, contrast}
```

Relationship types:
- **Dependency**: "Must implement X before Y"
- **Enabler**: "X makes Y much easier"
- **Synergy**: "X and Y together create more value"
- **Contrast**: "X and Y are different approaches to similar problems"

#### 6. Common Pitfalls (5-7 documented)

Each pitfall needs:
- **Bold title**: Descriptive name
- **Description**: What goes wrong
- **How to avoid**: Concrete prevention

Example:
```markdown
**Pitfall: Assuming HTTP PUT is always idempotent**

While PUT is semantically idempotent, application logic can break this.
For example, PUT /items/{id} that increments a counter violates idempotency.

Avoid by: Never embed side effects in PUT handlers. Keep state
transitions explicit and predicable based on request body only.
```

#### 7. Tools & Frameworks (Categorized)

Group tools by:
- **Languages/Frameworks**: Python libraries, JS frameworks
- **Platforms**: Cloud services, SaaS tools
- **Development Tools**: CLI utilities, IDE extensions
- **Testing/Validation**: Test frameworks, linters

Format:
```markdown
### Languages & Frameworks
- **[Tool Name](url)**: Brief description of what it does

### Platforms
- **[Platform Name](url)**: What it provides
```

#### 8. Implementation Checklist (8-12 items)

Create a checklist developers can use before committing code:
- Each item should be independently verifiable
- Items should be specific, not vague
- Include "how to verify" for non-obvious items

Example:
```markdown
- [ ] All API endpoints return same result on retry with same inputs
- [ ] Database operations use transactions with rollback capability
- [ ] File operations check existence before creating resources
- [ ] Generated unique IDs are deterministic or idempotency-key-based
```

### Phase 3: Quality Validation

Before submitting, validate against these criteria:

**Content Quality**
- [ ] Plain-language definition is clear to non-experts
- [ ] AI-first rationale includes 3 specific benefits
- [ ] At least 4 implementation approaches with when-to-use guidance
- [ ] 3-5 good/bad example pairs with working code
- [ ] 3-6 related principles with relationship explanations
- [ ] 5-7 common pitfalls with avoidance strategies
- [ ] Tools categorized and linked
- [ ] 8-12 item checklist with verification criteria

**Technical Quality**
- [ ] All code examples are syntactically correct
- [ ] Code examples are tested and work
- [ ] No placeholder code (no `// TODO` or `pass` stubs)
- [ ] Cross-references use correct paths and numbers
- [ ] Links are valid and accessible

**Consistency**
- [ ] Follows template structure exactly
- [ ] Uses consistent terminology with existing principles
- [ ] Matches tone and style of existing specifications
- [ ] File naming follows convention
- [ ] Approximately 300-400 lines (like existing principles)

### Phase 4: Integration

1. **Add to PROGRESS.md**
   ```markdown
   - [ ] 45 - Prompt Design Patterns
   ```

2. **Update README.md**
   Add to appropriate category index

3. **Update cross-reference-index.md**
   Add new principle and its relationships

4. **Run Validation Tools**
   ```bash
   cd ai-first-principles
   python3 tools/principle_builder.py validate 45
   python3 tools/fix_cross_references.py
   ```

5. **Test Cross-References**
   ```bash
   # Verify all referenced principles exist
   python3 tools/principle_builder.py list
   ```

## Quality Standards

### Writing Style

**Do:**
- Use active voice
- Write in present tense
- Be specific and concrete
- Include measurable outcomes
- Use "should" and "must" appropriately
- Reference real scenarios

**Don't:**
- Use marketing language or hype
- Make unsupported claims
- Include opinion without evidence
- Create artificial complexity
- Use jargon without explanation

### Code Examples

**Requirements:**
- Must be complete and runnable
- Should demonstrate real scenarios
- Include error handling where relevant
- Show both correct and incorrect patterns
- Use current syntax and best practices

**Anti-patterns to avoid:**
```python
# Bad: Placeholder code
def process_data():
    # TODO: implement this
    pass

# Bad: Toy example with no real context
def add(a, b):
    return a + b

# Good: Complete, realistic example
def create_user_with_idempotency(
    email: str,
    password: str,
    idempotency_key: str
) -> User:
    """Create user account with idempotency protection."""
    existing = db.get_user_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # Return cached result

    user = User(email=email, password_hash=hash_password(password))
    db.save_with_idempotency_key(user, idempotency_key)
    return user
```

### Cross-Reference Quality

Good cross-references explain the relationship:
```markdown
✅ Good:
- **[Principle #26 - Stateless by Default](../technology/26-stateless-by-default.md)** -
  Idempotency is much easier to achieve in stateless systems where each
  request contains all necessary information.

❌ Bad:
- See also: Principle #26
```

## Tools and Validation

### Available Tools

**Validation Tool**
```bash
python3 tools/principle_builder.py validate {number}
```
Checks:
- File structure
- Required sections
- Code syntax
- Cross-reference validity
- Quality metrics

**Search Tool**
```bash
python3 tools/principle_search.py "prompt patterns"
```
Helps find related existing principles to avoid duplication

**Cross-Reference Fixer**
```bash
python3 tools/fix_cross_references.py
```
Automatically fixes broken cross-reference paths

**List All Principles**
```bash
python3 tools/principle_builder.py list
```

### Quality Scoring

The validation tool provides quality scores:
- **90-100**: Excellent - ready for merge
- **80-89**: Good - minor improvements needed
- **70-79**: Acceptable - needs revision
- **< 70**: Needs significant work

## Integration Workflow

### For New Contributors

1. **Fork & Clone**
   ```bash
   git clone https://github.com/microsoft/amplifier.git
   cd amplifier/ai-first-principles
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b add-principle-45-prompt-patterns
   ```

3. **Create Specification**
   - Use `TEMPLATE.md` as starting point
   - Follow this guide for each section
   - Validate as you go

4. **Validate & Test**
   ```bash
   python3 tools/principle_builder.py validate 45
   python3 tools/fix_cross_references.py
   ```

5. **Update Documentation**
   - Add to PROGRESS.md
   - Update README.md
   - Update cross-reference-index.md

6. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add principle #45 - Prompt Design Patterns"
   git push origin add-principle-45-prompt-patterns
   ```

7. **Create Pull Request**
   - Reference this guide in PR description
   - Include validation results
   - Note any related issues

### Review Process

PRs are reviewed for:
1. **Completeness**: All template sections filled
2. **Quality**: Meets quality standards
3. **Originality**: Doesn't duplicate existing principles
4. **Accuracy**: Technical correctness of examples
5. **Consistency**: Matches library style and structure

## Common Pitfalls

### 1. Creating Duplicate Principles

**Problem**: New principle overlaps significantly with existing ones.

**Solution**:
- Use search tool to find related principles
- Review all principles in target category
- Consider enhancing existing principle instead

### 2. Too Abstract or Theoretical

**Problem**: Principle lacks concrete, actionable guidance.

**Solution**:
- Every approach needs specific "how-to" steps
- Include working code examples
- Add "when to use" guidance
- Create verifiable checklist items

### 3. Inconsistent Code Examples

**Problem**: Good/bad examples don't clearly show the difference.

**Solution**:
- Make differences obvious
- Use same scenario for both examples
- Explicitly state "Why It Matters"
- Test that bad example actually fails

### 4. Weak Cross-References

**Problem**: Just listing related principles without explanation.

**Solution**:
- Explain the relationship type
- Describe how principles work together
- Show which to apply first
- Note any conflicts or trade-offs

### 5. Missing AI-First Context

**Problem**: Principle applies to any development, not specific to AI-first.

**Solution**:
- Add "Why This Matters for AI-First Development" section
- Highlight agent-specific scenarios
- Show automated system failure modes
- Connect to existing AI-first principles

### 6. Vague Implementation Checklists

**Problem**: Checklist items are subjective or unverifiable.

**Solution**:
```markdown
❌ Bad:
- [ ] Code is idempotent

✅ Good:
- [ ] All database writes include "INSERT ... ON CONFLICT DO NOTHING"
- [ ] API returns 200 (not 201) when resource already exists
- [ ] File operations use atomic writes with temp files
```

## Process for Content Integration

### Converting Existing Content to Principles

When integrating content from external sources (research papers, blog posts, repositories):

1. **Synthesis Phase**
   - Read 3-5 source documents on the topic
   - Extract common patterns and techniques
   - Identify unique insights and innovations
   - Note practical implementation examples

2. **Distillation Phase**
   - Identify the core principle (atomic concept)
   - Determine what makes it AI-first specific
   - Map examples to implementation approaches
   - Extract pitfalls and anti-patterns

3. **Adaptation Phase**
   - Convert examples to our template format
   - Ensure code examples are complete and tested
   - Add AI-first development context
   - Create cross-references to existing principles

4. **Validation Phase**
   - Check against quality standards
   - Verify technical accuracy
   - Test all code examples
   - Run validation tools

### Example: From Research Paper to Principle

**Source**: "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"

**Extraction**:
- Core technique: Breaking down reasoning into steps
- Benefits: Improved accuracy on complex tasks
- Implementation: Specific prompt patterns
- Pitfalls: When it doesn't help, added cost

**Principle Template Mapping**:
- **Definition**: Chain-of-thought systems...
- **Why AI-First**: Agents need explicit reasoning traces...
- **Approaches**: Zero-shot CoT, few-shot CoT, self-consistency...
- **Examples**: Good (structured reasoning) vs Bad (single-step)
- **Related**: Links to prompt patterns, context management
- **Pitfalls**: Overuse on simple tasks, cost implications

## Questions and Support

- **Documentation**: See README.md for library overview
- **Issues**: Open GitHub issue for questions or bugs
- **Discussions**: Use GitHub Discussions for design questions
- **Validation**: Use provided tools before submitting

---

**Version**: 1.0
**Last Updated**: 2025-09-30
**Maintainers**: Amplifier Team

