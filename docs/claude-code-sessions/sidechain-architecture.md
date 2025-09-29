# Sidechain Architecture

## Definition

Sidechains are inline message sequences within Claude Code JSONL session files where Claude delegates tasks to specialized AI agents. They are marked by `isSidechain: true` and represent sub-agent conversations embedded within the main conversation flow.

## Message Structure

### Sidechain Markers

```json
{
  "isSidechain": true,          // Required sidechain marker
  "userType": "external",       // Claude acting as user
  "type": "user"|"assistant",   // Role within sidechain
  "parentUuid": "...",          // Links to parent message
  "sessionId": "...",           // Session context
}
```

### Role Semantics

| Message Type | Main Conversation | Sidechain Context |
|--------------|-------------------|-------------------|
| `user` | Human input | Claude delegating |
| `assistant` | Claude response | Sub-agent response |
| `userType: "external"` | Not applicable | Claude as user |

## Agent Identification

### Task Tool Correlation

Agent names are extracted from the `Task` tool invocation that precedes each sidechain:

```json
// Task tool invocation
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {
        "type": "tool_use",
        "id": "toolu_01KHFXvQPSoUtUMPeVdMdXKp",
        "name": "Task",
        "input": {
          "subagent_type": "bug-hunter",  // Agent identifier
          "prompt": "Analyze this code for bugs"
        }
      }
    ]
  },
  "uuid": "task-123"
}

// Sidechain first message - exact prompt match
{
  "type": "user",
  "isSidechain": true,
  "userType": "external",
  "message": {
    "role": "user",
    "content": "Analyze this code for bugs"  // Matches Task input.prompt
  },
  "parentUuid": "task-123"
}
```

### Agent Matching Algorithm

```python
def match_task_to_sidechain(task_tool, sidechain_first_msg):
    """Match Task tool to its sidechain."""
    task_prompt = task_tool['input']['prompt']
    sc_content = sidechain_first_msg.get('message', {})
    if isinstance(sc_content, dict):
        sc_text = sc_content.get('content', '')
    else:
        sc_text = str(sc_content)
    return task_prompt == sc_text  # Exact match required
```

## Specialized Agents

| Agent Type | Purpose |
|------------|---------|
| `zen-architect` | System architecture design |
| `bug-hunter` | Bug detection and analysis |
| `modular-builder` | Modular code construction |
| `test-coverage` | Test case generation |
| `refactor-architect` | Code refactoring strategies |
| `integration-specialist` | System integration design |
| `synthesis-master` | Knowledge synthesis |
| `subagent-architect` | Agent creation |

## Sidechain Lifecycle

### Execution Flow

1. Claude evaluates task complexity
2. Claude invokes `Task` tool with `subagent_type` parameter
3. First sidechain message marked with `isSidechain: true`
4. Claude becomes user (`userType: "external"`)
5. Sub-agent processes and responds
6. Optional multi-turn exchanges
7. Sidechain ends when `isSidechain` flag absent
8. Claude integrates results into main response

### Execution Patterns

#### Single Task Invocation

```json
{
  "message": {
    "content": [
      {
        "type": "tool_use",
        "name": "Task",
        "input": {"subagent_type": "zen-architect", "prompt": "Design the architecture"}
      }
    ]
  }
}
```

#### Parallel Task Execution

```json
{
  "message": {
    "content": [
      {"type": "tool_use", "name": "Task", "input": {"subagent_type": "bug-hunter", ...}},
      {"type": "tool_use", "name": "Task", "input": {"subagent_type": "test-coverage", ...}}
    ]
  }
}
```

Results return in completion order, not invocation order.

## DAG Structure

Sidechains maintain parent-child relationships forming a directed acyclic graph:

```
Main Conversation
├── Message 1 (user)
├── Message 2 (assistant)
│   └── Sidechain A
│       ├── SC-A1 (user/Claude)
│       ├── SC-A2 (assistant/agent)
│       └── SC-A3 (assistant/agent)
├── Message 3 (assistant)
└── Message 4 (assistant)
    ├── Sidechain B
    └── Sidechain C
```

### Nested Sidechains

Agents can invoke other agents:

```json
// Level 0: Main conversation
{"type": "assistant", "uuid": "main-1"}

// Level 1: Claude → zen-architect
{"type": "user", "uuid": "sc1-1", "parentUuid": "main-1", "isSidechain": true}
{"type": "assistant", "uuid": "sc1-2", "parentUuid": "sc1-1", "isSidechain": true}

// Level 2: zen-architect → modular-builder
{"type": "user", "uuid": "sc2-1", "parentUuid": "sc1-2", "isSidechain": true, "nestingLevel": 2}
{"type": "assistant", "uuid": "sc2-2", "parentUuid": "sc2-1", "isSidechain": true, "nestingLevel": 2}
```

## Parser Implementation

### Sidechain Extraction

```python
def extract_sidechains(messages):
    """Extract all sidechains with agent identification."""
    sidechains = []
    current_sidechain = []
    agent_name = None
    task_invocations = {}

    for msg in messages:
        # Track Task tool invocations
        if msg.get('message') and isinstance(msg['message'], dict):
            content = msg['message'].get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'tool_use' and item.get('name') == 'Task':
                        task_id = msg.get('uuid')
                        agent_name = item.get('input', {}).get('subagent_type', 'unknown')
                        task_prompt = item.get('input', {}).get('prompt', '')
                        task_invocations[task_id] = {
                            'agent': agent_name,
                            'prompt': task_prompt,
                            'timestamp': msg.get('timestamp')
                        }

        # Process sidechain messages
        if msg.get('isSidechain'):
            if not current_sidechain:
                # Starting new sidechain - find corresponding task
                parent_uuid = msg.get('parentUuid')
                if parent_uuid in task_invocations:
                    agent_name = task_invocations[parent_uuid]['agent']

            current_sidechain.append(msg)

        elif current_sidechain:
            # Sidechain ended
            sidechains.append({
                'agent': agent_name or 'unknown',
                'messages': current_sidechain,
                'depth': len(current_sidechain)
            })
            current_sidechain = []
            agent_name = None

    # Handle unclosed sidechain
    if current_sidechain:
        sidechains.append({
            'agent': agent_name or 'unknown',
            'messages': current_sidechain,
            'incomplete': True
        })

    return sidechains
```

### Role Identification

```python
def parse_message(msg):
    if msg.get('isSidechain'):
        # In sidechain context
        if msg['type'] == 'user':
            actor = 'Claude'  # Claude speaking to sub-agent
        else:
            actor = 'SubAgent'  # Sub-agent responding
    else:
        # Main conversation
        if msg['type'] == 'user':
            actor = 'Human'
        else:
            actor = 'Claude'
    return actor
```

## Multi-Turn Patterns

### Progressive Refinement

```
Claude: "Analyze this code"
Agent: "Initial analysis..."
Claude: "Look deeper at the database layer"
Agent: "Database analysis..."
Claude: "Check for SQL injection vulnerabilities"
Agent: "Security scan results..."
```

### Clarification Requests

```
Claude: "Generate test cases"
Agent: "What testing framework?"
Claude: "Use pytest"
Agent: "Generated pytest cases..."
```

### Error Recovery

```
Claude: "Parse this file"
Agent: "Error: File not found"
Claude: "The file is at /correct/path/file.py"
Agent: "Successfully parsed..."
```

## Tool Usage Within Sidechains

Agents use tools within sidechain context:

```json
{
  "type": "assistant",
  "isSidechain": true,
  "subtype": "tool_use",
  "toolName": "Read",
  "toolArguments": {"file_path": "/src/main.py"},
  "uuid": "sc-tool-1"
}
```

## Implementation Requirements

### Parser Requirements

1. Track `isSidechain` flag state
2. Handle role reversal semantics
3. Maintain parent-child relationships across boundaries
4. Track Task tool invocations for agent identification
5. Group consecutive sidechain messages
6. Support parallel sidechain detection

### Analysis Requirements

1. Separate main and sidechain message threads
2. Track delegation patterns by agent type
3. Calculate conversation depth metrics
4. Measure agent invocation frequency
5. Analyze multi-turn conversation patterns

### Reconstruction Requirements

1. Maintain context boundaries between main and sidechain
2. Preserve chronological message order
3. Display role reversal clearly in output
4. Link sidechains to initiating Task tools
5. Handle incomplete or orphaned sidechains