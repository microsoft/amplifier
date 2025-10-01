"""CLI commands for knowledge management."""

import json

import click

from amplifier.knowledge.manager import get_knowledge_manager


@click.group()
def knowledge():
    """Knowledge management commands."""
    pass


@knowledge.command()
def status():
    """Show knowledge system status."""
    manager = get_knowledge_manager()
    summary = manager.get_summary()

    click.echo("📚 Knowledge System Status")
    click.echo("=" * 60)
    click.echo(f"Status: {'✅ Loaded' if summary['loaded'] else '❌ Not Loaded'}")
    click.echo()
    click.echo("Statistics:")
    click.echo(f"  • Total concepts: {summary['total_concepts']}")
    click.echo(f"  • Total patterns: {summary['total_patterns']}")
    click.echo(f"  • Total insights: {summary['total_insights']}")
    click.echo(f"  • Knowledge graph: {summary['graph_nodes']} nodes, {summary['graph_edges']} edges")

    if summary["top_concepts"]:
        click.echo()
        click.echo("Top Concepts:")
        for concept in summary["top_concepts"]:
            click.echo(f"  • {concept['name']}: {concept['frequency']} occurrences")


@knowledge.command()
@click.argument("query")
def search(query: str):
    """Search knowledge for concepts."""
    manager = get_knowledge_manager()
    results = manager.search_concepts(query)

    if not results:
        click.echo(f"❌ No concepts found matching '{query}'")
        return

    click.echo(f"🔍 Found {len(results)} concepts matching '{query}'")
    click.echo()
    for concept in results[:10]:
        click.echo(f"• {concept['name']}")
        click.echo(f"  Frequency: {concept['frequency']}")
        if concept.get("principle_numbers"):
            principles = concept["principle_numbers"][:5]
            click.echo(f"  Principles: {', '.join(f'#{p}' for p in principles)}")
        if concept.get("context_samples"):
            sample = concept["context_samples"][0]
            if len(sample) > 80:
                sample = sample[:77] + "..."
            click.echo(f'  Context: "{sample}"')
        click.echo()


@knowledge.command()
@click.argument("context")
def recommend(context: str):
    """Get knowledge recommendations for a context."""
    manager = get_knowledge_manager()
    recommendations = manager.get_recommendations_for_context(context)

    if not recommendations:
        click.echo(f"❌ No recommendations found for '{context}'")
        return

    click.echo(f"💡 Recommendations for: {context}")
    click.echo("=" * 60)

    for rec in recommendations:
        click.echo(f"\n{rec['title']}:")
        if rec.get("items"):
            for item in rec["items"]:
                click.echo(f"  • {item}")
        if rec.get("principles"):
            principles = rec["principles"][:5]
            click.echo(f"  See principles: {', '.join(f'#{p}' for p in principles)}")


@knowledge.command()
def patterns():
    """Show identified patterns."""
    manager = get_knowledge_manager()
    patterns = manager.get_patterns()

    if not patterns:
        click.echo("❌ No patterns loaded")
        return

    click.echo("🎯 Identified Patterns")
    click.echo("=" * 60)

    for pattern in patterns:
        click.echo(f"\n{pattern['name']}")
        if pattern.get("description"):
            click.echo(f"  {pattern['description']}")
        if pattern.get("confidence"):
            click.echo(f"  Confidence: {pattern['confidence']}%")
        if pattern.get("principles"):
            principles = pattern["principles"][:5]
            click.echo(f"  Principles: {', '.join(f'#{p}' for p in principles)}")


@knowledge.command()
def insights():
    """Show strategic insights."""
    manager = get_knowledge_manager()
    insights = manager.get_insights()

    if not insights:
        click.echo("❌ No insights loaded")
        return

    click.echo("💡 Strategic Insights")
    click.echo("=" * 60)

    for i, insight in enumerate(insights, 1):
        click.echo(f"\n{i}. {insight['title']}")
        if insight.get("description"):
            click.echo(f"   {insight['description']}")
        if insight.get("recommendations"):
            click.echo("   Recommendations:")
            for rec in insight["recommendations"][:3]:
                click.echo(f"   • {rec}")


@knowledge.command()
def reload():
    """Reload knowledge from disk."""
    manager = get_knowledge_manager()
    click.echo("🔄 Reloading knowledge from disk...")
    manager.reload()
    summary = manager.get_summary()
    click.echo(f"✅ Reloaded: {summary['total_concepts']} concepts, {summary['total_patterns']} patterns")


@knowledge.command()
@click.option("--output", "-o", help="Output file for export")
def export(output: str):
    """Export knowledge to JSON file."""
    if not output:
        click.echo("❌ Please provide an output file with -o/--output")
        return

    manager = get_knowledge_manager()

    # Build export data
    export_data = {
        "summary": manager.get_summary(),
        "concepts": manager.get_concepts(),
        "patterns": manager.get_patterns(),
        "insights": manager.get_insights(),
        "knowledge_graph": manager.get_knowledge_graph(),
    }

    # Write to file
    with open(output, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    click.echo(f"✅ Knowledge exported to {output}")
