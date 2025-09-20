"""Text summarization module with minimalist approach."""

import re


def summarize_text(content: str, max_lines: int = 5) -> str:
    """Create a concise summary of text content.

    Uses simple heuristics to extract the most important lines:
    - First paragraph (often introduces the topic)
    - Lines with key indicators (conclusion, summary, etc.)
    - Lines that are longer (tend to be more informative)

    Args:
        content: Text to summarize
        max_lines: Maximum number of lines in summary

    Returns:
        Summary as a string
    """
    if not content:
        return "(empty file)"

    lines = content.strip().split("\n")
    if not lines:
        return "(empty file)"

    # Filter out blank lines and very short lines
    meaningful_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20]

    if not meaningful_lines:
        # Fall back to any non-empty lines
        meaningful_lines = [line.strip() for line in lines if line.strip()]

    if len(meaningful_lines) <= max_lines:
        return "\n".join(meaningful_lines)

    # Score lines by importance
    scored_lines = []

    for idx, line in enumerate(meaningful_lines):
        score = 0

        # First few lines get bonus
        if idx < 3:
            score += 10 - (idx * 2)

        # Lines with summary keywords
        summary_keywords = ["summary", "conclusion", "overview", "abstract", "introduction"]
        if any(keyword in line.lower() for keyword in summary_keywords):
            score += 5

        # Longer lines (but not too long)
        line_len = len(line)
        if 50 <= line_len <= 200:
            score += 3
        elif line_len > 200:
            score += 1

        # Lines that look like headers (short but meaningful)
        if line_len < 80 and (line[0].isupper() or line.startswith("#")):
            score += 4

        scored_lines.append((score, idx, line))

    # Sort by score and take top lines, then restore original order
    scored_lines.sort(key=lambda x: x[0], reverse=True)
    top_indices = sorted([idx for _, idx, _ in scored_lines[:max_lines]])

    summary_lines = [meaningful_lines[idx] for idx in top_indices]

    return "\n".join(summary_lines)


def extract_key_points(content: str, max_points: int = 3) -> list[str]:
    """Extract key points from text.

    Args:
        content: Text to analyze
        max_points: Maximum number of points to extract

    Returns:
        List of key points
    """
    if not content:
        return []

    # Look for bullet points or numbered lists
    bullet_pattern = r"^[\s]*[•\-\*\d+\.]+\s+(.+)"
    points = re.findall(bullet_pattern, content, re.MULTILINE)

    if points:
        return points[:max_points]

    # Fall back to first sentences of paragraphs
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    key_points = []

    for para in paragraphs[:max_points]:
        # Get first sentence
        sentences = para.split(". ")
        if sentences:
            first_sentence = sentences[0].strip()
            if first_sentence and not first_sentence.endswith("."):
                first_sentence += "."
            key_points.append(first_sentence)

    return key_points


__all__ = ["summarize_text", "extract_key_points"]
