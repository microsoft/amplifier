"""
Module Generator V2 - CCSDK Toolkit-based implementation.

A clean implementation using ClaudeSession and defensive utilities for robust
module generation with natural completion and session persistence.
"""

import re
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import extract_code_from_response
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.sessions import SessionManager
from amplifier.ccsdk_toolkit.sessions import SessionState

from .recipe import ModuleRecipe


class ModuleGeneratorV2:
    """Generate code modules using CCSDK toolkit patterns."""

    def __init__(
        self,
        output_dir: Path = Path("amplifier"),
        session_file: Path | None = None,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        """Initialize the generator.

        Args:
            output_dir: Base directory for generated modules
            session_file: Path to session persistence file (optional)
            model: Model to use for generation
        """
        self.output_dir = Path(output_dir)
        self.model = model
        self.recipe = ModuleRecipe()

        # Session management
        self.session_file = session_file
        self.session_manager = SessionManager() if session_file else None
        self.session_state: SessionState | None = None

    def extract_module_name(self, contract: str) -> str | None:
        """Extract module name from contract specification.

        Args:
            contract: Contract specification markdown

        Returns:
            Module name or None if not found
        """
        # Look for patterns like "Module: name" or "## Module: name"
        patterns = [
            r"^#+\s*Module:\s*([a-zA-Z_][a-zA-Z0-9_]*)",
            r"^Module:\s*([a-zA-Z_][a-zA-Z0-9_]*)",
            r"^module:\s*([a-zA-Z_][a-zA-Z0-9_]*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, contract, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    async def generate_with_session(
        self,
        module_name: str,
        contract: str,
        impl_spec: str,
        force: bool = False,
        resume: bool = False,
    ) -> bool:
        """Generate module using CCSDK session with persistence.

        Args:
            module_name: Name of the module to generate
            contract: Contract specification
            impl_spec: Implementation specification
            force: Overwrite existing module if True
            resume: Resume from previous session if True

        Returns:
            True if generation succeeded
        """
        # Prepare module path
        module_path = self.output_dir / module_name
        if module_path.exists() and not force:
            print(f"Module {module_path} already exists. Use --force to overwrite.")
            return False

        # Load or create session state
        if resume and self.session_manager and self.session_file:
            # Load session by ID from filename
            session_id = self.session_file.stem
            self.session_state = self.session_manager.load_session(session_id)
            if self.session_state:
                print(f"Resumed session from {self.session_file}")
            else:
                print("Creating new session (previous not found)")
                self.session_state = self.session_manager.create_session(name=f"module_{module_name}")
        else:
            if self.session_manager:
                self.session_state = self.session_manager.create_session(name=f"module_{module_name}")
            else:
                # Create a minimal session state without manager
                from amplifier.ccsdk_toolkit.sessions import SessionMetadata

                metadata = SessionMetadata(name=f"module_{module_name}")
                self.session_state = SessionState(metadata=metadata)

        # Create session options with proper system prompt
        options = SessionOptions(
            system_prompt="""You are a module code generator. Your role is to output code directly.

IMPORTANT INSTRUCTIONS:
- Output ONLY the requested code or JSON without any preamble or explanation
- Do NOT include phrases like "I'll generate", "Here is", "I will create", etc.
- Start your response directly with the code or JSON data
- For Python code: Begin immediately with imports or class/function definitions
- For JSON: Begin immediately with the opening brace {
- No markdown code blocks unless explicitly requested
- No explanatory text before, during, or after the code""",
            max_turns=1,  # Each task is a single turn
            retry_attempts=3,
            stream_output=False,  # Don't stream for programmatic use
        )

        # Run generation with session
        async with ClaudeSession(options=options) as session:
            # Get tasks in execution order
            tasks = self.recipe.get_execution_order()

            # Track context for prompt formatting
            context: dict[str, Any] = {
                "contract": contract,
                "impl_spec": impl_spec,
                "module_name": module_name,
            }

            # Execute tasks - get completed from context
            completed_tasks = self.session_state.context.get("completed_tasks", []) if self.session_state else []

            for task in tasks:
                # Skip already completed tasks
                if task.name in completed_tasks:
                    print(f"✓ Skipping completed task: {task.name}")
                    continue

                print(f"\n→ Executing: {task.name}")
                print(f"  {task.description}")

                # Format prompt with current context
                prompt = self.recipe.format_prompt(task, context)

                # Send to Claude directly (query already handles isolation)
                print("  → Querying LLM...")
                response = await session.query(prompt)

                # Check for errors
                if response.error:
                    print(f"  Error: {response.error}")
                    return False

                # Log response preview for debugging
                print(
                    f"  ← Response preview: {response.content[:100]}..."
                    if len(response.content) > 100
                    else f"  ← Response: {response.content}"
                )

                # Parse response defensively based on task type
                if "json" in task.checkpoint_key or task.checkpoint_key in ["parsed_contract", "module_design"]:
                    # These tasks expect JSON responses
                    print("  → Parsing JSON response...")
                    result = parse_llm_json(response.content)
                    if result:
                        print("  ✓ Successfully parsed JSON")
                    else:
                        print("  ⚠ Failed to parse JSON, using empty dict")
                        result = {}
                    context[task.checkpoint_key] = result
                elif task.checkpoint_key in ["core_implementation", "models", "init_file", "tests", "readme"]:
                    # These tasks return code/markdown that needs extraction
                    print("  → Extracting code from response...")
                    extracted = extract_code_from_response(
                        response.content, "python" if task.checkpoint_key != "readme" else "markdown"
                    )
                    if extracted != response.content:
                        print(f"  ✓ Extracted code ({len(extracted)} chars from {len(response.content)} chars)")
                    else:
                        print("  ⚠ No preamble detected, using full response")
                    context[task.checkpoint_key] = extracted
                else:
                    # Other tasks - use response as-is
                    print("  → Using raw response")
                    context[task.checkpoint_key] = response.content

                # Mark task complete
                completed_tasks.append(task.name)

                # Save checkpoint for milestone tasks
                if self.session_manager and task.name in self.recipe.get_milestone_tasks():
                    self._save_checkpoint(completed_tasks, context)
                    print("  ✓ Checkpoint saved")

            # Write generated files to disk
            success = await self._write_module_files(module_path, context, force)

            # Save final session state
            if self.session_manager:
                self._save_checkpoint(completed_tasks, context, final=True)

            return success

    def _save_checkpoint(self, completed_tasks: list[str], context: dict[str, Any], final: bool = False) -> None:
        """Save session checkpoint.

        Args:
            completed_tasks: List of completed task names
            context: Current generation context
            final: Whether this is the final checkpoint
        """
        if not self.session_manager or not self.session_file:
            return

        if not self.session_state:
            return

        # Create new metadata with updates
        from amplifier.ccsdk_toolkit.sessions import SessionMetadata

        # Get existing metadata as dict and update it
        metadata_dict = self.session_state.metadata.model_dump()
        metadata_dict["completed_tasks"] = completed_tasks
        metadata_dict["context"] = {
            k: v
            for k, v in context.items()
            if k not in ["contract", "impl_spec"]  # Don't save large inputs
        }
        if final:
            metadata_dict["status"] = "completed"

        # Create new metadata instance
        new_metadata = SessionMetadata(**{k: v for k, v in metadata_dict.items() if k in SessionMetadata.model_fields})

        # Store extra data in the state's context field
        self.session_state.metadata = new_metadata
        self.session_state.context["completed_tasks"] = completed_tasks
        self.session_state.context["generation_context"] = metadata_dict.get("context", {})
        if final:
            self.session_state.context["status"] = "completed"

        # Save using session manager
        self.session_manager.save_session(self.session_state)

    async def _write_module_files(self, module_path: Path, context: dict[str, Any], force: bool) -> bool:
        """Write generated module files to disk.

        Args:
            module_path: Directory to write module to
            context: Generation context with all results
            force: Overwrite existing files if True

        Returns:
            True if files were written successfully
        """
        try:
            # Create module directory
            if module_path.exists() and force:
                import shutil

                shutil.rmtree(module_path)
            module_path.mkdir(parents=True, exist_ok=True)

            # Determine which files to write based on context
            files_to_write = []

            # Core implementation
            if "core_implementation" in context:
                files_to_write.append(("core.py", context["core_implementation"]))

            # Models
            if "models" in context:
                if isinstance(context["models"], dict) and context["models"].get("models_needed") != False:
                    # Models were generated
                    files_to_write.append(("models.py", context["models"]))
                elif isinstance(context["models"], str) and "class" in context["models"]:
                    # Models as string
                    files_to_write.append(("models.py", context["models"]))

            # Init file
            if "init_file" in context:
                files_to_write.append(("__init__.py", context["init_file"]))

            # Tests
            if "tests" in context:
                test_dir = module_path / "tests"
                test_dir.mkdir(exist_ok=True)
                files_to_write.append(("tests/test_core.py", context["tests"]))
                # Create empty __init__.py for tests
                files_to_write.append(("tests/__init__.py", ""))

            # README
            if "readme" in context:
                files_to_write.append(("README.md", context["readme"]))

            # Write all files
            for filepath, content in files_to_write:
                full_path = module_path / filepath
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Clean content if it's wrapped in markdown blocks
                if filepath.endswith(".py"):
                    content = self._clean_code_content(content)

                full_path.write_text(content)
                print(f"  Created: {full_path.relative_to(self.output_dir.parent)}")

            return True

        except Exception as e:
            print(f"Error writing module files: {e}")
            return False

    def _clean_code_content(self, content: str) -> str:
        """Clean code content by removing markdown wrappers.

        Args:
            content: Raw content that might have markdown

        Returns:
            Cleaned code content
        """
        # Remove markdown code blocks
        if "```python" in content:
            # Extract content between ```python and ```
            import re

            pattern = r"```python\s*\n(.*?)\n```"
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                return "\n\n".join(matches)

        # Remove single backticks that might wrap the content
        content = content.strip()
        if content.startswith("```") and content.endswith("```"):
            lines = content.split("\n")
            # Remove first and last line
            return "\n".join(lines[1:-1])

        return content

    async def generate_plan(self, contract: str, impl_spec: str) -> str | None:
        """Generate an implementation plan for review.

        Args:
            contract: Contract specification
            impl_spec: Implementation specification

        Returns:
            Implementation plan as string or None if failed
        """
        options = SessionOptions(
            system_prompt="""You are a planning assistant. Output implementation plans directly.

IMPORTANT: Start your response immediately with the plan content.
Do NOT include preambles like "I'll create", "Here is", "Based on", etc.
Begin directly with the plan content.""",
            max_turns=1,
            retry_attempts=3,
            stream_output=False,
        )

        async with ClaudeSession(options=options) as session:
            prompt = f"""
            Contract Specification:
            {contract}

            Implementation Specification:
            {impl_spec}

            Generate a plan that includes:
            1. Module structure and files needed
            2. Key implementation decisions
            3. External dependencies required
            4. Testing approach
            5. Potential challenges and solutions

            OUTPUT ONLY THE PLAN CONTENT.
            Start immediately with "## Implementation Plan" or similar.
            Do NOT include any preamble or introductory text.
            """

            response = await session.query(prompt)
            return response.content


__all__ = ["ModuleGeneratorV2"]
