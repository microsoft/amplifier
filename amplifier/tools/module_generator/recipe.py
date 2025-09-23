"""
Module Generation Recipe - Task decomposition for module generation.

A self-contained brick that breaks down module generation into focused microtasks.
Each task is designed to fit comfortably within LLM context limits and produce
checkpointable results.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class GenerationTask:
    """A single focused task in the module generation process."""

    name: str
    description: str
    prompt_template: str
    requires: list[str] = field(default_factory=list)  # Task dependencies
    checkpoint_key: str = ""  # Key for saving intermediate results

    def __post_init__(self):
        """Initialize defaults."""
        if not self.checkpoint_key:
            self.checkpoint_key = self.name.lower().replace(" ", "_")


class ModuleRecipe:
    """Breaks down module generation into focused, checkpointable tasks."""

    def __init__(self):
        """Initialize the recipe with task definitions."""
        self.tasks = self._define_tasks()

    def _define_tasks(self) -> list[GenerationTask]:
        """Define the sequence of generation tasks."""
        return [
            GenerationTask(
                name="Parse Contract",
                description="Extract module name and public interface from contract",
                prompt_template="""
                Parse this module contract and extract:
                1. Module name
                2. Public functions/classes with signatures
                3. Key requirements and constraints

                Contract:
                {contract}

                OUTPUT ONLY VALID JSON starting with { and ending with }
                Required keys: module_name, public_interface, requirements
                Do NOT include any explanation, preamble, or text before or after the JSON.
                """,
                requires=[],
                checkpoint_key="parsed_contract",
            ),
            GenerationTask(
                name="Design Structure",
                description="Design the internal module structure",
                prompt_template="""
                Based on this contract and implementation spec, design the module structure:

                Contract Summary:
                {parsed_contract}

                Implementation Spec:
                {impl_spec}

                Design:
                1. File structure (which files needed)
                2. Internal architecture (how components connect)
                3. Key implementation decisions

                OUTPUT ONLY VALID JSON starting with { and ending with }
                Required keys: files, architecture, decisions
                Do NOT include any explanation or text before or after the JSON.
                """,
                requires=["Parse Contract"],
                checkpoint_key="module_design",
            ),
            GenerationTask(
                name="Generate Core Implementation",
                description="Generate the main implementation file(s)",
                prompt_template="""
                Module Design:
                {module_design}

                Contract:
                {contract}

                Implementation Requirements:
                {impl_spec}

                OUTPUT ONLY THE PYTHON CODE. Start immediately with imports or docstrings.
                Do NOT include any preamble like "I'll generate" or "Here is the code".
                Do NOT wrap in markdown code blocks.
                Begin your response with Python code only (imports, classes, or functions).
                """,
                requires=["Design Structure"],
                checkpoint_key="core_implementation",
            ),
            GenerationTask(
                name="Generate Models",
                description="Generate data models if needed",
                prompt_template="""
                Module Design:
                {module_design}

                Contract Interface:
                {parsed_contract}

                If models are needed:
                OUTPUT ONLY THE PYTHON CODE for Pydantic models or dataclasses.
                Start immediately with imports. No preamble or explanation.

                If no models are needed:
                OUTPUT ONLY this exact JSON: {{"models_needed": false}}

                Do NOT include any text before or after your output.
                """,
                requires=["Design Structure"],
                checkpoint_key="models",
            ),
            GenerationTask(
                name="Generate Tests",
                description="Generate comprehensive test suite",
                prompt_template="""
                Core Implementation:
                {core_implementation}

                Contract Requirements:
                {parsed_contract}

                Generate pytest tests that verify:
                1. Contract compliance
                2. Basic functionality
                3. Edge cases
                4. Error handling

                OUTPUT ONLY THE PYTHON TEST CODE.
                Start immediately with imports (import pytest, etc.).
                Do NOT include any preamble or explanation.
                Do NOT wrap in markdown code blocks.
                """,
                requires=["Generate Core Implementation"],
                checkpoint_key="tests",
            ),
            GenerationTask(
                name="Generate Init File",
                description="Generate __init__.py with public exports",
                prompt_template="""
                Contract Interface:
                {parsed_contract}

                Module Structure:
                {module_design}

                Create __init__.py with:
                1. Module docstring
                2. Imports from internal modules
                3. __all__ list with public exports only

                OUTPUT ONLY THE PYTHON CODE for __init__.py.
                Start immediately with docstring or imports.
                Do NOT include any preamble like "I'll create" or "Here is".
                Do NOT wrap in markdown code blocks.
                """,
                requires=["Generate Core Implementation"],
                checkpoint_key="init_file",
            ),
            GenerationTask(
                name="Generate README",
                description="Generate comprehensive README documentation",
                prompt_template="""
                Contract:
                {contract}

                Module Design:
                {module_design}

                Include:
                1. Module purpose and contract
                2. Installation/usage instructions
                3. API documentation
                4. Examples
                5. Testing instructions

                OUTPUT ONLY THE MARKDOWN CONTENT for README.md.
                Start immediately with # Module Name or similar heading.
                Do NOT include any preamble or "I'll generate" text.
                Do NOT wrap in markdown code blocks.
                """,
                requires=["Design Structure"],
                checkpoint_key="readme",
            ),
        ]

    def get_task(self, name: str) -> GenerationTask | None:
        """Get a specific task by name."""
        for task in self.tasks:
            if task.name == name:
                return task
        return None

    def get_next_task(self, completed_tasks: list[str]) -> GenerationTask | None:
        """Get the next task that can be executed given completed tasks."""
        for task in self.tasks:
            # Skip if already completed
            if task.name in completed_tasks:
                continue

            # Check if all dependencies are satisfied
            if all(req in completed_tasks for req in task.requires):
                return task

        return None

    def get_execution_order(self) -> list[GenerationTask]:
        """Get tasks in a valid execution order respecting dependencies."""
        ordered = []
        completed = set()

        while len(ordered) < len(self.tasks):
            for task in self.tasks:
                if task.name in completed:
                    continue

                # Check if all dependencies are satisfied
                if all(req in completed for req in task.requires):
                    ordered.append(task)
                    completed.add(task.name)
                    break
            else:
                # No task could be added - circular dependency or error
                remaining = [t.name for t in self.tasks if t.name not in completed]
                raise ValueError(f"Circular dependency or missing tasks: {remaining}")

        return ordered

    def format_prompt(self, task: GenerationTask, context: dict[str, Any]) -> str:
        """Format a task prompt with the given context."""
        # Extract only the context keys needed for this prompt
        prompt = task.prompt_template

        # Simple template replacement for context values
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in prompt:
                # Convert value to string, handling different types
                if isinstance(value, dict):
                    import json

                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value)
                prompt = prompt.replace(placeholder, value_str)

        return prompt

    def get_milestone_tasks(self) -> list[str]:
        """Get task names that represent major milestones worth checkpointing."""
        # These are the critical tasks that we definitely want to save
        return [
            "Parse Contract",
            "Design Structure",
            "Generate Core Implementation",
            "Generate Tests",
        ]


__all__ = ["ModuleRecipe", "GenerationTask"]
