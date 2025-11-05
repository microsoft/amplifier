#!/usr/bin/env python3
"""
Article Illustrator - Main Orchestrator and CLI

Generates illustrations for markdown articles using AI.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from amplifier.utils.logger import get_logger

from .content_analysis import ContentAnalyzer
from .image_generation import ImageGenerator
from .markdown_update import MarkdownUpdater
from .prompt_generation import PromptGenerator
from .state import SessionManager
from .state import StageState

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class ArticleIllustratorPipeline:
    """Orchestrates the article illustration pipeline."""

    def __init__(self, article_path: Path, output_dir: Path | None = None):
        """Initialize pipeline with output directory.

        Args:
            article_path: Path to article being processed
            output_dir: Optional explicit output directory. If None, generates
                       timestamped directory: .data/article_illustrator/{article_name}_{timestamp}/
        """
        if output_dir is None:
            # Use .data directory following blog_writer pattern
            base_dir = Path(".data/article_illustrator")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            article_name = article_path.stem  # filename without extension
            self.output_dir = base_dir / f"{article_name}_{timestamp}"
        else:
            self.output_dir = output_dir

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_mgr = SessionManager(self.output_dir)
        self.state = None

    async def run(
        self,
        article_path: Path,
        style: str | None = None,
        max_images: int = 5,
        apis: list[str] | None = None,
        resume: bool = False,
        prompts_only: bool = False,
        cost_limit: float | None = None,
    ) -> bool:
        """Run the complete illustration pipeline.

        Args:
            article_path: Path to markdown article
            style: Optional style description
            max_images: Maximum images to generate
            apis: List of APIs to use for generation
            resume: Whether to resume from previous session
            prompts_only: Only generate prompts, skip images
            cost_limit: Maximum cost limit

        Returns:
            True if successful, False otherwise
        """
        if apis is None:
            apis = ["gptimage"]

        session_file = self.output_dir / ".session_state.json"

        # Handle session creation/resumption
        if resume:
            if not session_file.exists():
                logger.warning(f"Cannot resume: No session found at {self.output_dir}")
                logger.info("Starting new session instead")
                self.state = self.session_mgr.create_new(article_path, {"style": style} if style else {})
            else:
                # Load existing session
                try:
                    self.state = self.session_mgr.load_existing()

                    # Validate compatibility
                    is_compatible, mismatches = self.session_mgr.validate_compatibility(self.state, article_path, style)

                    if not is_compatible:
                        logger.warning("⚠️  Session parameter mismatch detected:")
                        for mismatch in mismatches:
                            logger.warning(f"    • {mismatch}")
                        logger.warning("")
                        logger.warning("  You can either:")
                        logger.warning("    1. Stop and use a different OUTPUT directory")
                        logger.warning("    2. Continue with mismatched parameters (may cause issues)")

                        # For non-interactive environments, fail safe
                        if not sys.stdin.isatty():
                            logger.error("Cannot prompt in non-interactive mode. Aborting.")
                            return False

                        response = input("\n  Continue anyway? (y/N): ").strip().lower()
                        if response != "y":
                            logger.info("Aborted. Specify different OUTPUT or remove --resume flag.")
                            return False

                    logger.info(f"✓ Resumed session from {self.output_dir}")
                    self.session_mgr.log_progress(self.state)

                except (FileNotFoundError, ValueError) as e:
                    logger.error(f"Failed to resume: {e}")
                    logger.info("Starting new session instead")
                    self.state = self.session_mgr.create_new(article_path, {"style": style} if style else {})
        else:
            # New session (default behavior)
            if session_file.exists():
                logger.info(f"ℹ️  Note: Existing session found at {self.output_dir}")
                logger.info("    Ignoring it. Use --resume to continue existing session.")

            self.state = self.session_mgr.create_new(article_path, {"style": style} if style else {})
            logger.info(f"Starting new session in {self.output_dir}")

        try:
            # Stage 1: Content Analysis
            if not self.state.analysis_complete:
                await self._analyze_content(max_images)

            # Stage 2: Prompt Generation
            if not self.state.prompts_complete:
                await self._generate_prompts()

            if prompts_only:
                logger.info("\n=== Prompts-only mode - skipping image generation ===")
                self._print_summary()
                return True

            # Stage 3: Image Generation
            if not self.state.images_complete:
                await self._generate_images(apis, cost_limit)

            # Stage 4: Markdown Update
            if not self.state.markdown_complete:
                await self._update_markdown()

            # Print final summary
            self._print_summary()
            return True

        except KeyboardInterrupt:
            logger.warning("\nProcess interrupted - session saved for resume")
            if self.state:
                self.session_mgr.save(self.state)
            return False

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            if self.state:
                self.session_mgr.add_error(self.state, "main", str(e))
            return False

    async def _analyze_content(self, max_images: int) -> None:
        """Stage 1: Analyze article for illustration opportunities."""
        logger.info("\n=== Stage 1: Content Analysis ===")

        if not self.state:
            raise RuntimeError("Session state not initialized")

        analyzer = ContentAnalyzer(max_images=max_images)
        self.state.illustration_points = await analyzer.analyze(self.state.article_path)

        self.session_mgr.mark_complete(self.state, StageState.ANALYSIS)
        logger.info(f"✓ Identified {len(self.state.illustration_points)} illustration points")

    async def _generate_prompts(self) -> None:
        """Stage 2: Generate image prompts."""
        logger.info("\n=== Stage 2: Prompt Generation ===")

        if not self.state:
            raise RuntimeError("Session state not initialized")

        generator = PromptGenerator(style_params=self.state.style_params)
        self.state.prompts = await generator.generate_prompts(self.state.illustration_points, self.state.article_path)

        self.session_mgr.save_prompts(self.state)
        self.session_mgr.mark_complete(self.state, StageState.PROMPTS)
        logger.info(f"✓ Generated {len(self.state.prompts)} prompts")

    async def _generate_images(self, apis: list[str], cost_limit: float | None) -> None:
        """Stage 3: Generate images using specified APIs."""
        logger.info("\n=== Stage 3: Image Generation ===")

        if not self.state:
            raise RuntimeError("Session state not initialized")

        # Create save callback for expensive operations
        async def save_callback(images, total_cost):
            if self.state:  # Check again in callback
                self.state.images = images
                self.state.images_generated = len(images)
                self.state.total_cost = total_cost
                self.session_mgr.save(self.state)

        generator = ImageGenerator(
            apis=apis,
            output_dir=self.output_dir,
            cost_limit=cost_limit,
        )

        self.state.images = await generator.generate_images(self.state.prompts, save_callback=save_callback)
        self.state.total_cost = generator.total_cost

        self.session_mgr.mark_complete(self.state, StageState.IMAGES)
        logger.info(f"✓ Generated {len(self.state.images)} sets of images")

    async def _update_markdown(self) -> None:
        """Stage 4: Update markdown with generated images."""
        logger.info("\n=== Stage 4: Markdown Update ===")

        if not self.state:
            raise RuntimeError("Session state not initialized")

        updater = MarkdownUpdater(self.output_dir)
        output_path = updater.update_markdown(
            self.state.article_path, self.state.images, self.state.illustration_points
        )

        self.session_mgr.mark_complete(self.state, StageState.MARKDOWN)
        logger.info(f"✓ Updated markdown saved to: {output_path}")

    def _print_summary(self) -> None:
        """Print final summary of the session."""
        if not self.state:
            logger.warning("No session state to summarize")
            return

        logger.info("\n" + "=" * 50)
        logger.info("ILLUSTRATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Article: {self.state.article_path.name}")
        logger.info(f"Output: {self.state.output_dir}")
        logger.info(f"Illustration points: {len(self.state.illustration_points)}")
        logger.info(f"Prompts generated: {len(self.state.prompts)}")
        logger.info(f"Images generated: {self.state.images_generated}")
        logger.info(f"Total cost: ${self.state.total_cost:.2f}")

        if self.state.errors:
            logger.warning(f"\nErrors encountered: {len(self.state.errors)}")
            for error in self.state.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error['stage']}: {error['error']}")

        if self.state.prompts:
            logger.info("\nGenerated prompts saved to: prompts.json")

        if self.state.markdown_complete:
            logger.info("\n✨ Illustrated article ready!")
            logger.info(f"   View: {self.state.output_dir}/illustrated_{self.state.article_path.name}")


# CLI Interface
@click.command()
@click.argument("article_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory (default: {article_dir}/illustrated_{article_name}_{timestamp}/)",
)
@click.option(
    "--style",
    "-s",
    help="Style description for image generation",
)
@click.option(
    "--max-images",
    "-m",
    default=5,
    help="Maximum number of images to generate",
)
@click.option(
    "--apis",
    "-a",
    multiple=True,
    default=["gptimage"],
    type=click.Choice(["imagen", "dalle", "gptimage"]),
    help="APIs to use for generation (can specify multiple)",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from previous session",
)
@click.option(
    "--prompts-only",
    is_flag=True,
    help="Generate prompts only, skip image generation",
)
@click.option(
    "--cost-limit",
    type=float,
    help="Maximum cost limit for generation",
)
def illustrate(
    article_path: Path,
    output_dir: Path | None,
    style: str | None,
    max_images: int,
    apis: tuple[str, ...],
    resume: bool,
    prompts_only: bool,
    cost_limit: float | None,
):
    """Generate illustrations for a markdown article.

    ARTICLE_PATH: Path to the markdown article to illustrate
    """
    # Log what we're doing
    logger.info(f"Article: {article_path}")
    if output_dir:
        logger.info(f"Output: {output_dir} (explicit)")
    else:
        logger.info("Output: Auto-generated timestamped directory")

    logger.info(f"APIs: {', '.join(apis)}")
    logger.info(f"Max images: {max_images}")
    if style:
        logger.info(f"Style: {style}")
    if cost_limit:
        logger.info(f"Cost limit: ${cost_limit:.2f}")
    if resume:
        logger.info("Mode: Resume existing session")

    # Create and run pipeline
    pipeline = ArticleIllustratorPipeline(article_path, output_dir)
    success = asyncio.run(
        pipeline.run(
            article_path=article_path,
            style=style,
            max_images=max_images,
            apis=list(apis),
            resume=resume,
            prompts_only=prompts_only,
            cost_limit=cost_limit,
        )
    )

    sys.exit(0 if success else 1)


def main():
    """Entry point for the application."""
    illustrate()


if __name__ == "__main__":
    main()
