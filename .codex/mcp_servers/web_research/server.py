"""
Web Research MCP Server for Codex.
Provides web search and content fetching capabilities (WebFetch equivalent).
"""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Dict, Optional, Any
from urllib.parse import urlparse

import requests
from mcp.server.fastmcp import FastMCP

# Import base utilities
from ..base import AmplifierMCPServer, success_response, error_response

# Try to import beautifulsoup4 for HTML parsing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Try to import duckduckgo-search
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class WebResearchServer(AmplifierMCPServer):
    """MCP server for web search and content fetching"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-web")

        # Initialize base server
        super().__init__("web_research", mcp)

        # Setup cache directory
        self.cache_dir = Path(__file__).parent.parent / "web_cache"
        self.cache_dir.mkdir(exist_ok=True)

        # Rate limiting: max 10 requests per minute
        self.rate_limit = 10
        self.rate_window = 60  # seconds
        self.requests = []

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
            """Search the web using DuckDuckGo (no API key required)

            Args:
                query: Search query string
                num_results: Maximum number of results to return (default: 5, max: 20)

            Returns:
                List of search results with titles, URLs, and snippets
            """
            try:
                self.logger.info(f"Searching web for: {query}")

                # Check rate limit
                if not self._check_rate_limit():
                    return error_response("Rate limit exceeded. Please wait before making more requests.")

                # Validate inputs
                if not query.strip():
                    return error_response("Query cannot be empty")

                num_results = min(max(1, num_results), 20)  # Clamp between 1-20

                # Check cache first
                cache_key = f"search_{hashlib.md5(query.encode()).hexdigest()}_{num_results}"
                cached = self._get_cache(cache_key)
                if cached:
                    self.logger.info("Returning cached search results")
                    return success_response(cached, {"cached": True})

                # Perform search
                if not DDGS_AVAILABLE:
                    return error_response("DuckDuckGo search library not available. Please install duckduckgo-search.")

                results = []
                try:
                    with DDGS() as ddgs:
                        search_results = list(ddgs.text(
                            query,
                            region="us-en",
                            safesearch="moderate",
                            max_results=num_results
                        ))

                        for result in search_results:
                            results.append({
                                "title": result.get("title", ""),
                                "url": result.get("href", ""),
                                "snippet": result.get("body", "")
                            })

                except Exception as e:
                    self.logger.error(f"DuckDuckGo search failed: {e}")
                    return error_response(f"Search failed: {str(e)}")

                # Cache results for 1 hour
                self._set_cache(cache_key, results, ttl=3600)

                self.logger.info(f"Found {len(results)} search results")
                return success_response(results, {"cached": False, "query": query})

            except Exception as e:
                self.logger.exception("search_web failed", e)
                return error_response(f"Web search failed: {str(e)}")

        @self.mcp.tool()
        async def fetch_url(url: str, extract_text: bool = True) -> Dict[str, Any]:
            """Fetch content from a URL

            Args:
                url: URL to fetch
                extract_text: Whether to extract readable text from HTML (default: True)

            Returns:
                Fetched content with metadata
            """
            try:
                self.logger.info(f"Fetching URL: {url}")

                # Check rate limit
                if not self._check_rate_limit():
                    return error_response("Rate limit exceeded. Please wait before making more requests.")

                # Validate URL
                if not url.strip():
                    return error_response("URL cannot be empty")

                try:
                    parsed = urlparse(url)
                    if not parsed.scheme or not parsed.netloc:
                        return error_response("Invalid URL format")
                except Exception:
                    return error_response("Invalid URL")

                # Check cache first
                cache_key = f"url_{hashlib.md5(url.encode()).hexdigest()}_{extract_text}"
                cached = self._get_cache(cache_key)
                if cached:
                    self.logger.info("Returning cached URL content")
                    return success_response(cached, {"cached": True})

                # Fetch content
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (compatible; AmplifierWebResearch/1.0)"
                    }

                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()

                    content = response.text
                    content_type = response.headers.get('content-type', '').lower()

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"HTTP request failed: {e}")
                    return error_response(f"Failed to fetch URL: {str(e)}")

                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": len(content)
                }

                # Extract text if requested and it's HTML
                if extract_text and 'text/html' in content_type:
                    extracted_text = self._extract_text(content)
                    result["text_content"] = extracted_text
                    result["text_length"] = len(extracted_text)
                else:
                    result["content"] = content[:10000]  # Limit raw content

                # Cache results for 1 hour
                self._set_cache(cache_key, result, ttl=3600)

                self.logger.info(f"Successfully fetched URL: {len(content)} chars")
                return success_response(result, {"cached": False})

            except Exception as e:
                self.logger.exception("fetch_url failed", e)
                return error_response(f"URL fetch failed: {str(e)}")

        @self.mcp.tool()
        async def summarize_content(content: str, max_length: int = 500) -> Dict[str, Any]:
            """Summarize text content by extracting key sentences

            Args:
                content: Text content to summarize
                max_length: Maximum length of summary in characters (default: 500)

            Returns:
                Summarized content
            """
            try:
                self.logger.info(f"Summarizing content: {len(content)} chars")

                if not content.strip():
                    return error_response("Content cannot be empty")

                # Simple extractive summarization
                summary = self._extract_summary(content, max_length)

                result = {
                    "original_length": len(content),
                    "summary_length": len(summary),
                    "summary": summary
                }

                self.logger.info(f"Generated summary: {len(summary)} chars")
                return success_response(result)

            except Exception as e:
                self.logger.exception("summarize_content failed", e)
                return error_response(f"Summarization failed: {str(e)}")

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()

        # Remove old requests outside the window
        self.requests = [req for req in self.requests if now - req < self.rate_window]

        # Check if we can make another request
        if len(self.requests) >= self.rate_limit:
            return False

        # Add this request
        self.requests.append(now)
        return True

    def _extract_text(self, html_content: str) -> str:
        """Extract readable text from HTML"""
        if BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)

                return text

            except Exception as e:
                self.logger.warning(f"BeautifulSoup extraction failed: {e}")
                # Fall back to simple method

        # Simple fallback: remove HTML tags with regex
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_summary(self, content: str, max_length: int) -> str:
        """Simple extractive summarization"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return content[:max_length]

        # Score sentences by length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = len(sentence.split())  # Word count
            if i < 3:  # Boost early sentences
                score *= 1.5
            scored_sentences.append((score, sentence))

        # Sort by score and take top sentences
        scored_sentences.sort(reverse=True)

        summary = ""
        for _, sentence in scored_sentences:
            if len(summary) + len(sentence) + 1 <= max_length:
                summary += sentence + ". "
            else:
                break

        return summary.strip()

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        try:
            cache_file = self.cache_dir / f"{key}.json"
            if not cache_file.exists():
                return None

            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Check TTL
            if time.time() > data.get('expires', 0):
                cache_file.unlink()  # Remove expired cache
                return None

            return data['value']

        except Exception as e:
            self.logger.warning(f"Cache read failed: {e}")
            return None

    def _set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set item in cache"""
        try:
            cache_file = self.cache_dir / f"{key}.json"

            data = {
                'value': value,
                'expires': time.time() + ttl,
                'created': time.time()
            }

            with open(cache_file, 'w') as f:
                json.dump(data, f, default=str)

        except Exception as e:
            self.logger.warning(f"Cache write failed: {e}")


# Create and run server
if __name__ == "__main__":
    server = WebResearchServer()
    server.run()