"""
Click-based CLI interface for the ideas management system.

Provides command-line access to all ideas operations following
Amplifier's conventions and patterns.
"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from amplifier.ideas.models import Goal
from amplifier.ideas.models import Idea
from amplifier.ideas.storage import IdeasStorage
from amplifier.ideas.storage import get_default_ideas_file

console = Console()


@click.group()
@click.option(
    "--file", "-f", "ideas_file", type=click.Path(), help="Path to ideas YAML file (default: ~/amplifier/ideas.yaml)"
)
@click.pass_context
def ideas(ctx: click.Context, ideas_file: str | None) -> None:
    """
    Amplifier Ideas Management System

    Manage shared project ideas with goals, assignments, and AI-powered operations.
    """
    ctx.ensure_object(dict)

    # Determine ideas file path
    if ideas_file:
        ctx.obj["ideas_file"] = Path(ideas_file)
    else:
        ctx.obj["ideas_file"] = get_default_ideas_file()

    ctx.obj["storage"] = IdeasStorage(ctx.obj["ideas_file"])


@ideas.command()
@click.argument("title")
@click.option("--description", "-d", default="", help="Idea description")
@click.option("--assignee", "-a", help="Assign to user")
@click.option("--priority", "-p", type=click.Choice(["high", "medium", "low"]), default="medium", help="Idea priority")
@click.option("--themes", "-t", multiple=True, help="Themes/tags (can use multiple times)")
@click.option("--notes", "-n", help="Additional notes")
@click.pass_context
def add(
    ctx: click.Context,
    title: str,
    description: str,
    assignee: str | None,
    priority: str,
    themes: tuple[str],
    notes: str | None,
) -> None:
    """Add a new idea to the collection"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    # Create new idea
    idea = Idea(title=title, description=description, themes=list(themes), priority=priority, notes=notes)

    # Add to document
    doc.add_idea(idea)

    # Assign if specified
    if assignee:
        doc.assign_idea(idea.id, assignee)

    # Save
    storage.save(doc)

    console.print(f"✅ Added idea: [bold]{title}[/bold]")
    if assignee:
        console.print(f"   Assigned to: {assignee}")
    console.print(f"   ID: {idea.id}")


@ideas.command(name="list")
@click.option("--user", "-u", help="Filter by assigned user")
@click.option("--unassigned", is_flag=True, help="Show only unassigned ideas")
@click.option("--priority", "-p", type=click.Choice(["high", "medium", "low"]), help="Filter by priority")
@click.option("--theme", "-t", help="Filter by theme")
@click.option("--limit", "-l", type=int, default=20, help="Limit number of results")
@click.pass_context
def list_ideas(
    ctx: click.Context, user: str | None, unassigned: bool, priority: str | None, theme: str | None, limit: int
) -> None:
    """List ideas with optional filters"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    # Apply filters
    if user:
        ideas_list = doc.get_user_queue(user)
        title = f"Ideas assigned to {user}"
    elif unassigned:
        ideas_list = doc.get_unassigned()
        title = "Unassigned ideas"
    else:
        ideas_list = doc.ideas
        title = "All ideas"

    if priority:
        ideas_list = [i for i in ideas_list if i.priority == priority]

    if theme:
        ideas_list = [i for i in ideas_list if theme.lower() in [t.lower() for t in i.themes]]

    # Apply limit
    ideas_list = ideas_list[:limit]

    if not ideas_list:
        console.print("No ideas found matching criteria")
        return

    # Create table
    table = Table(title=title)
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Assignee")
    table.add_column("Priority")
    table.add_column("Themes", style="dim")

    for idea in ideas_list:
        assignee = idea.assignee or "[dim]unassigned[/dim]"
        priority_style = {"high": "[red]high[/red]", "medium": "[yellow]medium[/yellow]", "low": "[green]low[/green]"}
        priority_text = priority_style.get(idea.priority, idea.priority)
        themes_text = ", ".join(idea.themes) if idea.themes else ""

        table.add_row(idea.id, idea.title, assignee, priority_text, themes_text)

    console.print(table)
    console.print(f"\nShowing {len(ideas_list)} ideas")


@ideas.command()
@click.argument("idea_id")
@click.argument("assignee")
@click.pass_context
def assign(ctx: click.Context, idea_id: str, assignee: str) -> None:
    """Assign an idea to a user"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    if doc.assign_idea(idea_id, assignee):
        storage.save(doc)
        idea = doc.find_idea(idea_id)
        console.print(f"✅ Assigned '[bold]{idea.title}[/bold]' to {assignee}")
    else:
        console.print(f"❌ Idea not found: {idea_id}", err=True)
        sys.exit(1)


@ideas.command()
@click.argument("idea_id")
@click.pass_context
def remove(ctx: click.Context, idea_id: str) -> None:
    """Remove an idea from the collection"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    idea = doc.find_idea(idea_id)
    if not idea:
        console.print(f"❌ Idea not found: {idea_id}", err=True)
        sys.exit(1)

    if doc.remove_idea(idea_id):
        storage.save(doc)
        console.print(f"✅ Removed idea: [bold]{idea.title}[/bold]")
    else:
        console.print(f"❌ Failed to remove idea: {idea_id}", err=True)
        sys.exit(1)


@ideas.command()
@click.argument("idea_id")
@click.pass_context
def show(ctx: click.Context, idea_id: str) -> None:
    """Show detailed information about an idea"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    idea = doc.find_idea(idea_id)
    if not idea:
        console.print(f"❌ Idea not found: {idea_id}", err=True)
        sys.exit(1)

    # Display detailed info
    console.print(f"\n[bold]{idea.title}[/bold]")
    console.print(f"ID: {idea.id}")
    console.print(f"Priority: {idea.priority}")
    console.print(f"Assignee: {idea.assignee or 'unassigned'}")
    console.print(f"Created: {idea.created.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"Modified: {idea.modified.strftime('%Y-%m-%d %H:%M')}")

    if idea.themes:
        console.print(f"Themes: {', '.join(idea.themes)}")

    if idea.description:
        console.print(f"\nDescription:\n{idea.description}")

    if idea.notes:
        console.print(f"\nNotes:\n{idea.notes}")


@ideas.command("add-goal")
@click.argument("description")
@click.option("--priority", "-p", type=int, default=1, help="Goal priority (lower = higher)")
@click.pass_context
def add_goal(ctx: click.Context, description: str, priority: int) -> None:
    """Add a new goal for idea prioritization"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    goal = Goal(description=description, priority=priority)
    doc.add_goal(goal)

    storage.save(doc)
    console.print(f"✅ Added goal: [bold]{description}[/bold]")
    console.print(f"   Priority: {priority}")
    console.print(f"   ID: {goal.id}")


@ideas.command()
@click.pass_context
def goals(ctx: click.Context) -> None:
    """List all active goals"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    active_goals = doc.get_active_goals()

    if not active_goals:
        console.print("No active goals")
        return

    table = Table(title="Active Goals")
    table.add_column("Priority", style="bold")
    table.add_column("Description")
    table.add_column("Created")

    for goal in active_goals:
        table.add_row(str(goal.priority), goal.description, goal.created.strftime("%Y-%m-%d"))

    console.print(table)


@ideas.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show overall status of ideas collection"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    # Gather statistics
    total_ideas = len(doc.ideas)
    assigned = len([i for i in doc.ideas if i.is_assigned()])
    unassigned = len(doc.get_unassigned())

    high_priority = len(doc.get_by_priority("high"))
    medium_priority = len(doc.get_by_priority("medium"))
    low_priority = len(doc.get_by_priority("low"))

    # Get user assignments
    users = {}
    for idea in doc.ideas:
        if idea.assignee:
            users[idea.assignee] = users.get(idea.assignee, 0) + 1

    console.print("\n[bold]Ideas Collection Status[/bold]")
    console.print(f"File: {ctx.obj['ideas_file']}")
    console.print(f"Last modified: {doc.metadata.last_modified.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"By: {doc.metadata.last_modified_by}")

    console.print("\n📊 [bold]Statistics[/bold]")
    console.print(f"Total ideas: {total_ideas}")
    console.print(f"Assigned: {assigned}")
    console.print(f"Unassigned: {unassigned}")
    console.print(f"Active goals: {len(doc.get_active_goals())}")

    console.print("\n🎯 [bold]Priority Breakdown[/bold]")
    console.print(f"High: {high_priority}")
    console.print(f"Medium: {medium_priority}")
    console.print(f"Low: {low_priority}")

    if users:
        console.print("\n👥 [bold]Assignments[/bold]")
        for user, count in sorted(users.items()):
            console.print(f"{user}: {count} ideas")


@ideas.command("init")
@click.option("--sample", is_flag=True, help="Create with sample data")
@click.pass_context
def init_file(ctx: click.Context, sample: bool) -> None:
    """Initialize a new ideas file"""

    ideas_file: Path = ctx.obj["ideas_file"]

    if ideas_file.exists():
        console.print(f"❌ Ideas file already exists: {ideas_file}")
        console.print("Use --file to specify a different location")
        sys.exit(1)

    storage: IdeasStorage = ctx.obj["storage"]

    if sample:
        from amplifier.ideas.storage import create_sample_document

        doc = create_sample_document()
        console.print("✅ Created ideas file with sample data")
    else:
        doc = storage.load()  # Creates empty document
        console.print("✅ Created empty ideas file")

    storage.save(doc)
    console.print(f"📁 Location: {ideas_file}")


@ideas.command()
@click.pass_context
def reorder(ctx: click.Context) -> None:
    """Reorder ideas based on active goals using AI"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    active_goals = doc.get_active_goals()
    if not active_goals:
        console.print("❌ No active goals found. Add goals first with 'add-goal'")
        sys.exit(1)

    if not doc.ideas:
        console.print("❌ No ideas to reorder")
        sys.exit(1)

    console.print(f"🎯 Reordering {len(doc.ideas)} ideas based on {len(active_goals)} goals...")

    # Import and run the operation
    from amplifier.ideas.operations import reorder_ideas_by_goals

    async def run_reorder():
        return await reorder_ideas_by_goals(doc.ideas, active_goals)

    reordered_ideas = asyncio.run(run_reorder())

    # Update the document with new order
    doc.ideas = reordered_ideas
    storage.save(doc, "ai-reorder")

    console.print("✅ Ideas reordered based on goal alignment")
    console.print("Use 'list' to see the new order")


@ideas.command()
@click.pass_context
def themes(ctx: click.Context) -> None:
    """Detect common themes across ideas using AI"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    if not doc.ideas:
        console.print("❌ No ideas to analyze")
        sys.exit(1)

    console.print(f"🔍 Detecting themes in {len(doc.ideas)} ideas...")

    # Import and run the operation

    from amplifier.ideas.operations import detect_idea_themes

    async def run_detection():
        return await detect_idea_themes(doc.ideas)

    theme_groups = asyncio.run(run_detection())

    if not theme_groups:
        console.print("No common themes detected")
        return

    # Display themes
    table = Table(title="Detected Themes")
    table.add_column("Theme", style="bold")
    table.add_column("Description")
    table.add_column("Ideas", style="dim")

    for theme in theme_groups:
        idea_count = f"{len(theme.idea_ids)} ideas"
        table.add_row(theme.name, theme.description, idea_count)

    console.print(table)


@ideas.command()
@click.argument("idea_id")
@click.pass_context
def similar(ctx: click.Context, idea_id: str) -> None:
    """Find ideas similar to the specified idea using AI"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    target_idea = doc.find_idea(idea_id)
    if not target_idea:
        console.print(f"❌ Idea not found: {idea_id}", err=True)
        sys.exit(1)

    console.print(f"🔎 Finding ideas similar to: [bold]{target_idea.title}[/bold]")

    # Import and run the operation
    from amplifier.ideas.operations import find_similar_to_idea

    async def run_similarity():
        return await find_similar_to_idea(target_idea, doc.ideas)

    similar_ideas = asyncio.run(run_similarity())

    if not similar_ideas:
        console.print("No similar ideas found")
        return

    # Display similar ideas
    table = Table(title=f"Ideas similar to: {target_idea.title}")
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Themes", style="dim")

    for idea in similar_ideas:
        themes_text = ", ".join(idea.themes) if idea.themes else ""
        table.add_row(idea.id, idea.title, themes_text)

    console.print(table)


@ideas.command()
@click.pass_context
def optimize(ctx: click.Context) -> None:
    """Optimize idea order for maximum leverage using AI"""

    storage: IdeasStorage = ctx.obj["storage"]
    doc = storage.load()

    if not doc.ideas:
        console.print("❌ No ideas to optimize")
        sys.exit(1)

    console.print(f"⚡ Optimizing {len(doc.ideas)} ideas for maximum leverage...")

    # Import and run the operation
    from amplifier.ideas.operations import optimize_ideas_for_leverage

    async def run_optimization():
        return await optimize_ideas_for_leverage(doc.ideas)

    optimized_ideas = asyncio.run(run_optimization())

    # Update the document with new order
    doc.ideas = optimized_ideas
    storage.save(doc, "ai-optimize")

    console.print("✅ Ideas optimized for leverage")
    console.print("Use 'list' to see the optimized order")


if __name__ == "__main__":
    ideas()
