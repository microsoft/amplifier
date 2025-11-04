"""Agent Mapper Module for Super-Planner Phase 2

Purpose: Intelligent agent assignment based on task analysis and agent capabilities.
Contract: Maps tasks to the best-suited specialized agent from available pool.

This module is a self-contained brick that delivers intelligent agent assignment
by analyzing task content and matching it against agent capabilities.

Public Interface:
    assign_agent(task: Task, available_agents: list[str]) -> str
        Maps a task to the most appropriate agent based on task analysis.
        Returns the agent name that best matches the task requirements.

Dependencies:
    - amplifier.planner.models.Task: Task data structure
    - Standard library only (no external dependencies)
"""

from __future__ import annotations

import logging
import re

from amplifier.planner.models import Task

logger = logging.getLogger(__name__)


AGENT_CAPABILITIES = {
    "zen-code-architect": {
        "keywords": ["architecture", "design", "structure", "system", "blueprint", "specification"],
        "patterns": ["design.*pattern", "architect.*", "system.*design", "module.*structure"],
        "domains": ["architecture", "design", "planning"],
        "priority": 9,
    },
    "modular-builder": {
        "keywords": ["module", "component", "build", "implement", "create", "construct", "develop"],
        "patterns": ["build.*module", "create.*component", "implement.*feature", "develop.*"],
        "domains": ["implementation", "coding", "building"],
        "priority": 8,
    },
    "bug-hunter": {
        "keywords": ["bug", "error", "fix", "debug", "issue", "problem", "crash", "failure"],
        "patterns": ["fix.*bug", "debug.*", "error.*handling", "solve.*issue", "troubleshoot"],
        "domains": ["debugging", "fixing", "troubleshooting"],
        "priority": 10,
    },
    "test-coverage": {
        "keywords": ["test", "testing", "coverage", "unit", "integration", "validation", "verify"],
        "patterns": ["write.*test", "test.*coverage", "unit.*test", "integration.*test"],
        "domains": ["testing", "validation", "quality"],
        "priority": 7,
    },
    "integration-specialist": {
        "keywords": ["integrate", "api", "service", "connect", "interface", "endpoint", "webhook"],
        "patterns": ["integrate.*service", "api.*connection", "connect.*system", "interface.*"],
        "domains": ["integration", "apis", "connectivity"],
        "priority": 8,
    },
    "refactor-architect": {
        "keywords": ["refactor", "restructure", "optimize", "improve", "clean", "simplify"],
        "patterns": ["refactor.*code", "restructure.*", "optimize.*performance", "clean.*up"],
        "domains": ["refactoring", "optimization", "cleanup"],
        "priority": 7,
    },
    "performance-optimizer": {
        "keywords": ["performance", "speed", "optimize", "efficiency", "bottleneck", "slow"],
        "patterns": ["improve.*performance", "optimize.*speed", "performance.*issue"],
        "domains": ["performance", "optimization", "efficiency"],
        "priority": 8,
    },
    "database-architect": {
        "keywords": ["database", "sql", "query", "schema", "migration", "table", "index"],
        "patterns": ["database.*design", "sql.*query", "schema.*migration", "optimize.*query"],
        "domains": ["database", "sql", "data"],
        "priority": 7,
    },
    "analysis-engine": {
        "keywords": ["analyze", "analysis", "examine", "investigate", "study", "research"],
        "patterns": ["analyze.*code", "investigate.*", "study.*pattern", "examine.*"],
        "domains": ["analysis", "research", "investigation"],
        "priority": 6,
    },
    "content-researcher": {
        "keywords": ["research", "documentation", "content", "write", "document", "readme"],
        "patterns": ["write.*documentation", "research.*", "document.*", "create.*readme"],
        "domains": ["documentation", "writing", "research"],
        "priority": 5,
    },
    "api-contract-designer": {
        "keywords": ["api", "contract", "interface", "endpoint", "specification", "openapi"],
        "patterns": ["design.*api", "api.*contract", "interface.*specification"],
        "domains": ["api", "contracts", "specifications"],
        "priority": 7,
    },
    "ambiguity-guardian": {
        "keywords": ["clarify", "ambiguous", "unclear", "vague", "requirements", "specification"],
        "patterns": ["clarify.*requirements", "unclear.*specification", "ambiguous.*"],
        "domains": ["requirements", "clarification", "validation"],
        "priority": 6,
    },
}

DEFAULT_AGENT = "modular-builder"


def _calculate_match_score(task: Task, agent_config: dict) -> float:
    """Calculate how well an agent matches a task.

    Args:
        task: The task to analyze
        agent_config: Agent capability configuration

    Returns:
        Score from 0.0 to 1.0 indicating match strength
    """
    score = 0.0
    max_score = 0.0

    task_text = f"{task.title} {task.description}".lower()

    # Keyword matching (40% weight)
    keyword_matches = sum(1 for kw in agent_config["keywords"] if kw in task_text)
    if agent_config["keywords"]:
        score += (keyword_matches / len(agent_config["keywords"])) * 0.4
        max_score += 0.4

    # Pattern matching (30% weight)
    pattern_matches = 0
    for pattern in agent_config.get("patterns", []):
        if re.search(pattern, task_text, re.IGNORECASE):
            pattern_matches += 1
    if agent_config.get("patterns"):
        score += (pattern_matches / len(agent_config["patterns"])) * 0.3
        max_score += 0.3

    # Priority boost (30% weight)
    priority = agent_config.get("priority", 5) / 10.0
    score += priority * 0.3
    max_score += 0.3

    return score / max_score if max_score > 0 else 0.0


def _filter_available_agents(available_agents: list[str]) -> dict:
    """Filter capability map to only include available agents.

    Args:
        available_agents: List of agent names that are available

    Returns:
        Filtered capabilities dictionary
    """
    filtered = {}
    for agent_name in available_agents:
        # Try exact match first
        if agent_name in AGENT_CAPABILITIES:
            filtered[agent_name] = AGENT_CAPABILITIES[agent_name]
        else:
            # Try normalized match (handle case differences)
            normalized_name = agent_name.lower().replace("_", "-")
            for known_agent, config in AGENT_CAPABILITIES.items():
                if known_agent.lower() == normalized_name:
                    filtered[agent_name] = config
                    break

    return filtered


def assign_agent(task: Task, available_agents: list[str]) -> str:
    """Assign the most appropriate agent to a task.

    This function analyzes the task content and matches it against known
    agent capabilities to find the best fit. It considers keywords, patterns,
    and agent priority to make intelligent assignments.

    Args:
        task: Task object containing title, description, and metadata
        available_agents: List of available agent names to choose from

    Returns:
        Name of the assigned agent (best match or default)

    Raises:
        ValueError: If no agents are available

    Example:
        >>> task = Task(id="1", title="Fix login bug", description="Users can't login")
        >>> agents = ["bug-hunter", "modular-builder", "test-coverage"]
        >>> assign_agent(task, agents)
        "bug-hunter"
    """
    if not available_agents:
        raise ValueError("No agents available for assignment")

    # Get capabilities for available agents only
    agent_capabilities = _filter_available_agents(available_agents)

    # If no known agents match, use first available as fallback
    if not agent_capabilities:
        logger.warning(
            f"No known capabilities for agents: {available_agents}. Using first available: {available_agents[0]}"
        )
        return available_agents[0]

    # Calculate scores for each agent
    scores = {}
    for agent_name, config in agent_capabilities.items():
        scores[agent_name] = _calculate_match_score(task, config)

    # Find best match
    best_agent = max(scores, key=lambda k: scores[k])
    best_score = scores[best_agent]

    # Log assignment decision
    if best_score > 0.3:
        logger.info(f"Assigned task '{task.title}' to agent '{best_agent}' (score: {best_score:.2f})")
    else:
        # Low confidence match - use default if available
        if DEFAULT_AGENT in available_agents:
            logger.info(f"Low confidence match for task '{task.title}'. Using default agent: {DEFAULT_AGENT}")
            return DEFAULT_AGENT
        logger.warning(
            f"Low confidence match for task '{task.title}'. "
            f"Using best available: {best_agent} (score: {best_score:.2f})"
        )

    return best_agent


def get_agent_workload(tasks: list[Task]) -> dict:
    """Calculate workload distribution across agents.

    Analyzes a list of tasks to determine how many tasks are assigned
    to each agent. Useful for load balancing and capacity planning.

    Args:
        tasks: List of tasks with agent assignments

    Returns:
        Dictionary mapping agent names to task counts

    Example:
        >>> tasks = [
        ...     Task(id="1", title="Bug", assigned_to="bug-hunter"),
        ...     Task(id="2", title="Test", assigned_to="test-coverage"),
        ...     Task(id="3", title="Fix", assigned_to="bug-hunter")
        ... ]
        >>> get_agent_workload(tasks)
        {"bug-hunter": 2, "test-coverage": 1}
    """
    workload = {}
    for task in tasks:
        if task.assigned_to:
            workload[task.assigned_to] = workload.get(task.assigned_to, 0) + 1
    return workload


def suggest_agent_for_domain(domain: str, available_agents: list[str]) -> str:
    """Suggest an agent based on a domain keyword.

    Quick lookup function for finding agents that specialize in
    particular domains like "testing", "performance", etc.

    Args:
        domain: Domain keyword (e.g., "testing", "database", "api")
        available_agents: List of available agent names

    Returns:
        Suggested agent name or default if no match found

    Example:
        >>> suggest_agent_for_domain("testing", ["test-coverage", "bug-hunter"])
        "test-coverage"
    """
    domain_lower = domain.lower()
    agent_capabilities = _filter_available_agents(available_agents)

    # Find agents with matching domains
    matches = []
    for agent_name, config in agent_capabilities.items():
        if domain_lower in [d.lower() for d in config.get("domains", [])]:
            matches.append((agent_name, config.get("priority", 5)))

    if matches:
        # Return highest priority match
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]

    # Fallback to default or first available
    if DEFAULT_AGENT in available_agents:
        return DEFAULT_AGENT
    return available_agents[0] if available_agents else DEFAULT_AGENT


__all__ = ["assign_agent", "get_agent_workload", "suggest_agent_for_domain"]
