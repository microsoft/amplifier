"""
Core module generator logic.

Simple, direct implementation using Claude Code SDK and Task tool.
Enhanced with metacognitive conversation management for better reliability.
"""

import asyncio
import json
import logging
import re
import subprocess
from pathlib import Path

from amplifier.utils.file_io import write_text_with_retry

try:
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient

    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    ClaudeCodeOptions = None
    ClaudeSDKClient = None

logger = logging.getLogger(__name__)

# Import conversation manager for enhanced SDK interaction
try:
    from .conversation_manager import ConversationManager

    CONVERSATION_MANAGER_AVAILABLE = True
except ImportError:
    CONVERSATION_MANAGER_AVAILABLE = False
    logger.warning("ConversationManager not available - using simple SDK approach")


class ModuleGenerator:
    """Generate code modules from specifications using Claude SDK."""

    def __init__(self, output_dir: Path = Path("amplifier")):
        """Initialize the generator.

        Args:
            output_dir: Base directory for generated modules
        """
        self.output_dir = output_dir
        self._check_claude_sdk()

    def _check_claude_sdk(self) -> None:
        """Check if Claude Code SDK is available."""
        # Check if claude CLI is installed
        try:
            result = subprocess.run(["which", "claude"], capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                raise RuntimeError("Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError("Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")

        # Check Python SDK
        if not CLAUDE_SDK_AVAILABLE:
            raise RuntimeError("Claude Code SDK Python package not found. Install with: pip install claude-code-sdk")

    def extract_module_name(self, contract_content: str) -> str | None:
        """Extract module name from contract specification.

        Looks for patterns like:
        - # Module: module_name
        - ## Module Name: module_name
        - Module: module_name (at start of doc)

        Args:
            contract_content: The contract markdown content

        Returns:
            Module name if found, None otherwise
        """
        # Try different patterns
        patterns = [
            r"^#+ Module:\s*(\S+)",  # Header with Module:
            r"^Module:\s*(\S+)",  # Plain Module: at start
            r"^#+ Module Name:\s*(\S+)",  # Module Name:
            r"^name:\s*(\S+)",  # YAML-style name:
        ]

        for pattern in patterns:
            match = re.search(pattern, contract_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    async def generate_plan_with_workaround(self, contract: str, impl_spec: str) -> str | None:
        """Generate using workaround that avoids plan mode.

        The SDK enters interactive 'plan mode' with certain keywords.
        This workaround uses alternative terminology.
        """
        try:
            from .plan_generator_workaround import generate_module_design

            logger.info("Using workaround to avoid SDK plan mode")
            return await generate_module_design(contract, impl_spec, timeout=120)
        except ImportError:
            logger.warning("Workaround not available, falling back to original method")
            return await self.generate_plan_original(contract, impl_spec)

    async def generate_plan(self, contract: str, impl_spec: str) -> str | None:
        """Generate implementation plan - routes to workaround."""
        return await self.generate_plan_with_workaround(contract, impl_spec)

    async def generate_plan_original(self, contract: str, impl_spec: str) -> str | None:
        """Generate implementation design from specifications.

        Args:
            contract: Contract specification markdown
            impl_spec: Implementation specification markdown

        Returns:
            Implementation plan as text, or None if failed
        """
        # IMPORTANT: Avoid "plan/planning" keywords to prevent SDK from entering interactive mode
        # Use alternative terms like "design", "structure", "architecture"
        prompt = f"""Create a detailed MODULE DESIGN document. Output the complete design directly.

CONTRACT SPECIFICATION:
{contract}

IMPLEMENTATION SPECIFICATION:
{impl_spec}

OUTPUT THE MODULE DESIGN:

## Module Structure

List all directories and files that need to be created, with their purposes:
- Module root directory structure
- Core implementation files
- Test files
- Configuration files
- Documentation files

## Key Components

Detail each major component that needs to be implemented:
- Core classes and their responsibilities
- Key functions and methods
- Data models and structures
- Integration points

## Build Process

Describe the construction sequence:
1. [First step with details]
2. [Second step with details]
... (continue with all steps)

## Testing Strategy

Explain the testing approach:
- Unit test coverage areas
- Integration test scenarios
- Test fixtures and mocks needed
- Validation of contract requirements

## Dependencies

List all required dependencies:
- Python packages needed
- External services or APIs
- Configuration requirements
- Development tools

Generate everything in one response."""

        if not CLAUDE_SDK_AVAILABLE or ClaudeSDKClient is None or ClaudeCodeOptions is None:
            logger.error("Claude SDK not available")
            return None

        try:
            # Use Claude SDK with activity detection and progress feedback
            logger.info("Generating module blueprint with Claude Code SDK...")
            logger.info("This may take 1-3 minutes for complex specifications")
            logger.debug("Note: Avoiding 'plan' keyword to prevent SDK plan mode activation")

            import time

            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt="You are a software architect creating module blueprints and specifications. Respond directly without entering interactive modes.",
                    max_turns=1,
                )
            ) as client:
                await client.query(prompt)

                response = ""
                chunks_received = 0
                last_activity = time.time()
                last_progress = time.time()
                idle_timeout = 60  # 1 minute idle timeout
                total_timeout = 300  # 5 minutes total

                logger.info("Receiving plan response...")

                async with asyncio.timeout(total_timeout):
                    async for message in client.receive_response():
                        current_time = time.time()

                        # Check for idle timeout
                        if current_time - last_activity > idle_timeout:
                            raise TimeoutError(f"No activity for {idle_timeout} seconds")

                        # Debug: log message type to detect plan mode
                        if chunks_received == 0:
                            logger.debug(f"First message type: {type(message)}")
                            # Check if we got SystemMessage indicating plan mode
                            if hasattr(message, "subtype") and getattr(message, "subtype", None) == "init":
                                logger.warning("Detected SystemMessage init - SDK may be in interactive mode")

                        # Extract text from message
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        text = getattr(block, "text", "")
                                        if text:
                                            response += text
                                            chunks_received += 1
                                            last_activity = current_time

                                            # Log progress every 5 seconds or 10 chunks
                                            if current_time - last_progress > 5 or chunks_received % 10 == 0:
                                                logger.info(
                                                    f"Progress: {chunks_received} chunks, "
                                                    f"{len(response)} characters received"
                                                )
                                                last_progress = current_time

                if response.strip():
                    logger.info(f"Plan generation complete: {len(response)} characters")
                    return response
                logger.warning("Received empty plan response")
                return None

        except TimeoutError as e:
            logger.error(f"Plan generation timeout: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return None

    async def generate_module(
        self, module_name: str, contract: str, impl_spec: str, plan: str, force: bool = False
    ) -> bool:
        """Generate the complete module using safe workaround approach.

        Args:
            module_name: Name of the module to generate
            contract: Contract specification
            impl_spec: Implementation specification
            plan: Implementation plan
            force: Whether to overwrite existing module

        Returns:
            True if successful, False otherwise
        """
        module_path = self.output_dir / module_name

        # Create module directory
        if module_path.exists() and not force:
            logger.error(f"Module {module_path} already exists")
            return False

        module_path.mkdir(parents=True, exist_ok=True)

        # Try workaround first to avoid interactive mode issues
        try:
            from .module_generator_workaround import generate_module_code

            logger.info("Using workaround to avoid SDK interactive mode")
            result = await generate_module_code(module_name, module_path, contract, impl_spec, plan, timeout=300)
            if result:
                logger.info(f"Module {module_name} generated successfully via workaround")
                return True
            logger.warning("Workaround generation failed, falling back to original methods")
        except ImportError:
            logger.debug("Workaround not available, using original methods")

        # Prepare the task for modular-builder agent
        task_prompt = f"""Generate a complete Python module following these specifications:

MODULE NAME: {module_name}
OUTPUT DIRECTORY: {module_path}

CONTRACT SPECIFICATION:
{contract}

IMPLEMENTATION SPECIFICATION:
{impl_spec}

IMPLEMENTATION PLAN:
{plan}

REQUIREMENTS:
1. Create all necessary files (__init__.py, core implementation, tests, README.md)
2. Follow the modular "brick" philosophy - self-contained with clear interfaces
3. Include comprehensive docstrings and type hints
4. Create working tests that validate the contract
5. Use simple, direct implementations (ruthless simplicity)
6. Handle errors gracefully with clear messages

Generate the complete, working module now."""

        try:
            # Use Task tool to delegate to modular-builder agent
            from amplifier.utils.task_runner import run_task

            result = await run_task("modular-builder", task_prompt)

            if result and "error" not in result.lower():
                # Save a generation metadata file
                metadata = {
                    "module_name": module_name,
                    "generated_from": {
                        "contract": "provided",
                        "implementation_spec": "provided",
                        "plan": "generated",
                    },
                    "generator_version": "1.0.0",
                }

                metadata_path = module_path / ".generation_metadata.json"
                write_text_with_retry(json.dumps(metadata, indent=2), metadata_path)

                logger.info(f"Module {module_name} generated successfully")
                return True
            logger.error(f"Module generation failed: {result}")
            return False

        except ImportError:
            # Fallback to direct Claude SDK if Task tool not available
            logger.info("Task tool not available, using direct Claude SDK")
            result = await self._generate_with_sdk(module_path, task_prompt)
            return result if result is not None else False

        except Exception as e:
            logger.error(f"Error generating module: {e}")
            return False

    async def _generate_with_sdk(self, module_path: Path, task_prompt: str) -> bool:
        """Fallback generation using Claude SDK directly.

        Now uses enhanced conversation manager for better reliability.

        Args:
            module_path: Path to generate module in
            task_prompt: The generation prompt

        Returns:
            True if successful, False otherwise
        """
        if not CLAUDE_SDK_AVAILABLE or ClaudeSDKClient is None or ClaudeCodeOptions is None:
            logger.error("Claude SDK not available")
            return False

        # Extract module name from path
        module_name = module_path.name

        # Parse contract and spec from the prompt (simplified extraction)
        lines = task_prompt.split("\n")
        contract_start = spec_start = plan_start = -1

        for i, line in enumerate(lines):
            if "CONTRACT:" in line:
                contract_start = i
            elif "IMPLEMENTATION SPECIFICATION:" in line:
                spec_start = i
            elif "IMPLEMENTATION PLAN:" in line:
                plan_start = i

        contract = ""
        spec = ""

        if contract_start >= 0 and spec_start >= 0:
            contract = "\n".join(lines[contract_start + 1 : spec_start])
        if spec_start >= 0 and plan_start >= 0:
            spec = "\n".join(lines[spec_start + 1 : plan_start])

        # Use ConversationManager if available for better multi-turn handling
        if CONVERSATION_MANAGER_AVAILABLE:
            logger.info("Using enhanced conversation manager for generation")
            try:
                async with asyncio.timeout(600):  # 10 minutes total for conversation
                    async with ClaudeSDKClient(
                        options=ClaudeCodeOptions(
                            system_prompt="You are an expert Python developer generating clean, working code modules.",
                            max_turns=10,  # Allow multiple turns for conversation
                        )
                    ) as client:
                        # Use conversation manager
                        conversation = ConversationManager(self.output_dir)
                        result = await conversation.generate_with_conversation(module_name, contract, spec, client)

                        if result:
                            logger.info(f"Module {module_name} generated successfully via conversation")
                            # Save metadata
                            metadata = {
                                "module_name": module_name,
                                "generated_via": "conversation_manager",
                                "chunks_processed": len(conversation.state.completed_chunks),
                                "files_created": conversation.state.files_created,
                                "generator_version": "2.0.0",
                            }
                            metadata_path = module_path / ".generation_metadata.json"
                            write_text_with_retry(json.dumps(metadata, indent=2), metadata_path)

                        return result

            except TimeoutError as e:
                logger.error(f"Conversation-based generation timeout: {e}")
                return False  # Don't fall through - timeout is a failure
            except Exception as e:
                logger.error(f"Conversation manager error: {e}")
                return False  # Don't fall through - error is a failure

        # Fallback to simple single-shot approach
        logger.info("Using simple single-shot SDK approach")
        try:
            async with asyncio.timeout(300):  # 5 minutes for simple generation
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are an expert Python developer generating clean, working code modules.",
                        max_turns=1,  # Single shot - fixed from bug-hunter recommendation
                    )
                ) as client:
                    logger.info("Sending generation prompt to SDK...")
                    await client.query(task_prompt)

                    logger.info("Collecting SDK response...")
                    response = ""
                    response_chunks = 0

                    async for message in client.receive_response():
                        response_chunks += 1
                        if response_chunks % 10 == 0:
                            logger.debug(f"Received {response_chunks} message chunks...")

                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

                    logger.info(f"Collected response of {len(response)} characters")

                    # The SDK should have created the files
                    # Check if basic structure exists - need MORE than just __init__.py
                    required_files = [
                        module_path / "__init__.py",
                        module_path / "core.py",  # At minimum need core implementation
                    ]

                    if all(f.exists() for f in required_files):
                        logger.info(
                            f"Module files created successfully: {[f.name for f in required_files if f.exists()]}"
                        )
                        return True

                    existing = [f.name for f in required_files if f.exists()]
                    missing = [f.name for f in required_files if not f.exists()]
                    logger.warning(f"Incomplete module generation. Found: {existing}, Missing: {missing}")

                    # Try to parse and create files from response
                    logger.info("Files not created directly, attempting to parse response...")
                    return self._parse_and_create_files(module_path, response)

        except TimeoutError as e:
            logger.error(f"Module generation timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"SDK generation error: {e}")
            return False

        # This should never be reached, but satisfies type checker
        return False

    def _parse_and_create_files(self, module_path: Path, response: str) -> bool:
        """Parse response and create module files.

        Simple parser for code blocks in markdown format.

        Args:
            module_path: Directory to create files in
            response: Response containing code blocks

        Returns:
            True if files created, False otherwise
        """
        # Extract code blocks with file markers
        file_pattern = r"```(?:python|py)?\s*#\s*(.+?)\n(.*?)```"
        matches = re.findall(file_pattern, response, re.DOTALL)

        if not matches:
            logger.warning("No code blocks found in response")
            return False

        created_files = []
        for filename, content in matches:
            # Clean filename
            filename = filename.strip()
            if filename.startswith("File:"):
                filename = filename[5:].strip()

            # Create file path
            if "/" in filename:
                file_path = module_path / filename
            else:
                file_path = module_path / filename

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            write_text_with_retry(content.strip(), file_path)
            created_files.append(file_path)
            logger.info(f"Created: {file_path}")

        # Ensure __init__.py exists
        init_file = module_path / "__init__.py"
        if not init_file.exists():
            write_text_with_retry('"""Generated module."""\n', init_file)
            created_files.append(init_file)

        return len(created_files) > 0
