"""
Task Tracker MCP Server for Codex.
Provides task management within Codex sessions (TodoWrite equivalent).
Enables creating, listing, updating, completing, and exporting tasks.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP

# Import base utilities
from ..base import (
    MCPLogger,
    AmplifierMCPServer,
    get_project_root,
    success_response,
    error_response,
)


class TaskTrackerServer(AmplifierMCPServer):
    """MCP server for task tracking and management"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-tasks")

        # Initialize base server
        super().__init__("task_tracker", mcp)

        # Set up task storage
        self.tasks_dir = Path(__file__).parent.parent.parent / "tasks"
        self.tasks_dir.mkdir(exist_ok=True)
        self.tasks_file = self.tasks_dir / "session_tasks.json"

        # Initialize tasks structure
        self._ensure_tasks_file()

        # Register tools
        self._register_tools()

    def _ensure_tasks_file(self):
        """Ensure tasks file exists with proper structure"""
        if not self.tasks_file.exists():
            initial_data = {
                "tasks": [],
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat()
                }
            }
            with open(self.tasks_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
            self.logger.info(f"Created new tasks file: {self.tasks_file}")

    def _load_tasks(self) -> Dict[str, Any]:
        """Load tasks from file"""
        try:
            with open(self.tasks_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
            return {"tasks": [], "metadata": {}}

    def _save_tasks(self, data: Dict[str, Any]):
        """Save tasks to file"""
        try:
            data["metadata"]["last_modified"] = datetime.now().isoformat()
            with open(self.tasks_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved {len(data['tasks'])} tasks")
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
            raise

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def create_task(
            title: str,
            description: Optional[str] = None,
            priority: str = "medium",
            category: Optional[str] = None
        ) -> Dict[str, Any]:
            """Create a new task

            Args:
                title: Task title/summary
                description: Detailed task description (optional)
                priority: Task priority ("low", "medium", "high", "critical")
                category: Task category for organization (optional)

            Returns:
                Created task with generated ID and metadata
            """
            try:
                self.logger.info(f"Creating task: {title}")

                # Validate priority
                valid_priorities = ["low", "medium", "high", "critical"]
                if priority not in valid_priorities:
                    return error_response(
                        f"Invalid priority: {priority}",
                        {"valid_priorities": valid_priorities}
                    )

                # Load current tasks
                data = self._load_tasks()

                # Create new task
                task = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "description": description or "",
                    "priority": priority,
                    "category": category,
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "completed_at": None
                }

                # Add to tasks list
                data["tasks"].append(task)

                # Save
                self._save_tasks(data)

                self.logger.info(f"Created task {task['id']}: {title}")
                return success_response(task, {
                    "total_tasks": len(data["tasks"])
                })

            except Exception as e:
                self.logger.exception("create_task failed", e)
                return error_response(f"Failed to create task: {str(e)}")

        @self.mcp.tool()
        async def list_tasks(
            filter_status: Optional[str] = None,
            filter_priority: Optional[str] = None,
            filter_category: Optional[str] = None,
            limit: Optional[int] = None
        ) -> Dict[str, Any]:
            """List tasks with optional filtering

            Args:
                filter_status: Filter by status ("pending", "in_progress", "completed", "cancelled")
                filter_priority: Filter by priority ("low", "medium", "high", "critical")
                filter_category: Filter by category
                limit: Maximum number of tasks to return

            Returns:
                List of tasks matching filters
            """
            try:
                self.logger.info(f"Listing tasks with filters: status={filter_status}, priority={filter_priority}, category={filter_category}")

                # Load tasks
                data = self._load_tasks()
                tasks = data["tasks"]

                # Apply filters
                if filter_status:
                    tasks = [t for t in tasks if t["status"] == filter_status]

                if filter_priority:
                    tasks = [t for t in tasks if t["priority"] == filter_priority]

                if filter_category:
                    tasks = [t for t in tasks if t.get("category") == filter_category]

                # Apply limit
                if limit and limit > 0:
                    tasks = tasks[:limit]

                # Sort by created_at descending
                tasks = sorted(tasks, key=lambda t: t["created_at"], reverse=True)

                self.logger.info(f"Returning {len(tasks)} tasks")
                return success_response(tasks, {
                    "total_filtered": len(tasks),
                    "total_all": len(data["tasks"]),
                    "filters_applied": {
                        "status": filter_status,
                        "priority": filter_priority,
                        "category": filter_category
                    }
                })

            except Exception as e:
                self.logger.exception("list_tasks failed", e)
                return error_response(f"Failed to list tasks: {str(e)}")

        @self.mcp.tool()
        async def update_task(
            task_id: str,
            title: Optional[str] = None,
            description: Optional[str] = None,
            priority: Optional[str] = None,
            status: Optional[str] = None,
            category: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update an existing task

            Args:
                task_id: ID of task to update
                title: New title (optional)
                description: New description (optional)
                priority: New priority (optional)
                status: New status (optional)
                category: New category (optional)

            Returns:
                Updated task
            """
            try:
                self.logger.info(f"Updating task {task_id}")

                # Load tasks
                data = self._load_tasks()

                # Find task
                task = None
                for t in data["tasks"]:
                    if t["id"] == task_id:
                        task = t
                        break

                if not task:
                    return error_response(f"Task not found: {task_id}")

                # Update fields
                if title is not None:
                    task["title"] = title
                if description is not None:
                    task["description"] = description
                if priority is not None:
                    valid_priorities = ["low", "medium", "high", "critical"]
                    if priority not in valid_priorities:
                        return error_response(
                            f"Invalid priority: {priority}",
                            {"valid_priorities": valid_priorities}
                        )
                    task["priority"] = priority
                if status is not None:
                    valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
                    if status not in valid_statuses:
                        return error_response(
                            f"Invalid status: {status}",
                            {"valid_statuses": valid_statuses}
                        )
                    task["status"] = status
                    if status == "completed":
                        task["completed_at"] = datetime.now().isoformat()
                if category is not None:
                    task["category"] = category

                task["updated_at"] = datetime.now().isoformat()

                # Save
                self._save_tasks(data)

                self.logger.info(f"Updated task {task_id}")
                return success_response(task)

            except Exception as e:
                self.logger.exception("update_task failed", e)
                return error_response(f"Failed to update task: {str(e)}")

        @self.mcp.tool()
        async def complete_task(task_id: str) -> Dict[str, Any]:
            """Mark a task as completed

            Args:
                task_id: ID of task to complete

            Returns:
                Completed task
            """
            try:
                self.logger.info(f"Completing task {task_id}")

                # Load tasks
                data = self._load_tasks()

                # Find task
                task = None
                for t in data["tasks"]:
                    if t["id"] == task_id:
                        task = t
                        break

                if not task:
                    return error_response(f"Task not found: {task_id}")

                # Mark as completed
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                task["updated_at"] = datetime.now().isoformat()

                # Save
                self._save_tasks(data)

                self.logger.info(f"Completed task {task_id}: {task['title']}")
                return success_response(task)

            except Exception as e:
                self.logger.exception("complete_task failed", e)
                return error_response(f"Failed to complete task: {str(e)}")

        @self.mcp.tool()
        async def delete_task(task_id: str) -> Dict[str, Any]:
            """Delete a task

            Args:
                task_id: ID of task to delete

            Returns:
                Deletion confirmation
            """
            try:
                self.logger.info(f"Deleting task {task_id}")

                # Load tasks
                data = self._load_tasks()

                # Find and remove task
                initial_count = len(data["tasks"])
                data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

                if len(data["tasks"]) == initial_count:
                    return error_response(f"Task not found: {task_id}")

                # Save
                self._save_tasks(data)

                self.logger.info(f"Deleted task {task_id}")
                return success_response({
                    "deleted": True,
                    "task_id": task_id,
                    "remaining_tasks": len(data["tasks"])
                })

            except Exception as e:
                self.logger.exception("delete_task failed", e)
                return error_response(f"Failed to delete task: {str(e)}")

        @self.mcp.tool()
        async def export_tasks(format_type: str = "markdown") -> Dict[str, Any]:
            """Export tasks to different formats

            Args:
                format_type: Export format ("markdown", "json")

            Returns:
                Exported tasks in requested format
            """
            try:
                self.logger.info(f"Exporting tasks as {format_type}")

                # Load tasks
                data = self._load_tasks()
                tasks = data["tasks"]

                if format_type == "json":
                    # Return JSON dump
                    export = json.dumps(data, indent=2)

                elif format_type == "markdown":
                    # Generate markdown
                    lines = ["# Tasks\n"]

                    # Group by status
                    statuses = ["pending", "in_progress", "completed", "cancelled"]
                    for status in statuses:
                        status_tasks = [t for t in tasks if t["status"] == status]
                        if status_tasks:
                            lines.append(f"\n## {status.replace('_', ' ').title()} ({len(status_tasks)})\n")
                            for task in sorted(status_tasks, key=lambda t: t["priority"], reverse=True):
                                priority_emoji = {
                                    "critical": "🔴",
                                    "high": "🟠",
                                    "medium": "🟡",
                                    "low": "🟢"
                                }.get(task["priority"], "⚪")

                                lines.append(f"### {priority_emoji} {task['title']}")
                                if task.get("description"):
                                    lines.append(f"\n{task['description']}\n")
                                if task.get("category"):
                                    lines.append(f"**Category:** {task['category']}  ")
                                lines.append(f"**Priority:** {task['priority']}  ")
                                lines.append(f"**Created:** {task['created_at'][:10]}  ")
                                if task.get("completed_at"):
                                    lines.append(f"**Completed:** {task['completed_at'][:10]}  ")
                                lines.append("")

                    export = "\n".join(lines)

                else:
                    return error_response(
                        f"Unknown export format: {format_type}",
                        {"valid_formats": ["markdown", "json"]}
                    )

                self.logger.info(f"Exported {len(tasks)} tasks as {format_type}")
                return success_response({
                    "format": format_type,
                    "content": export,
                    "task_count": len(tasks)
                })

            except Exception as e:
                self.logger.exception("export_tasks failed", e)
                return error_response(f"Failed to export tasks: {str(e)}")


# Create and run server
if __name__ == "__main__":
    server = TaskTrackerServer()
    server.run()
