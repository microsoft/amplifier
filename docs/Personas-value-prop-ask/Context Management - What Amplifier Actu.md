 Context Management - What Amplifier Actually Offers

  After reviewing the entire repo, "Context Management" in Amplifier is actually multiple
  distinct systems working together. Let me break them down:

  1. Transcript Preservation & Restoration

  What It Is:

  When Claude Code compacts a conversation (summarizes and deletes detail), Amplifier saves
  the full transcript before it's lost.

  How It Works:

  Claude Code sends PreCompact event
    ↓
  hook_precompact.py captures full conversation
    ↓
  Saves to .data/transcripts/compact_TIMESTAMP_SESSIONID.txt
    ↓
  Later: /transcript command restores full history

  The Commands:

  # Restore full conversation after compaction
  /transcript

  # Or via CLI
  python tools/transcript_manager.py restore

  Real Problem Solved:

  Claude Code compaction is lossy - you lose detailed context. Amplifier preserves it.

  But Honestly:

  - How often does this happen? Depends on conversation length
  - Do you actually need the full history? Maybe not if summary is good enough
  - Could you just scroll up? Not after compaction - it's gone

  When Actually Useful:

  - Long sessions where you need to reference earlier decisions
  - Debugging conversations to see what went wrong
  - Compliance/documentation needs
  - Recovering context after compaction

  When It's Overhead:

  - Short conversations that don't compact
  - You don't need historical detail
  - Summaries are sufficient

  ---
  2. Memory System (Extracting Learnings)

  What It Is:

  Extracts key learnings, decisions, and patterns from conversations and stores them
  persistently across sessions.

  How It Works:

  Conversation ends (Stop event)
    ↓
  hook_stop.py extracts memories
    ↓
  Categories: learning, decision, issue_solved, pattern, context
    ↓
  Saves to .data/memories/memory.json
    ↓
  Next session: hook_session_start.py retrieves relevant memories

  What It Captures:

  - Learnings: "User prefers TypeScript over JavaScript"
  - Decisions: "Chose PostgreSQL for data persistence"
  - Issues Solved: "Fixed CORS error by adding origin header"
  - Patterns: "User always wants tests written first"

  But This Is:

  - DISABLED by default - You have to set MEMORY_SYSTEM_ENABLED=true
  - Pattern-based extraction (keyword matching) as fallback
  - Opt-in, not automatic

  Real Problem Solved:

  Claude Code forgets project-specific preferences, decisions, and learnings across sessions.

  When Actually Useful:

  - Long-term projects with many sessions
  - Team environments where decisions matter
  - You want AI to "remember" your preferences
  - Avoiding re-explaining the same things

  When It's Overhead:

  - Short projects
  - You don't mind re-explaining
  - Generic help is fine
  - Solo, inconsistent work

  ---
  3. AI Context Files (Project Documentation for AI)

  What It Is:

  The ai_context/ directory contains documentation specifically for AI consumption:
  - generated/ - Auto-generated project file roll-ups
  - Philosophy documents (IMPLEMENTATION_PHILOSOPHY.md, MODULAR_DESIGN_PHILOSOPHY.md)
  - Library documentation for reference

  How It Works:

  @ai_context/IMPLEMENTATION_PHILOSOPHY.md
  # Claude Code reads these files into context
  # All subsequent interactions follow these principles

  Real Problem Solved:

  "How do I tell Claude Code about MY project's way of doing things?"

  But Honestly:

  - This is just documentation in a designated place
  - You could do this anywhere (README.md, docs/, etc.)
  - The ai_context/ convention just makes it clear "this is for AI"

  When Actually Useful:

  - You have established patterns/philosophy
  - Team wants AI consistency
  - Complex projects with specific approaches

  When It's Overhead:

  - Small/simple projects
  - No established patterns yet
  - Generic approach is fine

  ---
  4. Session Management (For Scenario Tools)

  What It Is:

  The ccsdk_toolkit/sessions/ module provides session persistence for CLI tools that use
  Claude Code SDK.

  How It Works:

  from amplifier.ccsdk_toolkit import SessionManager

  manager = SessionManager()
  session = manager.create_session("my-task")
  session.add_message("user", "Do something")
  manager.save_session(session)

  # Later...
  resumed = manager.load_session(session_id)

  Real Problem Solved:

  Building CLI tools that can be interrupted and resumed.

  When Actually Useful:

  - You're building AI-powered CLI tools
  - Tasks take a long time
  - Need to interrupt and continue
  - Want to review conversation history

  When It's Overhead:

  - Not building CLI tools
  - Tasks are quick
  - Don't need resumability

  ---
  5. State Persistence (For Scenario Tools)

  What It Is:

  Each scenario tool (blog-writer, transcribe, etc.) has state management:
  - Tracks progress through multi-stage pipelines
  - Saves after each stage
  - Can resume from interruption

  How It Works:

  # In blog_writer/state.py
  state = BlogWriterState.load()  # Load from disk if exists
  state.current_stage = "drafting"
  state.save()  # Persists to .data/blog_writer/state.json

  # After interruption
  state = BlogWriterState.load()  # Picks up where it left off

  Real Problem Solved:

  Long-running AI workflows that crash or get interrupted lose all progress.

  When Actually Useful:

  - Multi-stage AI pipelines
  - Tasks that take 10+ minutes
  - Unreliable environments
  - Want to pause and continue

  When It's Overhead:

  - Quick tasks
  - Reliable environment
  - Single-shot operations

  ---
  The Honest Assessment

  Context Management is Actually 5 Different Things:

  1. Transcript preservation - Save conversations before compaction
  2. Memory extraction - Remember learnings across sessions (disabled by default)
  3. AI context files - Documentation for AI consumption
  4. Session management - For building resumable CLI tools
  5. State persistence - For multi-stage workflows

  When You Need Them:

  | Feature     | When Useful                            | When Overhead          |
  |-------------|----------------------------------------|------------------------|
  | Transcripts | Long sessions, need history            | Short conversations    |
  | Memory      | Long-term projects, preferences matter | One-off work           |
  | AI Context  | Established patterns, team consistency | Generic approach fine  |
  | Sessions    | Building CLI tools                     | Just using Claude Code |
  | State       | Long multi-stage workflows             | Quick tasks            |

  The Real Value:

  If you're:
  - Just coding with Claude Code → You don't need most of this
  - Building AI-powered tools → Session/state management is genuinely useful
  - Working on long-term projects → Memory + transcripts help
  - On a team with patterns → AI context files provide consistency

  The uncomfortable truth:
  Most of these features are solving problems that only exist for specific use cases:
  - Transcript preservation: Only matters if you hit compaction
  - Memory: Only useful for long-term project work
  - AI context: Only valuable if you have patterns to encode
  - Sessions/State: Only needed if you're building tools

  ---
  My Honest Take

  Context Management sounds like one feature but it's actually:
  - A grab bag of different solutions
  - For different problems
  - That most people won't have

  The positioning problem:
  The README says "Context Management" like it's a single coherent feature. But it's really:
  1. Backup system for compaction (niche)
  2. Learning extraction system (disabled by default!)
  3. Documentation convention (just a folder)
  4. Infrastructure for building tools (only if you build tools)
  5. State machines for workflows (only if you have workflows)

  Better positioning would be:
  "Building AI-powered CLI tools? Get session management, state persistence, and resumability
  for free.

  Working on long-term projects? Extract learnings and preserve conversation history.

  Team with established patterns? Encode them in ai_context/ for consistent AI behavior."

  But saying "Context Management" makes it sound like one thing when it's five different
  things solving five different problems.