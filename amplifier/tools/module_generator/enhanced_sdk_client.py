"""
Enhanced SDK client that uses structured contract parsing for better generation.

Key improvements:
- Uses parsed contract requirements instead of raw text
- Generates specific prompts for each component
- Validates during generation
- Self-tests after generation
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from .contract_parser import EnhancedContractParser
from .contract_validator import ContractValidator
from .import_mappings import build_import_instructions

try:
    from claude_code_sdk import AssistantMessage
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
    from claude_code_sdk import ClaudeSDKError
    from claude_code_sdk import CLINotFoundError
    from claude_code_sdk import ProcessError
    from claude_code_sdk import ResultMessage
    from claude_code_sdk import TextBlock
    from claude_code_sdk import ToolUseBlock
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
    """Ensure the Claude SDK is available."""
    if ClaudeSDKClient is None:
        raise RuntimeError(
            "claude_code_sdk is not available. Ensure it's installed and importable in this environment.\n"
            "Dependency is declared in the repo's pyproject; install via `make install`."
        )


async def _stream_all_messages(
    client: Any,
    activity_timeout: float = 60.0,
    max_total_time: float | None = None,
    show_progress: bool = True,
) -> tuple[str, str | None, float, int]:
    """Collects streamed assistant text with activity monitoring.

    Args:
        client: Claude SDK client instance
        activity_timeout: Max seconds without activity before timeout
        max_total_time: Optional absolute max seconds for operation (None = no limit)
        show_progress: Show progress indicators

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

    # Create task for monitoring
    response_task = asyncio.create_task(_collect_streaming_response(client, collected, show_progress, activity_state))

    # Monitor with activity timeout
    while not response_task.done():
        try:
            await asyncio.wait_for(
                asyncio.shield(response_task),
                timeout=1.0,
            )
            return await response_task
        except TimeoutError:
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

            # Heartbeat for long operations
            if show_progress and int(time_since_start) % 30 == 0 and int(time_since_start) > 0:
                elapsed_min = time_since_start / 60
                print(
                    f"\n💓 [Still running: {elapsed_min:.1f} minutes, {activity_state['message_count']} messages]\n",
                    flush=True,
                )

            continue

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
    tool_counts = {}

    async for msg in client.receive_response():
        message_count += 1

        # Update activity tracking
        if activity_state:
            activity_state["last_activity"] = time.time()
            activity_state["message_count"] = message_count

        # Process assistant messages
        if AssistantMessage is not None and isinstance(msg, AssistantMessage):
            for block in getattr(msg, "content", []) or []:
                # Track tool usage
                if hasattr(block, "type") and block.type == "tool_use":
                    tool_use_count += 1
                    tool_name = getattr(block, "name", "unknown")
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

                    if show_progress:
                        # Show tool-specific icons
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

                        # Show tool details if available
                        if hasattr(block, "input") and block.input:
                            input_data = block.input
                            if tool_name == "Write" and "file_path" in input_data:
                                print(f"    Creating: {input_data['file_path']}", flush=True)
                            elif tool_name in ["Edit", "MultiEdit"] and "file_path" in input_data:
                                print(f"    Editing: {input_data['file_path']}", flush=True)
                            elif tool_name == "Read" and "file_path" in input_data:
                                print(f"    Reading: {input_data['file_path']}", flush=True)

                # Handle text blocks
                if TextBlock is not None and isinstance(block, TextBlock):
                    text = getattr(block, "text", "")
                    if text:
                        if show_progress:
                            # Limit very long output
                            lines = text.split("\n")
                            if len(lines) > 50:
                                print("\n".join(lines[:20]), flush=True)
                                print(f"\n... [{len(lines) - 30} lines omitted] ...\n", flush=True)
                                print("\n".join(lines[-10:]), flush=True)
                            else:
                                print(text, end="", flush=True)
                        collected.append(text)

        # Capture result message
        if ResultMessage is not None and isinstance(msg, ResultMessage):
            total_cost = getattr(msg, "total_cost_usd", 0.0) or 0.0
            duration_ms = getattr(msg, "duration_ms", 0) or 0
            session_id = getattr(msg, "session_id", None)

            if show_progress:
                print("\n\n✅ Operation completed:", flush=True)
                print(f"   • Messages: {message_count}", flush=True)
                print(f"   • Tools used: {tool_use_count}", flush=True)

                # Show tool breakdown
                if len(tool_counts) > 1:
                    print("   • Tool breakdown:", flush=True)
                    for tool, count in sorted(tool_counts.items()):
                        print(f"       - {tool}: {count}x", flush=True)

                print(f"   • Duration: {duration_ms / 1000:.1f}s", flush=True)
                print(f"   • Cost: ${total_cost:.4f}\n", flush=True)
            break

        # Periodic progress
        if show_progress and message_count % 10 == 0:
            print(f"\n💓 [Progress: {message_count} messages, {tool_use_count} tools]\n", flush=True)

    if not session_id and show_progress:
        print("\n⚠️ No result message received - operation may have completed partially", flush=True)

    return ("".join(collected), session_id, total_cost, duration_ms)


def _default_system_prompt() -> str:
    """Generate system prompt with import instructions."""
    import_instructions = build_import_instructions()
    return (
        "You are the Modular Builder for the Amplifier repo.\n"
        "Follow contract-first, 'bricks & studs', and regeneration over patching.\n"
        "Use concise, explicit steps. Respect repo conventions and tests.\n\n" + import_instructions + "\n\n"
        "CRITICAL: Always use the correct import patterns listed above.\n"
        "IMPORTANT: Implement ALL requirements from the contract - no placeholders or TODOs."
    )


def _build_structured_generation_prompt(
    requirements: Any,  # ContractRequirements
    module_name: str,
    module_dir_rel: str,
    impl_spec_text: str,
) -> str:
    """Build a structured generation prompt from parsed requirements."""
    prompt = [
        "🚀 MODULE GENERATION TASK",
        "========================",
        "",
        f"Module: {module_name}",
        f"Target: {module_dir_rel}/",
        "",
        "PURPOSE:",
        requirements.purpose,
        "",
    ]

    # Add required functions
    if requirements.functions:
        prompt.append("REQUIRED FUNCTIONS:")
        for func in requirements.functions:
            params = ", ".join([f"{p[0]}: {p[1]}" for p in func.params])
            ret = f" -> {func.return_type}" if func.return_type else ""
            async_prefix = "async " if func.is_async else ""
            prompt.append(f"  - {async_prefix}def {func.name}({params}){ret}")
            if func.description:
                prompt.append(f"    # {func.description}")
        prompt.append("")

    # Add required classes
    if requirements.classes:
        prompt.append("REQUIRED CLASSES:")
        for cls in requirements.classes:
            prompt.append(f"  - class {cls.name}:")
            for method in cls.methods:
                params = ", ".join(["self"] + [f"{p[0]}: {p[1]}" for p in method.params])
                ret = f" -> {method.return_type}" if method.return_type else ""
                async_prefix = "async " if method.is_async else ""
                prompt.append(f"      {async_prefix}def {method.name}({params}){ret}")
        prompt.append("")

    # Add required data models with ALL fields
    if requirements.data_models:
        prompt.append("REQUIRED DATA MODELS (implement ALL fields exactly as specified):")
        for model in requirements.data_models:
            prompt.append("  - @dataclass")
            prompt.append(f"    class {model.name}:")
            if model.description:
                prompt.append(f'      """{model.description}"""')
            for field in model.fields:
                if field.default is not None:
                    prompt.append(f"      {field.name}: {field.type_hint} = {field.default}")
                else:
                    prompt.append(f"      {field.name}: {field.type_hint}")
                if field.description:
                    prompt.append(f"      # {field.description}")
            prompt.append("")

    # Add configuration parameters
    if requirements.config_params:
        prompt.append("REQUIRED CONFIG PARAMETERS (must be included in Config class):")
        for param in requirements.config_params:
            if param.default:
                prompt.append(f"  - {param.name}: {param.type_hint} = {param.default}")
            else:
                prompt.append(f"  - {param.name}: {param.type_hint}")
        prompt.append("")

    # Add required error types
    if requirements.errors:
        prompt.append("REQUIRED ERROR TYPES:")
        for error in requirements.errors:
            prompt.append(f"  - class {error.name}(Exception):")
            if error.description:
                prompt.append(f'      """{error.description}"""')
        prompt.append("")

    # Add input/output specifications
    if requirements.inputs:
        prompt.append("INPUT PARAMETERS:")
        for inp in requirements.inputs:
            req = "required" if inp.required else "optional"
            prompt.append(f"  - {inp.name} ({inp.type_hint}, {req}): {inp.description}")
        prompt.append("")

    if requirements.outputs:
        prompt.append("OUTPUT SPECIFICATIONS:")
        for out in requirements.outputs:
            prompt.append(f"  - {out.name}: {out.description}")
        prompt.append("")

    # Add file structure
    prompt.extend(
        [
            "FILE STRUCTURE TO CREATE:",
            "========================",
            f"1. {module_dir_rel}/__init__.py",
            "   - Import ALL public functions/classes",
            "   - Define __all__ with exports",
            "",
        ]
    )

    # Determine which files to create based on requirements
    files_needed = []

    if requirements.data_models or requirements.config_params:
        files_needed.append(("models.py", "All data models and config classes"))

    if requirements.functions or requirements.classes:
        # Check if we have a synthesizer pattern
        if any("synth" in f.name.lower() for f in requirements.functions):
            files_needed.append(("synthesizer.py", "Main synthesis implementation"))
        else:
            files_needed.append(("core.py", "Main implementation"))

    if requirements.errors:
        files_needed.append(("errors.py", "Custom exception classes"))

    # Always need utils if we have complex logic
    if len(requirements.functions) > 3:
        files_needed.append(("utils.py", "Helper functions"))

    files_needed.append(("README.md", "Module documentation"))
    files_needed.append(("tests/__init__.py", "Test package marker"))
    files_needed.append(("tests/test_core.py", "Unit tests"))

    for i, (filename, description) in enumerate(files_needed, start=2):
        prompt.append(f"{i}. {module_dir_rel}/{filename}")
        prompt.append(f"   - {description}")
        prompt.append("")

    # Add implementation spec details
    prompt.extend(
        [
            "IMPLEMENTATION DETAILS:",
            "======================",
            impl_spec_text,
            "",
            "CRITICAL REQUIREMENTS:",
            "=====================",
            "1. Implement ALL functions, classes, and data models listed above",
            "2. Include ALL fields in data models - no missing parameters!",
            "3. Follow the exact signatures specified",
            "4. No placeholders, TODOs, or NotImplementedError",
            "5. All code must be immediately runnable",
            "6. Create comprehensive tests",
            "",
            "BEGIN GENERATION NOW!",
        ]
    )

    return "\n".join(prompt)


async def generate_with_enhanced_parsing(
    contract_text: str,
    impl_text: str,
    module_name: str,
    module_dir_rel: str,
    cwd: str,
    add_dirs: list[str | Path] | None = None,
    settings: str | None = None,
) -> tuple[str | None, float, int, bool]:
    """Generate module using enhanced contract parsing."""
    _ensure_sdk_available()
    if add_dirs is None:
        add_dirs = []

    # Parse the contract to extract structured requirements
    parser = EnhancedContractParser(contract_text)
    requirements = parser.parse()

    # Build structured prompt
    prompt = _build_structured_generation_prompt(requirements, module_name, module_dir_rel, impl_text)

    # Save prompt for debugging
    debug_file = Path(cwd) / "debug_generation_prompt.txt"
    debug_file.write_text(prompt)
    print(f"📝 Generation prompt saved to {debug_file}")

    assert ClaudeSDKClient is not None
    assert ClaudeCodeOptions is not None

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
                permission_mode="acceptEdits",
                max_turns=50,
            )
        ) as client:
            await client.query(prompt)
            # Use activity-based monitoring with longer timeout for generation
            _, session_id, total_cost, duration_ms = await _stream_all_messages(
                client, activity_timeout=120, max_total_time=None, show_progress=True
            )
    except TimeoutError as e:
        print(f"\n⚠️ {e}")
        print("The generation stopped due to inactivity. This might indicate:")
        print("  • Claude CLI is not installed (npm install -g @anthropic-ai/claude-code)")
        print("  • Running outside Claude Code environment")
        print("  • The operation genuinely completed but didn't send a result message")

        # Still try to validate what was generated
        module_path = Path(cwd) / module_dir_rel
        if module_path.exists():
            validator = ContractValidator.from_contract_text(module_path, contract_text)
            result = validator.validate()
            print("\nPartial generation results:")
            print(result.summary())
        return (None, 0.0, 0, False)
    except (CLINotFoundError, ProcessError, Exception) as e:
        # Catch SDK errors and any other exceptions
        if isinstance(e, CLINotFoundError | ProcessError):
            print(f"\n❌ Claude Code SDK error: {e}")
            print("Please install the Claude CLI: npm install -g @anthropic-ai/claude-code")
        else:
            print(f"\n❌ Unexpected error: {e}")
        return (None, 0.0, 0, False)

    # Validate the generated module
    module_path = Path(cwd) / module_dir_rel
    validator = ContractValidator.from_contract_text(module_path, contract_text)
    result = validator.validate()

    print("\n" + "=" * 50)
    print("CONTRACT VALIDATION RESULTS:")
    print("=" * 50)
    print(result.summary())

    if not result.is_valid:
        # Generate fix prompt
        fix_prompt = validator.generate_missing_code_prompt(result)
        if fix_prompt:
            print("\n🔧 Attempting to fix missing implementations...")
            print(fix_prompt)

            # Run another generation pass to fix issues
            try:
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt=_default_system_prompt(),
                        cwd=cwd,
                        add_dirs=add_dirs,
                        settings=settings,
                        allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
                        permission_mode="acceptEdits",
                        max_turns=30,
                    )
                ) as fix_client:
                    await fix_client.query(fix_prompt)
                    await _stream_all_messages(fix_client, activity_timeout=60, max_total_time=None, show_progress=True)
            except TimeoutError as e:
                print(f"\n⚠️ Fix attempt timeout: {e}")
            except (CLINotFoundError, ProcessError, Exception) as e:
                # Catch SDK errors and any other exceptions
                if isinstance(e, CLINotFoundError | ProcessError):
                    print(f"\n❌ Fix attempt SDK error: {e}")
                else:
                    print(f"\n❌ Fix attempt error: {e}")

            # Re-validate
            result = validator.validate()
            print("\n" + result.summary())

    # Run self-tests
    if result.is_valid:
        print("\n🧪 Running self-tests...")
        success = await run_self_tests(module_path, module_name)
        if success:
            print("✅ Self-tests passed!")
        else:
            print("❌ Self-tests failed - module may have issues")
            result.is_valid = False

    return (session_id, total_cost, duration_ms, result.is_valid)


async def run_self_tests(module_path: Path, module_name: str) -> bool:
    """Run basic self-tests on the generated module."""
    import subprocess
    import sys

    tests_passed = True

    # Test 1: Can the module be imported?
    print("  Testing import...")
    init_file = module_path / "__init__.py"
    if not init_file.exists():
        print("    ❌ Missing __init__.py")
        return False

    # Add to path and try import
    parent_dir = str(module_path.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, init_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print("    ✅ Module imports successfully")

            # Check __all__ exists
            if hasattr(module, "__all__"):
                exports = module.__all__
                print(f"    ✅ Exports {len(exports)} items: {', '.join(exports[:5])}")
            else:
                print("    ⚠️  No __all__ export list")
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        tests_passed = False
    finally:
        if parent_dir in sys.path:
            sys.path.remove(parent_dir)

    # Test 2: Run pyright on the module
    print("  Testing type checking...")
    try:
        result = subprocess.run(
            ["pyright", str(module_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("    ✅ Type checking passed")
        else:
            # Check if it's just warnings
            if "error" in result.stdout.lower():
                print("    ❌ Type errors found")
                tests_passed = False
            else:
                print("    ⚠️  Type warnings found")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("    ⚠️  Could not run type checking")

    # Test 3: Check for test files
    print("  Checking test coverage...")
    tests_dir = module_path / "tests"
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        if test_files:
            print(f"    ✅ Found {len(test_files)} test files")
        else:
            print("    ⚠️  No test files found")
    else:
        print("    ❌ No tests directory")
        tests_passed = False

    return tests_passed


async def generate_from_specs_enhanced(
    contract_text: str,
    impl_text: str,
    module_name: str,
    module_dir_rel: str,
    cwd: str,
    add_dirs: list[str | Path] | None = None,
    settings: str | None = None,
    max_attempts: int = 3,
) -> tuple[str | None, float, int]:
    """Enhanced generation with validation and retries."""
    total_cost = 0.0
    total_ms = 0
    session_id = None

    for attempt in range(max_attempts):
        print(f"\n🔄 Generation attempt {attempt + 1}/{max_attempts}")

        sid, cost, ms, success = await generate_with_enhanced_parsing(
            contract_text,
            impl_text,
            module_name,
            module_dir_rel,
            cwd,
            add_dirs,
            settings,
        )

        session_id = sid or session_id
        total_cost += cost
        total_ms += ms

        if success:
            print("\n✅ Module successfully generated and validated!")
            break

        if attempt < max_attempts - 1:
            print("\n⚠️  Generation incomplete, retrying...")
    else:
        print(f"\n❌ Failed to generate complete module after {max_attempts} attempts")

    return (session_id, total_cost, total_ms)
