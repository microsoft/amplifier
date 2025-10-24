from typing import List, Dict, Tuple, Optional
"""URL processor for fetching and analyzing web content."""

import logging
import time
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession

from ..core.processor import BaseProcessor
from ..models import ContentItem, ContentType, ProcessingResult, ProcessingStatus, ProcessorConfig

logger = logging.getLogger(__name__)


class URLProcessor(BaseProcessor):
    """Processes URL content for design reference and inspiration.

    Handles:
    - Design inspiration sites (Dribbble, Behance, etc.)
    - Documentation and reference links
    - Design system examples
    - Product websites and landing pages
    """

    ANALYSIS_PROMPT = """Analyze this web content in the context of a design discovery session.

URL: {url}
Title: {title}

Content:
{content}

Focus on:
1. **Purpose**: What is this page/site trying to achieve?
2. **Design Patterns**: Notable UI patterns, layouts, or interactions
3. **Visual Style**: Overall aesthetic and design language
4. **User Experience**: How the content is organized and presented
5. **Relevance**: How this relates to design work or inspiration
6. **Key Takeaways**: Specific ideas or approaches worth noting

Provide insights that help understand why this URL was saved and what can be learned from it."""

    async def can_process(self, item: ContentItem) -> bool:
        """Check if this processor can handle the content item.

        Args:
            item: Content item to check

        Returns:
            True if item is a valid URL
        """
        if item.type != ContentType.URL:
            return False

        return self._is_url(item)

    async def process(self, item: ContentItem, config: Optional[ProcessorConfig] = None) -> ProcessingResult:
        """Process a URL by fetching and analyzing its content.

        Args:
            item: Content item to process
            config: Processor configuration (uses instance config if not provided)

        Returns:
            Processing result with content analysis
        """
        config = config or self.config
        start_time = time.time()

        try:
            url = item.source_path

            logger.info(f"Fetching URL: {url}")
            html_content, page_title = await self._fetch_url(url, config)

            if not html_content:
                return ProcessingResult(
                    content_id=item.id,
                    status=ProcessingStatus.FAILED,
                    error_message="Failed to fetch URL content",
                )

            # Extract text content
            text_content = self._extract_text(html_content)

            logger.info(f"Analyzing URL content with AI: {url}")
            analysis = await self._analyze_content(url, page_title, text_content, config)

            insights = self._extract_insights(analysis)
            design_elements = self._extract_design_elements(html_content, analysis)

            processing_time = int((time.time() - start_time) * 1000)

            return ProcessingResult(
                content_id=item.id,
                status=ProcessingStatus.COMPLETED,
                analysis=analysis,
                extracted_text=text_content[:1000],  # First 1000 chars
                insights=insights,
                design_elements=design_elements,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Error processing URL {item.source_path}: {e}", exc_info=True)
            return ProcessingResult(
                content_id=item.id,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _fetch_url(self, url: str, config: ProcessorConfig) -> Tuple[str, str]:
        """Fetch URL content.

        Args:
            url: URL to fetch
            config: Processor configuration

        Returns:
            Tuple of (html_content, page_title)
        """
        try:
            async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                    follow_redirects=True,
                )

                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Get page title
                title_tag = soup.find("title")
                page_title = title_tag.get_text(strip=True) if title_tag else urlparse(url).netloc

                return response.text, page_title

        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return "", ""

    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text content
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)

            # Limit length
            return text[:5000]  # First 5000 chars

        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return ""

    async def _analyze_content(self, url: str, title: str, content: str, config: ProcessorConfig) -> str:
        """Analyze URL content using Claude.

        Args:
            url: Original URL
            title: Page title
            content: Extracted text content
            config: Processor configuration

        Returns:
            Analysis text from Claude
        """
        try:
            session_options = SessionOptions(
                system_prompt="You are a design research expert analyzing web content for design insights.",
                max_turns=1,
                retry_attempts=3,
                stream_output=False,
            )

            prompt = self.ANALYSIS_PROMPT.format(url=url, title=title, content=content[:3000])  # Limit context

            async with ClaudeSession(options=session_options) as session:
                response = await session.query(prompt)

                if response.success:
                    return response.content
                else:
                    logger.error(f"Analysis error: {response.error}")
                    return f"Content from {title}: {content[:500]}"

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return f"Content from {title}: {content[:500]}"

    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract key insights from analysis.

        Args:
            analysis: Raw analysis text

        Returns:
            List of extracted insights
        """
        insights = []
        lines = analysis.split("\n")

        for line in lines:
            line = line.strip()
            if (
                line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))
                or line.startswith(("- ", "• ", "* "))
            ):
                cleaned = line.lstrip("0123456789.-•* ").strip()
                if cleaned and len(cleaned) > 10:
                    insights.append(cleaned)

        return insights[:10]

    def _extract_design_elements(self, html: str, analysis: str) -> dict:
        """Extract design elements from HTML and analysis.

        Args:
            html: Raw HTML content
            analysis: Claude analysis text

        Returns:
            Dictionary of design elements
        """
        elements = {}

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Count semantic elements
            elements["has_semantic_html"] = bool(soup.find(["article", "section", "nav", "main"]))
            elements["image_count"] = len(soup.find_all("img"))
            elements["link_count"] = len(soup.find_all("a"))

            # Check for design patterns mentioned in analysis
            lower_analysis = analysis.lower()
            if "component" in lower_analysis or "pattern" in lower_analysis:
                elements["has_design_patterns"] = True

            if "responsive" in lower_analysis or "mobile" in lower_analysis:
                elements["mentions_responsive"] = True

        except Exception as e:
            logger.error(f"Error extracting design elements: {e}")

        return elements

    def get_supported_types(self) -> List[str]:
        """Get supported content types.

        Returns:
            List containing 'url' type
        """
        return ["url", "text/html"]
