# Super-Planner Test Scenarios

Comprehensive test scenarios with verification criteria for the super-planner system.

## End-to-End Workflow Tests

### E2E-001: Complete Planning Mode Workflow

**Scenario**: Project creation through recursive task breakdown

**Setup**:
- Empty workspace with git repository
- Simple project requirements (web app with 3 components)
- Mock LLM service configured for task breakdown

**Execution Steps**:
1. Create new project via CLI: `amplifier plan create "Simple Web App"`
2. System enters planning mode and breaks down high-level goals
3. User confirms and approves initial task structure
4. System recursively breaks down complex tasks (depth 2-3)
5. System detects completion criteria and exits planning mode
6. Final task structure is persisted to git

**Success Criteria**:
- ✅ Project created with 8-12 tasks across 2-3 levels
- ✅ All tasks have valid states (NOT_STARTED) and dependencies
- ✅ No circular dependencies detected
- ✅ Git commit created with semantic message
- ✅ Task hierarchy matches expected structure from test data
- ✅ Planning mode automatically transitions to working mode

**Verification Commands**:
```bash
amplifier plan status
amplifier plan tree --show-dependencies
git log --oneline -5
```

### E2E-002: Complete Working Mode Workflow

**Scenario**: Task assignment through completion tracking

**Setup**:
- Project with 20 tasks in NOT_STARTED state (from complex_microservices_platform.json)
- 3 mock agents with different capabilities registered
- Git repository initialized

**Execution Steps**:
1. Enter working mode: `amplifier plan work`
2. System analyzes available tasks and agent capabilities
3. Assigns initial batch of 6 tasks to 3 agents
4. Agents claim tasks and begin work (simulated)
5. Tasks progress through states: ASSIGNED → IN_PROGRESS → COMPLETED
6. System detects completed dependencies and assigns follow-up tasks
7. Continue until all tasks completed or blocked

**Success Criteria**:
- ✅ Load balanced assignment across agents (variance <20%)
- ✅ Dependencies respected (no task starts before dependencies complete)
- ✅ All available tasks assigned within 30 seconds
- ✅ State transitions logged with timestamps
- ✅ Git commits created for major milestones
- ✅ Final project state shows all tasks COMPLETED

**Verification Commands**:
```bash
amplifier plan status --show-agents
amplifier plan history
git log --grep="task completion"
```

### E2E-003: Cross-Mode Switching

**Scenario**: Switch between planning and working modes based on conditions

**Setup**:
- Project 50% complete (half tasks in COMPLETED state)
- Discovery of new requirements requiring additional tasks
- 2 agents actively working on tasks

**Execution Steps**:
1. Start in working mode with active agents
2. User discovers new requirement: "Add mobile app support"
3. Switch to planning mode: `amplifier plan --mode=planning`
4. System pauses agent coordination
5. Break down new mobile requirements into tasks
6. Integrate new tasks into existing project structure
7. Switch back to working mode
8. Resume agent coordination with expanded task list

**Success Criteria**:
- ✅ Mode transition doesn't lose existing work
- ✅ Agent states preserved during planning pause
- ✅ New tasks properly integrated with dependencies
- ✅ No deadlocks or conflicts introduced
- ✅ Total project coherence maintained
- ✅ Git history shows clear mode transitions

## Multi-Agent Coordination Tests

### COORD-001: Concurrent Task Claiming

**Scenario**: Multiple agents attempt to claim same tasks simultaneously

**Setup**:
- Project with 10 available tasks
- 5 agents with overlapping capabilities
- Network partition simulation (delayed responses)

**Execution Steps**:
1. All 5 agents request task assignments simultaneously
2. System processes claims with optimistic locking
3. First agent succeeds, others receive updated state
4. Agents retry with remaining tasks
5. System ensures no double-assignment occurs

**Success Criteria**:
- ✅ No task assigned to multiple agents
- ✅ All agents receive tasks within reasonable time
- ✅ File system maintains consistency under concurrent access
- ✅ Optimistic locking prevents race conditions
- ✅ Agent retry logic handles conflicts gracefully

### COORD-002: Agent Failure and Recovery

**Scenario**: Agent crashes mid-task execution

**Setup**:
- Agent working on critical path task for 15 minutes
- Task 60% complete with intermediate state saved
- Other agents waiting on this task's completion

**Execution Steps**:
1. Agent crashes/disconnects during task execution
2. System detects stale agent lease (timeout)
3. Task returns to ASSIGNED state after lease expires
4. System reassigns task to another capable agent
5. New agent resumes work from last checkpoint
6. Task completes successfully

**Success Criteria**:
- ✅ Failed agent detected within 5 minutes
- ✅ Task reassigned within 2 minutes of detection
- ✅ No work lost (checkpoint recovery)
- ✅ Dependent tasks not indefinitely blocked
- ✅ System health metrics updated correctly

### COORD-003: Resource Contention Management

**Scenario**: More tasks available than agent capacity

**Setup**:
- 50 tasks ready for assignment
- 8 agents with capacity for 3 tasks each (24 total capacity)
- Tasks have different priorities and effort estimates

**Execution Steps**:
1. System analyzes available capacity and task priorities
2. Assigns 24 highest priority tasks to agents
3. Remaining 26 tasks queued by priority
4. As agents complete tasks, new tasks assigned from queue
5. System maintains optimal utilization throughout

**Success Criteria**:
- ✅ Highest priority tasks assigned first
- ✅ Agent utilization >85% maintained
- ✅ Queue processing fair and efficient
- ✅ No agent overloaded (>3 concurrent tasks)
- ✅ Load balancing considers task effort estimates

## Data Integrity Tests

### DATA-001: Concurrent State Modifications

**Scenario**: Multiple agents attempt to modify task state simultaneously

**Setup**:
- Task in IN_PROGRESS state
- Agent A attempts to mark COMPLETED
- Agent B attempts to mark BLOCKED (race condition)
- File system operations overlap

**Execution Steps**:
1. Both agents read current task state
2. Both prepare state transition modifications
3. Agent A writes COMPLETED state first
4. Agent B attempts to write BLOCKED state
5. System detects version conflict
6. Appropriate conflict resolution applied

**Success Criteria**:
- ✅ Final state is consistent and valid
- ✅ No intermediate corrupted states
- ✅ Conflicting modifications properly resolved
- ✅ Both agents notified of final state
- ✅ Audit log shows complete transaction history

### DATA-002: Dependency Cycle Detection

**Scenario**: Complex dependency modifications create circular references

**Setup**:
- Project with 100 tasks and complex dependency web
- Administrative changes to dependencies
- Some changes introduce cycles

**Execution Steps**:
1. Load project with existing dependencies
2. Add new dependency: Task A depends on Task B
3. Later add: Task B depends on Task C
4. Finally add: Task C depends on Task A (creates cycle)
5. System detects cycle before persisting
6. Reject modification with clear error message

**Success Criteria**:
- ✅ Cycle detected before persistence
- ✅ Clear error message with cycle path
- ✅ Suggestions for breaking cycle provided
- ✅ Data integrity maintained (no partial writes)
- ✅ Performance acceptable for large projects (<5s)

### DATA-003: File Corruption Recovery

**Scenario**: Task file becomes corrupted due to system crash

**Setup**:
- Project with 200 tasks persisted in JSON files
- Simulate system crash during file write operation
- Partial/corrupted task file on disk

**Execution Steps**:
1. System starts and detects corrupted task file
2. Attempts to parse file, fails with JSON error
3. Looks for backup/previous version in git history
4. Restores from last known good state
5. Reports data loss and recovery actions to user

**Success Criteria**:
- ✅ Corruption detected on startup
- ✅ Recovery attempted automatically
- ✅ Last known good state restored
- ✅ User notified of any data loss
- ✅ System functional after recovery

## Performance and Scale Tests

### PERF-001: Large Project Handling

**Scenario**: Project with 1000+ tasks and complex dependencies

**Setup**:
- Generate project with 1000 tasks across 6 levels
- 200+ cross-dependencies between tasks
- 12 different capability types required

**Execution Steps**:
1. Load complete project structure from disk
2. Analyze dependency graph for bottlenecks
3. Assign tasks to 10 concurrent agents
4. Track memory usage and response times
5. Complete 100 tasks with state transitions

**Performance Requirements**:
- ✅ Project load time <30 seconds
- ✅ Memory usage <1GB for full project
- ✅ Dependency analysis <10 seconds
- ✅ Task assignment <5 seconds per batch
- ✅ State transitions <100ms each

### PERF-002: Concurrent Agent Limits

**Scenario**: Stress test with maximum concurrent agents

**Setup**:
- Project with 500 available tasks
- 20 agents attempting to work simultaneously
- Network delays and processing variations simulated

**Execution Steps**:
1. Start 20 agents requesting work
2. System processes all requests concurrently
3. Monitor file I/O contention and locking
4. Track assignment fairness and efficiency
5. Measure system degradation points

**Performance Requirements**:
- ✅ Support 20 concurrent agents without deadlock
- ✅ Assignment fairness variance <15%
- ✅ File I/O errors <1% of operations
- ✅ Average response time <2 seconds
- ✅ System remains stable under load

### PERF-003: Git Operations Under Load

**Scenario**: Frequent git commits with concurrent modifications

**Setup**:
- High-frequency task completions (5 per minute)
- Each completion triggers git commit
- Multiple agents working simultaneously

**Execution Steps**:
1. Configure auto-commit for task completions
2. Start 8 agents completing tasks rapidly
3. Monitor git operation performance
4. Track commit conflicts and resolutions
5. Verify git history integrity

**Performance Requirements**:
- ✅ Git commits complete <5 seconds each
- ✅ No git conflicts or corruption
- ✅ History maintains chronological order
- ✅ Branch operations don't block agents
- ✅ Repository size growth reasonable

## Integration Tests

### INT-001: Amplifier Task Tool Integration

**Scenario**: Super-planner spawns agents using amplifier's Task tool

**Setup**:
- Amplifier environment with Task tool available
- Project requiring Python and TypeScript agents
- Mock agent implementations in catalog

**Execution Steps**:
1. System identifies tasks needing external agents
2. Use Task tool to spawn appropriate agents
3. Monitor agent communication and coordination
4. Track task progress from external agents
5. Handle agent failures and respawning

**Success Criteria**:
- ✅ Agents spawned successfully via Task tool
- ✅ Communication protocols work correctly
- ✅ Task progress updates received
- ✅ Failed agents automatically respawned
- ✅ Integration feels seamless to users

### INT-002: CCSDK Defensive Utilities Integration

**Scenario**: Use defensive utilities for robust LLM and file operations

**Setup**:
- Task breakdown requiring LLM calls
- File operations with cloud sync delays
- Network intermittency simulation

**Execution Steps**:
1. Task breakdown calls LLM for complex planning
2. Use parse_llm_json() for response parsing
3. File operations use retry_with_feedback()
4. Network issues trigger defensive patterns
5. System remains stable throughout

**Success Criteria**:
- ✅ LLM response parsing never fails
- ✅ File operations survive cloud sync delays
- ✅ Network issues handled gracefully
- ✅ No system crashes or data corruption
- ✅ User experience remains smooth

### INT-003: Git Workflow Compatibility

**Scenario**: Super-planner integrates with amplifier's git patterns

**Setup**:
- Amplifier project with existing git workflow
- Super-planner operating in same repository
- Multiple developers working simultaneously

**Execution Steps**:
1. Initialize planner in existing amplifier project
2. Planner creates commits following project conventions
3. External developers make concurrent changes
4. Planner handles merge conflicts appropriately
5. Git history remains clean and meaningful

**Success Criteria**:
- ✅ Commit messages follow project conventions
- ✅ No conflicts with external git workflow
- ✅ Branch management works correctly
- ✅ Merge conflicts resolved appropriately
- ✅ Git history helpful for debugging

## Failure Scenario Tests

### FAIL-001: Network Partition During Coordination

**Scenario**: Network issues prevent agent communication

**Setup**:
- 5 agents working across network partitions
- Tasks with complex interdependencies
- Simulate network splits and healing

**Execution Steps**:
1. Agents begin coordinated work on project
2. Network partition separates 2 agents from others
3. Isolated agents continue local work
4. Network heals after 10 minutes
5. System reconciles conflicting states

**Success Criteria**:
- ✅ Isolated agents don't block others
- ✅ Work continues on both sides of partition
- ✅ State reconciliation successful after healing
- ✅ No work lost due to partition
- ✅ Dependencies still respected after reconciliation

### FAIL-002: Disk Full During Operations

**Scenario**: File system runs out of space during task operations

**Setup**:
- Large project with extensive task data
- Disk space artificially limited
- Operations trigger disk full condition

**Execution Steps**:
1. Begin large task breakdown operation
2. Disk space exhausted mid-operation
3. System detects write failures
4. Gracefully degrade functionality
5. Resume when space available

**Success Criteria**:
- ✅ Write failures detected immediately
- ✅ Partial operations rolled back cleanly
- ✅ System remains stable despite failures
- ✅ Clear error messages provided to user
- ✅ Automatic recovery when space available

### FAIL-003: Corrupted Task Dependencies

**Scenario**: Task dependency data becomes corrupted

**Setup**:
- Project with complex dependency web
- Simulate data corruption in dependency files
- Some dependencies point to non-existent tasks

**Execution Steps**:
1. Load project with corrupted dependencies
2. System detects invalid references
3. Attempt to reconstruct valid dependency graph
4. Isolate corrupted tasks if necessary
5. Continue operations with partial data

**Success Criteria**:
- ✅ Corruption detected on load
- ✅ Invalid dependencies identified
- ✅ Partial recovery attempted
- ✅ System remains functional
- ✅ Recovery actions logged for debugging

## Success Metrics

Each test scenario must meet these comprehensive success criteria:

### Functional Correctness
- All specified behaviors work as documented
- Edge cases handled appropriately
- Error conditions fail gracefully
- Data integrity maintained under all conditions

### Performance Acceptability
- Response times within specified limits
- Memory usage within reasonable bounds
- Concurrent operations scale appropriately
- Degradation is graceful under load

### Reliability Standards
- 99.9% success rate on valid operations
- Automatic recovery from transient failures
- No data corruption under any circumstances
- Consistent behavior across multiple runs

### User Experience Quality
- Clear error messages with actionable guidance
- Visible progress indicators for long operations
- Predictable behavior that matches user expectations
- Seamless integration with existing amplifier workflow

These test scenarios ensure the super-planner system is robust, reliable, and ready for production use before any implementation begins.