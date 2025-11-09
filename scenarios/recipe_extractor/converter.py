"""Convert units and scale ingredients using pint library."""

import logging
import re
from copy import deepcopy

from pint import UnitRegistry

from scenarios.recipe_extractor.models import Ingredient

logger = logging.getLogger(__name__)

# Initialize pint unit registry with ingredient-specific conversions
ureg = UnitRegistry()

# Add ingredient-specific definitions (volume to weight)
# Based on common cooking conversions
ureg.define("cup_flour = 120 * gram")
ureg.define("cup_sugar = 200 * gram")
ureg.define("cup_brown_sugar = 220 * gram")
ureg.define("cup_butter = 227 * gram")
ureg.define("cup_oil = 220 * gram")
ureg.define("cup_milk = 240 * gram")
ureg.define("cup_water = 240 * gram")
ureg.define("tablespoon_generic = 15 * milliliter")
ureg.define("teaspoon_generic = 5 * milliliter")


def _parse_quantity_and_unit(raw_text: str) -> tuple[float | None, str | None]:
    """Parse quantity and unit from ingredient text.

    Args:
        raw_text: Raw ingredient text like "2 cups flour"

    Returns:
        Tuple of (quantity, unit) or (None, None) if parsing fails
    """
    # Common patterns:
    # "2 cups flour"
    # "1/2 cup sugar"
    # "2.5 tablespoons oil"
    # "1 1/2 cups milk"

    # Try to match: number (with optional fraction) + unit
    pattern = r"^(\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+)\s+([a-zA-Z]+)"
    match = re.match(pattern, raw_text.strip())

    if not match:
        return None, None

    quantity_str = match.group(1)
    unit = match.group(2).lower()

    # Parse quantity (handle fractions and mixed numbers)
    try:
        if "/" in quantity_str:
            # Handle "1/2" or "1 1/2"
            parts = quantity_str.strip().split()
            if len(parts) == 2:
                # Mixed number: "1 1/2"
                whole = float(parts[0])
                num, denom = parts[1].split("/")
                quantity = whole + float(num) / float(denom)
            else:
                # Simple fraction: "1/2"
                num, denom = quantity_str.split("/")
                quantity = float(num) / float(denom)
        else:
            quantity = float(quantity_str)

        return quantity, unit
    except (ValueError, ZeroDivisionError):
        return None, None


def convert_to_metric(ingredient: Ingredient) -> Ingredient:
    """Convert volume measurements to weight where possible.

    Args:
        ingredient: Ingredient with imperial/volume units

    Returns:
        Ingredient with metric_quantity and metric_unit populated

    Note:
        If conversion not possible, returns ingredient unchanged
        (metric fields remain None)
    """
    # If ingredient already has quantity and unit, use those
    # Otherwise, try to parse from raw_text
    if ingredient.quantity is None or ingredient.unit is None:
        quantity, unit = _parse_quantity_and_unit(ingredient.raw_text)
        if quantity is None or unit is None:
            logger.debug(f"Could not parse quantity/unit from: {ingredient.raw_text}")
            return ingredient
    else:
        quantity = ingredient.quantity
        unit = ingredient.unit

    # Try to identify ingredient type from item name for specialized conversions
    item_lower = ingredient.item.lower()
    ingredient_type = None

    if "flour" in item_lower:
        ingredient_type = "flour"
    elif "sugar" in item_lower and "brown" in item_lower:
        ingredient_type = "brown_sugar"
    elif "sugar" in item_lower:
        ingredient_type = "sugar"
    elif "butter" in item_lower:
        ingredient_type = "butter"
    elif "oil" in item_lower:
        ingredient_type = "oil"
    elif "milk" in item_lower:
        ingredient_type = "milk"
    elif "water" in item_lower:
        ingredient_type = "water"

    try:
        # Try ingredient-specific conversion first
        if ingredient_type and unit in ["cup", "cups"]:
            custom_unit = f"cup_{ingredient_type}"
            try:
                pint_quantity = quantity * ureg(custom_unit)
                # Convert to grams
                converted = pint_quantity.to(ureg.gram)
                metric_quantity = float(converted.magnitude)
                metric_unit = "g"

                # Update ingredient copy
                result = deepcopy(ingredient)
                result.quantity = quantity
                result.unit = unit
                result.metric_quantity = round(metric_quantity, 1)
                result.metric_unit = metric_unit

                logger.debug(
                    f"Converted {quantity} {unit} {ingredient_type} → {result.metric_quantity}{result.metric_unit}"
                )
                return result
            except Exception:
                pass  # Fall through to generic conversion

        # Generic conversion for standard units
        unit_map = {
            "cup": ureg.cup,
            "cups": ureg.cup,
            "tablespoon": ureg.tablespoon,
            "tablespoons": ureg.tablespoon,
            "tbsp": ureg.tablespoon,
            "teaspoon": ureg.teaspoon,
            "teaspoons": ureg.teaspoon,
            "tsp": ureg.teaspoon,
            "ounce": ureg.ounce,
            "ounces": ureg.ounce,
            "oz": ureg.ounce,
            "pound": ureg.pound,
            "pounds": ureg.pound,
            "lb": ureg.pound,
            "lbs": ureg.pound,
        }

        if unit in unit_map:
            pint_unit = unit_map[unit]
            pint_quantity = quantity * pint_unit

            # Try to convert to grams (for weight) or milliliters (for volume)
            try:
                # Try weight conversion first
                converted = pint_quantity.to(ureg.gram)
                metric_quantity = float(converted.magnitude)
                metric_unit = "g"
            except Exception:
                # Try volume conversion
                converted = pint_quantity.to(ureg.milliliter)
                metric_quantity = float(converted.magnitude)
                metric_unit = "ml"

            result = deepcopy(ingredient)
            result.quantity = quantity
            result.unit = unit
            result.metric_quantity = round(metric_quantity, 1)
            result.metric_unit = metric_unit

            logger.debug(f"Converted {quantity} {unit} → {result.metric_quantity}{result.metric_unit}")
            return result

    except Exception as e:
        logger.debug(f"Could not convert {quantity} {unit}: {str(e)}")

    # Return unchanged if conversion failed
    return ingredient


def scale_ingredients(ingredients: list[Ingredient], multiplier: float) -> list[Ingredient]:
    """Scale all ingredients by multiplier.

    Args:
        ingredients: Original ingredient list
        multiplier: Scale factor (2.0 for double, 3.0 for triple)

    Returns:
        New list with scaled quantities
    """
    scaled = []

    for ingredient in ingredients:
        # Create a copy
        scaled_ingredient = deepcopy(ingredient)

        # Scale quantity if present
        if scaled_ingredient.quantity is not None:
            scaled_ingredient.quantity = round(scaled_ingredient.quantity * multiplier, 2)

        # Scale metric_quantity if present
        if scaled_ingredient.metric_quantity is not None:
            scaled_ingredient.metric_quantity = round(scaled_ingredient.metric_quantity * multiplier, 1)

        scaled.append(scaled_ingredient)

    logger.debug(f"Scaled {len(ingredients)} ingredients by {multiplier}x")
    return scaled
