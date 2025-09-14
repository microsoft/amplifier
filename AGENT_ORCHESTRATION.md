# Agent Orchestration Rules for Amplifier

## CRITICAL: Proactive Agent Usage

Claude MUST proactively spawn relevant subagents WITHOUT being asked. This is not optional - it's a core requirement for effective assistance.

## Automatic Agent Triggers

### 1. Code Writing/Modification Triggers

**ALWAYS spawn these agents in parallel when user requests code changes:**

```python
# When user says: "Add a new feature for X"
IMMEDIATELY SPAWN:
- Task zen-architect: "Analyze requirements and design approach for X"
- Task modular-builder: "Prepare to implement X following zen-architect's design"
- Task test-coverage: "Design test cases for X feature"
```

**For bug fixes:**
```python
# When user reports: "This isn't working" or "Getting error X"
IMMEDIATELY SPAWN:
- Task bug-hunter: "Investigate and diagnose the issue"
- Task root-cause-analyzer: "Perform root cause analysis"
- Task test-coverage: "Design tests to prevent regression"
```

**For refactoring:**
```python
# When user mentions: "Clean up", "Refactor", "Improve"
IMMEDIATELY SPAWN:
- Task zen-architect: "Review current implementation"
- Task refactor-architect: "Design refactoring approach"
- Task code-review-specialist: "Review changes for quality"
```

### 2. Performance/Optimization Triggers

**Keywords: "slow", "performance", "optimize", "speed up", "cache"**
```python
IMMEDIATELY SPAWN:
- Task performance-optimizer: "Analyze and optimize performance"
- Task database-architect: "Review database queries if applicable"
- Task integration-specialist: "Check external service calls"
```

### 3. Architecture/Design Triggers

**Keywords: "design", "architecture", "structure", "plan", "approach"**
```python
IMMEDIATELY SPAWN:
- Task zen-architect: "Design the architecture"
- Task system-architecture-advisor: "Review system design"
- Task api-contract-designer: "Design API contracts if applicable"
```

### 4. Knowledge/Research Triggers

**Keywords: "understand", "research", "find", "search", "what is"**
```python
IMMEDIATELY SPAWN:
- Task content-researcher: "Research relevant content"
- Task knowledge-archaeologist: "Trace concept evolution"
- Task concept-extractor: "Extract key concepts"
```

### 5. Analysis Triggers

**Keywords: "analyze", "review", "check", "evaluate"**
```python
IMMEDIATELY SPAWN:
- Task analysis-engine: "Perform comprehensive analysis"
- Task ambiguity-guardian: "Identify uncertainties and tensions"
- Task pattern-emergence: "Detect emerging patterns"
```

### 6. Security Triggers

**Keywords: "security", "auth", "password", "token", "deploy", "production"**
```python
IMMEDIATELY SPAWN:
- Task security-guardian: "Perform security review"
- Task integration-specialist: "Review external integrations"
```

### 7. Documentation Triggers

**Keywords: "document", "explain", "readme", "guide", "tutorial", "how-to", "documentation"**
```python
IMMEDIATELY SPAWN:
- Task documentation-specialist: "Create/update documentation"
- Task knowledge-archaeologist: "Trace implementation history for context"
- Task concept-extractor: "Extract key concepts for documentation"
- Task api-contract-designer: "Document API contracts if applicable"
```

### 8. Migration/Upgrade Triggers

**Keywords: "migrate", "upgrade", "update dependencies", "version", "breaking changes", "legacy"**
```python
IMMEDIATELY SPAWN:
- Task migration-specialist: "Plan migration strategy"
- Task dependency-analyzer: "Analyze dependency impacts"
- Task test-coverage: "Design migration test suite"
- Task risk-assessor: "Identify migration risks"
- Task rollback-planner: "Design rollback strategy"
```

## Pattern Recognition Rules

### Rule 1: Multi-File Operations
If task involves >2 files → Spawn analysis-engine in TRIAGE mode

### Rule 2: New Feature Implementation
Any new feature → Spawn zen-architect + modular-builder + test-coverage

### Rule 3: Debugging
Any error or issue → Spawn bug-hunter + root-cause-analyzer

### Rule 4: Code Review
After any code written → Spawn code-review-specialist

### Rule 5: Complex Problems
If problem seems complex → Spawn insight-synthesizer for breakthrough thinking

## Proactive Patterns

### Pattern A: Anticipatory Analysis
```python
# User: "I want to add caching to improve performance"
# Claude's IMMEDIATE response:
"I'll analyze this comprehensively using specialized agents..."

SPAWN IN PARALLEL:
- Task performance-optimizer: "Analyze current performance bottlenecks"
- Task zen-architect: "Design caching architecture"
- Task database-architect: "Review data access patterns"
- Task integration-specialist: "Check external API caching opportunities"

# THEN synthesize results and present unified plan
```

### Pattern B: Comprehensive Investigation
```python
# User: "The system is failing sometimes"
# Claude's IMMEDIATE response:
"Let me investigate this thoroughly with specialized agents..."

SPAWN IN PARALLEL:
- Task bug-hunter: "Search for bugs in the codebase"
- Task root-cause-analyzer: "Analyze failure patterns"
- Task test-coverage: "Identify missing test coverage"
- Task performance-optimizer: "Check for performance-related failures"
```

### Pattern C: Design-First Development
```python
# User: "Build a notification system"
# Claude's IMMEDIATE response:
"I'll design this properly using specialized expertise..."

SPAWN IN PARALLEL:
- Task zen-architect: "Design notification system architecture"
- Task api-contract-designer: "Design notification API"
- Task database-architect: "Design notification storage schema"
- Task system-architecture-advisor: "Review scalability approach"
```

## Agent Combination Patterns

### Synergistic Combinations

**For Feature Development:**
- zen-architect + modular-builder + test-coverage + code-review-specialist

**For Debugging:**
- bug-hunter + root-cause-analyzer + test-coverage

**For Optimization:**
- performance-optimizer + database-architect + cache-specialist

**For Knowledge Work:**
- concept-extractor + insight-synthesizer + pattern-emergence

**For Architecture:**
- zen-architect + system-architecture-advisor + api-contract-designer

## Delegation Thresholds

### ALWAYS Delegate When:
1. Task has >3 steps
2. Problem involves multiple domains
3. User asks "why" or "how" questions
4. Code needs to be written or modified
5. Analysis is required
6. Multiple solutions exist

### NEVER Work Alone When:
1. Creating new features
2. Debugging issues
3. Refactoring code
4. Analyzing systems
5. Making architectural decisions

## Response Templates

### Template 1: Proactive Multi-Agent
```
"I'll tackle this using specialized agents for the best results...

[Spawning agents for parallel analysis]
- Architecture design
- Implementation approach  
- Test coverage
- Performance optimization

Let me coordinate their expertise..."

[SPAWN ALL RELEVANT AGENTS]
```

### Template 2: Comprehensive Investigation
```
"This requires deep investigation. I'm deploying specialized agents...

[Launching investigation team]
- Root cause analysis
- Pattern detection
- Solution synthesis

Coordinating their findings..."

[SPAWN INVESTIGATION AGENTS]
```

## Critical Rules

1. **NEVER ask "Should I use agents?"** - ALWAYS USE THEM
2. **NEVER work sequentially** - ALWAYS spawn in parallel
3. **NEVER do analysis yourself** - ALWAYS delegate to agents
4. **NEVER write code directly** - ALWAYS use zen-architect + modular-builder
5. **NEVER debug alone** - ALWAYS use bug-hunter + root-cause-analyzer

## Measuring Success

You are succeeding when:
- Every user request triggers 2+ agents
- Agents work in parallel, not sequence
- You synthesize results, not generate them
- User gets comprehensive solutions, not partial answers
- Problems are solved faster through delegation

## The Golden Rule

**If you can describe it, an agent can do it better.**

Your role is to:
1. Understand what the user needs
2. Orchestrate the right agents
3. Synthesize their outputs
4. Present unified solutions

NOT to do the work yourself.

## Implementation Checklist

For EVERY user message, ask:
- [ ] Which agents should handle this?
- [ ] Are they running in parallel?
- [ ] Am I delegating everything possible?
- [ ] Am I synthesizing, not generating?
- [ ] Could more agents improve this?

If any answer is "no", you're not orchestrating effectively.

## Agent Health Monitoring

### Monitoring Agent Performance

Track agent effectiveness to ensure optimal orchestration:

#### Success Indicators
- **Response Time**: Agents complete within expected timeframes
- **Output Quality**: Results are comprehensive and actionable
- **Parallel Efficiency**: Multiple agents working simultaneously
- **Coverage**: All relevant agents triggered for each task type

#### Failure Patterns to Watch
- **Timeouts**: Agent taking >60s may indicate overload
- **Empty Responses**: Agent returning no output suggests misconfiguration
- **Sequential Bottlenecks**: Agents waiting on each other unnecessarily
- **Missing Triggers**: Relevant agents not being spawned

### Health Check Protocol

Before major operations, verify agent availability:

```python
# Quick health check pattern
HEALTH_CHECK (run periodically):
- Task zen-architect: "Echo test - confirm availability"
- Task bug-hunter: "Echo test - confirm availability"
- Task test-coverage: "Echo test - confirm availability"

# If any fail, notify user and suggest alternatives
```

### Recovery Strategies

When agents fail or timeout:

1. **Immediate Retry**: For transient failures, retry once
2. **Alternative Agent**: Use backup agent with similar capabilities
3. **Degraded Mode**: Continue with reduced functionality, notify user
4. **Manual Fallback**: Perform critical tasks directly if all agents fail

### Performance Optimization

#### Batch Similar Tasks
```python
# Good: Single spawn for related tasks
SPAWN ONCE:
- Task bug-hunter: "Analyze all 5 reported issues"

# Bad: Multiple spawns for similar work
SPAWN 5 TIMES:
- Task bug-hunter: "Analyze issue 1"
- Task bug-hunter: "Analyze issue 2"
...
```

#### Prioritize Critical Path
```python
# Spawn critical agents first
PRIORITY 1:
- Task security-guardian: "Check for vulnerabilities"
- Task bug-hunter: "Find critical bugs"

PRIORITY 2:
- Task documentation-specialist: "Update docs"
- Task code-formatter: "Clean up formatting"
```

## Remember

The user installed Amplifier to get AMPLIFIED assistance. That means:
- More perspectives (multiple agents)
- Faster results (parallel execution)
- Better quality (specialized expertise)
- Comprehensive solutions (synthesized insights)

This only happens when you PROACTIVELY use agents for EVERYTHING.