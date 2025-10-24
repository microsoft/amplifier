"""
Task Tracker MCP Server for Codex.
Provides task management within sessions, replicating Claude Code's TodoWrite functionality.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from mcp.server.fastmcp import FastMCP

# Import base utilities
from ..base import MCPLogger, AmplifierMCPServer, get_project_root, success_response, error_response


class TaskTrackerServer(AmplifierMCPServer):
    """MCP server for task tracking and management"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-tasks")
        
        # Initialize base server
        super().__init__("task_tracker", mcp)
        
        # Set up task storage
        self.tasks_file = Path(".codex/tasks/session_tasks.json")
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing tasks or initialize empty
        self.tasks = self._load_tasks()
        
        # Register tools
        self._register_tools()

    def _load_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Load tasks from JSON file"""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded {len(data)} tasks from {self.tasks_file}")
                    return data
            else:
                self.logger.info("No existing tasks file found, starting with empty tasks")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
            return {}

    def _save_tasks(self):
        """Save tasks to JSON file"""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=2, default=str)
            self.logger.debug(f"Saved {len(self.tasks)} tasks to {self.tasks_file}")
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")

    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        return str(uuid.uuid4())

    def _register_tools(self):
        """Register all MCP tools"""
        
        @self.mcp.tool()
        async def create_task(
            title: str,
            description: Optional[str] = None,
            priority: str = "medium"
        ) -> Dict[str, Any]:
            """Create a new task
            
            Args:
                title: Task title (required)
                description: Task description (optional)
                priority: Task priority - "low", "medium", or "high" (default: "medium")
            
            Returns:
                Created task data
            """
            try:
                self.logger.info(f"Creating task: {title}")
                
                # Validate priority
                valid_priorities = ["low", "medium", "high"]
                if priority not in valid_priorities:
                    return error_response(f"Invalid priority. Must be one of: {valid_priorities}")
                
                # Create task
                task_id = self._generate_task_id()
                now = datetime.now().isoformat()
                
                task = {
                    "id": task_id,
                    "title": title,
                    "description": description or "",
                    "priority": priority,
                    "status": "pending",
                    "created_at": now,
                    "updated_at": now
                }
                
                self.tasks[task_id] = task
                self._save_tasks()
                
                self.logger.info(f"Created task {task_id}: {title}")
                return success_response(task)
                
            except Exception as e:
                self.logger.exception("create_task failed", e)
                return error_response(f"Failed to create task: {str(e)}")

        @self.mcp.tool()
        async def list_tasks(filter_status: Optional[str] = None) -> Dict[str, Any]:
            """List tasks with optional status filtering
            
            Args:
                filter_status: Filter by status - "pending", "completed", or None for all
            
            Returns:
                List of tasks matching filter
            """
            try:
                self.logger.info(f"Listing tasks with filter: {filter_status}")
                
                # Validate filter if provided
                valid_statuses = ["pending", "completed"]
                if filter_status and filter_status not in valid_statuses:
                    return error_response(f"Invalid status filter. Must be one of: {valid_statuses} or None")
                
                # Filter tasks
                if filter_status:
                    filtered_tasks = [
                        task for task in self.tasks.values()
                        if task["status"] == filter_status
                    ]
                else:
                    filtered_tasks = list(self.tasks.values())
                
                # Sort by priority (high > medium > low) then by creation time
                priority_order = {"high": 0, "medium": 1, "low": 2}
                filtered_tasks.sort(key=lambda t: (priority_order.get(t["priority"], 3), t["created_at"]))
                
                self.logger.info(f"Found {len(filtered_tasks)} tasks")
                return success_response({
                    "tasks": filtered_tasks,
                    "count": len(filtered_tasks),
                    "filter": filter_status
                })
                
            except Exception as e:
                self.logger.exception("list_tasks failed", e)
                return error_response(f"Failed to list tasks: {str(e)}")

        @self.mcp.tool()
        async def update_task(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
            """Update task properties
            
            Args:
                task_id: ID of task to update
                updates: Dictionary of properties to update (title, description, priority, status)
            
            Returns:
                Updated task data
            """
            try:
                self.logger.info(f"Updating task {task_id}")
                
                # Check if task exists
                if task_id not in self.tasks:
                    return error_response(f"Task {task_id} not found")
                
                task = self.tasks[task_id]
                
                # Validate updates
                valid_fields = ["title", "description", "priority", "status"]
                invalid_fields = [k for k in updates.keys() if k not in valid_fields]
                if invalid_fields:
                    return error_response(f"Invalid fields: {invalid_fields}. Valid fields: {valid_fields}")
                
                # Validate priority if provided
                if "priority" in updates:
                    valid_priorities = ["low", "medium", "high"]
                    if updates["priority"] not in valid_priorities:
                        return error_response(f"Invalid priority. Must be one of: {valid_priorities}")
                
                # Validate status if provided
                if "status" in updates:
                    valid_statuses = ["pending", "completed"]
                    if updates["status"] not in valid_statuses:
                        return error_response(f"Invalid status. Must be one of: {valid_statuses}")
                
                # Apply updates
                for key, value in updates.items():
                    task[key] = value
                
                task["updated_at"] = datetime.now().isoformat()
                self._save_tasks()
                
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
                Updated task data
            """
            try:
                self.logger.info(f"Completing task {task_id}")
                
                # Check if task exists
                if task_id not in self.tasks:
                    return error_response(f"Task {task_id} not found")
                
                # Update task status
                task = self.tasks[task_id]
                task["status"] = "completed"
                task["updated_at"] = datetime.now().isoformat()
                self._save_tasks()
                
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
                
                # Check if task exists
                if task_id not in self.tasks:
                    return error_response(f"Task {task_id} not found")
                
                task_title = self.tasks[task_id]["title"]
                del self.tasks[task_id]
                self._save_tasks()
                
                self.logger.info(f"Deleted task {task_id}: {task_title}")
                return success_response({
                    "deleted_task_id": task_id,
                    "deleted_task_title": task_title
                })
                
            except Exception as e:
                self.logger.exception("delete_task failed", e)
                return error_response(f"Failed to delete task: {str(e)}")

        @self.mcp.tool()
        async def export_tasks(format: str = "markdown") -> Dict[str, Any]:
            """Export tasks in specified format
            
            Args:
                format: Export format - "markdown" or "json" (default: "markdown")
            
            Returns:
                Exported tasks as string
            """
            try:
                self.logger.info(f"Exporting tasks in {format} format")
                
                # Validate format
                valid_formats = ["markdown", "json"]
                if format not in valid_formats:
                    return error_response(f"Invalid format. Must be one of: {valid_formats}")
                
                # Get all tasks sorted by priority and creation time
                tasks = list(self.tasks.values())
                priority_order = {"high": 0, "medium": 1, "low": 2}
                tasks.sort(key=lambda t: (priority_order.get(t["priority"], 3), t["created_at"]))
                
                if format == "json":
                    # Export as JSON string
                    export_data = {
                        "tasks": tasks,
                        "exported_at": datetime.now().isoformat(),
                        "total_tasks": len(tasks)
                    }
                    export_string = json.dumps(export_data, indent=2, default=str)
                    
                elif format == "markdown":
                    # Export as markdown
                    lines = [f"# Task Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
                    lines.append(f"Total tasks: {len(tasks)}\n")
                    
                    # Group by status
                    pending = [t for t in tasks if t["status"] == "pending"]
                    completed = [t for t in tasks if t["status"] == "completed"]
                    
                    if pending:
                        lines.append("## Pending Tasks\n")
                        for task in pending:
                            lines.append(f"- **[{task['priority'].upper()}]** {task['title']}")
                            if task['description']:
                                lines.append(f"  - {task['description']}")
                            lines.append(f"  - Created: {task['created_at'][:19]}")
                            lines.append("")
                    
                    if completed:
                        lines.append("## Completed Tasks\n")
                        for task in completed:
                            lines.append(f"- ~~[{task['priority'].upper()}] {task['title']}~~")
                            if task['description']:
                                lines.append(f"  - {task['description']}")
                            lines.append(f"  - Completed: {task['updated_at'][:19]}")
                            lines.append("")
                    
                    export_string = "\n".join(lines)
                
                self.logger.info(f"Exported {len(tasks)} tasks in {format} format")
                return success_response({
                    "format": format,
                    "content": export_string,
                    "task_count": len(tasks)
                })
                
            except Exception as e:
                self.logger.exception("export_tasks failed", e)
                return error_response(f"Failed to export tasks: {str(e)}")


# Create and run server
if __name__ == "__main__":
    server = TaskTrackerServer()
    server.run()