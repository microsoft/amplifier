"""Markdown enhancement using AI for better formatting and structure."""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path to import amplifier modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from amplifier.ccsdk_toolkit import ToolkitLogger  # type: ignore

    logger = ToolkitLogger(name="web_to_md")
except ImportError:
    logger = logging.getLogger(__name__)

try:
    from amplifier.ccsdk import claude_code_tool  # type: ignore

    CCSDK_AVAILABLE = True
except ImportError:
    CCSDK_AVAILABLE = False
    claude_code_tool = None  # type: ignore
    logger.warning("Claude Code SDK not available - enhancement will be limited")


def enhance_markdown(markdown: str, context: dict[str, Any]) -> str:
    """Enhance markdown content with AI assistance.

    Args:
        markdown: Raw markdown content
        context: Context including metadata about the page

    Returns:
        Enhanced markdown with frontmatter and improved formatting
    """
    # Add YAML frontmatter
    frontmatter = create_frontmatter(context)

    # If Claude Code SDK is available, use it for enhancement
    if CCSDK_AVAILABLE and len(markdown) > 100:
        try:
            enhanced = asyncio.run(ai_enhance(markdown, context))
            return frontmatter + enhanced
        except Exception as e:
            logger.warning(f"AI enhancement failed, using basic formatting: {e}")

    # Fallback to basic enhancement
    return frontmatter + basic_enhance(markdown)


def create_frontmatter(context: dict[str, Any]) -> str:
    """Create YAML frontmatter for the markdown file.

    Args:
        context: Metadata about the page

    Returns:
        YAML frontmatter string
    """
    lines = ["---"]

    # Add URL
    if "url" in context:
        lines.append(f"url: {context['url']}")

    # Add title (extract from markdown if not in context)
    title = context.get("title", "Untitled")
    lines.append(f"title: {title}")

    # Add domain
    if "domain" in context:
        lines.append(f"domain: {context['domain']}")

    # Add retrieval timestamp
    lines.append(f"retrieved_at: {datetime.now().isoformat()}")

    # Add content type if available
    if "content_type" in context:
        lines.append(f"content_type: {context['content_type']}")

    lines.append("---")
    lines.append("")  # Empty line after frontmatter

    return "\n".join(lines)


def basic_enhance(markdown: str) -> str:
    """Basic markdown enhancement without AI.

    Args:
        markdown: Raw markdown content

    Returns:
        Cleaned up markdown
    """
    lines = markdown.split("\n")
    enhanced_lines = []

    for line in lines:
        # Clean up excessive whitespace
        line = line.rstrip()

        # Ensure headings have space after #
        if line.startswith("#"):
            parts = line.split(" ", 1)
            if len(parts) == 2 and not parts[0].endswith("#"):
                line = parts[0] + " " + parts[1].strip()

        enhanced_lines.append(line)

    # Join with single newlines, avoiding excessive blank lines
    result = []
    prev_blank = False

    for line in enhanced_lines:
        is_blank = not line.strip()

        # Allow max 2 consecutive blank lines
        if is_blank and prev_blank:
            continue

        result.append(line)
        prev_blank = is_blank

    return "\n".join(result)


async def ai_enhance(markdown: str, context: dict[str, Any]) -> str:
    """Use AI to enhance markdown formatting and structure.

    Args:
        markdown: Raw markdown content
        context: Context about the page

    Returns:
        AI-enhanced markdown
    """
    if claude_code_tool is None:
        # Should never happen if CCSDK_AVAILABLE check is done first
        return markdown

    prompt = f"""Please enhance this markdown content for better readability and structure.

URL: {context.get("url", "unknown")}
Domain: {context.get("domain", "unknown")}

Current markdown:
{markdown[:3000]}  # Limit to avoid token limits

Please:
1. Fix any formatting issues
2. Ensure proper heading hierarchy
3. Clean up link formatting
4. Improve list formatting
5. Add appropriate line breaks for readability
6. Preserve all original content and links

Return only the enhanced markdown, no explanation."""

    try:
        result = await claude_code_tool(prompt=prompt, tool_name="markdown_enhancer")

        # Extract markdown from response if wrapped
        if "```" in result:
            # Extract content between markdown blocks
            lines = result.split("\n")
            in_block = False
            extracted = []

            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block or not line.strip().startswith("```"):
                    extracted.append(line)

            return "\n".join(extracted)

        return result

    except Exception as e:
        logger.error(f"AI enhancement failed: {e}")
        return markdown  # Return original on error
