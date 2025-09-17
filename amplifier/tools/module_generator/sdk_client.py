from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    # Claude Code SDK (declared in project pyproject)
    from claude_code_sdk import AssistantMessage
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
    from claude_code_sdk import ClaudeSDKError
    from claude_code_sdk import CLINotFoundError
    from claude_code_sdk import ProcessError
    from claude_code_sdk import ResultMessage
    from claude_code_sdk import TextBlock
except Exception:
    ClaudeSDKClient = None  # type: ignore
    ClaudeCodeOptions = None  # type: ignore
    AssistantMessage = None  # type: ignore
    ResultMessage = None  # type: ignore
    TextBlock = None  # type: ignore
    CLINotFoundError = Exception  # type: ignore
    ProcessError = Exception  # type: ignore
    ClaudeSDKError = Exception  # type: ignore


def _ensure_sdk_available() -> None:
    """Ensure the Claude SDK is available. Raises RuntimeError if not."""
    if ClaudeSDKClient is None:
        raise RuntimeError(
            "claude_code_sdk is not available. Ensure it's installed and importable in this environment.\n"
            "Dependency is declared in the repo's pyproject; install via `make install`."
        )


async def _stream_all_messages(client: Any) -> tuple[str, str | None, float, int]:
    """Collects streamed assistant text, returns (text, session_id, total_cost_usd, duration_ms)."""
    collected = []
    session_id = None
    total_cost = 0.0
    duration_ms = 0
    async for msg in client.receive_response():
        # Print any textual content while collecting
        if AssistantMessage is not None and isinstance(msg, AssistantMessage):
            for block in getattr(msg, "content", []) or []:
                if TextBlock is not None and isinstance(block, TextBlock):
                    text = getattr(block, "text", "")
                    if text:
                        print(text, end="", flush=True)
                        collected.append(text)
        if ResultMessage is not None and isinstance(msg, ResultMessage):
            # Final stats
            total_cost = getattr(msg, "total_cost_usd", 0.0) or 0.0
            duration_ms = getattr(msg, "duration_ms", 0) or 0
            session_id = getattr(msg, "session_id", None)
    print("", flush=True)
    return ("".join(collected), session_id, total_cost, duration_ms)


def _default_system_prompt() -> str:
    return (
        "You are the Modular Builder for the Amplifier repo.\n"
        "Follow contract-first, 'bricks & studs', and regeneration over patching.\n"
        "Use concise, explicit steps. Respect repo conventions and tests."
    )


async def plan_from_specs(
    contract_text: str,
    impl_text: str,
    cwd: str,
    add_dirs: list[str | Path] | None = None,
    settings: str | None = None,
) -> tuple[str, str | None, float, int]:  # pyright: ignore[reportReturnType]
    """Ask Claude to produce a concrete implementation plan (READ-ONLY)."""
    _ensure_sdk_available()
    if add_dirs is None:
        add_dirs = []
    prompt = (
        "You are in PLANNING phase. Do NOT write or edit files.\n"
        "Given the following module contract and implementation spec, output a precise, actionable plan.\n"
        "Include: file tree to create, key functions/classes, test plan, and acceptance checks.\n"
        "Return clear, stepwise instructions.\n\n"
        "=== CONTRACT ===\n" + contract_text + "\n\n"
        "=== IMPLEMENTATION SPEC ===\n" + impl_text + "\n\n"
        "End of inputs."
    )
    assert ClaudeSDKClient is not None  # Type guard for pyright
    assert ClaudeCodeOptions is not None  # Type guard for pyright

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt=_default_system_prompt(),
            cwd=cwd,
            add_dirs=add_dirs,
            settings=settings,
            # Plan mode not supported; emulate read-only by restricting tools.
            allowed_tools=["Read", "Grep"],
            permission_mode="default",
            max_turns=3,
        )
    ) as client:
        await client.query(prompt)
        return await _stream_all_messages(client)


async def generate_from_specs(
    contract_text: str,
    impl_text: str,
    module_name: str,
    module_dir_rel: str,
    cwd: str,
    add_dirs: list[str | Path] | None = None,
    settings: str | None = None,
) -> tuple[str | None, float, int]:  # pyright: ignore[reportReturnType]
    """Ask Claude to IMPLEMENT the module by creating files in the repo (WRITE-ENABLED)."""
    _ensure_sdk_available()
    if add_dirs is None:
        add_dirs = []

    # Parse contract to identify required functions/classes
    contract_lines = contract_text.split("\n")
    functions = []
    classes = []
    for line in contract_lines:
        if "def " in line or "async def " in line:
            # Extract function name
            parts = line.split("def ")
            if len(parts) > 1:
                func_name = parts[-1].split("(")[0].strip()
                if func_name and not func_name.startswith("_"):
                    functions.append(func_name)
        elif "class " in line:
            # Extract class name
            parts = line.split("class ")
            if len(parts) > 1:
                class_name = parts[-1].split(":")[0].split("(")[0].strip()
                if class_name:
                    classes.append(class_name)

    required_items = "\n".join(
        [f"  - Function: {func}" for func in functions] + [f"  - Class: {cls}" for cls in classes]
    )

    prompt = (
        "🚀 MODULE GENERATION TASK\n"
        "========================\n\n"
        f"Module: {module_name}\n"
        f"Target: {module_dir_rel}/\n\n"
        "YOUR MISSION: Generate a COMPLETE, WORKING module with ALL files.\n"
        "You have 50 turns. Use them ALL to ensure completeness.\n\n"
        "CONTRACT REQUIREMENTS DETECTED:\n" + required_items + "\n\n"
        "FILE GENERATION CHECKLIST:\n"
        "=========================\n"
        "YOU MUST CREATE ALL OF THESE FILES:\n\n"
        "[ ] 1. {module_dir_rel}/__init__.py\n"
        "       - Import all public functions/classes\n"
        "       - Define __all__ with exports\n\n"
        "[ ] 2. {module_dir_rel}/models.py (if data structures needed)\n"
        "       - All data models from contract\n"
        "       - Pydantic models, dataclasses, or TypedDicts\n\n"
        "[ ] 3. {module_dir_rel}/core.py OR {module_dir_rel}/synthesizer.py\n"
        "       - Main implementation file\n"
        "       - ALL functions/classes from contract\n"
        "       - Full working implementations\n\n"
        "[ ] 4. {module_dir_rel}/utils.py (if helpers needed)\n"
        "       - Helper functions\n"
        "       - Internal utilities\n\n"
        "[ ] 5. {module_dir_rel}/errors.py (if custom exceptions needed)\n"
        "       - Custom exception classes\n\n"
        "[ ] 6. {module_dir_rel}/README.md\n"
        "       - Module documentation\n"
        "       - Usage examples\n\n"
        "[ ] 7. {module_dir_rel}/tests/\n"
        "       - Create tests directory\n"
        "       - {module_dir_rel}/tests/__init__.py\n"
        "       - {module_dir_rel}/tests/test_core.py or test_synthesizer.py\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "====================\n"
        "1. DO NOT STOP until ALL files are created\n"
        "2. After creating each file, immediately create the next one\n"
        "3. If you mention importing from a file, CREATE that file\n"
        "4. No placeholders, no TODOs, no stubs\n"
        "5. All code must be immediately runnable\n"
        "6. Continue until the checklist is complete\n\n"
        "WORKFLOW:\n"
        "========\n"
        "Step 1: Create the module directory structure\n"
        "Step 2: Create __init__.py with imports (even if files don't exist yet)\n"
        "Step 3: Create models.py with data structures\n"
        "Step 4: Create main implementation file (core.py or synthesizer.py)\n"
        "Step 5: Create utils.py if needed by implementation\n"
        "Step 6: Create errors.py if needed\n"
        "Step 7: Create README.md\n"
        "Step 8: Create tests directory and test files\n"
        "Step 9: Verify all imports work\n\n"
        "Remember: You're creating a module that other developers will use.\n"
        "Make it complete, professional, and immediately usable.\n\n"
        "=== CONTRACT ===\n" + contract_text + "\n\n"
        "=== IMPLEMENTATION SPEC ===\n" + impl_text + "\n\n"
        "BEGIN NOW! Create files one by one until the module is complete."
    ).format(module_dir_rel=module_dir_rel)
    assert ClaudeSDKClient is not None  # Type guard for pyright
    assert ClaudeCodeOptions is not None  # Type guard for pyright

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt=_default_system_prompt(),
            cwd=cwd,
            add_dirs=add_dirs,
            settings=settings,
            allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
            permission_mode="acceptEdits",  # auto-approve file edits
            max_turns=50,  # Increased from 10 to allow full implementation
        )
    ) as client:
        await client.query(prompt)
        _, session_id, total_cost, duration_ms = await _stream_all_messages(client)
        return (session_id, total_cost, duration_ms)


async def generate_with_continuation(
    contract_text: str,
    impl_text: str,
    module_name: str,
    module_dir_rel: str,
    cwd: str,
    add_dirs: list[str | Path] | None = None,
    settings: str | None = None,
    max_attempts: int = 3,
) -> tuple[str | None, float, int]:  # pyright: ignore[reportReturnType]
    """Generate with automatic continuation if files are missing."""
    _ensure_sdk_available()
    if add_dirs is None:
        add_dirs = []

    total_cost = 0.0
    total_ms = 0
    session_id = None

    # Required files to check
    required_files = [
        f"{module_dir_rel}/__init__.py",
        f"{module_dir_rel}/core.py",  # or synthesizer.py, engine.py, etc.
        f"{module_dir_rel}/models.py",
        f"{module_dir_rel}/README.md",
    ]

    for attempt in range(max_attempts):
        print(f"\n🔄 Generation attempt {attempt + 1}/{max_attempts}")

        # Check what files exist
        from pathlib import Path as PathLib

        base_path = PathLib(cwd) / module_dir_rel
        existing_files = []
        missing_files = []

        for file_rel in required_files:
            file_path = PathLib(cwd) / file_rel
            if file_path.exists():
                existing_files.append(file_rel)
            else:
                # Check for alternative names for core functionality
                if "core.py" in file_rel:
                    # Check for synthesizer.py, engine.py, etc.
                    alt_names = ["synthesizer.py", "engine.py", "processor.py", "main.py"]
                    found_alt = False
                    for alt_name in alt_names:
                        alt_path = base_path / alt_name
                        if alt_path.exists():
                            existing_files.append(f"{module_dir_rel}/{alt_name}")
                            found_alt = True
                            break
                    if not found_alt:
                        missing_files.append(file_rel)
                else:
                    missing_files.append(file_rel)

        if not missing_files and base_path.exists():
            # Check if we have at least the basic structure
            has_init = (base_path / "__init__.py").exists()
            has_implementation = any(
                (base_path / name).exists()
                for name in ["core.py", "synthesizer.py", "engine.py", "processor.py", "main.py"]
            )

            if has_init and has_implementation:
                print("✅ Module generation complete!")
                break

        # Generate continuation prompt
        if attempt == 0:
            # First attempt - use enhanced prompt
            prompt = (
                "🚀 MODULE GENERATION TASK\n"
                "========================\n\n"
                f"Module: {module_name}\n"
                f"Target: {module_dir_rel}/\n\n"
                "YOUR MISSION: Generate a COMPLETE, WORKING module with ALL files.\n"
                "You have 50 turns. Use them ALL to ensure completeness.\n\n"
                "FILE GENERATION CHECKLIST:\n"
                "=========================\n"
                "YOU MUST CREATE ALL OF THESE FILES:\n\n"
                f"[ ] 1. {module_dir_rel}/__init__.py\n"
                f"[ ] 2. {module_dir_rel}/models.py (if data structures needed)\n"
                f"[ ] 3. {module_dir_rel}/core.py OR synthesizer.py OR engine.py\n"
                f"[ ] 4. {module_dir_rel}/utils.py (if helpers needed)\n"
                f"[ ] 5. {module_dir_rel}/errors.py (if custom exceptions needed)\n"
                f"[ ] 6. {module_dir_rel}/README.md\n"
                f"[ ] 7. {module_dir_rel}/tests/ directory with test files\n\n"
                "CRITICAL: Create files one by one until complete.\n\n"
                "=== CONTRACT ===\n" + contract_text + "\n\n"
                "=== IMPLEMENTATION SPEC ===\n" + impl_text + "\n\n"
                "BEGIN NOW! Create all files for the module."
            )
        else:
            # Continuation attempt - focus on missing files
            prompt = (
                "📋 CONTINUE MODULE GENERATION\n"
                "============================\n\n"
                f"Module: {module_name} in {module_dir_rel}/\n\n"
                "FILES ALREADY CREATED:\n"
            )
            for f in existing_files:
                prompt += f"  ✓ {f}\n"

            prompt += "\nFILES STILL NEEDED:\n"
            for f in missing_files:
                prompt += f"  ❌ {f}\n"

            # Also check for utils if core imports it
            if base_path.exists():
                for py_file in base_path.glob("*.py"):
                    if py_file.name == "__init__.py":
                        continue
                    content = py_file.read_text()
                    if "from .utils import" in content or "from . import utils" in content:
                        utils_path = base_path / "utils.py"
                        if not utils_path.exists():
                            prompt += f"  ❌ {module_dir_rel}/utils.py (imported but missing!)\n"

            prompt += (
                "\nCONTINUE creating the missing files.\n"
                "Remember the contract requirements:\n\n"
                "=== CONTRACT ===\n" + contract_text + "\n\n"
                "CREATE the missing files NOW to complete the module."
            )

        # Run generation
        assert ClaudeSDKClient is not None  # Type guard for pyright
        assert ClaudeCodeOptions is not None  # Type guard for pyright

        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt=_default_system_prompt(),
                cwd=cwd,
                add_dirs=add_dirs,
                settings=settings,
                allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
                permission_mode="acceptEdits",
                max_turns=50,
            )
        ) as client:
            await client.query(prompt)
            _, sid, cost, ms = await _stream_all_messages(client)

            session_id = sid or session_id
            total_cost += cost
            total_ms += ms

    return (session_id, total_cost, total_ms)
