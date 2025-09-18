"""
Parallel Pipeline Executor

Executes independent pipeline stages concurrently for improved performance.
Analyzes stage dependencies to identify parallelizable stages and runs them
using asyncio for maximum efficiency.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

from .orchestrator import run_pipeline, PipelineError
from .session import Session, create_session, save_checkpoint
from .stages import Stage, StageResult, PipelineDefinition
from .storage import save_json


@dataclass
class ParallelGroup:
    """A group of stages that can be executed in parallel"""

    stages: List[Stage]
    level: int  # Execution level (0 = first, 1 = second, etc.)


@dataclass
class ExecutionStatus:
    """Detailed execution status for monitoring and reporting"""

    total_stages: int
    completed: int = 0
    in_progress: int = 0
    failed: int = 0
    skipped: int = 0
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    parallel_groups: List[ParallelGroup] = field(default_factory=list)
    total_duration_seconds: float = 0.0


class ParallelPipelineExecutor:
    """Executes multi-stage pipelines with parallel execution of independent stages"""

    def __init__(self, workspace: Path):
        """
        Initialize the parallel executor.

        Args:
            workspace: Path to the workspace directory
        """
        self.workspace = workspace
        self.execution_status: Optional[ExecutionStatus] = None

    def find_parallel_stages(self, pipeline: PipelineDefinition) -> List[ParallelGroup]:
        """
        Analyze pipeline to identify stages that can run in parallel.

        Uses topological sorting to group stages by dependency level.
        Stages at the same level have no dependencies on each other
        and can run concurrently.

        Args:
            pipeline: Pipeline definition with stages and dependencies

        Returns:
            List of ParallelGroup objects, ordered by execution level
        """
        # Build dependency graph
        stages_by_id = {stage.id: stage for stage in pipeline.stages}

        # Calculate in-degree (number of dependencies) for each stage
        in_degree = defaultdict(int)
        dependents = defaultdict(list)

        for stage in pipeline.stages:
            in_degree[stage.id] = len(stage.depends_on)
            for dep_id in stage.depends_on:
                if dep_id in stages_by_id:
                    dependents[dep_id].append(stage.id)

        # Topological sort with level tracking
        parallel_groups = []
        level = 0

        while True:
            # Find all stages with no remaining dependencies
            ready_stages = []
            for stage_id, degree in in_degree.items():
                if degree == 0 and stage_id in stages_by_id:
                    ready_stages.append(stages_by_id[stage_id])

            if not ready_stages:
                break

            # Create parallel group for this level
            parallel_groups.append(ParallelGroup(stages=ready_stages, level=level))

            # Remove processed stages and update dependencies
            for stage in ready_stages:
                del stages_by_id[stage.id]
                del in_degree[stage.id]

                # Reduce in-degree for dependent stages
                for dependent_id in dependents[stage.id]:
                    if dependent_id in in_degree:
                        in_degree[dependent_id] -= 1

            level += 1

        return parallel_groups

    async def execute_stage_async(self, session: Session, stage: Stage) -> StageResult:
        """
        Execute a single stage asynchronously.

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

            print(f"   📊 Starting stage: {stage.name}")

            # Execute the pipeline of tasks for this stage
            try:
                await run_pipeline(session, stage.tasks)

                # Extract outputs
                outputs = {}
                for key in stage.outputs:
                    if key in session.data:
                        outputs[key] = session.data[key]

                # Mark stage as completed
                if "completed_stages" not in session.data:
                    session.data["completed_stages"] = []
                session.data["completed_stages"].append(stage.id)

                # Save stage results immediately (incremental save pattern)
                stage_file = self.workspace / "stages" / f"{session.id}_{stage.id}.json"
                stage_file.parent.mkdir(exist_ok=True)
                save_json(outputs, stage_file)

                # Save checkpoint after stage completion
                save_checkpoint(session)

                duration = (datetime.now() - start_time).total_seconds()

                print(f"   ✅ {stage.name} completed ({duration:.1f}s)")

                return StageResult(
                    stage_id=stage.id,
                    status="success",
                    outputs=outputs,
                    duration_seconds=duration,
                )

            except PipelineError as e:
                # Pipeline error includes partial results
                duration = (datetime.now() - start_time).total_seconds()
                print(f"   ❌ {stage.name} failed: {str(e)}")

                return StageResult(
                    stage_id=stage.id,
                    status="failed",
                    outputs=e.partial_results if hasattr(e, "partial_results") else {},
                    error=str(e),
                    duration_seconds=duration,
                )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"   ❌ {stage.name} failed: {str(e)}")

            return StageResult(
                stage_id=stage.id,
                status="failed",
                outputs={},
                error=str(e),
                duration_seconds=duration,
            )

    async def execute_parallel(
        self, stages: List[Stage], session: Session, timeout_per_stage: int = 120
    ) -> Dict[str, StageResult]:
        """
        Execute multiple stages in parallel.

        Uses asyncio.gather to run all stages concurrently.
        Each stage is given its own timeout to prevent hanging.

        Args:
            stages: List of stages to execute in parallel
            session: Active session with context
            timeout_per_stage: Timeout in seconds for each stage

        Returns:
            Dictionary mapping stage IDs to their results
        """
        print(f"\n🚀 Executing {len(stages)} stages in parallel")

        # Create tasks with timeout for each stage
        async def execute_with_timeout(stage: Stage) -> StageResult:
            try:
                async with asyncio.timeout(timeout_per_stage):
                    return await self.execute_stage_async(session, stage)
            except asyncio.TimeoutError:
                print(f"   ⏱️ {stage.name} timed out after {timeout_per_stage}s")
                return StageResult(
                    stage_id=stage.id,
                    status="failed",
                    outputs={},
                    error=f"Stage timed out after {timeout_per_stage} seconds",
                    duration_seconds=timeout_per_stage,
                )

        # Execute all stages concurrently
        # Use return_exceptions=True to continue even if some fail
        tasks = [execute_with_timeout(stage) for stage in stages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        stage_results = {}
        for stage, result in zip(stages, results):
            if isinstance(result, Exception):
                # Handle unexpected exceptions
                stage_results[stage.id] = StageResult(
                    stage_id=stage.id,
                    status="failed",
                    outputs={},
                    error=str(result),
                )
            else:
                stage_results[stage.id] = result

        return stage_results

    async def execute_pipeline_async(self, pipeline_def: PipelineDefinition) -> ExecutionStatus:
        """
        Execute a complete pipeline with parallel stage execution.

        Analyzes dependencies, groups parallelizable stages, and executes
        them level by level with concurrent execution within each level.

        Args:
            pipeline_def: Pipeline definition with stages

        Returns:
            ExecutionStatus with detailed results
        """
        start_time = datetime.now()

        # Create session
        session = create_session(self.workspace)
        session.data.update(pipeline_def.initial_data)
        session.data["pipeline_name"] = pipeline_def.name
        save_checkpoint(session)

        print(f"\n🚀 Starting parallel pipeline: {pipeline_def.name}")
        print(f"   {pipeline_def.description}")
        print(f"   Total stages: {len(pipeline_def.stages)}")
        print(f"   Session: {session.id[:8]}...")

        # Find parallel groups
        parallel_groups = self.find_parallel_stages(pipeline_def)

        # Initialize execution status
        self.execution_status = ExecutionStatus(total_stages=len(pipeline_def.stages), parallel_groups=parallel_groups)

        print(f"\n📊 Execution plan: {len(parallel_groups)} parallel groups")
        for i, group in enumerate(parallel_groups):
            stage_names = ", ".join(s.name for s in group.stages)
            print(f"   Level {i}: {stage_names}")

        # Execute groups in order
        all_results = {}

        for group_idx, group in enumerate(parallel_groups):
            print(f"\n🔄 Executing level {group_idx} ({len(group.stages)} stages)")

            # Update in-progress count
            self.execution_status.in_progress = len(group.stages)

            # Execute stages in this group concurrently
            group_results = await self.execute_parallel(group.stages, session, timeout_per_stage=120)

            # Update results and status
            all_results.update(group_results)
            self.execution_status.stage_results.update(group_results)

            # Update counters
            self.execution_status.in_progress = 0
            for result in group_results.values():
                if result.status == "success":
                    self.execution_status.completed += 1
                elif result.status == "failed":
                    self.execution_status.failed += 1
                elif result.status == "skipped":
                    self.execution_status.skipped += 1

            # Save intermediate results after each group
            self._save_intermediate_results(session.id, all_results)

        # Calculate total duration
        self.execution_status.total_duration_seconds = (datetime.now() - start_time).total_seconds()

        # Final summary
        self._print_summary()

        # Save final results
        self._save_final_results(session.id, pipeline_def.name)

        return self.execution_status

    def execute_pipeline(self, pipeline_def: PipelineDefinition) -> Dict[str, Any]:
        """
        Synchronous wrapper for pipeline execution.

        Args:
            pipeline_def: Pipeline definition with stages

        Returns:
            Dictionary with all stage results
        """
        try:
            # Check if we're already in an event loop
            asyncio.get_running_loop()
            # If we are, we can't use asyncio.run()
            raise RuntimeError(
                "execute_pipeline cannot be called from an async context. Use execute_pipeline_async directly."
            )
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            status = asyncio.run(self.execute_pipeline_async(pipeline_def))

            # Convert to serializable format
            results_data = {}
            for stage_id, result in status.stage_results.items():
                results_data[stage_id] = {
                    "status": result.status,
                    "outputs": result.outputs,
                    "error": result.error,
                    "duration_seconds": result.duration_seconds,
                }

            return results_data

    def get_execution_status(self) -> Optional[ExecutionStatus]:
        """
        Get the current execution status.

        Returns:
            ExecutionStatus if pipeline has been executed, None otherwise
        """
        return self.execution_status

    def _save_intermediate_results(self, session_id: str, results: Dict[str, StageResult]):
        """Save intermediate results after each parallel group"""
        results_file = self.workspace / "pipelines" / f"{session_id}_intermediate.json"
        results_file.parent.mkdir(exist_ok=True)

        # Convert to serializable format
        results_data = {}
        for stage_id, result in results.items():
            results_data[stage_id] = {
                "status": result.status,
                "outputs": result.outputs,
                "error": result.error,
                "duration_seconds": result.duration_seconds,
            }

        save_json(results_data, results_file)

    def _save_final_results(self, session_id: str, pipeline_name: str):
        """Save final execution results"""
        if not self.execution_status:
            return

        results_file = self.workspace / "pipelines" / f"{session_id}_results.json"
        results_file.parent.mkdir(exist_ok=True)

        # Convert results to serializable format
        results_data = {}
        for stage_id, result in self.execution_status.stage_results.items():
            results_data[stage_id] = {
                "status": result.status,
                "outputs": result.outputs,
                "error": result.error,
                "duration_seconds": result.duration_seconds,
            }

        # Save complete execution data
        save_json(
            {
                "pipeline": pipeline_name,
                "session_id": session_id,
                "completed": datetime.now().isoformat(),
                "total_duration_seconds": self.execution_status.total_duration_seconds,
                "summary": {
                    "total": self.execution_status.total_stages,
                    "completed": self.execution_status.completed,
                    "failed": self.execution_status.failed,
                    "skipped": self.execution_status.skipped,
                },
                "parallel_groups": [
                    {"level": group.level, "stages": [s.id for s in group.stages]}
                    for group in self.execution_status.parallel_groups
                ],
                "stages": results_data,
            },
            results_file,
        )

        print(f"\n💾 Results saved to: {results_file}")

    def _print_summary(self):
        """Print execution summary"""
        if not self.execution_status:
            return

        print("\n📈 Pipeline Execution Summary:")
        print(f"   ✅ Successful: {self.execution_status.completed}")
        print(f"   ❌ Failed: {self.execution_status.failed}")
        print(f"   ⏭️  Skipped: {self.execution_status.skipped}")
        print(f"   ⏱️  Total duration: {self.execution_status.total_duration_seconds:.1f}s")

        # Calculate time saved by parallelization
        sequential_time = sum(r.duration_seconds for r in self.execution_status.stage_results.values())
        time_saved = sequential_time - self.execution_status.total_duration_seconds

        if time_saved > 0:
            speedup = sequential_time / self.execution_status.total_duration_seconds
            print(f"   🚀 Time saved: {time_saved:.1f}s (speedup: {speedup:.1f}x)")


def identify_parallelizable_stages(stages: List[Stage]) -> List[Set[str]]:
    """
    Helper function to identify which stages can run in parallel.

    Args:
        stages: List of stages with dependencies

    Returns:
        List of sets, each containing stage IDs that can run in parallel
    """
    # Build dependency graph
    deps = {stage.id: set(stage.depends_on) for stage in stages}

    # Find stages with no dependencies (can start immediately)
    no_deps = {sid for sid, d in deps.items() if not d}

    groups = []
    if no_deps:
        groups.append(no_deps)

    # Find stages that only depend on stages in previous groups
    processed = no_deps.copy()
    remaining = set(deps.keys()) - processed

    while remaining:
        next_group = set()
        for stage_id in remaining:
            if deps[stage_id].issubset(processed):
                next_group.add(stage_id)

        if not next_group:
            # Circular dependency or unmet dependencies
            break

        groups.append(next_group)
        processed.update(next_group)
        remaining -= next_group

    return groups
