from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from .import_mappings import build_import_instructions
from .verification import ModuleVerifier
from .verification import extract_planned_files_from_prompt

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
    from claude_code_sdk import ToolUseBlock  # For detecting tool usage
except Exception:
    ClaudeSDKClient = None  # type: ignore
    ClaudeCodeOptions = None  # type: ignore
    AssistantMessage = None  # type: ignore
    ResultMessage = None  # type: ignore
    TextBlock = None  # type: ignore
    ToolUseBlock = None  # type: ignore
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


async def check_sdk_health() -> tuple[bool, str]:
    """Check if Claude Code SDK is properly configured and responsive.

    Returns:
        (is_healthy, diagnostic_message)
    """
    import shutil
    import subprocess

    diagnostics = []
    is_healthy = True

    # Check if SDK is importable
    if ClaudeSDKClient is None:
        diagnostics.append("❌ claude_code_sdk Python package not available")
        is_healthy = False
    else:
        diagnostics.append("✅ claude_code_sdk Python package imported")

    # Check if claude CLI is available
    claude_path = shutil.which("claude")
    if claude_path:
        diagnostics.append(f"✅ Claude CLI found at: {claude_path}")

        # Try to get version
        try:
            result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                diagnostics.append(f"✅ Claude CLI version: {version}")
            else:
                diagnostics.append("⚠️ Claude CLI found but version check failed")
                is_healthy = False
        except Exception as e:
            diagnostics.append(f"⚠️ Error checking Claude CLI version: {e}")
    else:
        diagnostics.append("❌ Claude CLI not found in PATH")
        diagnostics.append("   Install with: npm install -g @anthropic-ai/claude-code")
        is_healthy = False

    # Check environment
    import os

    if os.environ.get("CLAUDE_CODE_ENVIRONMENT"):
        diagnostics.append("✅ Running inside Claude Code environment")
    else:
        diagnostics.append("ℹ️ Not running inside Claude Code environment")
        diagnostics.append("   SDK operations may have limited functionality")

    return is_healthy, "\n".join(diagnostics)


async def _stream_all_messages_with_monitoring(
    client: Any, activity_timeout: float = 60.0, max_total_time: float | None = None, show_progress: bool = True
) -> tuple[str, str | None, float, int]:
    """Collects streamed assistant text with activity monitoring.

    This function monitors streaming activity and will only timeout if there's
    no activity for `activity_timeout` seconds. It allows operations to run
    indefinitely as long as they're actively producing output.

    Args:
        client: Claude SDK client instance
        activity_timeout: Max seconds without activity before timeout (default 60s)
        max_total_time: Optional absolute max seconds for the entire operation (default None = no limit)
        show_progress: Show progress indicators for long operations

    Returns:
        (text, session_id, total_cost_usd, duration_ms)
    """
    collected = []
    start_time = time.time()
    last_activity_time = time.time()
    activity_state = {"last_activity": last_activity_time, "message_count": 0}

    if show_progress:
        print("🔄 Starting Claude Code SDK operation...", flush=True)
        print(f"   • Activity timeout: {activity_timeout}s", flush=True)
        if max_total_time:
            print(f"   • Max total time: {max_total_time / 60:.0f} minutes\n", flush=True)
        else:
            print("   • No maximum time limit - will run as long as actively working\n", flush=True)

    # Create an async task to monitor the streaming
    response_task = asyncio.create_task(_collect_streaming_response(client, collected, show_progress, activity_state))

    # Monitor the task with activity timeout
    while not response_task.done():
        try:
            # Wait for a short period to check activity
            await asyncio.wait_for(
                asyncio.shield(response_task),
                timeout=1.0,  # Check every second
            )
            # Task completed successfully
            return await response_task
        except TimeoutError:
            # Check if we've exceeded timeouts
            current_time = time.time()
            time_since_start = current_time - start_time
            time_since_activity = current_time - activity_state["last_activity"]

            # Check absolute time limit if specified
            if max_total_time and time_since_start > max_total_time:
                response_task.cancel()
                print(f"\n⚠️ Operation exceeded maximum time ({max_total_time / 60:.0f} minutes)", flush=True)
                raise TimeoutError(f"Exceeded {max_total_time / 60:.0f} minute limit")

            # Check activity timeout
            if time_since_activity > activity_timeout:
                response_task.cancel()
                print(f"\n⚠️ No activity for {activity_timeout} seconds - timing out", flush=True)
                print(f"   • Received {activity_state['message_count']} messages before timeout", flush=True)
                raise TimeoutError(f"No activity for {activity_timeout} seconds")

            # Show heartbeat for very long operations
            if show_progress and int(time_since_start) % 30 == 0 and int(time_since_start) > 0:
                elapsed_min = time_since_start / 60
                print(
                    f"\n💓 [Still running: {elapsed_min:.1f} minutes, {activity_state['message_count']} messages]\n",
                    flush=True,
                )

            continue

    # Get the result from the completed task
    return await response_task


async def _collect_streaming_response(
    client: Any, collected: list, show_progress: bool, activity_state: dict | None = None
) -> tuple[str, str | None, float, int]:
    """Helper to collect streaming responses with activity tracking."""
    session_id = None
    total_cost = 0.0
    duration_ms = 0
    message_count = 0
    tool_use_count = 0
    tool_counts = {}  # Track usage per tool type

    async for msg in client.receive_response():
        message_count += 1

        # Update activity tracking
        if activity_state:
            activity_state["last_activity"] = time.time()
            activity_state["message_count"] = message_count

        # Process assistant messages with content
        if AssistantMessage is not None and isinstance(msg, AssistantMessage):
            for block in getattr(msg, "content", []) or []:
                # Check for tool use blocks
                if hasattr(block, "type") and block.type == "tool_use":
                    tool_use_count += 1
                    tool_name = getattr(block, "name", "unknown")
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

                    if show_progress:
                        # Show different icons for different tools
                        tool_icons = {
                            "Write": "📝",
                            "Read": "📖",
                            "Edit": "✏️",
                            "MultiEdit": "🔨",
                            "Bash": "💻",
                            "Grep": "🔍",
                        }
                        icon = tool_icons.get(tool_name, "🔧")
                        print(f"\n{icon} [Tool: {tool_name}]", flush=True)

                        # Show tool-specific info
                        if hasattr(block, "input") and block.input:
                            input_data = block.input
                            if tool_name == "Write" and "file_path" in input_data:
                                print(f"    Creating: {input_data['file_path']}", flush=True)
                            elif tool_name == "Edit" and "file_path" in input_data:
                                print(f"    Editing: {input_data['file_path']}", flush=True)
                            elif tool_name == "Read" and "file_path" in input_data:
                                print(f"    Reading: {input_data['file_path']}", flush=True)

                # Handle text blocks
                if TextBlock is not None and isinstance(block, TextBlock):
                    text = getattr(block, "text", "")
                    if text:
                        if show_progress:
                            # Limit very long text output for readability
                            lines = text.split("\n")
                            if len(lines) > 50:
                                # Show first 20 and last 10 lines
                                print("\n".join(lines[:20]), flush=True)
                                print(f"\n... [{len(lines) - 30} lines omitted] ...\n", flush=True)
                                print("\n".join(lines[-10:]), flush=True)
                            else:
                                print(text, end="", flush=True)
                        collected.append(text)

        # Capture final result message
        if ResultMessage is not None and isinstance(msg, ResultMessage):
            # Final stats
            total_cost = getattr(msg, "total_cost_usd", 0.0) or 0.0
            duration_ms = getattr(msg, "duration_ms", 0) or 0
            session_id = getattr(msg, "session_id", None)

            if show_progress:
                print("\n\n✅ Operation completed:", flush=True)
                print(f"   • Messages: {message_count}", flush=True)
                print(f"   • Tools used: {tool_use_count}", flush=True)

                # Show tool breakdown if multiple tools used
                if len(tool_counts) > 1:
                    print("   • Tool breakdown:", flush=True)
                    for tool, count in sorted(tool_counts.items()):
                        print(f"       - {tool}: {count}x", flush=True)

                print(f"   • Duration: {duration_ms / 1000:.1f}s", flush=True)
                print(f"   • Cost: ${total_cost:.4f}\n", flush=True)
            break

        # Periodic progress for long operations
        if show_progress and message_count % 10 == 0:
            print(f"\n💓 [Progress: {message_count} messages, {tool_use_count} tools]\n", flush=True)

    if not session_id and show_progress:
        print("\n⚠️ No result message received - operation may have completed partially", flush=True)

    return ("".join(collected), session_id, total_cost, duration_ms)


# Keep the original function name for backward compatibility
async def _stream_all_messages(
    client: Any, activity_timeout: float = 60.0, show_progress: bool = True, max_total_time: float | None = None
) -> tuple[str, str | None, float, int]:
    """Backward-compatible wrapper for streaming messages.

    Args:
        client: Claude SDK client instance
        activity_timeout: Max seconds without activity before timeout (default 60s)
        show_progress: Show progress indicators (default True)
        max_total_time: Optional absolute max seconds for operation (default None = no limit)
    """
    return await _stream_all_messages_with_monitoring(client, activity_timeout, max_total_time, show_progress)


async def _monitor_with_activity_timeout(
    coro: Any,
    activity_timeout: float = 60.0,
    max_total_time: float | None = None,
) -> Any:
    """Monitor a coroutine with activity timeout and optional total time limit.

    This wrapper allows long-running operations as long as they show activity.
    If max_total_time is specified, it will also enforce an absolute time limit.

    Args:
        coro: The coroutine to monitor
        activity_timeout: Max seconds without activity before timeout
        max_total_time: Optional absolute max seconds for the entire operation
    """
    start_time = time.time()

    # Create a task from the coroutine
    task = asyncio.create_task(coro)

    while not task.done():
        # Check total time limit if specified
        if max_total_time and time.time() - start_time > max_total_time:
            task.cancel()
            print(f"\n⚠️ Operation exceeded maximum time limit ({max_total_time / 60:.0f} minutes)", flush=True)
            raise TimeoutError(f"Operation exceeded {max_total_time / 60:.0f} minute limit")

        # Wait for either completion or short timeout
        try:
            result = await asyncio.wait_for(asyncio.shield(task), timeout=1.0)
            return result
        except TimeoutError:
            # Still running, check if we should continue
            continue

    return await task


def _default_system_prompt() -> str:
    import_instructions = build_import_instructions()
    return (
        "You are the Modular Builder for the Amplifier repo.\n"
        "Follow contract-first, 'bricks & studs', and regeneration over patching.\n"
        "Use concise, explicit steps. Respect repo conventions and tests.\n\n" + import_instructions + "\n\n"
        "CRITICAL: Always use the correct import patterns listed above."
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

    try:
        print("\n📋 Planning module implementation...\n", flush=True)
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
            # Use activity-based monitoring, not hard timeout
            return await _stream_all_messages(client, activity_timeout=60, show_progress=True)
    except TimeoutError as e:
        print(f"\n⚠️ {e}")
        print("The operation stopped due to inactivity. This might indicate:")
        print("  • Claude CLI is not installed (npm install -g @anthropic-ai/claude-code)")
        print("  • Running outside Claude Code environment")
        print("  • Network connectivity issues")
        raise RuntimeError("Operation timeout - cannot continue")
    except (CLINotFoundError, ProcessError) as e:
        print(f"\n❌ Claude Code SDK error: {e}")
        print("Please install the Claude CLI: npm install -g @anthropic-ai/claude-code")
        return ("", None, 0.0, 0)


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

    # Build prompt with module_dir_rel already substituted to avoid format conflicts
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
        f"[ ] 1. {module_dir_rel}/__init__.py\n"
        "       - Import all public functions/classes\n"
        "       - Define __all__ with exports\n\n"
        f"[ ] 2. {module_dir_rel}/models.py (if data structures needed)\n"
        "       - All data models from contract\n"
        "       - Pydantic models, dataclasses, or TypedDicts\n\n"
        f"[ ] 3. {module_dir_rel}/core.py OR {module_dir_rel}/synthesizer.py\n"
        "       - Main implementation file\n"
        "       - ALL functions/classes from contract\n"
        "       - Full working implementations\n\n"
        f"[ ] 4. {module_dir_rel}/utils.py (if helpers needed)\n"
        "       - Helper functions\n"
        "       - Internal utilities\n\n"
        f"[ ] 5. {module_dir_rel}/errors.py (if custom exceptions needed)\n"
        "       - Custom exception classes\n\n"
        f"[ ] 6. {module_dir_rel}/README.md\n"
        "       - Module documentation\n"
        "       - Usage examples\n\n"
        f"[ ] 7. {module_dir_rel}/tests/\n"
        "       - Create tests directory\n"
        f"       - {module_dir_rel}/tests/__init__.py\n"
        f"       - {module_dir_rel}/tests/test_core.py or test_synthesizer.py\n\n"
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
    )

    # Extract planned files from prompt for verification
    required_files, optional_files = extract_planned_files_from_prompt(prompt)

    assert ClaudeSDKClient is not None  # Type guard for pyright
    assert ClaudeCodeOptions is not None  # Type guard for pyright

    try:
        print(f"\n🚀 Generating module: {module_name}\n", flush=True)
        print("This may take several minutes for complex modules...\n", flush=True)

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
            # Use activity-based monitoring with longer timeout for generation
            _, session_id, total_cost, duration_ms = await _stream_all_messages(
                client, activity_timeout=120, show_progress=True
            )

            # Verify the generated module
            module_path = Path(cwd) / module_dir_rel
            verifier = ModuleVerifier(module_path, module_name)
            verifier.set_required_files(required_files)
            verifier.set_optional_files(optional_files)

            is_valid, report = verifier.verify_all()
            print("\n" + report + "\n")

            if not is_valid:
                print("⚠️  Module generation incomplete - consider running with continuation")

            return (session_id, total_cost, duration_ms)
    except TimeoutError as e:
        print(f"\n⚠️ {e}")
        print("The generation stopped due to inactivity. This might indicate:")
        print("  • Claude CLI is not installed (npm install -g @anthropic-ai/claude-code)")
        print("  • Running outside Claude Code environment")
        print("  • The operation genuinely completed but didn't send a result message")

        # Still try to verify what was generated
        module_path = Path(cwd) / module_dir_rel
        if module_path.exists():
            verifier = ModuleVerifier(module_path, module_name)
            is_valid, report = verifier.verify_all()
            print("\nPartial generation results:\n" + report)

        raise RuntimeError("Generation timeout - check partial results above")
    except (CLINotFoundError, ProcessError) as e:
        print(f"\n❌ Claude Code SDK error: {e}")
        return (None, 0.0, 0)


async def verify_and_fix_module(
    module_path: Path,
    module_name: str,
    contract_text: str,
    cwd: str,
    add_dirs: list[str | Path] | None = None,
    settings: str | None = None,
) -> tuple[bool, str]:  # pyright: ignore[reportReturnType]
    """Verify a generated module and attempt to fix issues."""
    _ensure_sdk_available()
    if add_dirs is None:
        add_dirs = []

    verifier = ModuleVerifier(module_path, module_name)
    is_valid, report = verifier.verify_all()

    if is_valid:
        return True, report

    # Generate fix prompt based on issues
    fix_prompt = (
        f"Module {module_name} has issues that need fixing:\n\n" + report + "\n\n"
        "Please fix these issues:\n"
        "1. Add any missing files\n"
        "2. Fix any import errors (use correct import patterns)\n"
        "3. Ensure all local dependencies exist\n\n"
        "Contract for reference:\n" + contract_text
    )

    assert ClaudeSDKClient is not None  # Type guard for pyright
    assert ClaudeCodeOptions is not None  # Type guard for pyright

    try:
        print("\n🔧 Attempting to fix module issues...\n", flush=True)

        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt=_default_system_prompt(),
                cwd=cwd,
                add_dirs=add_dirs,
                settings=settings,
                allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
                permission_mode="acceptEdits",
                max_turns=20,
            )
        ) as client:
            await client.query(fix_prompt)
            # Use shorter activity timeout for fixes
            await _stream_all_messages(client, activity_timeout=60, show_progress=True)

        # Re-verify after fixes
        is_valid, report = verifier.verify_all()
        return is_valid, report
    except TimeoutError as e:
        print(f"\n⚠️ Fix attempt timed out: {e}")
        # Return current state
        return is_valid, report
    except (CLINotFoundError, ProcessError) as e:
        print(f"\n❌ Claude Code SDK error during fix: {e}")
        return is_valid, report


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
                # Run full verification before declaring success
                verifier = ModuleVerifier(base_path, module_name)
                is_valid, report = verifier.verify_all()

                if is_valid:
                    print("✅ Module generation complete and verified!")
                    print(report)
                    break
                print("⚠️  Module has issues, continuing generation...")
                missing_files.append("VERIFICATION_FAILED")  # Force continuation

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

        try:
            if attempt == 0:
                print(f"\n🚀 Starting generation of module: {module_name}\n", flush=True)
            else:
                print(f"\n🔄 Continuing generation (attempt {attempt + 1}/{max_attempts})\n", flush=True)

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
                # Use activity-based monitoring with longer timeout for generation
                _, sid, cost, ms = await _stream_all_messages(client, activity_timeout=120, show_progress=True)

                session_id = sid or session_id
                total_cost += cost
                total_ms += ms
        except TimeoutError as e:
            print(f"\n⚠️ {e}")
            print("Generation stopped due to inactivity. Checking partial results...")

            # Check what was generated before timing out
            base_path = PathLib(cwd) / module_dir_rel
            if base_path.exists():
                verifier = ModuleVerifier(base_path, module_name)
                is_valid, report = verifier.verify_all()
                print("\nPartial results before timeout:\n" + report)

            # Ask user if they want to continue
            if attempt < max_attempts - 1:
                print("\nThe operation can be retried with continuation.")
                # For now, we'll break - in future could add interactive prompt
            break
        except (CLINotFoundError, ProcessError) as e:
            print(f"\n❌ Claude Code SDK error: {e}")
            print("Please ensure Claude CLI is installed: npm install -g @anthropic-ai/claude-code")
            break  # Exit the retry loop

            # Always run final verification
            if attempt == max_attempts - 1:
                verifier = ModuleVerifier(base_path, module_name)
                is_valid, final_report = verifier.verify_all()
                print("\n" + final_report + "\n")

                if not is_valid:
                    # Try to auto-fix issues
                    print("🔧 Attempting to auto-fix issues...")
                    is_fixed, fix_report = await verify_and_fix_module(
                        base_path, module_name, contract_text, cwd, add_dirs, settings
                    )
                    print(fix_report)

    return (session_id, total_cost, total_ms)
