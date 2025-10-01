"""CLI commands for working with AI-First Principles."""

import json
import logging

import click

from amplifier.principles import PrincipleLoader
from amplifier.principles import PrincipleSearcher
from amplifier.principles import PrincipleSynthesizer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@click.group()
def principles():
    """AI-First Principles knowledge and synthesis tools."""
    pass


@principles.command()
@click.option("--category", help="Filter by category (people/process/technology/governance)")
@click.option("--complete", is_flag=True, help="Show only complete specifications")
@click.option("--format", type=click.Choice(["simple", "detailed", "json"]), default="simple")
def list(category: str, complete: bool, format: str):
    """List all AI-First principles."""
    loader = PrincipleLoader()

    if category:
        principles = loader.get_by_category(category)
    else:
        principles = loader.get_all_principles()

    if complete:
        # Filter for complete specifications
        principles = [p for p in principles if len(p.examples) >= 5 and len(p.implementation_approaches) >= 6]

    if format == "json":
        output = [p.to_dict() for p in principles]
        click.echo(json.dumps(output, indent=2))
    elif format == "detailed":
        for p in principles:
            click.echo(f"#{p.number:02d} - {p.name}")
            click.echo(f"  Category: {p.category}")
            click.echo(f"  Title: {p.title}")
            if p.description:
                desc_preview = p.description[:100] + "..." if len(p.description) > 100 else p.description
                click.echo(f"  Description: {desc_preview}")
            click.echo(f"  Related: {', '.join(f'#{n}' for n in p.related_principles[:5])}")
            click.echo(f"  Examples: {len(p.examples)}, Approaches: {len(p.implementation_approaches)}")
            click.echo()
    else:
        click.echo(f"📋 Found {len(principles)} principles")
        click.echo()
        for p in principles:
            status = "✅" if len(p.examples) >= 5 else "⚠️"
            click.echo(f"{status} #{p.number:02d} - {p.name} ({p.category})")


@principles.command()
@click.argument("keyword")
@click.option("--context", type=int, default=2, help="Lines of context to show")
def search(keyword: str, context: int):
    """Search principles by keyword."""
    loader = PrincipleLoader()
    searcher = PrincipleSearcher(loader)

    results = searcher.search(query=keyword)

    click.echo(f"🔍 Found {len(results)} principles containing '{keyword}'")
    click.echo()

    for principle in results:
        click.echo(f"#{principle.number:02d} - {principle.name} ({principle.category})")

        # Show context where keyword appears
        if principle.content and context > 0:
            lines = principle.content.split("\n")
            keyword_lower = keyword.lower()

            for i, line in enumerate(lines):
                if keyword_lower in line.lower():
                    # Show context lines
                    start = max(0, i - context)
                    end = min(len(lines), i + context + 1)

                    click.echo("  ---")
                    for j in range(start, end):
                        prefix = "  > " if j == i else "    "
                        click.echo(f"{prefix}{lines[j][:80]}")
                    break
        click.echo()


@principles.command()
@click.argument("principle_number", type=int)
def show(principle_number: int):
    """Show detailed information about a specific principle."""
    loader = PrincipleLoader()
    principle = loader.get_principle(principle_number)

    if not principle:
        click.echo(f"❌ Principle #{principle_number} not found")
        return

    click.echo(f"#{principle.number:02d} - {principle.title}")
    click.echo("=" * 60)
    click.echo(f"Category: {principle.category}")
    click.echo(f"Name: {principle.name}")
    click.echo()

    if principle.description:
        click.echo("Description:")
        click.echo(principle.description)
        click.echo()

    click.echo(f"Related Principles: {', '.join(f'#{n}' for n in principle.related_principles)}")
    click.echo(f"Examples: {len(principle.examples)}")
    click.echo(f"Implementation Approaches: {len(principle.implementation_approaches)}")
    click.echo(f"Common Pitfalls: {len(principle.common_pitfalls)}")
    click.echo(f"Tools Mentioned: {len(principle.tools)}")
    click.echo(f"Checklist Items: {len(principle.checklist)}")

    # Show related principles with names
    if principle.related_principles:
        click.echo()
        click.echo("Related Principles:")
        for num in principle.related_principles[:5]:
            related = loader.get_principle(num)
            if related:
                click.echo(f"  #{related.number:02d} - {related.name}")


@principles.command()
@click.argument("task_description")
@click.option("--format", type=click.Choice(["summary", "detailed", "json"]), default="summary")
def synthesize(task_description: str, format: str):
    """Synthesize relevant principles for a task."""
    loader = PrincipleLoader()
    synthesizer = PrincipleSynthesizer(loader)

    result = synthesizer.synthesize_for_task(task_description)

    if format == "json":
        click.echo(json.dumps(result, indent=2))
    elif format == "detailed":
        click.echo(f"Task: {task_description}")
        click.echo("=" * 60)
        click.echo(f"Keywords: {', '.join(result['keywords'])}")
        click.echo()

        click.echo("Relevant Principles by Category:")
        for category, nums in result["by_category"].items():
            click.echo(f"  {category}: {', '.join(f'#{n}' for n in nums)}")
        click.echo()

        click.echo("Recommendations:")
        for i, rec in enumerate(result["recommendations"], 1):
            click.echo(f"  {i}. {rec}")
        click.echo()

        click.echo(f"Implementation Order: {', '.join(f'#{n}' for n in result['implementation_order'][:10])}")
    else:
        click.echo(f"🎯 Synthesis for: {task_description}")
        click.echo()
        click.echo(f"Found {len(result['relevant_principles'])} relevant principles")
        click.echo()

        # Show top 5 principles
        for p_dict in result["relevant_principles"][:5]:
            click.echo(f"  #{p_dict['number']:02d} - {p_dict['name']} ({p_dict['category']})")

        if result["recommendations"]:
            click.echo()
            click.echo("Key Recommendations:")
            for rec in result["recommendations"][:3]:
                click.echo(f"  • {rec}")


@principles.command()
@click.argument("principle_numbers", type=int, nargs=-1)
def roadmap(principle_numbers: tuple[int]):
    """Generate implementation roadmap for principles."""
    if not principle_numbers:
        click.echo("❌ Please provide principle numbers to create a roadmap")
        return

    loader = PrincipleLoader()
    synthesizer = PrincipleSynthesizer(loader)

    roadmap = synthesizer.generate_implementation_roadmap(list(principle_numbers))

    click.echo(f"📍 Implementation Roadmap for {roadmap['total_principles']} principles")
    click.echo("=" * 60)

    for phase in roadmap["phases"]:
        click.echo(f"\n{phase['name'].upper()} PHASE")
        click.echo(f"Focus: {phase['focus']}")
        click.echo("Principles:")
        for p_dict in phase["principles"]:
            click.echo(f"  #{p_dict['number']:02d} - {p_dict['name']}")
        click.echo("Success Criteria:")
        for criterion in phase["success_criteria"]:
            click.echo(f"  ✓ {criterion}")

    timeline = roadmap["estimated_timeline"]
    click.echo()
    click.echo(f"Estimated Timeline: {timeline['total_weeks']} weeks ({timeline['total_months']} months)")
    click.echo(f"Parallel Potential: {timeline['parallel_potential']} weeks")


@principles.command()
@click.argument("principle_numbers", type=int, nargs=-1)
@click.option("--output", help="Output file for coverage report")
def coverage(principle_numbers: tuple[int], output: str):
    """Analyze principle coverage in a project."""
    loader = PrincipleLoader()
    synthesizer = PrincipleSynthesizer(loader)

    if not principle_numbers:
        # If no principles provided, analyze zero coverage
        principle_numbers = []

    coverage = synthesizer.analyze_principle_coverage(list(principle_numbers))

    click.echo("📊 Principle Coverage Analysis")
    click.echo("=" * 60)
    click.echo(f"Total Principles: {coverage['total_principles']}")
    click.echo(f"Principles Used: {coverage['principles_used']}")
    click.echo(f"Coverage: {coverage['coverage_percentage']:.1f}%")
    click.echo()

    click.echo("By Category:")
    for category, stats in coverage["by_category"].items():
        click.echo(f"  {category}: {stats['used']}/{stats['total']} ({stats['percentage']:.1f}%)")
        if stats["missing"] and len(stats["missing"]) <= 3:
            missing_str = ", ".join(f"#{n}" for n in stats["missing"])
            click.echo(f"    Missing: {missing_str}")

    if coverage["missing_critical"]:
        click.echo()
        click.echo("⚠️  Missing Critical Principles:")
        for p in coverage["missing_critical"]:
            click.echo(f"  #{p['number']:02d} - {p['name']} ({p['category']})")

    if coverage["underutilized_categories"]:
        click.echo()
        click.echo(f"⚠️  Underutilized Categories: {', '.join(coverage['underutilized_categories'])}")

    if output:
        with open(output, "w") as f:
            json.dump(coverage, f, indent=2)
        click.echo(f"\n📁 Report saved to: {output}")


@principles.command()
@click.argument("principle_number", type=int)
@click.option("--depth", type=int, default=2, help="Depth of connections to analyze")
def connections(principle_number: int, depth: int):
    """Analyze connections for a principle."""
    loader = PrincipleLoader()
    searcher = PrincipleSearcher(loader)

    analysis = searcher.analyze_connections(principle_number)

    if not analysis:
        click.echo(f"❌ Principle #{principle_number} not found")
        return

    principle = analysis["principle"]
    click.echo(f"🔗 Connections for #{principle['number']:02d} - {principle['name']}")
    click.echo("=" * 60)

    click.echo(f"Direct Relations: {', '.join(f'#{n}' for n in analysis['direct_relations'])}")
    click.echo(f"Reverse Relations: {', '.join(f'#{n}' for n in analysis['reverse_relations'])}")
    click.echo()

    click.echo("Connection Strength:")
    sorted_connections = sorted(analysis["connection_strength"].items(), key=lambda x: x[1], reverse=True)
    for num, strength in sorted_connections[:5]:
        p = loader.get_principle(num)
        if p:
            click.echo(f"  #{num:02d} - {p.name}: {strength:.1f}")


@principles.command()
def stats():
    """Show statistics about the principles library."""
    loader = PrincipleLoader()
    searcher = PrincipleSearcher(loader)

    stats = loader.get_statistics()
    report = searcher.generate_summary_report()

    click.echo("📈 AI-First Principles Statistics")
    click.echo("=" * 60)

    click.echo(f"Total Principles: {stats['total']}")
    click.echo(f"Complete Specifications: {stats['complete']}")
    click.echo()

    click.echo("By Category:")
    for category, count in stats["by_category"].items():
        click.echo(f"  {category}: {count}")

    click.echo()
    click.echo("Coverage:")
    click.echo(f"  With Examples: {stats['with_examples']}")
    click.echo(f"  With Approaches: {stats['with_approaches']}")
    click.echo(f"  With Checklist: {stats['with_checklist']}")

    click.echo()
    click.echo("Most Connected Principles:")
    for p in report["most_connected"][:3]:
        click.echo(f"  #{p['number']:02d} - {p['name']}: {p['connections']} connections")

    click.echo()
    click.echo("Principle Clusters:")
    for cluster_name, members in report["clusters"].items():
        click.echo(f"  {cluster_name}: {', '.join(f'#{n}' for n in members[:5])}")


@principles.command()
@click.option("--output", "-o", help="Output file for knowledge extraction (JSON)")
@click.option("--report", "-r", help="Output file for synthesis report (Markdown)")
def extract_knowledge(output: str, report: str):
    """Extract comprehensive knowledge from all principles."""
    from pathlib import Path

    from amplifier.principles import PrincipleKnowledgeExtractor

    loader = PrincipleLoader()
    extractor = PrincipleKnowledgeExtractor(loader)

    click.echo("🧠 Extracting knowledge from AI-First Principles...")
    click.echo("=" * 60)

    # Extract knowledge
    knowledge = extractor.extract_all_knowledge()
    stats = knowledge["statistics"]

    click.echo(f"✅ Extracted {stats['total_concepts']} concepts")
    click.echo(f"✅ Identified {stats['total_patterns']} patterns")
    click.echo(f"✅ Generated {stats['total_insights']} insights")
    click.echo(f"✅ Built knowledge graph: {stats['graph_nodes']} nodes, {stats['graph_edges']} edges")
    click.echo()

    # Show top concepts
    click.echo("Top Concepts:")
    for concept in stats["top_concepts"]:
        click.echo(f"  • {concept['name']}: {concept['frequency']} occurrences")
    click.echo()

    # Save outputs if requested
    if output:
        output_path = Path(output)
        extractor.export_knowledge(output_path)
        click.echo(f"📁 Knowledge exported to: {output}")

    if report:
        report_path = Path(report)
        synthesis_report = extractor.generate_synthesis_report()
        report_path.write_text(synthesis_report)
        click.echo(f"📄 Report saved to: {report}")


@principles.command()
@click.argument("context")
def recommend(context: str):
    """Get recommendations based on context."""
    from amplifier.principles import PrincipleKnowledgeExtractor

    loader = PrincipleLoader()
    extractor = PrincipleKnowledgeExtractor(loader)

    # Extract knowledge first
    _ = extractor.extract_all_knowledge()

    # Get recommendations
    recommendations = extractor.get_recommendations_for_context(context)

    if not recommendations:
        click.echo(f"No specific recommendations found for: {context}")
        return

    click.echo(f"💡 Recommendations for: {context}")
    click.echo("=" * 60)

    for rec in recommendations:
        click.echo(f"\n{rec['title']}:")

        if rec["type"] == "concepts":
            click.echo(f"  Relevant concepts: {', '.join(rec['items'])}")
            click.echo(f"  See principles: {', '.join(f'#{p}' for p in rec['principles'])}")

        elif rec["type"] == "patterns":
            click.echo(f"  Applicable patterns: {', '.join(rec['items'])}")
            click.echo(f"  See principles: {', '.join(f'#{p}' for p in rec['principles'])}")

        elif rec["type"] == "insight":
            click.echo(f"  {rec['description']}")
            click.echo("  Recommendations:")
            for r in rec["recommendations"]:
                click.echo(f"    • {r}")


@principles.command()
def knowledge_report():
    """Generate and display a comprehensive knowledge synthesis report."""
    from amplifier.principles import PrincipleKnowledgeExtractor

    loader = PrincipleLoader()
    extractor = PrincipleKnowledgeExtractor(loader)

    click.echo("🧠 Generating Knowledge Synthesis Report...")
    click.echo("=" * 60)

    # Extract knowledge
    _ = extractor.extract_all_knowledge()

    # Generate and display report
    report = extractor.generate_synthesis_report()
    click.echo(report)
