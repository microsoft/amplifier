"""Multi-stage pipeline orchestrator for module generation with checkpoints and evaluation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .checkpoint_manager import CheckpointManager
from .context import GenContext
from .drift_detector import DriftDetector
from .enums import PipelineStage
from .parsers import parse_contract
from .parsers import parse_impl_spec
from .philosophy_injector import PhilosophyInjector
from .sdk_client import generate_from_specs
from .sdk_client import plan_from_specs
from .sdk_client import verify_and_fix_module
from .stage_evaluator import StageEvaluator

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Result from executing a pipeline stage."""

    stage: PipelineStage
    success: bool
    output: Any
    error: str | None = None
    drift_score: float = 0.0  # 0.0 = no drift, 1.0 = complete drift
    evaluation_notes: str | None = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        # Handle special serialization for output field
        output = self.output
        if output is not None:
            # Check if output is an EvaluationResult
            from amplifier.tools.module_generator.stage_evaluator import EvaluationResult

            if isinstance(output, EvaluationResult):
                output = output.to_dict()
            # Check if output is a dict containing objects with to_dict methods
            elif isinstance(output, dict):
                output = {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in output.items()}

        return {
            "stage": self.stage.value if isinstance(self.stage, PipelineStage) else self.stage,
            "success": self.success,
            "output": output,
            "error": self.error,
            "drift_score": self.drift_score,
            "evaluation_notes": self.evaluation_notes,
            "timestamp": self.timestamp,
        }


@dataclass
class PipelineState:
    """Current state of the pipeline execution."""

    context: GenContext
    current_stage: PipelineStage
    completed_stages: list[PipelineStage]
    stage_results: dict[str, StageResult]  # stage.value -> result
    contract_text: str | None = None
    spec_text: str | None = None
    plan_text: str | None = None
    session_id: str | None = None
    total_cost: float = 0.0
    total_ms: int = 0
    started_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.started_at

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "context": {
                "repo_root": str(self.context.repo_root),
                "tool_dir": str(self.context.tool_dir),
                "contract_path": str(self.context.contract_path),
                "spec_path": str(self.context.spec_path),
                "module_name": self.context.module_name,
                "target_rel": self.context.target_rel,
                "force": self.context.force,
            },
            "current_stage": self.current_stage.value,
            "completed_stages": [s.value for s in self.completed_stages],
            "stage_results": {k: v.to_dict() for k, v in self.stage_results.items()},
            "contract_text": self.contract_text,
            "spec_text": self.spec_text,
            "plan_text": self.plan_text,
            "session_id": self.session_id,
            "total_cost": self.total_cost,
            "total_ms": self.total_ms,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PipelineState:
        """Reconstruct from dictionary."""
        from amplifier.tools.module_generator.parsers import ModuleContract
        from amplifier.tools.module_generator.parsers import ModuleImplSpec
        from amplifier.tools.module_generator.stage_evaluator import EvaluationResult

        ctx_data = data["context"]
        context = GenContext(
            repo_root=Path(ctx_data["repo_root"]),
            tool_dir=Path(ctx_data["tool_dir"]),
            contract_path=Path(ctx_data["contract_path"]),
            spec_path=Path(ctx_data["spec_path"]),
            module_name=ctx_data["module_name"],
            target_rel=ctx_data["target_rel"],
            force=ctx_data.get("force", False),
        )

        # Helper function to deserialize output field
        def deserialize_output(stage_name: str, output: Any) -> Any:
            """Deserialize output field based on stage type."""
            if output is None:
                return None

            # Check if it's a serialized EvaluationResult (for EVALUATE_PLAN stage)
            if (
                stage_name == "evaluate_plan"
                and isinstance(output, dict)
                and "is_valid" in output
                and "score" in output
                and "notes" in output
            ):
                return EvaluationResult.from_dict(output)

            # Check if it's a dict with contract/impl_spec (for PARSE stage)
            if stage_name == "parse" and isinstance(output, dict):
                result = {}
                if "contract" in output and isinstance(output["contract"], dict):
                    result["contract"] = ModuleContract.from_dict(output["contract"])
                if "impl_spec" in output and isinstance(output["impl_spec"], dict):
                    result["impl_spec"] = ModuleImplSpec.from_dict(output["impl_spec"])
                return result if result else output

            return output

        return cls(
            context=context,
            current_stage=PipelineStage(data["current_stage"]),
            completed_stages=[PipelineStage(s) for s in data["completed_stages"]],
            stage_results={
                k: StageResult(
                    stage=PipelineStage(v["stage"]) if isinstance(v["stage"], str) else v["stage"],
                    success=v["success"],
                    output=deserialize_output(k, v["output"]),
                    error=v.get("error"),
                    drift_score=v.get("drift_score", 0.0),
                    evaluation_notes=v.get("evaluation_notes"),
                    timestamp=v.get("timestamp", ""),
                )
                for k, v in data["stage_results"].items()
            },
            contract_text=data.get("contract_text"),
            spec_text=data.get("spec_text"),
            plan_text=data.get("plan_text"),
            session_id=data.get("session_id"),
            total_cost=data.get("total_cost", 0.0),
            total_ms=data.get("total_ms", 0),
            started_at=data.get("started_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class PipelineOrchestrator:
    """Orchestrates the multi-stage module generation pipeline."""

    def __init__(self, context: GenContext):
        self.context = context
        self.checkpoint_manager = CheckpointManager(context.repo_root)
        self.philosophy_injector = PhilosophyInjector(context.repo_root)
        self.stage_evaluator = StageEvaluator()
        self.drift_detector = DriftDetector()
        self.state: PipelineState | None = None

    async def run_pipeline(self, resume_from_checkpoint: bool = True) -> PipelineState:
        """Run the complete pipeline with checkpoints and evaluation."""
        # Try to resume from checkpoint
        if resume_from_checkpoint:
            self.state = self.checkpoint_manager.load_latest(self.context.module_name)

        # Initialize state if not resuming
        if self.state is None:
            self.state = PipelineState(
                context=self.context,
                current_stage=PipelineStage.PARSE,
                completed_stages=[],
                stage_results={},
            )
            logger.info(f"Starting new pipeline for module: {self.context.module_name}")
        else:
            logger.info(
                f"Resuming pipeline for {self.context.module_name} from stage: {self.state.current_stage.value}"
            )

        # Execute stages in sequence
        while self.state.current_stage != PipelineStage.COMPLETE:
            logger.info(f"Executing stage: {self.state.current_stage.value}")

            # Execute current stage
            result = await self._execute_stage(self.state.current_stage)

            # Store result
            self.state.stage_results[self.state.current_stage.value] = result
            self.state.completed_stages.append(self.state.current_stage)
            self.state.updated_at = datetime.now().isoformat()

            # Save checkpoint after each stage
            self.checkpoint_manager.save(self.state)

            # Check if stage failed
            if not result.success:
                logger.error(f"Stage {self.state.current_stage.value} failed: {result.error}")
                break

            # Check for excessive drift
            if result.drift_score > 0.7:
                logger.warning(
                    f"High drift detected ({result.drift_score:.2f}) in stage {self.state.current_stage.value}"
                )
                # Could optionally retry or adjust here

            # Move to next stage
            next_stage = self.state.current_stage.next_stage()
            if next_stage:
                self.state.current_stage = next_stage
            else:
                self.state.current_stage = PipelineStage.COMPLETE

        logger.info(f"Pipeline completed. Final stage: {self.state.current_stage.value}")
        return self.state

    async def _execute_stage(self, stage: PipelineStage) -> StageResult:
        """Execute a specific pipeline stage."""
        try:
            if stage == PipelineStage.PARSE:
                return await self._parse_stage()
            if stage == PipelineStage.PLAN:
                return await self._plan_stage()
            if stage == PipelineStage.EVALUATE_PLAN:
                return await self._evaluate_plan_stage()
            if stage == PipelineStage.GENERATE:
                return await self._generate_stage()
            if stage == PipelineStage.VERIFY_CONTRACT:
                return await self._verify_contract_stage()
            if stage == PipelineStage.TEST:
                return await self._test_stage()
            return StageResult(
                stage=stage,
                success=False,
                output=None,
                error=f"Unknown stage: {stage.value}",
            )
        except Exception as e:
            logger.exception(f"Error in stage {stage.value}")
            return StageResult(
                stage=stage,
                success=False,
                output=None,
                error=str(e),
            )

    async def _parse_stage(self) -> StageResult:
        """Parse contract and implementation spec."""
        contract = parse_contract(self.context.contract_path)
        impl = parse_impl_spec(self.context.spec_path, expected_name=contract.name)

        # Store parsed texts
        if self.state:
            self.state.contract_text = contract.raw
            self.state.spec_text = impl.raw

        # Evaluate parsing quality
        evaluation = self.stage_evaluator.evaluate_parsing(contract, impl)

        return StageResult(
            stage=PipelineStage.PARSE,
            success=True,
            output={"contract": contract.to_dict(), "impl_spec": impl.to_dict()},
            evaluation_notes=evaluation.notes,
        )

    async def _plan_stage(self) -> StageResult:
        """Generate implementation plan."""
        if not self.state or not self.state.contract_text or not self.state.spec_text:
            return StageResult(
                stage=PipelineStage.PLAN,
                success=False,
                output=None,
                error="Missing contract or spec text",
            )

        # Inject philosophy into planning
        philosophy_context = self.philosophy_injector.get_stage_context(PipelineStage.PLAN)
        enhanced_contract = philosophy_context + "\n\n" + self.state.contract_text

        # Generate plan
        plan_text, session_id, cost, ms = await plan_from_specs(
            contract_text=enhanced_contract,
            impl_text=self.state.spec_text,
            cwd=str(self.context.repo_root),
            add_dirs=[str(self.context.repo_root / "ai_context"), str(self.context.repo_root / "amplifier")],
            settings=None,
        )

        if self.state:
            self.state.plan_text = plan_text
            self.state.session_id = session_id
            self.state.total_cost += cost
            self.state.total_ms += ms

        # Detect drift from requirements
        drift_score = self.drift_detector.measure_plan_drift(plan_text, self.state.contract_text, self.state.spec_text)

        # Evaluate plan quality
        evaluation = self.stage_evaluator.evaluate_plan(plan_text, self.state.contract_text)

        return StageResult(
            stage=PipelineStage.PLAN,
            success=bool(plan_text),
            output=plan_text,
            drift_score=drift_score,
            evaluation_notes=evaluation.notes,
        )

    async def _evaluate_plan_stage(self) -> StageResult:
        """Evaluate the generated plan before proceeding."""
        if not self.state or not self.state.plan_text:
            return StageResult(
                stage=PipelineStage.EVALUATE_PLAN,
                success=False,
                output=None,
                error="No plan to evaluate",
            )

        # Comprehensive evaluation
        evaluation = self.stage_evaluator.evaluate_plan_comprehensive(
            self.state.plan_text,
            self.state.contract_text or "",
            self.state.spec_text or "",
        )

        # Check if plan meets quality thresholds
        if not evaluation.is_valid:
            return StageResult(
                stage=PipelineStage.EVALUATE_PLAN,
                success=False,
                output=evaluation,
                error=f"Plan quality insufficient: {evaluation.notes}",
            )

        return StageResult(
            stage=PipelineStage.EVALUATE_PLAN,
            success=True,
            output=evaluation,
            evaluation_notes=evaluation.notes,
        )

    async def _generate_stage(self) -> StageResult:
        """Generate the module implementation."""
        if not self.state or not self.state.contract_text or not self.state.spec_text:
            return StageResult(
                stage=PipelineStage.GENERATE,
                success=False,
                output=None,
                error="Missing contract or spec text",
            )

        # Check if target exists
        target_dir = self.context.repo_root / self.context.target_rel
        if target_dir.exists() and not self.context.force:
            return StageResult(
                stage=PipelineStage.GENERATE,
                success=False,
                output=None,
                error=f"Target exists: {target_dir}. Use --force to overwrite.",
            )

        # Remove existing if forced
        if target_dir.exists() and self.context.force:
            import shutil

            shutil.rmtree(target_dir)
            logger.info(f"Removed existing directory: {target_dir}")

        # Inject philosophy into generation
        philosophy_context = self.philosophy_injector.get_stage_context(PipelineStage.GENERATE)
        enhanced_contract = philosophy_context + "\n\n" + self.state.contract_text

        # Generate module
        session_id, cost, ms = await generate_from_specs(
            contract_text=enhanced_contract,
            impl_text=self.state.spec_text,
            module_name=self.context.module_name,
            module_dir_rel=self.context.target_rel,
            cwd=str(self.context.repo_root),
            add_dirs=[str(self.context.repo_root / "ai_context"), str(self.context.repo_root / "amplifier")],
            settings=None,
        )

        if self.state:
            self.state.session_id = session_id or self.state.session_id
            self.state.total_cost += cost
            self.state.total_ms += ms

        # Check if generation succeeded
        success = target_dir.exists() and (target_dir / "__init__.py").exists()

        return StageResult(
            stage=PipelineStage.GENERATE,
            success=success,
            output=str(target_dir) if success else None,
            error=None if success else "Module generation failed",
        )

    async def _verify_contract_stage(self) -> StageResult:
        """Verify the generated module against the contract."""
        target_dir = self.context.repo_root / self.context.target_rel
        if not target_dir.exists():
            return StageResult(
                stage=PipelineStage.VERIFY_CONTRACT,
                success=False,
                output=None,
                error=f"Module directory not found: {target_dir}",
            )

        # Verify and potentially fix the module
        contract_text = self.state.contract_text if self.state and self.state.contract_text else ""
        is_valid, report = await verify_and_fix_module(
            module_path=target_dir,
            module_name=self.context.module_name,
            contract_text=contract_text,
            cwd=str(self.context.repo_root),
            add_dirs=[str(self.context.repo_root / "ai_context"), str(self.context.repo_root / "amplifier")],
            settings=None,
        )

        # Measure drift from contract
        contract_for_drift = self.state.contract_text if self.state and self.state.contract_text else ""
        drift_score = self.drift_detector.measure_implementation_drift(target_dir, contract_for_drift)

        return StageResult(
            stage=PipelineStage.VERIFY_CONTRACT,
            success=is_valid,
            output=report,
            drift_score=drift_score,
            error=None if is_valid else "Contract verification failed",
        )

    async def _test_stage(self) -> StageResult:
        """Run tests on the generated module."""
        target_dir = self.context.repo_root / self.context.target_rel
        test_dir = target_dir / "tests"

        if not test_dir.exists():
            return StageResult(
                stage=PipelineStage.TEST,
                success=False,
                output=None,
                error=f"Test directory not found: {test_dir}",
            )

        # Run pytest on the module
        import subprocess

        result = subprocess.run(
            ["python", "-m", "pytest", str(test_dir), "-v"],
            capture_output=True,
            text=True,
            cwd=str(self.context.repo_root),
        )

        success = result.returncode == 0
        output = result.stdout + result.stderr

        return StageResult(
            stage=PipelineStage.TEST,
            success=success,
            output=output,
            error=None if success else "Tests failed",
        )
