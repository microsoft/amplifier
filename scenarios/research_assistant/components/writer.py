"""Report writing component."""

import logging

from anthropic import Anthropic

from ..cli import get_user_input
from ..cli import print_info
from ..cli import print_progress
from ..models import DeepResearchFindings
from ..models import PreliminaryFindings
from ..models import ResearchContext
from ..models import Theme

logger = logging.getLogger(__name__)


class ReportWriter:
    """Generates research reports with iterative refinement."""

    def __init__(self: "ReportWriter", api_key: str) -> None:
        """Initialize report writer.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)

    async def generate_report(
        self: "ReportWriter",
        context: ResearchContext,
        preliminary: PreliminaryFindings,
        deep_research: DeepResearchFindings,
        themes: list[Theme],
    ) -> str:
        """Generate comprehensive research report.

        Args:
            context: Research context
            preliminary: Preliminary findings
            deep_research: Deep research findings
            themes: Refined themes

        Returns:
            Markdown-formatted report
        """
        print_progress("Synthesizing research into comprehensive report...")

        all_notes = preliminary.notes + deep_research.notes
        verified_notes = [n for n in all_notes if n.verified]

        all_sources = preliminary.sources + deep_research.sources
        high_cred_sources = [s for s in all_sources if s.credibility.value == "high"]

        themes_text = "\n".join([f"- {t.title}: {t.description}" for t in themes])

        prompt = f"""Generate a comprehensive research report based on this research:

{context.to_prompt_context()}

Key Themes:
{themes_text}

Research Statistics:
- Total sources: {len(all_sources)}
- High credibility sources: {len(high_cred_sources)}
- Verified notes: {len(verified_notes)}

Generate a well-structured markdown report with:

# Executive Summary
<2-3 paragraph overview of key findings>

# Key Themes
<For each theme, discuss findings with supporting evidence>

# Detailed Findings
<Organized by theme, with specific insights and data>

# Sources
<List high-credibility sources used>

Use proper markdown formatting, cite sources, and organize information clearly."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=4096, messages=[{"role": "user", "content": prompt}]
        )

        report = ""
        for block in response.content:
            if hasattr(block, "text"):
                report = block.text  # type: ignore[attr-defined]
                break
        if not report:
            report = str(response.content[0])

        print_progress("Report generated successfully")

        return report

    async def refine_with_feedback(self: "ReportWriter", draft: str, context: ResearchContext) -> str:
        """Interactive refinement loop with user feedback.

        Args:
            draft: Initial report draft
            context: Research context

        Returns:
            Final refined report
        """
        max_iterations = 3
        iteration = 0
        current_draft = draft

        while iteration < max_iterations:
            print_info(f"\n=== Report Draft (Iteration {iteration + 1}) ===\n")
            print(current_draft[:2000])  # Show first 2000 chars
            if len(current_draft) > 2000:
                print("\n[... content truncated ...]")
            print()

            feedback = get_user_input(
                "Is this report satisfactory? (yes/no/feedback). Type 'yes' to finalize, 'no' for regeneration, or provide specific feedback"
            )

            if feedback.lower() in ["yes", "y"]:
                print_progress("Report finalized!")
                return current_draft

            if feedback.lower() in ["no", "n"]:
                feedback = "Regenerate with better structure and more detailed analysis"

            print_progress("Refining report based on your feedback...")

            current_draft = await self._refine_report(current_draft, context, feedback)

            iteration += 1

        print_info("Max iterations reached. Using current draft.")
        return current_draft

    async def _refine_report(self: "ReportWriter", draft: str, context: ResearchContext, feedback: str) -> str:
        """Refine report based on feedback.

        Args:
            draft: Current draft
            context: Research context
            feedback: User feedback

        Returns:
            Refined report
        """
        prompt = f"""Refine this research report based on user feedback:

Research Context:
{context.to_prompt_context()}

Current Report:
{draft[:3000]}

User Feedback:
{feedback}

Generate an improved version that addresses the feedback while maintaining the core findings.
Return the complete revised report in markdown format."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=4096, messages=[{"role": "user", "content": prompt}]
        )

        refined = ""
        for block in response.content:
            if hasattr(block, "text"):
                refined = block.text  # type: ignore[attr-defined]
                break
        if not refined:
            refined = str(response.content[0])

        return refined
