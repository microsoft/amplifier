# Module: context
# Purpose: Inject philosophy context cleanly into prompts

PHILOSOPHY_CONTEXT = """
IMPORTANT: Follow these amplifier tool principles:

1. **Ruthless Simplicity**: Keep everything as simple as possible, but no simpler
   - Minimize abstractions
   - Start minimal, grow as needed
   - Avoid future-proofing

2. **Code for Structure, AI for Intelligence**:
   - Use code for reliable iteration and state management
   - Use AI for complex reasoning and creative tasks
   - Incremental saves after EVERY operation for resume capability

3. **Modular Design (Bricks & Studs)**:
   - Self-contained modules with clear interfaces
   - Each module does ONE thing well
   - Regenerate don't patch - rebuild modules from specs

4. **Zero Placeholder/Stub Code**:
   - Every function must work or not exist
   - No TODOs without implementation
   - No raise NotImplementedError (except abstract base classes)

Reference: @ai_context/IMPLEMENTATION_PHILOSOPHY.md and @ai_context/MODULAR_DESIGN_PHILOSOPHY.md
"""


def inject_philosophy(prompt: str, stage_name: str = None) -> str:
    """Inject philosophy context into a prompt."""

    # Stage-specific additions
    stage_context = {
        "code_generation": "\nFocus especially on: Working code with no stubs, incremental saves, clear modular structure.",
        "test_generation": "\nFocus especially on: Test what matters, avoid over-testing, clear test names.",
        "design": "\nFocus especially on: Simple architecture, minimal abstractions, clear data flow.",
    }

    additional = stage_context.get(stage_name, "")

    return f"{PHILOSOPHY_CONTEXT}{additional}\n\n---\n\n{prompt}"


def get_context_for_stage(stage_name: str) -> str:
    """Get specific context for a stage."""
    contexts = {
        "requirements": "Extract clear, measurable requirements. Avoid vague or future-looking items.",
        "design": "Design for current needs, not hypothetical futures. Prefer simple patterns.",
        "implementation": "Break into small, testable tasks. Each task should produce working code.",
        "code_generation": "Generate complete, working code. No stubs or placeholders.",
        "test_generation": "Test critical paths. Avoid testing implementation details.",
    }

    return contexts.get(stage_name, "")
