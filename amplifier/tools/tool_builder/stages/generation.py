"""
AI-powered code generation for tool building.

This module generates complete tool implementations using AI
instead of templates and rule-based assembly.
"""

import json
import logging
from typing import Any

from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession
from amplifier.ccsdk_toolkit.defensive.code_extraction import parse_llm_code
from amplifier.ccsdk_toolkit.defensive.retry_patterns import retry_with_feedback

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Pure AI-driven code generation."""

    def __init__(self, timeout: int = 180):  # Longer timeout for code generation
        """Initialize with configurable timeout."""
        self.timeout = timeout
        self.session_options = SessionOptions(max_turns=1)

    async def generate(self, requirements: dict[str, Any], analysis: dict[str, Any], tool_name: str) -> dict[str, Any]:
        """Generate complete tool implementation using AI.

        Args:
            requirements: Requirements from analysis stage
            analysis: Metacognitive analysis results
            tool_name: Name of the tool

        Returns:
            Generated code files and metadata
        """
        # Generate main tool implementation
        main_code = await self._generate_main_code(requirements, analysis, tool_name)

        # Generate test file if testing strategy exists
        test_code = None
        if analysis.get("testing_strategy"):
            test_code = await self._generate_test_code(requirements, analysis, tool_name, main_code)

        result = {
            "tool.py": main_code,
            "tokens_used": 0,  # Will be updated by actual session
        }

        if test_code:
            result["test_tool.py"] = test_code

        logger.info(f"Code generation complete for '{tool_name}'")
        return result

    async def _generate_main_code(self, requirements: dict[str, Any], analysis: dict[str, Any], tool_name: str) -> str:
        """Generate the main tool implementation."""
        max_attempts = 3
        for attempt in range(max_attempts):
            prompt = self._build_main_prompt(requirements, analysis, tool_name)

            # Add attempt-specific guidance if not first try
            if attempt > 0:
                prompt = self._add_code_only_reminder(prompt, attempt)

            async with ClaudeSession(self.session_options) as session:
                response = await retry_with_feedback(func=session.query, prompt=prompt, max_retries=2)

                # Extract text from SessionResponse
                raw_response = response.content if hasattr(response, "content") else str(response)

                # Use defensive code extraction
                result = parse_llm_code(raw_response, validate_python=True)

                if result:
                    logger.info("Code extraction successful")
                    return result

                logger.warning(f"Attempt {attempt + 1} failed to extract code")

        # Final fallback: try with most explicit prompt
        return await self._generate_with_explicit_format(requirements, analysis, tool_name)

    async def _generate_test_code(
        self, requirements: dict[str, Any], analysis: dict[str, Any], tool_name: str, main_code: str
    ) -> str | None:
        """Generate test code for the tool."""
        max_attempts = 2
        for attempt in range(max_attempts):
            prompt = self._build_test_prompt(requirements, analysis, tool_name, main_code, attempt)

            async with ClaudeSession(self.session_options) as session:
                response = await retry_with_feedback(func=session.query, prompt=prompt, max_retries=2)

                # Extract text from SessionResponse
                raw_response = response.content if hasattr(response, "content") else str(response)

                # Use defensive code extraction
                result = parse_llm_code(raw_response, validate_python=True)

                if result:
                    logger.info("Test code extraction successful")
                    return result

                logger.warning(f"Test generation attempt {attempt + 1} failed to extract code")

        logger.warning("Could not generate valid test code")
        return None

    def _build_main_prompt(
        self, requirements: dict[str, Any], analysis: dict[str, Any], tool_name: str, attempt: int = 0
    ) -> str:
        """Build the main code generation prompt with progressive clarity."""
        # Format context from requirements and analysis
        req_json = json.dumps(requirements, indent=2)
        analysis_json = json.dumps(analysis, indent=2)

        # Base prompt changes with attempt
        if attempt == 0:
            # First attempt: Clear but not overly prescriptive
            prompt = f"""<task>
Generate a complete Python implementation for a Claude Code tool.

Tool Name: {tool_name}

Requirements:
{req_json}

Implementation Analysis:
{analysis_json}
</task>

<output_format>
Provide the complete Python code implementation.
The code should be production-ready with proper error handling and type hints.
</output_format>

<python_code>
#!/usr/bin/env python3
\"\"\"Implementation of {tool_name} Claude Code tool.\"\"\"

import claude_code
from typing import Any, Optional

# Continue with the full implementation:
"""
        elif attempt == 1:
            # Second attempt: More explicit with example
            prompt = f"""You must output ONLY Python code. No explanations.

Task: Implement {tool_name} Claude Code tool

Requirements: {req_json}

<example_format>
import claude_code
from typing import Any

@claude_code.tool
def example_tool(param: str) -> str:
    return "result"
</example_format>

Now generate the actual implementation:
<python_code>
#!/usr/bin/env python3
import claude_code
"""
        else:
            # Final attempt: Most explicit
            prompt = f"""<system>OUTPUT ONLY PYTHON CODE</system>

<python_code>
#!/usr/bin/env python3
\"\"\"Implementation of {tool_name} Claude Code tool.\"\"\"

import claude_code
import json
from typing import Any, Optional, Dict, List

@claude_code.tool
def {tool_name.replace("-", "_")}(**kwargs: Any) -> str:
    \"\"\"Main tool function.

    Implements: {requirements.get("description", "Tool functionality")}
    \"\"\"
    # COMPLETE THIS IMPLEMENTATION BASED ON:
    # Requirements: {req_json[:500]}...

"""

        return prompt

    def _build_test_prompt(
        self, requirements: dict[str, Any], analysis: dict[str, Any], tool_name: str, main_code: str, attempt: int = 0
    ) -> str:
        """Build the test code generation prompt."""
        test_strategy = analysis.get("testing_strategy", {})

        if attempt == 0:
            prompt = f"""<task>
Generate pytest tests for a Claude Code tool.

Tool to test:
{tool_name}

Implementation to test:
<code>
{main_code[:1000]}...
</code>

Testing requirements:
{json.dumps(test_strategy, indent=2)}
</task>

<output_format>
Provide complete pytest test code.
</output_format>

<python_code>
import pytest
from unittest.mock import Mock, patch
# Add more imports as needed
"""
        else:
            # More explicit on retry
            prompt = f"""OUTPUT ONLY PYTHON TEST CODE.

<python_code>
import pytest
import {tool_name.replace("-", "_")}

def test_{tool_name.replace("-", "_")}_basic():
    # Test basic functionality
    pass

# Add more tests based on:
# {json.dumps(requirements.get("core_functionality", [])[:2], indent=2)}
"""

        return prompt

    async def _generate_with_explicit_format(
        self, requirements: dict[str, Any], analysis: dict[str, Any], tool_name: str
    ) -> str:
        """Final fallback with most explicit formatting."""
        # Build a very explicit template-based prompt
        core_funcs = requirements.get("core_functionality", [])
        func_list = "\n".join([f"    # - {func}" for func in core_funcs[:3]])

        prompt = f"""Complete this Python code:

```python
#!/usr/bin/env python3
\"\"\"Implementation of {tool_name} Claude Code tool.\"\"\"

import claude_code
import json
from typing import Any, Optional

@claude_code.tool
def {tool_name.replace("-", "_")}(**kwargs: Any) -> str:
    \"\"\"Tool implementation.

    Core functionality:
{func_list}
    \"\"\"
    # YOUR IMPLEMENTATION HERE
```

Provide ONLY the completed Python code."""

        async with ClaudeSession(self.session_options) as session:
            response = await session.query(prompt)
            raw_response = response.content if hasattr(response, "content") else str(response)

            # Try to extract with relaxed validation
            result = parse_llm_code(raw_response, validate_python=False)

            if result:
                logger.info("Fallback extraction succeeded")
                return result

            # Last resort - return working stub
            logger.error(f"All code generation attempts failed for {tool_name}")
            return self._generate_stub(tool_name, requirements)

    def _add_code_only_reminder(self, prompt: str, attempt: int) -> str:
        """Add code-only reminders for retry attempts."""
        if attempt == 1:
            reminder = (
                "\n\nIMPORTANT: You MUST return ONLY Python code. No explanations, no markdown blocks, no preambles."
            )
        else:
            reminder = (
                f"\n\nCRITICAL (Attempt {attempt + 1}): OUTPUT ONLY PYTHON CODE. Start with #!/usr/bin/env python3"
            )

        return prompt + reminder

    def _generate_stub(self, tool_name: str, requirements: dict[str, Any]) -> str:
        """Generate a working stub implementation."""
        description = requirements.get("description", "Tool functionality")
        params = requirements.get("parameters", [])

        # Build parameter list
        param_str = ", ".join([f"{p}: Any" for p in params[:3]]) if params else "**kwargs: Any"

        return f"""#!/usr/bin/env python3
\"\"\"Implementation of {tool_name} Claude Code tool.

Auto-generated stub - requires manual implementation.
\"\"\"

import claude_code
import json
from typing import Any, Optional, Dict, List

@claude_code.tool
def {tool_name.replace("-", "_")}({param_str}) -> str:
    \"\"\"{description}

    This is an auto-generated stub that needs implementation.
    \"\"\"
    # TODO: Implement based on requirements:
    # {json.dumps(requirements, indent=2)[:500]}

    result = {{
        "status": "not_implemented",
        "tool": "{tool_name}",
        "message": "This tool requires manual implementation"
    }}

    return json.dumps(result, indent=2)
"""
