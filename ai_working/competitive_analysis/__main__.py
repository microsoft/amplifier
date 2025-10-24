"""CLI entry point for competitive analysis tool.

Multi-stage pipeline:
1. Research: Web research on both entities
2. Analysis: Apply analytical frameworks (Porter, SWOT)
3. Format: Generate audience-specific reports

Checkpointing: Each stage saves JSON, enabling resume from any point.
"""

import asyncio
from pathlib import Path

import click

from .stages.analysis import run_analysis_async
from .stages.format import run_format_async
from .stages.research import run_research_async


@click.command()
@click.argument("entity1")
@click.argument("entity2")
@click.option(
    "--output-dir",
    "-o",
    default="output",
    help="Output directory for all results",
    type=click.Path(),
)
@click.option(
    "--frameworks",
    "-f",
    default="porter,swot",
    help="Comma-separated frameworks to apply (porter,swot)",
)
@click.option(
    "--audiences",
    "-a",
    default="executive,pm",
    help="Comma-separated audiences for reports (executive,pm)",
)
@click.option(
    "--skip-research",
    is_flag=True,
    help="Skip research stage (requires existing research.json)",
)
@click.option(
    "--skip-analysis",
    is_flag=True,
    help="Skip analysis stage (requires existing analysis.json)",
)
def main(
    entity1: str,
    entity2: str,
    output_dir: str,
    frameworks: str,
    audiences: str,
    skip_research: bool,
    skip_analysis: bool,
):
    """Generate competitive analysis comparing two entities.

    Runs a multi-stage pipeline: Research → Analysis → Format

    Examples:
        # Full analysis with defaults
        python -m ai_working.competitive_analysis "Notion" "Obsidian"

        # Custom frameworks and audiences
        python -m ai_working.competitive_analysis "AWS" "Azure" -f porter -a executive

        # Resume from existing research
        python -m ai_working.competitive_analysis "Notion" "Obsidian" --skip-research
    """
    try:
        # Parse options
        output_path = Path(output_dir)
        framework_list = [f.strip() for f in frameworks.split(",")]
        audience_list = [a.strip() for a in audiences.split(",")]

        # Run async pipeline
        asyncio.run(
            run_pipeline(
                entity1,
                entity2,
                output_path,
                framework_list,
                audience_list,
                skip_research,
                skip_analysis,
            )
        )

        print(f"\n✅ Analysis complete! Results saved to {output_path}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


async def run_pipeline(
    entity1: str,
    entity2: str,
    output_dir: Path,
    frameworks: list[str],
    audiences: list[str],
    skip_research: bool,
    skip_analysis: bool,
):
    """Execute the multi-stage pipeline.

    Args:
        entity1: First company/product name
        entity2: Second company/product name
        output_dir: Directory for all output files
        frameworks: List of frameworks to apply
        audiences: List of audiences for reports
        skip_research: Skip research stage if True
        skip_analysis: Skip analysis stage if True
    """
    # Stage 1: Research
    if skip_research:
        print(f"⏭️  Skipping research stage (loading from {output_dir}/research.json)")
        from .models import ResearchResult

        research_json = (output_dir / "research.json").read_text()
        research_result = ResearchResult.model_validate_json(research_json)
    else:
        print(f"\n🔍 Stage 1: Researching {entity1} and {entity2}...")
        research_result = await run_research_async(entity1, entity2, output_dir)
        print(f"✓ Research complete (saved to {output_dir}/research.json)")

    # Stage 2: Analysis
    if skip_analysis:
        print(f"⏭️  Skipping analysis stage (loading from {output_dir}/analysis.json)")
        from .models import AnalysisResult

        analysis_json = (output_dir / "analysis.json").read_text()
        analysis_result = AnalysisResult.model_validate_json(analysis_json)
    else:
        print(f"\n📊 Stage 2: Applying frameworks ({', '.join(frameworks)})...")
        analysis_result = await run_analysis_async(research_result, frameworks, output_dir, entity1, entity2)
        print(f"✓ Analysis complete (saved to {output_dir}/analysis.json)")

    # Stage 3: Format
    print(f"\n📝 Stage 3: Generating reports for audiences ({', '.join(audiences)})...")
    for audience in audiences:
        await run_format_async(analysis_result, audience, output_dir, entity1, entity2)
        print(f"✓ {audience.capitalize()} report (saved to {output_dir}/{audience}_report.md)")


if __name__ == "__main__":
    main()
