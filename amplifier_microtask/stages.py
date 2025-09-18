"""
Pipeline Stages System

Orchestrates multi-stage development pipelines where each stage
produces outputs that feed into the next stage.
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .agents.requirements import RequirementsAgent
from .orchestrator import Task, run_pipeline_sync
from .session import Session, create_session, save_checkpoint
from .storage import save_json


def extract_json_from_response(response: str) -> dict:
    """Extract JSON from AI response, handling preambles and markdown."""
    if not response:
        return {}

    cleaned = response.strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strip markdown code blocks
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    # Try parsing cleaned version
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # Extract JSON block with regex
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return {}


@dataclass
class Stage:
    """A single stage in a multi-stage pipeline"""

    id: str
    name: str
    description: str
    tasks: List[Task]
    depends_on: List[str] = field(default_factory=list)  # Stage IDs this depends on
    outputs: List[str] = field(default_factory=list)  # Keys that will be saved


@dataclass
class PipelineDefinition:
    """Complete multi-stage pipeline definition"""

    name: str
    description: str
    stages: List[Stage]
    initial_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    """Result from executing a single stage"""

    stage_id: str
    status: str  # "success", "failed", "skipped"
    outputs: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: float = 0.0
    task_timings: Dict[str, float] = field(default_factory=dict)  # Task ID -> duration in seconds


def calculate_task_timeout(base_timeout: int, task_type: str, context: Dict[str, Any]) -> int:
    """Calculate adaptive timeout based on task complexity.

    Args:
        base_timeout: Base timeout in seconds
        task_type: Type of task being executed
        context: Context dictionary with task details

    Returns:
        int: Calculated timeout in seconds (max 600)
    """
    # Base timeouts by task type
    timeouts = {
        "requirements": 180,
        "design": 300,
        "implementation": 240,
        "code_generation": 180,
        "unit_tests": 240,
        "integration_tests": 600,  # Increased for complex interactions
        "validation": 180,
    }

    base = timeouts.get(task_type, base_timeout)

    # Adjust based on context complexity
    if "requirements_analysis" in context:
        req_count = len(context.get("requirements_analysis", {}).get("requirements", []))
        if req_count > 5:
            base = int(base * 1.5)

    # Check for system design complexity
    if "system_design" in context:
        design = context.get("system_design", {})
        if isinstance(design, dict):
            # More components mean more complexity
            component_count = len(design.get("components", []))
            if component_count > 3:
                base = int(base * 1.2)

    # Never exceed 10 minutes
    return min(base, 600)


class PipelineExecutor:
    """Executes multi-stage pipelines with dependency management"""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.requirements_agent = RequirementsAgent()
        self.stage_timings: List[Tuple[str, float]] = []  # Track all stage timings for summary

    def create_requirements_stage(self, user_input: str) -> Stage:
        """
        Create a requirements analysis stage from user input.

        Args:
            user_input: Raw project description

        Returns:
            Stage configured for requirements analysis
        """
        tasks = [
            Task(
                id="analyze_requirements",
                prompt="""
Analyze the following project description and extract structured requirements.

PROJECT: {project_input}

Extract:
1. Main project goal
2. Individual requirements (up to 5 most important)
3. Constraints
4. Assumptions
5. Out of scope items

Return structured JSON with requirements breakdown.
""",
                context_keys=["project_input"],
                save_key="requirements_analysis",
                timeout=120,
            ),
            Task(
                id="prioritize_requirements",
                prompt="""
Given these analyzed requirements, determine implementation order:

{requirements_analysis}

Consider dependencies, priorities, and building foundational pieces first.
Return ordered list of requirement IDs.
""",
                context_keys=["requirements_analysis"],
                save_key="implementation_order",
                timeout=120,
            ),
        ]

        return Stage(
            id="requirements",
            name="Requirements Analysis",
            description="Analyze and prioritize project requirements",
            tasks=tasks,
            outputs=["requirements_analysis", "implementation_order"],
        )

    def create_design_stage(self) -> Stage:
        """Create a design stage that depends on requirements"""
        tasks = [
            Task(
                id="high_level_design",
                prompt="""
Based on these requirements, create a high-level system design:

{requirements_analysis}

Include:
1. Major components/modules
2. Data flow between components
3. Key interfaces
4. Technology choices

Return structured design document.
""",
                context_keys=["requirements_analysis"],
                save_key="system_design",
                timeout=300,  # Increased from 120 for complex designs
            ),
            Task(
                id="identify_risks",
                prompt="""
Given this design, identify technical risks:

{system_design}

List potential risks and mitigation strategies.
""",
                context_keys=["system_design"],
                save_key="risk_assessment",
                timeout=180,  # Increased from 120
            ),
        ]

        return Stage(
            id="design",
            name="System Design",
            description="Create high-level system design and identify risks",
            tasks=tasks,
            depends_on=["requirements"],
            outputs=["system_design", "risk_assessment"],
        )

    def create_implementation_stage(self) -> Stage:
        """Create an implementation planning stage"""
        tasks = [
            Task(
                id="break_into_tasks",
                prompt="""
Break down the first requirement into implementation tasks:

REQUIREMENTS: {requirements_analysis}
DESIGN: {system_design}
PRIORITY ORDER: {implementation_order}

For the highest priority requirement, create 3-5 specific implementation tasks.
Each task should be completable in 1-2 hours.

Return JSON list of tasks with descriptions and acceptance criteria.
""",
                context_keys=["requirements_analysis", "system_design", "implementation_order"],
                save_key="implementation_tasks",
                timeout=240,  # Increased for complex planning
            ),
        ]

        return Stage(
            id="implementation_planning",
            name="Implementation Planning",
            description="Break down requirements into specific tasks",
            tasks=tasks,
            depends_on=["requirements", "design"],
            outputs=["implementation_tasks"],
        )

    def create_code_generation_stage(self) -> Stage:
        """Create a code generation stage that produces a complete amplifier CLI tool"""
        tasks = [
            Task(
                id="analyze_tool_requirements",
                prompt="""
Analyze the requirements and design to create a tool specification.

REQUIREMENTS: {requirements_analysis}
DESIGN: {system_design}
TASKS: {implementation_tasks}

Determine:
1. Tool name (kebab-case, descriptive)
2. Short description (one line)
3. What capabilities it needs (ai_processing, batch_processing, file_io, web_api, data_transformation)
4. Does it process batches of items? (true/false)
5. Does it need AI integration? (true/false)
6. Input file pattern (e.g., "*.md", "*.json", "*.py")
7. Custom command-line options needed
8. AI prompts if AI processing is needed

CRITICAL: Return ONLY the JSON object below. Do NOT include any explanations, preambles, markdown formatting, or text before or after the JSON. Start your response with {{ and end with }}.

{{
    "name": "tool-name",
    "description": "Short tool description",
    "capabilities": ["ai_processing", "batch_processing"],
    "processes_batches": true,
    "needs_ai": true,
    "input_pattern": "*.md",
    "custom_options": [
        {{
            "name": "max-items",
            "default": 5,
            "help": "Maximum items to process"
        }}
    ],
    "ai_system_prompt": "You are a helpful assistant that...",
    "ai_prompt_template": "Process the following content..."
}}
""",
                context_keys=["requirements_analysis", "system_design", "implementation_tasks"],
                save_key="tool_specification",
                timeout=60,
            ),
            Task(
                id="generate_amplifier_tool",
                prompt="__TOOL_GENERATION__",  # Special marker for tool generation
                context_keys=["tool_specification"],
                save_key="generated_tool_info",
                timeout=30,  # Tool generation is mostly template rendering
            ),
        ]

        return Stage(
            id="code_generation",
            name="Code Generation",
            description="Generate actual Python code files from design",
            tasks=tasks,
            depends_on=["implementation_planning"],
            outputs=["tool_specification", "generated_tool_info"],
        )

    def create_test_generation_stage(self) -> Stage:
        """Create a test generation stage that produces pytest tests"""
        tasks = [
            Task(
                id="prepare_test_context",
                prompt="__PREPARE_TEST_CONTEXT__",  # Special marker for test context preparation
                context_keys=["generated_tool_info"],
                save_key="test_context",
                timeout=30,
            ),
            Task(
                id="generate_unit_tests",
                prompt="""
Generate comprehensive pytest unit tests for the generated amplifier tool:

REQUIREMENTS: {requirements_analysis}
TOOL CODE: {test_context}

Create pytest tests that:
1. Test all major functions and methods
2. Include edge cases and error conditions
3. Use fixtures for test data
4. Include parametrized tests where appropriate
5. Have clear test names and docstrings

Return as JSON object mapping test filenames to test code:
{
    "test_cli.py": "import pytest\\n...",
    "test_processor.py": "...",
    "conftest.py": "# Shared fixtures..."
}
""",
                context_keys=["requirements_analysis", "test_context"],
                save_key="test_files",
                timeout=300,  # Increased to 5 minutes for test generation
            ),
            Task(
                id="generate_integration_tests",
                prompt="""
Generate integration tests that verify the system works end-to-end:

SYSTEM DESIGN: {system_design}
REQUIREMENTS: {requirements_analysis}

Create tests that:
1. Test complete user workflows
2. Verify component interactions
3. Test data flow through the system
4. Include performance checks

Return as JSON mapping filenames to test code.
""",
                context_keys=["system_design", "requirements_analysis"],
                save_key="integration_test_files",
                timeout=600,  # Increased to 10 minutes for complex integration test generation
            ),
            Task(
                id="save_test_files",
                prompt="""
Process and prepare test files for saving:

UNIT TESTS: {test_files}
INTEGRATION TESTS: {integration_test_files}

Combine all test files and generate a test execution plan.
Return summary of test coverage and execution instructions.
""",
                context_keys=["test_files", "integration_test_files"],
                save_key="test_generation_summary",
                timeout=120,  # Increased to 2 minutes for save/processing tasks
            ),
        ]

        return Stage(
            id="test_generation",
            name="Test Generation",
            description="Generate pytest tests for the code",
            tasks=tasks,
            depends_on=["code_generation"],
            outputs=["test_files", "integration_test_files", "test_generation_summary"],
        )

    def create_feedback_loop_stage(self) -> Stage:
        """Create a feedback loop stage that runs tests and fixes failures"""
        tasks = [
            Task(
                id="run_feedback_loop",
                prompt="""
Analyze the generated code and test files, then prepare for test execution:

CODE SUMMARY: {code_generation_summary}
TEST SUMMARY: {test_generation_summary}

Return a JSON object with:
{
    "ready_for_testing": true/false,
    "code_directory": "path to generated code",
    "test_directory": "path to test files",
    "files_to_test": ["list of test files to run"]
}
""",
                context_keys=["code_generation_summary", "test_generation_summary"],
                save_key="feedback_preparation",
                timeout=120,  # Increased to 2 minutes for feedback preparation
            ),
        ]

        return Stage(
            id="feedback_loop",
            name="Test Feedback Loop",
            description="Run tests and fix any failures iteratively",
            tasks=tasks,
            depends_on=["code_generation", "test_generation"],
            outputs=["feedback_results", "final_test_status"],
        )

    def _save_code_files(self, result: Any, session: Session) -> Any:
        """Save generated code files to disk"""

        # Create generated code directory
        code_dir = self.workspace / "generated" / session.id[:8]
        code_dir.mkdir(parents=True, exist_ok=True)

        # Save main code files
        if "generated_code_files" in session.data:
            code_files = session.data["generated_code_files"]
            if isinstance(code_files, str):
                try:
                    code_files = json.loads(code_files)
                except json.JSONDecodeError:
                    code_files = {"main.py": code_files}

            if isinstance(code_files, dict):
                for filename, content in code_files.items():
                    file_path = code_dir / filename
                    file_path.write_text(content)
                    print(f"      📝 Generated: {file_path}")

        # Save API code files
        if "api_code_files" in session.data:
            api_files = session.data["api_code_files"]
            if isinstance(api_files, str):
                try:
                    api_files = json.loads(api_files)
                except json.JSONDecodeError:
                    api_files = {}

            if isinstance(api_files, dict):
                for filename, content in api_files.items():
                    file_path = code_dir / filename
                    file_path.write_text(content)
                    print(f"      📝 Generated: {file_path}")

        # Return summary
        return {
            "code_directory": str(code_dir),
            "files_generated": len(list(code_dir.glob("*.py"))),
            "timestamp": datetime.now().isoformat(),
        }

    def _save_test_files(self, result: Any, session: Session) -> Any:
        """Save generated test files to disk"""

        # Create test directory
        test_dir = self.workspace / "tests" / session.id[:8]
        test_dir.mkdir(parents=True, exist_ok=True)

        # Save unit test files
        if "test_files" in session.data:
            test_files = session.data["test_files"]
            if isinstance(test_files, str):
                try:
                    test_files = json.loads(test_files)
                except json.JSONDecodeError:
                    test_files = {"test_main.py": test_files}

            if isinstance(test_files, dict):
                for filename, content in test_files.items():
                    file_path = test_dir / filename
                    file_path.write_text(content)
                    print(f"      🧪 Generated: {file_path}")

        # Save integration test files
        if "integration_test_files" in session.data:
            int_files = session.data["integration_test_files"]
            if isinstance(int_files, str):
                try:
                    int_files = json.loads(int_files)
                except json.JSONDecodeError:
                    int_files = {}

            if isinstance(int_files, dict):
                int_test_dir = test_dir / "integration"
                int_test_dir.mkdir(exist_ok=True)
                for filename, content in int_files.items():
                    file_path = int_test_dir / filename
                    file_path.write_text(content)
                    print(f"      🧪 Generated: {file_path}")

        # Create pytest.ini if it doesn't exist
        pytest_ini = test_dir / "pytest.ini"
        if not pytest_ini.exists():
            pytest_ini.write_text("""[pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
""")
            print(f"      ⚙️  Generated: {pytest_ini}")

        return {
            "test_directory": str(test_dir),
            "test_files_generated": len(list(test_dir.rglob("test_*.py"))),
            "timestamp": datetime.now().isoformat(),
        }

    def _run_feedback_loop(self, session: Session) -> Dict[str, Any]:
        """Run the feedback loop to test and fix code"""

        # Check if we have both code and test files
        if "code_generation_summary" not in session.data or "test_generation_summary" not in session.data:
            return {
                "success": False,
                "error": "Missing code or test generation results",
                "iterations": 0,
            }

        code_summary = session.data.get("code_generation_summary", {})
        test_summary = session.data.get("test_generation_summary", {})

        code_dir = code_summary.get("code_directory")
        test_dir = test_summary.get("test_directory")

        if not code_dir or not test_dir:
            return {
                "success": False,
                "error": "Missing code or test directories",
                "iterations": 0,
            }

        # Create FeedbackLoop instance
        try:
            # Import here to avoid circular dependency
            from .feedback_loop import FeedbackLoop

            feedback_loop = FeedbackLoop(session_id=session.id[:8])

            # Find test and code files to pair
            test_path = Path(test_dir)
            code_path = Path(code_dir)

            test_files = list(test_path.glob("test_*.py"))
            if not test_files:
                # Check if tests already pass (nothing to fix)
                print("   ℹ️  No test files found to run")
                return {
                    "success": True,
                    "message": "No test files to run",
                    "iterations": 0,
                }

            # Run tests for each file
            all_results = []
            any_failures = False

            # First, just run all tests to see if they pass
            print("\n   🧪 Running initial tests...")
            for test_file in test_files:
                # Find corresponding code file
                # test_main.py -> main.py
                code_filename = test_file.name.replace("test_", "")
                code_file = code_path / code_filename

                if not code_file.exists():
                    # Try to find any .py file that's not a test
                    non_test_files = [f for f in code_path.glob("*.py") if not f.name.startswith("test_")]
                    if non_test_files:
                        code_file = non_test_files[0]  # Use first non-test file
                    else:
                        print(f"   ⚠️  No code file found for {test_file.name}")
                        continue

                # Run the test
                import asyncio

                test_result = asyncio.run(feedback_loop.run_tests(str(test_file)))

                print(
                    f"      {test_file.name}: {test_result.passed} passed, {test_result.failed} failed, {test_result.errors} errors"
                )

                # Check if we need to fix anything
                if test_result.failed > 0 or test_result.errors > 0:
                    any_failures = True
                    all_results.append(
                        {
                            "test_file": str(test_file),
                            "code_file": str(code_file),
                            "initial_failures": test_result.failed + test_result.errors,
                        }
                    )

            # If all tests pass initially, we're done!
            if not any_failures:
                print("   ✅ All tests passing! No fixes needed.")
                return {
                    "success": True,
                    "message": "All tests passed on first run",
                    "iterations": 0,
                    "test_results": all_results,
                }

            # Run the feedback loop to fix failures
            print("\n   🔧 Found failures, running feedback loop to fix...")

            test_code_pairs = [(r["test_file"], r["code_file"]) for r in all_results]

            # Run the feedback loop with max 3 iterations
            loop_results = asyncio.run(feedback_loop.batch_feedback_loop(test_code_pairs, max_iterations=3))

            # Get session summary
            summary = feedback_loop.get_session_summary()

            # Check overall success
            success = all(result["success"] for result in loop_results.values())

            return {
                "success": success,
                "iterations": summary.get("total_iterations", 0),
                "fixes_applied": summary.get("total_fixes_applied", 0),
                "results_by_file": loop_results,
                "summary": summary,
            }

        except Exception as e:
            print(f"   ❌ Feedback loop error: {e}")
            return {
                "success": False,
                "error": str(e),
                "iterations": 0,
            }

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def _estimate_remaining_time(self, completed: int, total: int, elapsed: float) -> str:
        """Estimate remaining time based on average task duration"""
        if completed == 0:
            return "calculating..."
        avg_per_task = elapsed / completed
        remaining_tasks = total - completed
        estimated_seconds = remaining_tasks * avg_per_task
        return self._format_duration(estimated_seconds)

    def _execute_tasks_with_progress(self, session: Session, tasks: List[Task]) -> Dict[str, float]:
        """Execute tasks with detailed progress tracking"""
        task_timings = {}
        total_tasks = len(tasks)
        stage_start = time.time()

        for idx, task in enumerate(tasks, 1):
            task_start = time.time()
            elapsed = task_start - stage_start

            # Progress header
            print(f"\n   [{idx}/{total_tasks}] {task.id}...")

            # Show estimated time if not first task
            if idx > 1:
                est_remaining = self._estimate_remaining_time(idx - 1, total_tasks, elapsed)
                print(f"        ⏱️  Elapsed: {self._format_duration(elapsed)} | Est. remaining: {est_remaining}")

            # Execute the task
            try:
                # Run single task through pipeline
                run_pipeline_sync(session, [task])

                # Calculate task duration
                task_duration = time.time() - task_start
                task_timings[task.id] = task_duration

                # Success message with timing
                print(f"        ✓ Completed in {self._format_duration(task_duration)}")

            except Exception as e:
                task_duration = time.time() - task_start
                task_timings[task.id] = task_duration
                print(f"        ✗ Failed after {self._format_duration(task_duration)}: {str(e)[:100]}")
                raise

        # Stage completion summary
        total_elapsed = time.time() - stage_start
        print(f"\n   📊 Stage completed in {self._format_duration(total_elapsed)}")
        if task_timings:
            avg_task_time = sum(task_timings.values()) / len(task_timings)
            print(f"      Average task time: {self._format_duration(avg_task_time)}")

            # Show slowest task
            slowest_task = max(task_timings.items(), key=lambda x: x[1])
            print(f"      Slowest task: {slowest_task[0]} ({self._format_duration(slowest_task[1])})")

        return task_timings

    def execute_stage(self, session: Session, stage: Stage) -> StageResult:
        """
        Execute a single stage of the pipeline.

        Args:
            session: Active session with context
            stage: Stage to execute

        Returns:
            StageResult with outputs or errors
        """
        start_time = datetime.now()

        try:
            # Check dependencies
            for dep_id in stage.depends_on:
                if dep_id not in session.data.get("completed_stages", []):
                    return StageResult(
                        stage_id=stage.id,
                        status="skipped",
                        outputs={},
                        error=f"Dependency '{dep_id}' not completed",
                    )

            # Execute stage tasks
            print(f"\n📊 Executing stage: {stage.name}")
            print(f"   {stage.description}")
            print(f"   Tasks to execute: {len(stage.tasks)}")

            # Add progress messages for long-running stages
            if stage.id in ["code_generation", "test_generation"]:
                print("   ⏳ This may take several minutes...")

            # Run the pipeline for this stage with progress tracking
            task_timings = self._execute_tasks_with_progress(session, stage.tasks)

            # Extract outputs
            outputs = {}
            for key in stage.outputs:
                if key in session.data:
                    outputs[key] = session.data[key]

            # Handle special post-processing for code and test generation stages
            if stage.id == "code_generation":
                summary = self._save_code_files(None, session)
                session.data["code_generation_summary"] = summary
                outputs["code_generation_summary"] = summary
            elif stage.id == "test_generation":
                summary = self._save_test_files(None, session)
                session.data["test_generation_summary"] = summary
                outputs["test_generation_summary"] = summary
            elif stage.id == "feedback_loop":
                # Run the feedback loop
                feedback_results = self._run_feedback_loop(session)
                session.data["feedback_results"] = feedback_results
                outputs["feedback_results"] = feedback_results
                outputs["final_test_status"] = feedback_results.get("success", False)

            # Mark stage as completed
            if "completed_stages" not in session.data:
                session.data["completed_stages"] = []
            session.data["completed_stages"].append(stage.id)

            # Save stage results
            stage_file = self.workspace / "stages" / f"{session.id}_{stage.id}.json"
            stage_file.parent.mkdir(exist_ok=True)
            save_json(outputs, stage_file)

            duration = (datetime.now() - start_time).total_seconds()

            return StageResult(
                stage_id=stage.id,
                status="success",
                outputs=outputs,
                duration_seconds=duration,
                task_timings=task_timings,
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return StageResult(
                stage_id=stage.id,
                status="failed",
                outputs={},
                error=str(e),
                duration_seconds=duration,
                task_timings=getattr(self, "_current_task_timings", {}),
            )

    def execute_pipeline(self, pipeline: PipelineDefinition) -> Dict[str, Any]:
        """
        Execute a complete multi-stage pipeline.

        Args:
            pipeline: Pipeline definition with stages

        Returns:
            Dictionary with all stage results
        """
        # Create session
        session = create_session(self.workspace)
        session.data.update(pipeline.initial_data)
        session.data["pipeline_name"] = pipeline.name
        save_checkpoint(session)

        # Track pipeline start time
        pipeline_start = datetime.now()

        print(f"\n🚀 Starting pipeline: {pipeline.name}")
        print(f"   {pipeline.description}")
        print(f"   Total stages: {len(pipeline.stages)}")
        print(f"   Session: {session.id[:8]}...")
        print(f"   Started at: {pipeline_start.strftime('%H:%M:%S')}\n")

        results = {}
        stage_timings = []  # Track timing for each stage
        completed_stages = 0
        total_stages = len(pipeline.stages)

        # Execute stages in order
        for stage_idx, stage in enumerate(pipeline.stages, 1):
            # Show overall pipeline progress
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"🔄 Pipeline Progress: Stage {stage_idx}/{total_stages}")
            elapsed = (datetime.now() - pipeline_start).total_seconds()
            print(f"   Total elapsed: {self._format_duration(elapsed)}")
            if completed_stages > 0:
                avg_stage_time = elapsed / completed_stages
                est_total = avg_stage_time * total_stages
                est_remaining = est_total - elapsed
                print(f"   Estimated remaining: {self._format_duration(max(0, est_remaining))}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

            stage_start = time.time()
            result = self.execute_stage(session, stage)
            stage_duration = time.time() - stage_start

            results[stage.id] = result
            stage_timings.append((stage.name, stage_duration))

            # Save checkpoint after each stage
            save_checkpoint(session)

            # Report progress with enhanced formatting
            if result.status == "success":
                completed_stages += 1
                print(f"\n   ✅ {stage.name} completed in {self._format_duration(result.duration_seconds)}")
                self.stage_timings.append((stage.name, result.duration_seconds))
            elif result.status == "failed":
                print(f"\n   ❌ {stage.name} failed after {self._format_duration(result.duration_seconds)}")
                if result.error:
                    print(f"      Error: {result.error[:200]}")
                # Continue with other stages that don't depend on this
            else:
                print(f"\n   ⏭️  {stage.name} skipped: {result.error if result.error else 'dependency not met'}")

        # Calculate total pipeline time
        total_pipeline_time = (datetime.now() - pipeline_start).total_seconds()

        # Final enhanced summary
        print("\n" + "═" * 50)
        print("📈 PIPELINE SUMMARY")
        print("═" * 50)

        # Status summary
        successful = sum(1 for r in results.values() if r.status == "success")
        failed = sum(1 for r in results.values() if r.status == "failed")
        skipped = sum(1 for r in results.values() if r.status == "skipped")

        print("\n📊 Stage Results:")
        print(f"   ✅ Successful: {successful}/{total_stages}")
        print(f"   ❌ Failed: {failed}/{total_stages}")
        print(f"   ⏭️  Skipped: {skipped}/{total_stages}")

        # Timing summary
        print("\n⏱️  Timing Analysis:")
        print(f"   Total pipeline time: {self._format_duration(total_pipeline_time)}")

        # Initialize variables for summary
        avg_stage_time = 0
        longest_stage = None

        if self.stage_timings:
            avg_stage_time = sum(t[1] for t in self.stage_timings) / len(self.stage_timings)
            print(f"   Average stage time: {self._format_duration(avg_stage_time)}")

            # Show timing breakdown for each stage
            print("\n   Stage Timing Breakdown:")
            sorted_timings = sorted(self.stage_timings, key=lambda x: x[1], reverse=True)
            for stage_name, duration in sorted_timings:
                percentage = (duration / total_pipeline_time) * 100
                bar_length = int(percentage / 2)  # Scale to 50 chars max
                bar = "█" * bar_length + "░" * (50 - bar_length)
                print(f"   {stage_name:30} {bar} {self._format_duration(duration)} ({percentage:.1f}%)")

            # Identify longest stage
            longest_stage = max(self.stage_timings, key=lambda x: x[1])
            print(f"\n   🐌 Slowest stage: {longest_stage[0]} ({self._format_duration(longest_stage[1])})")

            # Show task-level details for stages that took over 30 seconds
            print("\n   📋 Detailed Task Timings (for stages > 30s):")
            for stage_id, result in results.items():
                if result.status == "success" and result.duration_seconds > 30 and result.task_timings:
                    stage_obj = next((s for s in pipeline.stages if s.id == stage_id), None)
                    if stage_obj:
                        print(f"\n      {stage_obj.name}:")
                        for task_id, task_duration in result.task_timings.items():
                            print(f"         • {task_id}: {self._format_duration(task_duration)}")

        # Completion message
        print(f"\n🏁 Pipeline completed at {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Total duration: {self._format_duration(total_pipeline_time)}")
        print("═" * 50)

        # Save final results
        results_file = self.workspace / "pipelines" / f"{session.id}_results.json"
        results_file.parent.mkdir(exist_ok=True)

        # Convert results to serializable format
        results_data = {}
        for stage_id, result in results.items():
            results_data[stage_id] = {
                "status": result.status,
                "outputs": result.outputs,
                "error": result.error,
                "duration_seconds": result.duration_seconds,
                "task_timings": result.task_timings,
            }

        save_json(
            {
                "pipeline": pipeline.name,
                "session_id": session.id,
                "started": pipeline_start.isoformat(),
                "completed": datetime.now().isoformat(),
                "total_duration_seconds": total_pipeline_time,
                "stages": results_data,
                "summary": {
                    "successful_stages": successful,
                    "failed_stages": failed,
                    "skipped_stages": skipped,
                    "average_stage_time": avg_stage_time if self.stage_timings else 0,
                    "longest_stage": {"name": longest_stage[0], "duration": longest_stage[1]}
                    if longest_stage
                    else None,
                },
            },
            results_file,
        )

        print(f"\n💾 Results saved to: {results_file}")

        return results_data


def create_full_development_pipeline(user_input: str, workspace: Path) -> PipelineDefinition:
    """
    Create a complete development pipeline from user input.

    Args:
        user_input: Project description
        workspace: Workspace path

    Returns:
        Complete pipeline definition
    """
    executor = PipelineExecutor(workspace)

    stages = [
        executor.create_requirements_stage(user_input),
        executor.create_design_stage(),
        executor.create_implementation_stage(),
        executor.create_code_generation_stage(),
        executor.create_test_generation_stage(),
        executor.create_feedback_loop_stage(),
    ]

    return PipelineDefinition(
        name="Full Development Pipeline",
        description="Requirements → Design → Implementation → Code Generation → Test Generation → Feedback Loop",
        stages=stages,
        initial_data={"project_input": user_input},
    )
