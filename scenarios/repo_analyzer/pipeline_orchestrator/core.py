"""
Pipeline orchestrator module.

Coordinates all analysis modules with feedback loops.
"""

import asyncio
from pathlib import Path
from typing import Any

from amplifier.utils.logger import get_logger

from ..analysis_engine import AnalysisEngine
from ..completeness_reviewer import CompletenessReviewer
from ..grounding_reviewer import GroundingReviewer
from ..human_review_interface import HumanReviewInterface
from ..opportunity_generator import OpportunityGenerator
from ..philosophy_reviewer import PhilosophyReviewer
from ..repo_processor import RepoProcessor
from ..state import StateManager

logger = get_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete repository analysis pipeline."""

    def __init__(self, state_manager: StateManager):
        """Initialize pipeline with state management.

        Args:
            state_manager: State manager instance
        """
        self.state = state_manager

        # Initialize modules
        self.repo_processor = RepoProcessor()
        self.analysis_engine = AnalysisEngine()
        self.opportunity_generator = OpportunityGenerator()
        self.grounding_reviewer = GroundingReviewer()
        self.philosophy_reviewer = PhilosophyReviewer()
        self.completeness_reviewer = CompletenessReviewer()
        self.human_interface = HumanReviewInterface()

    async def run(
        self,
        source_path: Path,
        target_path: Path,
        analysis_request: str,
        focus_areas: list[str] | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        skip_review: bool = False,
    ) -> bool:
        """Run the complete analysis pipeline.

        Args:
            source_path: Path to source repository
            target_path: Path to target repository
            analysis_request: User's analysis request
            focus_areas: Optional focus areas
            include_patterns: Optional file patterns to include
            exclude_patterns: Optional file patterns to exclude
            skip_review: Skip the markdown review step if True

        Returns:
            True if successful, False otherwise
        """
        # Store inputs
        self.state.state.source_path = str(source_path)
        self.state.state.target_path = str(target_path)
        self.state.state.analysis_request = analysis_request
        self.state.state.focus_areas = focus_areas or []
        self.state.save()

        # Resume from saved stage if applicable
        stage = self.state.state.stage
        logger.info(f"Starting from stage: {stage}")

        try:
            # Process repositories if not done
            if stage == "initialized":
                await self._process_repositories(source_path, target_path, include_patterns, exclude_patterns)
                stage = self.state.state.stage

            # Perform initial analysis if not done
            if stage == "repos_processed":
                await self._perform_analysis(analysis_request, focus_areas)
                stage = self.state.state.stage

            # Generate opportunities if not done
            if stage == "analysis_complete":
                await self._generate_opportunities()
                stage = self.state.state.stage

            # Feedback loop with protection
            consecutive_refinements = 0
            while stage in ["opportunities_generated", "feedback_applied"]:
                if not self.state.increment_iteration():
                    logger.warning("Max iterations reached")
                    break

                # Run reviews in parallel
                await self._run_reviews()

                # Get human feedback
                feedback = await self._get_human_feedback()

                if feedback.get("approved"):
                    break

                # Track consecutive refinements to prevent infinite loops
                if feedback.get("action") == "refine":
                    consecutive_refinements += 1
                    if consecutive_refinements >= 3:
                        logger.warning("Reached maximum consecutive refinements (3). Consider changing approach.")
                        # Force user to choose a different action
                        feedback["action"] = None
                        continue
                    await self._apply_refinements(feedback)
                elif feedback.get("action") == "filter":
                    consecutive_refinements = 0  # Reset counter on different action
                    await self._apply_filters(feedback)
                elif feedback.get("action") == "focus":
                    consecutive_refinements = 0  # Reset counter on different action
                    await self._change_focus(feedback)
                else:
                    break  # skip or interrupted

                stage = self.state.state.stage

            # After human review stage, run the markdown review workflow
            if self.state.state.opportunities and stage == "opportunities_generated":
                # Import here to avoid circular dependency
                from amplifier.ccsdk_toolkit.defensive import write_json_with_retry

                from ..review import ReviewWorkflow

                # Save current opportunities before markdown review
                output_file = self.state.get_output_file()
                output_data = {
                    "opportunities": self.state.state.opportunities,
                    "metadata": {"total_count": len(self.state.state.opportunities)},
                }
                write_json_with_retry(output_data, output_file)

                # Run markdown review workflow
                review_workflow = ReviewWorkflow(self.state.session_dir)
                reviewed_file = await review_workflow.run_review_workflow(output_file, skip_review=skip_review)

                # Update opportunities with reviewed results if review was done
                if reviewed_file != output_file:
                    from amplifier.ccsdk_toolkit.defensive import read_json_with_retry

                    reviewed_data = read_json_with_retry(reviewed_file, default={})
                    if reviewed_data.get("opportunities"):
                        self.state.set_opportunities(reviewed_data["opportunities"])
                        logger.info(f"Updated opportunities from review: {len(reviewed_data['opportunities'])} items")

            # Mark complete
            self.state.mark_complete()
            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False
        finally:
            # Clean up temp files
            self.repo_processor.cleanup()

    async def _process_repositories(
        self,
        source_path: Path,
        target_path: Path,
        include_patterns: list[str] | None,
        exclude_patterns: list[str] | None,
    ) -> None:
        """Process both repositories with repomix."""
        logger.info("\n📦 Processing repositories...")
        self.state.update_stage("processing_repos")

        source_file, target_file = await self.repo_processor.process_both_repos(
            source_path, target_path, include_patterns, exclude_patterns
        )

        self.state.set_repo_files(source_file, target_file)
        self.state.update_stage("repos_processed")

    async def _perform_analysis(self, analysis_request: str, focus_areas: list[str] | None) -> None:
        """Perform comparative analysis."""
        logger.info("\n🔬 Analyzing repositories...")
        self.state.update_stage("analyzing")

        # Load repository content
        if not self.state.state.source_file or not self.state.state.target_file:
            raise RuntimeError("Repository files not found in state")
        source_file = Path(self.state.state.source_file)
        target_file = Path(self.state.state.target_file)

        source_content = source_file.read_text()
        target_content = target_file.read_text()

        # Run analysis
        results = await self.analysis_engine.analyze_repositories(
            source_content, target_content, analysis_request, focus_areas
        )

        self.state.set_analysis_results(results)
        self.state.update_stage("analysis_complete")

    async def _generate_opportunities(self) -> None:
        """Generate implementation opportunities."""
        logger.info("\n💡 Generating opportunities...")
        self.state.update_stage("generating_opportunities")

        # Get target content for context
        if not self.state.state.target_file:
            raise RuntimeError("Target repository file not found in state")
        target_file = Path(self.state.state.target_file)
        target_content = target_file.read_text()

        opportunities = await self.opportunity_generator.generate_opportunities(
            self.state.state.analysis_results, target_content, max_opportunities=10
        )

        self.state.set_opportunities(opportunities)
        self.state.update_stage("opportunities_generated")

    async def _run_reviews(self) -> None:
        """Run all review modules in parallel."""
        logger.info("\n🔍 Running review modules...")

        # Load content
        if not self.state.state.source_file or not self.state.state.target_file:
            raise RuntimeError("Repository files not found in state")
        source_file = Path(self.state.state.source_file)
        target_file = Path(self.state.state.target_file)
        source_content = source_file.read_text()
        target_content = target_file.read_text()

        # Run reviews in parallel
        grounding_task = self.grounding_reviewer.review_grounding(
            self.state.state.opportunities, source_content, target_content
        )

        philosophy_task = self.philosophy_reviewer.review_philosophy(self.state.state.opportunities, target_content)

        completeness_task = self.completeness_reviewer.review_completeness(
            self.state.state.opportunities, self.state.state.analysis_request or "", self.state.state.analysis_results
        )

        grounding, philosophy, completeness = await asyncio.gather(grounding_task, philosophy_task, completeness_task)

        self.state.set_review_results(grounding, philosophy, completeness)
        self.state.add_iteration_history(
            {"type": "reviews_complete", "reviews": ["grounding", "philosophy", "completeness"]}
        )

    async def _get_human_feedback(self) -> dict[str, Any]:
        """Get human feedback on opportunities."""
        logger.info("\n👤 Presenting results for review...")

        output_file = self.state.get_output_file(f"iter_{self.state.state.iteration}")

        # Prepare review results
        review_results = {
            "grounding_review": self.state.state.grounding_review,
            "philosophy_review": self.state.state.philosophy_review,
            "completeness_review": self.state.state.completeness_review,
        }

        # Run in thread to handle blocking input
        loop = asyncio.get_event_loop()
        feedback = await loop.run_in_executor(
            None,
            self.human_interface.present_opportunities,
            self.state.state.opportunities,
            review_results,
            output_file,
        )

        self.state.add_human_feedback(feedback)
        return feedback

    async def _apply_refinements(self, feedback: dict[str, Any]) -> None:
        """Apply refinement feedback."""
        logger.info("\n🔄 Applying refinements...")

        # Re-generate opportunities with feedback
        items = feedback.get("feedback", {}).get("items", [])

        # Update analysis request with refinements
        refined_request = self.state.state.analysis_request or ""
        if items:
            refined_request += "\n\nRefinements requested:\n" + "\n".join(f"- {item}" for item in items)

        # Re-run opportunity generation with feedback
        if not self.state.state.target_file:
            raise RuntimeError("Target repository file not found in state")
        target_file = Path(self.state.state.target_file)
        target_content = target_file.read_text()

        opportunities = await self.opportunity_generator.generate_opportunities(
            self.state.state.analysis_results, target_content, max_opportunities=10
        )

        self.state.set_opportunities(opportunities)
        self.state.update_stage("feedback_applied")

    async def _apply_filters(self, feedback: dict[str, Any]) -> None:
        """Apply filtering to opportunities."""
        logger.info("\n🔽 Filtering opportunities...")

        filters = feedback.get("feedback", {}).get("filters", {})
        opportunities = self.state.state.opportunities

        # Apply filters
        if "min_priority" in filters:
            min_p = filters["min_priority"]
            opportunities = [o for o in opportunities if o.get("impact", {}).get("priority", 0) >= min_p]

        if "categories" in filters:
            categories = filters["categories"]
            opportunities = [o for o in opportunities if o.get("category") in categories]

        if "max_complexity" in filters:
            max_c = filters["max_complexity"]
            complexity_order = {"low": 1, "medium": 2, "high": 3}
            max_level = complexity_order.get(max_c, 3)
            opportunities = [
                o
                for o in opportunities
                if complexity_order.get(o.get("implementation", {}).get("complexity", "high"), 3) <= max_level
            ]

        logger.info(f"Filtered to {len(opportunities)} opportunities")
        self.state.set_opportunities(opportunities)
        self.state.update_stage("feedback_applied")

    async def _change_focus(self, feedback: dict[str, Any]) -> None:
        """Re-analyze with new focus areas."""
        logger.info("\n🎯 Re-analyzing with new focus...")

        new_focus = feedback.get("feedback", {}).get("areas", [])
        self.state.state.focus_areas = new_focus

        # Re-run analysis with new focus
        await self._perform_analysis(self.state.state.analysis_request or "", new_focus)

        # Re-generate opportunities
        await self._generate_opportunities()
