#!/usr/bin/env python3
"""
Tool: UI/UX Pattern Miner
Purpose: Mine articles for UI/UX planning and implementation techniques

Contract:
  Inputs: Directory of markdown articles (minimum 2 for synthesis)
  Outputs: Structured JSON with patterns + human-readable markdown report
  Failures: Clear errors with recovery suggestions

Philosophy:
  - Ruthless simplicity: Direct solutions without abstractions
  - Fail fast and loud: Clear errors, no silent failures
  - Progress visibility: Show what's happening
  - Defensive by default: Handle LLM and file I/O edge cases
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from pydantic import BaseModel
from pydantic import Field

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.ccsdk_toolkit.logger import create_logger

logger = create_logger(__name__)


# ============================================================================
# DATA MODELS (Clear contracts for data structures)
# ============================================================================


class UIUXPattern(BaseModel):
    """A single UI/UX pattern extracted from an article."""

    technique: str = Field(description="Name/description of the technique")
    category: str = Field(description="Category (e.g., planning, implementation, design)")
    rationale: str = Field(description="Why this technique is valuable")
    practical_value: int = Field(description="Practical value rating 1-10", ge=1, le=10)
    examples: list[str] = Field(default_factory=list, description="Code/usage examples")
    source_article: str = Field(description="Source article filename")


class ArticleAnalysis(BaseModel):
    """Analysis results from a single article."""

    article_path: str
    article_title: str = ""
    patterns: list[UIUXPattern] = Field(default_factory=list)
    key_insights: list[str] = Field(default_factory=list)
    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SynthesisResult(BaseModel):
    """Final synthesis of all patterns."""

    total_articles: int
    total_patterns: int
    top_patterns: list[dict[str, Any]]  # Ranked patterns with metadata
    categories_found: dict[str, int]  # Category distribution
    synthesis_insights: list[str]
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# SESSION MANAGER (Resume capability)
# ============================================================================


class SessionManager:
    """Manages session state for resume capability."""

    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Load previous state for resume capability."""
        if self.session_file.exists():
            try:
                state = read_json_with_retry(self.session_file)
                logger.info(f"Resumed session with {len(state.get('processed', []))} processed items")
                return state
            except Exception as e:
                logger.warning(f"Could not load state: {e}, starting fresh")
        return {
            "processed": [],
            "stage1_results": [],
            "stage2_results": [],
            "stage3_results": None,
            "started_at": datetime.now().isoformat(),
        }

    def save_state(self) -> None:
        """Save state after each item (incremental progress)."""
        try:
            write_json_with_retry(self.state, self.session_file)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def is_processed(self, item: str) -> bool:
        """Check if an item was already processed."""
        return item in self.state["processed"]

    def mark_processed(self, item: str) -> None:
        """Mark an item as processed."""
        if item not in self.state["processed"]:
            self.state["processed"].append(item)
            self.save_state()

    def add_stage1_result(self, result: dict) -> None:
        """Add a stage 1 result."""
        self.state["stage1_results"].append(result)
        self.save_state()

    def add_stage2_result(self, result: dict) -> None:
        """Add a stage 2 result."""
        self.state["stage2_results"].append(result)
        self.save_state()

    def set_stage3_result(self, result: dict) -> None:
        """Set the stage 3 synthesis result."""
        self.state["stage3_results"] = result
        self.save_state()


# ============================================================================
# PATTERN EXTRACTOR (Core processing logic)
# ============================================================================


class UIUXPatternExtractor:
    """Extracts UI/UX patterns from articles using AI."""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    async def stage1_discover(self, articles_dir: Path, pattern: str = "**/*.md") -> list[Path]:
        """Stage 1: Discover and index articles."""
        logger.info("=== Stage 1: Article Discovery ===")

        # Find all articles
        articles = list(articles_dir.glob(pattern))

        if not articles:
            logger.error(f"No articles found in {articles_dir} with pattern {pattern}")
            return []

        logger.info(f"Found {len(articles)} articles:")
        for article in articles[:5]:
            logger.info(f"  • {article.name}")
        if len(articles) > 5:
            logger.info(f"  ... and {len(articles) - 5} more")

        # Save index to session
        for article in articles:
            if not self.session_manager.is_processed(f"stage1_{article}"):
                self.session_manager.add_stage1_result({"path": str(article)})
                self.session_manager.mark_processed(f"stage1_{article}")

        return articles

    async def stage2_extract_patterns(self, articles: list[Path]) -> list[ArticleAnalysis]:
        """Stage 2: Extract patterns from each article."""
        logger.info("=== Stage 2: Pattern Extraction ===")

        results = []
        options = SessionOptions(
            system_prompt="""You are an expert at analyzing technical articles for UI/UX patterns and techniques.
Focus on finding practical, implementable patterns related to:
- UI/UX planning strategies (like design.json files)
- WebUI implementation approaches
- Interface design methodologies
- Component architecture patterns
- User interaction patterns
- Design system approaches

Extract concrete, actionable techniques that developers can apply.""",
            retry_attempts=2,
            temperature=0.3,
        )

        for i, article in enumerate(articles, 1):
            article_key = f"stage2_{article}"

            # Skip if already processed
            if self.session_manager.is_processed(article_key):
                logger.info(f"[{i}/{len(articles)}] Skipping already processed: {article.name}")
                # Load from session state
                for result in self.session_manager.state.get("stage2_results", []):
                    if result.get("article_path") == str(article):
                        results.append(ArticleAnalysis(**result))
                        break
                continue

            logger.info(f"[{i}/{len(articles)}] Analyzing: {article.name}")

            try:
                # Read article content
                content = article.read_text(encoding="utf-8")
                if not content.strip():
                    logger.warning(f"Empty article: {article.name}")
                    continue

                # Truncate if too long (context window limit)
                max_chars = 50000
                if len(content) > max_chars:
                    content = content[:max_chars]
                    logger.info(f"Truncated {article.name} to {max_chars} chars")

                async with ClaudeSession(options) as session:
                    prompt = f"""Analyze this article for UI/UX patterns and techniques.

Article: {article.name}
Content:
{content}

Extract any UI/UX patterns, planning techniques, or implementation strategies mentioned.
Focus on practical, actionable patterns that developers can use.

Return a JSON object with this structure:
{{
    "article_title": "extracted or inferred title",
    "patterns": [
        {{
            "technique": "name/description of the technique",
            "category": "planning|implementation|design|architecture|interaction",
            "rationale": "why this technique is valuable",
            "practical_value": 1-10,
            "examples": ["any code examples or usage patterns from the article"]
        }}
    ],
    "key_insights": ["major insights about UI/UX from this article"]
}}

If no UI/UX patterns are found, return empty arrays."""

                    response = await session.query(prompt)
                    parsed = parse_llm_json(response.content, default={})

                    # Create analysis object
                    # Add source_article field to each pattern
                    patterns = []
                    for p in parsed.get("patterns", []):
                        p["source_article"] = article.name  # Add the missing field
                        try:
                            patterns.append(UIUXPattern(**p))
                        except Exception as e:
                            logger.warning(f"Skipping invalid pattern in {article.name}: {e}")
                            continue

                    analysis = ArticleAnalysis(
                        article_path=str(article),
                        article_title=parsed.get("article_title", article.name),
                        patterns=patterns,
                        key_insights=parsed.get("key_insights", []),
                    )

                    results.append(analysis)

                    # Save progress immediately
                    self.session_manager.add_stage2_result(analysis.dict())
                    self.session_manager.mark_processed(article_key)

                    # Show progress
                    if analysis.patterns:
                        logger.info(f"  → Found {len(analysis.patterns)} patterns")

            except Exception as e:
                logger.error(f"Failed to process {article.name}: {e}")
                # Continue on partial failure
                continue

        logger.info(f"Stage 2 complete: Extracted patterns from {len(results)} articles")
        return results

    async def stage3_synthesize(self, analyses: list[ArticleAnalysis]) -> SynthesisResult:
        """Stage 3: Synthesize and rank patterns."""
        logger.info("=== Stage 3: Pattern Synthesis ===")

        # Check if already synthesized
        if self.session_manager.state.get("stage3_results"):
            logger.info("Using cached synthesis results")
            return SynthesisResult(**self.session_manager.state["stage3_results"])

        # Collect all patterns
        all_patterns = []
        for analysis in analyses:
            for pattern in analysis.patterns:
                all_patterns.append(
                    {
                        "technique": pattern.technique,
                        "category": pattern.category,
                        "rationale": pattern.rationale,
                        "practical_value": pattern.practical_value,
                        "source": pattern.source_article,  # Already just the filename
                    }
                )

        if not all_patterns:
            logger.warning("No patterns found to synthesize")
            return SynthesisResult(
                total_articles=len(analyses),
                total_patterns=0,
                top_patterns=[],
                categories_found={},
                synthesis_insights=["No UI/UX patterns found in analyzed articles"],
            )

        # Category distribution
        categories = {}
        for p in all_patterns:
            cat = p["category"]
            categories[cat] = categories.get(cat, 0) + 1

        # AI synthesis for deeper insights
        options = SessionOptions(
            system_prompt="""You are an expert at synthesizing UI/UX patterns and identifying high-leverage techniques.
Your goal is to identify the most valuable, practical patterns that developers should prioritize.""",
            retry_attempts=2,
            temperature=0.4,
        )

        async with ClaudeSession(options) as session:
            patterns_json = json.dumps(all_patterns, indent=2)
            prompt = f"""Analyze these UI/UX patterns extracted from {len(analyses)} articles.

Patterns found:
{patterns_json}

Please:
1. Identify the TOP 10-15 most valuable patterns based on practical leverage
2. Look for emerging themes or meta-patterns
3. Provide synthesis insights about the overall landscape of techniques

Return JSON:
{{
    "top_patterns": [
        {{
            "rank": 1,
            "technique": "pattern name",
            "category": "category",
            "combined_score": 1-10,
            "why_valuable": "explanation",
            "sources": ["article1.md", "article2.md"]
        }}
    ],
    "synthesis_insights": [
        "insight about overall patterns",
        "emerging themes",
        "recommendations for developers"
    ]
}}"""

            response = await session.query(prompt)
            synthesis = parse_llm_json(response.content, default={})

        # Create final result
        result = SynthesisResult(
            total_articles=len(analyses),
            total_patterns=len(all_patterns),
            top_patterns=synthesis.get("top_patterns", all_patterns[:10]),
            categories_found=categories,
            synthesis_insights=synthesis.get("synthesis_insights", []),
        )

        # Save synthesis
        self.session_manager.set_stage3_result(result.dict())

        logger.info(f"Synthesis complete: {result.total_patterns} patterns ranked")
        return result


# ============================================================================
# REPORT GENERATION
# ============================================================================


def generate_markdown_report(synthesis: SynthesisResult, output_path: Path, articles_dir: Path) -> None:
    """Generate human-readable markdown report."""
    logger.info("Generating markdown report...")

    lines = [
        "# UI/UX Pattern Mining Report",
        f"\nGenerated: {synthesis.generated_at}",
        "\n## Summary",
        f"\n- **Articles Analyzed**: {synthesis.total_articles}",
        f"- **Patterns Extracted**: {synthesis.total_patterns}",
        f"- **Categories Found**: {', '.join(synthesis.categories_found.keys())}",
        "\n## Top UI/UX Patterns\n",
    ]

    # Top patterns table
    if synthesis.top_patterns:
        lines.append("| Rank | Technique | Category | Score | Why Valuable |")
        lines.append("|------|-----------|----------|-------|--------------|")

        for pattern in synthesis.top_patterns[:15]:
            rank = pattern.get("rank", "?")
            technique = pattern.get("technique", "Unknown")
            category = pattern.get("category", "")
            score = pattern.get("combined_score", pattern.get("practical_value", "?"))
            why = pattern.get("why_valuable", pattern.get("rationale", ""))[:100]
            if len(why) == 100:
                why += "..."

            lines.append(f"| {rank} | {technique} | {category} | {score}/10 | {why} |")

        # Sources section
        lines.append("\n### Pattern Sources\n")
        for pattern in synthesis.top_patterns[:10]:
            technique = pattern.get("technique", "Unknown")
            sources = pattern.get("sources", [])
            if sources:
                source_links = [f"`{s}`" for s in sources[:3]]
                lines.append(f"- **{technique}**: {', '.join(source_links)}")

    # Category breakdown
    if synthesis.categories_found:
        lines.append("\n## Category Distribution\n")
        for category, count in sorted(synthesis.categories_found.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / synthesis.total_patterns * 100) if synthesis.total_patterns > 0 else 0
            lines.append(f"- **{category}**: {count} patterns ({percentage:.1f}%)")

    # Synthesis insights
    if synthesis.synthesis_insights:
        lines.append("\n## Key Insights\n")
        for insight in synthesis.synthesis_insights:
            lines.append(f"- {insight}")

    # Recommendations
    lines.extend(
        [
            "\n## Recommendations\n",
            "Based on the patterns discovered, consider:",
            "",
            "1. **Adopt High-Value Patterns**: Focus on patterns with scores 8+ for immediate impact",
            "2. **Category Balance**: Ensure coverage across planning, implementation, and design",
            "3. **Pattern Combinations**: Look for patterns that work well together",
            "4. **Continuous Learning**: Regularly mine new articles for emerging patterns",
        ]
    )

    # Write report
    report_content = "\n".join(lines)
    output_path.write_text(report_content, encoding="utf-8")
    logger.info(f"📄 Markdown report saved to: {output_path}")


# ============================================================================
# CLI INTERFACE
# ============================================================================


@click.command()
@click.option(
    "--articles-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path.home() / "amplifier" / "content" / "medium" / "articles",
    help="Directory containing articles to mine",
)
@click.option(
    "--pattern",
    default="**/*.md",
    help="Glob pattern for article discovery (default: **/*.md)",
)
@click.option(
    "--min-articles",
    default=2,
    type=int,
    help="Minimum articles required for synthesis (default: 2)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("uiux_patterns_output"),
    help="Output directory for results",
)
@click.option(
    "--session-file",
    type=click.Path(path_type=Path),
    default=Path("uiux_mining_session.json"),
    help="Session file for resume capability",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def main(
    articles_dir: Path,
    pattern: str,
    min_articles: int,
    output_dir: Path,
    session_file: Path,
    verbose: bool,
):
    """UI/UX Pattern Miner - Extract UI/UX techniques from articles.

    Mines articles for UI/UX planning and implementation patterns,
    including design.json approaches, WebUI strategies, and interface
    design techniques.
    """
    # Setup
    global logger
    if verbose:
        logger = create_logger(__name__, level="DEBUG")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize session manager
    session_manager = SessionManager(session_file)

    # Create extractor
    extractor = UIUXPatternExtractor(session_manager)

    async def run_pipeline():
        # Stage 1: Discover articles
        articles = await extractor.stage1_discover(articles_dir, pattern)

        if len(articles) < min_articles:
            logger.error(f"Need at least {min_articles} articles, found {len(articles)}")
            sys.exit(1)

        # Stage 2: Extract patterns
        analyses = await extractor.stage2_extract_patterns(articles)

        if not analyses:
            logger.error("No analyses produced - cannot synthesize")
            sys.exit(1)

        # Stage 3: Synthesize
        synthesis = await extractor.stage3_synthesize(analyses)

        return synthesis, analyses

    # Run pipeline
    logger.info("Starting UI/UX pattern mining...")
    synthesis, analyses = asyncio.run(run_pipeline())

    # Save outputs
    output_json = output_dir / "patterns.json"
    output_md = output_dir / "patterns_report.md"

    # Save JSON results
    write_json_with_retry(
        {
            "synthesis": synthesis.dict(),
            "analyses": [a.dict() for a in analyses],
        },
        output_json,
    )
    logger.info(f"📊 JSON results saved to: {output_json}")

    # Generate markdown report
    generate_markdown_report(synthesis, output_md, articles_dir)

    # Summary
    logger.info("=" * 60)
    logger.info("✅ UI/UX Pattern Mining Complete!")
    logger.info(f"📈 Extracted {synthesis.total_patterns} patterns from {synthesis.total_articles} articles")
    logger.info(f"🏆 Identified top {len(synthesis.top_patterns)} high-value patterns")
    logger.info(f"📁 Results saved to: {output_dir}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
