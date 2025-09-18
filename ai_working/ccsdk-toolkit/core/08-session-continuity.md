# Core Improvement: Session Continuity

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🟢 Valuable (P3)

## Problem Statement

The toolkit has a sessions module but it's not integrated with the core session functionality. The module generator returns session_id which could enable resumption of interrupted work.

## Current Implementation

```python
# Sessions module exists but disconnected from core
# No session_id returned from queries
# No way to resume an interrupted session
```

## Proposed Solution

### Integrate Session Persistence

```python
# ccsdk_toolkit/core/session.py
from ..sessions import SessionManager

class ClaudeSession:
    def __init__(self, options: SessionOptions | None = None,
                 session_id: str | None = None):
        """Initialize with optional session resumption."""
        self.options = options or SessionOptions()
        self.session_id = session_id
        self.session_manager = SessionManager() if session_id else None
        self.conversation_history = []

        # Load previous conversation if resuming
        if session_id and self.session_manager:
            saved_session = self.session_manager.load_session(session_id)
            if saved_session:
                self.conversation_history = saved_session.messages
                # Restore options if not provided
                if not options and saved_session.metadata.config:
                    self.options = SessionOptions(**saved_session.metadata.config)

    async def query(self, prompt: str) -> SessionResponse:
        # ... execute query ...

        # Save to session if tracking
        if response.session_id and not self.session_id:
            self.session_id = response.session_id
            self.session_manager = SessionManager()

        if self.session_manager and self.session_id:
            # Create or update session
            session = self.session_manager.load_session(self.session_id) or \
                      self.session_manager.create_session(
                          name=f"session_{self.session_id[:8]}",
                          session_id=self.session_id
                      )

            # Add conversation turn
            session.add_message("user", prompt)
            session.add_message("assistant", response.content)
            session.metadata.total_cost = response.metadata.total_cost_usd
            session.metadata.total_duration_ms = response.metadata.duration_ms

            # Save session
            self.session_manager.save_session(session)

        return response
```

### Add Resumption Support

```python
# ccsdk_toolkit/core/utils.py
async def resume_session(session_id: str) -> ClaudeSession | None:
    """Resume a previous session by ID."""
    manager = SessionManager()
    saved_session = manager.load_session(session_id)

    if not saved_session:
        return None

    # Restore session with saved configuration
    options = SessionOptions(**saved_session.metadata.config) \
              if saved_session.metadata.config else SessionOptions()

    return ClaudeSession(options=options, session_id=session_id)

async def continue_conversation(session_id: str, prompt: str) -> SessionResponse:
    """Continue a previous conversation."""
    session = await resume_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    async with session:
        # Include conversation history in context
        full_prompt = _build_continuation_prompt(
            session.conversation_history,
            prompt
        )
        return await session.query(full_prompt)
```

## Usage Patterns

### Pattern 1: Auto-Save Sessions

```python
options = SessionOptions(
    system_prompt="Complex analysis agent",
    max_turns=40
)

async with ClaudeSession(options) as session:
    response = await session.query("Analyze this codebase...")

    # Session automatically saved with ID
    print(f"Session saved as: {response.session_id}")

# Later, resume the session
async with await resume_session(response.session_id) as session:
    response = await session.query("Continue the analysis...")
```

### Pattern 2: Explicit Session Management

```python
manager = SessionManager()

# Create named session
session_obj = manager.create_session(
    name="module_generation_2024_01",
    tags=["generation", "module_x"]
)

async with ClaudeSession(session_id=session_obj.metadata.session_id) as session:
    # Work is automatically saved to the session
    response = await session.query("Generate module...")

# List sessions
recent_sessions = manager.list_sessions(tags=["generation"])
for s in recent_sessions:
    print(f"{s.metadata.name}: ${s.metadata.total_cost:.2f}")
```

### Pattern 3: Checkpointing Long Operations

```python
async def long_operation_with_checkpoints(prompts: list[str]):
    """Execute long operation with resumption support."""
    checkpoint_file = Path("operation_checkpoint.json")

    # Load checkpoint if exists
    start_index = 0
    session_id = None
    if checkpoint_file.exists():
        checkpoint = json.loads(checkpoint_file.read_text())
        start_index = checkpoint["completed"]
        session_id = checkpoint["session_id"]

    # Resume or create session
    session = await resume_session(session_id) if session_id else \
              ClaudeSession(SessionPresets.GENERATION)

    async with session:
        for i, prompt in enumerate(prompts[start_index:], start_index):
            response = await session.query(prompt)

            # Save checkpoint
            checkpoint_file.write_text(json.dumps({
                "completed": i + 1,
                "session_id": response.session_id or session_id,
                "last_response": response.content[:500]
            }))

    # Clean up checkpoint on success
    checkpoint_file.unlink()
```

## Testing Requirements

- Test session save and restore
- Verify conversation history is preserved
- Test resumption after interruption
- Ensure costs accumulate correctly

## Migration Impact

- Existing code continues to work without sessions
- Opt-in session persistence
- Examples should show resumption patterns

## Success Criteria

- Interrupted work can be resumed
- Session history provides context
- Costs tracked across session lifetime
- Clear patterns for checkpointing

## Module Generator Insight

The generator always returns session_id, enabling potential resumption:
```python
return ClaudeRunResult(text, session_id, total_cost, duration_ms)
```

This simple pattern enables powerful continuity features.