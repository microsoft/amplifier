"""Markdown update for inserting generated images."""

from pathlib import Path

from amplifier.utils.logger import get_logger

from ..models import IllustrationPoint
from ..models import ImageAlternatives

logger = get_logger(__name__)


class MarkdownUpdater:
    """Updates markdown files with generated images."""

    def __init__(self, output_dir: Path):
        """Initialize markdown updater.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir

    def update_markdown(
        self,
        article_path: Path,
        images: list[ImageAlternatives],
        points: list[IllustrationPoint],
    ) -> Path:
        """Insert images into markdown with alternatives.

        Args:
            article_path: Original article path
            images: Generated images with alternatives
            points: Original illustration points

        Returns:
            Path to updated markdown file
        """
        logger.info(f"Updating markdown with {len(images)} images")

        # Read original content
        content = article_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Create mapping of illustration_id to images
        image_map = {img.illustration_id: img for img in images}

        # Sort points by line number in reverse to insert from bottom up
        sorted_points = sorted(
            [(p, image_map.get(f"illustration-{i + 1}")) for i, p in enumerate(points)],
            key=lambda x: x[0].line_number,
            reverse=True,
        )

        # Insert images at appropriate points
        for point, image_alt in sorted_points:
            if not image_alt:
                continue

            # Create image markdown
            image_markdown = self._create_image_markdown(image_alt, point)

            # Find insertion point
            insert_line = self._find_insertion_line(lines, point)

            # Insert the markdown
            if 0 <= insert_line < len(lines):
                lines.insert(insert_line, image_markdown)
                logger.info(f"Inserted image at line {insert_line}")

        # Save updated markdown
        output_path = self.output_dir / f"illustrated_{article_path.name}"
        output_path.write_text("\n".join(lines), encoding="utf-8")

        logger.info(f"Saved illustrated article: {output_path}")
        return output_path

    def _create_image_markdown(self, image_alt: ImageAlternatives, point: IllustrationPoint) -> str:
        """Create markdown for an image with alternatives.

        Args:
            image_alt: Image with alternatives
            point: Illustration point

        Returns:
            Markdown string for image
        """
        # Main image - using HTML img tag with 50% width
        primary_path = Path("images") / image_alt.primary.local_path.name
        markdown = f'\n<img src="./{primary_path}" alt="{point.section_title}" width="50%">\n'

        # Add alternatives as HTML comment
        if image_alt.alternatives:
            markdown += "\n<!-- ALTERNATIVES\n"
            for alt in image_alt.alternatives:
                alt_path = Path("images") / alt.local_path.name
                markdown += f'<img src="./{alt_path}" alt="{alt.api} version" width="50%">\n'

            markdown += "\nTo use an alternative, replace the main image above.\n"
            markdown += f"Generated from: {image_alt.primary.prompt_id}\n"
            markdown += "-->\n"

        return markdown

    def _find_insertion_line(self, lines: list[str], point: IllustrationPoint) -> int:
        """Find the best line to insert an image.

        Args:
            lines: Article lines
            point: Illustration point

        Returns:
            Line index for insertion
        """
        # Start from the point's line number
        target = point.line_number

        # Adjust based on placement preference
        if point.suggested_placement == "before_section":
            # Find the section header and insert before it
            for i in range(max(0, target - 5), min(len(lines), target + 5)):
                if lines[i].startswith("#") and point.section_title in lines[i]:
                    return i
        elif point.suggested_placement == "after_intro":
            # Insert after first paragraph of section
            for i in range(target, min(len(lines), target + 20)):
                if not lines[i].strip() and i > target:
                    return i + 1

        # Default: insert at the target line
        return min(target, len(lines))
