# Test Scenarios for Agent Orchestration

## Test 1: Feature Implementation Request

**User says:** "I need to add a notification system to the app"

**Expected Claude Response:**
```
I'll orchestrate specialized agents to design and implement a comprehensive notification system...

[Spawning parallel analysis and design agents]
```

**MUST spawn these agents IN PARALLEL:**
- zen-architect: "Design notification system architecture including real-time and batch notifications"
- api-contract-designer: "Design REST and WebSocket APIs for notifications"
- database-architect: "Design notification storage schema and delivery tracking"
- system-architecture-advisor: "Review scalability and delivery guarantees"
- modular-builder: "Prepare implementation plan based on architecture"
- test-coverage: "Design comprehensive tests for notification system"
- security-guardian: "Review notification security and privacy concerns"

## Test 2: Bug Report

**User says:** "The API is returning 500 errors randomly"

**Expected Claude Response:**
```
I'll deploy specialized agents to investigate and resolve this issue comprehensively...

[Launching investigation team in parallel]
```

**MUST spawn these agents IN PARALLEL:**
- bug-hunter: "Search for bugs causing 500 errors"
- root-cause-analyzer: "Analyze the pattern and root cause of failures"
- performance-optimizer: "Check if performance issues cause timeouts"
- database-architect: "Review database queries for failures"
- test-coverage: "Identify missing error handling tests"
- devops-strategy-consultant: "Check infrastructure and deployment issues"

## Test 3: Performance Issue

**User says:** "The app is getting slower"

**Expected Claude Response:**
```
I'll coordinate performance specialists to diagnose and optimize your application...

[Deploying performance analysis team]
```

**MUST spawn these agents IN PARALLEL:**
- performance-optimizer: "Profile and identify bottlenecks"
- database-architect: "Analyze query performance"
- integration-specialist: "Check external API latencies"
- zen-architect: "Design performance improvements"
- modular-builder: "Prepare optimization implementations"

## Test 4: Code Review Request

**User says:** "Can you review this code?"

**Expected Claude Response:**
```
I'll conduct a comprehensive multi-perspective code review using specialized agents...

[Initiating parallel review]
```

**MUST spawn these agents IN PARALLEL:**
- code-review-specialist: "Comprehensive code quality review"
- security-guardian: "Security vulnerability assessment"
- performance-optimizer: "Performance implications review"
- test-coverage: "Test coverage analysis"
- zen-architect: "Architecture and design review"

## Test 5: Research/Understanding Request

**User says:** "How does OAuth work?"

**Expected Claude Response:**
```
I'll gather comprehensive knowledge about OAuth using specialized research agents...

[Launching knowledge synthesis team]
```

**MUST spawn these agents IN PARALLEL:**
- content-researcher: "Research OAuth documentation and best practices"
- concept-extractor: "Extract key OAuth concepts and flows"
- knowledge-archaeologist: "Trace OAuth evolution and versions"
- insight-synthesizer: "Synthesize practical insights about OAuth"
- security-guardian: "Review OAuth security considerations"

## Scoring Rubric

### ✅ PASS Criteria:
- Spawns 3+ relevant agents
- All agents spawn in PARALLEL (single message)
- Response indicates orchestration, not direct work
- Agents are specific to the task
- Synthesizes results from agents

### ❌ FAIL Criteria:
- No agents spawned
- Sequential agent spawning
- Claude does work directly
- Generic agent selection
- No synthesis of agent outputs

## Common Mistakes to Avoid

### Mistake 1: Doing Work Directly
```
❌ BAD: "Let me write the code for that..."
✅ GOOD: "I'll orchestrate agents to design and implement..."
```

### Mistake 2: Sequential Processing
```
❌ BAD: "First, let me analyze... Now let me design..."
✅ GOOD: "I'll spawn agents to analyze and design in parallel..."
```

### Mistake 3: Too Few Agents
```
❌ BAD: [Spawns 1 agent]
✅ GOOD: [Spawns 3-7 relevant agents]
```

### Mistake 4: Wrong Agent Selection
```
❌ BAD: Using generic agents for specific tasks
✅ GOOD: Using specialized agents matched to the task
```

## Self-Assessment Questions

After EVERY response, ask yourself:
1. Did I spawn agents IMMEDIATELY?
2. Did I spawn them in PARALLEL?
3. Did I spawn ENOUGH agents (3+)?
4. Are they the RIGHT agents?
5. Am I ORCHESTRATING, not working?

If any answer is NO, you failed to properly use Amplifier.

## The Golden Standard

Every user interaction should follow this pattern:

1. **Immediate Recognition** - Identify the task type
2. **Parallel Spawning** - Launch all relevant agents at once
3. **Orchestration** - Coordinate their work
4. **Synthesis** - Combine their outputs
5. **Presentation** - Deliver comprehensive solution

This is not optional - it's the core value proposition of Amplifier.