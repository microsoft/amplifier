"""Theme extraction and refinement component."""

import logging

from anthropic import Anthropic

from ..cli import get_user_input
from ..cli import print_info
from ..cli import print_progress
from ..models import PreliminaryFindings
from ..models import ResearchContext
from ..models import Theme

logger = logging.getLogger(__name__)


class ThemeManager:
    """Extracts and refines research themes with user feedback."""

    def __init__(self: "ThemeManager", api_key: str) -> None:
        """Initialize theme manager.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)

    async def extract_themes(
        self: "ThemeManager", findings: PreliminaryFindings, context: ResearchContext
    ) -> list[Theme]:
        """Extract broad themes from research findings.

        Args:
            findings: Preliminary research findings
            context: Research context

        Returns:
            List of Theme objects
        """
        print_progress("Analyzing research notes to extract themes...")

        notes_text = "\n".join([f"- {note.content}" for note in findings.notes[:100]])

        prompt = f"""Analyze these research notes and extract 5-10 broad themes that answer this research question:

{context.to_prompt_context()}

Research Notes:
{notes_text}

Extract major themes that:
- Directly address the research question
- Are supported by multiple notes
- Represent distinct aspects or dimensions
- Are actionable or insightful

For each theme, provide:
THEME: <concise title>
DESCRIPTION: <1-2 sentence description>
PRIORITY: <number 1-10, higher = more important>

Separate themes with ---"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=2048, messages=[{"role": "user", "content": prompt}]
        )

        themes_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                themes_text = block.text  # type: ignore[attr-defined]
                break
        if not themes_text:
            themes_text = str(response.content[0])

        themes = self._parse_themes_response(themes_text)

        print_progress(f"Extracted {len(themes)} themes")

        return themes

    async def refine_themes_with_user(self: "ThemeManager", themes: list[Theme]) -> list[Theme]:
        """Interactive loop to refine themes with user.

        Args:
            themes: Initial themes

        Returns:
            Refined theme list
        """
        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            print_info(f"\n=== Extracted Themes (Iteration {iteration + 1}) ===\n")

            for i, theme in enumerate(themes, 1):
                print(f"{i}. [{theme.priority}/10] {theme.title}")
                print(f"   {theme.description}\n")

            print_info("Top recommended themes for deep research:")
            top_themes = sorted(themes, key=lambda t: t.priority, reverse=True)[:5]
            for i, theme in enumerate(top_themes, 1):
                print(f"  {i}. {theme.title}")
            print()

            feedback = get_user_input(
                "Are these themes good? (yes/no/feedback). Type 'yes' to proceed, 'no' for another iteration, or provide specific feedback"
            )

            if feedback.lower() in ["yes", "y"]:
                for theme in themes:
                    theme.user_approved = True
                print_progress("Themes approved!")
                return themes

            if feedback.lower() in ["no", "n"]:
                feedback = "Generate a different set of themes with better focus and relevance"

            print_progress("Refining themes based on your feedback...")

            themes = await self._refine_themes(themes, feedback)

            iteration += 1

        print_info("Max iterations reached. Using current themes.")
        return themes

    async def _refine_themes(self: "ThemeManager", themes: list[Theme], feedback: str) -> list[Theme]:
        """Refine themes based on user feedback.

        Args:
            themes: Current themes
            feedback: User feedback

        Returns:
            Refined themes
        """
        themes_text = "\n".join([f"- {t.title}: {t.description}" for t in themes])

        prompt = f"""Refine these research themes based on user feedback:

Current Themes:
{themes_text}

User Feedback:
{feedback}

Generate improved themes that address the feedback. Provide 5-10 themes in the same format:

THEME: <concise title>
DESCRIPTION: <1-2 sentence description>
PRIORITY: <number 1-10, higher = more important>

Separate themes with ---"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=2048, messages=[{"role": "user", "content": prompt}]
        )

        refined_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                refined_text = block.text  # type: ignore[attr-defined]
                break
        if not refined_text:
            refined_text = str(response.content[0])

        refined_themes = self._parse_themes_response(refined_text)

        return refined_themes

    def _parse_themes_response(self: "ThemeManager", text: str) -> list[Theme]:
        """Parse Claude's themes response.

        Args:
            text: Response text

        Returns:
            List of Theme objects
        """
        theme_blocks = text.split("---")
        themes = []

        for block in theme_blocks:
            lines = [line.strip() for line in block.strip().split("\n") if line.strip()]

            if not lines:
                continue

            title = ""
            description = ""
            priority = 5

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().upper()
                    value = value.strip()

                    if key == "THEME":
                        title = value
                    elif key == "DESCRIPTION":
                        description = value
                    elif key == "PRIORITY":
                        try:
                            priority = int(value)
                        except ValueError:
                            priority = 5

            if title and description:
                themes.append(Theme(title=title, description=description, priority=priority))

        return themes[:10]
