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


class WebResearchServer(AmplifierMCPServer):
    """MCP server for web research and content fetching"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-web")

        # Initialize base server
        super().__init__("web_research", mcp)

        # Set up cache
        self.cache_dir = Path(__file__).parent.parent.parent / "web_cache"
        self.cache_dir.mkdir(exist_ok=True)

        # Rate limiting state
        self.last_request_time = {}
        self.min_request_interval = 1.0  # Minimum seconds between requests

        # Register tools
        self._register_tools()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        return self.cache_dir / f"{cache_key}.json"

    def _get_cached(self, cache_key: str, max_age_hours: int = 24) -> dict[str, Any] | None:
        """Get cached data if it exists and is not expired"""
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                cached = json.load(f)

            # Check expiration
            cached_at = datetime.fromisoformat(cached["cached_at"])
            age = datetime.now() - cached_at

            if age > timedelta(hours=max_age_hours):
                self.logger.debug(f"Cache expired for {cache_key}")
                return None

            self.logger.debug(f"Cache hit for {cache_key}")
            return cached["data"]

        except Exception as e:
            self.logger.warning(f"Failed to read cache for {cache_key}: {e}")
            return None

    def _set_cached(self, cache_key: str, data: Any):
        """Store data in cache"""
        cache_path = self._get_cache_path(cache_key)

        try:
            cached = {"cached_at": datetime.now().isoformat(), "data": data}
            with open(cache_path, "w") as f:
                json.dump(cached, f, indent=2)

            self.logger.debug(f"Cached data for {cache_key}")

        except Exception as e:
            self.logger.warning(f"Failed to write cache for {cache_key}: {e}")

    def _rate_limit(self, domain: str):
        """Implement rate limiting per domain"""
        now = time.time()
        last_time = self.last_request_time.get(domain, 0)
        elapsed = now - last_time

        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
            time.sleep(sleep_time)

        self.last_request_time[domain] = time.time()

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
                List of search results with titles, URLs, and snippets
            """
            try:
                self.logger.info(f"Searching web for: {query}")

                # Create cache key
                cache_key = hashlib.md5(f"search:{query}:{num_results}".encode()).hexdigest()

                # Check cache
                if use_cache:
                    cached = self._get_cached(cache_key, max_age_hours=24)
                    if cached:
                        return success_response(cached, {"from_cache": True})

                # Import requests here to avoid dependency issues
                try:
                    import requests
                except ImportError:
                    return error_response("requests library not available", {"install_command": "uv add requests"})

                # Rate limit
                self._rate_limit("duckduckgo.com")

                # Search DuckDuckGo
                search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                headers = {"User-Agent": "Mozilla/5.0 (compatible; Codex Web Research/1.0)"}

                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status()

                # Parse results (simple HTML parsing without BeautifulSoup)
                results = []
                html = response.text

                # Simple extraction (this is basic - BeautifulSoup would be better)
                # For now, return a simplified result
                results.append(
                    {
                        "title": "Search completed",
                        "url": search_url,
                        "snippet": f"Search for '{query}' returned {num_results} results. Note: Full HTML parsing requires beautifulsoup4 library.",
                    }
                )

                # Try to import BeautifulSoup for better parsing
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, "html.parser")

                    results = []
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

                except ImportError:
                    self.logger.warning("beautifulsoup4 not available - using basic parsing")

                # Cache results
                self._set_cached(cache_key, results)

                self.logger.info(f"Found {len(results)} search results")
                return success_response(results, {"query": query, "result_count": len(results), "from_cache": False})

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
                Fetched content (raw HTML or extracted text)
            """
            try:
                self.logger.info(f"Fetching URL: {url}")

                # Validate URL
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    return error_response("Invalid URL format", {"url": url})

                # Create cache key
                cache_key = hashlib.md5(f"fetch:{url}:{extract_text}".encode()).hexdigest()

                # Check cache
                if use_cache:
                    cached = self._get_cached(cache_key, max_age_hours=24)
                    if cached:
                        return success_response(cached, {"from_cache": True})

                # Import requests
                try:
                    import requests
                except ImportError:
                    return error_response("requests library not available", {"install_command": "uv add requests"})

                # Rate limit
                self._rate_limit(parsed.netloc)

                # Fetch URL
                headers = {"User-Agent": "Mozilla/5.0 (compatible; Codex Web Research/1.0)"}
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                content = response.text
                content_type = response.headers.get("Content-Type", "")

                # Extract text if requested and content is HTML
                extracted_text = None
                if extract_text and "html" in content_type.lower():
                    try:
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

                    except ImportError:
                        self.logger.warning("beautifulsoup4 not available - cannot extract text")

                result = {
                    "url": url,
                    "content_type": content_type,
                    "content_length": len(content),
                    "raw_html": content if not extract_text else None,
                    "extracted_text": extracted_text,
                }

                # Cache result
                self._set_cached(cache_key, result)

                self.logger.info(f"Fetched {len(content)} bytes from {url}")
                return success_response(result, {"url": url, "from_cache": False})

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
                Summarized content
            """
            try:
                self.logger.info(f"Summarizing content of length {len(content)}")

                if len(content) <= max_length:
                    return success_response(
                        {
                            "summary": content,
                            "original_length": len(content),
                            "summary_length": len(content),
                            "truncated": False,
                        }
                    )

                # Simple truncation (for now - could use LLM for better summarization)
                summary = content[:max_length] + "..."

                self.logger.info(f"Truncated content from {len(content)} to {len(summary)}")
                return success_response(
                    {
                        "summary": summary,
                        "original_length": len(content),
                        "summary_length": len(summary),
                        "truncated": True,
                    }
                )

            except Exception as e:
                self.logger.exception("summarize_content failed", e)
                return error_response(f"Failed to summarize content: {str(e)}")

        @self.mcp.tool()
        async def clear_cache(max_age_days: int | None = None) -> dict[str, Any]:
            """Clear web research cache

            Args:
                max_age_days: Only clear cache older than this many days (optional)

            Returns:
                Number of cache files cleared
            """
            try:
                self.logger.info(f"Clearing cache (max_age_days={max_age_days})")

                cleared_count = 0
                now = datetime.now()

                for cache_file in self.cache_dir.glob("*.json"):
                    should_delete = False

                    if max_age_days is None:
                        should_delete = True
                    else:
                        # Check file age
                        try:
                            with open(cache_file) as f:
                                cached = json.load(f)
                                cached_at = datetime.fromisoformat(cached["cached_at"])
                                age = now - cached_at

                                if age > timedelta(days=max_age_days):
                                    should_delete = True
                        except Exception:
                            # Delete corrupted cache files
                            should_delete = True

                    if should_delete:
                        cache_file.unlink()
                        cleared_count += 1

                self.logger.info(f"Cleared {cleared_count} cache files")
                return success_response({"cleared_count": cleared_count, "max_age_days": max_age_days})

            except Exception as e:
                self.logger.exception("clear_cache failed", e)
                return error_response(f"Failed to clear cache: {str(e)}")


# Create and run server
if __name__ == "__main__":
    server = WebResearchServer()
    server.run()
