"""Web research component for gathering and analyzing sources."""

import asyncio
import contextlib
import logging
from datetime import datetime

from anthropic import Anthropic
from ddgs import DDGS

from ..cli import print_progress
from ..models import CredibilityLevel
from ..models import PreliminaryFindings
from ..models import ResearchContext
from ..models import ResearchNote
from ..models import Source
from .web_scraper import WebScraper

logger = logging.getLogger(__name__)


class WebResearcher:
    """Performs web research using search + scraping + AI analysis."""

    def __init__(self: "WebResearcher", api_key: str) -> None:
        """Initialize web researcher.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.scraper = WebScraper()
        self.ddgs = DDGS()

    async def research(self: "WebResearcher", context: ResearchContext, max_sources: int = 20) -> PreliminaryFindings:
        """Perform web research and return findings.

        Args:
            context: Research context
            max_sources: Maximum number of sources to gather

        Returns:
            PreliminaryFindings with sources, notes, and themes
        """
        print_progress(f"Generating search queries for: {context.question}")

        search_queries = self._generate_search_queries(context)
        findings = PreliminaryFindings(search_queries_used=search_queries)

        print_progress(f"Generated {len(search_queries)} search queries")

        sources_gathered = 0
        for query in search_queries:
            if sources_gathered >= max_sources:
                break

            print_progress(f'Searching: "{query}"')

            try:
                results = self.ddgs.text(query, max_results=5)

                for result in results:
                    if sources_gathered >= max_sources:
                        break

                    url = result.get("href", "")
                    if not url or not self.scraper.is_valid_url(url):
                        continue

                    print_progress(f"Scraping: {url}")

                    scraped = await self.scraper.scrape_url(url)

                    if not scraped.success or len(scraped.text) < 200:
                        logger.warning(f"Skipping {url}: {scraped.error or 'insufficient content'}")
                        continue

                    print_progress("Analyzing credibility and extracting notes...")

                    credibility, reasoning = self._assess_credibility(scraped.url, scraped.title, scraped.text)

                    source = Source(
                        url=scraped.url,
                        title=scraped.title,
                        content=scraped.text,
                        credibility=credibility,
                        credibility_reasoning=reasoning,
                    )
                    findings.sources.append(source)

                    notes = self._extract_notes(context, scraped.text, scraped.url, scraped.title)
                    findings.notes.extend(notes)

                    sources_gathered += 1
                    print_progress(f"Progress: {sources_gathered}/{max_sources} sources")

                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error searching '{query}': {e}")
                continue

        findings.completed_at = datetime.now().isoformat()

        print_progress(f"Research complete: {len(findings.sources)} sources, {len(findings.notes)} notes")

        return findings

    def _generate_search_queries(self: "WebResearcher", context: ResearchContext) -> list[str]:
        """Generate 5-10 search queries based on research context.

        Args:
            context: Research context

        Returns:
            List of search queries
        """
        prompt = f"""Generate 5-10 effective search queries for this research:

{context.to_prompt_context()}

Create diverse queries that will find:
- Authoritative sources
- Recent information
- Different perspectives
- Technical details if applicable
- Competitive insights if relevant

Return ONLY the queries, one per line, without numbering."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=1024, messages=[{"role": "user", "content": prompt}]
        )

        queries_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                queries_text = block.text  # type: ignore[attr-defined]
                break
        if not queries_text:
            queries_text = str(response.content[0])

        queries = [q.strip() for q in queries_text.strip().split("\n") if q.strip()]

        return queries[:10]

    def _assess_credibility(self: "WebResearcher", url: str, title: str, content: str) -> tuple[CredibilityLevel, str]:
        """Assess source credibility using Claude.

        Args:
            url: Source URL
            title: Page title
            content: Page content (truncated)

        Returns:
            Tuple of (credibility_level, reasoning)
        """
        content_sample = content[:2000]

        prompt = f"""Assess the credibility of this source:

URL: {url}
Title: {title}

Content Sample:
{content_sample}

Provide credibility assessment:
LEVEL: <one of: high, medium, low>
REASONING: <brief explanation>

High = Authoritative, well-established sources (official sites, reputable publications)
Medium = Reasonable credibility, needs verification (blogs with citations, industry sites)
Low = Questionable or unverified (personal blogs, no sources, promotional)"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=256, messages=[{"role": "user", "content": prompt}]
        )

        assessment_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assessment_text = block.text  # type: ignore[attr-defined]
                break
        if not assessment_text:
            assessment_text = str(response.content[0])

        level = CredibilityLevel.MEDIUM
        reasoning = "Unable to assess"

        for line in assessment_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().upper()
                value = value.strip()

                if key == "LEVEL":
                    with contextlib.suppress(ValueError):
                        level = CredibilityLevel(value.lower())
                elif key == "REASONING":
                    reasoning = value

        return level, reasoning

    def _extract_notes(
        self: "WebResearcher", context: ResearchContext, content: str, source_url: str, source_title: str
    ) -> list[ResearchNote]:
        """Extract research notes from content using Claude.

        Args:
            context: Research context
            content: Source content
            source_url: Source URL
            source_title: Source title

        Returns:
            List of ResearchNote objects
        """
        content_sample = content[:4000]

        prompt = f"""Extract key research notes relevant to this research question:

{context.to_prompt_context()}

Content:
{content_sample}

Extract 2-5 key insights, facts, or findings that directly address the research question.
Return ONLY the notes, one per line, as concise statements."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=1024, messages=[{"role": "user", "content": prompt}]
        )

        notes_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                notes_text = block.text  # type: ignore[attr-defined]
                break
        if not notes_text:
            notes_text = str(response.content[0])

        note_lines = [line.strip() for line in notes_text.strip().split("\n") if line.strip()]

        notes = [
            ResearchNote(content=note, source_url=source_url, source_title=source_title) for note in note_lines[:5]
        ]

        return notes
