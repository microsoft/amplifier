"""Content validation core functionality."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ContentValidationError(Exception):
    """Raised when content validation fails."""


@dataclass
class ValidationResult:
    """Result of content validation."""

    is_valid: bool
    reason: str | None = None
    detected_pattern: str | None = None


# Patterns that indicate paywalls or auth walls
PAYWALL_PATTERNS = [
    # Medium
    "member-only story",
    "members only",
    "this story is for members",
    # Substack
    "this post is for paid subscribers",
    "this post is for paying subscribers only",
    "upgrade to paid",
    # Patreon
    "this post is for paying subscribers",
    "unlock this post",
    # Generic
    "sign in to read",
    "sign up to read more",
    "log in to continue reading",
    "subscribe to continue reading",
    "this content is for subscribers",
    "premium content",
    "exclusive content",
]


def validate_content(html: str, markdown: str, url: str) -> ValidationResult:
    """Validate that content is accessible and not behind a paywall.

    Args:
        html: Raw HTML content
        markdown: Converted markdown content
        url: Original URL

    Returns:
        ValidationResult indicating if content is valid

    Raises:
        ContentValidationError: If content is behind paywall/auth wall
    """
    # Check for paywall patterns in HTML
    html_lower = html.lower()
    for pattern in PAYWALL_PATTERNS:
        if pattern in html_lower:
            return ValidationResult(is_valid=False, reason=f"Paywall detected: '{pattern}'", detected_pattern=pattern)

    # Check for common auth wall indicators in HTML structure
    # Count occurrences of auth-related class names in HTML
    auth_class_patterns = ["login", "signin", "signup", "paywall", "auth-wall"]
    auth_indicator_count = sum(
        html_lower.count(f'class="{pattern}"') + html_lower.count(f"class='{pattern}'")
        for pattern in auth_class_patterns
    )

    # Check if there are multiple auth indicators (suggests auth wall)
    if auth_indicator_count >= 3:
        logger.debug(f"Found {auth_indicator_count} auth-related class names in HTML")
        return ValidationResult(
            is_valid=False, reason="Multiple authentication elements detected", detected_pattern="auth_forms"
        )

    # Check markdown content quality
    # Remove YAML frontmatter
    lines = markdown.split("\n")
    content_lines = []
    in_frontmatter = False

    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if not in_frontmatter:
            content_lines.append(line)

    content_text = "\n".join(content_lines)

    # Count actual content words (excluding links, navigation)
    words = content_text.split()
    # Filter out likely navigation/link text
    content_words = [w for w in words if len(w) > 2 and not w.startswith("[") and not w.startswith("(http")]

    word_count = len(content_words)

    # Check for suspiciously short content (very lenient threshold)
    # Note: Even simple pages like example.com have some real content
    if word_count < 15:
        logger.debug(f"Content has only {word_count} words")
        return ValidationResult(
            is_valid=False,
            reason=f"Content too short ({word_count} words), likely incomplete or auth-walled",
            detected_pattern="short_content",
        )

    # Count auth-related text in markdown
    auth_mentions = sum(
        1 for pattern in ["sign in", "sign up", "log in", "subscribe", "member"] if pattern in content_text.lower()
    )

    # Only flag if there's a very high ratio of auth mentions to actual content
    if auth_mentions >= 5 and word_count < 150:
        logger.debug(f"High auth mention ratio: {auth_mentions} mentions in {word_count} words")
        return ValidationResult(
            is_valid=False, reason="High ratio of authentication prompts to content", detected_pattern="high_auth_ratio"
        )

    # Content appears valid
    logger.debug(f"Content validation passed: {word_count} words, {auth_mentions} auth mentions")
    return ValidationResult(is_valid=True)
