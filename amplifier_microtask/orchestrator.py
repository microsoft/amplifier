"""
Module: orchestrator

Purpose: Coordinate microtask execution pipeline

This module orchestrates the execution of microtask pipelines with full checkpoint
and recovery support. It executes tasks sequentially, saving state after each task,
and can resume from any point in case of interruption.
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from amplifier_microtask.agent import execute_task, SDKNotAvailableError
from amplifier_microtask.session import (
    Session,
    add_completed_task,
    update_session_stage,
    update_session_status,
    update_session_data,
)
from amplifier_microtask.storage import append_jsonl


class PipelineError(Exception):
    """Raised when pipeline execution fails with partial results."""

    def __init__(self, message: str, partial_results: Dict[str, Any]):
        super().__init__(message)
        self.partial_results = partial_results


@dataclass
class Task:
    """Definition of a single task in the pipeline.

    Attributes:
        id: Unique task identifier
        prompt: The prompt to send to the agent
        context_keys: List of session data keys to include as context
        save_key: Where to store the result in session data
        required: If True, pipeline stops on failure. If False, continues.
        timeout: Task-specific timeout in seconds (default: 120)
    """

    id: str
    prompt: str
    context_keys: List[str]  # Which session data to include
    save_key: str  # Where to store result in session
    required: bool = True  # If False, failure doesn't stop pipeline
    timeout: int = 120  # Task-specific timeout


@dataclass
class TaskResult:
    """Result from executing a single task.

    Attributes:
        task_id: The task identifier
        success: Whether the task completed successfully
        output: The task output (if successful)
        error: Error message (if failed)
    """

    task_id: str
    success: bool
    output: str = ""
    error: Optional[str] = None


async def run_pipeline(session: Session, tasks: List[Task]) -> Dict[str, Any]:
    """Execute a sequence of tasks with checkpoint recovery.

    Args:
        session: The session to use for state tracking
        tasks: List of tasks to execute

    Returns:
        Dictionary containing all task results

    Raises:
        PipelineError: If a required task fails (includes partial results)
    """
    results = {}

    # Start from where we left off
    start_index = recover_from_checkpoint(session, tasks)

    # Execute tasks from the start point
    for i, task in enumerate(tasks[start_index:], start=start_index):
        # Update stage
        update_session_stage(session, f"task_{task.id}")

        # Execute the task
        result = await execute_stage(session, task)
        results[task.id] = result

        # Save result to session data if successful
        if result.success and task.save_key:
            update_session_data(session, task.save_key, result.output)

        # Mark task as completed (even if failed, we don't retry it)
        add_completed_task(session, task.id)

        # Log the result
        _log_task_result(session, result)

        # Stop pipeline if required task failed
        if not result.success and task.required:
            update_session_status(session, "failed")
            raise PipelineError(f"Required task '{task.id}' failed: {result.error}", results)

    # All tasks completed successfully
    update_session_status(session, "completed")
    return results


async def execute_stage(session: Session, task: Task) -> TaskResult:
    """Execute a single task with error recovery.

    Args:
        session: The session containing context data
        task: The task to execute

    Returns:
        TaskResult with execution outcome
    """
    try:
        # Build context from session data
        context = {}
        for key in task.context_keys:
            if key in session.data:
                context[key] = session.data[key]

        # Add task_id and stage_name for progress monitoring
        context["task_id"] = task.id
        context["stage_name"] = session.current_stage or task.id

        # Check if this is a special operation
        if task.prompt == "__FILE_OPERATION__":
            # Handle file operations directly without AI
            output = await _handle_file_operation(task.id, context, session)
        elif task.prompt == "__TOOL_GENERATION__":
            # Handle tool generation
            output = await _handle_tool_generation(context, session)
        elif task.prompt == "__PREPARE_TEST_CONTEXT__":
            # Handle test context preparation
            output = await _prepare_test_context(context, session)
        else:
            # Execute normal AI task
            output = await execute_task(task.prompt, context, task.timeout)

        return TaskResult(
            task_id=task.id,
            success=True,
            output=output,
        )

    except SDKNotAvailableError as e:
        # SDK not available is a special case
        return TaskResult(
            task_id=task.id,
            success=False,
            error=f"SDK not available: {str(e)}",
        )

    except TimeoutError:
        # Task timed out
        return TaskResult(
            task_id=task.id,
            success=False,
            error=f"Task timed out after {task.timeout} seconds",
        )

    except Exception as e:
        # Generic error handling
        return TaskResult(
            task_id=task.id,
            success=False,
            error=str(e),
        )


def recover_from_checkpoint(session: Session, tasks: List[Task]) -> int:
    """Determine where to resume pipeline execution.

    Args:
        session: The session with completed tasks
        tasks: The full list of pipeline tasks

    Returns:
        Index of the first task to execute (0 if starting fresh)
    """
    if not session.completed_tasks:
        return 0

    # Find the last completed task in our pipeline
    task_ids = [task.id for task in tasks]
    last_index = -1

    for task_id in session.completed_tasks:
        if task_id in task_ids:
            last_index = task_ids.index(task_id)

    # Resume from the next task after the last completed one
    return last_index + 1 if last_index >= 0 else 0


def run_pipeline_sync(session: Session, tasks: List[Task]) -> Dict[str, Any]:
    """Synchronous wrapper for run_pipeline.

    Args:
        session: The session to use for state tracking
        tasks: List of tasks to execute

    Returns:
        Dictionary containing all task results

    Raises:
        PipelineError: If a required task fails (includes partial results)
    """
    try:
        # Check if we're already in an event loop
        asyncio.get_running_loop()
        # If we are, we can't use asyncio.run()
        raise RuntimeError("run_pipeline_sync cannot be called from an async context. Use run_pipeline directly.")
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(run_pipeline(session, tasks))


def _log_task_result(session: Session, result: TaskResult) -> None:
    """Log task result to session's task log.

    Args:
        session: The session to log to
        result: The task result to log
    """
    log_file = session.workspace / ".sessions" / f"{session.id}_tasks.jsonl"

    log_entry = {
        "task_id": result.task_id,
        "success": result.success,
        "error": result.error,
        "output_length": len(result.output) if result.output else 0,
    }

    append_jsonl(log_entry, log_file)


async def _handle_tool_generation(context: Dict[str, Any], session: Session) -> str:
    """Handle tool generation without using AI.

    Args:
        context: The context containing tool specification
        session: The session for workspace information

    Returns:
        JSON string with tool generation results
    """
    import json
    from amplifier_microtask.agents.tool_generator import ToolGeneratorAgent, ToolSpecification
    from amplifier_microtask.stages import extract_json_from_response

    # Get tool specification from context
    tool_spec_json = context.get("tool_specification", "{}")
    if isinstance(tool_spec_json, str):
        spec_data = extract_json_from_response(tool_spec_json)
        if not spec_data:
            return json.dumps(
                {
                    "status": "error",
                    "message": "Could not parse tool specification",
                    "raw_content": tool_spec_json[:500],
                }
            )
    else:
        spec_data = tool_spec_json

    # Create tool specification object
    spec = ToolSpecification(
        name=spec_data.get("name", "unnamed-tool"),
        description=spec_data.get("description", "Generated tool"),
        capabilities=spec_data.get("capabilities", []),
        processes_batches=spec_data.get("processes_batches", False),
        input_pattern=spec_data.get("input_pattern", "*.md"),
        custom_options=spec_data.get("custom_options", []),
        ai_system_prompt=spec_data.get("ai_system_prompt"),
        ai_prompt_template=spec_data.get("ai_prompt_template"),
    )

    # Generate the tool
    generator = ToolGeneratorAgent(workspace=session.workspace)
    generated_tool = generator.generate_tool_files(spec)

    # Check if generation failed
    if generated_tool.status == "failed":
        error_msg = f"Tool generation failed: {generated_tool.error}"
        if not generated_tool.files_created or len(generated_tool.files_created) == 0:
            error_msg += " (0 files generated)"
        raise RuntimeError(error_msg)

    # Check if no files were created (shouldn't happen if status is "generated", but be defensive)
    if not generated_tool.files_created or len(generated_tool.files_created) == 0:
        raise RuntimeError(f"Tool generation produced 0 files for '{generated_tool.tool_name}'")

    # Return generation results
    result = {
        "status": generated_tool.status,
        "tool_name": generated_tool.tool_name,
        "tool_path": generated_tool.tool_path,
        "files_created": generated_tool.files_created,
        "message": f"Tool '{generated_tool.tool_name}' generated at {generated_tool.tool_path}",
    }

    if generated_tool.error:
        result["error"] = generated_tool.error

    return json.dumps(result, indent=2)


async def _prepare_test_context(context: Dict[str, Any], session: Session) -> str:
    """Prepare test context by reading generated tool files.

    Args:
        context: The context containing generated_tool_info
        session: The session for workspace information

    Returns:
        JSON string with tool code files
    """
    import json
    from pathlib import Path

    # Get tool info from context
    tool_info = context.get("generated_tool_info", "{}")
    if isinstance(tool_info, str):
        try:
            tool_info = json.loads(tool_info)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid tool info"})

    # Get the tool path
    tool_path = tool_info.get("tool_path", "")
    if not tool_path or tool_path == "error":
        return json.dumps({"error": "No valid tool path found"})

    tool_dir = Path(tool_path)
    if not tool_dir.exists():
        return json.dumps({"error": f"Tool directory not found: {tool_path}"})

    # Read all Python files from the tool directory
    code_files = {}
    for py_file in tool_dir.glob("*.py"):
        try:
            content = py_file.read_text()
            code_files[py_file.name] = content
        except Exception as e:
            code_files[py_file.name] = f"# Error reading file: {e}"

    # Also check for subdirectories with Python files
    for subdir in tool_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("__"):
            for py_file in subdir.glob("*.py"):
                try:
                    content = py_file.read_text()
                    rel_path = py_file.relative_to(tool_dir)
                    code_files[str(rel_path)] = content
                except Exception as e:
                    code_files[str(rel_path)] = f"# Error reading file: {e}"

    return json.dumps(code_files)


async def _handle_file_operation(task_id: str, context: Dict[str, Any], session: Session) -> str:
    """Handle file operations without using AI.

    Args:
        task_id: The ID of the file operation task
        context: The context containing file data
        session: The session for workspace information

    Returns:
        A summary of the files that were saved
    """
    import json

    # For the save_generated_code task, save the generated files
    if task_id == "save_generated_code":
        generated_dir = session.workspace / "generated"
        generated_dir.mkdir(exist_ok=True)

        files_saved = []

        # Save generated code files
        if "generated_code_files" in context:
            code_files = context["generated_code_files"]
            if isinstance(code_files, str):
                try:
                    code_files = json.loads(code_files)
                except json.JSONDecodeError:
                    code_files = {}

            for filename, content in code_files.items():
                file_path = generated_dir / filename
                file_path.write_text(content)
                files_saved.append(str(file_path))

        # Save API code files
        if "api_code_files" in context:
            api_files = context["api_code_files"]
            if isinstance(api_files, str):
                try:
                    api_files = json.loads(api_files)
                except json.JSONDecodeError:
                    api_files = {}

            for filename, content in api_files.items():
                file_path = generated_dir / filename
                file_path.write_text(content)
                files_saved.append(str(file_path))

        # Return a summary of what was saved
        summary = {
            "status": "success",
            "files_saved": files_saved,
            "total_files": len(files_saved),
            "output_directory": str(generated_dir),
        }

        return json.dumps(summary, indent=2)

    # Default case for unknown file operations
    return json.dumps({"status": "success", "message": f"File operation {task_id} completed"})


def create_simple_pipeline(prompts: List[str]) -> List[Task]:
    """Helper to create a simple pipeline from a list of prompts.

    Each task will be given an auto-generated ID and will save its result
    to a key matching its ID.

    Args:
        prompts: List of prompt strings

    Returns:
        List of Task objects ready for execution
    """
    tasks = []
    for i, prompt in enumerate(prompts):
        task_id = f"task_{i + 1}"
        tasks.append(
            Task(
                id=task_id,
                prompt=prompt,
                context_keys=[],  # No context by default
                save_key=task_id,  # Save to session data with task ID as key
                required=True,  # All tasks required by default
            )
        )
    return tasks


def create_chained_pipeline(prompts: List[str]) -> List[Task]:
    """Helper to create a pipeline where each task uses the previous result.

    Each task (except the first) will receive the previous task's output
    as context.

    Args:
        prompts: List of prompt strings

    Returns:
        List of Task objects with chained context
    """
    tasks = []
    for i, prompt in enumerate(prompts):
        task_id = f"task_{i + 1}"
        context_keys = []

        # After the first task, include previous task's result as context
        if i > 0:
            context_keys = [f"task_{i}"]

        tasks.append(
            Task(
                id=task_id,
                prompt=prompt,
                context_keys=context_keys,
                save_key=task_id,
                required=True,
            )
        )
    return tasks
