"""Data models for recipe extraction."""

from pydantic import BaseModel


class Ingredient(BaseModel):
    """Single ingredient with parsing and conversion support."""

    raw_text: str  # "2 cups all-purpose flour"
    quantity: float | None = None  # 2.0
    unit: str | None = None  # "cups"
    item: str  # "all-purpose flour"
    metric_quantity: float | None = None  # 280.0
    metric_unit: str | None = None  # "g"


class RecipeData(BaseModel):
    """Complete recipe data structure."""

    title: str
    source_url: str
    fetched_date: str
    ingredients: list[Ingredient]
    instructions: list[str]
    prep_time: str | None = None
    cook_time: str | None = None
    total_time: str | None = None
    servings: str | None = None
    description: str | None = None
    tags: list[str] = []
    image_url: str | None = None
