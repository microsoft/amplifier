#!/usr/bin/env python3
"""
Tests for web_research MCP server.

Comprehensive tests covering web search, URL fetching, content summarization,
caching, rate limiting, and error handling.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

import pytest

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".codex"))

# Import modules under test (will be mocked where necessary)
try:
    from .codex.mcp_servers.web_research.server import (
        WebCache,
        RateLimiter,
        TextSummarizer,
        search_web,
        fetch_url,
        summarize_content,
        cache,
        rate_limiter,
        summarizer
    )
except ImportError:
    # Modules not yet implemented - tests will use mocks
    pass


# Test Fixtures

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project_dir(temp_dir) -> Path:
    """Create temporary project directory with common structure."""
    project_dir = temp_dir / "project"
    project_dir.mkdir()
    
    # Create pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")
    
    return project_dir


@pytest.fixture
def mock_requests():
    """Mock requests library."""
    with patch('codex.mcp_servers.web_research.server.requests') as mock_req:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Test Page</h1><p>This is test content.</p></body></html>"
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status.return_value = None
        mock_req.get.return_value = mock_response
        mock_req.exceptions.RequestException = Exception
        yield mock_req


@pytest.fixture
def mock_bs4():
    """Mock BeautifulSoup."""
    with patch('codex.mcp_servers.web_research.server.BeautifulSoup') as mock_bs:
        mock_soup = Mock()
        mock_soup.get_text.return_value = "Test Page This is test content."
        mock_soup.select.return_value = [
            Mock(get_text=lambda: "Test Result", get=lambda x: "http://example.com")
        ]
        mock_bs.return_value = mock_soup
        yield mock_bs


@pytest.fixture
def mock_ddgs():
    """Mock DuckDuckGo search."""
    with patch('codex.mcp_servers.web_research.server.DDGS') as mock_ddgs_class:
        mock_ddgs_instance = Mock()
        mock_ddgs_instance.text.return_value = [
            {'title': 'Test Result 1', 'href': 'http://example1.com', 'body': 'Snippet 1'},
            {'title': 'Test Result 2', 'href': 'http://example2.com', 'body': 'Snippet 2'}
        ]
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_class.return_value.__exit__.return_value = None
        yield mock_ddgs_class


@pytest.fixture
def mock_cache(temp_dir):
    """Mock WebCache instance."""
    cache_dir = temp_dir / "cache"
    cache_dir.mkdir()
    test_cache = WebCache(cache_dir)
    return test_cache


@pytest.fixture
def mock_rate_limiter():
    """Mock RateLimiter instance."""
    limiter = RateLimiter(requests_per_minute=5)
    return limiter


@pytest.fixture
def mock_summarizer():
    """Mock TextSummarizer instance."""
    summarizer = TextSummarizer()
    return summarizer


# Test Classes

class TestWebCache:
    """Test WebCache functionality."""

    def test_cache_initialization(self, temp_dir):
        """Test cache directory creation."""
        cache_dir = temp_dir / "test_cache"
        cache = WebCache(cache_dir)
        
        assert cache_dir.exists()
        assert cache.cache_dir == cache_dir
        assert cache.ttl_seconds == 24 * 3600

    def test_cache_key_generation(self, mock_cache):
        """Test cache key generation."""
        url = "http://example.com/test"
        key1 = mock_cache._get_cache_key(url)
        key2 = mock_cache._get_cache_key(url)
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length

    def test_cache_miss(self, mock_cache):
        """Test cache miss behavior."""
        url = "http://example.com/test"
        result = mock_cache.get(url)
        
        assert result is None

    def test_cache_hit(self, mock_cache):
        """Test cache hit behavior."""
        url = "http://example.com/test"
        test_data = {"content": "test", "url": url}
        
        # Set cache
        mock_cache.set(url, test_data)
        
        # Get cache
        result = mock_cache.get(url)
        
        assert result == test_data

    def test_cache_expiration(self, mock_cache):
        """Test cache expiration."""
        url = "http://example.com/test"
        test_data = {"content": "test"}
        
        # Set cache with old timestamp
        cache_file = mock_cache.cache_dir / f"{mock_cache._get_cache_key(url)}.json"
        old_data = {
            'timestamp': time.time() - (25 * 3600),  # 25 hours ago
            'content': test_data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(old_data, f)
        
        # Should return None due to expiration
        result = mock_cache.get(url)
        
        assert result is None
        assert not cache_file.exists()  # File should be cleaned up

    def test_cache_corruption(self, mock_cache):
        """Test handling of corrupted cache files."""
        url = "http://example.com/test"
        cache_file = mock_cache.cache_dir / f"{mock_cache._get_cache_key(url)}.json"
        
        # Write invalid JSON
        with open(cache_file, 'w') as f:
            f.write("invalid json")
        
        result = mock_cache.get(url)
        
        assert result is None
        assert not cache_file.exists()  # Corrupted file should be removed


class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter setup."""
        limiter = RateLimiter(requests_per_minute=10)
        
        assert limiter.requests_per_minute == 10
        assert limiter.requests == []

    def test_can_make_request_initial(self, mock_rate_limiter):
        """Test initial request allowance."""
        assert mock_rate_limiter.can_make_request() is True

    def test_rate_limit_enforcement(self, mock_rate_limiter):
        """Test rate limit enforcement."""
        # Fill up the rate limiter
        for _ in range(5):
            mock_rate_limiter.record_request()
        
        # Should not allow more requests
        assert mock_rate_limiter.can_make_request() is False

    def test_rate_limit_reset(self, mock_rate_limiter):
        """Test rate limit reset over time."""
        # Fill up the rate limiter
        for _ in range(5):
            mock_rate_limiter.record_request()
        
        # Simulate time passing (61 seconds)
        mock_rate_limiter.requests = [t - 61 for t in mock_rate_limiter.requests]
        
        # Should allow requests again
        assert mock_rate_limiter.can_make_request() is True


class TestTextSummarizer:
    """Test TextSummarizer functionality."""

    def test_summarizer_initialization(self):
        """Test summarizer setup."""
        summarizer = TextSummarizer()
        assert hasattr(summarizer, 'nltk_available')

    def test_summarize_short_text(self, mock_summarizer):
        """Test summarization of short text."""
        text = "This is a short test."
        summary = mock_summarizer.summarize(text, max_length=50)
        
        assert summary == text

    def test_summarize_long_text(self, mock_summarizer):
        """Test summarization of long text."""
        text = "This is a long test text. " * 50  # Repeat to make it long
        summary = mock_summarizer.summarize(text, max_length=50)
        
        assert len(summary) <= 53  # Allow some buffer for "..."
        assert "..." in summary or len(summary) < len(text)

    def test_summarize_empty_text(self, mock_summarizer):
        """Test summarization of empty text."""
        summary = mock_summarizer.summarize("", max_length=50)
        
        assert summary == ""

    def test_summarize_fallback(self):
        """Test fallback summarization when NLTK unavailable."""
        with patch('codex.mcp_servers.web_research.server.safe_import', return_value=None):
            summarizer = TextSummarizer()
            text = "This is a long test text that should be summarized. " * 10
            summary = summarizer.summarize(text, max_length=50)
            
            assert len(summary) <= 53
            assert "..." in summary


class TestWebResearchServer:
    """Test web_research MCP server."""

    @pytest.mark.asyncio
    async def test_search_web_success_ddgs(self, mock_ddgs):
        """Test successful web search with DDGS."""
        with patch('codex.mcp_servers.web_research.server.DDGS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter:
            
            mock_limiter.can_make_request.return_value = True
            
            result = await search_web("test query", num_results=2)
            
            assert result["success"] is True
            assert result["data"]["query"] == "test query"
            assert len(result["data"]["results"]) == 2
            assert result["data"]["results"][0]["title"] == "Test Result 1"

    @pytest.mark.asyncio
    async def test_search_web_success_requests_fallback(self, mock_requests, mock_bs4):
        """Test successful web search with requests fallback."""
        with patch('codex.mcp_servers.web_research.server.DDGS_AVAILABLE', False), \
             patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.BS4_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter:
            
            mock_limiter.can_make_request.return_value = True
            
            result = await search_web("test query", num_results=2)
            
            assert result["success"] is True
            assert len(result["data"]["results"]) == 1  # Mock returns 1 result

    @pytest.mark.asyncio
    async def test_search_web_empty_query(self):
        """Test search with empty query."""
        result = await search_web("", num_results=5)
        
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_search_web_rate_limited(self):
        """Test search when rate limited."""
        with patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter:
            mock_limiter.can_make_request.return_value = False
            
            result = await search_web("test query")
            
            assert result["success"] is False
            assert "rate limit" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_search_web_no_capability(self):
        """Test search when no search capability available."""
        with patch('codex.mcp_servers.web_research.server.DDGS_AVAILABLE', False), \
             patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', False):
            
            result = await search_web("test query")
            
            assert result["success"] is False
            assert "no search capability" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_search_web_ddgs_error(self, mock_ddgs):
        """Test search with DDGS error."""
        with patch('codex.mcp_servers.web_research.server.DDGS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter:
            
            mock_limiter.can_make_request.return_value = True
            mock_ddgs.return_value.__enter__.return_value.text.side_effect = Exception("DDGS error")
            
            result = await search_web("test query")
            
            assert result["success"] is False
            assert "search failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_fetch_url_success(self, mock_requests, mock_bs4):
        """Test successful URL fetching."""
        with patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.BS4_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter, \
             patch('codex.mcp_servers.web_research.server.cache') as mock_cache:
            
            mock_limiter.can_make_request.return_value = True
            mock_cache.get.return_value = None  # Cache miss
            
            result = await fetch_url("http://example.com", extract_text=True)
            
            assert result["success"] is True
            assert result["data"]["url"] == "http://example.com"
            assert result["data"]["status_code"] == 200
            assert "extracted_text" in result["data"]

    @pytest.mark.asyncio
    async def test_fetch_url_cached(self):
        """Test URL fetching with cache hit."""
        with patch('codex.mcp_servers.web_research.server.cache') as mock_cache:
            cached_data = {"url": "http://example.com", "cached": True}
            mock_cache.get.return_value = cached_data
            
            result = await fetch_url("http://example.com")
            
            assert result["success"] is True
            assert result["data"]["cached"] is True

    @pytest.mark.asyncio
    async def test_fetch_url_invalid_url(self):
        """Test fetching with invalid URL."""
        result = await fetch_url("not-a-url")
        
        assert result["success"] is False
        assert "invalid" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_fetch_url_rate_limited(self):
        """Test fetching when rate limited."""
        with patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter:
            mock_limiter.can_make_request.return_value = False
            
            result = await fetch_url("http://example.com")
            
            assert result["success"] is False
            assert "rate limit" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_fetch_url_no_requests(self):
        """Test fetching when requests not available."""
        with patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', False):
            result = await fetch_url("http://example.com")
            
            assert result["success"] is False
            assert "requests library not available" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_url_request_error(self, mock_requests):
        """Test fetching with request error."""
        with patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter:
            
            mock_limiter.can_make_request.return_value = True
            mock_requests.get.side_effect = Exception("Network error")
            
            result = await fetch_url("http://example.com")
            
            assert result["success"] is False
            assert "failed to fetch" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_fetch_url_no_text_extraction(self, mock_requests):
        """Test fetching without text extraction."""
        with patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.BS4_AVAILABLE', False), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter, \
             patch('codex.mcp_servers.web_research.server.cache') as mock_cache:
            
            mock_limiter.can_make_request.return_value = True
            mock_cache.get.return_value = None
            
            result = await fetch_url("http://example.com", extract_text=False)
            
            assert result["success"] is True
            assert "content" in result["data"]
            assert "extracted_text" not in result["data"]

    @pytest.mark.asyncio
    async def test_summarize_content_success(self):
        """Test successful content summarization."""
        content = "This is a long piece of content that should be summarized. " * 20
        result = await summarize_content(content, max_length=100)
        
        assert result["success"] is True
        assert result["data"]["original_length"] == len(content)
        assert result["data"]["summary_length"] <= 103  # Allow buffer
        assert "summary" in result["data"]

    @pytest.mark.asyncio
    async def test_summarize_content_empty(self):
        """Test summarization of empty content."""
        result = await summarize_content("", max_length=100)
        
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_summarize_content_short(self):
        """Test summarization of already short content."""
        content = "Short content"
        result = await summarize_content(content, max_length=100)
        
        assert result["success"] is True
        assert result["data"]["summary"] == content

    @pytest.mark.asyncio
    async def test_summarize_content_length_limits(self):
        """Test summarization length limits."""
        content = "Long content " * 100
        
        # Test minimum length
        result = await summarize_content(content, max_length=10)
        assert result["data"]["max_length_requested"] == 50  # Clamped to minimum
        
        # Test maximum length
        result = await summarize_content(content, max_length=2000)
        assert result["data"]["max_length_requested"] == 1000  # Clamped to maximum


# Integration Tests

class TestWebResearchIntegration:
    """Integration tests for web research functionality."""

    @pytest.mark.asyncio
    async def test_search_and_fetch_workflow(self, mock_ddgs, mock_requests, mock_bs4):
        """Test complete search and fetch workflow."""
        with patch('codex.mcp_servers.web_research.server.DDGS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.BS4_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter, \
             patch('codex.mcp_servers.web_research.server.cache') as mock_cache:
            
            mock_limiter.can_make_request.return_value = True
            mock_cache.get.return_value = None
            
            # Search first
            search_result = await search_web("test query", num_results=1)
            assert search_result["success"] is True
            url = search_result["data"]["results"][0]["url"]
            
            # Then fetch
            fetch_result = await fetch_url(url, extract_text=True)
            assert fetch_result["success"] is True
            
            # Then summarize
            if "extracted_text" in fetch_result["data"]:
                summary_result = await summarize_content(fetch_result["data"]["extracted_text"])
                assert summary_result["success"] is True

    @pytest.mark.asyncio
    async def test_caching_workflow(self, mock_requests, mock_bs4):
        """Test caching behavior in workflow."""
        with patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.BS4_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter, \
             patch('codex.mcp_servers.web_research.server.cache') as mock_cache:
            
            mock_limiter.can_make_request.return_value = True
            
            # First call - cache miss
            mock_cache.get.return_value = None
            result1 = await fetch_url("http://example.com")
            assert result1["success"] is True
            
            # Second call - cache hit
            cached_data = {"url": "http://example.com", "cached": True}
            mock_cache.get.return_value = cached_data
            result2 = await fetch_url("http://example.com")
            assert result2["success"] is True
            assert result2["data"]["cached"] is True

    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self):
        """Test rate limiting across multiple calls."""
        with patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter:
            # Allow first few requests
            call_count = 0
            def can_request():
                nonlocal call_count
                call_count += 1
                return call_count <= 3
            
            mock_limiter.can_make_request.side_effect = can_request
            
            # First requests should succeed
            result1 = await search_web("query1")
            result2 = await search_web("query2")
            result3 = await search_web("query3")
            
            assert result1["success"] is True
            assert result2["success"] is True
            assert result3["success"] is True
            
            # Fourth request should be rate limited
            result4 = await search_web("query4")
            assert result4["success"] is False
            assert "rate limit" in result4["error"].lower()

    @pytest.mark.asyncio
    async def test_error_recovery(self, mock_requests):
        """Test error recovery and graceful degradation."""
        with patch('codex.mcp_servers.web_research.server.REQUESTS_AVAILABLE', True), \
             patch('codex.mcp_servers.web_research.server.rate_limiter') as mock_limiter, \
             patch('codex.mcp_servers.web_research.server.cache') as mock_cache:
            
            mock_limiter.can_make_request.return_value = True
            mock_cache.get.return_value = None
            
            # Simulate network error
            mock_requests.get.side_effect = Exception("Network timeout")
            
            result = await fetch_url("http://example.com")
            
            assert result["success"] is False
            assert "failed to fetch" in result["error"].lower()
            
            # Should still be able to summarize content
            summary_result = await summarize_content("Some content to summarize")
            assert summary_result["success"] is True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])