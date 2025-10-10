"""
Human review interface module.

Presents results and collects feedback from users.
"""

import json
from pathlib import Path
from typing import Any

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class HumanReviewInterface:
    """Interface for human review and feedback."""

    def present_opportunities(
        self, opportunities: list[dict[str, Any]], review_results: dict[str, Any], output_file: Path
    ) -> dict[str, Any]:
        """Present opportunities for human review.

        Args:
            opportunities: Final opportunities list
            review_results: All review results
            output_file: Path to save opportunities

        Returns:
            Human feedback dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("REPOSITORY ANALYSIS COMPLETE")
        logger.info("=" * 70)

        # Summary statistics
        grounding = review_results.get("grounding_review", {})
        philosophy = review_results.get("philosophy_review", {})
        completeness = review_results.get("completeness_review", {})

        logger.info("\n📊 ANALYSIS SUMMARY")
        logger.info(f"  Total Opportunities: {len(opportunities)}")

        if grounding:
            summary = grounding.get("review_summary", {})
            logger.info(f"  Well Grounded: {summary.get('well_grounded', 0)}")

        if philosophy:
            alignment = philosophy.get("alignment_summary", {})
            logger.info(f"  Philosophy Fit: {alignment.get('overall_fit', 'unknown')}")

        if completeness:
            score = completeness.get("completeness_score", 0)
            logger.info(f"  Completeness: {score:.0%}")

        # Save opportunities to file
        self._save_opportunities(opportunities, output_file)
        logger.info(f"\n📄 Full results saved to: {output_file}")

        # Present top opportunities
        logger.info("\n🎯 TOP OPPORTUNITIES:")
        for i, opp in enumerate(opportunities[:5], 1):
            self._display_opportunity(i, opp)

        if len(opportunities) > 5:
            logger.info(f"\n... and {len(opportunities) - 5} more in {output_file}")

        # Get user feedback
        return self._collect_feedback(opportunities, output_file)

    def _display_opportunity(self, num: int, opportunity: dict[str, Any]) -> None:
        """Display a single opportunity."""
        logger.info(f"\n{num}. {opportunity.get('title', 'Unnamed Opportunity')}")
        logger.info(f"   Category: {opportunity.get('category', 'unknown')}")

        impact = opportunity.get("impact", {})
        logger.info(f"   Priority: {impact.get('priority', 'N/A')}/10")

        impl = opportunity.get("implementation", {})
        logger.info(f"   Effort: {impl.get('estimated_effort', 'unknown')}")
        logger.info(f"   Complexity: {impl.get('complexity', 'unknown')}")

        desc = opportunity.get("description", "")
        if desc:
            # Show first 150 chars of description
            desc_preview = desc[:150] + "..." if len(desc) > 150 else desc
            logger.info(f"   Description: {desc_preview}")

    def _save_opportunities(self, opportunities: list[dict[str, Any]], output_file: Path) -> None:
        """Save opportunities to JSON file."""
        try:
            output_data = {
                "opportunities": opportunities,
                "metadata": {"total_count": len(opportunities), "categories": self._get_category_counts(opportunities)},
            }

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(opportunities)} opportunities to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save opportunities: {e}")

    def _get_category_counts(self, opportunities: list[dict[str, Any]]) -> dict[str, int]:
        """Count opportunities by category."""
        counts = {}
        for opp in opportunities:
            cat = opp.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _collect_feedback(self, opportunities: list[dict[str, Any]], output_file: Path) -> dict[str, Any]:
        """Collect user feedback interactively."""
        logger.info("\n" + "=" * 70)
        logger.info("REVIEW OPTIONS")
        logger.info("=" * 70)
        logger.info("\nWhat would you like to do?")
        logger.info("  1. approve  - Accept the analysis as-is")
        logger.info("  2. filter   - Filter opportunities (by category/priority)")
        logger.info("  3. refine   - Request refinement with specific feedback")
        logger.info("  4. focus    - Re-analyze with different focus areas")
        logger.info("  5. skip     - Skip review and continue")

        logger.info(f"\n💡 TIP: Review {output_file} for full details")

        try:
            choice = input("\nYour choice (approve/filter/refine/focus/skip): ").strip().lower()

            if choice == "approve" or choice == "1":
                return {"action": "approve", "approved": True, "feedback": None}

            if choice == "filter" or choice == "2":
                return self._collect_filter_criteria()

            if choice == "refine" or choice == "3":
                return self._collect_refinement_feedback()

            if choice == "focus" or choice == "4":
                return self._collect_focus_areas()

            # skip or anything else
            return {"action": "skip", "approved": False, "feedback": None}

        except (EOFError, KeyboardInterrupt):
            logger.info("\nReview interrupted - saving current state")
            return {"action": "interrupted", "approved": False, "feedback": None}

    def _collect_filter_criteria(self) -> dict[str, Any]:
        """Collect filtering criteria from user."""
        logger.info("\nFILTER OPPORTUNITIES")
        logger.info("Enter criteria (leave blank to skip):")

        min_priority = input("  Minimum priority (1-10): ").strip()
        categories = input("  Categories to include (comma-separated): ").strip()
        max_complexity = input("  Maximum complexity (low/medium/high): ").strip()

        filters = {}
        if min_priority.isdigit():
            filters["min_priority"] = int(min_priority)
        if categories:
            filters["categories"] = [c.strip() for c in categories.split(",")]
        if max_complexity:
            filters["max_complexity"] = max_complexity

        return {"action": "filter", "approved": False, "feedback": {"type": "filter", "filters": filters}}

    def _collect_refinement_feedback(self) -> dict[str, Any]:
        """Collect specific refinement feedback."""
        logger.info("\nREFINEMENT FEEDBACK")
        logger.info("What needs improvement? (type 'done' when finished)")

        feedback_items = []
        while True:
            item = input("  > ").strip()
            if item.lower() == "done" or not item:
                break
            feedback_items.append(item)

        return {"action": "refine", "approved": False, "feedback": {"type": "refinement", "items": feedback_items}}

    def _collect_focus_areas(self) -> dict[str, Any]:
        """Collect new focus areas."""
        logger.info("\nFOCUS AREAS")
        logger.info("Enter areas to focus on (type 'done' when finished):")

        focus_areas = []
        while True:
            area = input("  > ").strip()
            if area.lower() == "done" or not area:
                break
            focus_areas.append(area)

        return {"action": "focus", "approved": False, "feedback": {"type": "focus", "areas": focus_areas}}
