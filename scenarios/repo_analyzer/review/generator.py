"""
Markdown generation from JSON opportunities.

Converts JSON opportunities to readable markdown files for human review.
"""

import re
from pathlib import Path
from typing import Any

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownGenerator:
    """Generate markdown files from opportunities."""

    def generate_markdown_files(self, opportunities: list[dict[str, Any]], output_dir: Path) -> list[Path]:
        """Generate markdown files for each opportunity.

        Args:
            opportunities: List of opportunity dictionaries
            output_dir: Directory to write markdown files

        Returns:
            List of generated file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []

        for idx, opportunity in enumerate(opportunities, 1):
            # Create slugified filename
            title = opportunity.get("title", f"Opportunity {idx}")
            slug = self._slugify(title)
            filename = f"{idx:03d}-{slug}.md"
            filepath = output_dir / filename

            # Generate markdown content
            content = self._generate_markdown(opportunity, idx)

            # Write file
            filepath.write_text(content, encoding="utf-8")
            generated_files.append(filepath)

        logger.info(f"Generated {len(generated_files)} markdown files in {output_dir}")
        return generated_files

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        # Convert to lowercase
        text = text.lower()
        # Replace non-alphanumeric with hyphens
        text = re.sub(r"[^a-z0-9]+", "-", text)
        # Remove leading/trailing hyphens
        text = text.strip("-")
        # Limit length
        if len(text) > 50:
            text = text[:50].rsplit("-", 1)[0]
        return text or "opportunity"

    def _generate_markdown(self, opportunity: dict[str, Any], index: int) -> str:
        """Generate markdown content for an opportunity."""
        lines = []

        # Add metadata as HTML comment
        lines.append("<!-- OPPORTUNITY METADATA")
        lines.append(f"Index: {index}")
        lines.append(f"ID: {opportunity.get('id', 'unknown')}")
        lines.append(f"Category: {opportunity.get('category', 'unknown')}")
        lines.append(f"Priority: {opportunity.get('impact', {}).get('priority', 'N/A')}")
        lines.append("-->")
        lines.append("")

        # Title
        title = opportunity.get("title", f"Opportunity {index}")
        lines.append(f"# {title}")
        lines.append("")

        # Quick Info
        lines.append("## Quick Info")
        lines.append("")
        lines.append(f"- **Category**: {opportunity.get('category', 'unknown')}")
        lines.append(f"- **Priority**: {opportunity.get('impact', {}).get('priority', 'N/A')}/10")
        lines.append(f"- **Effort**: {opportunity.get('implementation', {}).get('estimated_effort', 'unknown')}")
        lines.append(f"- **Complexity**: {opportunity.get('implementation', {}).get('complexity', 'unknown')}")
        lines.append("")

        # Description
        lines.append("## Description")
        lines.append("")
        description = opportunity.get("description", "No description provided.")
        lines.append(description)
        lines.append("")

        # Impact
        lines.append("## Impact")
        lines.append("")
        impact = opportunity.get("impact", {})
        if impact.get("benefits"):
            lines.append("### Benefits")
            lines.append("")
            for benefit in impact.get("benefits", []):
                lines.append(f"- {benefit}")
            lines.append("")

        if impact.get("risks"):
            lines.append("### Risks")
            lines.append("")
            for risk in impact.get("risks", []):
                lines.append(f"- {risk}")
            lines.append("")

        # Implementation
        lines.append("## Implementation")
        lines.append("")
        impl = opportunity.get("implementation", {})

        if impl.get("approach"):
            lines.append("### Approach")
            lines.append("")
            lines.append(impl.get("approach", ""))
            lines.append("")

        if impl.get("steps"):
            lines.append("### Steps")
            lines.append("")
            for i, step in enumerate(impl.get("steps", []), 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        if impl.get("files_to_modify"):
            lines.append("### Files to Modify")
            lines.append("")
            for file in impl.get("files_to_modify", []):
                lines.append(f"- `{file}`")
            lines.append("")

        if impl.get("dependencies"):
            lines.append("### Dependencies")
            lines.append("")
            for dep in impl.get("dependencies", []):
                lines.append(f"- {dep}")
            lines.append("")

        # Evidence
        if opportunity.get("evidence"):
            lines.append("## Evidence")
            lines.append("")
            evidence = opportunity.get("evidence", {})

            if evidence.get("source_examples"):
                lines.append("### Examples from Source Repository")
                lines.append("")
                for example in evidence.get("source_examples", []):
                    lines.append(f"- {example}")
                lines.append("")

            if evidence.get("patterns_found"):
                lines.append("### Patterns Identified")
                lines.append("")
                for pattern in evidence.get("patterns_found", []):
                    lines.append(f"- {pattern}")
                lines.append("")

        # Feedback Section
        lines.append("## Human Feedback")
        lines.append("")
        lines.append("<!-- FEEDBACK START -->")
        lines.append("")
        lines.append("*[Please add your feedback here. You can:*")
        lines.append("- *Accept as-is*")
        lines.append("- *Suggest modifications*")
        lines.append("- *Mark for rejection with reason*")
        lines.append("- *Request more details*")
        lines.append("- *Adjust priority or effort estimates]*")
        lines.append("")
        lines.append("<!-- FEEDBACK END -->")
        lines.append("")

        return "\n".join(lines)
