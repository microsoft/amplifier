"""
Web Research MCP Server for Codex.
Provides web search and content fetching capabilities (WebFetch equivalent).
Enables searching the web, fetching URLs, and summarizing content.
"""

import hashlib
import json
import time
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP

from ..base import AmplifierMCPServer

# Import base utilities
from ..base import error_response
from ..base import success_response

# Capability flags - set based on import success
DDGS_AVAILABLE = False
REQUESTS_AVAILABLE = False
BS4_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    pass

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    pass

try:
    from duckduckgo_search import DDGS

    DDGS_AVAILABLE = True
except ImportError:
    pass


class WebCache:
    """Simple file-based cache for web content."""

    def __init__(self, cache_dir: Path, ttl_seconds: int = 24 * 3600):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        """Generate cache key from string."""
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get cached data if it exists and is not expired."""
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                cached = json.load(f)

            # Check expiration
            cached_at = cached.get("timestamp", 0)
            age = time.time() - cached_at

            if age > self.ttl_seconds:
                cache_file.unlink()  # Clean up expired cache
                return None

            return cached.get("content")

        except Exception:
            # Clean up corrupted cache
            if cache_file.exists():
                cache_file.unlink()
            return None

    def set(self, key: str, data: Any):
        """Store data in cache."""
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            cached = {"timestamp": time.time(), "content": data}
            with open(cache_file, "w") as f:
                json.dump(cached, f, indent=2)
        except Exception:
            pass  # Fail silently on cache write errors

    def clear(self, max_age_seconds: int | None = None):
        """Clear cache files."""
        cleared = 0
        now = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            should_delete = False

            if max_age_seconds is None:
                should_delete = True
            else:
                try:
                    with open(cache_file) as f:
                        cached = json.load(f)
                        age = now - cached.get("timestamp", 0)
                        if age > max_age_seconds:
                            should_delete = True
                except Exception:
                    should_delete = True

            if should_delete:
                cache_file.unlink()
                cleared += 1

        return cleared


class RateLimiter:
    """Simple rate limiter for web requests."""

    def __init__(self, min_interval_seconds: float = 1.0):
        self.min_interval_seconds = min_interval_seconds
        self.last_request_time: dict[str, float] = {}

    def wait(self, domain: str):
        """Wait if necessary to enforce rate limit."""
        now = time.time()
        last_time = self.last_request_time.get(domain, 0)
        elapsed = now - last_time

        if elapsed < self.min_interval_seconds:
            sleep_time = self.min_interval_seconds - elapsed
            time.sleep(sleep_time)

        self.last_request_time[domain] = time.time()


class TextSummarizer:
    """Simple text summarization (truncation-based)."""

    def summarize(self, content: str, max_length: int = 500) -> dict[str, Any]:
        """Summarize content by truncation."""
        if len(content) <= max_length:
            return {
                "summary": content,
                "original_length": len(content),
                "summary_length": len(content),
                "truncated": False,
                "max_length_requested": max_length,
            }

        summary = content[:max_length] + "..."
        return {
            "summary": summary,
            "original_length": len(content),
            "summary_length": len(summary),
            "truncated": True,
            "max_length_requested": max_length,
        }


# Module-level instances (will be initialized by WebResearchServer)
cache: WebCache | None = None
rate_limiter: RateLimiter | None = None
summarizer: TextSummarizer | None = None


class WebResearchServer(AmplifierMCPServer):
    """MCP server for web research and content fetching"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-web")

        # Initialize base server
        super().__init__("web_research", mcp)

        # Read config from [mcp_server_config.web_research]
        config = self.get_server_config()
        self.cache_enabled = config.get("cache_enabled", True)
        cache_ttl_hours = config.get("cache_ttl_hours", 24)
        self.max_results = config.get("max_results", 10)
        self.min_request_interval = config.get("min_request_interval", 1.0)

        # Set up cache
        project_root = Path(__file__).parent.parent.parent.parent
        cache_dir = project_root / ".codex" / "web_cache"

        # Create module-level instances
        global cache, rate_limiter, summarizer
        cache = WebCache(cache_dir, ttl_seconds=int(cache_ttl_hours * 3600))
        rate_limiter = RateLimiter(min_interval_seconds=self.min_request_interval)
        summarizer = TextSummarizer()

        self.cache = cache
        self.rate_limiter = rate_limiter
        self.summarizer = summarizer

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def search_web(query: str, num_results: int = 5, use_cache: bool = True) -> dict[str, Any]:
            """Search the web using DuckDuckGo

            Args:
                query: Search query string
                num_results: Maximum number of results to return (default 5)
                use_cache: Use cached results if available (default True)

            Returns:
                Search results with query metadata
            """
            try:
                self.logger.info(f"Searching web for: {query}")

                # Clamp num_results to configured max
                num_results = min(num_results, self.max_results)

                # Create cache key
                cache_key = f"search:{query}:{num_results}"

                # Check cache if enabled
                if use_cache and self.cache_enabled:
                    cached = self.cache.get(cache_key)
                    if cached:
                        return success_response(
                            {"query": query, "results": cached},
                            {"from_cache": True, "requested_results": num_results, "clamped": num_results < num_results},
                        )

                # Check if requests is available
                if not REQUESTS_AVAILABLE:
                    return error_response("requests library not available", {"install_command": "uv add requests"})

                # Rate limit
                self.rate_limiter.wait("duckduckgo.com")

                # Search DuckDuckGo
                search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                headers = {"User-Agent": "Mozilla/5.0 (compatible; Codex Web Research/1.0)"}

                import requests

                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status()

                # Parse results
                results = []

                if BS4_AVAILABLE:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(response.text, "html.parser")
                    for result_div in soup.find_all("div", class_="result")[:num_results]:
                        title_elem = result_div.find("a", class_="result__a")
                        snippet_elem = result_div.find("a", class_="result__snippet")

                        if title_elem:
                            results.append(
                                {
                                    "title": title_elem.get_text(strip=True),
                                    "url": title_elem.get("href", ""),
                                    "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                                }
                            )
                else:
                    # Fallback without BeautifulSoup
                    results.append(
                        {
                            "title": "Search completed (limited parsing)",
                            "url": search_url,
                            "snippet": f"Search for '{query}'. Install beautifulsoup4 for better parsing: uv add beautifulsoup4",
                        }
                    )

                # Cache results if enabled
                if self.cache_enabled:
                    self.cache.set(cache_key, results)

                self.logger.info(f"Found {len(results)} search results")
                return success_response(
                    {"query": query, "results": results},
                    {"result_count": len(results), "from_cache": False, "bs4_available": BS4_AVAILABLE},
                )

            except Exception as e:
                self.logger.exception("search_web failed", e)
                return error_response(f"Web search failed: {str(e)}")

        @self.mcp.tool()
        async def fetch_url(url: str, extract_text: bool = True, use_cache: bool = True) -> dict[str, Any]:
            """Fetch content from a URL

            Args:
                url: URL to fetch
                extract_text: Extract text from HTML (default True)
                use_cache: Use cached content if available (default True)

            Returns:
                URL content with status and metadata
            """
            try:
                self.logger.info(f"Fetching URL: {url}")

                # Validate URL
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    return error_response("Invalid URL format", {"url": url})

                # Create cache key
                cache_key = f"fetch:{url}:{extract_text}"

                # Check cache if enabled
                if use_cache and self.cache_enabled:
                    cached = self.cache.get(cache_key)
                    if cached:
                        return success_response(cached, {"from_cache": True})

                # Check if requests is available
                if not REQUESTS_AVAILABLE:
                    return error_response("requests library not available", {"install_command": "uv add requests"})

                # Rate limit
                self.rate_limiter.wait(parsed.netloc)

                # Fetch URL
                import requests

                headers = {"User-Agent": "Mozilla/5.0 (compatible; Codex Web Research/1.0)"}
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                content = response.text
                content_type = response.headers.get("Content-Type", "")
                status_code = response.status_code

                # Extract text if requested and content is HTML
                extracted_text = None
                if extract_text and "html" in content_type.lower():
                    if BS4_AVAILABLE:
                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(content, "html.parser")

                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()

                        # Get text
                        extracted_text = soup.get_text(separator="\n", strip=True)

                        # Clean up whitespace
                        lines = (line.strip() for line in extracted_text.splitlines())
                        extracted_text = "\n".join(line for line in lines if line)
                    else:
                        self.logger.warning("beautifulsoup4 not available - cannot extract text")

                result = {
                    "url": url,
                    "status_code": status_code,
                    "content_type": content_type,
                    "content": content if not extract_text else None,
                    "extracted_text": extracted_text,
                }

                # Cache result if enabled
                if self.cache_enabled:
                    self.cache.set(cache_key, result)

                self.logger.info(f"Fetched {len(content)} bytes from {url}")
                return success_response(
                    result, {"content_length": len(content), "from_cache": False, "bs4_available": BS4_AVAILABLE}
                )

            except Exception as e:
                self.logger.exception("fetch_url failed", e)
                return error_response(f"Failed to fetch URL: {str(e)}")

        @self.mcp.tool()
        async def summarize_content(content: str, max_length: int = 500) -> dict[str, Any]:
            """Summarize text content (simple truncation)

            Args:
                content: Text content to summarize
                max_length: Maximum length of summary (default 500)

            Returns:
                Summary with length metadata
            """
            try:
                self.logger.info(f"Summarizing content of length {len(content)}")

                # Use summarizer instance
                result = self.summarizer.summarize(content, max_length)

                self.logger.info(f"Summary: {result['summary_length']} chars (truncated: {result['truncated']})")
                return success_response(result)

            except Exception as e:
                self.logger.exception("summarize_content failed", e)
                return error_response(f"Failed to summarize content: {str(e)}")

        @self.mcp.tool()
        async def clear_cache(max_age_days: int | None = None) -> dict[str, Any]:
            """Clear web research cache

            Args:
                max_age_days: Only clear cache older than this many days (optional)

            Returns:
                Cache clear results
            """
            try:
                self.logger.info(f"Clearing cache (max_age_days={max_age_days})")

                # Convert days to seconds if provided
                max_age_seconds = max_age_days * 24 * 3600 if max_age_days is not None else None

                # Use cache instance to clear
                cleared_count = self.cache.clear(max_age_seconds)

                self.logger.info(f"Cleared {cleared_count} cache files")
                return success_response({"cleared_count": cleared_count, "max_age_days": max_age_days})

            except Exception as e:
                self.logger.exception("clear_cache failed", e)
                return error_response(f"Failed to clear cache: {str(e)}")


# Create and run server
if __name__ == "__main__":
    server = WebResearchServer()
    server.run()
