"""
Smart Decomposer CLI implementation.

Provides commands for decomposing goals, assigning agents, and orchestrating execution.
"""

import argparse
import asyncio
import logging
import sys

from amplifier.planner import Project
from amplifier.planner import TaskState
from amplifier.planner import load_project
from amplifier.planner import save_project
from amplifier.planner.agent_mapper import assign_agent
from amplifier.planner.decomposer import ProjectContext
from amplifier.planner.decomposer import decompose_goal
from amplifier.planner.orchestrator import orchestrate_execution

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Projects are stored by the planner module in data/planner/projects/


def cmd_decompose(args) -> None:
    """Decompose a goal into tasks."""
    # Create or load project
    if args.project_id:
        try:
            project = load_project(args.project_id)
            logger.info(f"📂 Loaded existing project: {project.name}")
        except (FileNotFoundError, KeyError):
            project = Project(id=args.project_id, name=args.project_name or args.project_id)
            logger.info(f"✨ Created new project: {project.name}")
    else:
        import uuid

        project_id = str(uuid.uuid4())[:8]
        project = Project(id=project_id, name=args.project_name or f"Project-{project_id}")
        logger.info(f"✨ Created new project: {project.name} (ID: {project_id})")

    # Create context for decomposition
    context = ProjectContext(project=project, max_depth=args.max_depth, min_tasks=2)

    logger.info(f"🧠 Decomposing goal: {args.goal}")

    # Run async decomposition
    try:
        tasks = asyncio.run(decompose_goal(args.goal, context))

        # Add tasks to project
        for task in tasks:
            project.add_task(task)

        # Save project
        save_project(project)

        logger.info(f"✅ Generated {len(tasks)} tasks")
        logger.info(f"📁 Project saved with ID: {project.id}")

        # Display task hierarchy
        if args.verbose:
            logger.info("\n📋 Task Hierarchy:")
            for task in tasks[:5]:  # Show first 5
                logger.info(f"  • {task.title}")
                if task.description:
                    logger.info(f"    {task.description[:100]}...")

        logger.info(f"\n💡 Next step: Assign agents with 'assign --project-id {project.id}'")

    except Exception as e:
        logger.error(f"❌ Decomposition failed: {e}")
        sys.exit(1)


def cmd_assign(args) -> None:
    """Assign agents to tasks."""
    try:
        # Load project
        project = load_project(args.project_id)
    except (FileNotFoundError, KeyError):
        logger.error(f"❌ Project not found: {args.project_id}")
        logger.error("   Run 'decompose' first to create a project")
        sys.exit(1)
    logger.info(f"📂 Loaded project: {project.name}")

    # Get available agents (hardcoded for now, could be made configurable)
    available_agents = [
        "zen-code-architect",
        "modular-builder",
        "bug-hunter",
        "test-coverage",
        "refactor-architect",
        "integration-specialist",
    ]

    if args.agents:
        # Use custom agent list if provided
        available_agents = args.agents.split(",")

    logger.info(f"🤖 Assigning agents to {len(project.tasks)} tasks")
    logger.info(f"   Available agents: {', '.join(available_agents)}")

    # Assign agents to each task
    assignments = {}
    for task in project.tasks.values():
        agent = assign_agent(task, available_agents)
        task.assigned_to = agent
        assignments[task.title] = agent

    # Save updated project
    save_project(project)

    logger.info("✅ Agent assignments complete")

    # Show assignments
    if args.verbose or len(assignments) <= 10:
        logger.info("\n📋 Task Assignments:")
        for title, agent in list(assignments.items())[:10]:
            logger.info(f"  • {title[:50]}... → {agent}")

    logger.info(f"\n💡 Next step: Execute with 'execute --project-id {project.id}'")


def cmd_execute(args) -> None:
    """Execute project tasks with orchestration."""
    try:
        # Load project
        project = load_project(args.project_id)
    except (FileNotFoundError, KeyError):
        logger.error(f"❌ Project not found: {args.project_id}")
        sys.exit(1)
    logger.info(f"📂 Loaded project: {project.name}")

    # Check if agents are assigned
    unassigned = [t for t in project.tasks.values() if not t.assigned_to]

    if unassigned:
        logger.warning(f"⚠️  {len(unassigned)} tasks have no agent assigned")
        logger.warning("   Run 'assign' first to assign agents")
        if not args.force:
            sys.exit(1)

    logger.info(f"🚀 Executing {len(project.tasks)} tasks")

    if args.dry_run:
        logger.info("   🔍 DRY RUN - No actual execution")

    # Run orchestration
    try:
        results = asyncio.run(orchestrate_execution(project, max_parallel=args.max_parallel))

        # Save updated project
        save_project(project)

        # Display results
        logger.info("\n✅ Execution complete")
        logger.info(f"   Total tasks: {results.total_tasks}")
        logger.info(f"   Completed: {results.completed_tasks}")
        logger.info(f"   Failed: {results.failed_tasks}")
        logger.info(f"   Skipped: {results.skipped_tasks}")

        if results.failed_tasks > 0 and args.verbose:
            logger.info("\n❌ Failed Tasks:")
            for task_id, result in results.task_results.items():
                if result.status == "failed":
                    task = project.tasks.get(task_id)
                    if task:
                        logger.info(f"  • {task.title}: {result.error}")

    except Exception as e:
        logger.error(f"❌ Execution failed: {e}")
        sys.exit(1)


def cmd_status(args) -> None:
    """Show project status and progress."""
    try:
        # Load project
        project = load_project(args.project_id)
    except (FileNotFoundError, KeyError):
        logger.error(f"❌ Project not found: {args.project_id}")
        logger.info("\nTip: Use 'decompose' to create a new project")
        sys.exit(1)

    logger.info(f"📊 Project Status: {project.name}")
    logger.info(f"   ID: {project.id}")
    logger.info(f"   Tasks: {len(project.tasks)}")

    # Count by state
    from collections import Counter

    states = Counter(task.state.value for task in project.tasks.values())

    logger.info("\n📈 Task States:")
    for state in TaskState:
        count = states.get(state.value, 0)
        if count > 0:
            icon = {
                "pending": "⏳",
                "ready": "✅",
                "in_progress": "🔄",
                "completed": "✔️",
                "failed": "❌",
                "blocked": "🚫",
            }.get(state.value, "•")
            logger.info(f"   {icon} {state.value}: {count}")

    # Show agent assignments
    agents = Counter(task.assigned_to or "unassigned" for task in project.tasks.values())

    if len(agents) > 1 or "unassigned" not in agents:
        logger.info("\n🤖 Agent Assignments:")
        for agent, count in agents.most_common():
            logger.info(f"   • {agent}: {count} tasks")

    # Show sample tasks
    if args.verbose:
        logger.info("\n📋 Sample Tasks:")
        for task in list(project.tasks.values())[:5]:
            agent = task.assigned_to or "unassigned"
            logger.info(f"   • [{task.state.value}] {task.title[:60]}... ({agent})")

    # Show next steps
    if states.get("pending", 0) > 0 and "unassigned" in agents:
        logger.info(f"\n💡 Next step: Assign agents with 'assign --project-id {project.id}'")
    elif states.get("ready", 0) > 0 or states.get("pending", 0) > 0:
        logger.info(f"\n💡 Next step: Execute with 'execute --project-id {project.id}'")
    elif states.get("completed", 0) == len(project.tasks):
        logger.info("\n✅ All tasks completed!")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="smart-decomposer", description="Intelligent task decomposition and orchestration"
    )

    # Add global options
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Decompose command
    decompose_parser = subparsers.add_parser("decompose", help="Decompose a goal into tasks")
    decompose_parser.add_argument("--goal", required=True, help="Goal to decompose")
    decompose_parser.add_argument("--project-id", help="Project ID (auto-generated if not provided)")
    decompose_parser.add_argument("--project-name", help="Project name")
    decompose_parser.add_argument("--max-depth", type=int, default=3, help="Maximum decomposition depth")
    decompose_parser.set_defaults(func=cmd_decompose)

    # Assign command
    assign_parser = subparsers.add_parser("assign", help="Assign agents to tasks")
    assign_parser.add_argument("--project-id", required=True, help="Project ID")
    assign_parser.add_argument("--agents", help="Comma-separated list of available agents")
    assign_parser.set_defaults(func=cmd_assign)

    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute tasks with orchestration")
    execute_parser.add_argument("--project-id", required=True, help="Project ID")
    execute_parser.add_argument("--max-parallel", type=int, default=5, help="Maximum parallel tasks")
    execute_parser.add_argument("--dry-run", action="store_true", help="Simulate execution without running")
    execute_parser.add_argument("--force", action="store_true", help="Execute even with unassigned tasks")
    execute_parser.set_defaults(func=cmd_execute)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument("--project-id", required=True, help="Project ID")
    status_parser.set_defaults(func=cmd_status)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
