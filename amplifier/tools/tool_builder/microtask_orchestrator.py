"""Microtask orchestration for Tool Builder pipeline.

This module implements the core orchestration pattern that breaks tool creation
into focused microtasks, each designed to be completed efficiently by the AI.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exceptions import MicrotaskError
from .session_manager import ToolBuilderSession


class PipelineStage(Enum):
    """Stages in the tool creation pipeline."""

    INITIALIZING = "initializing"
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    MODULE_GENERATION = "module_generation"
    INTEGRATION_ASSEMBLY = "integration_assembly"
    QUALITY_VERIFICATION = "quality_verification"
    FINAL_POLISH = "final_polish"
    COMPLETED = "completed"


@dataclass
class MicrotaskResult:
    """Result from a microtask execution."""

    stage: PipelineStage
    success: bool
    data: dict[str, Any]
    duration_seconds: float
    error: str | None = None


@dataclass
class PipelineContext:
    """Context passed through the pipeline."""

    session: ToolBuilderSession
    current_stage: PipelineStage
    accumulated_results: dict[PipelineStage, MicrotaskResult]
    interruption_requested: bool = False


class MicrotaskOrchestrator:
    """Orchestrates the tool creation pipeline through focused microtasks."""

    def __init__(self):
        """Initialize the orchestrator."""
        self.pipeline_stages = [
            PipelineStage.REQUIREMENTS_ANALYSIS,
            PipelineStage.ARCHITECTURE_DESIGN,
            PipelineStage.MODULE_GENERATION,
            PipelineStage.INTEGRATION_ASSEMBLY,
            PipelineStage.QUALITY_VERIFICATION,
            PipelineStage.FINAL_POLISH,
        ]
        self.stage_handlers: dict[PipelineStage, Callable] = {}

        # Initialize microtask handlers
        self.requirements_analyzer = None
        self.architecture_designer = None
        self.module_generator = None
        self.integration_assembler = None
        self.quality_checker = None

        self._register_handlers()

    def _register_handlers(self):
        """Register microtask handlers for each stage."""
        self.stage_handlers = {
            PipelineStage.REQUIREMENTS_ANALYSIS: self._handle_requirements,
            PipelineStage.ARCHITECTURE_DESIGN: self._handle_architecture,
            PipelineStage.MODULE_GENERATION: self._handle_modules,
            PipelineStage.INTEGRATION_ASSEMBLY: self._handle_integration,
            PipelineStage.QUALITY_VERIFICATION: self._handle_quality,
            PipelineStage.FINAL_POLISH: self._handle_polish,
        }

    async def execute_pipeline(
        self,
        session: ToolBuilderSession,
        start_from: PipelineStage | None = None,
    ) -> PipelineContext:
        """Execute the tool creation pipeline.

        Args:
            session: The tool builder session
            start_from: Stage to start/resume from (for interrupted sessions)

        Returns:
            PipelineContext with results
        """
        # Initialize context
        context = PipelineContext(
            session=session,
            current_stage=start_from or PipelineStage.REQUIREMENTS_ANALYSIS,
            accumulated_results={},
        )

        # Find starting index
        start_index = 0
        if start_from:
            try:
                start_index = self.pipeline_stages.index(start_from)
            except ValueError:
                raise MicrotaskError(f"Invalid starting stage: {start_from}")

        # Execute pipeline stages
        for stage in self.pipeline_stages[start_index:]:
            if context.interruption_requested:
                break

            context.current_stage = stage
            session.update_stage(stage.value)

            try:
                # Execute the microtask for this stage
                result = await self._execute_microtask(stage, context)
                context.accumulated_results[stage] = result

                if not result.success:
                    raise MicrotaskError(f"Stage {stage.value} failed: {result.error}")

                # Save progress after each successful stage
                self._save_stage_results(session, stage, result)

            except asyncio.CancelledError:
                # Handle interruption gracefully
                context.interruption_requested = True
                session.add_metadata("interrupted_at", stage.value)
                break

            except Exception as e:
                # Log error and determine if we can continue
                error_msg = f"Error in stage {stage.value}: {str(e)}"
                session.add_metadata(f"error_{stage.value}", error_msg)

                if self._is_critical_stage(stage):
                    raise MicrotaskError(error_msg)

                # Non-critical stages can be skipped with a warning
                print(f"⚠ Warning: {error_msg}")
                continue

        # Mark as completed if we finished all stages
        if not context.interruption_requested and len(context.accumulated_results) == len(self.pipeline_stages):
            session.update_stage(PipelineStage.COMPLETED.value)

        return context

    async def _execute_microtask(
        self,
        stage: PipelineStage,
        context: PipelineContext,
    ) -> MicrotaskResult:
        """Execute a single microtask."""
        import time

        start_time = time.time()

        try:
            handler = self.stage_handlers.get(stage)
            if not handler:
                raise MicrotaskError(f"No handler registered for stage: {stage.value}")

            # Execute the handler
            data = await handler(context)

            duration = time.time() - start_time

            return MicrotaskResult(
                stage=stage,
                success=True,
                data=data,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return MicrotaskResult(
                stage=stage,
                success=False,
                data={},
                duration_seconds=duration,
                error=str(e),
            )

    def _save_stage_results(
        self,
        session: ToolBuilderSession,
        stage: PipelineStage,
        result: MicrotaskResult,
    ):
        """Save results from a completed stage."""
        if stage == PipelineStage.REQUIREMENTS_ANALYSIS:
            session.requirements = result.data
        elif stage == PipelineStage.ARCHITECTURE_DESIGN:
            session.architecture = result.data
        elif stage == PipelineStage.MODULE_GENERATION:
            modules = result.data.get("modules", [])
            session.generated_modules.extend(modules)
        elif stage == PipelineStage.QUALITY_VERIFICATION:
            session.quality_checks.append(result.data)

        # Always save the session after updating
        session.save()

    def _is_critical_stage(self, stage: PipelineStage) -> bool:
        """Determine if a stage is critical (cannot be skipped)."""
        critical_stages = [
            PipelineStage.REQUIREMENTS_ANALYSIS,
            PipelineStage.ARCHITECTURE_DESIGN,
            PipelineStage.MODULE_GENERATION,
        ]
        return stage in critical_stages

    async def _handle_requirements(self, context: PipelineContext) -> dict[str, Any]:
        """Handle requirements analysis stage."""
        from .requirements_analyzer import RequirementsAnalyzer

        if not self.requirements_analyzer:
            self.requirements_analyzer = RequirementsAnalyzer()

        session = context.session
        result = await self.requirements_analyzer.analyze(
            tool_name=session.tool_name,
            description=session.description,
        )
        return result

    async def _handle_architecture(self, context: PipelineContext) -> dict[str, Any]:
        """Handle architecture design stage."""
        from .architecture_designer import ArchitectureDesigner

        if not self.architecture_designer:
            self.architecture_designer = ArchitectureDesigner()

        session = context.session
        requirements = session.requirements or {}

        result = await self.architecture_designer.design(
            tool_name=session.tool_name,
            requirements=requirements,
        )
        return result

    async def _handle_modules(self, context: PipelineContext) -> dict[str, Any]:
        """Handle module generation stage."""
        from pathlib import Path

        from .module_generator import ModuleGenerator

        if not self.module_generator:
            self.module_generator = ModuleGenerator()

        session = context.session
        architecture = session.architecture or {}
        requirements = session.requirements or {}

        # Generate each module
        modules = architecture.get("modules", [])
        generated = []

        # Get output directory
        output_dir = Path.home() / ".amplifier" / "generated_tools" / session.tool_name
        output_dir.mkdir(parents=True, exist_ok=True)

        for module_spec in modules:
            result = await self.module_generator.generate(
                tool_name=session.tool_name,
                module_spec=module_spec,
                requirements=requirements,
                output_dir=output_dir,
            )
            generated.append(result)

        return {"modules": generated, "output_dir": str(output_dir)}

    async def _handle_integration(self, context: PipelineContext) -> dict[str, Any]:
        """Handle integration assembly stage."""
        from pathlib import Path

        from .integration_assembler import IntegrationAssembler

        if not self.integration_assembler:
            self.integration_assembler = IntegrationAssembler()

        session = context.session
        architecture = session.architecture or {}
        module_results = context.accumulated_results.get(PipelineStage.MODULE_GENERATION, None)

        if module_results:
            generated_modules = module_results.data.get("modules", [])
            output_dir = Path(module_results.data.get("output_dir", ""))
        else:
            # Session stores modules as list of file paths, convert to expected format
            generated_modules = [{"files": session.generated_modules}] if session.generated_modules else []
            output_dir = Path.home() / ".amplifier" / "generated_tools" / session.tool_name

        result = await self.integration_assembler.assemble(
            tool_name=session.tool_name,
            architecture=architecture,
            generated_modules=generated_modules,
            output_dir=output_dir,
        )
        return result

    async def _handle_quality(self, context: PipelineContext) -> dict[str, Any]:
        """Handle quality verification stage."""
        from pathlib import Path

        from .quality_checker import QualityChecker

        if not self.quality_checker:
            self.quality_checker = QualityChecker()

        session = context.session
        module_results = context.accumulated_results.get(PipelineStage.MODULE_GENERATION, None)

        if module_results:
            output_dir = Path(module_results.data.get("output_dir", ""))
        else:
            output_dir = Path.home() / ".amplifier" / "generated_tools" / session.tool_name

        result = await self.quality_checker.check(
            tool_name=session.tool_name,
            output_dir=output_dir,
        )
        return result

    async def _handle_polish(self, context: PipelineContext) -> dict[str, Any]:
        """Handle final polish stage."""
        from pathlib import Path

        # For now, just mark as complete
        # Future: Could add documentation generation, final formatting, etc.
        return {
            "status": "complete",
            "message": f"Tool '{context.session.tool_name}' is ready!",
            "location": str(Path.home() / ".amplifier" / "generated_tools" / context.session.tool_name),
        }

    def get_stage_progress(self, session: ToolBuilderSession) -> dict[str, Any]:
        """Get progress information for a session."""
        completed = session.completed_stages
        current = session.current_stage
        total = len(self.pipeline_stages)

        # Calculate progress percentage
        completed_count = len(completed)
        if current == PipelineStage.COMPLETED.value:
            progress = 100
        else:
            progress = int((completed_count / total) * 100)

        return {
            "completed_stages": completed,
            "current_stage": current,
            "total_stages": total,
            "progress_percentage": progress,
            "is_completed": current == PipelineStage.COMPLETED.value,
        }
