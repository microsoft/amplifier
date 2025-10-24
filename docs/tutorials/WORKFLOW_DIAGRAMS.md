# Workflow Diagrams

This document provides visual workflow diagrams for the Codex integration, illustrating key processes and architectures. All diagrams use Mermaid syntax and can be viewed live in the [Mermaid Live Editor](https://mermaid.live/).

## 1. Session Lifecycle

This flowchart shows the complete session lifecycle when using the wrapper script, highlighting automatic vs manual steps.

```mermaid
flowchart TD
    A[User runs ./amplify-codex.sh] --> B{Validate Prerequisites}
    B --> C[Auto: Load memories via initialize_session]
    C --> D[Auto: Start Codex with MCP servers]
    D --> E[Manual: User works in Codex session]
    E --> F[Manual: Use MCP tools as needed]
    F --> G[User exits Codex Ctrl+D]
    G --> H[Auto: Extract memories via finalize_session]
    H --> I[Auto: Export transcript]
    I --> J[Auto: Cleanup temporary files]
    J --> K[Display summary to user]

    style A fill:#e1f5fe
    style C fill:#c8e6c9
    style D fill:#c8e6c9
    style H fill:#c8e6c9
    style I fill:#c8e6c9
    style J fill:#c8e6c9
    style K fill:#c8e6c9
```

**Key Points:**
- **Blue nodes**: User-triggered actions
- **Green nodes**: Automatic wrapper script actions
- Memory loading and extraction happen automatically
- MCP servers run in background during session

## 2. MCP Server Architecture

This sequence diagram illustrates how Codex communicates with MCP servers and how they integrate with Amplifier modules.

```mermaid
sequenceDiagram
    participant U as User
    participant C as Codex CLI
    participant M as MCP Server (stdio)
    participant A as Amplifier Module

    Note over C,M: MCP Server Process Started
    C->>M: Initialize (JSON-RPC)
    M-->>C: Server capabilities

    U->>C: Use MCP tool (e.g., check_code_quality)
    C->>M: Tool call (JSON-RPC)
    M->>A: Call Amplifier function
    A-->>M: Return result
    M-->>C: Tool response (JSON-RPC)
    C-->>U: Display result

    Note over M,A: Example: task_tracker server calls task storage
```

**Communication Flow:**
- Codex spawns MCP server subprocess
- Communication via stdio using JSON-RPC protocol
- Servers call into Amplifier modules for business logic
- Results flow back through the same channel

## 3. Memory System Flow

This flowchart shows how the memory system operates throughout a session, from loading to extraction.

```mermaid
flowchart TD
    A[Session Start] --> B[Load Recent Memories]
    B --> C[Search Relevant Memories]
    C --> D[Format Context for Codex]
    D --> E[User Works in Session]
    E --> F[Generate New Content]
    F --> G[Extract Memories from Conversation]
    G --> H[Store New Memories]
    H --> I[Session End]

    B --> J[Memory Store]
    C --> J
    J --> K[Search Index]
    G --> L[Memory Extractor]
    L --> H

    style J fill:#fff3e0
    style K fill:#fff3e0
    style L fill:#fff3e0
```

**Memory Paths:**
- **Loading**: Recent + relevant memories from search
- **Storage**: Extracted memories stored in JSON files
- **Search**: Uses vector similarity for relevance
- **Extraction**: Analyzes conversation for memorable content

## 4. Quality Check Workflow

This sequence diagram shows the quality check process from code changes to result display.

```mermaid
sequenceDiagram
    participant U as User
    participant C as Codex
    participant M as MCP Server
    participant MF as Makefile
    participant T as Tools (ruff, pyright, pytest)

    U->>C: Modify code files
    U->>C: Run check_code_quality tool
    C->>M: check_code_quality(file_paths)
    M->>MF: make check
    MF->>T: Run linting (ruff)
    MF->>T: Run type checking (pyright)
    MF->>T: Run tests (pytest)
    T-->>MF: Results
    MF-->>M: Combined results
    M-->>C: Formatted results
    C-->>U: Display quality check summary

    Note over MF,T: Parallel execution of quality tools
```

**Integration Points:**
- MCP server calls `make check` target
- Makefile orchestrates individual tools
- Results aggregated and formatted for display
- Supports partial failures (some tools may fail while others succeed)

## 5. Agent Context Bridge

This sequence diagram illustrates the agent context bridge mechanism for seamless context handoff.

```mermaid
sequenceDiagram
    participant MS as Main Session
    participant CB as Context Bridge
    participant CF as Context File
    participant C as Codex CLI
    participant A as Agent Process
    participant AR as Agent Result

    MS->>CB: serialize_context(messages, task)
    CB->>CF: Write compressed context
    MS->>C: codex exec --agent name --context-file CF
    C->>A: Spawn agent with context
    A->>CF: Read context during execution
    A-->>C: Agent completes
    C->>CB: extract_agent_result(output)
    CB->>AR: Format and save result
    CB-->>MS: Return formatted result

    Note over CF: .codex/agent_context/session.json
    Note over AR: .codex/agent_results/agent_timestamp.md
```

**Context Handoff:**
- Main session context serialized to file
- Agent execution includes context file
- Results extracted and integrated back
- Supports token limits and compression

## 6. Backend Abstraction

This class diagram shows the backend abstraction architecture providing unified API across different backends.

```mermaid
classDiagram
    class AmplifierBackend {
        <<abstract>>
        +initialize_session(prompt, context)
        +finalize_session(messages, context)
        +run_quality_checks(file_paths, cwd)
        +export_transcript(session_id, format, output_dir)
        +manage_tasks(action, **kwargs)
        +search_web(query, num_results)
        +fetch_url(url)
        +get_capabilities()
        +get_backend_name()
        +is_available()
    }

    class ClaudeCodeBackend {
        +initialize_session(prompt, context)
        +finalize_session(messages, context)
        +run_quality_checks(file_paths, cwd)
        +export_transcript(session_id, format, output_dir)
        +manage_tasks(action, **kwargs)
        +search_web(query, num_results)
        +fetch_url(url)
        +get_capabilities()
        +get_backend_name()
        +is_available()
    }

    class CodexBackend {
        +initialize_session(prompt, context)
        +finalize_session(messages, context)
        +run_quality_checks(file_paths, cwd)
        +export_transcript(session_id, format, output_dir)
        +manage_tasks(action, **kwargs)
        +search_web(query, num_results)
        +fetch_url(url)
        +get_capabilities()
        +get_backend_name()
        +is_available()
    }

    class BackendFactory {
        +create_backend(backend_type)
        +get_available_backends()
        +auto_detect_backend()
        +get_backend_capabilities(backend_type)
    }

    AmplifierBackend <|-- ClaudeCodeBackend
    AmplifierBackend <|-- CodexBackend
    BackendFactory ..> AmplifierBackend
```

**Abstraction Benefits:**
- Unified API regardless of backend
- Easy switching via environment variables
- Backend-specific implementations hidden
- Extensible for future backends

---

**Viewing Diagrams Live:**
All diagrams can be copied and pasted into the [Mermaid Live Editor](https://mermaid.live/) for interactive viewing and editing. The live editor provides real-time rendering and allows you to experiment with diagram modifications.

**Diagram Legend:**
- **Flowcharts**: Show process flows and decision points
- **Sequence Diagrams**: Illustrate interactions between components over time
- **Class Diagrams**: Show object-oriented relationships and interfaces

These diagrams provide a comprehensive visual overview of the Codex integration architecture and workflows.