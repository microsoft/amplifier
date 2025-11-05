#!/usr/bin/env python3
"""
Blog Post Writer - Main Orchestrator and CLI

Coordinates the blog writing pipeline with state management.
"""

import asyncio
import sys
from pathlib import Path

import click

from amplifier.utils.logger import get_logger

from .blog_writer import BlogWriter
from .source_reviewer import SourceReviewer
from .state import StateManager
from .state import extract_title_from_markdown
from .state import slugify
from .style_extractor import StyleExtractor
from .style_reviewer import StyleReviewer
from .user_feedback import UserFeedbackHandler

logger = get_logger(__name__)


class BlogPostPipeline:
    """Orchestrates the blog post writing pipeline."""

    def __init__(self, state_manager: StateManager):
        """Initialize pipeline with state management.

        Args:
            state_manager: State manager instance
        """
        self.state = state_manager
        self.style_extractor = StyleExtractor()
        self.blog_writer = BlogWriter()
        self.source_reviewer = SourceReviewer()
        self.style_reviewer = StyleReviewer()
        self.user_feedback = UserFeedbackHandler()

        # Store inputs
        self.brain_dump: str = ""
        self.brain_dump_path: Path | None = None
        self.writings_dir: Path | None = None
        self.output_path: Path | None = None

    async def run(
        self,
        brain_dump_path: Path,
        writings_dir: Path,
        output_path: Path,
        additional_instructions: str | None = None,
    ) -> bool:
        """Run the complete pipeline.

        Args:
            brain_dump_path: Path to idea/brain dump markdown
            writings_dir: Directory with author's writings
            output_path: Output path for final blog
            additional_instructions: Optional guidance (e.g., "remove private info")

        Returns:
            True if successful, False otherwise
        """
        # Store paths and instructions
        self.brain_dump_path = brain_dump_path
        self.writings_dir = writings_dir
        self.output_path = output_path
        self.additional_instructions = additional_instructions or ""

        # Update state with inputs
        self.state.state.brain_dump_path = str(brain_dump_path)
        self.state.state.writings_dir = str(writings_dir)
        self.state.state.output_path = str(output_path)
        self.state.state.additional_instructions = additional_instructions
        self.state.save()

        # Load brain dump/idea
        try:
            self.brain_dump = brain_dump_path.read_text()
            logger.info(f"Loaded idea: {brain_dump_path.name}")
        except Exception as e:
            logger.error(f"Could not read idea: {e}")
            return False

        # Resume from saved stage if applicable
        stage = self.state.state.stage
        logger.info(f"Starting from stage: {stage}")

        try:
            # Execute pipeline stages
            if stage == "initialized":
                await self._extract_style()
                stage = self.state.state.stage

            if stage == "style_extracted":
                await self._write_initial_draft()
                stage = self.state.state.stage

            # Iteration loop
            while stage in ["draft_written", "revision_complete"]:
                if not self.state.increment_iteration():
                    logger.warning("Max iterations reached")
                    break

                # Source review
                await self._review_sources()

                # Style review
                await self._review_style()

                # Check if revision needed
                needs_revision = self.state.state.source_review.get(
                    "needs_revision", False
                ) or self.state.state.style_review.get("needs_revision", False)

                if needs_revision:
                    await self._revise_draft()

                # User feedback
                feedback = await self._get_user_feedback()
                if feedback.get("is_approved"):
                    break

                if feedback.get("continue_iteration"):
                    await self._apply_user_feedback(feedback, increment_after=True)
                else:
                    break

                stage = self.state.state.stage

            # Save final output
            await self._save_output()
            self.state.mark_complete()

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False

    async def _extract_style(self) -> None:
        """Extract author's writing style."""
        logger.info("\n📝 Extracting author's style...")
        self.state.update_stage("extracting_style")

        assert self.writings_dir is not None, "writings_dir must be set before extracting style"
        style_profile = await self.style_extractor.extract_style(self.writings_dir)
        self.state.set_style_profile(style_profile)
        self.state.update_stage("style_extracted")

    async def _write_initial_draft(self) -> None:
        """Write initial blog draft."""
        logger.info("\n✍️ Writing initial blog draft...")
        self.state.update_stage("writing_draft")

        draft = await self.blog_writer.write_blog(
            self.brain_dump,
            self.state.state.style_profile,
            additional_instructions=self.additional_instructions,
        )

        # Debug: Log draft info
        logger.debug(f"Generated draft length: {len(draft)} chars")
        logger.debug(f"Draft preview: {draft[:200]}...")

        self.state.update_draft(draft)
        self.state.update_stage("draft_written")

    async def _review_sources(self) -> None:
        """Review draft for source accuracy."""
        logger.info("\n🔍 Reviewing source accuracy...")

        review = await self.source_reviewer.review_sources(
            self.state.state.current_draft,
            self.brain_dump,
            additional_instructions=self.additional_instructions,
            user_feedback_history=self.state.state.user_feedback,
        )

        self.state.set_source_review(review)
        self.state.add_iteration_history({"type": "source_review", "review": review})

    async def _review_style(self) -> None:
        """Review draft for style consistency."""
        logger.info("\n🎨 Reviewing style consistency...")

        review = await self.style_reviewer.review_style(
            self.state.state.current_draft,
            self.state.state.style_profile,
        )

        self.state.set_style_review(review)
        self.state.add_iteration_history({"type": "style_review", "review": review})

    async def _revise_draft(self) -> None:
        """Revise draft based on reviews."""
        logger.info("\n🔄 Revising draft based on reviews...")

        # Compile feedback from reviews
        feedback = {
            "source_issues": self.state.state.source_review.get("issues", []),
            "style_issues": self.state.state.style_review.get("issues", []),
            "user_requests": [],  # Will be filled by user feedback
        }

        draft = await self.blog_writer.write_blog(
            self.brain_dump,
            self.state.state.style_profile,
            previous_draft=self.state.state.current_draft,
            feedback=feedback,
            additional_instructions=self.additional_instructions,
        )

        self.state.update_draft(draft)
        self.state.update_stage("revision_complete")

    async def _get_user_feedback(self) -> dict:
        """Get user feedback on current draft."""
        logger.info("\n👤 Getting user feedback...")

        # Get the path to the saved draft file in session directory
        draft_file_path = self.state.session_dir / f"draft_iter_{self.state.state.iteration}.md"

        # Run in thread to handle blocking input
        loop = asyncio.get_event_loop()
        feedback = await loop.run_in_executor(
            None,
            self.user_feedback.get_user_feedback,
            self.state.state.current_draft,
            self.state.state.iteration,
            draft_file_path,
        )

        self.state.add_user_feedback(feedback)
        self.state.add_iteration_history({"type": "user_feedback", "feedback": feedback})

        return feedback

    async def _apply_user_feedback(self, parsed_feedback: dict, increment_after: bool = False) -> None:
        """Apply user feedback to draft.

        Args:
            parsed_feedback: The parsed user feedback
            increment_after: If True, increment iteration before saving draft to prevent overwriting
        """
        if not parsed_feedback.get("has_feedback"):
            return

        logger.info("\n📝 Applying user feedback...")

        # Format feedback for revision
        feedback = self.user_feedback.format_feedback_for_revision(parsed_feedback)

        # Add issues from reviews
        feedback["source_issues"] = self.state.state.source_review.get("issues", [])
        feedback["style_issues"] = self.state.state.style_review.get("issues", [])

        draft = await self.blog_writer.write_blog(
            self.brain_dump,
            self.state.state.style_profile,
            previous_draft=self.state.state.current_draft,
            feedback=feedback,
            additional_instructions=self.additional_instructions,
        )

        # Increment BEFORE saving so we write to next iteration
        if increment_after and not self.state.increment_iteration():
            logger.warning("Max iterations reached while applying user feedback")
            return

        self.state.update_draft(draft)
        self.state.update_stage("revision_complete")

    async def _save_output(self) -> None:
        """Save final blog post to output file with slug-based filename."""
        # Extract title from the blog post
        title = extract_title_from_markdown(self.state.state.current_draft)

        if title:
            # Create slug from title for the filename
            slug = slugify(title)
            # Use the slug as filename in session directory
            output_path = self.state.session_dir / f"{slug}.md"
            logger.info(f"\n💾 Saving final blog post: {slug}.md")
            logger.info(f"   Title: {title}")
        else:
            # Fallback to provided output path if no title found
            output_path = self.output_path
            if output_path is None:
                logger.error("No output path available - cannot save blog post")
                return
            logger.info(f"\n💾 Saving final blog post to: {output_path}")

        try:
            output_path.write_text(self.state.state.current_draft)
            logger.info(f"✅ Blog post saved to: {output_path}")
            # Update state with actual output path
            self.state.state.output_path = str(output_path)
            self.state.save()
        except Exception as e:
            logger.error(f"Could not save output: {e}")


# CLI Interface
@click.command()
@click.option(
    "--idea",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to idea/brain dump markdown file",
)
@click.option(
    "--writings-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing author's writings for style extraction",
)
@click.option(
    "--instructions",
    type=str,
    default=None,
    help="Additional instructions/context to guide the writing (e.g., 'remove private info', 'focus on X')",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for final blog post (default: auto-generated from title in session dir)",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from saved state in data/state.json",
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset state and start fresh",
)
@click.option(
    "--max-iterations",
    type=int,
    default=10,
    help="Maximum iterations (default: 10)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    idea: Path,
    writings_dir: Path,
    instructions: str | None,
    output: Path | None,
    resume: bool,
    reset: bool,
    max_iterations: int,
    verbose: bool,
):
    """Blog Post Writer - Transform ideas into polished blog posts.

    This tool extracts your writing style from existing writings and uses it
    to transform rough ideas/brain dumps into polished blog posts that match your voice.

    Example:
        python -m scenarios.blog_writer \\
            --idea ideas.md \\
            --writings-dir my_posts/ \\
            --instructions "Remove any private company names mentioned"
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")  # Access underlying logger

    # Determine session directory
    session_dir = None
    if resume:
        # Find most recent session for resume
        base_dir = Path(".data/blog_post_writer")
        if base_dir.exists():
            sessions = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
            if sessions:
                session_dir = sessions[0]
                logger.info(f"Resuming session: {session_dir.name}")

    # Create state manager (new session if not resuming)
    state_manager = StateManager(session_dir)

    # Handle reset
    if reset:
        state_manager.reset()
        logger.info("State reset - starting fresh")

    # Set max iterations
    state_manager.state.max_iterations = max_iterations

    # Check for resume
    if resume and state_manager.state_file.exists() and not reset:
        logger.info("Resuming from saved state")
        # Use saved paths if not provided
        if state_manager.state.brain_dump_path:
            idea = Path(state_manager.state.brain_dump_path)
        if state_manager.state.writings_dir:
            writings_dir = Path(state_manager.state.writings_dir)
        if state_manager.state.output_path and output is None:
            output = Path(state_manager.state.output_path)
        if state_manager.state.additional_instructions and instructions is None:
            instructions = state_manager.state.additional_instructions

    # Create and run pipeline
    pipeline = BlogPostPipeline(state_manager)

    logger.info("🚀 Starting Blog Post Writer Pipeline")
    logger.info(f"  Session: {state_manager.session_dir}")
    logger.info(f"  Idea: {idea.name}")
    logger.info(f"  Writings dir: {writings_dir}")
    if instructions:
        logger.info(f"  Instructions: {instructions}")
    if output:
        logger.info(f"  Output: {output}")
    else:
        logger.info("  Output: Auto-generated from title")
    logger.info(f"  Max iterations: {max_iterations}")

    # Use a placeholder output path (will be overridden with slug-based name)
    output_path = output or state_manager.session_dir / "blog_post.md"

    success = asyncio.run(
        pipeline.run(
            brain_dump_path=idea,
            writings_dir=writings_dir,
            output_path=output_path,
            additional_instructions=instructions,
        )
    )

    if success:
        logger.info("\n✨ Blog post generation complete!")
        final_output = state_manager.state.output_path
        logger.info(f"📄 Output saved to: {final_output}")
        return 0
    logger.error("\n❌ Blog post generation failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
