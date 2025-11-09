"""Fetch recipe data from URLs using recipe-scrapers library."""

import logging
from datetime import datetime

from recipe_scrapers import scrape_me
from recipe_scrapers._exceptions import WebsiteNotImplementedError

from scenarios.recipe_extractor.models import Ingredient
from scenarios.recipe_extractor.models import RecipeData

logger = logging.getLogger(__name__)


def fetch_recipe(url: str) -> RecipeData:
    """Fetch recipe from URL using recipe-scrapers.

    Args:
        url: Recipe URL

    Returns:
        Structured recipe data

    Raises:
        ValueError: If URL not supported or fetch fails
    """
    try:
        # Use recipe-scrapers to fetch the recipe
        logger.info(f"Fetching recipe from: {url}")
        scraper = scrape_me(url)

        # Log which site/scraper is being used
        logger.info(f"Using scraper: {scraper.__class__.__name__}")

        # Extract all available fields
        title = scraper.title()
        ingredients_raw = scraper.ingredients()
        instructions = scraper.instructions_list()

        # Parse ingredients into Ingredient objects
        ingredients = []
        for raw_text in ingredients_raw:
            # Basic parsing - just store raw text and item name for now
            # More sophisticated parsing happens in converter.py
            ingredient = Ingredient(
                raw_text=raw_text,
                item=raw_text,  # For now, item is the full raw text
            )
            ingredients.append(ingredient)

        # Extract optional metadata
        try:
            prep_time = scraper.prep_time()
        except Exception:
            prep_time = None

        try:
            cook_time = scraper.cook_time()
        except Exception:
            cook_time = None

        try:
            total_time = scraper.total_time()
        except Exception:
            total_time = None

        try:
            yields = scraper.yields()
        except Exception:
            yields = None

        try:
            description = scraper.description()
        except Exception:
            description = None

        try:
            image_url = scraper.image()
        except Exception:
            image_url = None

        # Build RecipeData object
        recipe = RecipeData(
            title=title,
            source_url=url,
            fetched_date=datetime.now().strftime("%Y-%m-%d"),
            ingredients=ingredients,
            instructions=instructions,
            prep_time=str(prep_time) if prep_time else None,
            cook_time=str(cook_time) if cook_time else None,
            total_time=str(total_time) if total_time else None,
            servings=str(yields) if yields else None,
            description=description,
            tags=[],  # Tags will be added in future enhancements
            image_url=image_url,
        )

        logger.info(f"Successfully fetched recipe: {title}")
        return recipe

    except WebsiteNotImplementedError as e:
        logger.error(f"Site not supported: {url}")
        raise ValueError(f"Site not supported by recipe-scrapers: {url}") from e

    except Exception as e:
        logger.error(f"Failed to fetch recipe from {url}: {str(e)}")
        raise ValueError(f"Failed to fetch recipe from {url}: {str(e)}") from e
