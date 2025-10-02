"""
Article Illustrator Module

Generates AI illustrations for markdown articles with multiple stages:
1. Content analysis to find illustration opportunities
2. Prompt generation for consistent style
3. Multi-API image generation
4. Markdown update with image insertion
"""

from .content_analysis import ContentAnalyzer
from .image_generation import ImageGenerator
from .main import ArticleIllustratorPipeline
from .main import illustrate
from .markdown_update import MarkdownUpdater
from .models import GeneratedImage
from .models import IllustrationPoint
from .models import ImageAlternatives
from .models import ImagePrompt
from .models import SessionState
from .prompt_generation import PromptGenerator
from .state import SessionManager

__all__ = [
    # Main pipeline
    "ArticleIllustratorPipeline",
    "illustrate",
    # Stage modules
    "ContentAnalyzer",
    "PromptGenerator",
    "ImageGenerator",
    "MarkdownUpdater",
    # State management
    "SessionManager",
    "SessionState",
    # Data models
    "IllustrationPoint",
    "ImagePrompt",
    "GeneratedImage",
    "ImageAlternatives",
]
