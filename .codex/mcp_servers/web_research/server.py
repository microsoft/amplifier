"""
Web Research MCP Server for Codex.
Provides web search and content fetching capabilities.
Replaces Claude Code WebFetch functionality with explicit MCP tools.
"""

import asyncio
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Import FastMCP for server framework
from mcp.server.fastmcp import FastMCP

# Import base utilities
from ..base import (
    AmplifierMCPServer,
    MCPLogger,
    get_project_root,
    success_response,
    error_response,
    safe_import
)

# Try to import required libraries with fallbacks
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# Initialize FastMCP server
mcp = FastMCP("amplifier-web")

# Initialize base server
server = AmplifierMCPServer("web_research", mcp)
logger = server.logger


class WebCache:
    """Simple file-based cache for web requests"""
    
    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600
        
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached response if valid"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                
            # Check if cache is expired
            if time.time() - data['timestamp'] > self.ttl_seconds:
                cache_file.unlink()
                return None
                
            return data['content']
        except Exception:
            # If cache file is corrupted, remove it
            cache_file.unlink()
            return None
    
    def set(self, url: str, content: Dict[str, Any]):
        """Cache response"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        data = {
            'timestamp': time.time(),
            'content': content
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to cache response for {url}: {e}")


class RateLimiter:
    """Simple rate limiter to be respectful to web services"""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        
    def can_make_request(self) -> bool:
        """Check if we can make a request"""
        now = time.time()
        # Remove old requests
        self.requests = [t for t in self.requests if now - t < 60]
        return len(self.requests) < self.requests_per_minute
    
    def record_request(self):
        """Record a request"""
        self.requests.append(time.time())


class TextSummarizer:
    """Simple text summarizer using frequency analysis"""
    
    def __init__(self):
        self.nltk_available = safe_import('nltk') is not None
        if self.nltk_available:
            try:
                import nltk
                from nltk.corpus import stopwords
                from nltk.tokenize import sent_tokenize, word_tokenize
                # Download required data if not present
                try:
                    nltk.data.find('tokenizers/punkt')
                except LookupError:
                    nltk.download('punkt', quiet=True)
                try:
                    nltk.data.find('corpora/stopwords')
                except LookupError:
                    nltk.download('stopwords', quiet=True)
                self.stopwords = set(stopwords.words('english'))
                self.sent_tokenize = sent_tokenize
                self.word_tokenize = word_tokenize
            except Exception:
                self.nltk_available = False
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize text to approximately max_length characters"""
        if not text or len(text) <= max_length:
            return text
            
        if not self.nltk_available:
            # Simple fallback: take first part of text
            return text[:max_length].rsplit(' ', 1)[0] + "..."
        
        try:
            # Split into sentences
            sentences = self.sent_tokenize(text)
            if len(sentences) <= 2:
                return text[:max_length] + "..." if len(text) > max_length else text
            
            # Tokenize and clean words
            words = []
            for sent in sentences:
                sent_words = [w.lower() for w in self.word_tokenize(sent) 
                            if w.isalpha() and w.lower() not in self.stopwords]
                words.extend(sent_words)
            
            # Build frequency table
            freq = {}
            for word in words:
                freq[word] = freq.get(word, 0) + 1
            
            if not freq:
                return text[:max_length] + "..."
            
            # Score sentences
            sentence_scores = []
            for i, sent in enumerate(sentences):
                sent_words = [w.lower() for w in self.word_tokenize(sent) 
                            if w.isalpha() and w.lower() not in self.stopwords]
                if not sent_words:
                    continue
                score = sum(freq.get(w, 0) for w in sent_words) / len(sent_words)
                sentence_scores.append((score, i, sent))
            
            # Get top sentences, maintaining order
            top_sentences = sorted(sentence_scores, key=lambda x: x[0], reverse=True)[:3]
            selected_sentences = [sent for _, _, sent in sorted(top_sentences, key=lambda x: x[1])]
            
            summary = ' '.join(selected_sentences)
            
            # Trim to max_length
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(' ', 1)[0] + "..."
            
            return summary
            
        except Exception as e:
            logger.warning(f"Summarization failed, using fallback: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text


# Initialize components
cache_dir = Path(__file__).parent.parent / "web_cache"
cache = WebCache(cache_dir)
rate_limiter = RateLimiter()
summarizer = TextSummarizer()


@mcp.tool()
@server.tool_error_handler
async def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo and return results.
    
    Args:
        query: Search query string
        num_results: Maximum number of results to return (default: 5, max: 10)
        
    Returns:
        Dictionary containing search results with titles, URLs, and snippets
    """
    try:
        logger.info(f"Searching web for: {query}")
        
        # Validate inputs
        if not query or not query.strip():
            return error_response("Query cannot be empty")
        
        num_results = min(max(1, num_results), 10)  # Clamp between 1 and 10
        
        # Check rate limit
        if not rate_limiter.can_make_request():
            return error_response("Rate limit exceeded. Please wait before making another request.")
        
        results = []
        
        if DDGS_AVAILABLE:
            # Use duckduckgo_search library
            logger.debug("Using DDGS library for search")
            try:
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=num_results))
                    
                for result in search_results:
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('href', result.get('url', '')),
                        'snippet': result.get('body', '')
                    })
                    
                rate_limiter.record_request()
                
            except Exception as e:
                logger.error(f"DDGS search failed: {e}")
                return error_response("Search failed", {"error": str(e)})
                
        elif REQUESTS_AVAILABLE:
            # Fallback to direct DuckDuckGo HTML scraping
            logger.debug("Using requests fallback for search")
            try:
                url = "https://duckduckgo.com/html/"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; WebResearch/1.0)'
                }
                
                response = requests.get(url, params={'q': query}, headers=headers, timeout=10)
                response.raise_for_status()
                
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    result_links = soup.select('a.result__a')[:num_results]
                    
                    for link in result_links:
                        title = link.get_text(strip=True)
                        href = link.get('href', '')
                        # DuckDuckGo uses redirect URLs, try to extract real URL
                        if href.startswith('/l/?uddg='):
                            # This is a redirect, we can't easily get the real URL without following
                            continue
                        
                        results.append({
                            'title': title,
                            'url': href,
                            'snippet': ''  # No snippet in basic HTML results
                        })
                else:
                    return error_response("BeautifulSoup not available for HTML parsing")
                    
                rate_limiter.record_request()
                
            except Exception as e:
                logger.error(f"Requests search failed: {e}")
                return error_response("Search failed", {"error": str(e)})
        else:
            return error_response("No search capability available - requests library not found")
        
        logger.info(f"Found {len(results)} search results")
        return success_response({
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.exception("Unexpected error in search_web", e)
        return error_response("Search failed", {"error": str(e)})


@mcp.tool()
@server.tool_error_handler
async def fetch_url(url: str, extract_text: bool = True) -> Dict[str, Any]:
    """
    Fetch content from a URL and optionally extract readable text.
    
    Args:
        url: URL to fetch
        extract_text: Whether to extract readable text from HTML (default: True)
        
    Returns:
        Dictionary containing fetched content, metadata, and extracted text if requested
    """
    try:
        logger.info(f"Fetching URL: {url}")
        
        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return error_response("Invalid URL format")
        except Exception:
            return error_response("Invalid URL")
        
        # Check cache first
        cached = cache.get(url)
        if cached:
            logger.info("Returning cached content")
            return success_response(cached)
        
        # Check rate limit
        if not rate_limiter.can_make_request():
            return error_response("Rate limit exceeded. Please wait before making another request.")
        
        if not REQUESTS_AVAILABLE:
            return error_response("Requests library not available")
        
        # Fetch content
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; WebResearch/1.0)'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return error_response("Failed to fetch URL", {"error": str(e)})
        
        content_type = response.headers.get('content-type', '').lower()
        content = response.text
        
        result = {
            'url': url,
            'status_code': response.status_code,
            'content_type': content_type,
            'content_length': len(content)
        }
        
        # Extract text if requested and it's HTML
        if extract_text and 'text/html' in content_type and BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                result['extracted_text'] = text
                
            except Exception as e:
                logger.warning(f"Text extraction failed: {e}")
                result['extracted_text'] = content  # Fallback to raw content
        elif extract_text and 'text/html' in content_type:
            logger.warning("BeautifulSoup not available for text extraction")
            result['extracted_text'] = content
        else:
            result['content'] = content[:5000]  # Limit raw content size
        
        # Cache the result
        cache.set(url, result)
        rate_limiter.record_request()
        
        logger.info(f"Successfully fetched {len(content)} characters from {url}")
        return success_response(result)
        
    except Exception as e:
        logger.exception("Unexpected error in fetch_url", e)
        return error_response("Fetch failed", {"error": str(e)})


@mcp.tool()
@server.tool_error_handler
async def summarize_content(content: str, max_length: int = 200) -> Dict[str, Any]:
    """
    Summarize text content to a specified maximum length.
    
    Args:
        content: Text content to summarize
        max_length: Maximum length of summary in characters (default: 200, max: 1000)
        
    Returns:
        Dictionary containing the summary and metadata
    """
    try:
        logger.info(f"Summarizing content of length {len(content)}")
        
        # Validate inputs
        if not content or not content.strip():
            return error_response("Content cannot be empty")
        
        max_length = min(max(50, max_length), 1000)  # Clamp between 50 and 1000
        
        # Generate summary
        summary = summarizer.summarize(content, max_length)
        
        result = {
            'original_length': len(content),
            'summary_length': len(summary),
            'summary': summary,
            'max_length_requested': max_length
        }
        
        logger.info(f"Generated summary of {len(summary)} characters")
        return success_response(result)
        
    except Exception as e:
        logger.exception("Unexpected error in summarize_content", e)
        return error_response("Summarization failed", {"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting Web Research MCP Server")
    server.run()