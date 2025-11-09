"""Format recipe data as markdown with YAML frontmatter."""

import logging
import re

from scenarios.recipe_extractor.converter import scale_ingredients
from scenarios.recipe_extractor.models import Ingredient
from scenarios.recipe_extractor.models import RecipeData

logger = logging.getLogger(__name__)


def create_slug(title: str) -> str:
    """Create URL-friendly slug from recipe title.

    Args:
        title: Recipe title

    Returns:
        Lowercase slug with hyphens

    Example:
        "Best Chocolate Chip Cookies" → "best-chocolate-chip-cookies"
    """
    # Convert to lowercase
    slug = title.lower()

    # Replace spaces and special characters with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)

    return slug


def _format_ingredient(ingredient: Ingredient) -> str:
    """Format a single ingredient for display.

    Args:
        ingredient: Ingredient to format

    Returns:
        Formatted ingredient string
    """
    parts = []

    # Add quantity and unit if present
    if ingredient.quantity is not None and ingredient.unit is not None:
        parts.append(f"{ingredient.quantity} {ingredient.unit}")

    # Add metric conversion if present
    if ingredient.metric_quantity is not None and ingredient.metric_unit is not None:
        parts.append(f"({ingredient.metric_quantity}{ingredient.metric_unit})")

    # Add item name
    parts.append(ingredient.item)

    return " ".join(parts)


def _calculate_scaled_servings(servings: str | None, multiplier: float) -> str:
    """Calculate scaled servings.

    Args:
        servings: Original servings string (e.g., "24 cookies", "4 servings")
        multiplier: Scale factor

    Returns:
        Scaled servings string
    """
    if not servings:
        return ""

    # Try to extract number from servings
    match = re.search(r"(\d+)", servings)
    if match:
        original_count = int(match.group(1))
        scaled_count = int(original_count * multiplier)
        # Replace the number in the original string
        scaled_servings = servings.replace(str(original_count), str(scaled_count), 1)
        return scaled_servings

    # If we can't parse, just return the original with multiplier note
    return f"{servings} (×{multiplier:.0f})"


def generate_markdown(recipe: RecipeData, scales: list[float] | None = None) -> str:
    """Generate markdown with frontmatter and scaled ingredient sections.

    Args:
        recipe: Recipe data to format
        scales: List of multipliers for ingredient sections (default: [1, 2, 3])

    Returns:
        Complete markdown string with YAML frontmatter
    """
    if scales is None:
        scales = [1.0, 2.0, 3.0]

    logger.info(f"Generating markdown for: {recipe.title}")

    lines = []

    # YAML frontmatter
    lines.append("---")
    lines.append(f"title: {recipe.title}")
    lines.append(f"source_url: {recipe.source_url}")
    lines.append(f"fetched_date: {recipe.fetched_date}")

    if recipe.tags:
        tags_str = ", ".join(recipe.tags)
        lines.append(f"tags: [{tags_str}]")

    if recipe.prep_time:
        lines.append(f"prep_time: {recipe.prep_time}")

    if recipe.cook_time:
        lines.append(f"cook_time: {recipe.cook_time}")

    if recipe.total_time:
        lines.append(f"total_time: {recipe.total_time}")

    if recipe.servings:
        lines.append(f"servings: {recipe.servings}")

    if recipe.description:
        # Escape quotes in description
        description = recipe.description.replace('"', '\\"')
        lines.append(f'description: "{description}"')

    if recipe.image_url:
        lines.append(f"image_url: {recipe.image_url}")

    lines.append("---")
    lines.append("")

    # Title as H1
    lines.append(f"# {recipe.title}")
    lines.append("")

    # Description if present
    if recipe.description:
        lines.append(recipe.description)
        lines.append("")

    # Metadata section
    metadata = []
    if recipe.prep_time:
        metadata.append(f"**Prep time:** {recipe.prep_time}")
    if recipe.cook_time:
        metadata.append(f"**Cook time:** {recipe.cook_time}")
    if recipe.total_time:
        metadata.append(f"**Total time:** {recipe.total_time}")
    if recipe.servings:
        metadata.append(f"**Servings:** {recipe.servings}")

    if metadata:
        lines.extend(metadata)
        lines.append("")

    # Ingredients section with scaled subsections
    lines.append("## Ingredients")
    lines.append("")

    for scale in scales:
        # Section header with scaled servings
        if scale == 1.0:
            header = "### 1×"
        else:
            header = f"### {scale:.0f}×"

        if recipe.servings:
            scaled_servings = _calculate_scaled_servings(recipe.servings, scale)
            header += f" ({scaled_servings})"

        lines.append(header)
        lines.append("")

        # Scale ingredients if needed
        if scale == 1.0:
            scaled_ingredients = recipe.ingredients
        else:
            scaled_ingredients = scale_ingredients(recipe.ingredients, scale)

        # Format each ingredient
        for ingredient in scaled_ingredients:
            formatted = _format_ingredient(ingredient)
            lines.append(f"- {formatted}")

        lines.append("")

    # Instructions section
    lines.append("## Instructions")
    lines.append("")

    for i, instruction in enumerate(recipe.instructions, start=1):
        lines.append(f"{i}. {instruction}")

    lines.append("")

    # Source link
    lines.append("---")
    lines.append("")
    lines.append(f"*Source: [{recipe.source_url}]({recipe.source_url})*")
    lines.append("")

    markdown = "\n".join(lines)
    logger.info(f"Generated {len(lines)} lines of markdown")

    return markdown
