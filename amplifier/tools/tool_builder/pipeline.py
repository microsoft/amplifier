"""
Main orchestrator for AI-first tool building pipeline.

This module coordinates the tool building process through AI-powered stages,
managing state and enabling resumability at any point.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from amplifier.tools.tool_builder.stages.analysis import MetacognitiveAnalyzer
from amplifier.tools.tool_builder.stages.generation import CodeGenerator
from amplifier.tools.tool_builder.stages.requirements import RequirementsAnalyzer
from amplifier.tools.tool_builder.stages.validation import QualityValidator
from amplifier.tools.tool_builder.state import StateManager
from amplifier.tools.tool_builder.state import ToolBuilderState

logger = logging.getLogger(__name__)


class ToolBuilderPipeline:
    """Orchestrates the AI-first tool building process."""

    def __init__(self, state_dir: Path | None = None, tools_dir: Path | None = None):
        """Initialize pipeline with state management.

        Args:
            state_dir: Directory for state files
            tools_dir: Directory where tools are created (default: amplifier/tools)
        """
        self.state_dir = state_dir or Path.home() / ".amplifier" / "tool_builder_state"
        self.state_manager = StateManager(self.state_dir)
        self.tools_dir = tools_dir or Path("amplifier/tools")

        # Initialize stage processors
        self.requirements_analyzer = RequirementsAnalyzer()
        self.metacognitive_analyzer = MetacognitiveAnalyzer()
        self.code_generator = CodeGenerator()
        self.quality_validator = QualityValidator()

        # Stage mapping for execution
        self.stages = {
            "requirements": self.run_requirements_stage,
            "analysis": self.run_analysis_stage,
            "generation": self.run_generation_stage,
            "validation": self.run_validation_stage,
            "integration": self.run_integration_stage,  # Add integration stage
        }

    async def build_tool(
        self, tool_name: str, description: str, resume: bool = False, skip_validation: bool = False
    ) -> dict[str, Any]:
        """Build a Claude Code tool from description.

        Args:
            tool_name: Name of the tool to build
            description: Natural language description of the tool's purpose
            resume: Whether to resume from a previous run
            skip_validation: Whether to skip the validation stage

        Returns:
            Dictionary containing generated code and metadata
        """
        # Load or create state
        state = self._initialize_state(tool_name, description, resume)

        # Determine starting point
        start_stage = state.get_resume_point()
        if not start_stage:
            logger.info(f"Tool '{tool_name}' already complete")
            return self._prepare_results(state)

        if resume and state.current_stage:
            logger.info(f"Resuming from stage: {state.current_stage}")
        else:
            logger.info(f"Starting new tool build: {tool_name}")

        # Execute pipeline stages
        pipeline_order = ["requirements", "analysis", "generation"]
        if not skip_validation:
            pipeline_order.append("validation")
        pipeline_order.append("integration")  # Always run integration to save files

        try:
            for stage in pipeline_order:
                if state.can_skip_stage(stage):
                    logger.info(f"Skipping completed stage: {stage}")
                    continue

                if stage == start_stage or start_stage in pipeline_order[: pipeline_order.index(stage)]:
                    await self._execute_stage(stage, state)

        except Exception as e:
            logger.error(f"Pipeline failed at stage '{state.current_stage}': {e}")
            state.mark_stage_failed(state.current_stage or "unknown", str(e))
            self.state_manager.save_checkpoint(state)
            raise

        # Save final state
        self.state_manager.save_checkpoint(state)
        logger.info(f"Tool '{tool_name}' build complete")

        return self._prepare_results(state)

    def _initialize_state(self, tool_name: str, description: str, resume: bool) -> ToolBuilderState:
        """Initialize or load state for tool building."""
        if resume:
            state = self.state_manager.load_state(tool_name)
            if state:
                logger.info(f"Loaded existing state for '{tool_name}'")
                return state
            logger.warning(f"No existing state found for '{tool_name}', starting fresh")

        return self.state_manager.create_state(tool_name, description)

    async def _execute_stage(self, stage_name: str, state: ToolBuilderState) -> None:
        """Execute a single pipeline stage."""
        state.start_stage(stage_name)
        self.state_manager.save_checkpoint(state)

        try:
            stage_func = self.stages[stage_name]
            await stage_func(state)
            self.state_manager.save_checkpoint(state)
        except Exception as e:
            logger.error(f"Stage '{stage_name}' failed: {e}")
            state.mark_stage_failed(stage_name, str(e))
            self.state_manager.save_checkpoint(state)
            raise

    async def run_requirements_stage(self, state: ToolBuilderState) -> None:
        """Run AI requirements analysis stage."""
        logger.info("Analyzing requirements with AI")

        requirements = await self.requirements_analyzer.analyze(
            tool_name=state.tool_name, description=state.description
        )

        state.requirements = requirements
        state.mark_stage_complete("requirements", requirements)
        state.increment_ai_metrics(requirements.get("tokens_used", 0))

    async def run_analysis_stage(self, state: ToolBuilderState) -> None:
        """Run AI metacognitive analysis stage."""
        logger.info("Performing metacognitive analysis with AI")

        if not state.requirements:
            raise ValueError("Requirements stage must complete before analysis")

        analysis = await self.metacognitive_analyzer.analyze(requirements=state.requirements, tool_name=state.tool_name)

        state.analysis = analysis
        state.mark_stage_complete("analysis", analysis)
        state.increment_ai_metrics(analysis.get("tokens_used", 0))

    async def run_generation_stage(self, state: ToolBuilderState) -> None:
        """Run AI code generation stage."""
        logger.info("Generating code with AI")

        if not state.analysis:
            raise ValueError("Analysis stage must complete before generation")

        if not state.requirements:
            raise ValueError("Requirements must be available for generation")

        generated_code = await self.code_generator.generate(
            requirements=state.requirements, analysis=state.analysis, tool_name=state.tool_name
        )

        state.generated_code = generated_code
        state.mark_stage_complete("generation", generated_code)
        state.increment_ai_metrics(generated_code.get("tokens_used", 0))

    async def run_validation_stage(self, state: ToolBuilderState) -> None:
        """Run AI quality validation stage."""
        logger.info("Validating quality with AI")

        if not state.generated_code:
            raise ValueError("Generation stage must complete before validation")

        if not state.requirements:
            raise ValueError("Requirements must be available for validation")

        validation = await self.quality_validator.validate(
            generated_code=state.generated_code, requirements=state.requirements, tool_name=state.tool_name
        )

        state.validation_results = validation
        state.mark_stage_complete("validation", validation)
        state.increment_ai_metrics(validation.get("tokens_used", 0))

    async def run_integration_stage(self, state: ToolBuilderState) -> None:
        """Run integration stage to save generated files."""
        logger.info("Saving generated files")

        if not state.generated_code:
            raise ValueError("Generation stage must complete before integration")

        # Create tool directory
        tool_name_clean = state.tool_name.replace("-", "_")
        tool_dir = self.tools_dir / tool_name_clean
        tool_dir.mkdir(parents=True, exist_ok=True)

        # Save generated files
        saved_files = []
        for filename, content in state.generated_code.items():
            if isinstance(content, str):  # Only save string content, skip metadata
                filepath = tool_dir / filename
                filepath.write_text(content)
                saved_files.append(str(filepath))
                logger.info(f"Saved {filename} to {filepath}")

        # Create or update __init__.py if not provided
        init_file = tool_dir / "__init__.py"
        if not init_file.exists():
            init_content = f'"""{state.tool_name} - {state.description[:100]}..."""\n\n__version__ = "1.0.0"\n'
            init_file.write_text(init_content)
            saved_files.append(str(init_file))

        integration_result = {
            "tool_dir": str(tool_dir),
            "saved_files": saved_files,
            "status": "success",
        }

        state.integration_results = integration_result
        state.mark_stage_complete("integration", integration_result)

    def _prepare_results(self, state: ToolBuilderState) -> dict[str, Any]:
        """Prepare final results from completed state."""
        return {
            "tool_name": state.tool_name,
            "description": state.description,
            "generated_code": state.generated_code or {},
            "validation": state.validation_results,
            "integration_results": state.integration_results,
            "metrics": {
                "total_ai_calls": state.total_ai_calls,
                "total_tokens": state.total_tokens_used,
                "stages_completed": len(state.completed_stages),
            },
            "state_file": str(self.state_manager.get_state_path(state.tool_name)),
        }

    async def resume_incomplete_tools(self) -> dict[str, dict[str, Any]]:
        """Resume all incomplete tool builds."""
        incomplete = self.state_manager.list_incomplete_tools()
        results = {}

        for tool_name in incomplete:
            logger.info(f"Resuming incomplete tool: {tool_name}")
            state = self.state_manager.load_state(tool_name)
            if state:
                try:
                    result = await self.build_tool(
                        tool_name=state.tool_name, description=state.description, resume=True
                    )
                    results[tool_name] = result
                except Exception as e:
                    logger.error(f"Failed to resume '{tool_name}': {e}")
                    results[tool_name] = {"error": str(e)}

        return results

    def cleanup_completed(self) -> int:
        """Remove state files for completed tools."""
        return self.state_manager.cleanup_completed()

    def get_tool_status(self, tool_name: str) -> dict[str, Any] | None:
        """Get the current status of a tool build."""
        state = self.state_manager.load_state(tool_name)
        if not state:
            return None

        return {
            "tool_name": state.tool_name,
            "current_stage": state.current_stage,
            "completed_stages": state.completed_stages,
            "next_stage": state.get_resume_point(),
            "failed_attempts": state.failed_attempts,
            "metrics": {"ai_calls": state.total_ai_calls, "tokens_used": state.total_tokens_used},
        }


async def main():
    """CLI entry point for tool builder pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="AI-first tool builder")
    parser.add_argument("tool_name", help="Name of the tool to build")
    parser.add_argument("description", help="Description of what the tool should do")
    parser.add_argument("--resume", action="store_true", help="Resume from previous run")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation stage")
    parser.add_argument("--state-dir", type=Path, help="Directory for state files")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run pipeline
    pipeline = ToolBuilderPipeline(state_dir=args.state_dir)

    try:
        result = await pipeline.build_tool(
            tool_name=args.tool_name,
            description=args.description,
            resume=args.resume,
            skip_validation=args.skip_validation,
        )

        # Output generated code
        if result.get("generated_code"):
            for filename, content in result["generated_code"].items():
                print(f"\n=== {filename} ===")
                print(content)

        # Show metrics
        metrics = result.get("metrics", {})
        print("\n✓ Tool built successfully")
        print(f"  AI calls: {metrics.get('total_ai_calls', 0)}")
        print(f"  Tokens used: {metrics.get('total_tokens', 0)}")

    except Exception as e:
        logger.error(f"Tool building failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
