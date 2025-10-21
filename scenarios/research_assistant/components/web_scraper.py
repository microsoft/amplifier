"""Web scraping utilities for research assistant."""

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Content scraped from a web page."""

    url: str
    title: str
    text: str
    error: str | None = None
    success: bool = True


class WebScraper:
    """Simple HTTP-based web scraper."""

    def __init__(self: "WebScraper", timeout: int = 30) -> None:
        """Initialize web scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ResearchAssistant/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def scrape_url(self: "WebScraper", url: str) -> ScrapedContent:
        """Scrape content from a URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedContent with extracted text or error
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extract title
                if soup.title and soup.title.string:
                    title = str(soup.title.string)
                else:
                    title = urlparse(url).netloc

                # Extract text from main content areas
                # Try to find main content first
                main_content = (
                    soup.find("main")
                    or soup.find("article")
                    or soup.find("div", {"class": ["content", "main-content", "article-body"]})
                    or soup.find("body")
                )

                if main_content:
                    text = main_content.get_text(separator="\n", strip=True)
                else:
                    text = soup.get_text(separator="\n", strip=True)

                # Clean up excessive whitespace
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                text = "\n".join(lines)

                # Limit text length to avoid massive documents
                max_chars = 50000
                if len(text) > max_chars:
                    text = text[:max_chars] + "\n\n[Content truncated]"

                return ScrapedContent(url=url, title=title, text=text)

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
            logger.warning(f"Failed to scrape {url}: {error_msg}")
            return ScrapedContent(url=url, title="", text="", error=error_msg, success=False)

        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.warning(f"Failed to scrape {url}: {error_msg}")
            return ScrapedContent(url=url, title="", text="", error=error_msg, success=False)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to scrape {url}: {error_msg}", exc_info=True)
            return ScrapedContent(url=url, title="", text="", error=error_msg, success=False)

    def is_valid_url(self: "WebScraper", url: str) -> bool:
        """Check if a URL is valid and accessible.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ["http", "https"], result.netloc])
        except Exception:
            return False
