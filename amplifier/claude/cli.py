"""
CLI commands for Claude integration features.
"""

from datetime import UTC
from datetime import datetime

import click

from amplifier.claude.session_awareness import SessionAwareness


@click.group("claude")
def claude_group():
    """Claude Code integration features."""
    pass


@claude_group.command("status")
def session_status():
    """Show status of active Claude sessions."""
    sa = SessionAwareness()
    status = sa.get_status()

    click.echo("\n🔄 Claude Session Awareness Status")
    click.echo("=" * 40)
    click.echo(f"Current Session: {status['current_session']}")
    click.echo(f"Active Sessions: {status['active_sessions']}")

    if status["sessions"]:
        click.echo("\n📊 Active Sessions:")
        for session in status["sessions"]:
            click.echo(
                f"  • {session['id']} (PID: {session['pid']}) "
                f"- {session['duration_minutes']}min "
                f"- Last: {session['last_activity'] or 'No activity'}"
            )

    if status["recent_activity"]:
        click.echo("\n📝 Recent Activity:")
        for activity in status["recent_activity"][:5]:
            click.echo(f"  • [{activity['session']}] {activity['action']} ({activity['ago_seconds']}s ago)")
            if activity["details"]:
                click.echo(f"    → {activity['details']}")


@claude_group.command("track")
@click.argument("action")
@click.option("--details", "-d", help="Additional details about the action")
def track_activity(action: str, details: str | None):
    """Track an activity for the current session.

    Example:
        amplifier claude track "Working on feature X" -d "Adding session awareness"
    """
    sa = SessionAwareness()
    sa.register_activity(action, details)
    click.echo(f"✅ Tracked: {action}")


@claude_group.command("broadcast")
@click.argument("message")
def broadcast_message(message: str):
    """Broadcast a message to all active sessions.

    Example:
        amplifier claude broadcast "Starting deployment - please pause edits"
    """
    sa = SessionAwareness()
    sa.broadcast_message(message)
    click.echo(f"📢 Broadcast sent: {message}")


@claude_group.command("activity")
@click.option("--limit", "-n", default=20, help="Number of activities to show")
def show_activity(limit: int):
    """Show recent activity across all sessions."""
    sa = SessionAwareness()
    activities = sa.get_recent_activity(limit)

    if not activities:
        click.echo("No recent activity found.")
        return

    click.echo("\n📜 Recent Activity Log:")
    click.echo("=" * 40)

    for activity in activities:
        timestamp = datetime.fromtimestamp(activity.timestamp, UTC).strftime("%H:%M:%S")
        click.echo(f"[{timestamp}] {activity.session_id}: {activity.action}")
        if activity.details:
            click.echo(f"  → {activity.details}")


# Register the command group
def register_commands(cli):
    """Register Claude commands with the main CLI."""
    cli.add_command(claude_group)
