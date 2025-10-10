"""
Review workflow orchestration.

Coordinates the markdown-based review process.
"""

import subprocess
import sys
from pathlib import Path

from amplifier.ccsdk_toolkit.defensive import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive import write_json_with_retry
from amplifier.utils.logger import get_logger

from .generator import MarkdownGenerator
from .merger import FeedbackMerger
from .state import ReviewStateManager

logger = get_logger(__name__)


class ReviewWorkflow:
    """Orchestrates the markdown review workflow."""

    def __init__(self, session_dir: Path):
        """Initialize workflow.

        Args:
            session_dir: Session directory for all files
        """
        self.session_dir = session_dir
        self.review_dir = session_dir / "review"
        self.review_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.generator = MarkdownGenerator()
        self.merger = FeedbackMerger()
        self.state_manager = ReviewStateManager(self.review_dir)

    async def run_review_workflow(self, opportunities_file: Path, skip_review: bool = False) -> Path:
        """Run the complete review workflow.

        Args:
            opportunities_file: Path to JSON file with opportunities
            skip_review: If True, skip the manual review step

        Returns:
            Path to reviewed opportunities file
        """
        logger.info("\n" + "=" * 70)
        logger.info("MARKDOWN REVIEW WORKFLOW")
        logger.info("=" * 70)

        # Load opportunities
        data = read_json_with_retry(opportunities_file, default={})
        opportunities = data.get("opportunities", [])

        if not opportunities:
            logger.warning("No opportunities to review")
            return opportunities_file

        logger.info(f"Loaded {len(opportunities)} opportunities for review")

        # Check for resume
        if self.state_manager.state.markdown_files:
            logger.info("Resuming previous review session")
            logger.info(self.state_manager.get_progress())
            markdown_files = [Path(f) for f in self.state_manager.state.markdown_files]
        else:
            # Generate markdown files
            logger.info("\n📝 Generating markdown files...")
            markdown_files = self.generator.generate_markdown_files(opportunities, self.review_dir)
            self.state_manager.set_markdown_files(markdown_files)

        if not skip_review:
            # Prompt user to review
            self._prompt_for_review(markdown_files)

            # Wait for user to complete review
            if not self._wait_for_user_confirmation():
                logger.info("Review cancelled by user")
                return opportunities_file
        else:
            logger.info("Skipping manual review step (--skip-review flag)")

        # Mark review complete
        self.state_manager.mark_review_complete()

        # Merge feedback
        logger.info("\n🔄 Merging feedback from markdown files...")
        enhanced, rejected = await self.merger.merge_feedback(markdown_files, opportunities)

        # Save results
        self.state_manager.set_results(enhanced, rejected)

        # Write final output
        output_file = self.session_dir / "opportunities_reviewed.json"
        output_data = {
            "opportunities": enhanced,
            "rejected": rejected,
            "metadata": {
                "original_count": len(opportunities),
                "enhanced_count": len(enhanced),
                "rejected_count": len(rejected),
                "human_reviewed": True,
            },
        }

        write_json_with_retry(output_data, output_file)
        logger.info(f"\n✅ Review complete! Enhanced {len(enhanced)} opportunities, rejected {len(rejected)}")
        logger.info(f"📄 Results saved to: {output_file}")

        return output_file

    def _prompt_for_review(self, markdown_files: list[Path]) -> None:
        """Prompt user to review markdown files."""
        logger.info("\n" + "=" * 70)
        logger.info("MANUAL REVIEW REQUIRED")
        logger.info("=" * 70)
        logger.info("\n📁 Markdown files generated in:")
        logger.info(f"   {self.review_dir}")
        logger.info("\n📝 Files to review:")

        # Show first 5 files
        for i, filepath in enumerate(markdown_files[:5], 1):
            logger.info(f"   {i}. {filepath.name}")

        if len(markdown_files) > 5:
            logger.info(f"   ... and {len(markdown_files) - 5} more")

        logger.info("\n💡 HOW TO REVIEW:")
        logger.info("1. Open the markdown files in your editor")
        logger.info("2. Add feedback in the 'Human Feedback' section")
        logger.info("3. You can:")
        logger.info("   - Accept as-is (leave feedback blank)")
        logger.info("   - Suggest modifications")
        logger.info("   - Mark for rejection (write 'reject' with reason)")
        logger.info("   - Adjust priority or effort estimates")
        logger.info("4. Save your changes")
        logger.info("5. Return here and press Enter to continue")

        # Try to open the directory in the system file explorer
        self._try_open_directory(self.review_dir)

    def _try_open_directory(self, directory: Path) -> None:
        """Try to open directory in system file explorer."""
        try:
            system = sys.platform
            if system == "darwin":  # macOS
                subprocess.run(["open", str(directory)], check=False)
            elif system == "win32":  # Windows
                subprocess.run(["explorer", str(directory)], check=False)
            elif system.startswith("linux"):  # Linux
                # Try xdg-open first (most common)
                subprocess.run(["xdg-open", str(directory)], check=False)
        except Exception:
            # Silently fail if we can't open the directory
            pass

    def _wait_for_user_confirmation(self) -> bool:
        """Wait for user to confirm review completion."""
        logger.info("\n" + "=" * 70)

        try:
            response = input("\nPress Enter when review is complete (or 'skip' to skip): ").strip().lower()

            if response == "skip":
                logger.info("Skipping review - using original opportunities")
                return False

            return True

        except (EOFError, KeyboardInterrupt):
            logger.info("\nReview interrupted")
            return False
