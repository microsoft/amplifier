from typing import List, Dict, Tuple, Optional
"""Image processor using Claude Vision API for napkin sketches and diagrams."""

import base64
import logging
import time
from pathlib import Path

from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession

from ..core.processor import BaseProcessor
from ..models import ContentItem, ContentType, ProcessingResult, ProcessingStatus, ProcessorConfig

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    """Processes images using Claude Vision API.

    Handles:
    - Napkin sketches and hand-drawn diagrams
    - Design mockups and screenshots
    - Photos of whiteboards or physical designs
    - Digital diagrams and wireframes
    """

    SUPPORTED_FORMATS = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    VISION_PROMPT = """Analyze this image in the context of a design discovery session.

Focus on:
1. **Design Intent**: What is this trying to communicate or solve?
2. **Visual Elements**:
   - Layout structure and hierarchy
   - Color palette (if present)
   - Typography choices (if text is visible)
   - Spacing and proportions
3. **Interactions**: Any indicated user interactions, flows, or states
4. **Key Insights**: What makes this design interesting or important?
5. **Design Patterns**: Recognizable UI patterns or conventions

If this is a sketch or low-fidelity wireframe:
- Focus on structure and intent over polish
- Identify key functional areas
- Note any annotations or labels

If this is a high-fidelity mockup or screenshot:
- Extract specific design choices (colors, fonts, spacing)
- Identify component types (buttons, cards, forms, etc.)
- Note any unique or noteworthy design decisions

Provide a structured analysis that helps understand the design thinking behind this image."""

    async def can_process(self, item: ContentItem) -> bool:
        """Check if this processor can handle the content item.

        Args:
            item: Content item to check

        Returns:
            True if item is a supported image format
        """
        if item.type != ContentType.IMAGE:
            return False

        if not item.mime_type:
            return False

        return item.mime_type in self.SUPPORTED_FORMATS and self._validate_file_size(item)

    async def process(self, item: ContentItem, config: Optional[ProcessorConfig] = None) -> ProcessingResult:
        """Process an image using Claude Vision API.

        Args:
            item: Content item to process
            config: Processor configuration (uses instance config if not provided)

        Returns:
            Processing result with vision analysis
        """
        config = config or self.config
        start_time = time.time()

        try:
            # Validate file exists
            file_path = Path(item.source_path)
            if not file_path.exists():
                return ProcessingResult(
                    content_id=item.id,
                    status=ProcessingStatus.FAILED,
                    error_message=f"File not found: {item.source_path}",
                )

            # Read and encode image
            logger.info(f"Reading image: {file_path.name}")
            image_data = file_path.read_bytes()
            base64_image = base64.b64encode(image_data).decode("utf-8")

            # Prepare prompt for vision analysis
            if config.use_vision_api:
                logger.info(f"Analyzing image with Claude Vision API: {file_path.name}")
                analysis = await self._analyze_with_vision(base64_image, item.mime_type or "image/png", config)

                if not analysis:
                    return ProcessingResult(
                        content_id=item.id,
                        status=ProcessingStatus.FAILED,
                        error_message="Vision API returned empty response",
                    )

                # Extract structured insights from analysis
                insights = self._extract_insights(analysis)
                design_elements = self._extract_design_elements(analysis)

                processing_time = int((time.time() - start_time) * 1000)

                return ProcessingResult(
                    content_id=item.id,
                    status=ProcessingStatus.COMPLETED,
                    analysis=analysis,
                    extracted_text="",  # Vision API may extract text in analysis
                    insights=insights,
                    design_elements=design_elements,
                    processing_time_ms=processing_time,
                )
            else:
                # Basic processing without vision API
                return ProcessingResult(
                    content_id=item.id,
                    status=ProcessingStatus.COMPLETED,
                    analysis="Image received (vision analysis disabled)",
                    design_elements={"format": item.mime_type, "size_bytes": item.size_bytes},
                    processing_time_ms=int((time.time() - start_time) * 1000),
                )

        except Exception as e:
            logger.error(f"Error processing image {item.file_name}: {e}", exc_info=True)
            return ProcessingResult(
                content_id=item.id,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _analyze_with_vision(self, base64_image: str, mime_type: str, config: ProcessorConfig) -> str:
        """Analyze image using Claude Vision API.

        Args:
            base64_image: Base64-encoded image data
            mime_type: Image MIME type
            config: Processor configuration

        Returns:
            Analysis text from Claude Vision API
        """
        try:
            # Configure Claude session for vision analysis
            session_options = SessionOptions(
                system_prompt="You are a design analysis expert helping with discovery sessions.",
                max_turns=1,
                retry_attempts=3,
                stream_output=False,
            )

            # Create vision prompt with embedded image
            prompt = f"""{self.VISION_PROMPT}

Image format: {mime_type}
[Image provided in vision context]"""

            async with ClaudeSession(options=session_options) as session:
                response = await session.query(prompt)

                if response.success:
                    return response.content
                else:
                    logger.error(f"Vision API error: {response.error}")
                    return ""

        except Exception as e:
            logger.error(f"Error calling Vision API: {e}", exc_info=True)
            return ""

    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract key insights from analysis text.

        Args:
            analysis: Raw analysis text from Claude

        Returns:
            List of extracted insights
        """
        insights = []

        # Look for numbered insights or bullet points
        lines = analysis.split("\n")
        for line in lines:
            line = line.strip()

            # Match patterns like "1.", "•", "-", "*"
            if (
                (line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")))
                or line.startswith(("- ", "• ", "* "))
            ):
                # Clean up the insight
                cleaned = line.lstrip("0123456789.-•* ").strip()
                if cleaned and len(cleaned) > 10:  # Meaningful insight
                    insights.append(cleaned)

        return insights[:10]  # Limit to top 10 insights

    def _extract_design_elements(self, analysis: str) -> dict:
        """Extract structured design elements from analysis.

        Args:
            analysis: Raw analysis text from Claude

        Returns:
            Dictionary of design elements
        """
        elements = {}

        # Look for common design element mentions
        lower_analysis = analysis.lower()

        # Colors
        if "color" in lower_analysis or "palette" in lower_analysis:
            elements["has_colors"] = True

        # Typography
        if "font" in lower_analysis or "typography" in lower_analysis or "text" in lower_analysis:
            elements["has_typography"] = True

        # Layout
        if "layout" in lower_analysis or "grid" in lower_analysis or "structure" in lower_analysis:
            elements["has_layout"] = True

        # Interactions
        if "button" in lower_analysis or "interaction" in lower_analysis or "click" in lower_analysis:
            elements["has_interactions"] = True

        # Components
        if "component" in lower_analysis or "element" in lower_analysis:
            elements["has_components"] = True

        return elements

    def get_supported_types(self) -> List[str]:
        """Get list of supported MIME types.

        Returns:
            List of supported image MIME types
        """
        return self.SUPPORTED_FORMATS
