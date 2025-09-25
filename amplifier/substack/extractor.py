#!/usr/bin/env python3
"""
Substack Article Extractor for Amplifier Knowledge Mining
Extracts all articles from a Substack author and saves them as markdown files
"""

import asyncio
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from bs4 import Tag


class SubstackExtractor:
    """Extract articles from a Substack publication"""

    def __init__(self, substack_url: str, output_dir: str = "data/articles/raw"):
        """Initialize the extractor

        Args:
            substack_url: URL of the Substack (e.g., https://michaeljjabbour.substack.com/)
            output_dir: Directory to save articles (default: data/articles/raw)
        """
        self.base_url = substack_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Extract the subdomain for the publication name
        parsed = urlparse(self.base_url)
        hostname = parsed.hostname or "unknown"
        self.publication_name = hostname.split(".")[0]

    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch a page's HTML content"""
        async with session.get(url) as response:
            return await response.text()

    async def get_article_links(self, session: aiohttp.ClientSession) -> list[str]:
        """Get all article links from the Substack - handles pagination properly"""
        print(f"Fetching all articles from {self.base_url}...")

        article_links = []
        offset = 0
        limit = 12

        # Keep fetching until we get no more posts
        while True:
            # Substack's public API endpoint for posts
            api_url = f"{self.base_url}/api/v1/posts?offset={offset}&limit={limit}&sort=new"

            try:
                async with session.get(api_url, headers={"Accept": "application/json"}) as response:
                    if response.status == 200:
                        text = await response.text()
                        # Parse JSON response
                        import json

                        data = json.loads(text)

                        # Get the posts array
                        posts = data if isinstance(data, list) else data.get("posts", [])

                        if not posts:
                            print(f"No more posts found at offset {offset}")
                            break

                        for post in posts:
                            # Extract the URL from the post data
                            slug = post.get("slug", "")
                            if slug:
                                article_url = f"{self.base_url}/p/{slug}"
                                if article_url not in article_links:
                                    article_links.append(article_url)
                                    print(f"  Found: {post.get('title', 'Untitled')}")

                        print(f"Fetched {len(posts)} articles at offset {offset}")

                        # Check if there are more posts
                        if len(posts) < limit:
                            print("Reached end of articles")
                            break

                        offset += limit
                        await asyncio.sleep(0.5)  # Be polite to the API
                    else:
                        # Try alternate API endpoint
                        print(f"First API endpoint returned {response.status}, trying alternate...")
                        break

            except Exception as e:
                print(f"API error: {e}")
                break

        # If API didn't work or found nothing, try HTML scraping with pagination
        if not article_links:
            print("API approach failed, trying HTML scraping...")
            page_num = 0

            while True:
                # Try to access paginated archive pages
                if page_num == 0:
                    archive_url = f"{self.base_url}/archive"
                else:
                    archive_url = f"{self.base_url}/archive?offset={page_num * 12}"

                try:
                    html = await self.fetch_page(session, archive_url)
                    soup = BeautifulSoup(html, "html.parser")

                    page_links = []
                    for link in soup.find_all("a", href=True):
                        if not isinstance(link, Tag):
                            continue
                        href = link.get("href", "")
                        if not isinstance(href, str):
                            continue
                        if "/p/" in href:
                            if href.startswith("/"):
                                href = f"{self.base_url}{href}"
                            elif not href.startswith("http"):
                                href = f"{self.base_url}/{href}"
                            href = href.split("?")[0].replace("/comments", "")
                            if href not in article_links and href not in page_links:
                                page_links.append(href)

                    if not page_links:
                        print(f"No more articles found on page {page_num + 1}")
                        break

                    article_links.extend(page_links)
                    print(f"Found {len(page_links)} articles on page {page_num + 1}")

                    # Check if there's a "Load more" or similar indicator
                    # Most Substack archives load 12 articles at a time
                    if len(page_links) < 12:
                        break

                    page_num += 1
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"Error fetching page {page_num + 1}: {e}")
                    break

        return article_links

    async def extract_article(self, session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
        """Extract article content from a URL"""
        print(f"Extracting: {url}")

        html = await self.fetch_page(session, url)
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = soup.find("h1", class_="post-title")
        if not title:
            title = soup.find("h1")
        title_text = title.get_text(strip=True) if title else "Untitled"

        # Extract subtitle if present
        subtitle = soup.find("h3", class_="subtitle")
        subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

        # Extract publish date
        date_elem = soup.find("time")
        publish_date = ""
        if isinstance(date_elem, Tag):
            publish_date = date_elem.get("datetime", "")

        # Extract author
        author_elem = soup.find("a", class_="frontend-pencraft-Text-module__decoration-hover-underline--BEYAn")
        if not author_elem:
            author_elem = soup.find("span", string=re.compile(r".*"))
        author = self.publication_name  # Default to publication name

        # Extract main content - Substack uses different class names
        content_div = soup.find("div", class_="available-content")
        if not content_div:
            content_div = soup.find("div", class_="body markup")
        if not content_div:
            content_div = soup.find("div", {"class": re.compile(r"body.*")})
        if not content_div:
            content_div = soup.find("article")

        content_parts = []
        if isinstance(content_div, Tag):
            # Convert to markdown-like format
            for elem in content_div.find_all(["p", "h1", "h2", "h3", "h4", "blockquote", "ul", "ol", "li"]):
                if not isinstance(elem, Tag):
                    continue
                text = elem.get_text(strip=True)
                if not text:
                    continue

                elem_name = getattr(elem, "name", None)
                if elem_name == "h1":
                    content_parts.append(f"\n# {text}\n")
                elif elem_name == "h2":
                    content_parts.append(f"\n## {text}\n")
                elif elem_name == "h3":
                    content_parts.append(f"\n### {text}\n")
                elif elem_name == "h4":
                    content_parts.append(f"\n#### {text}\n")
                elif elem_name == "blockquote":
                    content_parts.append(f"\n> {text}\n")
                elif elem_name == "li":
                    content_parts.append(f"- {text}")
                else:
                    content_parts.append(f"{text}\n")

        return {
            "url": url,
            "title": title_text,
            "subtitle": subtitle_text,
            "author": author,
            "date": publish_date,
            "content": "\n".join(content_parts),
        }

    def save_article(self, article: dict[str, Any]) -> Path:
        """Save article as markdown file"""
        # Create a safe filename from the title
        safe_title = re.sub(r"[^\w\s-]", "", article["title"])
        safe_title = re.sub(r"[-\s]+", "-", safe_title)[:100]

        filename = f"{self.publication_name}_{safe_title}.md"
        filepath = self.output_dir / filename

        # Create markdown content with frontmatter
        markdown_content = f"""---
title: {article["title"]}
author: {article["author"]}
date: {article["date"]}
source: {article["url"]}
publication: {self.publication_name}
---

# {article["title"]}

"""
        if article["subtitle"]:
            markdown_content += f"*{article['subtitle']}*\n\n"

        markdown_content += article["content"]

        filepath.write_text(markdown_content, encoding="utf-8")
        print(f"Saved: {filepath}")
        return filepath

    async def extract_all(self) -> list[Path]:
        """Extract all articles from the Substack"""
        async with aiohttp.ClientSession() as session:
            # Get all article links
            article_links = await self.get_article_links(session)
            print(f"Found {len(article_links)} articles")

            # Extract each article
            saved_files = []
            for url in article_links:
                try:
                    article = await self.extract_article(session, url)
                    if article["content"]:
                        filepath = self.save_article(article)
                        saved_files.append(filepath)
                    await asyncio.sleep(1)  # Be polite to the server
                except Exception as e:
                    print(f"Error extracting {url}: {e}")
                    continue

            return saved_files


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python substack_extractor.py <substack_url>")
        print("Example: python substack_extractor.py https://michaeljjabbour.substack.com/")
        sys.exit(1)

    substack_url = sys.argv[1]

    # Create extractor and run
    extractor = SubstackExtractor(substack_url)
    saved_files = await extractor.extract_all()

    print("\n✅ Extraction complete!")
    print(f"📁 Saved {len(saved_files)} articles to {extractor.output_dir}")
    print("\n🚀 Now run: amplifier mine-knowledge")
    print("   Then: amplifier synthesize")
    print("   To build your knowledge graph!")


if __name__ == "__main__":
    asyncio.run(main())
