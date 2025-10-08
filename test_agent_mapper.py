#!/usr/bin/env python3
"""Quick test of the agent_mapper module."""

from amplifier.planner import Task
from amplifier.planner import assign_agent
from amplifier.planner import get_agent_workload
from amplifier.planner import suggest_agent_for_domain

# Test data
available_agents = [
    "bug-hunter",
    "modular-builder",
    "test-coverage",
    "performance-optimizer",
    "database-architect",
    "zen-code-architect",
]

# Test 1: Bug-related task
bug_task = Task(
    id="1", title="Fix login authentication bug", description="Users report they cannot login with valid credentials"
)
assigned = assign_agent(bug_task, available_agents)
print(f"Bug task assigned to: {assigned}")
assert assigned == "bug-hunter", f"Expected bug-hunter, got {assigned}"

# Test 2: Architecture task
arch_task = Task(
    id="2",
    title="Design new microservice architecture",
    description="Need to design a scalable system architecture for the new features",
)
assigned = assign_agent(arch_task, available_agents)
print(f"Architecture task assigned to: {assigned}")
assert assigned == "zen-code-architect", f"Expected zen-code-architect, got {assigned}"

# Test 3: Testing task
test_task = Task(
    id="3",
    title="Write unit tests for payment module",
    description="Add comprehensive test coverage for the payment processing system",
)
assigned = assign_agent(test_task, available_agents)
print(f"Testing task assigned to: {assigned}")
assert assigned == "test-coverage", f"Expected test-coverage, got {assigned}"

# Test 4: Generic task (should use default)
generic_task = Task(id="4", title="Update documentation", description="Update the readme file")
assigned = assign_agent(generic_task, available_agents)
print(f"Generic task assigned to: {assigned}")

# Test 5: Workload calculation
tasks = [
    Task(id="1", title="Bug 1", assigned_to="bug-hunter"),
    Task(id="2", title="Bug 2", assigned_to="bug-hunter"),
    Task(id="3", title="Test", assigned_to="test-coverage"),
    Task(id="4", title="Build", assigned_to="modular-builder"),
]
workload = get_agent_workload(tasks)
print(f"\nWorkload distribution: {workload}")
assert workload["bug-hunter"] == 2
assert workload["test-coverage"] == 1

# Test 6: Domain suggestion
suggested = suggest_agent_for_domain("testing", available_agents)
print(f"\nSuggested agent for 'testing' domain: {suggested}")
assert suggested == "test-coverage"

suggested = suggest_agent_for_domain("database", available_agents)
print(f"Suggested agent for 'database' domain: {suggested}")
assert suggested == "database-architect"

print("\n✅ All tests passed!")
