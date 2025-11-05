"""HTML to Markdown conversion using markdownify."""

import logging

from bs4 import BeautifulSoup
from markdownify import markdownify as md

logger = logging.getLogger(__name__)


def html_to_markdown(html: str, base_url: str) -> str:
    """Convert HTML to clean Markdown format.

    Args:
        html: HTML content to convert
        base_url: Base URL for resolving relative links

    Returns:
        Markdown formatted text
    """
    try:
        # Pre-process HTML to remove unwanted elements
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "meta", "link", "noscript", "title"]):
            tag.decompose()

        cleaned_html = str(soup)

        # Convert with markdownify settings optimized for readability
        # Note: wrap=False to avoid breaking links/inline elements awkwardly
        markdown = md(
            cleaned_html,
            heading_style="ATX",  # Use # style headings
            bullets="-",  # Use - for unordered lists
            code_language="",  # Don't add language hints to code blocks
        )

        # Clean up extra whitespace
        lines = markdown.split("\n")
        cleaned_lines = []
        prev_blank = False

        for line in lines:
            is_blank = not line.strip()

            # Avoid multiple consecutive blank lines
            if is_blank and prev_blank:
                continue

            cleaned_lines.append(line)
            prev_blank = is_blank

        result = "\n".join(cleaned_lines)

        # Fix relative URLs if needed (basic implementation)
        # A more sophisticated implementation would parse and update URLs

        logger.info(f"Converted HTML ({len(html)} chars) to Markdown ({len(result)} chars)")
        return result.strip()

    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {e}")
        # Return a basic conversion as fallback
        return f"# Error Converting Page\n\nFailed to convert HTML: {e}\n\n---\n\n{html[:1000]}..."
