#!/usr/bin/env python3
"""
Agent Analytics MCP Server

Tracks and analyzes agent usage patterns, success rates, and provides recommendations.
"""

import json
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from ..base import AmplifierMCPServer
from ..base import MCPLogger


class AgentExecution:
    """Represents a single agent execution."""

    def __init__(
        self,
        agent_name: str,
        task: str,
        duration_seconds: float,
        success: bool,
        result_summary: str | None = None,
        context_tokens: int | None = None,
        error_message: str | None = None,
    ):
        self.agent_name = agent_name
        self.task = task
        self.duration_seconds = duration_seconds
        self.success = success
        self.result_summary = result_summary
        self.context_tokens = context_tokens
        self.error_message = error_message
        self.timestamp = time.time()


class AgentAnalyticsServer(AmplifierMCPServer):
    """MCP server for agent analytics and recommendations."""

    def __init__(self, mcp_instance):
        super().__init__("amplifier_agent_analytics", mcp_instance)
        self.executions: list[AgentExecution] = []
        self.logger = MCPLogger("agent_analytics")

        # Create analytics directory
        self.analytics_dir = Path(".codex/agent_analytics")
        self.analytics_dir.mkdir(exist_ok=True)

        # Load existing data
        self._load_executions()

    def _load_executions(self):
        """Load executions from storage."""
        executions_file = self.analytics_dir / "executions.jsonl"
        if executions_file.exists():
            try:
                with open(executions_file) as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line.strip())
                            execution = AgentExecution(**data)
                            self.executions.append(execution)
            except Exception as e:
                self.logger.error(f"Failed to load executions: {e}")

    def _save_execution(self, execution: AgentExecution):
        """Save execution to storage."""
        executions_file = self.analytics_dir / "executions.jsonl"
        data = {
            "agent_name": execution.agent_name,
            "task": execution.task,
            "duration_seconds": execution.duration_seconds,
            "success": execution.success,
            "result_summary": execution.result_summary,
            "context_tokens": execution.context_tokens,
            "error_message": execution.error_message,
            "timestamp": execution.timestamp,
        }

        with open(executions_file, "a") as f:
            f.write(json.dumps(data) + "\n")

    def _calculate_stats(self) -> dict[str, Any]:
        """Calculate statistics from executions."""
        if not self.executions:
            return {}

        # Group by agent
        agent_stats = {}
        for exec in self.executions:
            if exec.agent_name not in agent_stats:
                agent_stats[exec.agent_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "total_duration": 0,
                    "durations": [],
                }

            stats = agent_stats[exec.agent_name]
            stats["total_executions"] += 1
            if exec.success:
                stats["successful_executions"] += 1
            stats["total_duration"] += exec.duration_seconds
            stats["durations"].append(exec.duration_seconds)

        # Calculate derived metrics
        for _agent, stats in agent_stats.items():
            stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
            stats["avg_duration"] = stats["total_duration"] / stats["total_executions"]
            stats["durations"].sort()
            stats["median_duration"] = stats["durations"][len(stats["durations"]) // 2]

        return agent_stats

    def _save_stats(self):
        """Save calculated statistics."""
        stats = self._calculate_stats()
        stats_file = self.analytics_dir / "stats.json"

        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)

    def _get_agent_recommendation(self, task: str) -> str | None:
        """Get agent recommendation based on task analysis."""
        if not self.executions:
            return None

        # Simple keyword matching for now
        task_lower = task.lower()

        # Define agent specialties (could be made configurable)
        specialties = {
            "bug-hunter": ["bug", "fix", "error", "debug", "issue"],
            "zen-architect": ["design", "architecture", "structure", "pattern"],
            "test-coverage": ["test", "coverage", "spec", "validation"],
        }

        # Score agents based on task keywords
        scores = {}
        for agent, keywords in specialties.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                scores[agent] = score

        if not scores:
            return None

        # Return agent with highest score
        return max(scores, key=scores.get)

    async def log_agent_execution(
        self,
        agent_name: str,
        task: str,
        duration_seconds: float,
        success: bool,
        result_summary: str | None = None,
        context_tokens: int | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Log an agent execution for analytics.

        Args:
            agent_name: Name of the agent
            task: Task description
            duration_seconds: Execution duration
            success: Whether execution was successful
            result_summary: Summary of results
            context_tokens: Number of context tokens used
            error_message: Error message if failed

        Returns:
            True if logged successfully
        """
        try:
            execution = AgentExecution(
                agent_name=agent_name,
                task=task,
                duration_seconds=duration_seconds,
                success=success,
                result_summary=result_summary,
                context_tokens=context_tokens,
                error_message=error_message,
            )

            self.executions.append(execution)
            self._save_execution(execution)
            self._save_stats()

            self.logger.info(f"Logged execution for {agent_name}: {success}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to log execution: {e}")
            return False

    async def get_agent_stats(self, agent_name: str | None = None, time_period: int | None = None) -> dict[str, Any]:
        """Get statistics for agent(s).

        Args:
            agent_name: Specific agent name, or None for all agents
            time_period: Hours to look back, or None for all time

        Returns:
            Statistics dictionary
        """
        try:
            # Filter executions
            filtered_executions = self.executions

            if time_period:
                cutoff = time.time() - (time_period * 3600)
                filtered_executions = [e for e in filtered_executions if e.timestamp >= cutoff]

            if agent_name:
                filtered_executions = [e for e in filtered_executions if e.agent_name == agent_name]

            if not filtered_executions:
                return {"message": "No executions found for the specified criteria"}

            # Calculate stats for filtered executions
            agent_stats = {}
            for exec in filtered_executions:
                if exec.agent_name not in agent_stats:
                    agent_stats[exec.agent_name] = {
                        "total_executions": 0,
                        "successful_executions": 0,
                        "total_duration": 0,
                        "durations": [],
                    }

                stats = agent_stats[exec.agent_name]
                stats["total_executions"] += 1
                if exec.success:
                    stats["successful_executions"] += 1
                stats["total_duration"] += exec.duration_seconds
                stats["durations"].append(exec.duration_seconds)

            # Calculate derived metrics
            for _agent, stats in agent_stats.items():
                stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
                stats["avg_duration"] = stats["total_duration"] / stats["total_executions"]
                stats["durations"].sort()
                stats["median_duration"] = stats["durations"][len(stats["durations"]) // 2]

            return agent_stats

        except Exception as e:
            self.logger.error(f"Failed to get agent stats: {e}")
            return {"error": str(e)}

    async def get_agent_recommendations(self, current_task: str) -> dict[str, Any]:
        """Get agent recommendations for a task.

        Args:
            current_task: Description of the current task

        Returns:
            Recommendation with reasoning
        """
        try:
            recommendation = self._get_agent_recommendation(current_task)

            if recommendation:
                # Get stats for the recommended agent
                stats = await self.get_agent_stats(recommendation)
                agent_stats = stats.get(recommendation, {})

                return {
                    "recommended_agent": recommendation,
                    "confidence": "medium",  # Could be calculated based on historical success
                    "reasoning": f"Task analysis suggests {recommendation} based on keyword matching",
                    "agent_stats": agent_stats,
                }
            # Return most used agent as fallback
            if self.executions:
                agent_counts = {}
                for exec in self.executions:
                    agent_counts[exec.agent_name] = agent_counts.get(exec.agent_name, 0) + 1

                most_used = max(agent_counts, key=agent_counts.get)
                stats = await self.get_agent_stats(most_used)
                agent_stats = stats.get(most_used, {})

                return {
                    "recommended_agent": most_used,
                    "confidence": "low",
                    "reasoning": f"No specific match found, recommending most used agent {most_used}",
                    "agent_stats": agent_stats,
                }

            return {"message": "No agent execution data available for recommendations"}

        except Exception as e:
            self.logger.error(f"Failed to get recommendations: {e}")
            return {"error": str(e)}

    async def export_agent_report(self, format: str = "markdown", time_period: int | None = None) -> str:
        """Export agent analytics report.

        Args:
            format: Export format ("markdown" or "json")
            time_period: Hours to look back, or None for all time

        Returns:
            Report content
        """
        try:
            stats = await self.get_agent_stats(None, time_period)

            if format == "json":
                return json.dumps(stats, indent=2)

            if format == "markdown":
                report = ["# Agent Analytics Report\n"]

                if time_period:
                    report.append(f"**Time Period:** Last {time_period} hours\n")
                else:
                    report.append("**Time Period:** All time\n")

                report.append(f"**Total Executions:** {sum(s.get('total_executions', 0) for s in stats.values())}\n\n")

                for agent, agent_stats in stats.items():
                    report.append(f"## {agent}\n")
                    report.append(f"- **Total Executions:** {agent_stats['total_executions']}\n")
                    report.append(f"- **Success Rate:** {agent_stats['success_rate']:.1%}\n")
                    report.append(f"- **Average Duration:** {agent_stats['avg_duration']:.1f}s\n")
                    report.append(f"- **Median Duration:** {agent_stats['median_duration']:.1f}s\n\n")

                return "\n".join(report)

            return f"Unsupported format: {format}"

        except Exception as e:
            self.logger.error(f"Failed to export report: {e}")
            return f"Error generating report: {e}"

    async def get_recent_executions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent agent executions.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of recent executions
        """
        try:
            # Sort by timestamp descending
            sorted_executions = sorted(self.executions, key=lambda e: e.timestamp, reverse=True)

            recent = []
            for exec in sorted_executions[:limit]:
                recent.append(
                    {
                        "agent_name": exec.agent_name,
                        "task": exec.task,
                        "duration_seconds": exec.duration_seconds,
                        "success": exec.success,
                        "result_summary": exec.result_summary,
                        "context_tokens": exec.context_tokens,
                        "error_message": exec.error_message,
                        "timestamp": exec.timestamp,
                    }
                )

            return recent

        except Exception as e:
            self.logger.error(f"Failed to get recent executions: {e}")
            return []


def main():
    """Main entry point for the agent analytics MCP server."""
    mcp = FastMCP("amplifier_agent_analytics")
    server = AgentAnalyticsServer(mcp)

    # Register tools
    @mcp.tool()
    async def log_agent_execution(
        agent_name: str,
        task: str,
        duration_seconds: float,
        success: bool,
        result_summary: str | None = None,
        context_tokens: int | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Log an agent execution for analytics."""
        return await server.tool_error_handler(server.log_agent_execution)(
            agent_name, task, duration_seconds, success, result_summary, context_tokens, error_message
        )

    @mcp.tool()
    async def get_agent_stats(agent_name: str | None = None, time_period: int | None = None) -> dict[str, Any]:
        """Get statistics for agent(s)."""
        return await server.tool_error_handler(server.get_agent_stats)(agent_name, time_period)

    @mcp.tool()
    async def get_agent_recommendations(current_task: str) -> dict[str, Any]:
        """Get agent recommendations for a task."""
        return await server.tool_error_handler(server.get_agent_recommendations)(current_task)

    @mcp.tool()
    async def export_agent_report(format: str = "markdown", time_period: int | None = None) -> str:
        """Export agent analytics report."""
        return await server.tool_error_handler(server.export_agent_report)(format, time_period)

    @mcp.tool()
    async def get_recent_executions(limit: int = 10) -> list[dict[str, Any]]:
        """Get recent agent executions."""
        return await server.tool_error_handler(server.get_recent_executions)(limit)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
