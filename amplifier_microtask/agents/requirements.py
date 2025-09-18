"""
Requirements Analysis Agent

Specialized agent for breaking down high-level requirements into actionable microtasks.
Each microtask is focused, testable, and sized for reliable AI execution.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from ..agent import execute_task


@dataclass
class Requirement:
    """A single requirement with breakdown"""

    id: str
    description: str
    user_story: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    technical_notes: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    estimated_complexity: str = "medium"  # simple, medium, complex


@dataclass
class RequirementsBreakdown:
    """Complete requirements analysis output"""

    project_goal: str
    requirements: List[Requirement]
    constraints: List[str]
    assumptions: List[str]
    out_of_scope: List[str]


class RequirementsAgent:
    """Agent specialized in requirements analysis and breakdown"""

    def __init__(self):
        self.agent_type = "requirements"
        self.max_requirements_per_task = 5  # Keep tasks focused

    async def analyze_input(self, user_input: str) -> RequirementsBreakdown:
        """
        Analyze raw user input and extract structured requirements.

        Args:
            user_input: Raw description from user

        Returns:
            Structured requirements breakdown
        """
        prompt = """
Analyze the following project description and extract structured requirements.

PROJECT DESCRIPTION:
{input}

Extract and structure:
1. Main project goal (one sentence)
2. Individual requirements (up to 5 most important)
3. Constraints (technical, time, resource)
4. Assumptions you're making
5. What's explicitly out of scope

For each requirement provide:
- ID (req_001, req_002, etc.)
- Clear description
- User story if applicable ("As a..., I want..., so that...")
- 2-3 acceptance criteria (testable conditions)
- Priority (critical/high/medium/low)
- Complexity estimate (simple/medium/complex)

Return ONLY valid JSON in this format:
{{
    "project_goal": "...",
    "requirements": [
        {{
            "id": "req_001",
            "description": "...",
            "user_story": "...",
            "acceptance_criteria": ["...", "..."],
            "technical_notes": "...",
            "priority": "high",
            "estimated_complexity": "medium"
        }}
    ],
    "constraints": ["..."],
    "assumptions": ["..."],
    "out_of_scope": ["..."]
}}
"""

        context = {"input": user_input}
        response = await execute_task(prompt, context, timeout=180)  # Increased to 3 minutes for requirements analysis

        # Parse response
        try:
            data = json.loads(response)

            # Convert to dataclass objects
            requirements = []
            for req_data in data.get("requirements", []):
                requirements.append(
                    Requirement(
                        id=req_data.get("id", ""),
                        description=req_data.get("description", ""),
                        user_story=req_data.get("user_story"),
                        acceptance_criteria=req_data.get("acceptance_criteria", []),
                        technical_notes=req_data.get("technical_notes"),
                        priority=req_data.get("priority", "medium"),
                        estimated_complexity=req_data.get("estimated_complexity", "medium"),
                    )
                )

            return RequirementsBreakdown(
                project_goal=data.get("project_goal", ""),
                requirements=requirements,
                constraints=data.get("constraints", []),
                assumptions=data.get("assumptions", []),
                out_of_scope=data.get("out_of_scope", []),
            )

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse requirements analysis: {e}")

    async def elaborate_requirement(self, requirement: Requirement) -> Dict[str, Any]:
        """
        Take a single requirement and elaborate with implementation details.

        Args:
            requirement: A requirement to elaborate

        Returns:
            Detailed implementation notes
        """
        prompt = """
Elaborate on this requirement with implementation details:

REQUIREMENT: {description}
USER STORY: {user_story}
ACCEPTANCE CRITERIA: {criteria}
COMPLEXITY: {complexity}

Provide:
1. Technical approach (2-3 sentences)
2. Key components needed
3. Data structures/models required
4. Potential challenges
5. Testing strategy

Return ONLY valid JSON:
{{
    "technical_approach": "...",
    "components": ["..."],
    "data_models": ["..."],
    "challenges": ["..."],
    "testing_strategy": "..."
}}
"""

        context = {
            "description": requirement.description,
            "user_story": requirement.user_story or "N/A",
            "criteria": "\n".join(requirement.acceptance_criteria or []),
            "complexity": requirement.estimated_complexity,
        }

        response = await execute_task(prompt, context, timeout=180)  # Increased to 3 minutes for requirements analysis

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse elaboration: {e}")

    async def prioritize_requirements(self, requirements: List[Requirement]) -> List[str]:
        """
        Given a list of requirements, return them in implementation order.

        Args:
            requirements: List of requirements to prioritize

        Returns:
            List of requirement IDs in recommended implementation order
        """
        if not requirements:
            return []

        # Format requirements for the prompt
        req_summaries = []
        for req in requirements:
            req_summaries.append(
                f"{req.id}: {req.description} (Priority: {req.priority}, Complexity: {req.estimated_complexity})"
            )

        prompt = """
Given these requirements, determine the best implementation order.

REQUIREMENTS:
{requirements}

Consider:
1. Dependencies between requirements
2. Priority levels (critical > high > medium > low)
3. Building foundational pieces first
4. Quick wins for momentum
5. Risk mitigation

Return ONLY a JSON array of requirement IDs in implementation order:
["req_001", "req_002", ...]
"""

        context = {"requirements": "\n".join(req_summaries)}
        response = await execute_task(prompt, context, timeout=180)  # Increased to 3 minutes for requirements analysis

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to priority order
            return [
                req.id
                for req in sorted(
                    requirements,
                    key=lambda r: (
                        {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(r.priority, 2),
                        {"simple": 0, "medium": 1, "complex": 2}.get(r.estimated_complexity, 1),
                    ),
                )
            ]

    async def generate_test_cases(self, requirement: Requirement) -> List[Dict[str, str]]:
        """
        Generate test cases for a requirement.

        Args:
            requirement: The requirement to test

        Returns:
            List of test cases
        """
        prompt = """
Generate test cases for this requirement:

REQUIREMENT: {description}
ACCEPTANCE CRITERIA:
{criteria}

For each acceptance criterion, create 1-2 test cases.
Include both positive and negative test cases.

Return ONLY a JSON array of test cases:
[
    {{
        "id": "test_001",
        "description": "...",
        "type": "positive|negative",
        "steps": ["..."],
        "expected_result": "..."
    }}
]
"""

        context = {
            "description": requirement.description,
            "criteria": "\n".join(requirement.acceptance_criteria or ["No specific criteria"]),
        }

        response = await execute_task(prompt, context, timeout=180)  # Increased to 3 minutes for requirements analysis

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []  # Return empty list if parsing fails
