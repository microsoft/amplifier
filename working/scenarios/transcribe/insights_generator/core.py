"""
Insights Generator Core Implementation

Combines summary and quotes into a single, readable insights document.
"""

from amplifier.utils.logger import get_logger

from ..quote_extractor.core import Quote
from ..summary_generator.core import Summary

logger = get_logger(__name__)


def generate_insights(
    summary: Summary | None,
    quotes: list[Quote] | None,
    title: str,
) -> str:
    """
    Combine summary and quotes into a single insights document.

    Creates a unified document with overview, key points, notable quotes,
    and central themes. Handles cases where summary or quotes may be missing.

    Args:
        summary: Summary object with overview and key points
        quotes: List of Quote objects with timestamps
        title: Title of the video/content

    Returns:
        Formatted markdown insights document
    """
    lines = [
        f"# Insights: {title}",
        "",
    ]

    # Add overview if available
    if summary and summary.overview:
        lines.extend(
            [
                "## Overview",
                "",
                summary.overview,
                "",
            ]
        )

    # Add key points if available
    if summary and summary.key_points:
        lines.extend(
            [
                "## Key Points",
                "",
            ]
        )

        # Integrate quotes with key points where relevant
        for point in summary.key_points:
            lines.append(f"- {point}")

        lines.append("")

    # Add notable quotes section if quotes are available
    if quotes:
        lines.extend(
            [
                "## Notable Quotes",
                "",
            ]
        )

        # Select most impactful quotes (limit to top 5-7)
        notable_quotes = quotes[:7] if len(quotes) > 7 else quotes

        for quote in notable_quotes:
            # Format quote with timestamp
            timestamp_str = _format_timestamp(quote.timestamp)

            # Add quote text
            lines.append(f'> "{quote.text}"')

            # Add timestamp and link if available
            if quote.timestamp_link:
                lines.append(f"> — [{timestamp_str}]({quote.timestamp_link})")
            else:
                lines.append(f"> — [{timestamp_str}]")

            # Add context if particularly insightful
            if quote.context:
                lines.append(">")
                lines.append(f"> *{quote.context}*")

            lines.append("")

    # Add central themes if available
    if summary and summary.themes:
        lines.extend(
            [
                "## Central Themes",
                "",
            ]
        )

        for theme in summary.themes:
            lines.append(f"- {theme}")

        lines.append("")

    # Add additional quotes section if there are many quotes
    if quotes and len(quotes) > 7:
        lines.extend(
            [
                "## Additional Quotes",
                "",
            ]
        )

        for quote in quotes[7:]:
            timestamp_str = _format_timestamp(quote.timestamp)

            # More compact format for additional quotes
            lines.append(f'- "{quote.text}" [{timestamp_str}]')
            if quote.timestamp_link:
                lines[-1] = f'- "{quote.text}" [[{timestamp_str}]({quote.timestamp_link})]'

        lines.append("")

    # Handle case where both summary and quotes are missing
    if not summary and not quotes:
        lines.extend(
            [
                "## Note",
                "",
                "_No insights were generated for this content. This may be due to processing errors or unavailable AI services._",
                "",
            ]
        )

    return "\n".join(lines)


def _format_timestamp(seconds: float) -> str:
    """Format timestamp as MM:SS or HH:MM:SS.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
